"""Pure-Python taxonomy → HTML mapping for the V(N+1) variant render.

Takes a `synthesized_variant` dict (the cascade's chosen values per dimension)
and produces a single self-contained HTML string that `visual.py` rasterizes
to PNG via Playwright.

This module has zero browser dependency — it can be imported and exercised
without playwright installed. The output HTML is also viewable directly in
any browser, which makes the template iterable without re-rendering PNGs.

Design notes:
- Every base-taxonomy dimension (see `taxonomy_data/element-taxonomy-base.md`)
  has at least one branch in the dispatch tables below. Unknown values render
  as a labeled placeholder so the engineer immediately sees what wasn't
  templated, rather than a silent omission.
- Freeform values (cta_primary_label) render verbatim.
- The CSS class names use the convention `.s2d-<dimension>--<value>` so
  selectors line up 1:1 with taxonomy values.
"""

from __future__ import annotations

import html
from importlib.resources import files
from typing import Any

# ─── Helpers ────────────────────────────────────────────────────────────────


def _esc(s: Any) -> str:
    """HTML-escape an arbitrary value, coercing to str."""
    return html.escape(str(s if s is not None else ""))


def _value_of(elements: dict, dimension: str) -> Any:
    """Pull the value for a dimension out of synthesized_variant.elements.

    The synthesized_variant.elements dict from the cascade looks like:
        {"layout": {"value": "full_screen", "confidence": "high", ...}, ...}
    But callers may also pass the simpler {"layout": "full_screen", ...} shape
    from hand-built fixtures or downstream summaries.
    """
    raw = elements.get(dimension)
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def _placeholder(dimension: str, value: Any, *, hint: str = "") -> str:
    """Render an unknown / untemplated value as a visible placeholder.

    The engineer sees what was intended, not a silent gap.
    """
    suffix = f" — {_esc(hint)}" if hint else ""
    return (
        f'<div class="s2d-placeholder">'
        f'<span class="s2d-placeholder__label">{_esc(dimension)}</span>'
        f'{_esc(value)}{suffix}'
        f'</div>'
    )


def _load_base_css() -> str:
    """Load the bundled base.css. Raises FileNotFoundError if not packaged."""
    return (files("simul2design.render.template_assets") / "base.css").read_text(
        encoding="utf-8"
    )


# ─── Per-dimension renderers ────────────────────────────────────────────────


_LAYOUT_CLASSES = {
    "full_screen": "s2d-screen--full-screen",
    "full_screen_dark": "s2d-screen--full-screen-dark",
    "bottom_modal": "s2d-screen--bottom-modal",
    "inline": "s2d-screen--inline",
    "side_panel": "s2d-screen--side-panel",
}

_CTA_STYLE_CLASSES = {
    "neutral_default": "s2d-cta--neutral-default",
    "low_contrast_subordinate": "s2d-cta--low-contrast-subordinate",
    "high_contrast_warm": "s2d-cta--high-contrast-warm",
    "high_contrast_cool": "s2d-cta--high-contrast-cool",
    "high_contrast_green": "s2d-cta--high-contrast-green",
    "muted_premium": "s2d-cta--muted-premium",
    "text_link": "s2d-cta--text-link",
}

_URGENCY_TEMPLATES = {
    "countdown_timer": ("s2d-urgency--countdown", "⏱", "Offer ends in 04:23"),
    "scarcity_count": ("s2d-urgency--scarcity", "⚡", "Only 7 spots left"),
    "social_proof_realtime": ("s2d-urgency--social", "👥", "23 people viewing now"),
    "deadline_text": ("s2d-urgency--deadline", "📅", "Closes 30 Sep 2026"),
}

_REFUND_COPY = {
    "implicit_refund": "Refund available",
    "explicit_sla": "Full refund within 60s, no questions",
    "money_back_guarantee": "30-day money-back guarantee",
    "no_questions_asked": "No-questions-asked refund",
}


def _render_header(elements: dict) -> str:
    branding = _value_of(elements, "branding")
    if branding == "crown_header":
        return (
            '<div class="s2d-header">'
            '<span class="s2d-header__crown">♛</span>'
            '<span class="s2d-header__title">Premium</span>'
            '</div>'
        )
    if branding == "logo_only":
        return (
            '<div class="s2d-header">'
            '<div class="s2d-header__logo">LOGO</div>'
            '</div>'
        )
    if branding in (None, "none", ""):
        return ""
    return _placeholder("branding", branding)


