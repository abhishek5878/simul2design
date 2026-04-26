#!/usr/bin/env python3
"""test-ab-report-adapter.py — tests for simul2design/adapters/ab_report.py.

Validates the AbReport → ComparisonData adapter using:
1. The minimal `_canned_ab_report()` fixture from apriori_simulation_engine's
   tests/unit/test_multiflow_orchestrator.py (sourced from a clone at
   /tmp/apriori_engine_clone, with a checked-in copy below as fallback so this
   test runs even without the clone).
2. A richer in-memory fixture exercising every AbReport field
   (annotated_screens with real elements, persona_split with mixed preferred
   variants, friction_provenance on both sides, monologue_diff with multiple
   personas, ship_list with kill/keep/revisit actions, and a deep_dive).

Each test asserts:
- adapter output validates as `simul2design.ComparisonData`
- `simul2design.ingest.build_matrix(...)` runs without error and produces the
  expected segments / variants / friction structure
- the preference-proxy completion-rate encoding matches the input

Usage:
    scripts/test-ab-report-adapter.py
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


# ─── Fixtures ───────────────────────────────────────────────────────────────

def _canned_ab_report_minimal(simulation_id: str = "test-sim") -> dict:
    """Mirror of `_canned_ab_report` in apriori_simulation_engine's
    tests/unit/test_multiflow_orchestrator.py:105-124.

    Pinning a copy here keeps this test runnable in isolation; the engine
    repo's version is the source of truth for the AbReport pydantic shape.
    """
    return {
        "meta": {
            "simulation_id": simulation_id,
            "study_name": "Flow A vs Flow B",
            "client": "",
            "screen_label": "Single screen",
            "persona_count": 5,
            "runs_per_persona": 1,
            "generated_at": "2026-04-26T12:00:00Z",
        },
        "verdict": {"sentence": "Ship Flow A.", "confidence": "high"},
        "ship_list": [],
        "annotated_screens": {"screens": []},
        "persona_split": [],
        "friction_provenance": {"variant_a": [], "variant_b": []},
        "monologue_diff": [],
        "deep_dive": {"personas": []},
    }


def _canned_ab_report_rich() -> dict:
    """A fuller AbReport with non-empty entries in every section. Mirrors the
    AbReport pydantic shape at `src/api/models/ab_report.py`."""
    return {
        "meta": {
            "simulation_id": "rich-fixture-001",
            "study_name": "Onboarding A vs B (rich)",
            "client": "",
            "screen_label": "5-screen onboarding",
            "persona_count": 8,
            "runs_per_persona": 2,
            "generated_at": "2026-04-27T08:30:00Z",
        },
        "verdict": {
            "sentence": "Ship Variant B for urban-tech but defer for low-literacy users.",
            "confidence": "medium",
        },
        "ship_list": [
            {
                "id": "s1", "action": "keep", "source_variant": "B",
                "feature": "single-tap signup",
                "rationale": "Removed two friction points on the welcome screen.",
                "bullet": "Adopt single-tap signup from B",
                "confidence": "high",
                "markdown": "- [ ] Adopt single-tap signup from B",
            },
            {
                "id": "s2", "action": "kill", "source_variant": "A",
                "feature": "interstitial value-prop modal",
                "rationale": "60% of users dismissed without reading.",
                "bullet": "Remove interstitial value-prop modal",
                "confidence": "high",
                "markdown": "- [ ] Remove interstitial value-prop modal",
            },
            {
                "id": "s3", "action": "revisit", "source_variant": "both",
                "feature": "phone-number gate",
                "rationale": "Ambiguous signal across segments.",
                "bullet": "Test phone-gate placement variants",
                "confidence": "low",
                "markdown": "- [ ] Test phone-gate placement variants",
            },
        ],
        "annotated_screens": {
            "screens": [
                {
                    "id": "scr1", "index": 0, "screen_label": "Welcome",
                    "variant_a": {
                        "image_path": "/screens/a/welcome.png",
                        "elements": [
                            {"id": "e1", "label": "Hero CTA", "anchor": {"x": 0.5, "y": 0.4},
                             "verdict": "drag", "callout": "Buried under modal",
                             "persona_count": 5, "summary": "CTA hard to find behind interstitial."},
                        ],
                    },
                    "variant_b": {
                        "image_path": "/screens/b/welcome.png",
                        "elements": [
                            {"id": "e2", "label": "Hero CTA", "anchor": {"x": 0.5, "y": 0.5},
                             "verdict": "lift", "callout": "Front-and-center",
                             "persona_count": 7, "summary": "CTA immediately tappable."},
                        ],
                    },
                },
                {
                    "id": "scr2", "index": 1, "screen_label": "Plan selection",
                    "variant_a": {"image_path": "/screens/a/plan.png", "elements": []},
                    "variant_b": {"image_path": "/screens/b/plan.png", "elements": []},
                },
            ],
        },
        "persona_split": [
            {
                "segment": "urban tech workers",
                "persona_count": 3,
                "preferred_variant": "B",
                "reactions": {
                    "loved": [{"name": "single-tap signup", "source": "B"}],
                    "disliked": [{"name": "interstitial modal", "source": "A"}],
                },
                "interpretation": "B's reduced friction wins decisively for this segment.",
            },
            {
                "segment": "rural low-literacy",
                "persona_count": 3,
                "preferred_variant": "A",
                "reactions": {
                    "loved": [{"name": "explanatory modal", "source": "A"}],
                    "disliked": [{"name": "no copy", "source": "B"}],
                },
                "interpretation": "A's verbose explanations help rural users understand the offer.",
            },
            {
                "segment": "skeptical investors",
                "persona_count": 2,
                "preferred_variant": "neither",
                "reactions": {
                    "loved": [],
                    "disliked": [{"name": "trust signals weak", "source": "both"}],
                },
                "interpretation": "Neither variant addresses trust concerns adequately.",
            },
        ],
        "friction_provenance": {
            "variant_a": [
                {"type": "interruption", "severity": "high", "persona_count": 5,
                 "note": "Interstitial modal blocks first-screen CTA."},
                {"type": "copy_overload", "severity": "low", "persona_count": 2,
                 "note": "Plan-selection screen has dense copy."},
            ],
            "variant_b": [
                {"type": "missing_context", "severity": "medium", "persona_count": 3,
                 "note": "No explanation of what 'unlimited healthcare' covers."},
            ],
        },
        "monologue_diff": [
            {
                "persona_id": "p1", "persona_name": "Aanya (urban tech)",
                "segment": "urban tech workers",
                "variant_a_monologue": "Why is there a modal blocking me before I even see the offer?",
                "variant_b_monologue": "Clean, fast — let me try this.",
                "inflection": "Friction removal at first screen.",
                "decision_a": "abandon", "decision_b": "convert",
            },
            {
                "persona_id": "p2", "persona_name": "Ramesh (rural)",
                "segment": "rural low-literacy",
                "variant_a_monologue": "Good — they explained what unlimited means.",
                "variant_b_monologue": "What does 'unlimited' even mean? I'm not sure I trust this.",
                "inflection": "Explanation density preference.",
                "decision_a": "convert", "decision_b": "hesitate",
            },
        ],
        "deep_dive": {
            "personas": [
                {
                    "id": "p1", "name": "Aanya", "segment": "urban tech workers",
                    "archetype": "Time-constrained professional", "occupation": "PM at SaaS co",
                    "age": 29, "city": "Bengaluru", "income_band": "20-40 LPA",
                    "tags": ["mobile_first", "high_digital_literacy"],
                    "behavior_summary": "Skips long copy. Wants to convert in <30s.",
                    "variant_a": {"outcome": "abandon", "monologue": "Modal blocked me.",
                                  "primary_emotion": "frustrated", "why": "Forced interrupt.",
                                  "liked": [], "disliked": ["modal"]},
                    "variant_b": {"outcome": "convert", "monologue": "Smooth.",
                                  "primary_emotion": "satisfied", "why": "Fast path to value.",
                                  "liked": ["single-tap signup"], "disliked": []},
                    "overall_reflection": {"text": "B clearly wins for me.", "leaning": "B"},
                },
            ],
        },
    }


# ─── Tests ──────────────────────────────────────────────────────────────────

def test_minimal_fixture_validates_as_comparison_data():
    """Minimal AbReport adapts to a dict that ComparisonData validates."""
    from simul2design.adapters import from_ab_report
    from simul2design import ComparisonData

    adapted = from_ab_report(_canned_ab_report_minimal())
    cd = ComparisonData(**adapted)
    assert cd.metadata["simulation_id"] == "test-sim"
    assert len(cd.variants) == 2
    assert {v["id"] for v in cd.variants} == {"a", "b"}
    assert cd.segment_verdicts == []
    assert cd.friction_provenance == []


def test_rich_fixture_validates_as_comparison_data():
    """Rich AbReport adapts cleanly and preserves segment + friction structure."""
    from simul2design.adapters import from_ab_report
    from simul2design import ComparisonData

    adapted = from_ab_report(_canned_ab_report_rich())
    cd = ComparisonData(**adapted)

    assert cd.metadata["simulation_id"] == "rich-fixture-001"
    assert cd.metadata["persona_count"] == 8
    assert len(cd.segment_verdicts) == 3
    assert {sv["segment_name"] for sv in cd.segment_verdicts} == {
        "urban tech workers", "rural low-literacy", "skeptical investors"
    }
    assert len(cd.friction_provenance) == 3  # 2 from variant_a + 1 from variant_b
    assert len(cd.persona_journeys) == 1     # one deep_dive persona


def test_measured_subsample_for_segments_with_persona_outcomes():
    """Segments with persona-level outcomes get measured_subsample rates +
    observed_n; segments without outcomes fall back to preference proxy."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    sv_by_name = {sv["segment_name"]: sv for sv in adapted["segment_verdicts"]}

    # Urban: persona p1 in deep_dive (variant_a.outcome=abandon, variant_b.outcome=convert)
    # AND in monologue_diff (decision_a=abandon, decision_b=convert) — de-duped by id.
    # Observed n=1 per variant. Convert rate: a=0%, b=100%.
    urban = sv_by_name["urban tech workers"]
    assert urban["winner"] == "b"
    assert urban["metrics_by_variant"]["a"]["completion_rate"] == 0.0
    assert urban["metrics_by_variant"]["b"]["completion_rate"] == 100.0
    assert urban["metrics_by_variant"]["a"]["observed_n"] == 1
    assert urban["metrics_by_variant"]["b"]["observed_n"] == 1
    assert urban["metrics_by_variant"]["a"]["completion_rate_source"] == "measured_subsample"

    # Rural: persona p2 in monologue_diff (decision_a=convert, decision_b=hesitate).
    # Observed n=1. Convert rate: a=100%, b=0% (hesitate ≠ convert).
    rural = sv_by_name["rural low-literacy"]
    assert rural["winner"] == "a"
    assert rural["metrics_by_variant"]["a"]["completion_rate"] == 100.0
    assert rural["metrics_by_variant"]["b"]["completion_rate"] == 0.0
    assert rural["metrics_by_variant"]["a"]["observed_n"] == 1
    assert rural["metrics_by_variant"]["a"]["completion_rate_source"] == "measured_subsample"

    # Skeptical: no persona-level outcomes anywhere AND preferred_variant=neither
    # → both null with absent source label.
    skeptical = sv_by_name["skeptical investors"]
    assert skeptical["winner"] is None
    assert skeptical["metrics_by_variant"]["a"]["completion_rate"] is None
    assert skeptical["metrics_by_variant"]["b"]["completion_rate"] is None
    assert skeptical["metrics_by_variant"]["a"]["observed_n"] == 0
    assert skeptical["metrics_by_variant"]["a"]["completion_rate_source"] == "absent"


