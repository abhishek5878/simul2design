# Active tasks (index)

This file is the pointer to the currently active plan.

**Active plan:** _None — Univest V5 v2 deliverable complete, ship-blocked on 2 Univest-side operational preconditions._

**Latest handoff:** [`tasks/handoff-2026-04-26.md`](handoff-2026-04-26.md) — read first if you're picking this up. Supersedes `handoff-2026-04-23-late.md` (which was pre-V2-cascade).

**The V5 buildable design is in [`data/univest/v5-spec.md`](../data/univest/v5-spec.md) (v2).** Engineer-ready. Subject to 2 Operational Preconditions (refund SLA per payment method; "free" outline-CTA flow delivers 3 trades pre-payment).

**Status:** Univest proof-of-concept complete end-to-end. The matrix v2 cascade (2026-04-24) corrected 11 extraction errors and reduced the untested-stack count from 3 to 1. Pipeline observability + sim-flow are now v2-aware. Next work is either (a) post-ship Univest actuals feed-back when they arrive, or (b) a second client engagement to validate genericity.

## Parked / upcoming

- **Post-ship evaluation loop** — when Univest V5 ships and actuals return, record predicted-vs-actual delta via `scripts/sim-flow.py record-actuals univest <file>`; calibrate non-linearity discount; update lessons. Immutable evaluator scaffolded.
- **Second client** — the test of genericity. Run the full pipeline against a non-Univest client without any Univest-specific code edits. Expected pain points: new taxonomy overlay, possibly new dimensions to lift into base. Three Open improvements gated on this trigger (VoC grounding audit, persona diversity audit skill, parse-simulation voc_evidence schema).
- **Research layer activation** — autoresearch script exists in `.claude/research/run-autoresearch.sh`; needs user to install crontab.
- **First weekly self-edit ritual** — 2026-04-30 per `.claude/self-edit/weekly-ritual.md` (4 days away).

## Archived

- `tasks/parse-simulation-plan.md` — **complete 2026-04-23**.
- `tasks/weigh-segments-plan.md` — **complete 2026-04-23**.
- `tasks/synthesize-plan.md` — **complete 2026-04-23**.
- **Univest V5 end-to-end pipeline** — **complete 2026-04-23**, **re-cascaded with corrections 2026-04-24** (matrix v2). See `tasks/progress.md` for full breakdown including the v2 cascade and the 2026-04-26 catch-up session.
