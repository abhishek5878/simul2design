# Plan — `AbReport → ComparisonData` adapter

## Goal

Apriori's engine (`dechrone/apriori_simulation_engine`) emits its comparison
output as `AbReport` (defined at `src/api/models/ab_report.py:198-208`), but
`simul2design.ComparisonData` was designed against an older legacy-comparator
shape with completely different field names. Direct ingestion fails Pydantic
validation on the first call. This adapter unblocks the merge into their main
repo by converting `AbReport → ComparisonData` losslessly where the data exists,
and explicitly flagging the one place where AbReport carries weaker signal
(per-segment per-variant completion rates) than `ComparisonData` was designed
for.

## Phases

### Phase 1 — adapter module (status: complete)

- [x] Create `simul2design/adapters/__init__.py` (re-exports)
- [x] Create `simul2design/adapters/ab_report.py`:
  - `from_ab_report(report: dict, *, client_slug: str | None = None) -> dict`
  - Returns a dict that `ComparisonData.model_validate(dict)` accepts
  - Sets `_extraction_confidence._adapter_note` flagging the preference-proxy
    completion rates
- [x] Export `from_ab_report` from `simul2design.adapters` and `simul2design`
  top-level

### Phase 2 — LangGraph node auto-detection (status: complete)

- [x] Update `simul2design/langgraph_node.py`:
  - If `state["ab_report"]` present → run adapter → continue with adapted
    `ComparisonData`
  - Else fall back to `state["comparison_data"]` (back-compat)
  - Surface the source path (`synthesis_input_source: "ab_report" | "comparison_data"`)
    in the returned state update for downstream debugging
  - `_derive_client_slug` extended to read `ab_report.meta.client` /
    `ab_report.meta.simulation_id`

### Phase 3 — tests (status: complete)

