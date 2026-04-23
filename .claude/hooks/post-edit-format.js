#!/usr/bin/env node
// Post-edit formatter. Runs after any Edit or Write.
// Graceful when no code exists yet: exit 0 silently.

const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = process.cwd();
const pkgPath = path.join(root, 'package.json');

if (!fs.existsSync(pkgPath)) {
  process.exit(0);
}

let pkg;
try {
  pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
} catch {
  process.exit(0);
}

const hasFormat = pkg.scripts && pkg.scripts.format;
if (!hasFormat) {
  process.exit(0);
}

try {
  execSync('npm run format --silent', { stdio: 'inherit', cwd: root });
} catch {
  process.stderr.write('[post-edit-format] formatter failed — fix before committing.\n');
}
process.exit(0);
