# Integration — plugging the synthesis engine into Apriori

This document covers the end-to-end product loop: Apriori simulation → our engine → buildable spec → customer-facing report → ship → post-ship calibration.

The audience is anyone integrating this engine with the [apriori_landing](https://github.com/dechrone/apriori_landing) frontend or running a new client through the pipeline.

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

## 3. The current workflow (manual ingestion)

For a new client today:

```bash
# 1. Hand-write source from Apriori's variant descriptions + screenshots
mkdir -p data/<client>/source-screenshots
# (download all variant PNGs from apriori.work/screens/<client>/*.png)
# Write data/<client>/source.md with variant descriptions, segments, conversion table, friction.

# 2. Hand-write the matrix (taxonomy-normalize variant elements)
# Edit data/<client>/element_matrix.json — see existing data/univest/element_matrix.json as template.
# Edit .claude/rules/element-taxonomy-<client>.md for the client overlay.

# 3. Run the pipeline (cascading; each stage reads the previous)
scripts/sim-flow.py status <client>          # status check; will list missing artifacts
# Run weigh-segments / synthesize / adversary / estimate-conversion / generate-spec
# (currently each is a manual reasoning pass following the SKILL.md docstrings)

# 4. Render the customer-facing report
scripts/render-report.py <client>            # validates inputs + renders preview PNG
```

This works but takes ~4-6 hours of human attention per new client. Phase 2 brings it down to ~30 minutes.

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

### ✅ Phase 1 (current state, 2026-04-26)
- Manual ingestion + manual matrix construction.
- Manual cascade through `weigh-segments → synthesize → adversary → estimate-conversion → generate-spec`.
- Hand-curated HTML report per client.
- `scripts/sim-flow.py` for state probing and immutable evaluator.
- `scripts/render-report.py` for report PNG re-rendering.
- One client end-to-end: Univest V5.

### ⏭ Phase 2 (next, ~1 day)
**`scripts/ingest-apriori.py <client> --from-comparison-json <file>`**
- Accepts the `ComparisonData` JSON object (Apriori dev exports it from page.tsx, or fetches from a JSON endpoint Apriori adds).
- Auto-populates `data/<client>/source.md` (formatted from `screen_comparison` + `theme_movement` + `persona_journeys`).
- Auto-fetches variant screenshots to `data/<client>/source-screenshots/`.
- Emits a starter `element_matrix.json` with:
  - Direct fields (`segments`, `conversion_by_segment`, `aggregate_metrics`) fully populated.
  - Taxonomy fields flagged `extraction_confidence: needs_review` for the human pass.
  - `friction_points` re-shaped from `friction_provenance`.

After ingest: human runs the pipeline manually, no different from Phase 1 except the input scaffolding is automated. Onboarding time drops from ~4 hours to ~1 hour (just the taxonomy mapping pass).

### ⏭ Phase 3 (next quarter, ~2-3 days)
**Taxonomy auto-mapper (LLM-driven, Sonnet-class)**
- Reads `screen_comparison[].summaries[v]` natural-language descriptions.
- Proposes taxonomy values for each (variant, dimension) cell.
- Marks each as `auto_mapped` (high confidence) or `needs_review` (human required).
- Eliminates ~70% of the human taxonomy-mapping work on a typical client.

After this lands, onboarding time drops to ~30 minutes for a typical client.

### ⏭ Phase 4 (after Phase 3 proves on 2-3 clients)
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
| See pipeline state for a client | `scripts/sim-flow.py status <client>` |
| List all clients | `scripts/sim-flow.py list` |
| Render the HTML report → PNG | `scripts/render-report.py <client>` |
| Record post-ship actuals | `scripts/sim-flow.py record-actuals <client> <file>` |
| Re-fetch source (auto-versioned) | `scripts/refetch-source.sh <url> <client>` |
| Wilson interval on (p, n) | `scripts/wilson-intervals.py <p> <n>` |
| Auto-detect element confounds | `scripts/detect-confounds.py <client>` |

For the synthesis reasoning steps (`weigh-segments`, `synthesize`, `adversary`, `estimate-conversion`, `generate-spec`), see the corresponding `.claude/skills/<name>/SKILL.md` files.
