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
