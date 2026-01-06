from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging
import json
import os
from datetime import datetime
from .fetch_bus_info import get_bus_info, get_latest_bus_data, invalidate_bus_session, refresh_map_with_session_restore, create_bus_session
from .models import BusSession, BusData
from .bus_image_renderer import render_icon_at_coordinates
from .weather import get_hourly_forecast, get_weekly_forecast

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
    - debug: Optional. If 'true', returns JSON location data instead of BMP image response.
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    if not key:
        return JsonResponse({'error': 'Not found'}, status=404)

    tablet_key = os.getenv('TABLET_KEY')
    if not tablet_key or key != tablet_key:
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

        parsed_bus_data = None
        try:
            parsed_bus_data = json.loads(bus_data.response_text)
        except:
            pass

        # Prepare response data (always fresh, never cached)
        response_data = {
            'success': True,
            'timestamp': bus_data.created_at.isoformat(),
            'bus_data': parsed_bus_data,
            'request_successful': bus_data.request_successful
        }

        # Add processed location data if available
        if bus_data.bus_location:
            response_data['location'] = bus_data.bus_location
            if bus_data.bus_location.get('lat') is not None:
                # Check if client wants image data
                if request.GET.get('debug') == 'true':
                    response_data['map_available'] = True
                else:
                    map_image_bytes = render_icon_at_coordinates(
                        bus_data.bus_location['lat'],
                        bus_data.bus_location['lon'],
                        return_bytes=True
                    )
                    if map_image_bytes:
                        # Return image directly as BMP response
                        response = HttpResponse(map_image_bytes, content_type='image/bmp')
                        response['Content-Disposition'] = f'inline; filename="bus_map_{bus_data.bus_location["lat"]}_{bus_data.bus_location["lon"]}.bmp"'
                        return response

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
        logger.error(f"Error in bus view for key {key}", e)
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

    Returns:
    - BMP image response with the rendered bus icon, or JSON error response if coordinates are invalid
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

        # Call the render function to get image bytes
        image_bytes = render_icon_at_coordinates(lat, lon, return_bytes=True)

        if image_bytes:
            # Return image directly as BMP response
            response = HttpResponse(image_bytes, content_type='image/bmp')
            response['Content-Disposition'] = f'inline; filename="bus_map_{lat}_{lon}.bmp"'
            return response
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


