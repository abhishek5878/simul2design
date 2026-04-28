"""HTML → PNG render via Playwright (lazy-imported).

Importing this module does NOT require playwright. The dependency is only
checked when `render_variant_png` is called. Callers without the render
extra installed see a single, actionable error.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from simul2design.render.html_template import render_variant_html


class RenderUnavailableError(RuntimeError):
    """Raised when the render extra (`pip install simul2design[render]`) is
    not installed and a PNG render is attempted."""


_PLAYWRIGHT_INSTALL_HINT = (
    "Playwright is required for PNG rendering but isn't installed. Run:\n"
    "  pip install 'simul2design[render]'\n"
    "  playwright install chromium\n"
    "Or use simul2design.render.render_variant_html(...) for HTML-only output."
)


def _import_sync_playwright():
    """Lazy import. Raises RenderUnavailableError on ImportError."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RenderUnavailableError(_PLAYWRIGHT_INSTALL_HINT) from e
    return sync_playwright


def render_variant_png(
    synthesized_variant: dict,
    *,
    variant_name: str = "V_next",
    headline: str = "Get the trade idea your portfolio is missing",
    subhead: str = "One real, closed trade — yours to keep, refunded if it doesn't deliver.",
    footer: bool = False,
    viewport: tuple[int, int] = (375, 812),
    output_path: Optional[str | Path] = None,
    device_scale_factor: float = 2.0,
) -> bytes:
    """Render the synthesized variant to a PNG.

    Args:
        synthesized_variant: The cascade's `synthesized_variant` dict.
        variant_name / headline / subhead / footer: passed through to
            `render_variant_html`.
        viewport: (width, height) in CSS pixels. Default 375×812 (iPhone-ish).
        output_path: If given, also write the PNG to this path. The bytes are
            still returned regardless.
        device_scale_factor: 2.0 = retina (default). 1.0 for crisper text on
            non-retina displays. 3.0 for high-DPI marketing.

    Returns:
        Raw PNG bytes.

    Raises:
        RenderUnavailableError: if `simul2design[render]` extras aren't installed.
    """
    sync_playwright = _import_sync_playwright()

    html_str = render_variant_html(
        synthesized_variant,
        variant_name=variant_name,
        headline=headline,
        subhead=subhead,
        footer=footer,
    )

    width, height = viewport
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=device_scale_factor,
            )
            page = context.new_page()
            page.set_content(html_str, wait_until="load")
            png_bytes = page.screenshot(full_page=True, type="png")
        finally:
            browser.close()

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(png_bytes)

    return png_bytes
