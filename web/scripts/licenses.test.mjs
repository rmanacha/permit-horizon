// Every npm package in the lock file (all platforms, including optional native binaries) must
// carry a licence the challenge allows for dependencies: MIT, ISC, BSD-2/3-Clause or Apache-2.0.
// The lock file records each package's licence, so this needs no download and no extra tool.
// (`npx license-checker --summary` gives the same answer for the installed tree; see docs/methods/ui.md.)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const ALLOWED = new Set(['MIT', 'ISC', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', '0BSD']);
const lock = JSON.parse(readFileSync(new URL('../package-lock.json', import.meta.url), 'utf8'));

test('every locked package has a permissive licence', () => {
  const bad = [];
  let n = 0;
  for (const [path, pkg] of Object.entries(lock.packages)) {
    if (path === '') continue;
    n += 1;
    if (!ALLOWED.has(pkg.license)) bad.push(`${path}: ${pkg.license}`);
  }
  assert.ok(n > 0);
  assert.deepEqual(bad, [], `non-permissive or missing licences:\n${bad.join('\n')}`);
});

test('the site itself is Apache-2.0', () => {
  assert.equal(lock.packages[''].license, 'Apache-2.0');
});