@require_http_methods(["GET"])
def weather_view(request):
    """
    Get weather information and render an HTML chart showing hourly temperature forecast.
    Returns an HTML page with a grayscale temperature chart (800x480 pixels).
    Fetches exactly 24 hours of hourly forecast data.

    Query parameters:
    - lat: Required. Latitude coordinate (float)
    - lon: Required. Longitude coordinate (float)
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    if not key:
        return JsonResponse({'error': 'Not found'}, status=404)

    tablet_key = os.getenv('TABLET_KEY')
    if not tablet_key or key != tablet_key:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        # Get Tomorrow.io API key from environment
        api_key = os.getenv('TOMORROW_IO_API_KEY')
        if not api_key:
            return HttpResponse(
                '<html><body><h1>Error</h1><p>Weather service configuration error: Tomorrow.io API key not configured</p></body></html>',
                status=500,
                content_type='text/html'
            )

        # Get lat/lon from query parameters
        lat_str = request.GET.get('lat')
        lon_str = request.GET.get('lon')

        if not lat_str or not lon_str:
            return HttpResponse(
                '<html><body><h1>Error</h1><p>Missing required parameters: Both lat and lon parameters are required</p></body></html>',
                status=400,
                content_type='text/html'
            )

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return HttpResponse(
                '<html><body><h1>Error</h1><p>Invalid coordinate format: lat and lon must be valid floating point numbers</p></body></html>',
                status=400,
                content_type='text/html'
            )

        # Get hourly forecast (24 hours)
        hourly_forecast = get_hourly_forecast(lat, lon, api_key)

        if not hourly_forecast:
            return HttpResponse(
                '<html><body><h1>Error</h1><p>Failed to fetch hourly forecast</p></body></html>',
                status=500,
                content_type='text/html'
            )

        # Get weekly forecast
        weekly_forecast = get_weekly_forecast(lat, lon, api_key)

        # Extract temperatures, UV index, precipitation probability, and times from forecast
        temperatures = [item['temperature'] for item in hourly_forecast]
        uv_indices = [item.get('uv_index', 0) for item in hourly_forecast]
        precipitation_probabilities = [item.get('precipitation_probability', 0) for item in hourly_forecast]
        datetimes = [item['datetime'] for item in hourly_forecast]

        # Parse datetime strings to extract hour labels
        hour_labels = []
        datetime_objects = []
        for dt_str in datetimes:
            try:
                # Handle ISO format datetime strings (e.g., "2026-01-04T23:00:00-05:00")
                dt_str_clean = dt_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(dt_str_clean)
                datetime_objects.append(dt)
                # Format as 12-hour time with AM/PM (e.g., "3 AM", "6 PM")
                hour_12 = dt.hour % 12
                if hour_12 == 0:
                    hour_12 = 12
                am_pm = 'AM' if dt.hour < 12 else 'PM'
                hour_labels.append(f"{hour_12} {am_pm}")
            except Exception as e:
                logger.warning(f"Failed to parse datetime {dt_str}: {e}")
                datetime_objects.append(None)
                hour_labels.append('')

        # Calculate chart dimensions
        total_width = 800
        total_height = 480  # Total height exactly 480px
        x_axis_label_height = 30  # Space for x-axis labels
        hourly_chart_height = 230  # Hourly chart height (half of total)
        weekly_chart_height = 230  # Weekly chart height (half of total)
        chart_margin_y = total_height - hourly_chart_height - weekly_chart_height
        hourly_padding_width = 20
        plot_width = total_width - 2 * hourly_padding_width
        # Plot height is chart height minus x-axis label space
        plot_height = hourly_chart_height - x_axis_label_height  # 210px for hourly chart

        # Calculate derived values needed for chart generation
        x_axis_start = 0
        x_axis_end = total_width
        hourly_chart_offset_y = 0  # No title, starts at top
        y_axis_end = hourly_chart_offset_y + plot_height  # End of plot area

        # Calculate average temperature and center y-axis on it with 50-degree range
        avg_temp = sum(temperatures) / len(temperatures) if temperatures else 50
        temp_range = 50
        min_temp = avg_temp - 25
        max_temp = avg_temp + 25

        # Generate SVG chart path
        points = []
        temp_points = []  # Store temp and coordinates for finding min/max
        for i, temp in enumerate(temperatures):
            x = hourly_padding_width + (i / (len(temperatures) - 1)) * plot_width if len(temperatures) > 1 else hourly_padding_width + plot_width / 2
            # Invert y-axis (SVG y increases downward)
            y = hourly_chart_offset_y + plot_height - ((temp - min_temp) / temp_range) * plot_height
            points.append(f"{x},{y}")
            temp_points.append({'x': x, 'y': y, 'temp': temp})

        path_data = f"M {points[0]} " + " ".join([f"L {point}" for point in points[1:]])

        # Find min and max temperature points
        min_temp_point = min(temp_points, key=lambda p: p['temp'])
        max_temp_point = max(temp_points, key=lambda p: p['temp'])

        # Calculate label positions (8 pixels above the point)
        min_temp_label = {
            'x': min_temp_point['x'],
            'y': min_temp_point['y'] - 8,
            'temp': int(round(min_temp_point['temp']))
        }
        max_temp_label = {
            'x': max_temp_point['x'],
            'y': max_temp_point['y'] - 8,
            'temp': int(round(max_temp_point['temp']))
        }

        # Generate UV index shaded area using secondary y-axis (0-11 range)
        uv_max = 11
        uv_min = 0
        uv_range = uv_max - uv_min
        uv_points = []
        uv_points_with_data = []
        for i, uv_index in enumerate(uv_indices):
            x = hourly_padding_width + (i / (len(uv_indices) - 1)) * plot_width if len(uv_indices) > 1 else hourly_padding_width + plot_width / 2
            # UV index uses same x positions but different y scale (0-11 mapped to plot_height)
            # Invert y-axis (SVG y increases downward)
            y = hourly_chart_offset_y + plot_height - ((uv_index - uv_min) / uv_range) * plot_height
            uv_points.append(f"{x},{y}")
            uv_points_with_data.append({'x': x, 'y': y, 'uv_index': uv_index})

        # Create UV index area path (shaded area, no line)
        uv_path_data = f"M {hourly_padding_width},{y_axis_end} "  # Start at bottom-left
        uv_path_data += f"L {uv_points[0]} "  # Move to first UV point
        uv_path_data += " ".join([f"L {point}" for point in uv_points[1:]])  # Draw line through all UV points
        uv_path_data += f" L {x_axis_end},{y_axis_end} Z"  # Close the path to bottom-right

        # Find peak UV index point
        peak_uv_point = max(uv_points_with_data, key=lambda p: p['uv_index'])
        peak_uv_label = {
            'x': peak_uv_point['x'],
            'y': peak_uv_point['y'] - 8,
            'uv_index': int(round(peak_uv_point['uv_index']))
        }

        # Generate precipitation probability dotted line using third y-axis (0-100 range)
        # Only render if there are non-zero values
        precip_max = 100
        precip_min = 0
        precip_range = precip_max - precip_min

        # Check if there are any non-zero precipitation probabilities
        has_precipitation = any(p > 0 for p in precipitation_probabilities)

        if has_precipitation:
            precip_points = []
            for i, precip_prob in enumerate(precipitation_probabilities):
                x = hourly_padding_width + (i / (len(precipitation_probabilities) - 1)) * plot_width if len(precipitation_probabilities) > 1 else hourly_padding_width + plot_width / 2
                # Precipitation probability uses same x positions but different y scale (0-100 mapped to plot_height)
                # Invert y-axis (SVG y increases downward)
                y = hourly_chart_offset_y + plot_height - ((precip_prob - precip_min) / precip_range) * plot_height
                precip_points.append(f"{x},{y}")

            # Create precipitation probability line path (dotted line)
            precip_path_data = f"M {precip_points[0]} " + " ".join([f"L {point}" for point in precip_points[1:]])
        else:
            precip_path_data = None

        # Prepare grid lines data (50-degree range centered on average)
        # Note: Y-axis labels removed per requirements
        num_grid_lines = 5
        grid_lines = []
        for i in range(num_grid_lines + 1):
            y_pos = hourly_chart_offset_y + (i / num_grid_lines) * plot_height
            grid_lines.append({
                'y_pos': y_pos
            })

        # Prepare hour labels with x positions (only every 3 hours)
        hour_labels_with_pos = []
        for i, (label, dt_obj) in enumerate(zip(hour_labels, datetime_objects)):
            # Only show labels for hours divisible by 3 (0, 3, 6, 9, 12, 15, 18, 21)
            if dt_obj is not None and dt_obj.hour % 3 == 0:
                x_pos = hourly_padding_width + (i / (len(hour_labels) - 1)) * plot_width if len(hour_labels) > 1 else hourly_padding_width + plot_width / 2
                hour_labels_with_pos.append({
                    'label': label,
                    'x_pos': x_pos
                })

        # Calculate remaining derived values for template
        y_label_x = hourly_padding_width - 10
        x_label_y = y_axis_end + 20

        # Process weekly forecast data for second chart
        weekly_chart_data = []
        weekly_plot_padding_x = 40
        weekly_plot_padding_y = 20
        weekly_plot_height = weekly_chart_height - x_axis_label_height - (2 * weekly_plot_padding_y)
        weekly_plot_width = total_width - (2 * weekly_plot_padding_x)
        # Weekly chart starts after hourly chart
        weekly_chart_offset_y = hourly_chart_height + weekly_plot_padding_y + chart_margin_y

        if weekly_forecast:
            # Find min and max temps across all days for scaling
            all_temps = []
            for day in weekly_forecast:
                if day.get('low_temp') is not None:
                    all_temps.append(day['low_temp'])
                if day.get('high_temp') is not None:
                    all_temps.append(day['high_temp'])

            if all_temps:
                weekly_min_temp = min(all_temps)
                weekly_max_temp = max(all_temps)
                weekly_temp_range = weekly_max_temp - weekly_min_temp if weekly_max_temp != weekly_min_temp else 1
            else:
                weekly_min_temp = 0
                weekly_max_temp = 100
                weekly_temp_range = 100

            # Process each day
            for i, day in enumerate(weekly_forecast):
                day_name = day.get('name', '')
                low_temp = day.get('low_temp')
                high_temp = day.get('high_temp')

                if low_temp is not None and high_temp is not None:
                    # Calculate x position (centered in each day's slot)
                    x_pos = weekly_plot_padding_x + (i / (len(weekly_forecast) - 1)) * weekly_plot_width if len(weekly_forecast) > 1 else weekly_plot_padding_x + weekly_plot_width / 2

                    # Calculate y positions (invert y-axis) - add offset for second chart
                    low_y = weekly_chart_offset_y + weekly_plot_height - ((low_temp - weekly_min_temp) / weekly_temp_range) * weekly_plot_height
                    high_y = weekly_chart_offset_y + weekly_plot_height - ((high_temp - weekly_min_temp) / weekly_temp_range) * weekly_plot_height

                    # Pill shape dimensions (Apple-style)
                    pill_width = 24
                    pill_half_width = pill_width / 2
                    pill_height = abs(high_y - low_y)

                    # Pill position (centered on x_pos, spanning from low_y to high_y)
                    pill_x = x_pos - pill_half_width
                    pill_y = min(low_y, high_y)  # Use min since SVG y increases downward
                    pill_radius = pill_half_width  # Fully rounded ends for pill shape

                    weekly_chart_data.append({
                        'day_name': day_name,
                        'x_pos': x_pos,
                        'low_temp': int(round(low_temp)),
                        'high_temp': int(round(high_temp)),
                        'low_y': low_y,
                        'high_y': high_y,
                        'pill_x': pill_x,
                        'pill_y': pill_y,
                        'pill_width': pill_width,
                        'pill_height': pill_height,
                        'pill_radius': pill_radius,
                        'low_label_y': low_y + 20,  # Label below the low point
                        'high_label_y': high_y - 5,  # Label above the high point
                        'day_label_y': weekly_chart_offset_y + weekly_plot_height + (x_axis_label_height * 1.5),
                    })

        # Prepare context for template
        context = {
            'chart_width': total_width,
            'chart_height': total_height,
            'padding': hourly_padding_width,
            'x_axis_start': x_axis_start,
            'x_axis_end': x_axis_end,
            'y_axis_end': y_axis_end,
            'y_label_x': y_label_x,
            'x_label_y': x_label_y,
            'grid_lines': grid_lines,
            'hour_labels': hour_labels_with_pos,
            'path_data': path_data,
            'min_temp_label': min_temp_label,
            'max_temp_label': max_temp_label,
            'uv_path_data': uv_path_data,
            'peak_uv_label': peak_uv_label,
            'precip_path_data': precip_path_data,
            'weekly_chart_data': weekly_chart_data,
            'weekly_chart_height': weekly_chart_height,
            'weekly_padding': weekly_plot_padding_x,
            'weekly_y_axis_end': weekly_chart_offset_y + weekly_plot_height + x_axis_label_height,
            'weekly_chart_offset_y': weekly_chart_offset_y,
            'x_axis_label_height': x_axis_label_height,
        }

        return render(request, 'tablet/weather_chart.html', context)

    except Exception as e:
        logger.error(f"Error in weather view", e)
        return HttpResponse(
            f'<html><body><h1>Error</h1><p>Failed to fetch weather information: {str(e)}</p></body></html>',
            status=500,
            content_type='text/html'
        )
