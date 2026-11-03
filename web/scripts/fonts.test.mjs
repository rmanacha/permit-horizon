// The self-hosted fonts (web/public/fonts/) are exactly the files the manifest names, each from
// the official Google Fonts repository at a pinned commit, with the SIL Open Font License text
// for each family beside them. No Biro Script (commercial) and no other font file.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const DIR = fileURLToPath(new URL('../public/fonts/', import.meta.url));
const manifest = JSON.parse(readFileSync(`${DIR}manifest.json`, 'utf8'));

test('every font file is in the manifest with a matching sha256 and an OFL licence', () => {
  const files = readdirSync(DIR).filter((f) => f !== 'manifest.json');
  assert.deepEqual(files.sort(), Object.keys(manifest.files).sort());
  for (const f of files) {
    const sha = createHash('sha256').update(readFileSync(DIR + f)).digest('hex');
    assert.equal(sha, manifest.files[f].sha256, `${f} differs from its manifest entry`);
    assert.match(manifest.files[f].url, /^https:\/\/raw\.githubusercontent\.com\/google\/fonts\/[0-9a-f]{40}\/ofl\//);
  }
  for (const lic of files.filter((f) => f.endsWith('OFL.txt'))) {
    assert.match(readFileSync(DIR + lic, 'utf8'), /SIL Open Font License, Version 1\.1/);
  }
  assert.ok(!files.some((f) => /biro/i.test(f)), 'Biro Script is commercial and must not be shipped');
});
