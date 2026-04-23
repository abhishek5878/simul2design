#!/usr/bin/env node
// Observability: detect user corrections and log them.
// Runs on UserPromptSubmit. Corrections are the signal self-edit needs.
// Crude heuristic: lowercase user message matches any of the phrases below.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const logDir = path.join(root, '.claude', 'observability');
const logPath = path.join(logDir, 'corrections.jsonl');

const CORRECTION_SIGNALS = [
  "don't", "do not", "stop", "no,", "wrong", "that's not", "that is not",
  "undo", "revert", "instead", "actually", "rather than", "i said",
  "you're not", "you are not", "that's incorrect", "mistake"
];

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
  process.exit(0);
}

const prompt = (event.prompt || event.message || '').toString().toLowerCase();
if (!prompt) process.exit(0);

const matched = CORRECTION_SIGNALS.filter((s) => prompt.includes(s));
if (matched.length === 0) process.exit(0);

const record = {
  ts: new Date().toISOString(),
  session_id: event.session_id || null,
  signals: matched,
  snippet: prompt.slice(0, 200)
};

try {
  fs.mkdirSync(logDir, { recursive: true });
  fs.appendFileSync(logPath, JSON.stringify(record) + '\n');
  process.stderr.write('[log-user-correction] Correction signal detected. Consider adding a lesson to tasks/lessons.md before continuing.\n');
} catch {
  // Silent.
}

process.exit(0);
