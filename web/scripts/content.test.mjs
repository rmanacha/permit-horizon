// The site's glossary, limits and tour come from Markdown; these tests keep the JSON the site
// imports in step with it, make sure every term the components link to is defined, and that every
// tour stop points at an element on its page and reads like the rest of the site.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { render } from './build_content.mjs';
import { PAGES } from '../src/lib/route.ts';

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

test('glossary.json, limits.json and tour.json match their Markdown sources (fix: cd web && npm run content)', () => {
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

test('every tour stop targets an element on a real page, with no internal wording', () => {
  const { stops } = JSON.parse(readFileSync(join(SRC, 'content', 'tour.json'), 'utf8'));
  assert.equal(stops.length, 5);
  const code = sourceFiles(SRC).map((f) => readFileSync(f, 'utf8')).join('\n');
  // decision numbers, phase names, results keys and register ids never reach a reader (as tests/test_bundle.py checks the bundle)
  const internal = /\bdecisions? \d|\bPhase \d|\b[a-z]+_[a-z_]+\b/;
  for (const s of stops) {
    assert.ok(code.includes(`data-tour="${s.target}"`), `stop "${s.title}": no element carries data-tour="${s.target}"`);
    assert.ok(PAGES.includes(s.page), `stop "${s.title}": unknown page ${s.page}`);
    assert.ok(s.text.split('. ').length <= 4, `stop "${s.title}": more than four sentences`);
    assert.equal(internal.exec(`${s.title} ${s.text}`), null, `stop "${s.title}" uses internal wording`);
  }
});
