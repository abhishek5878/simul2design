#!/usr/bin/env node
// Pre-tool-use reminder. Fires before Write/Edit/Bash.
// Points the agent back at the active plan so it stays anchored.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const todoPath = path.join(root, 'tasks', 'todo.md');

if (!fs.existsSync(todoPath)) {
  process.exit(0);
}

const content = fs.readFileSync(todoPath, 'utf8');
const activeMatch = content.match(/\*\*Active plan:\*\*\s*`([^`]+)`/);
if (!activeMatch) {
  process.exit(0);
}

const activePlan = activeMatch[1];
const activePlanPath = path.join(root, activePlan);
if (!fs.existsSync(activePlanPath)) {
  process.stderr.write(`[pre-tool-use-plan] tasks/todo.md points at ${activePlan} but the file does not exist.\n`);
  process.exit(0);
}

process.stderr.write(`[pre-tool-use-plan] Active plan: ${activePlan}. Verify this action aligns with an in_progress phase.\n`);
process.exit(0);
