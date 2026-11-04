import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { lawLead, rankIncrements, registerLookup, scenarioView } from './viewmodel.ts';
import type { Registers, Results } from '../types/results.ts';

const DIR = fileURLToPath(new URL('../../public/results/', import.meta.url));
const NH = JSON.parse(readFileSync(`${DIR}NH.json`, 'utf8')) as Results;
const REG = registerLookup((JSON.parse(readFileSync(`${DIR}registers.json`, 'utf8')) as Registers).assumptions);

test('register default: increment, total and homes come straight from the results file', () => {
  const v = scenarioView(NH, 'adu', REG, {}, { kind: 'register_default' });
  assert.deepEqual(v.increment, NH.scenarios.adu.increment.estimate);
  assert.equal(v.total.mid, NH.baseline.state.mid + NH.scenarios.adu.increment.estimate.mid);
  assert.ok(Math.abs(v.homes.mid - NH.scenarios.adu.increment.completed_homes_equivalent.mid) < 1e-9);
  assert.equal(v.status, 'register_default');
  assert.equal(v.share, 0.25);
  assert.equal(v.humanReview, 'human review pending');
});

test('the current-law lead-in says whether any of the reform is in state law', () => {
  const AZ = JSON.parse(readFileSync(`${DIR}AZ.json`, 'utf8')) as Results;
  const adu = scenarioView(AZ, 'adu', REG, {}, { kind: 'register_default' });
  const tod = scenarioView(AZ, 'tod', REG, {}, { kind: 'register_default' });
  assert.equal(lawLead(adu.lawSource, adu.lawStrength), 'A statewide law is on file. ');
  assert.equal(lawLead(tod.lawSource, tod.lawStrength), 'State law checked. ');
  assert.equal(lawLead('default', 0), '');
});

test('a user case reads that case from the file', () => {
  const v = scenarioView(NH, 'fees', REG, {}, { kind: 'eligible', share: 50, delay: 1 });
  assert.deepEqual(v.increment, NH.scenarios.fees.cases.eligible_50_delay_1.estimate_permits);
  assert.equal(v.status, 'user_case');
  assert.equal(v.delay, 1);
});

test('order flips are reported only for strict reversals', () => {
  const { order, flips } = rankIncrements([
    { name: 'adu', increment: { low: 40, mid: 277, high: 1556 } },
    { name: 'fees', increment: { low: 0, mid: 934, high: 3535 } },
    { name: 'parking', increment: { low: 0, mid: 157, high: 596 } },
  ]);
  assert.deepEqual(order, ['fees', 'adu', 'parking']);
  assert.deepEqual(flips, [{ above: 'fees', below: 'adu', level: 'low' }]);
});
