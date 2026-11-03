// The rescale against the engine's own numbers in the committed bundle, for every state:
// each tornado bar is an exact engine run with one assumption at its low or high end, and each
// grid cell is an exact engine run for one combination of levels, so the page's arithmetic must
// reproduce them (to the 4 decimals tornado and grid values are written with).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { adjust, cliCommand, gridValue, relevantIds, type RegisterValues } from './rescale.ts';
import type { Registers, Results, ScenarioName } from '../types/results.ts';

const DIR = fileURLToPath(new URL('../../public/results/', import.meta.url));
const read = <T>(f: string): T => JSON.parse(readFileSync(DIR + f, 'utf8')) as T;
const registers = read<Registers>('registers.json');
const REG: Record<string, RegisterValues> = Object.fromEntries(registers.assumptions.map((a) => [a.id, a]));
const STATES = readdirSync(DIR)
  .filter((f) => /^[A-Z]{2}\.json$/.test(f))
  .map((f) => f.slice(0, 2));
const results = new Map<string, Results>(STATES.map((st) => [st, read<Results>(`${st}.json`)]));

const near = (a: number, b: number, tol = 1e-3) => Math.abs(a - b) <= tol * Math.max(1, Math.abs(b));

test('the bundle has 51 jurisdictions', () => {
  assert.equal(STATES.length, 51);
});

test('every tornado bar is reproduced (multiplicative ids by rescaling, the others by lookup)', () => {
  let checked = 0;
  for (const [st, r] of results) {
    for (const [name, s] of Object.entries(r.scenarios)) {
      for (const bar of s.tornado) {
        for (const level of ['low', 'high'] as const) {
          const a = adjust(s, REG, { [bar.id]: { level } });
          const want = level === 'low' ? bar.at_low : bar.at_high;
          assert.notEqual(a.value, null, `${st} ${name} ${bar.id} ${level}: ${a.reason}`);
          assert.ok(near(a.value as number, want), `${st} ${name} ${bar.id} ${level}: ${a.value} vs ${want} (${a.route})`);
          assert.ok(a.exactness === 'exact' || a.exactness === 'unchanged', `${st} ${name} ${bar.id}: ${a.exactness}`);
          checked += 1;
        }
      }
    }
  }
  assert.ok(checked > 1000, `checked ${checked}`);
});

test('every parking and fee grid cell is reproduced', () => {
  let checked = 0;
  for (const [st, r] of results) {
    for (const name of ['parking', 'fees'] as ScenarioName[]) {
      const s = r.scenarios[name];
      assert.ok(s.grid, `${st} ${name} has no grid`);
      for (const [key, cell] of Object.entries(s.grid.cells)) {
        const settings = Object.fromEntries(
          key.split('|').map((kv) => {
            const [id, lv] = kv.split('=');
            return [id, { level: lv as 'low' | 'mid' | 'high' }];
          }),
        );
        const a = adjust(s, REG, settings);
        assert.equal(a.exactness === 'exact' || a.exactness === 'unchanged', true, `${st} ${name} ${key}: ${a.reason}`);
        assert.ok(near(a.value as number, cell), `${st} ${name} ${key}: ${a.value} vs ${cell}`);
        checked += 1;
      }
    }
  }
  assert.equal(checked, 51 * (81 + 9));
});

const NH = results.get('NH') as Results;

test('a value between two grid levels is interpolated and labeled so', () => {
  const s = NH.scenarios.parking;
  const lo = REG.parking_built_share.mid as number;
  const hi = REG.parking_built_share.high as number;
  const a = adjust(s, REG, { parking_built_share: { value: (lo + hi) / 2 } });
  assert.equal(a.exactness, 'interpolated');
  const g = s.grid!;
  const mid = g.cells['builder_response_override=mid|parking_built_share=mid|parking_cost_per_space=mid|new_home_price_ratio=mid'];
  const high = g.cells['builder_response_override=mid|parking_built_share=high|parking_cost_per_space=mid|new_home_price_ratio=mid'];
  assert.ok(near(a.value as number, (mid + high) / 2, 1e-9));
  assert.equal(gridValue(g, REG, { parking_built_share: 1.5 }), null, 'no extrapolation');
});

test('a typed value for a multiplicative id is exact', () => {
  const s = NH.scenarios.fees;
  const a = adjust(s, REG, { fee_cut_share: { value: 0.3 } });
  assert.equal(a.exactness, 'exact');
  assert.ok(near(a.value as number, s.components.increment_mid_permits * 0.3 / 0.5, 1e-12));
});

test('two non-multiplicative changes outside a grid are not computed in the browser', () => {
  const s = NH.scenarios.adu;
  const a = adjust(s, REG, { adu_rate_tier_1: { level: 'high' }, ramp_adu: { level: 'high' } });
  assert.equal(a.exactness, 'not_available');
  assert.equal(a.value, null);
});

test('a case combines with multiplicative changes only', () => {
  const s = NH.scenarios.adu;
  const key = 'eligible_50_delay_1';
  const a = adjust(s, REG, { adu_permits_per_completion: { level: 'high' } }, key);
  assert.equal(a.exactness, 'exact');
  assert.ok(near(a.value as number, s.cases[key].estimate_permits.mid * 1.4 / 1.18, 1e-12));
  assert.equal(adjust(s, REG, { ramp_adu: { level: 'high' } }, key).exactness, 'not_available');
  assert.equal(adjust(s, REG, {}, key).value, s.cases[key].estimate_permits.mid);
});

test('settings for other scenarios are ignored, and mid is no change', () => {
  const s = NH.scenarios.tod;
  const a = adjust(s, REG, { fee_cut_share: { value: 0.3 }, tod_rate_per_home: { level: 'mid' } });
  assert.equal(a.exactness, 'unchanged');
  assert.equal(a.value, s.components.increment_mid_permits);
  assert.ok(!relevantIds(s).includes('fee_cut_share'));
});

test('the parking density factor rescales only counties outside central metropolitan areas', () => {
  const s = NH.scenarios.parking;
  const scoped = new Set(s.components.linear_counties.parking_low_density_factor);
  assert.ok(scoped.size > 0 && scoped.size < s.components.by_county.length);
  const a = adjust(s, REG, { parking_low_density_factor: { level: 'low' } });
  const want = s.components.by_county.filter((c) => !scoped.has(c.fips)).reduce((t, c) => t + c.increment_mid_permits, 0);
  assert.ok(near(a.value as number, want, 1e-12));
});

test('the command line route names every setting', () => {
  assert.equal(
    cliCommand('UT', { fee_cut_share: { value: 0.3 }, ramp_adu: { level: 'high' } }),
    'uv run hre run --state UT --set fee_cut_share=0.3 --level ramp_adu=high',
  );
});
