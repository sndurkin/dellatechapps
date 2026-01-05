"""
Django service to fetch bus information by:
1. Making a GET request to retrieve a form page
2. Extracting form data from the HTML response
3. Building and submitting a POST request with the form data
4. Storing session data in Django models for persistence across requests
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import datetime
import logging
import re
import uuid

from django.conf import settings
from django.utils import timezone
from .models import BusSession, BusData

logger = logging.getLogger(__name__)

# Constants
LOGIN_URL = "https://login2.herecomesthebus.com/authenticate.aspx?action=login"
REFRESH_URL = "https://login2.herecomesthebus.com/Map.aspx/RefreshMap"

# Output directory for debug files (relative to Django's BASE_DIR)
OUTPUT_DIR = os.path.join(settings.BASE_DIR, "bus_output")


def safe_cookies_to_dict(cookie_jar):
    """
    Safely convert a requests cookie jar to a dictionary, handling duplicate cookie names.

    When multiple cookies exist with the same name (but different domains/paths),
    this function will keep the last one encountered, avoiding CookieConflictError.

    Args:
        cookie_jar: requests.cookies.RequestsCookieJar object

    Returns:
        dict: Dictionary of cookie name -> value pairs
    """
    cookies_dict = {}
    for cookie in cookie_jar:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict


def ensure_output_dir():
    """
    Ensure the output directory exists, creating it if necessary.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")


def get_bus_credentials():
    """
    Get bus tracking credentials from environment variables.

    Returns:
        Dictionary containing credentials (username, password, school_code, passenger)
    """
    credentials = {
        'username': os.getenv('BUS_USERNAME'),
        'password': os.getenv('BUS_PASSWORD'),
        'school_code': os.getenv('BUS_SCHOOL_CODE'),
        'passenger': os.getenv('BUS_PASSENGER_NAME'),
    }

    # Validate that all required credentials are present
    missing_vars = [key for key, value in credentials.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return credentials


def fetch_login_page(url=LOGIN_URL, session=None, bus_session=None):
    """
    Fetch the login page and optionally save it to an HTML file for debugging.

    Args:
        url: The URL to fetch
        session: Optional requests.Session object
        bus_session: Optional BusSession instance for storing request data

    Returns:
        The HTML content as a string
    """
    if session is None:
        session = requests.Session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    logger.info(f"Making GET request to {url}...")

    # Create BusData record to track this login page request
    bus_data = None
    if bus_session:
        bus_data = BusData(
            session=bus_session,
            request_url=url,
            request_method='GET',
            request_parameters={},
            request_headers=headers
        )

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()

        html_content = response.text

        # Store response data in BusData record
        if bus_data:
            bus_data.response_text = response.text
            bus_data.response_headers = dict(response.headers)
            bus_data.response_status_code = response.status_code
            bus_data.request_successful = True
            bus_data.save()

        # Save to file in output directory for debugging if in DEBUG mode
        if settings.DEBUG:
            ensure_output_dir()
            output_path = os.path.join(OUTPUT_DIR, "login_page.html")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug(f"Login page saved to {output_path}")

        return html_content

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching login page: {e}")
        if bus_data:
            bus_data.request_successful = False
            bus_data.error_message = str(e)
            # Store response data even for failed requests if available
            if hasattr(e, 'response') and e.response is not None:
                bus_data.response_text = e.response.text
                bus_data.response_headers = dict(e.response.headers)
                bus_data.response_status_code = e.response.status_code
            bus_data.save()
        raise


def extract_form_data(html_content, base_url=LOGIN_URL):
    """
    Extract form data from HTML content.

    Args:
        html_content: HTML content as a string
        base_url: Base URL for resolving relative form actions

    Returns:
        Tuple of (form_url, form_method, post_data)
    """
    # Parse HTML to extract form data
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the form (adjust selector as needed)
    form = soup.find('form')
    if not form:
        raise ValueError("No form found on the page")

    # Extract form action URL (use current URL if action is relative or missing)
    form_action = form.get('action', '')
    if form_action:
        # Handle relative URLs
        if form_action.startswith('/') or not form_action.startswith('http'):
            form_url = urljoin(base_url, form_action)
        else:
            form_url = form_action
    else:
        form_url = base_url

    # Extract form method (default to POST)
    form_method = form.get('method', 'post').lower()

    # Build POST data dictionary
    post_data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': '',
        '__VIEWSTATEGENERATOR': '',
        '__EVENTVALIDATION': '',
    }

    # Extract all input fields from the form
    inputs = form.find_all(['input', 'select', 'textarea'])
    for input_field in inputs:
        input_name = input_field.get('name')
        input_type = input_field.get('type', '').lower()

        if not input_name:
            continue

        # Handle different input types
        if input_type == 'checkbox' or input_type == 'radio':
            if input_field.get('checked'):
                post_data[input_name] = input_field.get('value', 'on')
        elif input_type == 'hidden':
            # Include hidden fields (often contain CSRF tokens, etc.)
            post_data[input_name] = input_field.get('value', '')
        elif input_type == 'submit':
            # Optionally include submit button value
            pass
        elif input_field.name == 'select':
            # Handle select dropdowns
            selected_option = input_field.find('option', selected=True)
            if selected_option:
                post_data[input_name] = selected_option.get('value', '')
            else:
                # Use first option as default
                first_option = input_field.find('option')
                if first_option:
                    post_data[input_name] = first_option.get('value', '')
        elif input_field.name == 'textarea':
            post_data[input_name] = input_field.string or ''
        else:
            # Regular text inputs, etc.
            post_data[input_name] = input_field.get('value', '')

    return form_url, form_method, post_data


