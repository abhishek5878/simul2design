#!/usr/bin/env python3
"""test-cascade-llm.py — tests for Sprint B Phase 2 LLM-required cascade steps.

Covers:
- run_synthesize: prompt structure, mocked LLM call, output envelope
- run_adversary: prompt structure, mocked LLM call, output envelope
- run_generate_spec: prompt structure, mocked LLM call, markdown header
- SynthesisPipeline.run() with run_full_cascade=True end-to-end (mocked)

Tests use unittest.mock to patch the Anthropic SDK — no API key needed.

Usage:
    scripts/test-cascade-llm.py
"""

from __future__ import annotations
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

UNIVEST_MATRIX = ROOT / "data" / "univest" / "element_matrix.json"
FIXTURE_UNIVEST = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def make_mock_json_response(payload: dict, in_t=2000, out_t=500, cw_t=0, cr_t=0):
    """Mock Anthropic Message with a JSON-shaped text content."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(payload))],
        usage={
            "input_tokens": in_t, "output_tokens": out_t,
            "cache_read_input_tokens": cr_t, "cache_creation_input_tokens": cw_t,
        },
    )


def make_mock_text_response(text: str, in_t=2000, out_t=1000, cw_t=0, cr_t=0):
    """Mock Anthropic Message with markdown text content."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage={
            "input_tokens": in_t, "output_tokens": out_t,
            "cache_read_input_tokens": cr_t, "cache_creation_input_tokens": cw_t,
        },
    )


def load_univest_matrix():
    if not UNIVEST_MATRIX.is_file():
        return None
    return json.loads(UNIVEST_MATRIX.read_text())


# ─── synthesize tests ───────────────────────────────────────────────────────

def test_synthesize_imports_and_has_default_model():
    from simul2design.synthesize.synthesize import (
        run_synthesize, build_system_prompt, build_user_prompt, DEFAULT_MODEL,
    )
    assert DEFAULT_MODEL == "claude-opus-4-7"
    sp = build_system_prompt()
    assert "synthesize" in sp.lower()
    assert "elements" in sp
    assert "per_segment_predicted" in sp


def test_synthesize_user_prompt_includes_inputs_and_no_narrative():
    """Ensure the prompt does NOT include any narrative / IDEA.md content — only data."""
    from simul2design.synthesize.synthesize import build_user_prompt
    matrix = {"client": "test", "segments": [{"id": "s1", "weight": 1.0}]}
    ws = {"dimensions": {}}
    prompt = build_user_prompt(matrix, ws, conservatism_mode="balanced")
    assert "test" in prompt
    assert "weighted_scores.json" in prompt
    assert "element_matrix.json" in prompt
    # The function signature has no idea/narrative parameter — guarantees we can't
    # accidentally feed client preference into the prompt
    import inspect
    sig = inspect.signature(build_user_prompt)
    assert "narrative" not in sig.parameters
    assert "idea" not in sig.parameters


def test_synthesize_with_mocked_llm():
    from simul2design.synthesize.synthesize import run_synthesize
    matrix = load_univest_matrix() or {"client": "test", "segments": [], "variants": []}
    ws = {"dimensions": {}, "audience_weights": {}}
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_json_response({
        "elements": {
            "layout": {
                "value": "full_screen_dark", "confidence": "high", "untested": False,
                "citation": {"type": "observed_v4_match", "ref": "matrix.V4.layout",
                             "verbatim_quote": "V4 uses dark theme"},
                "rationale_one_line": "V4 demonstrated dark theme works",
            },
        },
        "per_segment_predicted": {
            "skeptical_investor": {
                "baseline_variant": "V4", "baseline_conversion": 0.25,
                "predicted_point": 0.35, "predicted_range": [0.30, 0.40],
                "drivers": [{"lever": "trade_evidence", "expected_pts": 5,
                             "evidence": "removes 100% friction"}],
                "kill_condition": "Skeptical conv < 27% over 2 weeks",
            },
            "weighted_overall": {
                "predicted_point": 0.51, "predicted_range": [0.45, 0.56],
                "computation": "0.24×0.35 + ...",
            },
        },
        "untested_stack_count": 1,
        "confidence_grade_overall": "medium-high",
        "confidence_rationale": "Most picks are observed-pattern matches",
    })

    result, usage, err = run_synthesize(matrix, ws, anthropic_client=fake_client)
    assert err is None
    assert "elements" in result
    assert result["client"] == matrix.get("client", "unknown")
    assert "model_used" in result
    assert "audience_weights_used" in result
    # Verify cache_control was set on the system message
    call = fake_client.messages.create.call_args
    assert call.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    # Adaptive thinking on Opus
    assert call.kwargs.get("thinking") == {"type": "adaptive"}


