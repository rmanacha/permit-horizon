import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fmtCount, fmtShare, outcomeLabel } from './format.ts';

test('counts, shares and labels', () => {
  assert.equal(fmtCount(24250), '24,250');
  assert.equal(fmtCount(276.898), '277');
  assert.equal(fmtCount(0.3), 'under 1');
  assert.equal(fmtCount(0), '0');
  assert.equal(fmtShare(0.0366), '3.7%');
  assert.equal(fmtShare(0.136), '14%');
  assert.equal(fmtShare(0.000126), 'under 0.1%');
  assert.equal(outcomeLabel('cost_response_proxy'), 'cost-response permits');
  assert.equal(outcomeLabel('completed_homes'), 'completed homes');
});