def test_preference_proxy_fallback_when_no_outcomes():
    """When persona-level outcomes are absent for a segment, preferred_variant
    drives a binary 100/0 with completion_rate_source='preference_proxy'."""
    from simul2design.adapters import from_ab_report

    # Strip persona-level outcome data; keep persona_split intact.
    rich = _canned_ab_report_rich()
    rich["monologue_diff"] = []
    rich["deep_dive"] = {"personas": []}

    adapted = from_ab_report(rich)
    sv_by_name = {sv["segment_name"]: sv for sv in adapted["segment_verdicts"]}

    urban = sv_by_name["urban tech workers"]
    assert urban["metrics_by_variant"]["a"]["completion_rate"] == 0.0
    assert urban["metrics_by_variant"]["b"]["completion_rate"] == 100.0
    assert urban["metrics_by_variant"]["a"]["observed_n"] == 0
    assert urban["metrics_by_variant"]["a"]["completion_rate_source"] == "preference_proxy"


def test_measured_overrides_preference_when_they_disagree():
    """If a deep_dive persona's outcomes contradict preferred_variant, the
    measured outcomes win (real signal beats segment-level preference tag)."""
    from simul2design.adapters import from_ab_report

    # Adversarial fixture: persona_split says urban prefers A, but the only
    # deep_dive persona for urban converted on B and abandoned A.
    report = _canned_ab_report_minimal()
    report["persona_split"] = [
        {"segment": "urban", "persona_count": 3, "preferred_variant": "A",
         "reactions": {"loved": [], "disliked": []}, "interpretation": "leans A"},
    ]
    report["deep_dive"] = {"personas": [
        {"id": "p99", "name": "Contrarian", "segment": "urban", "archetype": "skeptic",
         "occupation": "?", "age": 30, "city": "?", "income_band": "?", "tags": [],
         "behavior_summary": "",
         "variant_a": {"outcome": "abandon", "monologue": "", "primary_emotion": "", "why": "",
                       "liked": [], "disliked": []},
         "variant_b": {"outcome": "convert", "monologue": "", "primary_emotion": "", "why": "",
                       "liked": [], "disliked": []},
         "overall_reflection": {"text": "", "leaning": "B"}},
    ]}

    adapted = from_ab_report(report)
    urban = adapted["segment_verdicts"][0]
    # winner stays as the source-of-truth tag from persona_split (A) — that's the
    # AbReport's own analysis. But the metric cells reflect the MEASURED outcome.
    assert urban["winner"] == "a"
    assert urban["metrics_by_variant"]["a"]["completion_rate"] == 0.0
    assert urban["metrics_by_variant"]["b"]["completion_rate"] == 100.0
    assert urban["metrics_by_variant"]["a"]["completion_rate_source"] == "measured_subsample"


