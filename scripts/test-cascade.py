#!/usr/bin/env python3
"""test-cascade.py — tests for simul2design/synthesize/ (Sprint B Phase 1).

Covers the deterministic cascade steps:
- weigh_segments: evidence classification + clean-contrast weighted scores
- estimate_conversion: Wilson 95% intervals + per-segment baseline application
- LLM-required steps (synthesize, adversary, generate_spec) — verifies they
  raise NotImplementedError so callers don't accidentally use stubs

Validation against the hand-built v2 univest fixtures in data/univest/ —
specifically the cta_style clean-contrast which should weighted-sum to 6.42
(matches hand calculation in matrix.clean_element_contrasts[V2->V3]).

Usage:
    scripts/test-cascade.py
"""

from __future__ import annotations
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

UNIVEST_MATRIX = ROOT / "data" / "univest" / "element_matrix.json"

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


# ─── weigh_segments tests ───────────────────────────────────────────────────

def test_wilson_95_basic():
    """Wilson 95% interval matches scipy.stats.binom equivalent at known points."""
    from simul2design.synthesize import wilson_95_interval
    # p=0.5, n=10 — well-known reference point: ~[0.224, 0.776]
    low, high = wilson_95_interval(0.5, 10)
    assert 0.20 < low < 0.25, f"low: {low}"
    assert 0.75 < high < 0.80, f"high: {high}"
    # p=0.0, n=10 — should not return negative or 0; small positive upper bound
    low, high = wilson_95_interval(0.0, 10)
    assert low == 0.0
    assert 0 < high < 0.30
    # p=1.0, n=10 — should not return >1 or 1.0; positive lower bound
    low, high = wilson_95_interval(1.0, 10)
    assert 0.7 < low < 1.0
    assert high == 1.0
    # n=0 → safe degenerate case
    assert wilson_95_interval(0.5, 0) == (0.0, 0.0)


def test_wilson_widens_at_low_n():
    """Smaller n → wider interval. Sanity check on the math."""
    from simul2design.synthesize import wilson_95_interval
    low_10, high_10 = wilson_95_interval(0.5, 10)
    low_100, high_100 = wilson_95_interval(0.5, 100)
    width_10 = high_10 - low_10
    width_100 = high_100 - low_100
    assert width_10 > width_100, f"n=10 width {width_10} should exceed n=100 width {width_100}"


def test_apply_wilson_to_segments_univest():
    """Apply Wilson to univest matrix's V4 baseline; check Skeptical CI matches the hand-computed one."""
    from simul2design.synthesize import apply_wilson_to_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    out = apply_wilson_to_segments(matrix, baseline_variant_id="V4")
    assert "skeptical_investor" in out
    skeptical = out["skeptical_investor"]
    # Skeptical V4: n=12, p=0.25 → Wilson 95% ≈ [0.089, 0.532] (per existing conversion_estimates.json)
    low, high = skeptical["baseline_wilson_95_ci"]
    assert 0.08 < low < 0.10, f"skeptical low: {low}"
    assert 0.50 < high < 0.55, f"skeptical high: {high}"


def test_weigh_segments_cta_style_matches_hand_calc():
    """The univest cta_style clean contrast should weighted-sum to 6.42pt for high_contrast_green.

    This is THE critical test — if this fails, the port breaks the deterministic
    arithmetic the SKILL.md spot-check requires.
    """
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    cta_dim = result["dimensions"]["cta_style"]
    green = cta_dim["values"]["high_contrast_green"]
    assert green["evidence_type"] == "clean_contrast", \
        f"cta_style high_contrast_green should be clean_contrast (V2→V3), got: {green['evidence_type']}"
    assert green["weighted_score_pts"] is not None
    # Hand calc: 0.24×9 + 0.30×7 + 0.26×16 + 0.20×(-10) = 2.16 + 2.10 + 4.16 - 2.00 = 6.42
    assert abs(green["weighted_score_pts"] - 6.42) < 0.05, \
        f"cta_style high_contrast_green weighted_score_pts should be ~6.42, got {green['weighted_score_pts']}"
    # Per-segment deltas
    per_seg = green["per_segment_impact"]
    assert abs(per_seg["skeptical_investor"]["delta_pts"] - 9.0) < 0.5
    assert abs(per_seg["bargain_hunter"]["delta_pts"] - 16.0) < 0.5
    assert abs(per_seg["trust_seeker"]["delta_pts"] - (-10.0)) < 0.5
    # Confidence is 'high' since |bargain_delta| = 16pt ≥ 8
    assert green["confidence"] == "high"


def test_weigh_segments_cta_style_low_contrast_subordinate_inverse_sign():
    """The 'from' side of a clean contrast gets the opposite sign delta."""
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    sub = result["dimensions"]["cta_style"]["values"]["low_contrast_subordinate"]
    assert sub["evidence_type"] == "clean_contrast"
    # Adopting low_contrast_subordinate over high_contrast_green is the inverse: -6.42pt
    assert abs(sub["weighted_score_pts"] - (-6.42)) < 0.05, \
        f"low_contrast_subordinate should be ~-6.42, got {sub['weighted_score_pts']}"


def test_weigh_segments_dimensions_present():
    """Every base-taxonomy dimension appears exactly once in output."""
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    expected_dims = {"layout", "modal_interrupt", "branding", "price_visibility",
                     "cta_style", "cta_stack", "urgency_mechanism",
                     "refund_or_guarantee_copy", "trust_signal", "evidence_detail"}
    actual_dims = set(result["dimensions"].keys())
    missing = expected_dims - actual_dims
    assert not missing, f"missing dimensions: {missing}"


