# Session persistence

## At session start

1. Read `tasks/lessons.md` — skim the accumulated rules (reactive — what corrections to follow).
2. Read `tasks/improvements.md` "Open" section — skim the forward-looking backlog (proactive — what's weak but deferred). Consider whether any should be promoted to today's plan.
3. Read `tasks/<feature>-plan.md` (or `tasks/todo.md`) — what phase are we in? What's `in_progress`?
4. Read the last ~50 lines of `tasks/progress.md` — what happened last session?
5. Pick ONE phase to work on. Write it at the top of your scratchpad.
6. Enter plan mode. Draft this session's plan. Iterate once. Execute.

## At session end

1. Update `tasks/<feature>-plan.md` phase status. Nothing stays `in_progress` without a handoff note.
2. Write the session's key actions to `tasks/progress.md` (date + actions + files modified + issues).
3. Review any user corrections from this session. Add to `tasks/lessons.md`.
4. Review any weaknesses noticed but not yet addressed. Add to `tasks/improvements.md` (Open section) with severity + trigger-to-fix.
5. If an improvement got shipped this session, move its entry from `improvements.md` Open → Applied with a one-paragraph description.
6. Run `verify` skill. Green? Commit. Red? Checkpoint and note the failure.
7. If anything non-trivial shipped, run `handoff` skill so the next session has context.

## Handoff notes

If a phase is `in_progress` at session end, write a one-paragraph note:
- Where exactly did the work stop?
- What was the next intended action?
- What is the current hypothesis / belief about how the problem is shaped?
- Any dead-ends already ruled out this session.

This is the most valuable 2 minutes you will spend in the session.

## Context rot

When a conversation has 50+ tool calls or feels foggy: reset. Paste the current state (plan, progress, lessons) into a fresh session. Do not fight autocompact.
