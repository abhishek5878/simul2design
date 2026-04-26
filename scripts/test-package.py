#!/usr/bin/env python3
"""test-package.py — tests for the simul2design package public API.

Covers what's NEW in the package layer (the underlying logic is tested by
test-ingest-apriori, test-automap-taxonomy, test-automap-taxonomy-llm):

- SynthesisPipeline: end-to-end run (rules-only mode, no API needed)
- SynthesisPipeline: with mocked Anthropic client
- LangGraph node: state in → state out, with mocked pipeline
- Pydantic schemas: validation, serialization
- Bundled taxonomy stays in sync with .claude/rules/

Usage:
    scripts/test-package.py
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

FIXTURE_UNIVEST = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
FIXTURE_SIMPLE = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-example.json"
TAXONOMY_REPO = ROOT / ".claude" / "rules" / "element-taxonomy-base.md"
TAXONOMY_BUNDLED = ROOT / "simul2design" / "taxonomy_data" / "element-taxonomy-base.md"

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


# ─── tests ──────────────────────────────────────────────────────────────────

def test_package_imports():
    """All public names import from the package root."""
    from simul2design import (
        SynthesisPipeline, SynthesisResult, ComparisonData, CellRef,
        TokenUsage, __version__,
    )
    assert __version__ == "0.1.0", f"unexpected version: {__version__}"


def test_schemas_validation():
    """ComparisonData validates required fields; rejects missing ones."""
    from simul2design import ComparisonData
    from pydantic import ValidationError

    # Loading the real univest fixture works
    raw = json.loads(FIXTURE_UNIVEST.read_text())
    cd = ComparisonData(**raw)
    assert cd.metadata["persona_count"] == 50
    assert len(cd.variants) == 5
    assert len(cd.segment_verdicts) == 4

    # Missing required field rejected
    raw_bad = dict(raw)
    del raw_bad["variants"]
    try:
        ComparisonData(**raw_bad)
    except ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError for missing 'variants'")

    # Extra fields are preserved (model_config extra='allow')
    raw_extra = dict(raw)
    raw_extra["custom_field"] = "future-proof"
    cd = ComparisonData(**raw_extra)
    # Pydantic v2 puts extras on the model
    assert cd.model_dump().get("custom_field") == "future-proof"


def test_synthesis_result_schema():
    from simul2design import SynthesisResult, CellRef, TokenUsage
    result = SynthesisResult(
        client_slug="test",
        pipeline_version="0.1.0",
        element_matrix={"foo": "bar"},
        automap_trace={"_summary": {}},
        source_markdown="# test",
        cells_needing_review=[
            CellRef(variant_id="V1", dimension="layout", confidence="needs_review"),
        ],
        ready_for_synthesis=False,
        estimated_cost_usd=0.05,
    )
    assert result.has_full_spec is False  # spec_markdown is None
    assert len(result.cells_needing_review) == 1


def test_pipeline_rules_only_mode_no_api_needed():
    """SynthesisPipeline(skip_llm_fallback=True) runs without ANTHROPIC_API_KEY."""
    from simul2design import SynthesisPipeline, ComparisonData

    raw = json.loads(FIXTURE_UNIVEST.read_text())
    cd = ComparisonData(**raw)

    pipeline = SynthesisPipeline(skip_llm_fallback=True)
    result = asyncio.run(pipeline.run(cd, client_slug="univest-test"))

    assert result.client_slug == "univest-test"
    assert result.pipeline_version == "0.1.0"
    assert "variants" in result.element_matrix
    assert len(result.element_matrix["variants"]) == 5
    assert "_summary" in result.automap_trace
    # Rules-only mode: no LLM cost
    assert result.estimated_cost_usd == 0.0
    assert result.token_usage.input_tokens == 0
    # Should match what test-automap-taxonomy reported: ~75% match, 1 needs_review
    n_needs_review = sum(1 for c in result.cells_needing_review if c.confidence == "needs_review")
    assert 0 <= n_needs_review <= 5, f"unexpected needs_review count: {n_needs_review}"
    # source_markdown was generated
    assert "# Apriori simulation — univest-test" in result.source_markdown
    assert "## 1. Variants" in result.source_markdown


def test_pipeline_with_mocked_anthropic_client():
    """SynthesisPipeline routes LLM calls through the provided anthropic client."""
    from simul2design import SynthesisPipeline, ComparisonData

    raw = json.loads(FIXTURE_UNIVEST.read_text())
    cd = ComparisonData(**raw)

    fake_client = MagicMock()
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(
            type="text",
            text='{"value": "Unlock FREE trade", "confidence": "high", "reasoning": "test"}',
        )],
        usage={
            "input_tokens": 500, "output_tokens": 50,
            "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
        },
    )

    pipeline = SynthesisPipeline(anthropic_client=fake_client)
    result = asyncio.run(pipeline.run(cd, client_slug="univest-mocked"))

    # The client was called for the needs_review cell(s)
    assert fake_client.messages.create.called, "expected LLM call for needs_review cells"
    # The result's automap_trace has _llm_pass populated
    assert "_llm_pass" in result.automap_trace
    assert result.estimated_cost_usd > 0


def test_pipeline_accepts_raw_dict_or_pydantic_model():
    """ComparisonData OR raw dict both work as input."""
    from simul2design import SynthesisPipeline, ComparisonData

    raw = json.loads(FIXTURE_SIMPLE.read_text())

    pipeline = SynthesisPipeline(skip_llm_fallback=True)

    # As Pydantic model
    cd_model = ComparisonData(**raw)
    r1 = asyncio.run(pipeline.run(cd_model, client_slug="fixturo-a"))
    assert len(r1.element_matrix["variants"]) == 3

    # As raw dict
    r2 = asyncio.run(pipeline.run(raw, client_slug="fixturo-b"))
    assert len(r2.element_matrix["variants"]) == 3

    # Same matrix shape regardless of input form
    assert [v["id"] for v in r1.element_matrix["variants"]] == \
           [v["id"] for v in r2.element_matrix["variants"]]


def test_langgraph_node_state_in_state_out():
    """The node reads comparison_data + client_slug from state and writes synthesis_result."""
    from simul2design.langgraph_node import synthesis_node
    from simul2design import SynthesisPipeline

    raw = json.loads(FIXTURE_SIMPLE.read_text())

    pipeline = SynthesisPipeline(skip_llm_fallback=True)
    state = {
        "comparison_data": raw,
        "client_slug": "fixturo-graph",
        # other fields like a real LangGraph state would have are ignored
        "session_id": "ses_abc",
        "user_id": "usr_xyz",
    }
    update = asyncio.run(synthesis_node(state, pipeline=pipeline))
    assert "synthesis_result" in update
    assert "synthesis_ready_for_human" in update
    assert update["synthesis_result"]["client_slug"] == "fixturo-graph"
    # The dict shape matches SynthesisResult fields
    assert "element_matrix" in update["synthesis_result"]
    assert "cells_needing_review" in update["synthesis_result"]


def test_langgraph_node_derives_client_slug_from_metadata():
    """If state has no client_slug, derive from comparison_data.metadata.simulation_id."""
    from simul2design.langgraph_node import synthesis_node, _derive_client_slug
    raw = json.loads(FIXTURE_SIMPLE.read_text())  # has simulation_id="FIXTURO_ONBOARDING_TEST"
    slug = _derive_client_slug({"comparison_data": raw})
    assert slug == "fixturo-onboarding-test", f"got: {slug}"


def test_langgraph_node_raises_on_missing_comparison_data():
    """Node raises ValueError if comparison_data isn't in state."""
    from simul2design.langgraph_node import synthesis_node
    try:
        asyncio.run(synthesis_node({"some_other_field": "x"}))
    except ValueError as e:
        assert "comparison_data" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_taxonomy_bundled_matches_repo():
    """Bundled taxonomy is in sync with .claude/rules/element-taxonomy-base.md."""
    if not (TAXONOMY_REPO.is_file() and TAXONOMY_BUNDLED.is_file()):
        return  # Skip if either is missing
    repo_text = TAXONOMY_REPO.read_text()
    bundled_text = TAXONOMY_BUNDLED.read_text()
    assert repo_text == bundled_text, (
        "Bundled simul2design/taxonomy_data/element-taxonomy-base.md is out of sync with "
        ".claude/rules/element-taxonomy-base.md. Re-copy the repo file into the package."
    )


