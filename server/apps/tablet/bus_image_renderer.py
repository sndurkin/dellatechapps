from PIL import Image, ImageDraw
import os
import io
import json

# Cache for fixed palettes per map image
_palette_cache = {}


def _get_fixed_palette_image(base_image):
    """
    Generate or retrieve a fixed palette image for a base image.
    This ensures consistent palette mapping across renders.
    Returns a quantized palette-mode image that can be used as a reference.
    """
    # Use image size as cache key (assuming same size = same base image)
    cache_key = base_image.size

    if cache_key not in _palette_cache:
        # Convert to RGB if needed
        if base_image.mode != 'RGB':
            rgb_image = base_image.convert('RGB')
        else:
            rgb_image = base_image

        # Create a fixed palette from the base image
        # Use quantize to create a deterministic palette
        # MEDIANCUT should be deterministic for the same input
        palette_image = rgb_image.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        _palette_cache[cache_key] = palette_image

        return palette_image
    else:
        return _palette_cache[cache_key]


def load_image_coords():
    """
    Load image coordinates from JSON file.
    Start is SW point, End is NE point.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    coords_path = os.path.join(current_dir, "assets", "image_coords.json")

    try:
        with open(coords_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Image coordinates file {coords_path} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing image coordinates JSON: {e}")
        return []


# Load image coordinates at module level
image_coords = load_image_coords()


def render_icon_at_coordinates(lat, lon, return_bytes=False):
    """
    Render an icon at the given lat/lon coordinates on the appropriate image.

    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        return_bytes (bool): If True, return image bytes. If False, return file path (legacy behavior).

    Returns:
        bytes or str or None:
        - If return_bytes=True: Image bytes as BMP format, or None if coordinates don't match any bounds
        - If return_bytes=False: Path to the saved image file, or None if coordinates don't match any bounds
    """
    # Iterate from end to beginning to find first matching bounds
    for idx in range(len(image_coords) - 1, -1, -1):
        bounds = image_coords[idx]
        start_lat, start_lon = bounds['start']
        end_lat, end_lon = bounds['end']

        # Check if coordinates are within bounds
        # Note: start/end might not be min/max, so we need to handle both cases
        min_lon, max_lon = min(start_lon, end_lon), max(start_lon, end_lon)
        min_lat, max_lat = min(start_lat, end_lat), max(start_lat, end_lat)

        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
            # Found matching bounds, load the corresponding image
            # Get the directory where this Python file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "assets", f"{idx}.png")

            if not os.path.exists(image_path):
                print(f"Warning: Image file {image_path} not found")
                continue

            # Load the image
            img = Image.open(image_path)

            width, height = img.size

            # Calculate position within image
            # Map lat/lon to pixel coordinates
            x_ratio = (lon - min_lon) / (max_lon - min_lon)
            y_ratio = (lat - min_lat) / (max_lat - min_lat)

            # Convert to pixel coordinates (note: y is flipped for image coordinates)
            pixel_x = int(x_ratio * width)
            pixel_y = int((1 - y_ratio) * height)  # Flip Y axis

            # Create a copy of the image to draw on
            img_with_icon = img.copy()
            draw = ImageDraw.Draw(img_with_icon)

            # Load and place pre-made bus icon PNG
            bus_icon = None
            try:
                # Load the bus icon from the assets directory
                icon_path = os.path.join(current_dir, "assets", "bus_icon.png")

                if os.path.exists(icon_path):
                    bus_icon = Image.open(icon_path)

                    # Convert to RGBA if not already (for transparency support)
                    if bus_icon.mode != 'RGBA':
                        bus_icon = bus_icon.convert('RGBA')

                    # Get icon dimensions
                    icon_width, icon_height = bus_icon.size

                    # Calculate position to center the icon
                    paste_x = pixel_x - icon_width // 2
                    paste_y = pixel_y - icon_height // 2

                    # Paste the icon onto the image
                    img_with_icon.paste(bus_icon, (paste_x, paste_y), bus_icon)
                else:
                    print(f"Warning: Image file {icon_path} not found")
            except Exception as e:
                pass

            # Fallback: draw a simple white circle with black border if there's any error
            if bus_icon is None:
                icon_radius = 5
                draw.ellipse([
                    pixel_x - icon_radius - 1, pixel_y - icon_radius - 1,
                    pixel_x + icon_radius + 1, pixel_y + icon_radius + 1
                ], fill='black', outline='black')
                draw.ellipse([
                    pixel_x - icon_radius, pixel_y - icon_radius,
                    pixel_x + icon_radius, pixel_y + icon_radius
                ], fill='white', outline='white')
                print(f"Error loading bus icon: {e}, using fallback circle")

            # Convert to 8-bit palette mode for smaller file size
            # Convert to RGB first if image has transparency (RGBA)
            if img_with_icon.mode == 'RGBA':
                # Create a white background and paste the image onto it
                rgb_img = Image.new('RGB', img_with_icon.size, (255, 255, 255))
                rgb_img.paste(img_with_icon, mask=img_with_icon.split()[3])  # Use alpha channel as mask
                img_with_icon = rgb_img
            elif img_with_icon.mode != 'RGB':
                img_with_icon = img_with_icon.convert('RGB')

            # Use a fixed palette based on the base map image (before bus icon was added)
            # This ensures consistent palette mapping and prevents false differences
            # when only the bus icon position changes
            base_img_rgb = img.convert('RGB') if img.mode != 'RGB' else img
            fixed_palette_image = _get_fixed_palette_image(base_img_rgb)

            # Quantize the image with the bus icon using the fixed palette as reference
            # This ensures the same colors map to the same palette indices
            # The fixed palette prevents adaptive palette recalculation that causes
            # false pixel differences when only the bus icon position changes
            try:
                img_with_icon = img_with_icon.quantize(palette=fixed_palette_image)
            except TypeError:
                # Fallback for older PIL versions that don't support palette parameter
                # Apply the fixed palette manually
                img_with_icon = img_with_icon.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                img_with_icon.putpalette(fixed_palette_image.palette)

            if return_bytes:
                # Return image as bytes (BMP format)
                img_buffer = io.BytesIO()
                img_with_icon.save(img_buffer, format='BMP')
                img_buffer.seek(0)
                print(f"Icon rendered at ({pixel_x}, {pixel_y}) and returned as bytes")
                return img_buffer.getvalue()
            else:
                # Legacy behavior: save to file
                output_filename = f"rendered_{lat}_{lon}_{idx}.bmp"
                output_filename = os.path.join(current_dir, output_filename)
                img_with_icon.save(output_filename, format='BMP')
                print(f"Icon rendered at ({pixel_x}, {pixel_y}) and saved to {output_filename}")
                return output_filename

    print(f"No matching bounds found for coordinates ({lat}, {lon})")
    return None


