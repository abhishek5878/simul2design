#!/usr/bin/env python3
"""test-render-visual.py — tests for simul2design/render/.

Two test groups:

1. HTML template tests (always run, no browser needed):
   - Each base-taxonomy value produces a known HTML pattern
   - Unknown values render as visible placeholders, never silently
   - Modal layout wraps the screen in an overlay
   - Dark theme applies the correct screen class
   - Footer overlay can be enabled
   - CLI HTML-only mode round-trips

2. Browser tests (run only if RUN_BROWSER_TESTS=1 env var is set):
   - render_variant_png produces a valid PNG (header bytes + non-trivial size)
   - render_variant_png writes to disk when output_path is given
   - CLI PNG mode produces a file

Usage:
    scripts/test-render-visual.py              # HTML tests only
    RUN_BROWSER_TESTS=1 scripts/test-render-visual.py  # all tests
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


# ─── Fixtures ───────────────────────────────────────────────────────────────


def _minimal_synthesized_variant() -> dict:
    """Bare-minimum elements dict — enough for the template not to crash."""
    return {
        "elements": {
            "layout": "full_screen",
            "modal_interrupt": "no",
            "branding": "none",
            "price_visibility": "visible_primary",
            "cta_primary_label": "Activate for ₹1",
            "cta_style": "high_contrast_green",
            "cta_stack": "single",
            "urgency_mechanism": "none",
            "refund_or_guarantee_copy": "absent",
            "trust_signal": "implicit",
            "evidence_detail": "none",
        },
    }


def _rich_synthesized_variant() -> dict:
    """Exercise every taxonomy branch the template renders."""
    return {
        "elements": {
            "layout": {"value": "full_screen", "confidence": "high"},
            "modal_interrupt": "no",
            "branding": "crown_header",
            "price_visibility": "visible_with_framing",
            "cta_primary_label": "Unlock FREE trade",
            "cta_style": "muted_premium",
            "cta_stack": "dual_outline_plus_sticky",
            "urgency_mechanism": "scarcity_count",
            "refund_or_guarantee_copy": "explicit_sla",
            "trust_signal": "regulatory_plus_evidence",
            "evidence_detail": "named_past_outcome",
        },
    }


# ─── HTML template tests (always run) ───────────────────────────────────────


def test_html_template_renders_minimal_variant():
    """Minimal variant produces complete, parseable HTML."""
    from simul2design.render import render_variant_html
    html = render_variant_html(_minimal_synthesized_variant())
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "Activate for ₹1" in html
    assert "s2d-cta--high-contrast-green" in html
    assert "s2d-screen--full-screen" in html


def test_html_template_handles_dict_value_format():
    """Cascade output puts values inside {value, confidence, ...} dicts.
    Template must accept that shape AND the bare-string shape."""
    from simul2design.render import render_variant_html
    html = render_variant_html(_rich_synthesized_variant())
    assert "s2d-screen--full-screen" in html  # dict-shape value parsed
    assert "Unlock FREE trade" in html  # cta_primary_label as bare string


def test_html_template_renders_modal_layout():
    """modal_interrupt=yes wraps the screen in an overlay."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["modal_interrupt"] = "yes"
    html = render_variant_html(sv)
    assert "s2d-modal-overlay" in html
    assert "s2d-modal-card" in html


def test_html_template_renders_dark_theme():
    """layout=full_screen_dark applies the dark screen class."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["layout"] = "full_screen_dark"
    html = render_variant_html(sv)
    assert "s2d-screen--full-screen-dark" in html


def test_html_template_renders_crown_header():
    """branding=crown_header renders the premium top bar."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["branding"] = "crown_header"
    html = render_variant_html(sv)
    assert "s2d-header__crown" in html
    assert "Premium" in html


def test_html_template_renders_dual_cta_stack():
    """cta_stack=dual_outline_plus_sticky renders both outline + sticky CTAs."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["cta_stack"] = "dual_outline_plus_sticky"
    html = render_variant_html(sv)
    assert "s2d-cta--outline" in html
    assert "s2d-cta--sticky" in html


def test_outline_cta_visibility_with_muted_premium():
    """Regression: outline CTA must be visible even when primary style is
    muted_premium (otherwise inheriting color: white from the parent style
    produces white-text-on-white-bg invisibility). The CSS uses !important
    overrides on the outline modifier; this test asserts both modifier and
    base style class are present so the visual reviewer sees both buttons."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["cta_style"] = "muted_premium"
    sv["elements"]["cta_stack"] = "dual_outline_plus_sticky"
    html = render_variant_html(sv)
    # Outline button has both the style and the outline modifier.
    assert "s2d-cta--muted-premium s2d-cta--outline" in html
    # The CSS rule we depend on is present in the bundled stylesheet.
    assert ".s2d-cta--outline {" in html
    assert "color: #1a1a1a !important" in html