def test_weigh_segments_confounded_emits_null():
    """Confounded values must emit null weighted_score_pts (no fabrication)."""
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    # Walk all dims; any value classified confounded must have null score
    for dim_name, dim in result["dimensions"].items():
        for val_name, val in dim["values"].items():
            if val["evidence_type"] in ("confounded", "untested", "variant_only"):
                assert val["weighted_score_pts"] is None, \
                    f"{dim_name}.{val_name} ({val['evidence_type']}) should have null score, got {val['weighted_score_pts']}"


def test_weigh_segments_evidence_tier_distribution():
    """Output includes the evidence_tier_distribution KPI."""
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    summary = result["dimension_summary"]
    assert "evidence_tier_distribution" in summary
    tiers = summary["evidence_tier_distribution"]
    # The univest matrix should have at least one clean_contrast (cta_style V2→V3)
    assert tiers.get("clean_contrast", 0) >= 2  # both sides of V2->V3 cta_style


def test_weigh_segments_dimension_recommendation():
    """Each dimension produces a recommended value (or null with rationale)."""
    from simul2design.synthesize import weigh_segments
    if not UNIVEST_MATRIX.is_file():
        return
    matrix = json.loads(UNIVEST_MATRIX.read_text())
    result = weigh_segments(matrix)
    cta = result["dimensions"]["cta_style"]
    assert cta["recommended"]["value"] == "high_contrast_green", \
        f"expected high_contrast_green to win, got {cta['recommended']['value']}"
    assert cta["dimension_informativeness"] == "rankable"


# ─── pipeline integration test ──────────────────────────────────────────────

def test_pipeline_includes_weighted_scores_when_enabled():
    """SynthesisPipeline.run() returns weighted_scores when run_weigh_segments=True."""
    import asyncio
    from simul2design import SynthesisPipeline, ComparisonData

    fixture = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
    if not fixture.is_file():
        return
    raw = json.loads(fixture.read_text())
    cd = ComparisonData(**raw)
    pipeline = SynthesisPipeline(skip_llm_fallback=True, run_weigh_segments=True)
    result = asyncio.run(pipeline.run(cd, client_slug="univest-cascade-test"))
    assert result.weighted_scores is not None
    assert "dimensions" in result.weighted_scores
    assert "dimension_summary" in result.weighted_scores


def test_pipeline_includes_wilson_baseline_when_enabled():
    """SynthesisPipeline.run() returns conversion_estimates when run_wilson_baseline=True."""
    import asyncio
    from simul2design import SynthesisPipeline, ComparisonData

    fixture = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
    if not fixture.is_file():
        return
    raw = json.loads(fixture.read_text())
    cd = ComparisonData(**raw)
    pipeline = SynthesisPipeline(skip_llm_fallback=True, run_wilson_baseline=True,
                                  wilson_baseline_variant="V4")
    result = asyncio.run(pipeline.run(cd, client_slug="univest-wilson-test"))
    assert result.conversion_estimates is not None
    assert "per_segment_baseline" in result.conversion_estimates
    assert "skeptical_investor" in result.conversion_estimates["per_segment_baseline"]


def test_pipeline_can_disable_cascade_steps():
    """run_weigh_segments=False and run_wilson_baseline=False leave fields None."""
    import asyncio
    from simul2design import SynthesisPipeline, ComparisonData

    fixture = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
    if not fixture.is_file():
        return
    raw = json.loads(fixture.read_text())
    cd = ComparisonData(**raw)
    pipeline = SynthesisPipeline(
        skip_llm_fallback=True,
        run_weigh_segments=False,
        run_wilson_baseline=False,
    )
    result = asyncio.run(pipeline.run(cd, client_slug="univest-noop-test"))
    assert result.weighted_scores is None
    assert result.conversion_estimates is None


# Note: stub-raises tests removed — the three LLM-required steps were
# implemented in Sprint B Phase 2 and are now tested by test-cascade-llm.py.


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    # Wilson math
    test_wilson_95_basic,
    test_wilson_widens_at_low_n,
    test_apply_wilson_to_segments_univest,
    # weigh_segments — the critical hand-calc check + classification correctness
    test_weigh_segments_cta_style_matches_hand_calc,
    test_weigh_segments_cta_style_low_contrast_subordinate_inverse_sign,
    test_weigh_segments_dimensions_present,
    test_weigh_segments_confounded_emits_null,
    test_weigh_segments_evidence_tier_distribution,
    test_weigh_segments_dimension_recommendation,
    # Pipeline integration (deterministic only)
    test_pipeline_includes_weighted_scores_when_enabled,
    test_pipeline_includes_wilson_baseline_when_enabled,
    test_pipeline_can_disable_cascade_steps,
]


def main() -> int:
    print(f"Running {len(TESTS)} tests against simul2design/synthesize/...\n")
    passed, failed = [], []
    for t in TESTS:
        name = t.__name__
        try:
            t()
            passed.append(name)
            print(f"  {GREEN}✓{RESET} {name}")
        except AssertionError as e:
            failed.append((name, str(e)))
            print(f"  {RED}✗{RESET} {name}{DIM} — {e}{RESET}")
        except Exception as e:
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  {RED}✗{RESET} {name}{DIM} — {type(e).__name__}: {e}{RESET}")

    print()
    print(f"{GREEN}Passed:{RESET} {len(passed)}/{len(TESTS)}")
    if failed:
        print(f"{RED}Failed:{RESET} {len(failed)}")
        return 1
    print(f"{GREEN}All tests passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
