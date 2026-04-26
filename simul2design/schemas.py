"""Pydantic schemas for the public API.

Input: ComparisonData (loose validation — Apriori may add fields).
Output: SynthesisResult (everything the LangGraph node returns).

Phase 3c-only fields (synthesized_variant, adversary_review, conversion_estimates,
spec_markdown, report_html) are Optional and default to None until the cascade
is ported from .claude/skills/ to standalone Python.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class CellRef(BaseModel):
    """Reference to a single (variant, dimension) cell in the element matrix."""
    variant_id: str
    dimension: str
    confidence: str = Field(description="'low_default' | 'needs_review' | 'auto_mapped_llm' | 'high'")
    current_value: Any = None


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def add_(self, other: "TokenUsage") -> None:
        """In-place add (mutates self)."""
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens


class ComparisonData(BaseModel):
    """Apriori ComparisonData — see apriori_landing's src/components/comparator/.

    Loose validation: only the 6 fields the engine consumes are required;
    everything else is preserved as dict. Apriori may add fields without
    breaking the pipeline.
    """
    model_config = ConfigDict(extra="allow")

    metadata: dict[str, Any]
    variants: list[dict[str, Any]]
    metrics: dict[str, Any]
    segment_verdicts: list[dict[str, Any]]
    friction_provenance: list[dict[str, Any]]
    variant_screenshots: dict[str, Any]

    # Optional but commonly present
    theme_movement: dict[str, Any] = Field(default_factory=dict)
    screen_comparison: list[dict[str, Any]] = Field(default_factory=list)
    persona_journeys: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    recommended_next_test: Optional[dict[str, Any]] = None
    risks_to_monitor: list[str] = Field(default_factory=list)
    verdict: Optional[dict[str, Any]] = None


class SynthesisResult(BaseModel):
    """End-to-end output from SynthesisPipeline.

    Always-populated fields cover the automated portion (ingest → automap →
    automap-llm). Phase 3c fields populate once the cascade is ported.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Identity
    client_slug: str
    pipeline_version: str

    # Always-populated (Sprint A)
    element_matrix: dict[str, Any]
    automap_trace: dict[str, Any]
    source_markdown: str
    cells_needing_review: list[CellRef] = Field(default_factory=list)
    ready_for_synthesis: bool = False

    # Cost + usage tracking
    estimated_cost_usd: float = 0.0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    # Phase 3c — cascade outputs (None until ported from .claude/skills/)
    weighted_scores: Optional[dict[str, Any]] = None
    synthesized_variant: Optional[dict[str, Any]] = None
    adversary_review: Optional[dict[str, Any]] = None
    conversion_estimates: Optional[dict[str, Any]] = None
    spec_markdown: Optional[str] = None
    report_html: Optional[str] = None

    @property
    def has_full_spec(self) -> bool:
        """True if Phase 3c cascade ran and a buildable spec is available."""
        return self.spec_markdown is not None