def extract_map_form_data(html_content, passenger_name):
    """
    Extract select element values from the post-login HTML page.

    Args:
        html_content: HTML content as a string from the post-login page
        passenger_name: Name of the passenger to match in the select options

    Returns:
        Tuple of (passenger_value, time_of_day_select_element)
        passenger_value: The value attribute of the matched passenger option
        time_of_day_select: The select element for time of day (or None if not found)
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the passenger select element
    passenger_select = soup.find('select', {
        'name': 'ctl00$ctl00$cphWrapper$cphControlPanel$ddlSelectPassenger',
    })
    if not passenger_select:
        raise ValueError("Passenger select element not found")

    # Find the option whose text matches the passenger name
    passenger_value = None
    options = passenger_select.find_all('option')
    for option in options:
        # Get the text content of the option (strip whitespace)
        option_text = option.get_text(strip=True)
        if option_text == passenger_name:
            passenger_value = option.get('value')
            print(f"Found passenger '{passenger_name}' with value: {passenger_value}")
            break

    if passenger_value is None:
        raise ValueError(f"Passenger '{passenger_name}' not found in select options")

    # Find the time of day select element
    time_of_day_values = { 'AM': None, 'MID': None, 'PM': None }
    time_of_day_select = soup.find('select', {
        'name': 'ctl00$ctl00$cphWrapper$cphControlPanel$ddlSelectTimeOfDay',
    })
    if not time_of_day_select:
        print("Warning: Time of day select element not found")
    else:
        options = time_of_day_select.find_all('option')
        for option in options:
            option_text = option.get_text(strip=True)
            if option_text in time_of_day_values:
                time_of_day_values[option_text] = option.get('value')
                print(f"Found time with value: {option_text}")

    return passenger_value, time_of_day_values


def parse_bus_data_code(bus_data):
    """
    Parse the 'd' field from bus_data response to extract specific properties.

    Args:
        bus_data: Dictionary containing the bus response data with 'd' field

    Returns:
        Dictionary with parsed properties: lat, lon, bus_number, last_update_dt (ISO string)
        Returns None values for properties that couldn't be parsed
    """
    if not bus_data or 'd' not in bus_data:
        return {
            'lat': None,
            'lon': None,
            'bus_number': None,
            'last_update_dt': None
        }

    js_code = bus_data['d']

    # Unescape Unicode characters
    unescaped_js_code = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), js_code)

    # Clean up whitespace
    cleaned_js_code = re.sub(r'[\s]+', ' ', unescaped_js_code)

    # Extract latitude and longitude from SetBusPushPin function
    lat, lon = None, None
    m = re.search(r'SetBusPushPin\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,', cleaned_js_code)
    if m:
        lat, lon = map(float, m.groups())
        logger.debug(f'Parsed coordinates: {lat}, {lon}')

    # Extract bus number
    bus_number = None
    m = re.search(r'Bus\s+(\d+)', cleaned_js_code)
    if m:
        bus_number = int(m.group(1))
        logger.debug(f'Parsed bus number: {bus_number}')

    # Extract last update timestamp
    last_update_dt = None
    m = re.search(r'(\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+[AP]M)', cleaned_js_code)
    if m:
        try:
            parsed_dt = datetime.datetime.strptime(m.group(1), "%m-%d-%y %I:%M %p")
            last_update_dt = parsed_dt.isoformat()  # Convert to ISO string for JSON serialization
            logger.debug(f'Parsed last update: {last_update_dt}')
        except ValueError as e:
            logger.warning(f'Failed to parse datetime "{m.group(1)}": {e}')

    return {
        'lat': lat,
        'lon': lon,
        'bus_number': bus_number,
        'last_update_dt': last_update_dt
    }


def refresh_map_with_session_restore(bus_session):
    """
    Refresh the map by making a POST request, with automatic session restoration if needed.

    Args:
        bus_session: BusSession model instance

    Returns:
        BusData model instance with the response
    """
    # Create requests session and restore cookies
    requests_session = requests.Session()
    if bus_session.cookies_data:
        # Clear any existing cookies to prevent duplicates
        requests_session.cookies.clear()
        requests_session.cookies.update(bus_session.cookies_data)

    try:
        # Try to refresh with existing session
        bus_data = refresh_map(bus_session, requests_session)

        # Update stored cookies in case they changed
        bus_session.cookies_data = safe_cookies_to_dict(requests_session.cookies)
        bus_session.save()

        return bus_data

    except requests.exceptions.RequestException as e:
        # If refresh failed, it might be due to expired session
        # Try to re-login and refresh again
        logger.warning(f"Map refresh failed, attempting to re-login: {e}")

        try:
            # Get credentials and re-login
            credentials = get_bus_credentials()

            # Fetch login page
            html_content = fetch_login_page(session=requests_session, bus_session=bus_session)

            # Extract form data from HTML
            form_url, form_method, post_data = extract_form_data(html_content)

            # Add credentials to form data
            post_data['ctl00$ctl00$cphWrapper$cphContent$tbxUserName'] = credentials['username']
            post_data['ctl00$ctl00$cphWrapper$cphContent$tbxPassword'] = credentials['password']
            post_data['ctl00$ctl00$cphWrapper$cphContent$tbxAccountNumber'] = credentials['school_code']
            post_data['ctl00$ctl00$cphWrapper$cphContent$btnAuthenticate'] = 'Log In'

            # Submit login form
            login_response = login(form_url, form_method, post_data, requests_session, bus_session)

            # Extract passenger and time data from post-login page
            passenger_value, time_of_day_values = extract_map_form_data(login_response, credentials['passenger'])

            # Update session with new data
            bus_session.cookies_data = safe_cookies_to_dict(requests_session.cookies)
            bus_session.passenger_value = passenger_value
            bus_session.time_of_day_values = time_of_day_values
            bus_session.save()

            # Now try to refresh again
            bus_data = refresh_map(bus_session, requests_session)

            # Update stored cookies again
            bus_session.cookies_data = safe_cookies_to_dict(requests_session.cookies)
            bus_session.save()

            return bus_data

        except Exception as login_error:
            logger.error(f"Failed to re-login and refresh: {login_error}")
            raise


def refresh_map(bus_session, session=None):
    """
    Refresh the map by making a POST request with JSON body and store the result.

    Args:
        bus_session: BusSession model instance
        session: Optional requests.Session object (creates new one if not provided)

    Returns:
        BusData model instance with the response
    """
    if session is None:
        session = requests.Session()

    # Determine timeSpanId based on current time
    current_time = timezone.now()
    if current_time.hour < 12:
        time_span_id = bus_session.time_of_day_values.get('AM')
    else:
        time_span_id = bus_session.time_of_day_values.get('PM')

    # Build JSON body
    json_body = {
        'legacyID': bus_session.passenger_value,
        'name': bus_session.passenger_name,
        'timeSpanId': time_span_id,
        'wait': 'false'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    logger.warning(f"Refreshing map with data: {json_body}")
    logger.warning(f"Making POST request to {REFRESH_URL}...")
    for h in logger.handlers:
        h.flush()

    bus_data = BusData(session=bus_session)

    # Store request information
    bus_data.request_url = REFRESH_URL
    bus_data.request_method = 'POST'
    bus_data.request_parameters = json_body
    bus_data.request_headers = headers

    try:
        response = session.post(REFRESH_URL, json=json_body, headers=headers)
        response.raise_for_status()
        logger.info(f"Map refresh successful! Status code: {response.status_code}")

        # Store response data
        response_json = response.json()
        bus_data.response_text = response.text
        bus_data.response_headers = dict(response.headers)
        bus_data.response_status_code = response.status_code
        bus_data.request_successful = True

        # Parse the 'd' field to extract specific bus location properties
        parsed_data = parse_bus_data_code(response_json)
        bus_data.bus_location = parsed_data
        if any(value is not None for value in parsed_data.values()):
            logger.info(f"Parsed bus data: {parsed_data}")
        else:
            logger.warning("No bus location data could be parsed from response")

        # Update session last refresh time
        bus_session.last_refresh = timezone.now()
        bus_session.save()

        # Save to file in output directory for debugging if in DEBUG mode
        if settings.DEBUG:
            ensure_output_dir()
            output_path = os.path.join(OUTPUT_DIR, f'map_refresh_response_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(output_path, 'w') as f:
                json.dump(response_json, f, indent=2)
            logger.debug(f"Map refresh response written to {output_path}")

        bus_data.save()
        return bus_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error refreshing map: {e}")
        bus_data.request_successful = False
        bus_data.error_message = str(e)
        # Store response data even for failed requests if available
        if hasattr(e, 'response') and e.response is not None:
            bus_data.response_text = e.response.text
            bus_data.response_headers = dict(e.response.headers)
            bus_data.response_status_code = e.response.status_code
        bus_data.save()
        raise


def get_or_create_bus_session(session_key):
    """
    Get existing bus session or create a new one if needed.

    Args:
        session_key: Unique identifier for the session

    Returns:
        BusSession instance
    """
    try:
        bus_session = BusSession.objects.get(session_key=session_key, is_active=True)
        logger.info(f"Found existing bus session for key: {session_key}")
        return bus_session
    except BusSession.DoesNotExist:
        logger.info(f"No active bus session found for key: {session_key}. Will create new one.")
        return None


def create_bus_session(session_key):
    """
    Create a new bus session by logging in and extracting session data.

    Args:
        session_key: Unique identifier for the session

    Returns:
        BusSession instance
    """
    # Create a requests session to maintain cookies
    requests_session = requests.Session()

    try:
        # Get credentials from environment
        credentials = get_bus_credentials()

        # Create temporary session for logging
        temp_session = BusSession(
            session_key=str(uuid.uuid4()),
            passenger_name="temp"
        )
        temp_session.save()  # Save temporarily to get an ID for foreign key relationships

        # Step 1: Fetch login page
        html_content = fetch_login_page(session=requests_session, bus_session=temp_session)

        # Step 2: Extract form data from HTML
        form_url, form_method, post_data = extract_form_data(html_content)

        # Add credentials to form data
        post_data['ctl00$ctl00$cphWrapper$cphContent$tbxUserName'] = credentials['username']
        post_data['ctl00$ctl00$cphWrapper$cphContent$tbxPassword'] = credentials['password']
        post_data['ctl00$ctl00$cphWrapper$cphContent$tbxAccountNumber'] = credentials['school_code']
        post_data['ctl00$ctl00$cphWrapper$cphContent$btnAuthenticate'] = 'Log In'

        # Step 3: Submit login form
        login_response = login(form_url, form_method, post_data, requests_session, temp_session)

        # Step 4: Extract passenger and time data from post-login page
        passenger_value, time_of_day_values = extract_map_form_data(login_response, credentials['passenger'])

        # Step 5: Create and save bus session
        bus_session = BusSession.objects.create(
            session_key=session_key,
            cookies_data=safe_cookies_to_dict(requests_session.cookies),
            passenger_name=credentials['passenger'],
            passenger_value=passenger_value,
            time_of_day_values=time_of_day_values,
            is_active=True
        )

        # Transfer BusData records from temp session to real session
        temp_session.bus_data.update(session=bus_session)
        temp_session.delete()  # Clean up temporary session

        logger.info(f"Created new bus session for key: {session_key}")
        return bus_session

    except Exception as e:
        logger.error(f"Error creating bus session: {e}")
        raise


def login(form_url, form_method, post_data, session=None, bus_session=None):
    """
    Login to the system by submitting the login form with POST data.

    Args:
        form_url: URL to submit the form to
        form_method: HTTP method ('post' or 'get')
        post_data: Dictionary of form data
        session: Optional requests.Session object (creates new one if not provided)
        bus_session: Optional BusSession instance for storing request data

    Returns:
        Response text from the server after login
    """
    if session is None:
        session = requests.Session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    logger.info(f"Submitting {form_method.upper()} request to {form_url}...")
    logger.debug(f"Form data keys: {list(post_data.keys())}")

    # Create BusData record to track this login request
    bus_data = None
    if bus_session:
        bus_data = BusData(
            session=bus_session,
            request_url=form_url,
            request_method=form_method.upper(),
            request_parameters=post_data,
            request_headers=headers
        )

    try:
        # Submit request with form data (allow_redirects=True automatically follows 302 redirects)
        if form_method == 'post':
            response = session.post(form_url, data=post_data, headers=headers, allow_redirects=True)
        else:
            # Fallback to GET if method is not POST
            response = session.get(form_url, params=post_data, headers=headers, allow_redirects=True)

        # Check if a redirect occurred
        if response.history:
            logger.info(f"Request redirected (302). Final status code: {response.status_code}")
        else:
            logger.info(f"Request successful! Status code: {response.status_code}")

        response.raise_for_status()

        # Store response data in BusData record
        if bus_data:
            bus_data.response_text = response.text
            bus_data.response_headers = dict(response.headers)
            bus_data.response_status_code = response.status_code
            bus_data.request_successful = True
            bus_data.save()

        # Write login response to file for debugging if in DEBUG mode
        if settings.DEBUG:
            ensure_output_dir()
            output_path = os.path.join(OUTPUT_DIR, 'login_response.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.debug(f"Login response written to {output_path}")

        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during login: {e}")
        if bus_data:
            bus_data.request_successful = False
            bus_data.error_message = str(e)
            # Store response data even for failed requests if available
            if hasattr(e, 'response') and e.response is not None:
                bus_data.response_text = e.response.text
                bus_data.response_headers = dict(e.response.headers)
                bus_data.response_status_code = e.response.status_code
            bus_data.save()
        raise


def get_bus_info(session_key):
    """
    Main function to get bus information for a given session key.
    This function handles session management and fetches current bus data.

    Args:
        session_key: Unique identifier for the session (e.g., user key, device ID)

    Returns:
        BusData instance with the latest bus information
    """
    try:
        # Get or create bus session
        bus_session = get_or_create_bus_session(session_key)

        if bus_session is None:
            # Create new session
            bus_session = create_bus_session(session_key)

        # Create requests session and restore cookies
        requests_session = requests.Session()
        if bus_session.cookies_data:
            # Clear any existing cookies to prevent duplicates
            requests_session.cookies.clear()
            requests_session.cookies.update(bus_session.cookies_data)

        # Fetch current bus data
        bus_data = refresh_map(bus_session, requests_session)

        # Update stored cookies in case they changed
        bus_session.cookies_data = safe_cookies_to_dict(requests_session.cookies)
        bus_session.save()

        return bus_data

    except Exception as e:
        logger.error(f"Error getting bus info for session {session_key}: {e}")
        raise


def invalidate_bus_session(session_key):
    """
    Invalidate a bus session (mark as inactive).

    Args:
        session_key: Unique identifier for the session
    """
    try:
        bus_session = BusSession.objects.get(session_key=session_key, is_active=True)
        bus_session.is_active = False
        bus_session.save()
        logger.info(f"Invalidated bus session for key: {session_key}")
    except BusSession.DoesNotExist:
        logger.warning(f"No active bus session found to invalidate for key: {session_key}")


def get_latest_bus_data(session_key, max_age_minutes=5):
    """
    Get the latest bus data for a session, optionally filtering by age.

    Args:
        session_key: Unique identifier for the session
        max_age_minutes: Maximum age of data in minutes (default: 5)

    Returns:
        BusData instance or None if no recent data found
    """
    try:
        bus_session = BusSession.objects.get(session_key=session_key, is_active=True)
        cutoff_time = timezone.now() - datetime.timedelta(minutes=max_age_minutes)

        latest_data = bus_session.bus_data.filter(
            created_at__gte=cutoff_time,
            request_successful=True
        ).first()

        return latest_data

    except BusSession.DoesNotExist:
        logger.warning(f"No active bus session found for key: {session_key}")
        return None