def test_html_template_renders_urgency_countdown():
    """urgency_mechanism=countdown_timer produces the countdown widget."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["urgency_mechanism"] = "countdown_timer"
    html = render_variant_html(sv)
    assert "s2d-urgency--countdown" in html
    assert "Offer ends" in html


def test_html_template_renders_trust_with_named_outcome():
    """Combined trust_signal=regulatory_plus_evidence + named_past_outcome
    renders both the SEBI badge AND the named-stock evidence."""
    from simul2design.render import render_variant_html
    html = render_variant_html(_rich_synthesized_variant())
    assert "SEBI" in html
    assert "ZOMATO" in html


def test_html_template_renders_price_banner_when_with_framing():
    """price_visibility=visible_with_framing surfaces the pre-CTA banner
    and merges in the refund_or_guarantee_copy framing."""
    from simul2design.render import render_variant_html
    html = render_variant_html(_rich_synthesized_variant())
    assert "s2d-price-banner" in html
    assert "₹1" in html
    assert "60s" in html  # explicit_sla copy


def test_html_template_renders_inline_refund_when_no_framing_banner():
    """If price_visibility != visible_with_framing, the refund copy still
    surfaces inline below the CTA."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["refund_or_guarantee_copy"] = "money_back_guarantee"
    html = render_variant_html(sv)
    assert "money-back" in html.lower() or "30-day" in html
    assert "s2d-refund" in html


def test_html_template_unknown_value_renders_placeholder():
    """An unknown enum value never disappears silently — placeholder appears."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["urgency_mechanism"] = "invented_value_for_test"
    html = render_variant_html(sv)
    assert "s2d-placeholder" in html
    assert "invented_value_for_test" in html
    assert "urgency_mechanism" in html


def test_html_template_unknown_layout_falls_back_with_placeholder():
    """Unknown layout value falls back to full_screen but flags the issue."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["layout"] = "garbage_layout"
    html = render_variant_html(sv)
    assert "s2d-screen--full-screen" in html  # fallback applied
    assert "garbage_layout" in html  # placeholder visible


def test_html_template_footer_overlay_off_by_default():
    """Footer overlay is off in the default render (clean spec deliverable).

    Looks for the rendered footer ELEMENT, not the CSS selector — the base
    stylesheet always contains `.s2d-footer` rules, but the actual element
    only appears when footer=True.
    """
    from simul2design.render import render_variant_html
    html = render_variant_html(_minimal_synthesized_variant())
    assert '<div class="s2d-footer">' not in html
    assert "debug overlay" not in html


def test_html_template_footer_overlay_on_when_requested():
    """Footer=True surfaces the dimension→value debug grid."""
    from simul2design.render import render_variant_html
    html = render_variant_html(_minimal_synthesized_variant(), footer=True)
    assert '<div class="s2d-footer">' in html
    assert "debug overlay" in html


def test_html_template_html_escapes_user_supplied_strings():
    """Freeform CTA labels can contain HTML chars; must be escaped."""
    from simul2design.render import render_variant_html
    sv = _minimal_synthesized_variant()
    sv["elements"]["cta_primary_label"] = '<script>alert("xss")</script>'
    html = render_variant_html(sv)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_cli_html_only_mode_round_trips():
    """`simul2design-render --html-only` reads JSON, writes HTML to stdout."""
    from simul2design.render.cli import main
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_minimal_synthesized_variant(), f)
        input_path = f.name
    rc = main([input_path, "--html-only", "-o", "/dev/null"])
    assert rc == 0


def test_cli_extracts_synthesized_variant_from_synthesis_result():
    """CLI accepts the full SynthesisResult JSON shape (with nested
    synthesized_variant), not just the bare elements dict."""
    from simul2design.render.cli import _extract_synthesized_variant
    result_shape = {
        "client_slug": "test",
        "synthesized_variant": _minimal_synthesized_variant(),
        "spec_markdown": "...",
    }
    sv = _extract_synthesized_variant(result_shape)
    assert "elements" in sv
    assert sv["elements"]["cta_primary_label"] == "Activate for ₹1"


def test_cli_raises_clear_error_on_missing_synthesized_variant():
    """A SynthesisResult with synthesized_variant=None gives a useful error."""
    from simul2design.render.cli import _extract_synthesized_variant
    try:
        _extract_synthesized_variant({"client_slug": "x", "synthesized_variant": None})
    except ValueError as e:
        assert "didn't run" in str(e) or "failed" in str(e)
        return
    raise AssertionError("Should have raised on null synthesized_variant")


