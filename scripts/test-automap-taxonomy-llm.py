#!/usr/bin/env python3
"""
test-automap-taxonomy-llm.py — test suite for scripts/automap-taxonomy-llm.py.

Mocks the Anthropic SDK so tests run without an API key. Covers helpers
(taxonomy parsing, prompt building, cell selection, cost math) and a
full mocked end-to-end run against the univest fixture.

Usage:
    scripts/test-automap-taxonomy-llm.py
"""

from __future__ import annotations
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
LLM_MAPPER = ROOT / "scripts" / "automap-taxonomy-llm.py"
INGEST = ROOT / "scripts" / "ingest-apriori.py"
AUTOMAP = ROOT / "scripts" / "automap-taxonomy.py"
FIXTURE_UNIVEST = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"

TMP_BASE = Path("/tmp/test-automap-llm")

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


# ─── helpers ────────────────────────────────────────────────────────────────

def import_mapper():
    """Import automap-taxonomy-llm as a module (with hyphen-to-underscore name)."""
    spec = importlib.util.spec_from_file_location("automap_llm", LLM_MAPPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_tmp_dir(name: str) -> Path:
    p = TMP_BASE / name
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def setup_fixture_dir(name: str) -> Path:
    """Run ingest-apriori + automap-taxonomy to seed a /tmp dir for testing."""
    out_dir = make_tmp_dir(name)
    subprocess.run([sys.executable, str(INGEST), "univest-test",
                    "--from-comparison-json", str(FIXTURE_UNIVEST),
                    "--no-fetch-screenshots", "-o", str(out_dir)],
                   capture_output=True, check=True, timeout=20)
    subprocess.run([sys.executable, str(AUTOMAP), "univest-test", "-o", str(out_dir)],
                   capture_output=True, check=True, timeout=20)
    return out_dir


def make_mock_response(value: str, confidence: str = "high",
                       reasoning: str = "test reasoning",
                       input_tokens: int = 500, output_tokens: int = 50,
                       cache_read: int = 0, cache_write: int = 0) -> MagicMock:
    """Build a mock anthropic Message response."""
    text_block = SimpleNamespace(
        type="text",
        text=json.dumps({"value": value, "confidence": confidence, "reasoning": reasoning}),
    )
    return SimpleNamespace(
        content=[text_block],
        usage={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_write,
        },
    )


# ─── unit tests ─────────────────────────────────────────────────────────────

def test_taxonomy_parses_all_dims():
    mod = import_mapper()
    taxonomy_md = mod.load_taxonomy_text()
    allowed = mod.parse_allowed_values(taxonomy_md)
    expected = {"layout", "modal_interrupt", "branding", "price_visibility",
                "cta_style", "cta_stack", "urgency_mechanism",
                "refund_or_guarantee_copy", "trust_signal", "evidence_detail"}
    missing = expected - set(allowed.keys())
    assert not missing, f"missing dimensions in parsed taxonomy: {missing}"
    # Spot-check a few values
    assert "bottom_modal" in allowed["layout"]
    assert "full_screen_dark" in allowed["layout"]
    assert "crown_header" in allowed["branding"]
    assert "regulatory_plus_evidence" in allowed["trust_signal"]


def test_select_cells_default_needs_review_only():
    """select_cells_to_map by default returns only needs_review cells, not low_default."""
    mod = import_mapper()
    trace = {"per_variant": {
        "V1": {
            "layout": {"value": "full_screen", "confidence": "high"},
            "branding": {"value": "none", "confidence": "low_default"},
            "cta_primary_label": {"value": "__needs_review__", "confidence": "needs_review"},
        },
    }}
    cells = mod.select_cells_to_map(trace, include_low_default=False)
    assert len(cells) == 1
    vid, dim, _ = cells[0]
    assert (vid, dim) == ("V1", "cta_primary_label")


def test_select_cells_include_low_default():
    """--include-low-default also picks up low_default cells."""
    mod = import_mapper()
    trace = {"per_variant": {
        "V1": {
            "layout": {"value": "full_screen", "confidence": "high"},
            "branding": {"value": "none", "confidence": "low_default"},
            "cta_primary_label": {"value": "__needs_review__", "confidence": "needs_review"},
        },
    }}
    cells = mod.select_cells_to_map(trace, include_low_default=True)
    assert len(cells) == 2
    dims = {c[1] for c in cells}
    assert dims == {"branding", "cta_primary_label"}


def test_build_system_prompt_contains_taxonomy_and_format_rules():
    mod = import_mapper()
    taxonomy_md = mod.load_taxonomy_text()
    sp = mod.build_system_prompt(taxonomy_md)
    # Must include the taxonomy verbatim
    assert "Base dimensions" in sp
    assert "high_contrast_green" in sp
    # Must specify JSON output format
    assert '"value"' in sp and '"reasoning"' in sp and '"confidence"' in sp
    # Must instruct to use enum values only
    assert "ONLY values from the dimension's allowed set" in sp


def test_build_user_prompt_includes_prior_verdict_and_text():
    mod = import_mapper()
    prompt = mod.build_user_prompt(
        variant_id="V4",
        dimension="layout",
        allowed_values=["bottom_modal", "full_screen", "full_screen_dark"],
        variant_context="VARIANT_DESCRIPTION: Dark theme, full-screen.",
        prior_verdict={"value": "full_screen", "confidence": "low_default", "matched_pattern": None},
    )
    assert "V4" in prompt
    assert "layout" in prompt
    assert "Dark theme" in prompt
    assert "full_screen_dark" in prompt
    assert "low_default" in prompt


def test_estimate_cost_sonnet_caching():
    mod = import_mapper()
    # Subsequent (cached) call: 100 input + 50 output + 1000 cache_read + 0 cache_write
    cost = mod.estimate_cost(
        {"input_tokens": 100, "output_tokens": 50,
         "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 0},
        "claude-sonnet-4-6")
    # 0.0001 × 3 + 0.00005 × 15 + 0.001 × 0.30 = 0.0003 + 0.00075 + 0.0003 = 0.00135
    assert 0.0010 < cost < 0.0020, f"unexpected cost: {cost}"


def test_call_llm_with_mocked_client():
    """call_llm parses a JSON response and returns the dict."""
    mod = import_mapper()
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_response(
        value="full_screen_dark", confidence="high", reasoning="dark theme mentioned")
    parsed, usage, err = mod.call_llm(fake_client, "claude-sonnet-4-6", "system", "user")
    assert err is None
    assert parsed == {"value": "full_screen_dark", "confidence": "high", "reasoning": "dark theme mentioned"}
    assert usage["input_tokens"] == 500
    # Verify the call shape (system has cache_control)
    call_args = fake_client.messages.create.call_args
    assert call_args.kwargs["model"] == "claude-sonnet-4-6"
    assert call_args.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_call_llm_strips_markdown_fences():
    """LLM responses wrapped in ```json...``` get unwrapped."""
    mod = import_mapper()
    fake_client = MagicMock()
    fenced = '```json\n{"value": "x", "confidence": "high", "reasoning": "y"}\n```'
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=fenced)],
        usage={"input_tokens": 100, "output_tokens": 50,
               "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
    )
    parsed, _, err = mod.call_llm(fake_client, "claude-sonnet-4-6", "system", "user")
    assert err is None
    assert parsed["value"] == "x"


