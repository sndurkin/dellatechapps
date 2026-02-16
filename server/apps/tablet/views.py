from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import logging
import json
import os
import hashlib
import base64
import io
from datetime import datetime, time, date
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
from .fetch_bus_info import get_bus_info, get_latest_bus_data, invalidate_bus_session, refresh_map_with_session_restore, create_bus_session
from .models import BusSession, BusData, BusDashboardSkip
from .bus_image_renderer import render_icon_at_coordinates
from .weather import render_weather_chart_bmp
from .svg_to_bmp import render_svg_to_bmp
from constance import config

logger = logging.getLogger(__name__)

# Header name for poll interval (seconds to wait before next request)
X_POLL_INTERVAL_HEADER = "X-Poll-Interval"


def _add_poll_interval_header(response, interval):
    """Add X-Poll-Interval header to the response."""
    response[X_POLL_INTERVAL_HEADER] = str(interval)
    return response

# In-memory cache for storing recent bus images by hash
# Format: {hash_string: image_bytes}
_bus_image_cache = {}
# In-memory cache for storing recent weather images by hash
_weather_image_cache = {}
# Maximum number of images to keep in cache
_MAX_CACHE_SIZE = 3


@require_http_methods(["GET"])
def bus_view(request):
    """
    Get current bus information for a given session key.
    Supports partial refresh by comparing with a previously generated image.

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
    - lastHash: Optional. Hash of the previous image to compare against for partial refresh.

    Returns:
    - Full refresh: BMP image with X-Update-Type: full, X-Image-Hash headers
    - Partial refresh: JSON with changed regions, X-Update-Type: partial, X-Image-Hash headers
    - Skip: 204 No Content with X-Update-Type: skip, X-Image-Hash headers
    - Error: JSON error response if coordinates are invalid or debug=true
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    tablet_key = os.getenv('TABLET_KEY')
    if not key or not tablet_key or key != tablet_key:
        return _add_poll_interval_header(JsonResponse({'error': 'Not found'}, status=404), config.TABLET_BUS_POLL_INTERVAL)

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
                    lat = bus_data.bus_location['lat']
                    lon = bus_data.bus_location['lon']
                    last_hash = request.GET.get('lastHash')

                    logger.info(f"bus_view: Rendering image for lat={lat}, lon={lon}, lastHash={'provided' if last_hash else 'not provided'}")

                    # Call the render function to get image bytes
                    map_image_bytes = render_icon_at_coordinates(lat, lon, return_bytes=True)

                    if not map_image_bytes:
                        logger.warning(f"bus_view: Map could not be rendered for coordinates ({lat}, {lon})")
                        response_data['error_message'] = 'Map could not be rendered as an image'
                    else:
                        # Generate hash for current image
                        current_hash = _generate_image_hash(map_image_bytes)
                        logger.info(f"bus_view: Generated current hash: {current_hash[:16]}... (image size: {len(map_image_bytes)} bytes)")

                        # Store current image in cache
                        _bus_image_cache[current_hash] = map_image_bytes
                        logger.info(f"bus_view: Cache size: {len(_bus_image_cache)}/{_MAX_CACHE_SIZE}, cached hashes: {[h[:8] + '...' for h in list(_bus_image_cache.keys())[:5]]}")

                        # Limit cache size
                        if len(_bus_image_cache) > _MAX_CACHE_SIZE:
                            # Remove oldest entry (simple FIFO - remove first key)
                            oldest_key = next(iter(_bus_image_cache))
                            del _bus_image_cache[oldest_key]
                            logger.info(f"bus_view: Removed oldest cache entry: {oldest_key[:16]}...")

                        # If lastHash is provided, try to find and compare with previous image
                        if last_hash:
                            logger.info(f"bus_view: lastHash provided: {last_hash[:16]}...")
                            if last_hash in _bus_image_cache:
                                logger.info(f"bus_view: Found lastHash in cache, comparing images...")
                                previous_bytes = _bus_image_cache[last_hash]

                                # Compare images
                                result_type, data = _compare_images_and_find_regions(map_image_bytes, previous_bytes)
                                logger.info(f"bus_view: Comparison result: {result_type}")

                                if result_type == 'identical':
                                    # Images are identical - return skip
                                    logger.info(f"bus_view: Images identical, returning skip (204)")
                                    response = HttpResponse(status=204)
                                    response['X-Update-Type'] = 'skip'
                                    response['X-Image-Hash'] = current_hash
                                    return _add_poll_interval_header(response, config.TABLET_BUS_POLL_INTERVAL)
                                elif result_type == 'partial':
                                    # Partial refresh - return changed regions
                                    regions, changed_count, total_pixels = data
                                    logger.info(f"bus_view: Partial refresh: {len(regions)} region(s), {changed_count}/{total_pixels} pixels changed")
                                    response_data = {
                                        'regions': regions
                                    }
                                    response = JsonResponse(response_data, content_type='application/json')
                                    response['X-Update-Type'] = 'partial'
                                    response['X-Image-Hash'] = current_hash
                                    return _add_poll_interval_header(response, config.TABLET_BUS_POLL_INTERVAL)
                                else:
                                    # result_type == 'full' - too many changes, return full refresh
                                    logger.info(f"bus_view: Comparison returned 'full', returning full refresh")
                                    response = HttpResponse(map_image_bytes, content_type='image/bmp')
                                    response['X-Update-Type'] = 'full'
                                    response['X-Image-Hash'] = current_hash
                                    response['Content-Disposition'] = f'inline; filename="bus_map_{lat}_{lon}.bmp"'
                                    return _add_poll_interval_header(response, config.TABLET_BUS_POLL_INTERVAL)
                            else:
                                logger.warning(f"bus_view: lastHash {last_hash[:16]}... not found in cache. Cache keys: {[h[:8] + '...' for h in list(_bus_image_cache.keys())]}")

                        # No lastHash provided or hash not found - return full refresh
                        if not last_hash:
                            logger.info(f"bus_view: No lastHash provided, returning full refresh")
                        else:
                            logger.info(f"bus_view: lastHash not found in cache, returning full refresh")
                        response = HttpResponse(map_image_bytes, content_type='image/bmp')
                        response['X-Update-Type'] = 'full'
                        response['X-Image-Hash'] = current_hash
                        response['Content-Disposition'] = f'inline; filename="bus_map_{lat}_{lon}.bmp"'
                        return _add_poll_interval_header(response, config.TABLET_BUS_POLL_INTERVAL)

        # Add error message if request was not successful
        if not bus_data.request_successful and bus_data.error_message:
            response_data['error_message'] = bus_data.error_message

        return _add_poll_interval_header(JsonResponse(response_data), config.TABLET_BUS_POLL_INTERVAL)

    except ValueError as e:
        # This typically means missing environment variables
        logger.error(f"Configuration error for bus view: {e}")
        return _add_poll_interval_header(JsonResponse({
            'error': 'Bus service configuration error',
            'details': str(e)
        }, status=500), config.TABLET_BUS_POLL_INTERVAL)

    except Exception as e:
        logger.error(f"Error in bus view for key {key}", e)
        return _add_poll_interval_header(JsonResponse({
            'error': 'Failed to fetch bus information',
            'details': str(e)
        }, status=500), config.TABLET_BUS_POLL_INTERVAL)


@require_http_methods(["GET"])
def test_bus(request, num):
    """
    Test endpoint for bus map images.
    - num=1: Returns bus_map_1.bmp directly.
    - num=2: Diffs bus_map_1 vs bus_map_2 and returns the same partial refresh JSON
             used in bus_view (regions with base64-encoded changed areas), or full/skip
             depending on the comparison result.

    Query parameters:
    - key: Required. Must match TABLET_KEY environment variable.

    Path parameters:
    - num: Required. Integer. 1 or 2.
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    tablet_key = os.getenv('TABLET_KEY')
    if not key or not tablet_key or key != tablet_key:
        return JsonResponse({'error': 'Not found'}, status=404)

    if num not in (1, 2):
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "assets")

        if num == 1:
            # Return bus_map_1.bmp directly
            filename = "bus_map_1.bmp"
            image_path = os.path.join(assets_dir, filename)
            if not os.path.exists(image_path):
                logger.warning(f"test_bus: Image file not found: {image_path}")
                return JsonResponse({'error': 'Not found'}, status=404)
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            response = HttpResponse(image_bytes, content_type="image/bmp")
            response["Content-Disposition"] = f'inline; filename="{filename}"'
            return response

        # num == 2: diff bus_map_1 vs bus_map_2, return partial refresh format like bus_view
        path_1 = os.path.join(assets_dir, "bus_map_1.bmp")
        path_2 = os.path.join(assets_dir, "bus_map_2.bmp")
        if not os.path.exists(path_1) or not os.path.exists(path_2):
            logger.warning(f"test_bus: One or both image files not found: {path_1}, {path_2}")
            return JsonResponse({'error': 'Not found'}, status=404)

        with open(path_1, "rb") as f:
            previous_bytes = f.read()
        with open(path_2, "rb") as f:
            current_bytes = f.read()

        current_hash = _generate_image_hash(current_bytes)
        result_type, data = _compare_images_and_find_regions(current_bytes, previous_bytes)

        if result_type == 'identical':
            response = HttpResponse(status=204)
            response['X-Update-Type'] = 'skip'
            response['X-Image-Hash'] = current_hash
            return response
        elif result_type == 'partial':
            regions, changed_count, total_pixels = data
            response_data = {'regions': regions}
            response = JsonResponse(response_data, content_type='application/json')
            response['X-Update-Type'] = 'partial'
            response['X-Image-Hash'] = current_hash
            return response
        else:
            # result_type == 'full' - too many changes, return full bus_map_2.bmp
            response = HttpResponse(current_bytes, content_type='image/bmp')
            response['X-Update-Type'] = 'full'
            response['X-Image-Hash'] = current_hash
            response['Content-Disposition'] = 'inline; filename="bus_map_2.bmp"'
            return response

    except Exception as e:
        logger.error(f"Error in test_bus view for num={num}: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Failed to load test bus image',
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


def _generate_image_hash(image_bytes):
    """Generate SHA256 hash for image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


def _find_connected_components(changed_pixels_set, width, height):
    """
    Find connected components in a set of changed pixels using flood fill.

    Returns:
        List of sets, where each set contains the pixels in one connected component.
    """
    components = []
    visited = set()

    # Directions for 8-connected neighbors
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def flood_fill(start_pixel):
        """Flood fill to find all connected pixels."""
        component = set()
        stack = [start_pixel]

        while stack:
            x, y = stack.pop()
            if (x, y) in visited or (x, y) not in changed_pixels_set:
                continue

            visited.add((x, y))
            component.add((x, y))

            # Check all 8 neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) in changed_pixels_set and (nx, ny) not in visited:
                        stack.append((nx, ny))

        return component

    # Find all connected components
    for pixel in changed_pixels_set:
        if pixel not in visited:
            component = flood_fill(pixel)
            if component:
                components.append(component)

    return components


def _merge_close_regions(bounding_boxes, merge_threshold=50):
    """
    Merge regions that are close together.

    Args:
        bounding_boxes: List of dicts with keys 'x1', 'y1', 'x2', 'y2'
        merge_threshold: Maximum distance between regions to merge them (default 50 pixels)

    Returns:
        List of merged bounding boxes
    """
    if not bounding_boxes:
        return []

    merged = []
    used = set()

    for i, box1 in enumerate(bounding_boxes):
        if i in used:
            continue

        # Start with box1
        merged_box = {
            'x1': box1['x1'],
            'y1': box1['y1'],
            'x2': box1['x2'],
            'y2': box1['y2']
        }
        used.add(i)

        # Try to merge with other boxes
        changed = True
        while changed:
            changed = False
            for j, box2 in enumerate(bounding_boxes):
                if j in used or j == i:
                    continue

                # Calculate distance between boxes
                # Distance is the minimum distance between any two points on the boxes
                # If boxes overlap or are close, merge them
                center1_x = (merged_box['x1'] + merged_box['x2']) / 2
                center1_y = (merged_box['y1'] + merged_box['y2']) / 2
                center2_x = (box2['x1'] + box2['x2']) / 2
                center2_y = (box2['y1'] + box2['y2']) / 2

                # Calculate distance between centers
                dist = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5

                # Also check if boxes are close (considering their sizes)
                # Merge if distance is less than threshold
                if dist < merge_threshold:
                    # Merge boxes
                    merged_box['x1'] = min(merged_box['x1'], box2['x1'])
                    merged_box['y1'] = min(merged_box['y1'], box2['y1'])
                    merged_box['x2'] = max(merged_box['x2'], box2['x2'])
                    merged_box['y2'] = max(merged_box['y2'], box2['y2'])
                    used.add(j)
                    changed = True

        merged.append(merged_box)

    return merged


def _compare_images_and_find_regions(current_bytes, previous_bytes, threshold=0.05, merge_threshold=50):
    """
    Compare two BMP images and find changed regions.
    Supports multiple separate regions and merges them if close together.

    Args:
        current_bytes: Current image as BMP bytes
        previous_bytes: Previous image as BMP bytes
        threshold: Maximum fraction of changed pixels to consider for partial refresh (default 5%)
        merge_threshold: Maximum distance between regions to merge them (default 50 pixels)

    Returns:
        tuple: (result_type, data)
        - result_type: 'identical', 'partial', or 'full'
        - data: For 'partial': (regions, changed_count, total_pixels)
                For 'identical' or 'full': None
    """
    try:
        logger.info(f"_compare_images_and_find_regions: Starting comparison (threshold={threshold})")
        logger.info(f"_compare_images_and_find_regions: Current image size: {len(current_bytes)} bytes, Previous image size: {len(previous_bytes)} bytes")

        # Quick check: if bytes are identical, images are identical
        if current_bytes == previous_bytes:
            logger.info(f"_compare_images_and_find_regions: Images are byte-identical, returning 'identical'")
            return ('identical', None)

        # Load images from bytes
        current_img = Image.open(io.BytesIO(current_bytes))
        previous_img = Image.open(io.BytesIO(previous_bytes))

        logger.info(f"_compare_images_and_find_regions: Current image: {current_img.size} {current_img.mode}, Previous image: {previous_img.size} {previous_img.mode}")

        # Ensure images are same size
        if current_img.size != previous_img.size:
            logger.warning(f"_compare_images_and_find_regions: Image sizes differ ({current_img.size} vs {previous_img.size}), returning 'full'")
            return ('full', None)

        # Convert to RGB for comparison if needed
        if current_img.mode != 'RGB':
            current_img = current_img.convert('RGB')
        if previous_img.mode != 'RGB':
            previous_img = previous_img.convert('RGB')

        # Get image dimensions
        width, height = current_img.size
        total_pixels = width * height
        logger.info(f"_compare_images_and_find_regions: Image dimensions: {width}x{height}, total pixels: {total_pixels}")

        # Get pixel data
        current_pixels = current_img.load()
        previous_pixels = previous_img.load()

        # Find changed pixels
        # Both images are in RGB mode at this point
        logger.info(f"_compare_images_and_find_regions: Scanning for changed pixels...")
        changed_pixels_set = set()
        for y in range(height):
            for x in range(width):
                if current_pixels[x, y] != previous_pixels[x, y]:
                    changed_pixels_set.add((x, y))

        changed_pixel_count = len(changed_pixels_set)
        change_ratio = changed_pixel_count / total_pixels if total_pixels > 0 else 0
        logger.info(f"_compare_images_and_find_regions: Changed pixels: {changed_pixel_count}/{total_pixels} ({change_ratio*100:.2f}%), threshold: {threshold*100:.2f}%")

        # If no changes, return identical
        if changed_pixel_count == 0:
            logger.info(f"_compare_images_and_find_regions: No changed pixels, returning 'identical'")
            return ('identical', None)

        # If too many changes, return full refresh
        if change_ratio > threshold:
            logger.info(f"_compare_images_and_find_regions: Change ratio {change_ratio*100:.2f}% exceeds threshold {threshold*100:.2f}%, returning 'full'")
            return ('full', None)

        # Find connected components (separate regions)
        logger.info(f"_compare_images_and_find_regions: Finding connected components...")
        components = _find_connected_components(changed_pixels_set, width, height)
        logger.info(f"_compare_images_and_find_regions: Found {len(components)} connected component(s)")

        if not components:
            logger.info(f"_compare_images_and_find_regions: No components found, returning 'identical'")
            return ('identical', None)

        # Create bounding boxes for each component
        bounding_boxes = []
        for i, component in enumerate(components):
            if not component:
                continue

            min_x = min(p[0] for p in component)
            max_x = max(p[0] for p in component)
            min_y = min(p[1] for p in component)
            max_y = max(p[1] for p in component)
            logger.info(f"_compare_images_and_find_regions: Component {i+1}: {len(component)} pixels, bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")

            # Add padding around changed region (10 pixels)
            padding = 10
            x1 = max(0, min_x - padding)
            y1 = max(0, min_y - padding)
            x2 = min(width, max_x + padding + 1)
            y2 = min(height, max_y + padding + 1)

            bounding_boxes.append({
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            })

        # Merge close regions
        logger.info(f"_compare_images_and_find_regions: Merging close regions (threshold: {merge_threshold}px)...")
        merged_boxes = _merge_close_regions(bounding_boxes, merge_threshold)
        logger.info(f"_compare_images_and_find_regions: After merging: {len(merged_boxes)} region(s)")

        img_width, img_height = width, height

        # Extract regions and encode them
        regions = []
        for box in merged_boxes:
            x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']

            # Align coordinates to 8-pixel boundaries for byte alignment
            # (1 bit per pixel = 8 pixels per byte)
            x1 = (max(0, x1) // 8) * 8
            y1 = (max(0, y1) // 8) * 8
            x2 = (min(img_width, (x2 + 7) // 8 * 8) // 8) * 8
            y2 = (min(img_height, (y2 + 7) // 8 * 8) // 8) * 8
            if x2 <= x1:
                x2 = min(img_width, x1 + 8)
            if y2 <= y1:
                y2 = min(img_height, y1 + 8)

            # Extract region from current image
            region_img = current_img.crop((x1, y1, x2, y2))

            # Convert to raw 1-bit packed bytes for Waveshare display:
            # Each byte = 8 horizontal pixels, row-major, (aligned_width) * height bytes
            # Convention: 0 = black, 1 = white (invert bit if your display expects opposite)
            region_img = region_img.convert('L')  # grayscale
            width, height = region_img.size
            aligned_width_bytes = (width + 7) // 8
            packed = bytearray()
            pixels = region_img.load()
            for y in range(height):
                for byte_x in range(aligned_width_bytes):
                    b = 0
                    for bit in range(8):
                        px = byte_x * 8 + bit
                        if px < width:
                            # 0 = black (ink), 1 = white (no ink)
                            b |= (1 << (7 - bit)) if pixels[px, y] > 128 else 0
                    packed.append(b)

            # Encode as base64
            region_base64 = base64.b64encode(bytes(packed)).decode('utf-8')

            regions.append({
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'data': region_base64
            })

        logger.info(f"_compare_images_and_find_regions: Returning 'partial' with {len(regions)} region(s)")
        return ('partial', (regions, changed_pixel_count, total_pixels))

    except Exception as e:
        logger.error(f"_compare_images_and_find_regions: Error comparing images: {e}", exc_info=True)
        return ('full', None)


@require_http_methods(["GET"])
def weather_view(request):
    """
    Get weather information and render an SVG chart showing hourly temperature forecast.
    Returns a BMP image (converted from SVG) with a grayscale temperature chart (800x480 pixels).
    Fetches exactly 24 hours of hourly forecast data.
    Supports skip when unchanged (same hour) via lastHash comparison.
    When the image changes, always returns full refresh (no partial).

    Query parameters:
    - key: Required. Must match TABLET_KEY environment variable.
    - lat: Required. Latitude coordinate (float)
    - lon: Required. Longitude coordinate (float)
    - lastHash: Optional. Hash of the previous image to skip refresh when unchanged.

    Returns:
    - Full refresh: BMP image with X-Update-Type: full, X-Image-Hash headers
    - Skip: 204 No Content with X-Update-Type: skip, X-Image-Hash headers (when unchanged)
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    tablet_key = os.getenv('TABLET_KEY')
    if not key or not tablet_key or key != tablet_key:
        return _add_poll_interval_header(JsonResponse({'error': 'Not found'}, status=404), config.TABLET_WEATHER_POLL_INTERVAL)

    try:
        # Get lat/lon from query parameters (required for cache key)
        lat_str = request.GET.get('lat')
        lon_str = request.GET.get('lon')

        if not lat_str or not lon_str:
            return _add_poll_interval_header(JsonResponse({
                'error': 'Missing required parameters: Both lat and lon parameters are required'
            }, status=400), config.TABLET_WEATHER_POLL_INTERVAL)

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return _add_poll_interval_header(JsonResponse({
                'error': 'Invalid coordinate format: lat and lon must be valid floating point numbers'
            }, status=400), config.TABLET_WEATHER_POLL_INTERVAL)

        # Check cache FIRST before any API calls or processing
        # Set up cache directory and filename
        current_time = timezone.now()
        current_file = Path(__file__).resolve()
        cache_dir = current_file.parent / 'cache' / 'weather_bmp'
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with date, hour, and rounded lat/lon (e.g., weather_chart_2024-01-15_14_40.71_-74.01.bmp)
        date_hour_str = current_time.strftime('%Y-%m-%d_%H')
        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)
        cache_filename = f'weather_chart_{date_hour_str}_{lat_rounded}_{lon_rounded}.bmp'
        cache_filepath = cache_dir / cache_filename

        # Check if cached file exists for current hour and coordinates
        if cache_filepath.exists():
            try:
                with open(cache_filepath, 'rb') as f:
                    cached_bmp_bytes = f.read()
                logger.info(f"Returning cached BMP file: {cache_filename}")

                # Apply same hash/cache/skip logic as for newly generated images
                current_hash = _generate_image_hash(cached_bmp_bytes)
                _weather_image_cache[current_hash] = cached_bmp_bytes
                if len(_weather_image_cache) > _MAX_CACHE_SIZE:
                    oldest_key = next(iter(_weather_image_cache))
                    del _weather_image_cache[oldest_key]

                last_hash = request.GET.get('lastHash')
                if last_hash and last_hash in _weather_image_cache and current_hash == last_hash:
                    response = HttpResponse(status=204)
                    response['X-Update-Type'] = 'skip'
                    response['X-Image-Hash'] = current_hash
                    return _add_poll_interval_header(response, config.TABLET_WEATHER_POLL_INTERVAL)

                response = HttpResponse(cached_bmp_bytes, content_type='image/bmp')
                response['X-Update-Type'] = 'full'
                response['X-Image-Hash'] = current_hash
                response['Content-Disposition'] = f'inline; filename="{cache_filename}"'
                return _add_poll_interval_header(response, config.TABLET_WEATHER_POLL_INTERVAL)
            except Exception as e:
                logger.warning(f"Error reading cached file {cache_filename}: {e}, will regenerate")

        # Get Tomorrow.io API key from environment
        api_key = os.getenv('TOMORROW_IO_API_KEY')
        if not api_key:
            return _add_poll_interval_header(JsonResponse({
                'error': 'Weather service configuration error: Tomorrow.io API key not configured'
            }, status=500), config.TABLET_WEATHER_POLL_INTERVAL)

        bmp_bytes, context = render_weather_chart_bmp(lat, lon, api_key)
        if not bmp_bytes and not context:
            return _add_poll_interval_header(JsonResponse({
                'error': 'Failed to fetch hourly forecast'
            }, status=500), config.TABLET_WEATHER_POLL_INTERVAL)

        # Clean up old cached files
        try:
            for existing_file in cache_dir.glob('weather_chart_*.bmp'):
                if existing_file.name != cache_filename:
                    try:
                        existing_file.unlink()
                        logger.info(f"Deleted old cached file: {existing_file.name}")
                    except Exception as e:
                        logger.warning(f"Error deleting old cached file {existing_file.name}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up old cache files: {e}")

        if bmp_bytes:
            # Save to disk cache
            try:
                with open(cache_filepath, 'wb') as f:
                    f.write(bmp_bytes)
                logger.info(f"Cached BMP file: {cache_filename}")
            except Exception as e:
                logger.warning(f"Error saving BMP to cache {cache_filename}: {e}")

            # Generate hash and add to in-memory cache for skip-when-unchanged
            current_hash = _generate_image_hash(bmp_bytes)
            _weather_image_cache[current_hash] = bmp_bytes
            if len(_weather_image_cache) > _MAX_CACHE_SIZE:
                oldest_key = next(iter(_weather_image_cache))
                del _weather_image_cache[oldest_key]

            last_hash = request.GET.get('lastHash')
            if last_hash and last_hash in _weather_image_cache and current_hash == last_hash:
                response = HttpResponse(status=204)
                response['X-Update-Type'] = 'skip'
                response['X-Image-Hash'] = current_hash
                return _add_poll_interval_header(response, config.TABLET_WEATHER_POLL_INTERVAL)

            # Full refresh (no lastHash, hash not in cache, or image changed)
            response = HttpResponse(bmp_bytes, content_type='image/bmp')
            response['X-Update-Type'] = 'full'
            response['X-Image-Hash'] = current_hash
            response['Content-Disposition'] = f'inline; filename="weather_chart_{lat}_{lon}.bmp"'
            return _add_poll_interval_header(response, config.TABLET_WEATHER_POLL_INTERVAL)

        # Fallback to SVG if BMP rendering fails
        logger.warning("Failed to render SVG to BMP, falling back to SVG")
        return _add_poll_interval_header(render(request, 'tablet/weather_chart.svgt', context), config.TABLET_WEATHER_POLL_INTERVAL)

    except Exception as e:
        logger.error(f"Error in weather view", e)
        return _add_poll_interval_header(JsonResponse({
            'error': 'Failed to fetch weather information',
            'details': str(e)
        }, status=500), config.TABLET_WEATHER_POLL_INTERVAL)


