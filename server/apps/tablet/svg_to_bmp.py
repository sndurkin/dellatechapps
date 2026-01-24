"""
Helper module for converting SVG templates to BMP images.
Uses CairoSVG for SVG rendering and PIL for PNG to BMP conversion.
"""
import io
import logging
import cairosvg
from PIL import Image
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

        # Convert SVG to PNG using CairoSVG
        # output_width and output_height specify the output dimensions
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=width,
            output_height=height
        )

        # Convert PNG to BMP using PIL
        img = Image.open(io.BytesIO(png_bytes))
        bmp_buffer = io.BytesIO()
        img.save(bmp_buffer, format='BMP')
        bmp_buffer.seek(0)

        return bmp_buffer.getvalue()

    except Exception as e:
        logger.error(f"Error converting SVG template to BMP: {e}", exc_info=True)
        return None
