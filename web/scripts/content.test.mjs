// The site's glossary and limits come from Markdown under docs/; these tests keep the JSON the
// site imports in step with it, and make sure every term the components link to is defined.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { render } from './build_content.mjs';

const REPO = fileURLToPath(new URL('../../', import.meta.url));
const SRC = join(REPO, 'web', 'src');

function sourceFiles(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) sourceFiles(p, out);
    else if (/\.tsx?$/.test(name) && !name.endsWith('.test.ts')) out.push(p);
  }
  return out;
}

test('glossary.json and limits.json match their Markdown sources (fix: cd web && npm run content)', () => {
  for (const [path, text] of Object.entries(render())) {
    assert.equal(readFileSync(join(REPO, path), 'utf8'), text, `${path} is out of date`);
  }
});

test('every glossary id the site links to is defined in docs/GLOSSARY.md', () => {
  const glossary = JSON.parse(readFileSync(join(SRC, 'content', 'glossary.json'), 'utf8'));
  const ids = new Set(glossary.terms.map((t) => t.id));
  const missing = [];
  for (const f of sourceFiles(SRC)) {
    for (const m of readFileSync(f, 'utf8').matchAll(/term="([a-z0-9-]+)"|glossary: '([a-z0-9-]+)'/g)) {
      const id = m[1] ?? m[2];
      if (!ids.has(id)) missing.push(`${f.slice(SRC.length + 1)}: ${id}`);
    }
  }
  assert.deepEqual(missing, []);
});
