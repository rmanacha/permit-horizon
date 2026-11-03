// Rishabh restyles the site later, so the styling has one home: src/styles/tokens.css.
// These rules keep it that way: components carry class names only (no inline styles), and no
// color, font family or length is written anywhere but tokens.css.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = fileURLToPath(new URL('../src/', import.meta.url));
const TOKENS = join(SRC, 'styles', 'tokens.css');

function files(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) files(p, out);
    else out.push(p);
  }
  return out;
}

const all = files(SRC);
const code = all.filter((p) => /\.(tsx?|css)$/.test(p) && !p.endsWith('.test.ts'));

test('no inline styles in components', () => {
  for (const p of code.filter((f) => f.endsWith('.tsx'))) {
    const text = readFileSync(p, 'utf8');
    assert.ok(!/\bstyle\s*=\s*\{/.test(text), `${relative(SRC, p)} uses style={...}; add a class in app.css`);
  }
});

test('colors and font families are written only in tokens.css', () => {
  for (const p of code.filter((f) => f !== TOKENS)) {
    const text = readFileSync(p, 'utf8');
    const hit = /#[0-9a-fA-F]{3,8}\b(?![\w-])|\brgba?\(|\bhsla?\(|font-family\s*:(?!\s*var\()/.exec(text);
    assert.equal(hit, null, `${relative(SRC, p)} contains ${hit?.[0]}; use a token from tokens.css`);
  }
});

test('lengths in stylesheets come from tokens (except media-query breakpoints)', () => {
  for (const p of code.filter((f) => f.endsWith('.css') && f !== TOKENS)) {
    const lines = readFileSync(p, 'utf8').split('\n');
    lines.forEach((line, i) => {
      if (/^\s*@media/.test(line) || /^\s*\/?\*/.test(line)) return;
      const hit = /(?<![\w-])\d*\.?\d+(px|rem|em)\b/.exec(line.replace(/var\([^)]*\)/g, ''));
      assert.equal(hit, null, `${relative(SRC, p)}:${i + 1} writes ${hit?.[0]}; add a token`);
    });
  }
});