def test_taxonomy_loader_returns_full_md():
    from simul2design.taxonomy import load_base_taxonomy, parse_allowed_values
    md = load_base_taxonomy()
    assert "Base dimensions" in md
    assert "high_contrast_green" in md
    allowed = parse_allowed_values(md)
    assert "layout" in allowed
    assert "full_screen_dark" in allowed["layout"]


def test_pyproject_toml_well_formed():
    """pyproject.toml parses as TOML and declares the package + scripts correctly."""
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.is_file()
    # tomllib is in Python 3.11+; tomli is the backport
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return  # No TOML reader available; can't validate but pip install will catch it
    data = tomllib.loads(pyproject.read_text())
    assert data["project"]["name"] == "simul2design"
    assert data["project"]["version"] == "0.1.0"
    assert "anthropic" in " ".join(data["project"]["dependencies"])
    assert "pydantic" in " ".join(data["project"]["dependencies"])
    # CLI entry points point at our package
    scripts = data["project"]["scripts"]
    assert "simul2design.ingest:_cli_main" in scripts.get("simul2design-ingest", "")


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    test_package_imports,
    test_schemas_validation,
    test_synthesis_result_schema,
    test_pipeline_rules_only_mode_no_api_needed,
    test_pipeline_with_mocked_anthropic_client,
    test_pipeline_accepts_raw_dict_or_pydantic_model,
    test_langgraph_node_state_in_state_out,
    test_langgraph_node_derives_client_slug_from_metadata,
    test_langgraph_node_raises_on_missing_comparison_data,
    test_taxonomy_bundled_matches_repo,
    test_taxonomy_loader_returns_full_md,
    test_pyproject_toml_well_formed,
]


def main() -> int:
    print(f"Running {len(TESTS)} tests against simul2design/ package...\n")
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