def test_call_llm_handles_invalid_json():
    """Garbled JSON returns an error."""
    mod = import_mapper()
    fake_client = MagicMock()
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="not json at all")],
        usage={"input_tokens": 100, "output_tokens": 50,
               "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
    )
    parsed, _, err = mod.call_llm(fake_client, "claude-sonnet-4-6", "system", "user")
    assert parsed is None
    assert "Failed to parse JSON" in err


def test_call_llm_handles_auth_error():
    """AuthenticationError surfaces as a clean error message."""
    import anthropic
    mod = import_mapper()
    fake_client = MagicMock()
    # Construct a real AuthenticationError (needs message + response + body)
    fake_response = SimpleNamespace(status_code=401, headers={}, request=SimpleNamespace(method="POST", url=""))
    fake_client.messages.create.side_effect = anthropic.AuthenticationError(
        message="Invalid key", response=fake_response, body={"error": {"message": "Invalid key"}})
    parsed, _, err = mod.call_llm(fake_client, "claude-sonnet-4-6", "system", "user")
    assert parsed is None
    assert "Invalid ANTHROPIC_API_KEY" in err


# ─── integration test ──────────────────────────────────────────────────────

def test_dry_run_no_api_calls():
    """--dry-run mode runs without ANTHROPIC_API_KEY set; no API calls made."""
    out_dir = setup_fixture_dir("dry-run")
    # Ensure no real call by clearing the API key for this subprocess
    env = {**__import__("os").environ, "ANTHROPIC_API_KEY": ""}
    result = subprocess.run(
        [sys.executable, str(LLM_MAPPER), "univest-test",
         "--dry-run", "-o", str(out_dir)],
        capture_output=True, text=True, timeout=15, env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "(dry-run mode" in result.stdout or "would call LLM" in result.stdout
    # Matrix not modified
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    assert "_llm_pass" not in matrix.get("extraction_confidence", {})


def test_no_api_key_errors_cleanly():
    """Without --dry-run and without API key, should exit with error."""
    out_dir = setup_fixture_dir("no-api-key")
    env = {**__import__("os").environ}
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(LLM_MAPPER), "univest-test", "-o", str(out_dir)],
        capture_output=True, text=True, timeout=15, env=env,
    )
    assert result.returncode == 2, f"unexpected exit: {result.returncode}"
    assert "ANTHROPIC_API_KEY" in result.stderr


