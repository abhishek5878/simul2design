"""CLI entry point for `simul2design-render`.

Reads a SynthesisResult JSON (or just a synthesized_variant JSON), renders
the V(N+1) variant to a PNG, and writes it to disk. Useful for re-rendering
without re-running the cascade after tweaking the template.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from simul2design.render import render_variant_html, render_variant_png


def _parse_viewport(spec: str) -> tuple[int, int]:
    """Parse a 'WIDTHxHEIGHT' string (e.g. '375x812') into (W, H)."""
    try:
        w, h = spec.lower().split("x", 1)
        return (int(w), int(h))
    except (ValueError, AttributeError) as e:
        raise argparse.ArgumentTypeError(
            f"--viewport expects 'WIDTHxHEIGHT' (e.g. '375x812'), got {spec!r}"
        ) from e


def _extract_synthesized_variant(payload: dict) -> dict:
    """A SynthesisResult JSON has synthesized_variant nested; a raw
    synthesized_variant dict has elements at top level. Accept either."""
    if "synthesized_variant" in payload:
        sv = payload["synthesized_variant"]
        if not sv:
            raise ValueError(
                "Input has 'synthesized_variant: null'. The cascade either "
                "didn't run or failed before producing a variant. Re-run "
                "SynthesisPipeline with run_full_cascade=True."
            )
        return sv
    if "elements" in payload:
        return payload
    raise ValueError(
        "Input does not look like a SynthesisResult or synthesized_variant. "
        "Expected either a top-level 'synthesized_variant' key or an 'elements' key."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="simul2design-render",
        description="Render a synthesized V(N+1) variant to PNG.",
    )
    p.add_argument(
        "input",
        help="Path to a SynthesisResult JSON, or a raw synthesized_variant JSON. "
             "Pass '-' to read from stdin.",
    )
    p.add_argument(
        "-o", "--output", default="variant.png",
        help="Path to write the PNG (default: variant.png).",
    )
    p.add_argument(
        "--viewport", type=_parse_viewport, default=(375, 812),
        help="Viewport size as WIDTHxHEIGHT (default: 375x812 — mobile).",
    )
    p.add_argument(
        "--variant-name", default="V_next",
        help="Display name for the debug footer (default: V_next).",
    )
    p.add_argument(
        "--footer", action="store_true",
        help="Overlay the dimension→value mapping at the bottom of the PNG. "
             "Useful for internal review; OFF for spec deliverables.",
    )
    p.add_argument(
        "--device-scale", type=float, default=2.0,
        help="Device pixel ratio (default: 2.0 — retina). "
             "Set to 1.0 for crisper text on non-retina, 3.0 for high-DPI marketing.",
    )
    p.add_argument(
        "--html-only", action="store_true",
        help="Print HTML to stdout instead of rendering PNG. "
             "Useful when Playwright isn't installed.",
    )
    p.add_argument(
        "--headline", default="Get the trade idea your portfolio is missing",
        help="Headline copy for the variant body (placeholder for visual review).",
    )
    p.add_argument(
        "--subhead",
        default="One real, closed trade — yours to keep, refunded if it doesn't deliver.",
        help="Subhead copy for the variant body (placeholder for visual review).",
    )

    args = p.parse_args(argv)

    if args.input == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: {args.input} is not valid JSON: {e}", file=sys.stderr)
        return 1

    try:
        sv = _extract_synthesized_variant(payload)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.html_only:
        html = render_variant_html(
            sv, variant_name=args.variant_name,
            headline=args.headline, subhead=args.subhead, footer=args.footer,
        )
        sys.stdout.write(html)
        return 0

    try:
        png = render_variant_png(
            sv,
            variant_name=args.variant_name,
            headline=args.headline,
            subhead=args.subhead,
            footer=args.footer,
            viewport=args.viewport,
            output_path=args.output,
            device_scale_factor=args.device_scale,
        )
    except Exception as e:
        print(f"Render failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output} ({len(png):,} bytes, viewport {args.viewport[0]}x{args.viewport[1]} @ {args.device_scale}x)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
