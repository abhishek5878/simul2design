#!/usr/bin/env node
// Observability: append every tool call to a JSONL log. Runs on every PostToolUse.
// Data lands in .claude/observability/tool-calls.jsonl. Read with:
//   jq -c '.' .claude/observability/tool-calls.jsonl | tail -20
//
// Reads the hook event from stdin per Claude Code's hook JSON schema.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const logDir = path.join(root, '.claude', 'observability');
const logPath = path.join(logDir, 'tool-calls.jsonl');

let stdin = '';
try {
  stdin = fs.readFileSync(0, 'utf8');
} catch {
  process.exit(0);
}

let event;
try {
  event = JSON.parse(stdin || '{}');
} catch {
  event = { raw: stdin };
}

const record = {
  ts: new Date().toISOString(),
  tool: event.tool_name || event.tool || null,
  session_id: event.session_id || null,
  cwd: event.cwd || root,
  matcher_result: event.tool_input ? Object.keys(event.tool_input) : null
};

try {
  fs.mkdirSync(logDir, { recursive: true });
  fs.appendFileSync(logPath, JSON.stringify(record) + '\n');
} catch {
  // Silent: observability must never block the session.
}

process.exit(0);