def get_dashboard_status():
    """
    Determine which dashboard to show based on current time and skip periods.

    Returns 'bus' dashboard during specific time windows on weekdays:
    - Morning: 6:48 AM to 6:55 AM
    - Afternoon: 2:38 PM to 2:45 PM

    Returns 'weather' dashboard at all other times.

    Date ranges configured in BusDashboardSkip model will override and force 'weather'.

    Returns:
        str: 'bus' or 'weather'
    """
    # Get current time in America/New_York timezone
    eastern_tz = ZoneInfo('America/New_York')
    now_utc = timezone.now()
    now_eastern = now_utc.astimezone(eastern_tz)

    current_date = now_eastern.date()
    current_time = now_eastern.time()
    current_weekday = now_eastern.weekday()  # 0 = Monday, 6 = Sunday

    # Check if current date falls within any skip periods
    skip_periods = BusDashboardSkip.objects.filter(is_active=True)
    for skip_period in skip_periods:
        if skip_period.contains_date(current_date):
            return 'weather'

    # Check if it's a weekday (Monday = 0, Friday = 4)
    is_weekday = current_weekday < 5

    if not is_weekday:
        return 'weather'

    # Define bus time windows
    morning_start = time(6, 48)  # 6:48 AM
    morning_end = time(6, 55)    # 6:55 AM
    afternoon_start = time(14, 38)  # 2:38 PM
    afternoon_end = time(14, 45)    # 2:45 PM

    # Check if current time is within bus windows
    in_morning_window = morning_start <= current_time <= morning_end
    in_afternoon_window = afternoon_start <= current_time <= afternoon_end

    if in_morning_window or in_afternoon_window:
        return 'bus'
    return 'weather'


