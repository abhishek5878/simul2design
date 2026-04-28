# Integration — plugging the synthesis engine into Apriori

This document covers the end-to-end product loop: Apriori simulation → our engine → buildable spec → customer-facing report → ship → post-ship calibration.

The audience is anyone integrating this engine with the [apriori_landing](https://github.com/dechrone/apriori_landing) frontend or running a new client through the pipeline.

> **Recommended integration: drop our package in as a node on Apriori's LangGraph.** See §10 below for the worked example. This eliminates the two-systems-with-handoff problem — synthesis runs in Apriori's existing graph runtime, state flows through naturally, and there's no separate hosting to maintain.

---

## 1. The product loop

```
┌─────────────────────────┐
│  Apriori sim engine     │  brand uploads variants → simulation runs
│  (apriori.work)         │  → ComparisonData object emitted
└────────────┬────────────┘
             │
             │  source.md  +  source-screenshots/  +  ComparisonData JSON
             ▼
┌─────────────────────────┐
│  parse-simulation       │  taxonomy normalization → element_matrix.json
│  weigh-segments         │  evidence-tier classification → weighted_scores.json
│  synthesize             │  V(N+1) element set with citations → synthesized_variant.{json,md}
│  adversary              │  falsifiable challenges → adversary_review.json
│  estimate-conversion    │  Wilson intervals + coupling → conversion_estimates.json
│  generate-spec          │  buildable spec with components + preconditions → v5-spec.md
│  visual-design          │  HTML mockup + PNG render → design/v5a-green.png
│  render-report          │  customer-facing HTML → report/index.html
└────────────┬────────────┘
             │
             │  V(N+1) spec + mockup + report
             ▼
┌─────────────────────────┐
│  Brand engineering team │  ships the variant subject to operational
│                         │  preconditions in §4 of the spec
└────────────┬────────────┘
             │
             │  post-ship analytics
             ▼
┌─────────────────────────┐
│  sim-flow record-actuals│  freezes predictions immutably; computes
│                         │  predicted-vs-actual delta + calibration signal
└─────────────────────────┘
```

Apriori does the **research** (find what works in the simulator). Our engine produces the **engineering-ready next variant** (with citations, kill-conditions, and operational ship gates) and the **customer-facing report**.

---

## 2. What Apriori emits vs. what our engine consumes

### Apriori's output (`ComparisonData`)

The rich data shape Apriori produces lives **inside each demo page's `page.tsx`** as a hardcoded `ComparisonData` constant — not in the documented `ProductFlowSimulationResult` API contract (which is just the summary metrics).

The full shape (as observed in [`src/app/demo/univest/page.tsx`](https://github.com/dechrone/apriori_landing/blob/main/src/app/demo/univest/page.tsx)):

```ts
interface ComparisonData {
  metadata: { simulation_id; simulation_name; persona_count; screen_count; flow_screens };
  variants: Array<{ id; label; is_control; color; description }>;        // narrative descriptions, not enums
  metrics: Record<variantId, { sus; seq; completion_rate; friction_count; avg_sentiment }>;
  verdict: { recommended_variant; recommendation_type; modifications[]; verdict_text; confidence };
  theme_movement: { persistent[]; resolved[]; introduced[] };            // friction analysis with monologues
  screen_comparison: Array<{ screen_name; divergence_score; summaries: Record<variantId, string> }>;
  persona_journeys: Array<{ persona_id; name; segment; preferred_variant; narrative }>;
  segment_verdicts: Array<{ segment_name; persona_count; winner; metrics_by_variant }>;  // per-segment conversion
  friction_provenance: Array<{ id; friction; status; presence: Record<variantId, string> }>;
  recommendations: Array<{ recommendation; type; priority; rice_score; rationale; success_metric }>;
  recommended_next_test: { name; hypothesis; predicted_conversion; predicted_lift };  // ← Apriori's V5 proposal
  variant_screenshots: Record<variantId, string | string[]>;            // PNG paths
  // ...
}
```

### What our engine consumes (`element_matrix.json`)

Taxonomy-normalized, machine-readable. The 12 dimensions defined in `.claude/rules/element-taxonomy-base.md` (+ client overlay), plus per-segment conversion, friction points, citations, confounds, clean contrasts, extraction confidence flags, and aggregate metrics.

### The mapping work

| Apriori field | Maps to our matrix |
|---|---|
| `metrics[v].completion_rate` | `aggregate_metrics.completion_rate[v]` (direct) |
| `segment_verdicts[s].metrics_by_variant[v].completion_rate` | `variants[v].conversion_by_segment[s]` (direct) |
| `metadata.persona_count`, `segment_verdicts[s].persona_count` | `n_total`, `segments[s].n` (direct) |
| `friction_provenance[]`, `theme_movement.persistent[]` | `friction_points[]` (re-shaped) |
| `screen_comparison[].summaries[v]` (natural-language) | `variants[v].elements[*]` (12 taxonomy dimensions — **needs human or LLM-driven mapping**) |
| `verdict.recommended_variant`, `recommended_next_test.*` | not directly used — our synthesis is independent |

The taxonomy mapping (the last row) is the **integration friction**. For Univest we did it manually by reading the screenshots. Phase 2 of the plug-in roadmap (§5 below) automates this.

---

## 3. The current workflow

For a new client today:

```bash
# 1. Get the Apriori ComparisonData JSON
# (Apriori dev exports the COMPARISON_DATA constant from src/app/demo/<client>/page.tsx
#  as JSON, OR provides it via a JSON endpoint — see Phase 5 for productized version.)

# 2. Ingest into the engine (Phase 2 — automatic scaffolding)
scripts/ingest-apriori.py <client> --from-comparison-json <file>
# Produces:
#   data/<client>/apriori_input.json        — audit trail
#   data/<client>/source.md                 — human-readable summary
#   data/<client>/element_matrix.json       — starter (direct fields populated; taxonomy needs review)
#   data/<client>/source-screenshots/       — variant PNGs auto-fetched

# 3. Auto-map taxonomy (Phase 3a — rule-based; ~75% match against hand-built ground truth)
scripts/automap-taxonomy.py <client>
# → updates element_matrix.json with high-confidence values where rules match,
#   sensible defaults where they don't, __needs_review__ where neither
# → writes data/<client>/automap-trace.json with per-cell confidence + matched-pattern audit

# 4. LLM fallback for cells the rules couldn't handle (Phase 3b — Sonnet 4.6)
scripts/automap-taxonomy-llm.py <client>
# → for each cell trace shows as needs_review, calls Claude Sonnet 4.6 with the variant text
#   + the dimension's allowed enum values; updates the matrix when the LLM returns high/medium confidence
# → cost: ~$0.05 per typical client (~14 cells)
# → requires ANTHROPIC_API_KEY env var + `pip install -r requirements.txt`
# → use --dry-run to preview prompts without API calls; --max-cells N to cap iterations

# 5. Human review of any cells the LLM still couldn't determine
# Most clients land at this step with only 1–3 cells left. Edit element_matrix.json
# for those, plus .claude/rules/element-taxonomy-<client>.md for client-specific
# overlay values (e.g. compound CTA-style values not in base taxonomy).

# 6. Run the pipeline cascade (each stage reads the previous)
scripts/sim-flow.py status <client>          # state probe
# Then weigh-segments → synthesize → adversary → estimate-conversion → generate-spec
# (each is currently a manual reasoning pass following the SKILL.md docstrings)

# 7. Render the customer-facing report
scripts/render-report.py <client>            # validates inputs + renders preview PNG
```

After Phase 3b (current state): rules fill ~75% of cells, the LLM closes most of the remaining 25%, and only 1–3 cells per client typically need human review. **Total onboarding time ≈ 15–20 minutes** for human review + downstream cascade.

---

## 4. The 4 customer-visible artifacts

After the pipeline runs, these are what the customer cares about:

| Artifact | Path | Audience |
|---|---|---|
| **Synthesis report** (HTML) | `data/<client>/report/index.html` | Brand stakeholders, PMs |
| **Visual mockup** (PNG) | `data/<client>/design/v5a-green.png` | Brand stakeholders, designers |
| **Buildable spec** (Markdown) | `data/<client>/v5-spec.md` | Brand engineering team |
| **Conversion math** (JSON) | `data/<client>/conversion_estimates.json` | Data team, sceptics |

The HTML report is the headline deliverable — it's what a brand stakeholder sees when they open the link. It links down to the spec and JSON for engineers and data teams. Sample at [`data/univest/report/index.html`](data/univest/report/index.html).

---

## 5. Plug-in roadmap

### ✅ Phase 1 (shipped 2026-04-26)
- Manual cascade through `weigh-segments → synthesize → adversary → estimate-conversion → generate-spec`.
- Hand-curated HTML report per client.
- `scripts/sim-flow.py` for state probing and immutable evaluator.
- `scripts/render-report.py` for report PNG re-rendering.
- One client end-to-end: Univest V5.

### ✅ Phase 2 (shipped 2026-04-26)
**`scripts/ingest-apriori.py <client> --from-comparison-json <file>`**
- Accepts the `ComparisonData` JSON object (Apriori dev exports it from page.tsx, or fetches from a JSON endpoint Apriori adds).
- Auto-populates `data/<client>/source.md` (10 sections: variants, segments, conversion table, friction points, theme movement, screen comparison, persona journeys, recommendations, recommended next test, risks).
- Auto-fetches variant screenshots to `data/<client>/source-screenshots/` (single-PNG and multi-PNG variants both supported).
- Emits a starter `element_matrix.json` with:
  - **Auto-populated:** segments (with weights from persona_count), variants[].conversion_by_segment, variants[].id (Apriori `a/b/c` → our `V1/V2/V3`), friction_points (re-shaped from friction_provenance + theme_movement persona_counts), citations (extracted from theme_movement.monologue_evidence), aggregate_metrics (sus/seq/completion_rate/sentiment/friction_count remapped), apriori_recommended_next_test surfaced as metadata.
  - **Flagged `__needs_review__`:** all 12 taxonomy element values per variant (layout, branding, cta_*, etc.) — these require either a human pass or the Phase 3 LLM auto-mapper.
- Saves canonical input at `data/<client>/apriori_input.json` for audit trail.
- Modes: `--dry-run`, `--no-fetch-screenshots`, `-o <output-dir>`.
- Test fixture at `scripts/test-fixtures/apriori-comparison-example.json` (synthetic 'fixturo' client).

After ingest, the human taxonomy pass + downstream pipeline cascade is unchanged from Phase 1. Onboarding time drops from ~4–6 hours to ~1.5–2 hours (the matrix scaffolding is no longer hand-typed; the taxonomy review remains the bottleneck).

### ✅ Phase 3a (shipped 2026-04-26) — rule-based auto-mapper
**`scripts/automap-taxonomy.py <client>`**
- Reads the starter matrix (with `__needs_review__` taxonomy fields) + `apriori_input.json`.
- Applies pattern rules per dimension across the variant's text corpus (description + screen_comparison.summaries[this_variant] + present-friction + persistent/introduced themes).
- Adds derived INFER_* signals from friction antitheses (e.g., modal-friction RESOLVED → INFER_NO_MODAL → maps to `modal_interrupt=no` and `layout=full_screen`) and combined trust signals (regulator + aggregate/named/third-party → `regulatory_plus_evidence`).
- Negation-aware: stocks like TMPV/ZOMATO matched only outside negation context ("stripped", "no concrete", "absent of"...).
- Three-tier confidence: `high` (explicit pattern match), `low_default` (sensible default like `none`/`single`/`absent`/`implicit`), `needs_review` (no signal).
- Audit trail: `data/<client>/automap-trace.json` with per-cell value + confidence + matched_pattern.

**Validated coverage on real Univest data** (5 variants × 11 dims = 55 cells):
- 95% cells auto-filled (high or low_default)
- ~75% match against hand-built v2 univest matrix (overall)
- ~84% match on high-confidence cells

**Tested by 18-test suite** (`scripts/test-automap-taxonomy.py`): unit tests on helpers (extract_cta_label, _derive_inferences, map_cell), integration tests on synthetic + real-univest fixtures, regression thresholds (≥70% overall match, ≥80% high-confidence, ≥95% auto-fill coverage).

**Limitations (known, by design):**
- Cannot recover facts that aren't in the text (V4 dark theme, V2-V4 countdown timer where Apriori's friction model was incomplete) — needs Phase 3b LLM or screenshot OCR.
- Cannot generate Univest-overlay-specific compound values (e.g. `cta_style=outline_on_dark_plus_sticky_green`) — only base-taxonomy enums.
- Cross-variant inheritance ("Same as V2") is not tracked across variants.

### ✅ Phase 3b (shipped 2026-04-27) — LLM fallback for the ~25% gap
**`scripts/automap-taxonomy-llm.py <client>`**
- For cells flagged `needs_review` (or `low_default` with `--include-low-default`) after Phase 3a, calls Claude Sonnet 4.6 (default; configurable via `--model`) with the variant's text corpus + the dimension's allowed enum values + the Phase 3a verdict.
- High/medium-confidence LLM picks update the matrix and get tagged `auto_mapped_llm` in the trace; low-confidence picks (or null) are left for the human pass.
- Prompt caching on the system message (full taxonomy enum, ~2KB) — first call writes cache (1.25× cost), subsequent calls read at 0.1×.
- Cost: ~$0.05 per typical client (~14 cells × ~$0.003 each on Sonnet 4.6).
- Cost guards: `--max-cells N` caps iterations; `--dry-run` builds prompts without API calls (no auth required).
- Error handling: typed exceptions for auth + rate-limit; SDK auto-retries 5xx; markdown-fence stripping; JSON parse failures surfaced.
- Requires `anthropic` Python SDK (`pip install -r requirements.txt`) + `ANTHROPIC_API_KEY` env var.
- Tested by 15-test suite (`scripts/test-automap-taxonomy-llm.py`) using mocked API client (no key required to run tests).

**Onboarding time after Phase 3b: ~15–20 minutes** per client — only the human pipeline cascade remains.

### ⏭ Phase 4 (after Phase 3b proves on 2-3 clients)
**Webhook / GitHub Action**
- When a new `/src/app/demo/<client>/` lands in apriori_landing → trigger our engine.
- Engine runs full pipeline + report render.
- Publishes `report/index.html` back as a comment on the apriori_landing PR (or a separate hosted URL).

After this lands: real plug-and-play. Brand finishes simulation → 5-10 minutes later, V(N+1) spec + report URL available.

### ⏭ Phase 5 (real product UX)
**Synthesis-as-a-tab in apriori_landing**
- Add a "Synthesis" tab to each `/demo/<client>` page.
- Embeds our `report/index.html` (or fetches synthesis JSON and renders inline using their design system).
- Single URL for the brand: see Apriori's research + our V(N+1) prescription side by side.
- Post-ship actuals collection via the same UX.

This requires coordination with the apriori_landing team to add a route and a small data fetch. Out of our repo's scope until it's a joint project.

---

## 6. Where to write actuals (post-ship)

When Univest (or any client) ships V5 and real conversion data comes back:

```bash
# Save actuals as JSON (schema documented in scripts/sim-flow.py docstring for record-actuals)
# Then:
scripts/sim-flow.py record-actuals univest path/to/actuals.json
```

This freezes the V5 prediction immutably (`evaluator/predicted.json`), records the actual (`evaluator/actual.json`), and computes the delta + calibration signal (`evaluator/comparison.json`). Subsequent `sim-flow status` runs surface the predicted-vs-actual comparison.

The calibration signal feeds back into our `non_linearity_discount` improvement (currently the 0.7 constant in `synthesize` is uncalibrated; once we have 2-3 clients' actuals, we fit it against data).

---

## 7. Repo conventions (for new clients)

- **All client data lives in `data/<client>/`.** Never hardcode client names in skills, base rules, or scripts. The skill `.claude/skills/parse-simulation/SKILL.md` is client-agnostic; the overlay `.claude/rules/element-taxonomy-<client>.md` is the only place client-specific dimension values go.
- **Source files are immutable.** `data/<client>/source.md` is never edited after extraction. Re-extractions create `source-v2.md`, `source-v3.md`, etc. (use `scripts/refetch-source.sh`).
- **Screenshots are immutable.** `data/<client>/source-screenshots/` is the ground-truth visual reference. Always pull screenshots; the source page's prose is prescriptive (highlights variant differences) and omits shared elements.
- **Predictions, once frozen, are never edited.** `data/<client>/evaluator/predicted.json` is overwrite-protected by `record-actuals`. The synthesis system cannot edit what counts as success.

---

## 8. Quick reference

| Action | Command |
|---|---|
| **Ingest Apriori ComparisonData** | `scripts/ingest-apriori.py <client> --from-comparison-json <file>` |
| **Auto-map taxonomy** (rule-based, Phase 3a) | `scripts/automap-taxonomy.py <client>` |
| Test the auto-mapper (18 tests) | `scripts/test-automap-taxonomy.py` |
| **LLM fallback for taxonomy** (Phase 3b, Sonnet 4.6) | `scripts/automap-taxonomy-llm.py <client>` |
| Test the LLM mapper (15 tests, mocked API) | `scripts/test-automap-taxonomy-llm.py` |
| See pipeline state for a client | `scripts/sim-flow.py status <client>` |
| List all clients | `scripts/sim-flow.py list` |
| Render the HTML report → PNG | `scripts/render-report.py <client>` |
| Record post-ship actuals | `scripts/sim-flow.py record-actuals <client> <file>` |
| Re-fetch source (auto-versioned) | `scripts/refetch-source.sh <url> <client>` |
| Wilson interval on (p, n) | `scripts/wilson-intervals.py <p> <n>` |
| Auto-detect element confounds | `scripts/detect-confounds.py <client>` |

For the synthesis reasoning steps (`weigh-segments`, `synthesize`, `adversary`, `estimate-conversion`, `generate-spec`), see the corresponding `.claude/skills/<name>/SKILL.md` files.

---

## 10. LangGraph integration (`simul2design` package)

The repo ships as an installable Python package — `simul2design` — that exposes the engine as a class + a pre-built LangGraph node. This is the recommended integration shape: **the synthesis engine becomes a node in Apriori's graph**, not a separate system with hand-off.

### Install

From PyPI (when published):

```bash
pip install simul2design
```

Or directly from the repo:

```bash
pip install git+https://github.com/abhishek5878/simul2design.git
```

For LangGraph users, install the optional extra:

```bash
pip install "simul2design[langgraph]"
```

`simul2design` declares `anthropic>=0.85.0` and `pydantic>=2.0.0` as runtime dependencies. `langgraph` itself is **not** required — the node is a plain async function that any orchestrator can call.

### Library API

```python
import os, asyncio, json
from simul2design import SynthesisPipeline, ComparisonData

# Apriori produced this from one of their simulations
comparison_data = json.load(open("apriori_output.json"))

pipeline = SynthesisPipeline(
    automap_model="claude-sonnet-4-6",          # default — taxonomy mapping
    skip_llm_fallback=False,                    # set True for rules-only runs
    include_low_default_in_llm_pass=False,      # set True for tighter coverage
    max_llm_cells=None,                         # cap on LLM API calls
)

result = asyncio.run(pipeline.run(
    comparison_data,                             # ComparisonData OR raw dict
    client_slug="univest",
))

# Always populated (Sprint A — automated portion)
print(result.element_matrix)                     # taxonomy-normalized matrix
print(result.automap_trace)                      # per-cell confidence + matched-pattern audit
print(result.source_markdown)                    # human-readable summary of Apriori's output
print(result.cells_needing_review)               # list[CellRef] — cells the auto-mapper couldn't resolve
print(result.ready_for_synthesis)                # True if no cells need human review
print(result.estimated_cost_usd)                 # LLM cost for this run (~$0.05 typical)
print(result.token_usage)                        # input/output/cache token counts

# Phase 3c (cascade automation — not yet shipped)
print(result.synthesized_variant)                # None today; populated once .claude/skills/synthesize is ported
print(result.spec_markdown)                      # None today
print(result.report_html)                        # None today
```

### LangGraph node — drop-in usage

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from simul2design.langgraph_node import synthesis_node


# Apriori's existing state — only the two fields the node reads need to be defined
class AprioriState(TypedDict, total=False):
    # ... Apriori's existing state fields ...
    simulation_id: str
    comparison_data: dict[str, Any]                  # input to our node
    # output of our node:
    synthesis_result: Optional[dict[str, Any]]
    synthesis_ready_for_human: Optional[bool]


graph = StateGraph(AprioriState)
graph.add_node("simulation", run_apriori_simulation)
graph.add_node("synthesis", synthesis_node)          # ← OUR NODE
graph.add_node("dashboard", render_apriori_dashboard)

graph.add_edge("simulation", "synthesis")
graph.add_edge("synthesis", "dashboard")
graph.set_entry_point("simulation")
graph.set_finish_point("dashboard")

app = graph.compile()
final_state = await app.ainvoke({"simulation_id": "sim_abc123", ...})

# Apriori's UI now has access to:
final_state["synthesis_result"]["element_matrix"]       # the taxonomy-normalized matrix
final_state["synthesis_result"]["cells_needing_review"] # cells flagged for human review
final_state["synthesis_result"]["estimated_cost_usd"]   # cost telemetry
final_state["synthesis_ready_for_human"]                # True if nothing to review
```

The node:
1. Reads either `state["ab_report"]` (apriori_simulation_engine canonical output, preferred) OR `state["comparison_data"]` (legacy). If both are present, `ab_report` wins.
2. Resolves `state["client_slug"]` (or derives from `simulation_id` / `ab_report.meta.client` / `comparison_data.metadata.simulation_id`).
3. Runs the SynthesisPipeline (ingest → automap-rules → automap-llm → optional cascade).
4. Writes `state["synthesis_result"]` (a `SynthesisResult` dict), `state["synthesis_ready_for_human"]` (bool), and `state["synthesis_input_source"]` (`"ab_report"` | `"comparison_data"`).

### Wiring against `dechrone/apriori_simulation_engine`

The engine emits the canonical `AbReport` payload at `src/api/models/ab_report.py:198-208`. To wire simul2design as a synthesis node:

```python
# In src/core/multiflow_orchestrator.py, around line 273 (right before the
# `comparison_ready` event yield):

from simul2design.langgraph_node import synthesis_node
from simul2design import SynthesisPipeline

# Build the pipeline once at module import (or inject from app state):
_synth_pipeline = SynthesisPipeline(run_full_cascade=True, max_llm_cells=20)

# After the AbReport dict (`report`) is assembled and validated:
synth_state = {"ab_report": report, "client_slug": meta["client"]}
synth_out = await synthesis_node(synth_state, pipeline=_synth_pipeline)

# Yield a follow-on event with the synthesis result:
yield _ndjson({"type": "synthesis_ready", "data": synth_out["synthesis_result"]})
```

Or as a `StateGraph` node in `src/core/langgraph_orchestrator.py`'s `build_simulation_graph()` at line ~1684:

```python
graph.add_node("synthesize_design", synthesis_node)
graph.add_edge("generate_insights", "synthesize_design")
```

**Latency caveat:** A full cascade run is ~4 minutes synchronous and ~$0.44. The engine's `stream_events()` SSE pattern at `multiflow_orchestrator.py:97` will block for that duration. For production UX, run the cascade in a background task and yield `synthesis_running` heartbeats every 10s, then a final `synthesis_ready` event when it completes. Disable the cascade by leaving `run_full_cascade=False` (default) — the node still returns the auto-mapped matrix in <5 seconds.

### AbReport → ComparisonData adapter (three-tier metric resolution)

The adapter at `simul2design/adapters/ab_report.py` performs a structural conversion between the two schemas. Per-segment per-variant completion rates resolve through three tiers, per cell, in priority order:

1. **`measured_subsample`** — real conversion rate computed from per-persona outcomes mined from `AbReport.deep_dive.personas[].variant_{a,b}.outcome` and `AbReport.monologue_diff[].decision_{a,b}` (de-duped by `persona_id`). Each cell carries `observed_n` so downstream Wilson 95% intervals widen appropriately on small samples.
2. **`preference_proxy`** — binary 100/0 derived from `AbReport.persona_split[].preferred_variant`, used when no per-persona outcomes exist for that segment. `observed_n = 0`. Direction-only signal.
3. **`absent`** — both null when `preferred_variant == "neither"` AND `observed_n == 0`.

The per-cell source is recorded in `_extraction_confidence.segment_verdicts.metrics_by_variant.completion_rate.cells = {<segment>: {a: <source>, b: <source>}}`. Aggregate `metrics.completion_rate` uses pooled measured outcomes when any are observed, falling back to preference-share otherwise.

**When measured and preference disagree, measured wins.** If `persona_split` says urban-tech-workers prefers A but the deep-dive persona for that segment converted on B and abandoned A, `metrics_by_variant.a.completion_rate=0` and `b=100` — driven by the actual outcome, not the segment-level tag. (The `winner` field still mirrors `preferred_variant` because that's AbReport's own analysis layer; lift math runs off the measured cells.)

The adapter reads outcomes that already exist in AbReport — no engine-side change is required to get measured rates. To raise the observed_n per segment, the engine team would need to populate more `deep_dive.personas` or `monologue_diff` entries; the adapter automatically picks them up.

```python
# Direct usage of the adapter, outside the LangGraph node:
from simul2design import from_ab_report, ComparisonData, SynthesisPipeline

adapted_dict = from_ab_report(ab_report_dump, client_slug="loop_health")
cd = ComparisonData(**adapted_dict)
result = await SynthesisPipeline().run(cd, client_slug="loop_health")

# Inspect per-cell sources to see which segments are measured vs proxy:
print(adapted_dict["_extraction_confidence"]
      ["segment_verdicts.metrics_by_variant.completion_rate.cells"])
```

### Pre-configured pipeline injection

For tests, cost caps, or model overrides, construct the pipeline once and pass it to the node:

```python
from simul2design import SynthesisPipeline
from simul2design.langgraph_node import synthesis_node
from functools import partial

pipeline = SynthesisPipeline(
    anthropic_client=my_anthropic_client,    # for tests / shared client / Bedrock
    automap_model="claude-haiku-4-5",        # cheaper for high-volume orgs
    max_llm_cells=10,                        # cost cap per run
)

# Bind the pipeline to the node
graph.add_node("synthesis", partial(synthesis_node, pipeline=pipeline))
```

### Auth + dependencies

- The LLM fallback step requires `ANTHROPIC_API_KEY` in the environment (or a pre-configured `anthropic_client` passed to the pipeline).
- The pipeline is otherwise self-contained — no external storage, no hosted services, no auth on Apriori's side beyond the `ANTHROPIC_API_KEY` they're already using.
- For runs without an API key (CI smoke tests, free-tier previews), set `skip_llm_fallback=True` — the pipeline returns a rules-only matrix and zero cost.

### What the node delivers today (full cascade)

**As of Sprint B Phase 2, the LangGraph node delivers a complete spec end-to-end.** Set `run_full_cascade=True` on `SynthesisPipeline` and the node returns synthesized_variant + adversary_review + spec_markdown alongside the auto-mapped matrix + weighted scores + Wilson baselines.

| Field on `SynthesisResult` | Status | Source |
|---|---|---|
| `element_matrix` | ✅ taxonomy-normalized | ingest + automap (rules + LLM) |
| `automap_trace` | ✅ per-cell audit | automap |
| `source_markdown` | ✅ from Apriori narrative | ingest |
| `cells_needing_review` | ✅ list[CellRef] | automap |
| `weighted_scores` | ✅ per-(dim, value) deterministic score | weigh-segments (pure Python) |
| `conversion_estimates` | ✅ Wilson 95% CI per segment | estimate-conversion (pure Python) |
| `synthesized_variant` | ✅ V(N+1) element set + per-segment predictions | synthesize (Opus 4.7, requires `run_full_cascade=True`) |
| `adversary_review` | ✅ falsifiable objections + op preconditions | adversary (Opus 4.7) |
| `spec_markdown` | ✅ engineer-ready buildable spec | generate-spec (Sonnet 4.6) |
| `estimated_cost_usd` | ✅ all LLM calls totalled | tracked across cascade |
| `token_usage` | ✅ input/output/cache breakdown | tracked across cascade |
| `report_html` | ❌ None (deferred — separate render step) | manual `scripts/render-report.py` |

**Cost per full-cascade run (~$0.15-0.30 typical):**
- automap-llm: ~$0.05 (Sonnet 4.6, ~14 cells)
- synthesize: ~$0.05-0.10 (Opus 4.7 with adaptive thinking)
- adversary: ~$0.05-0.10 (Opus 4.7 with adaptive thinking)
- generate-spec: ~$0.02-0.05 (Sonnet 4.6, mostly templating)

**Anti-bias enforcement (per .claude/agents/adversary/AGENT.md):**
The adversary's prompt context contains ONLY the matrix + weighted_scores + synthesized_variant. NO IDEA.md, NO client narrative. The function signature enforces this — `run_adversary` and `build_user_prompt` have no `narrative` or `idea` parameter, so client preference can't accidentally leak into the adversarial reasoning.

**SynthesisPipeline toggles:**
```python
SynthesisPipeline(
    run_weigh_segments=True,         # deterministic, $0
    run_wilson_baseline=True,        # deterministic, $0
    wilson_baseline_variant="V4",
    run_full_cascade=False,          # default — pipeline exits after auto-mapper
    synthesize_model="claude-opus-4-7",   # configurable
    adversary_model="claude-opus-4-7",
    spec_model="claude-sonnet-4-6",
    conservatism_mode="balanced",         # | "conservative" | "exploratory"
)
```

`run_full_cascade=True` runs all three LLM cascade steps in order: synthesize → adversary → generate-spec, each consuming the prior step's output. If synthesize fails, adversary + generate-spec are skipped (with `_skipped` annotations in the result). Cost is rolled into `result.estimated_cost_usd`.

### Tests

```bash
scripts/test-package.py             # 12 tests: schemas, pipeline, LangGraph node, taxonomy sync
scripts/test-cascade.py             # 12 tests: weigh_segments + Wilson math + pipeline integration
scripts/test-cascade-llm.py         # 10 tests: synthesize + adversary + generate-spec (mocked)
scripts/test-ab-report-adapter.py   # 16 tests: AbReport → ComparisonData adapter + LangGraph wiring
scripts/test-render-visual.py       # 22 tests: HTML template + Playwright PNG (browser tests gated on RUN_BROWSER_TESTS=1)
```

Tests use mocked Anthropic client — no API key required. Two critical
regression checks:
- `test-cascade.py` — `simul2design/synthesize/weigh_segments.py` must reproduce
  the hand-calculated 6.42pt weighted score for the univest V2→V3 cta_style
  clean contrast. If that breaks, the deterministic arithmetic that the SKILL.md
  spec mandates as a spot-check is broken.
- `test-cascade-llm.py` — verifies the function signatures of `run_synthesize`
  and `run_adversary` have NO `narrative` / `idea` parameter — protects the
  anti-bias rule that adversary must not see client preference.

### Variant image render (v0.2.0+)

Engineers asked: "you give me a markdown spec — where's the picture?" The render module produces a PNG mockup of the V(N+1) screen by mapping `synthesized_variant.elements` (taxonomy values) to an HTML/CSS layout, then screenshotting via headless Chromium.

**Install the render extra:**

```bash
pip install 'simul2design[render]'
playwright install chromium     # one-time, ~150MB
```

The render extra is OPTIONAL. The core package + cascade work without it; only the render step needs Playwright. Importing `simul2design` without the extra is safe — `render_variant_png` raises `RenderUnavailableError` with the install hint only when called.

**Pipeline toggle:**

```python
from simul2design import SynthesisPipeline

pipeline = SynthesisPipeline(
    run_full_cascade=True,
    run_render_visual=True,                  # NEW — opt-in
    render_viewport=(375, 812),               # mobile default; pass (1440, 900) for desktop
    render_output_dir="/srv/simul2design/renders",  # PNG goes here; None → tmpdir
)

result = await pipeline.run(comp, client_slug="loop_health")
print(result.variant_image_path)           # "/srv/simul2design/renders/loop_health-v_next.png"
print(result.variant_image_size_bytes)     # ~110_000 bytes typical
```

**Programmatic API (without the pipeline):**

```python
from simul2design.render import render_variant_html, render_variant_png

# HTML-only — no browser dependency. Always available.
html = render_variant_html(synthesized_variant, variant_name="V_next", footer=False)

# PNG via Playwright. Requires the render extra.
png_bytes = render_variant_png(
    synthesized_variant,
    variant_name="V_next",
    viewport=(375, 812),
    footer=False,                  # set True to overlay the dim→value debug grid
    output_path="variant.png",     # also returns bytes
    device_scale_factor=2.0,        # retina by default
)
```

**CLI:**

```bash
# Render from a SynthesisResult JSON (cascade output)
simul2design-render result.json -o variant.png

# Or from a bare synthesized_variant.json (e.g. extracted manually)
simul2design-render synthesized_variant.json -o variant.png \
    --viewport 375x812 \
    --variant-name "V_next" \
    --footer                       # debug overlay
    --device-scale 2.0

# HTML-only mode — useful when Playwright isn't installed
simul2design-render result.json --html-only > preview.html
```

**Engine integration (`apriori_simulation_engine`):**

The `synthesis_ready` SSE event already carries the full `SynthesisResult` dict. With `run_render_visual=True` set on the cached `_synth_pipeline` in `multiflow_orchestrator.py`, the engine can:

```python
# After synthesis_node returns, the path is in the result dict.
result_dict = synth_out["synthesis_result"]
png_path = result_dict.get("variant_image_path")  # str | None

if png_path:
    # Upload to Cloudinary (engine already has cloudinary>=1.36.0)
    from cloudinary import uploader
    cdn_url = uploader.upload(png_path, folder=f"variants/{client_slug}")["secure_url"]
    result_dict["variant_image_url"] = cdn_url

yield _ndjson({"type": "synthesis_ready", "data": result_dict})
```

The frontend reads `data.result.variant_image_url` and renders the picture next to the spec markdown — exactly the "engineer-ready picture + buildable spec" deliverable.

**Cost & latency:** Zero LLM cost for the render. Adds ~2 seconds to a cascade run (Playwright cold-start dominates). Cached browser instance is feasible if needed but not currently implemented.

**Taxonomy → HTML coverage:** Every base-taxonomy dimension has a render branch. Unknown enum values render as a visible labeled placeholder (never silently dropped) so the engineer immediately sees what was intended but not yet templated.

### Versioning

The package follows semver.

| Version | Scope |
|---|---|
| `0.1.0` | Sprint A — ingest + automap (rules + LLM) + Wilson + weigh-segments + full LLM cascade (synthesize/adversary/spec) + AbReport adapter v1.1.0 |
| `0.2.0` | Adds `simul2design.render` — HTML/PNG visual artifact for the V(N+1) variant. Optional `[render]` extra; existing flows unchanged when toggle is off. |

Breaking changes to the public API bump the major version; the `SynthesisResult` schema is stable across minor versions (new fields are added with `Optional` defaults).
