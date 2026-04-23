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

- **Scaffold phase complete** (2026-04-23). All of SETUP.md Section 10 is done.
- **Active work:** Phase 1 of `tasks/parse-simulation-plan.md` — element taxonomy design. Load-bearing step.
- **Blocked on:** Univest Apriori output file (not yet in repo).

## Structure

```
.
├── IDEA.md                     # Why
├── SETUP.md                    # How
├── README.md                   # This file
├── .claude/
│   ├── CLAUDE.md               # Project rules (auto-loaded)
│   ├── settings.json           # Permissions + hooks
│   ├── rules/                  # @imported rule files
│   ├── skills/                 # plan, commit, verify (+ growing) — each in <skill>/SKILL.md
│   ├── agents/                 # planner, code-reviewer — <agent>/AGENT.md, plus <agent>.md symlinks for Task-tool discovery
│   ├── hooks/                  # Format, typecheck, plan-anchor, progress nudge, stop-verify, compact-suggest, log-tool-call, log-user-correction
│   ├── research/               # Daily autoresearch prompt + cron stub
│   ├── observability/          # Tool-call + correction logs (gitignored)
│   ├── self-edit/              # Weekly ritual
│   └── plans/                  # Saved plans from plan mode
└── tasks/
    ├── todo.md                 # Active plan pointer
    ├── lessons.md              # Self-improvement ledger
    ├── findings.md             # Research log
    ├── progress.md             # Backward-looking log
    └── parse-simulation-plan.md  # First feature plan
```

## Conventions

- **One commit, one concern.** Never bundle a bug fix with a refactor.
- **Verify before commit.** `verify` skill runs tests, types, lint. No `--no-verify` without explicit approval.
- **Never fabricate validation.** If a step didn't run, say so.
- **Every synthesis output cites its simulation data point.** No unsupported claims in a deliverable.
- **Every conversion prediction names its failure condition.** No confidence number without a kill condition.
