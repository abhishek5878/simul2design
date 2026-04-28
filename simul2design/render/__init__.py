"""Variant render — synthesized_variant dict → HTML and PNG.

Public API:
    render_variant_html(synthesized_variant, ...) -> str
        Pure Python; no browser dep. Always available.

    render_variant_png(synthesized_variant, ...) -> bytes
        Requires `pip install simul2design[render]` and
        `playwright install chromium`. Raises RenderUnavailableError otherwise.
"""

from simul2design.render.html_template import render_variant_html
from simul2design.render.visual import RenderUnavailableError, render_variant_png

__all__ = [
    "render_variant_html",
    "render_variant_png",
    "RenderUnavailableError",
]
