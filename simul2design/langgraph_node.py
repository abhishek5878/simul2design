"""LangGraph node wrapper.

Drop into Apriori's existing LangGraph after their simulation node:

    from simul2design.langgraph_node import synthesis_node

    graph = StateGraph(AprioriState)
    graph.add_node("simulation", run_apriori_simulation)
    graph.add_node("synthesis", synthesis_node)
    graph.add_edge("simulation", "synthesis")
    graph.add_edge("synthesis", "render_dashboard")

The node:
- Reads `state["ab_report"]` (apriori_simulation_engine canonical output) OR
  `state["comparison_data"]` (legacy / direct ComparisonData dict).
  If both are present, `ab_report` wins.
- Resolves `state["client_slug"]` (or `state["simulation_id"]` as fallback).
- Runs the SynthesisPipeline (ingest → automap-rules → automap-llm → optional cascade).
- Writes `state["synthesis_result"]` (a `SynthesisResult` dict) and
  `state["synthesis_ready_for_human"]` (bool).

LangGraph itself is NOT a hard dependency — this module works with any
state-graph framework that calls async functions with a dict-like state.
"""

from __future__ import annotations
from typing import Any, TypedDict, Optional

from simul2design.pipeline import SynthesisPipeline
from simul2design.schemas import ComparisonData, SynthesisResult
from simul2design.adapters.ab_report import from_ab_report


class SynthesisNodeStateInput(TypedDict, total=False):
    """Fields the node reads from graph state.

    Marked total=False because LangGraph state contains many other fields
    that aren't ours; we only need these.
    """
    ab_report: dict[str, Any]         # apriori_simulation_engine AbReport dict (preferred)
    comparison_data: dict[str, Any]   # legacy ComparisonData dict (fallback)
    client_slug: str                  # e.g. "univest" — derived from sim id if missing
    simulation_id: str                # fallback for client_slug if explicit slug absent


class SynthesisNodeStateOutput(TypedDict):
    """Fields the node writes to graph state."""
    synthesis_result: dict[str, Any]
    synthesis_ready_for_human: bool
    synthesis_input_source: str  # 'ab_report' | 'comparison_data'


def _derive_client_slug(state: dict[str, Any]) -> str:
    """Pick a client slug from state. Prefers explicit field, falls back to sim id."""
    if state.get("client_slug"):
        return state["client_slug"]
    sid = state.get("simulation_id")
    if sid:
        return str(sid).lower().replace("_", "-")
    ab = state.get("ab_report") or {}
    client = (ab.get("meta") or {}).get("client")
    if client:
        return str(client).lower().replace(" ", "-").replace("_", "-")
    sid = (ab.get("meta") or {}).get("simulation_id")
    if sid:
        return str(sid).lower().replace("_", "-")
    cd = state.get("comparison_data") or {}
    sid = cd.get("metadata", {}).get("simulation_id")
    if sid:
        return str(sid).lower().replace("_", "-")
    return "unknown"


async def synthesis_node(
    state: dict[str, Any],
    *,
    pipeline: Optional[SynthesisPipeline] = None,
) -> dict[str, Any]:
    """LangGraph-compatible async node.

    Args:
        state: Graph state. Must contain `comparison_data`. Optionally
            `client_slug` or `simulation_id` (used to derive a slug).
        pipeline: Pre-configured SynthesisPipeline. If None, a default one
            is constructed (Sonnet 4.6 LLM model, reads ANTHROPIC_API_KEY
            from env at first LLM call).

    Returns:
        Partial state update: `{"synthesis_result": {...}, "synthesis_ready_for_human": bool}`.
    """
    if pipeline is None:
        pipeline = SynthesisPipeline()

    ab_report = state.get("ab_report")
    raw_comp = state.get("comparison_data")

    if ab_report is not None:
        client_slug = _derive_client_slug(state)
        adapted = from_ab_report(ab_report, client_slug=client_slug if client_slug != "unknown" else None)
        comp = ComparisonData(**adapted)
        source = "ab_report"
    elif raw_comp is not None:
        comp = raw_comp if isinstance(raw_comp, ComparisonData) else ComparisonData(**raw_comp)
        client_slug = _derive_client_slug(state)
        source = "comparison_data"
    else:
        raise ValueError(
            "synthesis_node: state must contain 'ab_report' (apriori_simulation_engine "
            "AbReport dict) or 'comparison_data' (legacy ComparisonData dict)."
        )

    result: SynthesisResult = await pipeline.run(comp, client_slug=client_slug)

    return {
        "synthesis_result": result.model_dump(),
        "synthesis_ready_for_human": result.ready_for_synthesis,
        "synthesis_input_source": source,
    }


def synthesis_node_sync(
    state: dict[str, Any],
    *,
    pipeline: Optional[SynthesisPipeline] = None,
) -> dict[str, Any]:
    """Sync version of synthesis_node — for graph frameworks that want sync nodes.

    Internally calls asyncio.run on the async version. Don't use inside an
    already-running event loop (use `synthesis_node` directly there).
    """
    import asyncio
    return asyncio.run(synthesis_node(state, pipeline=pipeline))