- [x] `scripts/test-ab-report-adapter.py` — 12 tests, all passing:
  - minimal AbReport (mirrored from engine's `tests/unit/test_multiflow_orchestrator.py:105`)
  - rich AbReport exercising every field
  - `ComparisonData(**adapted)` validates
  - `ingest.build_matrix(adapted, "test_client")` runs end-to-end and produces
    expected segments / variants / friction structure
  - preference-proxy completion-rate encoding is correct (100/0/null)
  - extraction_confidence note contains "PREFERENCE PROXY"
  - `synthesis_node(state={"ab_report": ...})` runs the adapter automatically

### Phase 4 — verification (status: complete)

- [x] All 4 test suites green in clean Python 3.11 venv with installed wheel:
  - `test-package.py`           12/12
  - `test-cascade.py`           12/12
  - `test-cascade-llm.py`       10/10
  - `test-ab-report-adapter.py` 16/16  (4 new tests added in 1.1.0 upgrade)
  - **Total: 50/50 passing**
- [ ] Optional: 1 real-API cascade on adapted AbReport (~$0.45) — deferred;
  mock-cascade exercises the full path via `test_langgraph_node_consumes_ab_report_state`.

### Phase 6 — fidelity upgrade (1.1.0 — status: complete)

- [x] Added `_collect_segment_outcomes()` to mine per-persona outcomes from
  `monologue_diff` and `deep_dive` (de-duped by `persona_id`)
- [x] `_build_segment_verdicts()` now emits per-cell `completion_rate_source`
  (`measured_subsample` | `preference_proxy` | `absent`) and `observed_n`
- [x] `_build_metrics()` aggregates measured outcomes pooled across segments,
  falls back to preference-share when none observed
- [x] `_extraction_confidence` records per-cell source labels under
  `segment_verdicts.metrics_by_variant.completion_rate.cells`
- [x] 4 new adversarial tests:
  - `test_measured_subsample_for_segments_with_persona_outcomes`
  - `test_preference_proxy_fallback_when_no_outcomes`
  - `test_measured_overrides_preference_when_they_disagree` (the headline test)
  - `test_outcomes_deduped_across_deep_dive_and_monologue_diff`
  - `test_aggregate_metrics_use_measured_when_any_outcomes_present`
  - `test_aggregate_metrics_fallback_to_preference_share`
- [x] ADAPTER_VERSION bumped 1.0.0 → 1.1.0

### Phase 5 — docs (status: complete)

- [x] Updated `INTEGRATION.md` §10:
  - Documents the `state["ab_report"]` pathway
  - Documents the preference-proxy caveat
  - Shows the engine-side change at `multiflow_orchestrator.py:273` and
    the alternative `langgraph_orchestrator.py` `add_node` wiring
  - Records the 4-min latency caveat with the SSE pattern

## Design decisions

### Why a dict-in / dict-out adapter (not Pydantic-in / Pydantic-out)

`simul2design` must NOT import the engine's `AbReport` type — that would
create a circular dependency (engine depends on simul2design, simul2design
depends on engine's models). The adapter consumes a plain dict (the shape
`AbReport.model_dump()` produces) and emits a plain dict that
`ComparisonData.model_validate()` accepts.

### Variant naming convention

AbReport encodes variants as fixed `"A"` / `"B"` tags. The adapter emits
`variants[0].id = "a"`, `variants[1].id = "b"`, then `simul2design.ingest`'s
existing `DEFAULT_VARIANT_LABEL_MAP` re-labels them to `V1` / `V2`.
`is_control = True` for `"a"` (A/B convention; AbReport doesn't designate one).

### Three-tier completion-rate resolution (replaces the preference-proxy floor)

`ComparisonData.segment_verdicts[].metrics_by_variant[v_id].completion_rate`
expects per-segment per-variant numerical conversion rates (0–100).

`AbReport.persona_split[]` only carries `preferred_variant: "A"|"B"|"neither"`
and `persona_count` per segment, BUT per-persona per-variant outcomes already
exist in two other AbReport sections:

- `AbReport.deep_dive.personas[].variant_{a,b}.outcome` — `DecisionOutcome` literal per persona per variant
- `AbReport.monologue_diff[].decision_{a,b}` — same `DecisionOutcome`, possibly overlapping personas

The adapter mines both, de-duplicates by `persona_id` (deep_dive wins on
collision since it's structurally richer), and resolves each segment+variant
cell through three tiers in priority order:

1. `measured_subsample` — `(#convert / observed_n) * 100`. Cell carries
   `observed_n` so downstream Wilson 95% intervals widen on small samples.
2. `preference_proxy` — binary 100/0 from `persona_split[].preferred_variant`,
   used when the segment has zero observed outcomes for that variant.
3. `absent` — both null when neither outcomes nor preference are available.

When measured and preference disagree (e.g., persona_split says urban prefers
A but the deep_dive persona converted on B), the measured rate wins. The
`winner` field still mirrors `preferred_variant` because that's AbReport's
own analysis layer; the lift math runs off the measured cells.

Aggregate `metrics.{a,b}.completion_rate` uses pooled measured outcomes when
any are observed across the report, falling back to preference-share otherwise.
Source labels are recorded in
`_extraction_confidence.segment_verdicts.metrics_by_variant.completion_rate.cells`.

To raise observed_n per segment, the engine team would populate more
`deep_dive.personas` or `monologue_diff` entries — the adapter automatically
picks them up. No engine-side schema change is required to get measured rates
on segments where deep-dive personas already exist.

### Theme / citation extraction

`ComparisonData.theme_movement` is the citation source for `simul2design.ingest.map_citations()`.
AbReport doesn't have themes, but `monologue_diff[]` carries the same
structural information per persona. Adapter emits each `MonologueDiff` as one
`theme_movement.persistent[]` entry with `monologue_evidence.monologues =
{a: variant_a_monologue, b: variant_b_monologue}`. This preserves citations
end-to-end.

### Friction shape conversion

AbReport: `friction_provenance: {variant_a: [...], variant_b: [...]}`
ComparisonData: `friction_provenance: [{id, friction, screen, status, presence: {a, b}, ...}]`

For each item in `variant_a`: emit one ComparisonData friction entry with
`presence={a: "present", b: "absent"}`. Same for `variant_b`. Items are not
deduplicated across variants (they're typed differently per side and that's
intentional — the AbReport tagged them per side for a reason).

## Errors Encountered

| Phase | Error | Resolution |
|---|---|---|
| _(empty)_ | _(none yet)_ | _(none yet)_ |

## Out of scope

- Per-screen-pair element-by-element extraction from
  `annotated_screens.screens[].variant_a.elements[]` into the taxonomy. The
  taxonomy auto-mapper (`automap_rules` + `automap_llm`) will still need to
  run on the screenshots because AbReport's `ScreenElement.label` is
  freeform user-facing copy, not taxonomy values.
- Backwards extension of `AbReport` to carry per-segment per-variant
  completion rates. That's an engine-side change to discuss with the engine
  team after we confirm the preference-proxy floor is acceptable.