def _render_trust(elements: dict) -> str:
    trust = _value_of(elements, "trust_signal")
    detail = _value_of(elements, "evidence_detail")

    if trust in (None, "implicit", ""):
        return ""

    parts: list[str] = []
    if trust in ("regulatory", "regulatory_plus_evidence"):
        parts.append(
            '<div class="s2d-trust__badge">SEBI Reg INH000001234</div>'
            '<div class="s2d-trust__detail">Authorised investment adviser</div>'
        )

    if trust in ("third_party_endorsement",):
        parts.append(
            '<div class="s2d-trust__badge">Featured in</div>'
            '<div class="s2d-trust__detail">Forbes · Bloomberg · ET</div>'
        )

    if trust in ("evidence_mode", "regulatory_plus_evidence"):
        if detail == "aggregate_metric":
            parts.append(
                '<div class="s2d-evidence-stat">'
                '<span class="s2d-evidence-stat__num">84%</span>'
                '<span class="s2d-evidence-stat__label">accuracy across 1,247 trades</span>'
                '</div>'
            )
        elif detail == "named_past_outcome":
            parts.append(
                '<div class="s2d-trust__detail">'
                '<strong>ZOMATO</strong> · entry ₹95 → exit ₹147 in 3 days · +₹23,435'
                '</div>'
            )
        elif detail == "user_testimonial":
            parts.append(
                '<div class="s2d-trust__detail">"Made my first profit in week 1." — Rahul, Mumbai</div>'
            )
        elif detail == "third_party_logos":
            parts.append('<div class="s2d-trust__detail">Forbes · Bloomberg · ET</div>')
        elif detail == "real_outcome_disclosure":
            parts.append(
                '<div class="s2d-trust__detail">'
                'Last trade: <strong>RELIANCE</strong> — entry ₹2,840 → exit ₹2,985 (5.1%) over 4 days'
                '</div>'
            )
        elif detail in (None, "none", ""):
            parts.append(_placeholder("evidence_detail", "missing", hint="trust=evidence_mode but no detail"))
        else:
            parts.append(_placeholder("evidence_detail", detail))

    if not parts and trust not in _REFUND_COPY:
        # Trust value was set but didn't match any branch above.
        return _placeholder("trust_signal", trust)

    return f'<div class="s2d-trust">{"".join(parts)}</div>'


def _render_urgency(elements: dict) -> str:
    urgency = _value_of(elements, "urgency_mechanism")
    if urgency in (None, "none", ""):
        return ""
    if urgency in _URGENCY_TEMPLATES:
        css_class, icon, copy = _URGENCY_TEMPLATES[urgency]
        return (
            f'<div class="s2d-urgency {css_class}">'
            f'<span class="s2d-urgency__icon">{_esc(icon)}</span>'
            f'<span>{_esc(copy)}</span>'
            f'</div>'
        )
    return _placeholder("urgency_mechanism", urgency)


def _render_price_banner(elements: dict) -> str:
    """Renders the framing banner above the CTA when price_visibility=visible_with_framing."""
    price_vis = _value_of(elements, "price_visibility")
    refund = _value_of(elements, "refund_or_guarantee_copy")
    if price_vis != "visible_with_framing":
        return ""
    framing = _REFUND_COPY.get(refund, "")
    framing_html = f' &middot; <span class="s2d-price-chip">{_esc(framing)}</span>' if framing else ""
    return (
        '<div class="s2d-price-banner">'
        f'Activate @ <span class="s2d-price-chip">₹1</span>{framing_html}'
        '</div>'
    )


def _render_refund_inline(elements: dict) -> str:
    """Refund line shown below the CTA when price_visibility != with_framing
    (so the refund/guarantee copy still surfaces somewhere)."""
    price_vis = _value_of(elements, "price_visibility")
    refund = _value_of(elements, "refund_or_guarantee_copy")
    if price_vis == "visible_with_framing":
        return ""
    if refund in (None, "absent", ""):
        return ""
    copy = _REFUND_COPY.get(refund)
    if not copy:
        return _placeholder("refund_or_guarantee_copy", refund)
    return f'<div class="s2d-refund">{_esc(copy)}</div>'


def _render_cta_button(label: str, *, style_class: str, modifier: str = "",
                       price_chip: str = "") -> str:
    chip_html = f'<span class="s2d-cta__price-chip">{_esc(price_chip)}</span>' if price_chip else ""
    classes = f"s2d-cta {style_class}"
    if modifier:
        classes += f" {modifier}"
    return f'<button class="{classes}">{_esc(label)}{chip_html}</button>'


