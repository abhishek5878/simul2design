"""simul2design — Multiverse Synthesis Engine.

Turns Apriori simulation output (ComparisonData) into a buildable variant
specification. Designed to drop into Apriori's LangGraph as a synthesis node.

Quick start:

    from simul2design import SynthesisPipeline

    pipeline = SynthesisPipeline()
    result = await pipeline.run(comparison_data, client_slug="univest")

    print(result.element_matrix)         # taxonomy-normalized matrix
    print(result.cells_needing_review)   # cells the auto-mapper couldn't resolve
    print(result.estimated_cost_usd)     # LLM cost for this run

LangGraph integration:

    from simul2design.langgraph_node import synthesis_node

    graph.add_node("synthesis", synthesis_node)
    graph.add_edge("simulation", "synthesis")

See INTEGRATION.md for the full plug-in roadmap.

Phase 3c (cascade automation — synthesize/adversary/estimate-conversion/
generate-spec ported from .claude/skills/) is not yet shipped; the pipeline
returns the auto-mapped matrix + cells-needing-review for human kickoff
of the cascade.
"""

__version__ = "0.1.0"

from simul2design.schemas import (
    CellRef,
    ComparisonData,
    SynthesisResult,
    TokenUsage,
)
from simul2design.pipeline import SynthesisPipeline

__all__ = [
    "__version__",
    "SynthesisPipeline",
    "SynthesisResult",
    "ComparisonData",
    "CellRef",
    "TokenUsage",
]
