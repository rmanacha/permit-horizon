// Downloads of the current view, built in the browser from the bundle (nothing is sent anywhere).
import type { Results, ScenarioName } from '../types/results.ts';
import type { ScenarioView } from './viewmodel.ts';
import type { Settings } from './route.ts';

export function toCSV(header: string[], rows: Array<Array<string | number | null>>): string {
  const cell = (v: string | number | null) => {
    if (v === null || v === undefined) return '';
    const s = typeof v === 'number' ? String(Math.round(v * 10000) / 10000) : v;
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [header, ...rows].map((r) => r.map(cell).join(',')).join('\n') + '\n';
}

export function saveFile(name: string, text: string, type: string): void {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** The view as rows: one per layer per scenario, plus the baseline and the package. */
export function viewTable(r: Results, views: ScenarioView[], settings: Settings) {
  const header = ['state', 'item', 'layer', 'low', 'mid', 'high', 'outcome', 'status', 'case', 'your_assumptions_mid', 'how_computed', 'note'];
  const st = r.meta.state;
  const b = r.baseline.state;
  const rows: Array<Array<string | number | null>> = [
    [st, 'baseline', 'baseline', b.low, b.mid, b.high, 'permits', '', '', null, '', r.baseline.band_rule.reading],
  ];
  const changed = Object.keys(settings).length > 0;
  for (const v of views) {
    rows.push([st, v.name, 'benchmark', v.benchmark.low, v.benchmark.mid, v.benchmark.high, v.benchmark.outcome, '', '', null, '', v.benchmark.interpretation]);
    rows.push([st, v.name, 'increment', v.increment.low, v.increment.mid, v.increment.high, 'permits', v.status, v.caseKey,
      changed ? v.adjusted.value : null, changed ? v.adjusted.exactness : '', v.lawNote]);
    rows.push([st, v.name, 'total', v.total.low, v.total.mid, v.total.high, 'permits', v.status, v.caseKey, null, '', 'baseline plus increment, low with low, high with high']);
  }
  if (r.combined) {
    const c = r.combined.increment.estimate;
    rows.push([st, 'combined', 'increment', c.low, c.mid, c.high, 'permits', 'register_default', 'register_default', null, '', `${r.combined.label}; ${r.combined.limits[0] ?? ''}`]);
  }
  rows.push([st, 'cross_check', 'housing_units_pep', null, r.cross_check.housing_units_pep.state?.net_change ?? null, null, 'stock_change', '', '', null, '', r.cross_check.housing_units_pep.caveat]);
  return { header, rows };
}

/** Every county figure in long form, each row with its outcome label and caveats. */
export function countyTable(r: Results) {
  const header = ['state', 'county_fips', 'county', 'measure', 'low', 'mid', 'high', 'outcome', 'caveats'];
  const st = r.meta.state;
  const rows: Array<Array<string | number | null>> = [];
  for (const c of r.baseline.county) {
    rows.push([st, c.fips, c.name, 'baseline', c.low, c.mid, c.high, 'permits', r.baseline.band_rule.applied_to_counties]);
  }
  for (const [name, s] of Object.entries(r.scenarios) as Array<[ScenarioName, Results['scenarios'][ScenarioName]]>) {
    for (const c of s.benchmark.by_county) {
      rows.push([st, c.fips, c.name, `${name} benchmark`, c.low, c.mid, c.high, s.benchmark.outcome, s.benchmark.interpretation]);
    }
    for (const c of s.increment.by_county) {
      rows.push([st, c.fips, c.name, `${name} increment`, c.low, c.mid, c.high, 'permits',
        `register default; ${s.increment.current_law.note} Results are statewide; county figures are the parts of the state estimate, not county forecasts.`]);
    }
  }
  const pep = r.cross_check.housing_units_pep;
  for (const c of pep.county) {
    rows.push([st, c.fips, c.name, 'housing-unit estimates, net change since April 2020', null, c.net_change, null, 'stock_change', pep.caveat]);
  }
  return { header, rows };
}