def _render_cta_stack(elements: dict) -> str:
    label = _value_of(elements, "cta_primary_label") or "Continue"
    style = _value_of(elements, "cta_style")
    style_class = _CTA_STYLE_CLASSES.get(style, "s2d-cta--neutral-default")
    if style and style not in _CTA_STYLE_CLASSES:
        # Unknown style; render placeholder + fall through to default
        prefix = _placeholder("cta_style", style)
    else:
        prefix = ""

    stack = _value_of(elements, "cta_stack")
    price_vis = _value_of(elements, "price_visibility")
    price_chip = "₹1" if price_vis == "visible_primary" else ""

    if stack in (None, "single", ""):
        body = _render_cta_button(label, style_class=style_class, price_chip=price_chip)
        return prefix + f'<div class="s2d-cta-stack">{body}</div>'

    if stack == "dual_outline_plus_sticky":
        outline = _render_cta_button(label, style_class=style_class, modifier="s2d-cta--outline")
        sticky_label = "₹1 Trial" if price_chip else "Get started"
        sticky = _render_cta_button(sticky_label, style_class=style_class, modifier="s2d-cta--sticky",
                                     price_chip=price_chip)
        return prefix + f'<div class="s2d-cta-stack">{outline}{sticky}</div>'

    if stack == "dual_side_by_side":
        primary = _render_cta_button(label, style_class=style_class, price_chip=price_chip)
        secondary = _render_cta_button("Skip for now", style_class="s2d-cta--low-contrast-subordinate")
        return prefix + (
            f'<div class="s2d-cta-stack s2d-cta-stack--side-by-side">{primary}{secondary}</div>'
        )

    if stack == "primary_plus_secondary_link":
        primary = _render_cta_button(label, style_class=style_class, price_chip=price_chip)
        link = '<a class="s2d-cta-secondary-link" href="#">No thanks, maybe later</a>'
        return prefix + f'<div class="s2d-cta-stack">{primary}{link}</div>'

    return prefix + _placeholder("cta_stack", stack)


def _render_footer_overlay(elements: dict, *, variant_name: str) -> str:
    rows = []
    for dim, raw in elements.items():
        val = raw.get("value") if isinstance(raw, dict) else raw
        rows.append(
            f'<div class="s2d-footer__row">'
            f'<span class="s2d-footer__dim">{_esc(dim)}</span>'
            f'<span>{_esc(val)}</span>'
            f'</div>'
        )
    return (
        '<div class="s2d-footer">'
        f'<div class="s2d-footer__title">{_esc(variant_name)} · debug overlay</div>'
        f'{"".join(rows)}'
        '</div>'
    )


# ─── Public entry point ─────────────────────────────────────────────────────


def render_variant_html(
    synthesized_variant: dict,
    *,
    variant_name: str = "V_next",
    headline: str = "Get the trade idea your portfolio is missing",
    subhead: str = "One real, closed trade — yours to keep, refunded if it doesn't deliver.",
    footer: bool = False,
) -> str:
    """Render a synthesized_variant dict as a complete HTML string.

    Args:
        synthesized_variant: The cascade's `synthesized_variant` dict.
            Must contain an `elements` key mapping dimension names to either
            a value string or a {value, confidence, ...} sub-dict.
        variant_name: Display name for the debug footer (e.g. "V_next", "V5").
        headline / subhead: Default copy for the screen body. Real copy comes
            from the spec's Copy Book; these are placeholders for visual review.
        footer: If True, overlay the dimension→value mapping at the bottom of
            the screen for debugging. False for the spec deliverable.

    Returns:
        A self-contained HTML string with inline CSS. Suitable for direct
        rendering in a browser or screenshotting via Playwright.
    """
    elements = synthesized_variant.get("elements") or {}

    layout_value = _value_of(elements, "layout") or "full_screen"
    layout_class = _LAYOUT_CLASSES.get(layout_value)
    if layout_class is None:
        # Unknown layout — fall through to full_screen but flag it.
        layout_class = _LAYOUT_CLASSES["full_screen"]
        layout_warning = _placeholder("layout", layout_value)
    else:
        layout_warning = ""

    modal = _value_of(elements, "modal_interrupt")
    is_modal = modal == "yes"

    header = _render_header(elements)
    trust = _render_trust(elements)
    urgency = _render_urgency(elements)
    price_banner = _render_price_banner(elements)
    cta_block = _render_cta_stack(elements)
    refund_inline = _render_refund_inline(elements)
    footer_html = _render_footer_overlay(elements, variant_name=variant_name) if footer else ""

    body = (
        '<div class="s2d-body">'
        f'{layout_warning}'
        f'<h1 class="s2d-headline">{_esc(headline)}</h1>'
        f'<p class="s2d-subhead">{_esc(subhead)}</p>'
        f'{trust}'
        f'{urgency}'
        f'{price_banner}'
        f'{cta_block}'
        f'{refund_inline}'
        '</div>'
    )

    screen_inner = f'{header}{body}'

    if is_modal:
        # Render the screen as a sticky bottom modal sitting over a backdrop.
        screen_html = (
            f'<div class="s2d-screen {layout_class}">'
            f'<div class="s2d-modal-overlay">'
            f'<div class="s2d-modal-card">{screen_inner}</div>'
            f'</div>'
            f'</div>'
        )
    else:
        screen_html = f'<div class="s2d-screen {layout_class}">{screen_inner}</div>'

    css = _load_base_css()
    return (
        '<!DOCTYPE html>'
        '<html lang="en">'
        '<head>'
        '<meta charset="utf-8">'
        f'<title>{_esc(variant_name)} · simul2design</title>'
        f'<style>{css}</style>'
        '</head>'
        '<body>'
        f'{screen_html}'
        f'{footer_html}'
        '</body>'
        '</html>'
    )
