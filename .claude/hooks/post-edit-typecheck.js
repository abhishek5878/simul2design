#!/usr/bin/env node
// Post-edit typecheck. Runs after any Edit or Write.
// Graceful when no code exists yet: exit 0 silently.

const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const pkgPath = path.join(root, 'package.json');
const tsconfigPath = path.join(root, 'tsconfig.json');

if (!fs.existsSync(pkgPath) || !fs.existsSync(tsconfigPath)) {
  process.exit(0);
}

try {
  execSync('npx --no-install tsc --noEmit', { stdio: 'inherit', cwd: root });
} catch {
  process.stderr.write('[post-edit-typecheck] type errors present — fix before committing.\n');
}
process.exit(0);