def test_full_run_with_mocked_api():
    """End-to-end: mocked LLM responses update the matrix + trace correctly."""
    out_dir = setup_fixture_dir("full-mocked")
    # Read the trace to find which cells need_review (just one for univest: V3.cta_primary_label)
    trace_before = json.loads((out_dir / "automap-trace.json").read_text())
    before_v3_cta = trace_before["per_variant"]["V3"]["cta_primary_label"]
    assert before_v3_cta["confidence"] == "needs_review"

    # Patch anthropic.Anthropic to return a canned response
    mod = import_mapper()
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_response(
        value="Unlock FREE trade", confidence="high",
        reasoning="V3 inherits CTA from V2 which uses 'Unlock FREE trade'")

    with patch("anthropic.Anthropic", return_value=fake_client), \
         patch.dict(__import__("os").environ, {"ANTHROPIC_API_KEY": "test-key"}):
        # Run main() directly to use the patched anthropic module
        sys.argv = [str(LLM_MAPPER), "univest-test", "-o", str(out_dir)]
        rc = mod.main()
        assert rc == 0

    # Verify matrix was updated
    matrix_after = json.loads((out_dir / "element_matrix.json").read_text())
    v3 = next(v for v in matrix_after["variants"] if v["id"] == "V3")
    assert v3["elements"]["cta_primary_label"] == "Unlock FREE trade"

    # Verify trace was updated with auto_mapped_llm tier
    trace_after = json.loads((out_dir / "automap-trace.json").read_text())
    after_v3_cta = trace_after["per_variant"]["V3"]["cta_primary_label"]
    assert after_v3_cta["confidence"] == "auto_mapped_llm"
    assert after_v3_cta["llm_confidence"] == "high"
    assert "_llm_pass" in trace_after
    assert trace_after["_llm_pass"]["successes_high_or_medium"] == 1


def test_low_confidence_does_not_update_matrix():
    """If LLM returns low confidence, matrix value is left as-is."""
    out_dir = setup_fixture_dir("low-conf")
    matrix_before = json.loads((out_dir / "element_matrix.json").read_text())
    v3_cta_before = next(v for v in matrix_before["variants"] if v["id"] == "V3")["elements"]["cta_primary_label"]

    mod = import_mapper()
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_response(
        value="some_guess", confidence="low",  # low → don't update
        reasoning="not sure")

    with patch("anthropic.Anthropic", return_value=fake_client), \
         patch.dict(__import__("os").environ, {"ANTHROPIC_API_KEY": "test-key"}):
        sys.argv = [str(LLM_MAPPER), "univest-test", "-o", str(out_dir)]
        rc = mod.main()
        assert rc == 0

    matrix_after = json.loads((out_dir / "element_matrix.json").read_text())
    v3_cta_after = next(v for v in matrix_after["variants"] if v["id"] == "V3")["elements"]["cta_primary_label"]
    assert v3_cta_after == v3_cta_before, "low-conf LLM result shouldn't have updated matrix"


def test_max_cells_caps_iterations():
    """--max-cells limits the number of cells attempted."""
    out_dir = setup_fixture_dir("max-cells")
    mod = import_mapper()
    fake_client = MagicMock()
    fake_client.messages.create.return_value = make_mock_response(value="x", confidence="high")

    with patch("anthropic.Anthropic", return_value=fake_client), \
         patch.dict(__import__("os").environ, {"ANTHROPIC_API_KEY": "test-key"}):
        sys.argv = [str(LLM_MAPPER), "univest-test",
                    "--include-low-default", "--max-cells", "2",
                    "-o", str(out_dir)]
        rc = mod.main()
        assert rc == 0

    # Only 2 calls should have been made
    assert fake_client.messages.create.call_count == 2


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    # Unit
    test_taxonomy_parses_all_dims,
    test_select_cells_default_needs_review_only,
    test_select_cells_include_low_default,
    test_build_system_prompt_contains_taxonomy_and_format_rules,
    test_build_user_prompt_includes_prior_verdict_and_text,
    test_estimate_cost_sonnet_caching,
    test_call_llm_with_mocked_client,
    test_call_llm_strips_markdown_fences,
    test_call_llm_handles_invalid_json,
    test_call_llm_handles_auth_error,
    # Integration (mocked)
    test_dry_run_no_api_calls,
    test_no_api_key_errors_cleanly,
    test_full_run_with_mocked_api,
    test_low_confidence_does_not_update_matrix,
    test_max_cells_caps_iterations,
]


def main() -> int:
    if not LLM_MAPPER.is_file():
        print(f"Error: {LLM_MAPPER} not found", file=sys.stderr)
        return 1

    print(f"Running {len(TESTS)} tests against {LLM_MAPPER.name}...\n")
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

    if TMP_BASE.exists():
        shutil.rmtree(TMP_BASE)

    print()
    print(f"{GREEN}Passed:{RESET} {len(passed)}/{len(TESTS)}")
    if failed:
        print(f"{RED}Failed:{RESET} {len(failed)}")
        return 1
    print(f"{GREEN}All tests passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
