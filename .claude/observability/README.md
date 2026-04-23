# Observability

Two log streams capture failure modes:

- `tool-calls.jsonl` — every tool call (appended by `hooks/log-tool-call.js` on PostToolUse).
- `corrections.jsonl` — user messages that match correction signals (appended by `hooks/log-user-correction.js` on UserPromptSubmit).

Both logs are `.gitignore`d. They are per-machine operational data, not project artifacts.

## Reading the logs

```bash
# Last 20 tool calls
jq -c . .claude/observability/tool-calls.jsonl | tail -20

# Tool-call frequency this session
jq -r '.tool' .claude/observability/tool-calls.jsonl | sort | uniq -c | sort -rn

# All user corrections this week
jq -c 'select(.ts > "'"$(date -u -v-7d +%Y-%m-%dT%H:%M:%S)"'")' .claude/observability/corrections.jsonl
```

## Dashboard (when data warrants)

Once there are 100+ corrections logged, build a simple dashboard — for now, weekly `jq` queries are enough. Do not pre-build tooling before you have the data to justify it.

## What to do with corrections

The corrections log is the input to the **self-edit layer**. Every Friday:

1. Pull this week's corrections: `jq -c 'select(.ts > "...")' corrections.jsonl`
2. For each, write the lesson it implies to `tasks/lessons.md`.
3. Delete duplicate / stale lessons.
4. If a lesson has held 30+ sessions without violation, promote it to `CLAUDE.md`.

See `.claude/self-edit/weekly-ritual.md` for the full process.
