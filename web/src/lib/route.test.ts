import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildHash, caseKey, parseHash, DEFAULT_VIEW } from './route.ts';

test('a share link restores the view', () => {
  const v = {
    ...DEFAULT_VIEW,
    page: 'scenario' as const,
    state: 'UT',
    scenario: 'fees' as const,
    caseSel: { kind: 'eligible' as const, share: 50 as const, delay: 1 as const },
    settings: { builder_response_override: { level: 'high' as const }, fee_cut_share: { value: 0.3 } },
    show: ['adu' as const, 'fees' as const],
  };
  const h = buildHash(v);
  assert.equal(h, '#/scenario?st=UT&sc=fees&case=50-1&set=builder_response_override:high,fee_cut_share:0.3&show=adu,fees');
  assert.deepEqual(parseHash(h), v);
  assert.equal(caseKey(v.caseSel), 'eligible_50_delay_1');
});

test('junk in the hash falls back to defaults', () => {
  const v = parseHash('#/nowhere?st=new&sc=x&case=7-9&set=a:b,:1,Bad-Id:2&show=zz');
  assert.deepEqual(v, DEFAULT_VIEW);
  assert.equal(buildHash(DEFAULT_VIEW), '#/explore');
});
