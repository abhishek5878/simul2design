---
name: plan
description: Trigger when the user asks to plan a feature, task, refactor, or investigation. Creates persistent markdown files (tasks/<feature>-plan.md, tasks/findings.md, tasks/progress.md) that survive context resets and act as the agent's working memory.
---

# Plan skill (Manus-style persistent planning)

## When to use

- User asks to plan a feature, task, refactor, or investigation.
- Task has 3+ steps, multiple files to touch, or architectural decisions.
- A previous session ended mid-work and needs to be resumed.

## When NOT to use

- Single-file trivial edits (rename a variable, fix a typo).
- Quick exploratory questions ("how does X work in this codebase?").
- Drafting a plan would take longer than the implementation.

## Workflow

1. Read `tasks/lessons.md` for relevant accumulated rules.
2. Create or update `tasks/<feature>-plan.md` with:
   - Goal (one paragraph, user's words).
   - Phases with checkbox items.
   - Status for each phase: `pending` / `in_progress` / `complete`.
   - Errors Encountered table.
3. For research-heavy phases, update `tasks/findings.md` after every 2 view/browser/search operations. Do not batch.
4. After implementing each phase, update `tasks/progress.md`:
   - Actions taken.
   - Files created/modified.
   - Issues encountered and how resolved.
5. Update `tasks/<feature>-plan.md` phase status as work progresses. Never leave a phase in `in_progress` across sessions without a note on where it stopped.

## Decision tree

- If a `tasks/<feature>-plan.md` exists and has an `in_progress` phase, resume from there.
- If all phases in the plan are `complete`, ask whether to archive (`tasks/archive/`) and start a new plan.
- If no plan for this feature yet, create one.

## Success criteria

- Every non-trivial task has a live plan file.
- `findings.md` is updated throughout research, not dumped at the end.
- `progress.md` tells the story of what happened, readable by a new session or a new engineer.

## Common pitfalls

- Skipping `findings.md` updates during research. Fix: hard rule, update after every 2 research operations.
- Letting the plan drift from reality. Fix: update phase status in the same turn as the work.
- Conflating plan (forward-looking) and progress (backward-looking). Fix: plan says "will happen," progress says "happened."
