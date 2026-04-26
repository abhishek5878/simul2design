# Multiverse Synthesis Engine

A Claude Code agent system that ingests simulation output and emits a **prescriptive variant specification** — the optimal untested design derived from per-element, per-segment performance data, weighted by audience composition. The deliverable is a buildable spec, not a research report.

**Proof-of-concept:** Univest ₹1 trial activation screen. 50 synthetic personas, 5 tested variants, **synthesized V5 predicted at 51% (mechanism range 45–56%, Wilson envelope 22–74%) vs V4's 44% — +7pt median lift.**

---

## For new humans and new agents: read `SETUP.md` first

This project follows the disciplines in [`SETUP.md`](SETUP.md). Read it before touching anything.

The short version:

- **Context is state.** Everything we learn that isn't written back into `.claude/` is a tax paid every future session.
- **Four layers:** build (`.claude/` + skills + agents + hooks), research (`.claude/research/`), observation (`.claude/observability/`), self-edit (`.claude/self-edit/`).
- **Adversarial by default.** Models agree too readily. Every review, plan validation, and synthesis step is framed to surface the strongest counterargument first.
- **Cross-model verification at 15+ exchanges on hard decisions.** See `.claude/rules/cross-model-verification.md`.

## The source of truth

| File | What it is |
|---|---|
| [`IDEA.md`](IDEA.md) | Why this project exists. The problem, the insight, the Univest proof. |
| [`SETUP.md`](SETUP.md) | The disciplined scaffold. How to work in this repo. |
| [`INTEGRATION.md`](INTEGRATION.md) | **The end-to-end go-live workflow.** Apriori → engine → spec → report → ship → actuals. Read this if you want to plug a new client in. |
| [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | Project rules loaded automatically. Under 1000 tokens. |
| [`tasks/todo.md`](tasks/todo.md) | Pointer to the active plan. |
| [`tasks/lessons.md`](tasks/lessons.md) | The self-improvement ledger. Every correction lands here. |

---

## Plug-in workflow (for a new client)

The end-to-end flow from an Apriori simulation to a customer-ready V(N+1) spec + report:

```bash
# 1. Ingest Apriori's ComparisonData JSON into the engine
scripts/ingest-apriori.py <client> --from-comparison-json <path/to/apriori_input.json>
# → produces data/<client>/{apriori_input.json, source.md, element_matrix.json, source-screenshots/}

# 2. Auto-map taxonomy (rule-based; ~75% match against hand-built ground truth)
scripts/automap-taxonomy.py <client>
# → updates element_matrix.json with high-confidence values + sensible defaults
# → writes data/<client>/automap-trace.json (per-cell confidence audit)

# 3. Human review of remaining cells
# Open automap-trace.json — review cells flagged `low_default` (best-guesses) or
# `needs_review` (no signal). Edit element_matrix.json to fix.
# Edit .claude/rules/element-taxonomy-<client>.md for client-specific overlay.

# 4. Confirm pipeline state
scripts/sim-flow.py status <client>
# → one-screen dashboard showing all 7 pipeline stages, blockers, flags, validation, next action

# 5. Cascade through the synthesis skills
#    weigh-segments → synthesize → adversary → estimate-conversion → generate-spec
#    (each is a manual reasoning pass against the SKILL.md docstring)

# 6. Render the customer-facing HTML report
scripts/render-report.py <client>
# → validates inputs + re-renders data/<client>/report/preview.png
# → prints `open` commands for the HTML and PNG
```

After ship, close the calibration loop:

```bash
scripts/sim-flow.py record-actuals <client> path/to/actuals.json
# → freezes predictions immutably, computes predicted-vs-actual delta + calibration signal
```

**See [`INTEGRATION.md`](INTEGRATION.md) for the full plug-in roadmap (5 phases) and the data shape contract between Apriori and our engine.**

---

## Command reference

| Action | Command |
|---|---|
| **Ingest Apriori ComparisonData** | `scripts/ingest-apriori.py <client> --from-comparison-json <file>` |
| Test the ingest adapter (19 tests) | `scripts/test-ingest-apriori.py` |
| **Auto-map taxonomy** (rule-based) | `scripts/automap-taxonomy.py <client>` |
| Test the auto-mapper (18 tests) | `scripts/test-automap-taxonomy.py` |
| Pipeline state for a client | `scripts/sim-flow.py status <client>` |
| List all clients | `scripts/sim-flow.py list` |
| Render customer-facing HTML report | `scripts/render-report.py <client>` |
| Record post-ship actuals (immutable) | `scripts/sim-flow.py record-actuals <client> <file>` |
| Re-fetch source (auto-versioned) | `scripts/refetch-source.sh <url> <client>` |
| Wilson 95% interval on (p, n) | `scripts/wilson-intervals.py <p> <n>` |
| Auto-detect element confounds | `scripts/detect-confounds.py <client>` |

`sim-flow.py status` exit codes: `0` = clean / shipped, `1` = input error, `2` = ship-blocked (unresolved blockers OR operational preconditions). Useful for CI.

`ingest-apriori.py --dry-run` validates the input + previews the output paths without writing files. Use `--no-fetch-screenshots` to skip the variant PNG download.

---

## Starting a session

1. `cat tasks/lessons.md` — skim accumulated rules.
2. `cat tasks/todo.md` → follow to the active plan. Find the `in_progress` phase.
3. `tail -50 tasks/progress.md` — what happened last session.
4. `cat tasks/handoff-*.md | tail -1` — read the most recent handoff.
5. Pick one phase. Write it down. Enter plan mode. Execute.

(Full session-start and session-end rituals in `.claude/rules/session-persistence.md`.)

---

## Current state

- **Univest proof-of-concept: design-complete** (matrix v2, screenshot-validated re-extraction). End-to-end pipeline executed: `data/univest/` contains the source (+ source-v2 + source-screenshots), element matrix, weighted scores, synthesized V5 variant, adversary review, Wilson conversion estimates, buildable spec, visual mockup, and customer-facing HTML report.
- **Customer-facing deliverable:** [`data/univest/report/index.html`](data/univest/report/index.html) — single self-contained HTML with per-segment audience reasoning + V5 mockup + diff vs V4 + predictions + ship gates + kill conditions. This is what a brand stakeholder opens.
- **Engineer-facing deliverable:** [`data/univest/v5-spec.md`](data/univest/v5-spec.md) (buildable) + [`data/univest/design/v5a-green.png`](data/univest/design/v5a-green.png) (mockup).
- **V5 prediction:** **51%** weighted overall (mechanism range 45–56%, Wilson envelope 22–74%) vs V4 actual 44%. Median lift +7pt. Untested-stack count: 1. Confidence: medium. Ship blocked on **2 Operational Preconditions** ("free" outline-CTA flow delivers 3 trades pre-payment + refund SLA per payment method).
- **Plug-in roadmap:** Phase 2 (Apriori adapter) + Phase 3a (rule-based taxonomy auto-mapper, ~75% match on univest) shipped 2026-04-26. Phase 3b (LLM fallback for the ~25% gap) is next.
- **Next work:** post-ship Univest actuals (feeds calibration), second-client engagement (genericity test), or Phase 3 auto-mapper.

---

## Structure

```
.
├── IDEA.md                     # Why
├── SETUP.md                    # How
├── INTEGRATION.md              # Plug-in workflow + roadmap
├── README.md                   # This file
├── .claude/
│   ├── CLAUDE.md               # Project rules (auto-loaded)
│   ├── settings.json           # Permissions + hooks
│   ├── rules/                  # @imported rule files incl. element-taxonomy-{base,<client>}.md
│   ├── skills/                 # plan, commit, verify + parse-simulation, weigh-segments,
│   │                           # synthesize, estimate-conversion, generate-spec
│   ├── agents/                 # planner, code-reviewer, adversary
│   ├── hooks/                  # 8 hooks (format, typecheck, log-*, etc.)
│   ├── research/               # Daily autoresearch prompt + cron runner
│   ├── observability/          # Tool-call + correction JSONL logs (gitignored)
│   └── self-edit/              # Weekly ritual
├── data/
│   └── univest/
│       ├── source.md / source-v2.md     # Immutable raw + screenshot-validated v2
│       ├── source-screenshots/          # Immutable variant PNGs (ground truth)
│       ├── apriori_input.json           # Canonical Apriori ComparisonData (audit trail)
│       ├── element_matrix.json          # Taxonomy-normalized matrix
│       ├── weighted_scores.json         # Per-(dimension, value) weighted score
│       ├── synthesized_variant.{json,md}# V5 element set + citations
│       ├── adversary_review.json        # Falsifiable objections
│       ├── conversion_estimates.json    # Wilson intervals + kill-conditions
│       ├── v5-spec.md                   # Engineer-facing buildable spec
│       ├── design/                      # V4-before, V5a-green, V5b-muted-premium mockups
│       ├── report/index.html            # Customer-facing HTML report
│       └── evaluator/                   # (created on first record-actuals call)
│           ├── predicted.json           # Frozen at ship time, never overwrites
│           ├── actual.json              # Post-ship truth
│           └── comparison.json          # Derived delta + calibration signal
├── scripts/
│   ├── sim-flow.py             # Pipeline status + record-actuals (v2-schema-aware)
│   ├── ingest-apriori.py       # Apriori ComparisonData → engine input adapter
│   ├── test-ingest-apriori.py  # 19-test suite for the adapter
│   ├── automap-taxonomy.py     # Rule-based taxonomy auto-mapper (Phase 3a)
│   ├── test-automap-taxonomy.py# 18-test suite for the auto-mapper
│   ├── render-report.py        # Validate + re-render customer-facing report PNG
│   ├── refetch-source.sh       # Versioned source re-fetch (no overwrite)
│   ├── detect-confounds.py     # Auto-detect element confounds
│   ├── wilson-intervals.py     # Wilson 95% binomial CI helper
│   └── test-fixtures/          # Test inputs for ingest-apriori
│       ├── apriori-comparison-example.json     # Synthetic 3v×3s
│       └── apriori-comparison-univest.json     # Real univest 5v×4s×50p
└── tasks/
    ├── todo.md                 # Active plan pointer
    ├── lessons.md              # Reactive: corrections the user has given
    ├── improvements.md         # Proactive: weaknesses seen, deferred
    ├── findings.md             # Research log
    ├── progress.md             # Backward-looking session log
    ├── related-work.md         # Cited papers + methodology adoption notes
    ├── handoff-YYYY-MM-DD.md   # Session-end handoffs (most recent = canonical)
    └── *-plan.md               # Feature plans
```

---

## Testing

Two pieces have automated tests (the synthesis skills are reasoning-driven and tested by re-running the pipeline end-to-end):

```bash
scripts/test-ingest-apriori.py             # 19 tests: unit + integration + edge + real-data
scripts/test-automap-taxonomy.py           # 18 tests: unit + integration + coverage thresholds
```

**ingest-apriori tests** (19): helper functions (slugify, variant_label), simple-fixture integration (dry-run + real-run), segment weight computation, aggregate metrics normalization, taxonomy `__needs_review__` flagging, citation extraction from monologues, friction reshaping, edge cases (invalid JSON, missing file, missing required fields), and real-data validation against the hand-built univest v2 matrix (segments, conversions, aggregate metrics all match within tolerance).

**automap-taxonomy tests** (18): helper unit tests (`extract_cta_label` rejects brand/banner strings, prefers imperatives; `_derive_inferences` handles modal-resolved + named-with-negation + aggregate-plus-named correctly; `map_cell` returns correct confidence tier), integration tests on synthetic + real-univest fixtures, regression thresholds (≥70% overall match against hand-built v2 univest, ≥80% high-confidence match, ≥95% auto-fill coverage). Threshold failures = either regression or rules improved (in which case bump threshold).

---

## Conventions

- **One commit, one concern.** Never bundle a bug fix with a refactor.
- **Verify before commit.** `verify` skill runs tests, types, lint. No `--no-verify` without explicit approval.
- **Never fabricate validation.** If a step didn't run, say so.
- **Every synthesis output cites its simulation data point.** No unsupported claims in a deliverable.
- **Every conversion prediction names its failure condition.** No confidence number without a kill condition.
- **Source data is immutable.** `source.md` / `source-screenshots/` are never edited after extraction. Re-extractions create `source-v2.md`, `-v3`, etc.
- **Predictions, once frozen, are never edited.** `evaluator/predicted.json` is overwrite-protected by `record-actuals`. The synthesis system cannot edit what counts as success.
- **Build for the second client from the first commit.** Every skill, rule, and agent is client-agnostic unless its path makes the client scope explicit.
