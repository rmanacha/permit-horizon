import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { countyTable, toCSV, viewTable } from './downloads.ts';
import { registerLookup, scenarioView } from './viewmodel.ts';
import { SCENARIOS, type Registers, type Results } from '../types/results.ts';

const DIR = fileURLToPath(new URL('../../public/results/', import.meta.url));
const UT = JSON.parse(readFileSync(`${DIR}UT.json`, 'utf8')) as Results;
const REG = registerLookup((JSON.parse(readFileSync(`${DIR}registers.json`, 'utf8')) as Registers).assumptions);

test('CSV escapes commas, quotes and new lines', () => {
  assert.equal(toCSV(['a', 'b'], [['x, y', 'say "hi"'], [1.23456, null]]), 'a,b\n"x, y","say ""hi"""\n1.2346,\n');
});

test('every downloaded row carries an outcome label', () => {
  const views = SCENARIOS.map((n) => scenarioView(UT, n, REG, {}, { kind: 'register_default' }));
  for (const t of [viewTable(UT, views, {}), countyTable(UT)]) {
    const col = t.header.indexOf('outcome');
    assert.ok(col >= 0);
    assert.ok(t.rows.length > 10);
    for (const row of t.rows) assert.ok(typeof row[col] === 'string' && (row[col] as string).length > 0, String(row));
  }
  const counties = countyTable(UT);
  assert.ok(counties.rows.every((r) => typeof r[counties.header.indexOf('caveats')] === 'string'));
});