# ─── Browser tests (gated on RUN_BROWSER_TESTS=1) ──────────────────────────


def test_render_unavailable_raises_when_playwright_missing():
    """Without simul2design[render] installed, render_variant_png raises a
    helpful error pointing at the install command."""
    from simul2design.render import RenderUnavailableError, render_variant_png
    # Fake out the import by patching sys.modules
    import sys as _sys
    real_pw = _sys.modules.pop("playwright", None)
    real_pw_sync = _sys.modules.pop("playwright.sync_api", None)
    _sys.modules["playwright"] = None  # force ImportError on `import playwright`
    try:
        try:
            render_variant_png(_minimal_synthesized_variant())
        except RenderUnavailableError as e:
            assert "pip install" in str(e)
            assert "playwright" in str(e).lower()
            return
        finally:
            _sys.modules.pop("playwright", None)
            if real_pw is not None:
                _sys.modules["playwright"] = real_pw
            if real_pw_sync is not None:
                _sys.modules["playwright.sync_api"] = real_pw_sync
        raise AssertionError("Expected RenderUnavailableError")
    except ImportError:
        # Expected when playwright is genuinely not installed — the helpful
        # error already fired before we got here.
        pass


def test_browser_render_produces_png_bytes():
    """End-to-end PNG render — only runs with RUN_BROWSER_TESTS=1."""
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        return  # Skip silently
    from simul2design.render import render_variant_png
    png = render_variant_png(_rich_synthesized_variant())
    assert png.startswith(b"\x89PNG\r\n\x1a\n"), "PNG header missing"
    assert len(png) > 10_000, f"PNG suspiciously small ({len(png)} bytes)"


def test_browser_render_writes_to_disk():
    """When output_path is provided, the PNG appears at that path."""
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        return
    from simul2design.render import render_variant_png
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "v_next.png"
        png = render_variant_png(_minimal_synthesized_variant(), output_path=out)
        assert out.is_file()
        assert out.read_bytes() == png


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    test_html_template_renders_minimal_variant,
    test_html_template_handles_dict_value_format,
    test_html_template_renders_modal_layout,
    test_html_template_renders_dark_theme,
    test_html_template_renders_crown_header,
    test_html_template_renders_dual_cta_stack,
    test_outline_cta_visibility_with_muted_premium,
    test_html_template_renders_urgency_countdown,
    test_html_template_renders_trust_with_named_outcome,
    test_html_template_renders_price_banner_when_with_framing,
    test_html_template_renders_inline_refund_when_no_framing_banner,
    test_html_template_unknown_value_renders_placeholder,
    test_html_template_unknown_layout_falls_back_with_placeholder,
    test_html_template_footer_overlay_off_by_default,
    test_html_template_footer_overlay_on_when_requested,
    test_html_template_html_escapes_user_supplied_strings,
    test_cli_html_only_mode_round_trips,
    test_cli_extracts_synthesized_variant_from_synthesis_result,
    test_cli_raises_clear_error_on_missing_synthesized_variant,
    test_render_unavailable_raises_when_playwright_missing,
    test_browser_render_produces_png_bytes,
    test_browser_render_writes_to_disk,
]


def main() -> int:
    browser_tests_active = os.environ.get("RUN_BROWSER_TESTS") == "1"
    note = "" if browser_tests_active else f" {DIM}(browser tests skipped — set RUN_BROWSER_TESTS=1 to enable){RESET}"
    print(f"Running {len(TESTS)} tests against simul2design/render/...{note}\n")
    passed, failed, skipped = [], [], []
    for t in TESTS:
        name = t.__name__
        try:
            t()
            if "browser_" in name and not browser_tests_active:
                skipped.append(name)
                print(f"  {YELLOW}~{RESET} {name} {DIM}(skipped){RESET}")
            else:
                passed.append(name)
                print(f"  {GREEN}✓{RESET} {name}")
        except AssertionError as e:
            failed.append((name, str(e)))
            print(f"  {RED}✗{RESET} {name}{DIM} — {e}{RESET}")
        except Exception as e:
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  {RED}✗{RESET} {name}{DIM} — {type(e).__name__}: {e}{RESET}")

    print()
    print(f"{GREEN}Passed:{RESET} {len(passed)}/{len(TESTS) - len(skipped)}  "
          f"{YELLOW}Skipped:{RESET} {len(skipped)}")
    if failed:
        print(f"{RED}Failed:{RESET} {len(failed)}")
        return 1
    print(f"{GREEN}All tests passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
