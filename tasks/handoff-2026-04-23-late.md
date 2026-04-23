# Handoff — 2026-04-23 (late)

Supersedes [handoff-2026-04-23.md](handoff-2026-04-23.md). Same day; state advanced meaningfully.

## TL;DR

Pipeline now has observability (`sim-flow status <client>`) and a closed-loop evaluator (`sim-flow record-actuals <client> <file>`). Univest V5 design still complete, still ship-blocked on the 3 Operational Preconditions, but the post-ship record path is now one command. Two commits landed since the earlier handoff: `82d0d55` + `cb6d1f0`, both on `origin/main`.

## State of the tree

- Branch: `main`. Tracks `origin/main`. **Clean.**
- Last 5 commits:
  - `cb6d1f0` sim-flow: add record-actuals verb and immutable-evaluator loop
  - `82d0d55` Add sim-flow.py: session-start-style pipeline dashboard
  - `de05c22` Session-end ritual: add handoff skill + 2026-04-23 handoff note
  - `73a12e2` Update README and progress log with end-of-session state
  - `401c44a` Univest V5: end-to-end synthesis + buildable design + visual mockups
- Any synthetic test data from the evaluator smoke test has been cleaned up (verified in session-end `verify` pass).

## Active plans

**None.** `tasks/todo.md` active-plan pointer is "None." Every `tasks/*-plan.md` has all phases marked `complete`.

## The one command you should know

```bash
scripts/sim-flow.py status univest
```

Reads the whole pipeline in < 2 seconds. Output includes next-action recommendation. If you don't know where to start — start there.

## Next work (user's choice)

Unchanged from earlier handoff. Three paths possible; none active:

1. **Post-ship Univest** — when Univest ships V5 and actuals come back:
   ```bash
   scripts/sim-flow.py record-actuals univest <actuals.json>
   ```
   Actuals schema documented in the `record-actuals` docstring. This freezes predictions (immutable), records actuals, computes delta, and surfaces the calibration signal in `status`.

2. **Second client** — the genericity test. See earlier handoff's "If you're continuing for a second client" section.

3. **Research / observation layer activation** — still wired but unused.

## Deferred (improvements.md Open — top 4)

Unchanged from earlier handoff:

1. V4.refund_or_guarantee_copy source inconsistency — blocker if V5 synthesis mis-prioritizes refund copy.
2. Non-linearity discount not calibrated — **now directly consumable**: when first actuals arrive via `record-actuals`, `evaluator/comparison.json.calibration_signal` gives the first datapoint.
3. Stock-selection out-of-matrix context — needs real user analytics.
4. Research/observation hooks unused — weekly self-edit ritual scheduled for 2026-04-30.

## Known unknowns

Unchanged — see earlier handoff.

## If you're picking this up — first 30 minutes

1. `scripts/sim-flow.py list` (1 sec) → see clients.
2. `scripts/sim-flow.py status univest` (2 sec) → see state.
3. Read `tasks/progress.md` last 3 entries (5 min) — today's work.
4. Read `tasks/lessons.md` + `tasks/improvements.md` Open section (5 min).
5. Open the V5 design: `data/univest/design/v5a-green.png` side-by-side with `data/univest/v5-spec.md` (5 min).
6. Run the session-start ritual from `.claude/rules/session-persistence.md`. Pick one thing.

If Univest actuals arrived:

```bash
scripts/sim-flow.py record-actuals univest <path-to-actuals.json>
scripts/sim-flow.py status univest    # now shows Post-ship evaluator block
```

Schema for the actuals file is in the `record-actuals` docstring at `scripts/sim-flow.py` — minimal: `{variant, weighted_overall_actual, per_segment_actual: {sid: rate}, cohort_size, observed_over}`.

## Verify output (session-end)

All JSON parses. All Python compiles. sim-flow runs. Synthetic test artifacts cleaned. Univest `status` exits 2 (3 adversary blockers unresolved — intended).
