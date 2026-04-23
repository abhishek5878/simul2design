#!/usr/bin/env node
// Post-tool-use reminder. Fires after significant actions.
// Nudges the agent to update tasks/progress.md when meaningful work happened.

const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const progressPath = path.join(root, 'tasks', 'progress.md');

if (!fs.existsSync(progressPath)) {
  process.exit(0);
}

const stats = fs.statSync(progressPath);
const ageMinutes = (Date.now() - stats.mtimeMs) / 60000;

if (ageMinutes > 30) {
  process.stderr.write(`[post-tool-use-progress] tasks/progress.md last updated ${Math.round(ageMinutes)}m ago. If a phase advanced, update it.\n`);
}
process.exit(0);
