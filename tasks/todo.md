# Active tasks (index)

This file is the pointer to the currently active plan.

**Active plan:** _None — V5 buildable design shipped_

**Latest handoff:** [`tasks/handoff-2026-04-23.md`](handoff-2026-04-23.md) — read first if you're picking this up.

**The V5 buildable design is in `data/univest/v5-spec.md`.** Engineer-ready. Subject to 3 Operational Preconditions (legal/ops/product sign-offs).

**Status:** Univest proof-of-concept complete end-to-end through the five-skill + three-agent pipeline. Next work is either (a) post-ship Univest actuals feed-back when they arrive, or (b) a second client engagement to validate genericity.

## Parked / upcoming

- **Post-ship evaluation loop** — when Univest V5 ships and actuals return, record predicted-vs-actual delta; calibrate non-linearity discount; update lessons. Immutable evaluator.
- **Second client** — the test of genericity. Run the full pipeline without any Univest-specific code edits. Expected pain points: new taxonomy overlay, new contradiction rules, potentially new dimensions to lift into base taxonomy.
- **Research layer activation** — cron the autoresearch runner (needs user to install crontab line per `.claude/research/run-autoresearch.sh` header).
- **First weekly self-edit ritual** — 2026-04-30 per the weekly-ritual doc.
- **Per-segment Wilson interval helper** — extract the Python in `data/univest/conversion_estimates.json` generation into `scripts/wilson-intervals.py` for reuse on second client.

## Archived

- `tasks/parse-simulation-plan.md` — **complete 2026-04-23**. Univest matrix shipped to `data/univest/element_matrix.json`. See `tasks/progress.md` for full ingest summary.
- `tasks/weigh-segments-plan.md` — **complete 2026-04-23**. `data/univest/weighted_scores.json` shipped. Evidence-tier KPI: 1/12 fully rankable (cta_style +6.42pt), 5/12 directional, 3/12 weak, 3/12 non-informative. See `tasks/progress.md` for full breakdown.
- `tasks/synthesize-plan.md` — **complete 2026-04-23**. `data/univest/synthesized_variant.{json,md}` shipped. V5 predicted at 49.3% (range 45.5%–53.0%) vs V4 actual 44%. Medium confidence. 3 untested values stacked with mechanism arguments. Inline adversarial review surfaced operational/contextual failure modes passed to next steps. See `tasks/progress.md` for full breakdown.
- **Univest V5 end-to-end pipeline** — **complete 2026-04-23**. Adversary sub-agent built + run (3 blockers, 5 should-fixes). estimate-conversion skill built + applied (Wilson intervals; point 48.6%, Wilson band 22.3%–52.0%). generate-spec skill built + produced `data/univest/v5-spec.md` (5 components, 4 operational preconditions, 10 instrumentation events). 5 improvements moved Open → Applied. See `tasks/progress.md`.