def test_outcomes_deduped_across_deep_dive_and_monologue_diff():
    """A persona present in both deep_dive AND monologue_diff is counted once."""
    from simul2design.adapters import from_ab_report

    report = _canned_ab_report_minimal()
    report["persona_split"] = [
        {"segment": "urban", "persona_count": 5, "preferred_variant": "B",
         "reactions": {"loved": [], "disliked": []}, "interpretation": ""},
    ]
    # Same persona id in both sections; deep_dive wins (recorded first).
    report["deep_dive"] = {"personas": [
        {"id": "p1", "name": "Aanya", "segment": "urban", "archetype": "?", "occupation": "?",
         "age": 30, "city": "?", "income_band": "?", "tags": [], "behavior_summary": "",
         "variant_a": {"outcome": "abandon", "monologue": "", "primary_emotion": "", "why": "",
                       "liked": [], "disliked": []},
         "variant_b": {"outcome": "convert", "monologue": "", "primary_emotion": "", "why": "",
                       "liked": [], "disliked": []},
         "overall_reflection": {"text": "", "leaning": "B"}},
    ]}
    report["monologue_diff"] = [
        {"persona_id": "p1", "persona_name": "Aanya", "segment": "urban",
         "variant_a_monologue": "", "variant_b_monologue": "",
         "inflection": "", "decision_a": "convert", "decision_b": "abandon"},
    ]

    adapted = from_ab_report(report)
    urban = adapted["segment_verdicts"][0]
    # Only the deep_dive entry contributes (p1 is de-duped). a=abandon → 0%; b=convert → 100%.
    assert urban["metrics_by_variant"]["a"]["observed_n"] == 1
    assert urban["metrics_by_variant"]["b"]["observed_n"] == 1
    assert urban["metrics_by_variant"]["a"]["completion_rate"] == 0.0
    assert urban["metrics_by_variant"]["b"]["completion_rate"] == 100.0


