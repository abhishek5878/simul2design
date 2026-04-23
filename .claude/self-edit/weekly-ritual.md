# Weekly self-edit ritual

Every Friday (or whichever cadence sticks), 15-30 minutes. This is the compounding layer — skip it and the system stops learning.

## The five steps

### 1. Pull the week's corrections

```bash
SINCE=$(date -u -v-7d +%Y-%m-%dT%H:%M:%S)
jq -c --arg t "$SINCE" 'select(.ts > $t)' .claude/observability/corrections.jsonl > /tmp/week-corrections.jsonl
wc -l /tmp/week-corrections.jsonl
```

If zero lines: either a quiet week (fine) or the correction detector missed signals (look at the transcripts manually).

### 2. For each correction, propose a lesson

Open the transcript around each correction timestamp. Ask:
- What did I do that triggered the correction?
- What is the general rule I should follow next time?
- Is the rule already in `tasks/lessons.md`?

If not already captured, draft a one-line entry in the lesson format:

```
[CATEGORY] <situation> — rule: <action>.
```

### 3. Run an adversarial review of the proposed lessons

Before committing any new lesson, run it through this prompt (separate Claude session):

> Here is a proposed lesson for my agent system: "[lesson text]"
>
> Give me the strongest objection to adding this lesson:
> - Is it too specific to generalize?
> - Is it too vague to pattern-match?
> - Does it conflict with an existing rule in the file?
> - Will it become obsolete in 1 week?
>
> Reject it unless you can defend it against all four.

Keep only the lessons that survive.

### 4. Accept / reject individually

For each surviving candidate:
- [ ] Read it aloud. Does it make sense out of context?
- [ ] Add it to `tasks/lessons.md` under the right category, OR
- [ ] Skip it (write the reason in `tasks/progress.md` for future reflection).

### 5. Promote and prune

- **Promote:** If a lesson has held for ~30 sessions without violation, move it to `.claude/CLAUDE.md` as a hard rule. Delete from `lessons.md`.
- **Prune:** If two lessons overlap, merge. If a lesson has been obsolete for 4+ weeks, delete. If `lessons.md` has more than ~50 entries, you're hoarding — consolidate.
- Commit the changes with message: `chore(self-edit): week of YYYY-MM-DD — N lessons added, M pruned`.

## Guardrails

- **Immutable evaluator.** The self-edit process can update skills, rules, and CLAUDE.md. It must never edit the success metric (predicted-vs-actual delta in `tasks/findings.md` for synthesis runs). Separation of direction, implementation, and evaluation is the thing that keeps the compounding honest.
- **One-person sign-off.** The user approves every lesson before it lands. No auto-apply.
- **Adversarial by default.** Treat every proposed lesson as guilty until proven innocent. Sycophantic self-edit is worse than no self-edit.

## Optional: Evo plugin

Once the manual version has run for ~4 cycles, consider the Evo plugin (Claude Code) for tree-search-over-code-changes with worktree isolation and regression gating. Requires a stable test suite first, so don't jump to it before there's code to regress.
