// The bundle contract: every committed file has the keys and types src/types/results.ts
// declares and the pages read (docs/methods/results_schema.md). A schema change in the engine
// that the site does not know about fails here, not on a judge's screen.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { SCENARIOS, type BundleIndex, type BundleMeta, type Registers, type Results } from '../types/results.ts';

const DIR = fileURLToPath(new URL('../../public/results/', import.meta.url));
const read = <T>(f: string): T => JSON.parse(readFileSync(DIR + f, 'utf8')) as T;
const OUTCOMES = new Set(['permits', 'net_permits', 'completed_homes', 'stock_change', 'cost_response_proxy']);
const STATES = readdirSync(DIR).filter((f) => /^[A-Z]{2}\.json$/.test(f)).map((f) => f.slice(0, 2));

const isLMH = (x: unknown) =>
  typeof x === 'object' && x !== null && ['low', 'mid', 'high'].every((k) => typeof (x as Record<string, unknown>)[k] === 'number');

test('index, registers and meta have the shape the site reads', () => {
  const index = read<BundleIndex>('index.json');
  assert.equal(index.states.length, 51);
  for (const row of index.states) {
    assert.ok(isLMH(row.baseline) && row.name && row.state);
    for (const n of SCENARIOS) assert.ok(isLMH(row.scenarios[n].increment), `${row.state} ${n}`);
  }
  const reg = read<Registers>('registers.json');
  assert.ok(reg.assumptions.length >= 50);
  for (const e of reg.assumptions) {
    assert.ok(e.id && e.label && e.unit && e.grade && Array.isArray(e.sources) && 'low' in e && 'mid' in e && 'high' in e, e.id);
  }
  assert.ok(reg.sources.length >= 10 && reg.sources.every((s) => s.title && 'license' in s && Array.isArray(s.where)));
  assert.equal(typeof reg.current_law_default, 'string');
  const meta = read<BundleMeta>('meta.json');
  assert.equal(meta.results_schema_version, '1');
  assert.equal(typeof meta.no_llm, 'string');
});

test('every state file has the keys and types the pages use', () => {
  for (const st of STATES) {
    const r = read<Results>(`${st}.json`);
    const where = (k: string) => `${st}: ${k}`;
    assert.equal(r.results_schema_version, '1', where('schema'));
    assert.equal(r.meta.state, st);
    assert.ok(r.meta.build_id && r.meta.vintages, where('meta'));
    const b = r.baseline;
    assert.ok(isLMH(b.state) && b.county.length > 0 && b.forecast_years.length === 5, where('baseline'));
    assert.ok(b.band_rule.reading && b.band_rule.reading_history && b.band_rule.coverage_by_period.length === 5, where('band_rule'));
    assert.equal(typeof b.alternative_band.available, 'boolean');
    const p = r.cross_check.housing_units_pep;
    assert.equal(p.outcome, 'stock_change');
    assert.equal(p.can_add_to_baseline, false);
    assert.ok(typeof p.caveat === 'string' && Array.isArray(p.county), where('pep'));
    for (const n of SCENARIOS) {
      const s = r.scenarios[n];
      const w = (k: string) => where(`${n}.${k}`);
      assert.ok(s.label && s.formula, w('label'));
      assert.ok(isLMH(s.benchmark) && OUTCOMES.has(s.benchmark.outcome), w('benchmark'));
      assert.ok(isLMH(s.increment.estimate) && s.increment.outcome === 'permits', w('increment'));
      assert.ok(isLMH(s.increment.completed_homes_equivalent), w('homes'));
      assert.equal(typeof s.increment.current_law.note, 'string');
      assert.equal(s.increment.years.length, 5);
      assert.ok(isLMH(s.total.estimate), w('total'));
      for (const k of ['register_default', 'no_change', 'after_horizon', ...[25, 50, 100].flatMap((sh) => [0, 1, 2].map((d) => `eligible_${sh}_delay_${d}`))]) {
        assert.ok(isLMH(s.cases[k]?.estimate_permits) && Array.isArray(s.cases[k].assumptions), w(`cases.${k}`));
      }
      for (const t of s.tornado) assert.ok(t.id && typeof t.at_low === 'number' && typeof t.at_high === 'number' && t.low_text !== undefined, w('tornado'));
      assert.ok(typeof s.joint.favorable.value === 'number' && Array.isArray(s.joint.unfavorable.settings), w('joint'));
      const c = s.components;
      assert.ok(typeof c.increment_mid_permits === 'number' && c.linear_in && c.linear_counties && c.by_county.length === b.county.length, w('components'));
      if (n === 'parking' || n === 'fees') assert.ok(s.grid && s.grid.params.length && Object.keys(s.grid.cells).length === 3 ** s.grid.params.length, w('grid'));
      assert.ok(Array.isArray(s.limits) && s.limits.length > 0 && Array.isArray(s.narrative), w('limits'));
    }
    assert.ok(r.combined && isLMH(r.combined.increment.estimate) && r.combined.label && Array.isArray(r.combined.rules), where('combined'));
    assert.equal(typeof r.no_llm, 'string');
  }
});