def test_aggregate_metrics_use_measured_when_any_outcomes_present():
    """Top-level metrics.{a,b}.completion_rate pools measured outcomes across
    all segments when any are observed; falls back to preference share otherwise."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    # Pooled: a outcomes = [abandon (urban p1), convert (rural p2)] → 1/2 = 50%.
    #         b outcomes = [convert (urban p1), hesitate (rural p2)] → 1/2 = 50%.
    assert adapted["metrics"]["a"]["completion_rate"] == 50.0
    assert adapted["metrics"]["b"]["completion_rate"] == 50.0
    assert adapted["metrics"]["a"]["observed_n"] == 2
    assert adapted["metrics"]["b"]["observed_n"] == 2
    assert adapted["metrics"]["a"]["completion_rate_source"] == "measured_subsample"
    # SUS / SEQ / sentiment absent in source → null.
    assert adapted["metrics"]["a"]["sus"] is None
    # friction_count counts from friction_provenance.variant_x.
    assert adapted["metrics"]["a"]["friction_count"] == 2
    assert adapted["metrics"]["b"]["friction_count"] == 1


def test_aggregate_metrics_fallback_to_preference_share():
    """With no persona-level outcomes anywhere, aggregate metrics fall back to
    the persona_split preference-share calculation."""
    from simul2design.adapters import from_ab_report

    rich = _canned_ab_report_rich()
    rich["monologue_diff"] = []
    rich["deep_dive"] = {"personas": []}

    adapted = from_ab_report(rich)
    # Total persona_count across persona_split = 3 + 3 + 2 = 8.
    # 'B' got 3 (urban). 'A' got 3 (rural). 'neither' = 2 (skeptical).
    # → a: 37.5, b: 37.5
    assert adapted["metrics"]["a"]["completion_rate"] == 37.5
    assert adapted["metrics"]["b"]["completion_rate"] == 37.5
    assert adapted["metrics"]["a"]["completion_rate_source"] == "preference_proxy"
    assert adapted["metrics"]["a"]["observed_n"] == 0


def test_friction_presence_shape():
    """Each friction_provenance item carries `presence: {a, b}` in the legacy shape."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    for fp in adapted["friction_provenance"]:
        assert "presence" in fp
        assert set(fp["presence"].keys()) == {"a", "b"}
        # Exactly one side should be 'present'.
        present_sides = [k for k, v in fp["presence"].items() if v == "present"]
        assert len(present_sides) == 1


