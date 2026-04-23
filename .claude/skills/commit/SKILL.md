---
name: commit
description: Trigger when the user asks to commit, check in, or save work. Stages changes, writes a conventional commit message, and creates the commit after running the verify skill.
---

# Commit skill

## When to use

- User says "commit," "check in," "save this," "git commit."
- End of a phase where work is ready to ship.
- After a `verify` run comes back green.

## When NOT to use

- Work is in progress and tests haven't been run. Run `verify` first.
- User is experimenting — use `checkpoint` skill instead.

## Workflow

1. Run `verify` skill. If red, STOP. Report failures. Do not commit.
2. Run in parallel:
   - `git status` to see untracked files.
   - `git diff` (staged + unstaged) to see changes.
   - `git log -5 --oneline` to match the repo's commit style.
3. Stage only the files relevant to the current concern. Never `git add -A` without reading what you're adding.
4. Draft a commit message:
   - Subject: imperative mood, ≤72 chars. Example: `Add parse-simulation element-extraction step`.
   - Body: one short paragraph on WHY. No bullet lists of what changed — the diff shows that.
5. Commit with a HEREDOC to preserve formatting. Include the Co-Authored-By trailer.
6. Run `git status` to confirm the commit succeeded.
7. Update `tasks/progress.md` with the commit SHA and one-line summary.

## Decision tree

- If `.env`, credentials, or large binaries are in the diff: STOP. Warn the user.
- If the diff has unrelated concerns (e.g., bug fix + unrelated refactor): propose splitting into multiple commits.
- If a pre-commit hook fails: fix the underlying issue, re-stage, create a NEW commit. Never `--amend` after hook failure.

## Success criteria

- Commit message body explains WHY, not WHAT.
- Only relevant files staged.
- `verify` passed before the commit.
- `progress.md` reflects the commit.

## Common pitfalls

- Committing without running tests. Fix: hard rule, run `verify` first.
- Opportunistic refactoring bundled into a bug-fix commit. Fix: one commit, one concern.
- Generic messages like "update code." Fix: if you can't name the concern in 10 words, you don't know what changed.