@require_http_methods(["GET"])
def status_view(request):
    """
    Get the current dashboard status (bus or weather).

    Returns 'bus' dashboard during specific time windows on weekdays:
    - Morning: 6:48 AM to 6:55 AM
    - Afternoon: 2:38 PM to 2:45 PM

    Returns 'weather' dashboard at all other times.

    Date ranges configured in BusDashboardSkip model will override and force 'weather'.

    Query parameters:
    - key: Required. Must match TABLET_KEY environment variable.
    """
    # Check if key is provided and matches TABLET_KEY environment variable
    key = request.GET.get('key')
    tablet_key = os.getenv('TABLET_KEY')
    if not key or not tablet_key or key != tablet_key:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        eastern_tz = ZoneInfo('America/New_York')
        now_eastern = timezone.now().astimezone(eastern_tz)

        response_data = {
            'dashboard': get_dashboard_status(),
            'current_time': now_eastern.isoformat(),
            'current_time_readable': now_eastern.strftime('%Y-%m-%d %I:%M:%S %p') + ' ' + str(eastern_tz),
            'timezone': 'America/New_York'
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in status view: {e}")
        return JsonResponse({
            'error': 'Failed to get dashboard status',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def test_client_view(request):
    """
    Serves the HTML test client page at /tablet/?key=<tablet_key>.
    The page mimics real client behavior: polls /tablet/dashboard/ with lat/lon,
    displays 800x480 image or error JSON, shows response headers and X-Poll-Interval countdown.
    """
    return render(request, 'tablet/test_client.html')


@require_http_methods(["GET"])
def dashboard_view(request):
    """
    Route to the appropriate dashboard (bus or weather) based on current status.

    Delegates to bus_view during bus time windows on weekdays, weather_view otherwise.
    Client should include lat/lon query params when the result may be weather.

    Query parameters:
    - key: Required. Must match TABLET_KEY environment variable.
    - lat, lon: Required when weather dashboard is shown.
    - lastHash: Optional. Passed through for partial refresh (bus) or skip-when-unchanged (weather).
    - debug: Optional. Passed through to bus_view when applicable.
    """
    key = request.GET.get('key')
    tablet_key = os.getenv('TABLET_KEY')
    if not key or not tablet_key or key != tablet_key:
        return JsonResponse({'error': 'Not found'}, status=404)

    status = get_dashboard_status()

    if status == 'bus':
        return bus_view(request)
    else:
        return weather_view(request)
