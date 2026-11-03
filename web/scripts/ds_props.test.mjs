// The design-system port keeps the system's props: every prop the system declares for a
// component we use exists on our TypeScript port, except `style`, which becomes `className`
// (no inline styles on this site). Source of truth: scripts/ds-reference/index.d.ts.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const ref = readFileSync(`${ROOT}scripts/ds-reference/index.d.ts`, 'utf8');
const PORTED = { Button: 'Button', Tag: 'Tag', Card: 'Card', StatCallout: 'StatCallout', Tabs: 'Tabs', Select: 'Select', Input: 'Input', Checkbox: 'Checkbox' };

function props(src, name) {
  const m = new RegExp(`interface ${name}Props\\s*\\{([\\s\\S]*?)\\n\\}`).exec(src);
  assert.ok(m, `${name}Props not found`);
  return [...m[1].matchAll(/^\s*'?([A-Za-z-]+)'?\??\s*:/gm)].map((x) => x[1]);
}

test('every declared design-system prop exists on the port (style becomes className)', () => {
  for (const [name, file] of Object.entries(PORTED)) {
    const ours = new Set(props(readFileSync(`${ROOT}src/components/ds/${file}.tsx`, 'utf8'), name));
    for (const p of props(ref, name)) {
      const want = p === 'style' ? 'className' : p;
      assert.ok(ours.has(want), `${name}: prop "${want}" is declared by the design system but missing on the port`);
    }
    assert.ok(!ours.has('style'), `${name}: the port must not take a style prop`);
  }
});
