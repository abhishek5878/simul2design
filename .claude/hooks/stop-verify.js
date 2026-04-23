#!/usr/bin/env node
// Stop-event check. Fires when Claude Code is about to end the session.
// Scans the active plan for phases left as `in_progress` without a handoff note.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const todoPath = path.join(root, 'tasks', 'todo.md');

if (!fs.existsSync(todoPath)) {
  process.exit(0);
}

const todoContent = fs.readFileSync(todoPath, 'utf8');
const activeMatch = todoContent.match(/\*\*Active plan:\*\*\s*`([^`]+)`/);
if (!activeMatch) {
  process.exit(0);
}

const activePlanPath = path.join(root, activeMatch[1]);
if (!fs.existsSync(activePlanPath)) {
  process.exit(0);
}

const plan = fs.readFileSync(activePlanPath, 'utf8');
const phaseBlocks = plan.split(/^## Phase /m).slice(1);
const dangling = [];

for (const block of phaseBlocks) {
  const phaseName = block.split('\n')[0].trim();
  const statusMatch = block.match(/\*\*Status:\*\*\s*(\w+)/);
  if (!statusMatch) continue;
  if (statusMatch[1].toLowerCase() !== 'in_progress') continue;
  const hasHandoff = /\*\*Handoff:\*\*/i.test(block);
  if (!hasHandoff) dangling.push(phaseName);
}

if (dangling.length > 0) {
  process.stderr.write(`[stop-verify] ${dangling.length} phase(s) in_progress without a handoff note: ${dangling.join(', ')}.\n`);
  process.stderr.write('[stop-verify] Add a **Handoff:** note to each before ending the session.\n');
}
process.exit(0);