def test_theme_movement_carries_monologue_evidence():
    """monologue_diff[] becomes theme_movement.persistent[] with monologue_evidence."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    persistent = adapted["theme_movement"]["persistent"]
    assert len(persistent) == 2  # one per monologue_diff entry
    for theme in persistent:
        ev = theme["monologue_evidence"]
        assert "monologues" in ev
        assert set(ev["monologues"].keys()) == {"a", "b"}
        assert ev["persona_name"]


def test_screenshots_grouped_by_variant():
    """variant_screenshots.{a,b} collects image_paths from every annotated screen pair."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    vs = adapted["variant_screenshots"]
    assert vs["a"] == ["/screens/a/welcome.png", "/screens/a/plan.png"]
    assert vs["b"] == ["/screens/b/welcome.png", "/screens/b/plan.png"]


def test_recommendations_and_risks():
    """ship_list keeps/revisits become recommendations; kills become risks."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    assert len(adapted["recommendations"]) == 3
    assert any(r["action"] == "kill" for r in adapted["recommendations"])
    # The single 'kill' ship item should also surface in risks_to_monitor.
    assert len(adapted["risks_to_monitor"]) == 1
    assert "interstitial" in adapted["risks_to_monitor"][0].lower()


def test_extraction_confidence_records_per_cell_sources():
    """The adapter records per-(segment, variant) source labels so
    generate_spec can surface which cells are measured vs proxy vs absent."""
    from simul2design.adapters import from_ab_report

    adapted = from_ab_report(_canned_ab_report_rich())
    ec = adapted["_extraction_confidence"]
    assert ec["_source"].endswith("ab_report")

    cells = ec["segment_verdicts.metrics_by_variant.completion_rate.cells"]
    # Urban + rural have measured outcomes; skeptical has neither.
    assert cells["urban tech workers"] == {"a": "measured_subsample", "b": "measured_subsample"}
    assert cells["rural low-literacy"] == {"a": "measured_subsample", "b": "measured_subsample"}
    assert cells["skeptical investors"] == {"a": "absent", "b": "absent"}

    # Aggregate metric source should match the overall picture (some measured).
    assert ec["metrics.completion_rate"] == "measured_subsample"

    # The adapter note documents the three-tier resolution explicitly.
    note = ec["_adapter_note"].upper()
    assert "MEASURED_SUBSAMPLE" in note
    assert "PREFERENCE_PROXY" in note
    assert "ABSENT" in note


def test_ingest_build_matrix_runs_end_to_end():
    """The full ingest path consumes the adapted output without error."""
    from simul2design.adapters import from_ab_report
    from simul2design.ingest import build_matrix

    adapted = from_ab_report(_canned_ab_report_rich(), client_slug="test_client")
    matrix = build_matrix(adapted, client="test_client", source_path="(in-memory)")

    assert matrix["client"] == "test_client"
    assert matrix["n_total"] == 8
    assert len(matrix["variants"]) == 2
    assert {v["id"] for v in matrix["variants"]} == {"V1", "V2"}
    assert len(matrix["segments"]) == 3
    seg_weights = {s["id"]: s["weight"] for s in matrix["segments"]}
    # 3/8 + 3/8 + 2/8 = 1.0 exactly (floats: allow tiny epsilon).
    assert abs(sum(seg_weights.values()) - 1.0) < 1e-6
    # Friction points carry through with presence shape understood by ingest.
    assert len(matrix["friction_points"]) == 3
    # Citations were extracted from theme_movement (which we built from monologue_diff).
    assert len(matrix["citations"]) >= 2


def test_invalid_input_raises():
    """Adapter rejects a non-AbReport input with a clear error."""
    from simul2design.adapters import from_ab_report
    try:
        from_ab_report({"foo": "bar"})
    except ValueError as e:
        assert "AbReport" in str(e)
        return
    raise AssertionError("from_ab_report should have raised on a non-AbReport dict")


def test_langgraph_node_consumes_ab_report_state():
    """synthesis_node() with state['ab_report'] runs the adapter automatically."""
    import asyncio
    from simul2design.langgraph_node import synthesis_node
    from simul2design import SynthesisPipeline

    state = {
        "ab_report": _canned_ab_report_rich(),
        "client_slug": "test_client",
    }
    pipeline = SynthesisPipeline(skip_llm_fallback=True)
    out = asyncio.run(synthesis_node(state, pipeline=pipeline))

    assert out["synthesis_input_source"] == "ab_report"
    assert "synthesis_result" in out
    assert "synthesis_ready_for_human" in out
    sr = out["synthesis_result"]
    assert sr["client_slug"] == "test_client"
    assert len(sr["element_matrix"]["variants"]) == 2


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    test_minimal_fixture_validates_as_comparison_data,
    test_rich_fixture_validates_as_comparison_data,
    test_measured_subsample_for_segments_with_persona_outcomes,
    test_preference_proxy_fallback_when_no_outcomes,
    test_measured_overrides_preference_when_they_disagree,
    test_outcomes_deduped_across_deep_dive_and_monologue_diff,
    test_aggregate_metrics_use_measured_when_any_outcomes_present,
    test_aggregate_metrics_fallback_to_preference_share,
    test_friction_presence_shape,
    test_theme_movement_carries_monologue_evidence,
    test_screenshots_grouped_by_variant,
    test_recommendations_and_risks,
    test_extraction_confidence_records_per_cell_sources,
    test_ingest_build_matrix_runs_end_to_end,
    test_invalid_input_raises,
    test_langgraph_node_consumes_ab_report_state,
]


def main() -> int:
    print(f"Running {len(TESTS)} tests against simul2design/adapters/ab_report.py...\n")
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