def test_synthesize_handles_invalid_json_response():
    from simul2design.synthesize.synthesize import run_synthesize
    fake_client = MagicMock()
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="not json at all")],
        usage={"input_tokens": 100, "output_tokens": 50,
               "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
    )
    result, usage, err = run_synthesize({"client": "test", "segments": []},
                                          {"dimensions": {}},
                                          anthropic_client=fake_client)
    assert err is not None
    assert "Failed to parse JSON" in err
    assert result.get("_error") is not None


# ─── adversary tests ────────────────────────────────────────────────────────

def test_adversary_signature_excludes_narrative():
    """Per AGENT.md: adversary must NOT receive client preference / IDEA.md content."""
    from simul2design.synthesize.adversary import run_adversary
    import inspect
    sig = inspect.signature(run_adversary)
    assert "narrative" not in sig.parameters
    assert "idea" not in sig.parameters


def test_adversary_with_mocked_llm():
    from simul2design.synthesize.adversary import run_adversary
    matrix = load_univest_matrix() or {"client": "test"}
    ws = {"dimensions": {}}
    sv = {
        "variant_id": "V5",
        "elements": {"trade_evidence": {"value": "real_closed_trade", "untested": True}},
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_json_response({
        "blind_review": True,
        "objections": [
            {
                "id": "obj-001",
                "targets": ["trade_evidence"],
                "severity": "operational_precondition",
                "title": "Real closed trade requires backend SLA",
                "challenge": "If the backend has no recent winning trade...",
                "kill_condition": "v5_closed_trade_card_hidden rate > 20% for 24h",
                "suggested_revision": None,
            },
        ],
        "summary": {
            "blockers_v2": 0, "operational_preconditions_v2": 1,
            "should_fixes_v2": 0, "watch_items_v2": 0,
            "recommends": "approve_with_operational_preconditions",
            "v2_summary_one_line": "1 op precondition; no blockers",
        },
    })
    result, usage, err = run_adversary(matrix, ws, sv, anthropic_client=fake_client)
    assert err is None
    assert "objections" in result
    assert len(result["objections"]) == 1
    assert result["objections"][0]["severity"] == "operational_precondition"
    assert result["model_used"]
    # Adaptive thinking enabled for Opus
    call = fake_client.messages.create.call_args
    assert call.kwargs.get("thinking") == {"type": "adaptive"}


# ─── generate-spec tests ────────────────────────────────────────────────────

def test_generate_spec_with_mocked_llm():
    from simul2design.synthesize.generate_spec import run_generate_spec
    matrix = load_univest_matrix() or {"client": "test", "segments": []}
    ws = {"dimensions": {}}
    sv = {"variant_id": "V5", "elements": {}}
    adv = {"objections": [], "summary": {}}
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_text_response(
        "# V5 buildable spec\n\n## 0. Executive summary\n\nThe decision: ship V5...\n"
    )
    md, usage, err = run_generate_spec(matrix, ws, sv, adv, anthropic_client=fake_client)
    assert err is None
    assert "<!-- Generated by simul2design" in md
    assert "## 0. Executive summary" in md
    # Sonnet by default, no adaptive thinking
    call = fake_client.messages.create.call_args
    assert "sonnet" in call.kwargs["model"]
    assert call.kwargs.get("thinking") is None


def test_generate_spec_unwraps_markdown_fence():
    from simul2design.synthesize.generate_spec import run_generate_spec
    fake_client = MagicMock()
    fenced = "```markdown\n# V5 spec\n\n## 0. Summary\n```"
    fake_client.messages.create.return_value = make_mock_text_response(fenced)
    md, _, err = run_generate_spec({"client": "x"}, {}, {"variant_id": "V"}, {},
                                     anthropic_client=fake_client)
    assert err is None
    assert "```markdown" not in md
    assert "# V5 spec" in md


# ─── pipeline integration ───────────────────────────────────────────────────

def test_pipeline_full_cascade_end_to_end():
    """SynthesisPipeline(run_full_cascade=True) calls all 3 LLM steps and
    returns synthesized_variant + adversary_review + spec_markdown."""
    from simul2design import SynthesisPipeline, ComparisonData

    if not FIXTURE_UNIVEST.is_file():
        return
    raw = json.loads(FIXTURE_UNIVEST.read_text())
    cd = ComparisonData(**raw)

    fake_client = MagicMock()
    # Side-effect routing: first call is automap-llm, then synthesize, adversary, generate-spec.
    call_count = {"n": 0}

    def side_effect(**kwargs):
        call_count["n"] += 1
        msg_text = kwargs["messages"][0]["content"] if kwargs.get("messages") else ""
        # Route based on the LEAD PHRASE of the system prompt — substring match on
        # role keywords is too loose because spec-writer's prompt mentions
        # "adversary's op_precondition objections" which would match the adversary check.
        sys_text = kwargs.get("system", [{}])[0].get("text", "")

        # automap-llm — distinguishable by user-message shape
        if "Variant:" in msg_text and "Dimension:" in msg_text and "Allowed values:" in msg_text:
            return make_mock_json_response(
                {"value": "Unlock FREE trade", "confidence": "high",
                 "reasoning": "matched"},
                in_t=300, out_t=30,
            )
        # Cascade steps — check lead phrase precisely
        if sys_text.startswith("You are the synthesizer"):
            return make_mock_json_response({
                "elements": {"layout": {"value": "full_screen_dark", "confidence": "high",
                                          "untested": False,
                                          "citation": {"type": "obs", "ref": "x", "verbatim_quote": ""},
                                          "rationale_one_line": "ok"}},
                "per_segment_predicted": {
                    "weighted_overall": {"predicted_point": 0.51,
                                          "predicted_range": [0.45, 0.56],
                                          "computation": "x"},
                },
                "untested_stack_count": 1,
                "confidence_grade_overall": "medium",
                "confidence_rationale": "test",
            }, in_t=3000, out_t=500)
        if sys_text.startswith("You are the adversary"):
            return make_mock_json_response({
                "blind_review": True,
                "objections": [{"id": "obj-001", "targets": ["x"],
                                 "severity": "operational_precondition",
                                 "title": "test", "challenge": "x",
                                 "kill_condition": "x", "suggested_revision": None}],
                "summary": {"blockers_v2": 0, "operational_preconditions_v2": 1,
                             "should_fixes_v2": 0, "watch_items_v2": 0,
                             "recommends": "approve_with_operational_preconditions",
                             "v2_summary_one_line": "test"},
            }, in_t=3000, out_t=500)
        if sys_text.startswith("You are the spec-writer"):
            return make_mock_text_response("# V5 spec\n\n## 0. Summary\n\nShip V5.",
                                            in_t=3500, out_t=2000)
        # Fallback for any unexpected call
        return make_mock_json_response({"value": "x", "confidence": "low", "reasoning": "fallback"})

    fake_client.messages.create.side_effect = side_effect

    pipeline = SynthesisPipeline(
        anthropic_client=fake_client,
        run_full_cascade=True,
        max_llm_cells=3,  # limit automap-llm cost
    )
    result = asyncio.run(pipeline.run(cd, client_slug="univest-cascade-test"))

    # All three new fields populated
    assert result.synthesized_variant is not None
    assert result.adversary_review is not None
    assert result.spec_markdown is not None

    # Synthesized variant has expected envelope
    assert result.synthesized_variant.get("client_slug") in (None, "univest-cascade-test") or \
           result.synthesized_variant.get("client") == "univest-cascade-test"
    assert "elements" in result.synthesized_variant
    assert "model_used" in result.synthesized_variant

    # Adversary review has objections + summary
    assert "objections" in result.adversary_review
    assert "summary" in result.adversary_review

    # Spec markdown has the generated-by header + content
    assert "<!-- Generated by simul2design" in result.spec_markdown
    assert "## 0. Summary" in result.spec_markdown

    # Cost is tracked
    assert result.estimated_cost_usd > 0
    assert result.token_usage.input_tokens > 0


def test_pipeline_full_cascade_off_by_default():
    """run_full_cascade defaults to False — backward compat with Sprint B Phase 1."""
    from simul2design import SynthesisPipeline, ComparisonData
    if not FIXTURE_UNIVEST.is_file():
        return
    raw = json.loads(FIXTURE_UNIVEST.read_text())
    cd = ComparisonData(**raw)
    pipeline = SynthesisPipeline(skip_llm_fallback=True)  # no full_cascade kwarg
    result = asyncio.run(pipeline.run(cd, client_slug="univest-default-test"))
    # Cascade fields stay None
    assert result.synthesized_variant is None
    assert result.adversary_review is None
    assert result.spec_markdown is None


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    test_synthesize_imports_and_has_default_model,
    test_synthesize_user_prompt_includes_inputs_and_no_narrative,
    test_synthesize_with_mocked_llm,
    test_synthesize_handles_invalid_json_response,
    test_adversary_signature_excludes_narrative,
    test_adversary_with_mocked_llm,
    test_generate_spec_with_mocked_llm,
    test_generate_spec_unwraps_markdown_fence,
    test_pipeline_full_cascade_end_to_end,
    test_pipeline_full_cascade_off_by_default,
]


def main() -> int:
    print(f"Running {len(TESTS)} tests against simul2design/synthesize/ Phase 2...\n")
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
