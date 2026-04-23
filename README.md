# Multiverse Synthesis Engine

A Claude Code agent system that ingests simulation output and emits a **prescriptive variant specification** — the optimal untested design derived from per-element, per-segment performance data, weighted by audience composition. The deliverable is a buildable spec, not a research report.

**Proof-of-concept:** Univest ₹1 trial activation screen. 50 synthetic personas, 5 tested variants, synthesized V5 predicted at 52-55% overall vs. V4's 44%.

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
| [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | Project rules loaded automatically. Under 1000 tokens. |
| [`tasks/todo.md`](tasks/todo.md) | Pointer to the active plan. |
| [`tasks/lessons.md`](tasks/lessons.md) | The self-improvement ledger. Every correction lands here. |

## Starting a session

1. `cat tasks/lessons.md` — skim accumulated rules.
2. `cat tasks/todo.md` → follow to the active plan. Find the `in_progress` phase.
3. `tail -50 tasks/progress.md` — what happened last session.
4. Pick one phase. Write it down. Enter plan mode. Execute.

(Full session-start and session-end rituals in `.claude/rules/session-persistence.md`.)

## Current state

- **Univest proof-of-concept: design-complete.** End-to-end pipeline executed: `data/univest/` contains the source, element matrix, weighted scores, synthesized V5 variant, adversary review, Wilson conversion estimates, buildable spec, and visual design mockups (V4 before, V5a green, V5b muted_premium).
- **Deliverable:** [`data/univest/v5-spec.md`](data/univest/v5-spec.md) (buildable) + [`data/univest/design/`](data/univest/design/) (PNG mockups).
- **V5 prediction:** 48.6% weighted overall (Wilson 95% band 22.3%–52.0%) vs V4 actual 44%. Medium confidence. Ship blocked on 3 Operational Preconditions (legal / ops / product sign-off per adversary blockers 1-3).
- **Next work:** post-ship Univest actuals (feeds calibration) OR second-client engagement (genericity test).

## Structure

```
.
├── IDEA.md                     # Why
├── SETUP.md                    # How
├── README.md                   # This file
├── .claude/
│   ├── CLAUDE.md               # Project rules (auto-loaded)
│   ├── settings.json           # Permissions + hooks
│   ├── rules/                  # @imported rule files incl. element-taxonomy-{base,<client>}.md
│   ├── skills/                 # plan, commit, verify + parse-simulation, weigh-segments, synthesize, estimate-conversion, generate-spec
│   ├── agents/                 # planner, code-reviewer, adversary (folder + AGENT.md + symlink)
│   ├── hooks/                  # 8 hooks (format, typecheck, plan-anchor, progress-nudge, stop-verify, compact-suggest, log-tool-call, log-user-correction)
│   ├── research/               # Daily autoresearch prompt + cron runner
│   ├── observability/          # Tool-call + correction JSONL logs (gitignored)
│   └── self-edit/              # Weekly ritual
├── data/
│   └── univest/                # First client's artifacts
│       ├── source.md                  # Immutable raw simulation source
│       ├── element_matrix.json        # parse-simulation output
│       ├── weighted_scores.json       # weigh-segments output
│       ├── synthesized_variant.json + .md   # V5 element set + citations
│       ├── adversary_review.json      # 3 blockers, 5 should-fixes
│       ├── conversion_estimates.json  # Wilson intervals + kill-conditions
│       ├── v5-spec.md                 # The buildable deliverable
│       └── design/                    # V4 before + V5a/V5b mockup PNGs
├── scripts/
│   ├── refetch-source.sh       # Versioned source re-fetch (no overwrite)
│   ├── detect-confounds.py     # Auto-detect element confounds
│   └── wilson-intervals.py     # Wilson 95% binomial CI helper
└── tasks/
    ├── todo.md                 # Active plan pointer
    ├── lessons.md              # Reactive: corrections the user has given
    ├── improvements.md         # Proactive: weaknesses seen, deferred
    ├── findings.md             # Research log
    ├── progress.md             # Backward-looking session log
    └── *-plan.md               # Feature plans (parse-simulation, weigh-segments, synthesize)
```

## Conventions

- **One commit, one concern.** Never bundle a bug fix with a refactor.
- **Verify before commit.** `verify` skill runs tests, types, lint. No `--no-verify` without explicit approval.
- **Never fabricate validation.** If a step didn't run, say so.
- **Every synthesis output cites its simulation data point.** No unsupported claims in a deliverable.
- **Every conversion prediction names its failure condition.** No confidence number without a kill condition.
