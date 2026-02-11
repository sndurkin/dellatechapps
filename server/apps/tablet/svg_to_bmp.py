"""
Helper module for converting SVG templates to BMP images.
Uses CairoSVG for SVG rendering and PIL for PNG to BMP conversion.
"""
import io
import logging
import cairosvg
from PIL import Image, ImageFilter
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def render_svg_to_bmp(template_name, context, width=800, height=480):
    """
    Render a Django SVG template and convert it to a BMP image.

    Args:
        template_name (str): Name of the SVG template to render (e.g., 'tablet/weather_chart.svgt')
        context (dict): Template context dictionary
        width (int): Viewport width in pixels (default: 800)
        height (int): Viewport height in pixels (default: 480)

    Returns:
        bytes: BMP image bytes, or None if rendering failed
    """

    try:
        # Render template to SVG string
        svg_content = render_to_string(template_name, context)

        # Convert SVG to PNG at a higher resolution so that after downscale + threshold,
        # the same digits render identically (avoids anti-alias position-dependent differences)
        scale = 8
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=width * scale,
            output_height=height * scale
        )

        # Grayscale, downscale, then threshold to 1-bit.
        img = Image.open(io.BytesIO(png_bytes)).convert('L')
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        img = img.point(lambda p: 255 if p >= 128 else 0, mode='1')
        bmp_buffer = io.BytesIO()
        img.save(bmp_buffer, format='BMP')
        bmp_buffer.seek(0)

        return bmp_buffer.getvalue()

    except Exception as e:
        logger.error(f"Error converting SVG template to BMP: {e}", exc_info=True)
        return None
