# Planning rules

## When to plan

- Any task with 3+ steps, or touching 2+ files.
- Any architectural decision (new skill, new agent, new data format).
- Any change to the synthesis pipeline order.

## How to plan

1. Read `tasks/lessons.md` first. Don't re-learn.
2. Write or update `tasks/<feature>-plan.md` with:
   - Goal (one paragraph, in user's words).
   - Phases with checkbox items. Each phase has a status: `pending` / `in_progress` / `complete`.
   - Errors Encountered table (phase, error, resolution).
3. Check in with the user before starting implementation.
4. Update phase status in the same turn as the work happens.

## When NOT to plan

- Single-file trivial edits.
- Exploratory questions ("how does X work here?").
- A plan that would be longer than the implementation.

## Forward-looking vs backward-looking

- `tasks/<feature>-plan.md` is forward-looking: what WILL happen.
- `tasks/progress.md` is backward-looking: what HAPPENED.
- Never conflate them. Updating the code without updating the plan is how plans drift from reality.
