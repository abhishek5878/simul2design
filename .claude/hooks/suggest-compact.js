#!/usr/bin/env node
// Suggest /compact after ~50 tool calls to pre-empt context rot.
// Counter is persisted in .claude/.tool-call-counter.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const counterPath = path.join(root, '.claude', '.tool-call-counter');
const THRESHOLD = 50;
const RESET_AT = 100;

let count = 0;
if (fs.existsSync(counterPath)) {
  const raw = fs.readFileSync(counterPath, 'utf8').trim();
  count = Number.parseInt(raw, 10) || 0;
}
count += 1;

if (count === THRESHOLD) {
  process.stderr.write(`[suggest-compact] ${THRESHOLD} tool calls this session. Consider /compact or a context reset.\n`);
}
if (count >= RESET_AT) {
  count = 0;
}

fs.writeFileSync(counterPath, String(count));
process.exit(0);
