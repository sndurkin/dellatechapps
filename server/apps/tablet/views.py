from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging
import json
import os
from .fetch_bus_info import get_bus_info, get_latest_bus_data, invalidate_bus_session, refresh_map_with_session_restore, create_bus_session
from .models import BusSession, BusData
from .bus_image_renderer import render_icon_at_coordinates

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def bus_view(request):
    """
    Get current bus information for a given session key.

    Requirements:
    - Compare the key to BUS_KEY env variable, return 404 if no match
    - Check for existing BusSession (should only be 1 record)
    - If present and not expired, use REFRESH_URL to get latest data
    - If no session or expired, use LOGIN_URL first, then REFRESH_URL
    - Store BusData records for debugging but don't return cached data
    - Delete BusData records when BusSession is replaced

    Query parameters:
    - key: Required. Must match BUS_KEY environment variable.
    """
    key = request.GET.get('key')

    # Check if key is provided and matches BUS_KEY environment variable
    if not key:
        return JsonResponse({'error': 'Not found'}, status=404)

    bus_key = os.getenv('BUS_KEY')
    if not bus_key or key != bus_key:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        # Check if there's an existing BusSession (there should only be 1 record)
        bus_sessions = BusSession.objects.filter(is_active=True)

        if bus_sessions.count() > 1:
            logger.warning(f"Found multiple active BusSession records: {bus_sessions.count()}")

        bus_session = bus_sessions.first()

        # Determine if we need to create a new session
        need_new_session = False

        if not bus_session:
            logger.info("No existing BusSession found, will create new one")
            need_new_session = True
        elif bus_session.is_expired():
            logger.info(f"Existing BusSession is expired (last refresh: {bus_session.last_refresh}), will create new one")
            need_new_session = True

        if need_new_session:
            # Delete old session and its data if it exists
            if bus_session:
                logger.info(f"Deleting expired BusSession and its {bus_session.bus_data.count()} BusData records")
                bus_session.delete()  # This will cascade delete BusData records

            # Create new session using LOGIN_URL
            logger.info("Creating new BusSession with login")
            bus_session = create_bus_session(key)

        # Use existing session with REFRESH_URL to get latest data
        logger.info(f"Refreshing bus data for session: {bus_session.session_key}")
        bus_data = refresh_map_with_session_restore(bus_session)

        response_data = None
        try:
            response_data = json.loads(bus_data.response_text)
        except:
            pass

        # Prepare response data (always fresh, never cached)
        response_data = {
            'success': True,
            'timestamp': bus_data.created_at.isoformat(),
            'bus_data': response_data,
            'request_successful': bus_data.request_successful
        }

        # Add processed location data if available
        if bus_data.bus_location:
            response_data['location'] = bus_data.bus_location
            if bus_data.bus_location.get('lat') is not None:
                map_image_path = render_icon_at_coordinates(bus_data.bus_location['lat'], bus_data.bus_location['lon'], None)
                if map_image_path:
                    response_data['map_image'] = map_image_path

        # Add error message if request was not successful
        if not bus_data.request_successful and bus_data.error_message:
            response_data['error_message'] = bus_data.error_message

        return JsonResponse(response_data)

    except ValueError as e:
        # This typically means missing environment variables
        logger.error(f"Configuration error for bus view: {e}")
        return JsonResponse({
            'error': 'Bus service configuration error',
            'details': str(e)
        }, status=500)

    except Exception as e:
        logger.error(f"Error in bus view for key {key}: {e}")
        return JsonResponse({
            'error': 'Failed to fetch bus information',
            'details': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def invalidate_session_view(request):
    """
    Invalidate a bus session.

    POST body should contain JSON with 'key' field.
    """
    try:
        data = json.loads(request.body)
        key = data.get('key')

        if not key:
            return JsonResponse({
                'error': 'Missing required parameter: key'
            }, status=400)

        invalidate_bus_session(key)

        return JsonResponse({
            'success': True,
            'message': f'Session {key} invalidated'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error invalidating session: {e}")
        return JsonResponse({
            'error': 'Failed to invalidate session',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def session_status_view(request):
    """
    Get status information for a bus session.

    Query parameters:
    - key: Required. Unique session identifier
    """
    key = request.GET.get('key')

    if not key:
        return JsonResponse({
            'error': 'Missing required parameter: key'
        }, status=400)

    try:
        bus_session = BusSession.objects.get(session_key=key, is_active=True)

        # Get latest bus data
        latest_data = bus_session.bus_data.first()

        response_data = {
            'success': True,
            'key': key,
            'session_created': bus_session.created_at.isoformat(),
            'last_updated': bus_session.updated_at.isoformat(),
            'last_refresh': bus_session.last_refresh.isoformat() if bus_session.last_refresh else None,
            'passenger_name': bus_session.passenger_name,
            'is_active': bus_session.is_active,
            'has_data': latest_data is not None,
            'latest_data_time': latest_data.created_at.isoformat() if latest_data else None,
            'latest_request_successful': latest_data.request_successful if latest_data else None
        }

        return JsonResponse(response_data)

    except BusSession.DoesNotExist:
        return JsonResponse({
            'success': True,
            'key': key,
            'session_exists': False
        })
    except Exception as e:
        logger.error(f"Error getting session status for key {key}: {e}")
        return JsonResponse({
            'error': 'Failed to get session status',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def render_bus_view(request):
    """
    Render a bus icon at the specified lat/lon coordinates on the appropriate map image.

    Query parameters:
    - lat: Required. Latitude coordinate (float)
    - lon: Required. Longitude coordinate (float)
    - filename: Optional. Custom output filename for the rendered image

    Returns:
    - JSON response with success status and image path, or error details
    """
    try:
        # Get lat/lon from query parameters
        lat_str = request.GET.get('lat')
        lon_str = request.GET.get('lon')
        custom_filename = request.GET.get('filename')

        if not lat_str or not lon_str:
            return JsonResponse({
                'error': 'Missing required parameters',
                'details': 'Both lat and lon parameters are required'
            }, status=400)

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return JsonResponse({
                'error': 'Invalid coordinate format',
                'details': 'lat and lon must be valid floating point numbers'
            }, status=400)

        # Call the render function
        result_path = render_icon_at_coordinates(lat, lon, custom_filename)

        if result_path:
            return JsonResponse({
                'success': True,
                'lat': lat,
                'lon': lon,
                'image_path': result_path,
                'message': f'Icon rendered successfully at coordinates ({lat}, {lon})'
            })
        else:
            return JsonResponse({
                'success': False,
                'lat': lat,
                'lon': lon,
                'error': 'No matching bounds found',
                'details': f'The coordinates ({lat}, {lon}) do not fall within any of the defined image bounds'
            }, status=404)

    except Exception as e:
        logger.error(f"Error rendering bus icon: {e}")
        return JsonResponse({
            'error': 'Failed to render bus icon',
            'details': str(e)
        }, status=500)
