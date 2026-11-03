// Assumption changes without Python (decision 25): the page never reruns the model. When a user
// moves an assumption it recomputes a scenario's middle increment from what the engine exported:
//
//   1. multiplicative ids (components.linear_in): exact. Each county's increment is proportional
//      to the value, so new = sum over counties of old x new value / old value (an id listed in
//      components.linear_counties multiplies only those counties). Same arithmetic as the engine;
//      web/scripts/rescale_equality.mjs checks it against `hre run --set` to 1e-9.
//   2. the parking and fee grids: the engine ran every low/mid/high combination of their
//      assumptions, so a combination of levels is a lookup (exact); a value between two levels
//      is interpolated linearly between the engine's results and labeled "interpolated".
//   3. one other assumption at its low or high end: the engine's tornado bar holds that exact
//      one-at-a-time result.
//   4. anything else: not computed in the browser; the page shows the `hre run --set` command.
//
// This file imports nothing at run time (only types), so Node runs it directly in the tests.
import type { Components, Grid, Level, TornadoBar } from '../types/results.ts';

export type ParamValue = number | number[];

/** What the engine exported for one scenario that the rescale needs. */
export interface RescaleScenario {
  components: Components;
  grid: Grid | null;
  tornado: TornadoBar[];
  cases: Record<string, { estimate_permits: { mid: number } }>;
}

/** A register entry's three values (and nothing else the rescale needs). */
export interface RegisterValues {
  id: string;
  low: ParamValue;
  mid: ParamValue;
  high: ParamValue;
}

export type Choice = { level: Level } | { value: number };

export interface Change {
  id: string;
  value: ParamValue;
  /** The named level when the value is one; null for a typed value. */
  level: Level | null;
}

export type Exactness = 'unchanged' | 'exact' | 'interpolated' | 'not_available';
export type Route = 'none' | 'multiplicative' | 'grid' | 'tornado' | 'case';

export interface Adjusted {
  value: number | null;
  exactness: Exactness;
  route: Route;
  changes: Change[];
  reason: string;
}

const LEVEL_ORDER: Level[] = ['low', 'mid', 'high'];

function same(a: ParamValue, b: ParamValue): boolean {
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((x, i) => close(x, b[i]));
  }
  return close(a, b);
}

function close(a: number, b: number): boolean {
  return a === b || Math.abs(a - b) <= 1e-12 * Math.max(Math.abs(a), Math.abs(b));
}

/** The ids whose change can move this scenario's result. */
export function relevantIds(s: RescaleScenario): string[] {
  const ids = new Set<string>(Object.keys(s.components.linear_in));
  for (const id of s.grid?.params ?? []) ids.add(id);
  for (const b of s.tornado) ids.add(b.id);
  return [...ids];
}

export function isMultiplicative(s: RescaleScenario, id: string): boolean {
  return id in s.components.linear_in;
}

/** Can the user type any number for this id (exact or interpolated), or only pick a level? */
export function acceptsValue(s: RescaleScenario, id: string): 'exact' | 'interpolated' | 'levels_only' {
  if (isMultiplicative(s, id)) return 'exact';
  if (s.grid?.params.includes(id)) return 'interpolated';
  return 'levels_only';
}

/** The user's choices that apply to this scenario, as values, leaving out anything at mid. */
export function resolveChanges(
  s: RescaleScenario,
  register: Record<string, RegisterValues>,
  settings: Record<string, Choice>,
): Change[] {
  const out: Change[] = [];
  for (const id of relevantIds(s)) {
    const choice = settings[id];
    const entry = register[id];
    if (!choice || !entry) continue;
    const value: ParamValue = 'level' in choice ? entry[choice.level] : choice.value;
    if (same(value, entry.mid)) continue;
    let level: Level | null = 'level' in choice ? choice.level : null;
    if (level === null) level = LEVEL_ORDER.find((lv) => same(entry[lv], value)) ?? null;
    out.push({ id, value, level });
  }
  return out.sort((a, b) => a.id.localeCompare(b.id));
}

/** Route 1: the exact multiplicative rescale, county by county. Null when it cannot apply. */
export function rescaleMultiplicative(c: Components, changes: Array<{ id: string; value: number }>): number | null {
  for (const ch of changes) {
    if (!(ch.id in c.linear_in) || typeof ch.value !== 'number') return null;
    if (c.linear_in[ch.id] === 0) return null;
  }
  let total = 0;
  for (const county of c.by_county) {
    let term = county.increment_mid_permits;
    for (const ch of changes) {
      const scoped = c.linear_counties?.[ch.id];
      if (scoped === undefined || scoped.includes(county.fips)) term *= ch.value / c.linear_in[ch.id];
    }
    total += term;
  }
  return total;
}

/** The product of new/old for multiplicative ids that multiply every county; null if any is county-scoped. */
export function uniformRatio(c: Components, changes: Array<{ id: string; value: number }>): number | null {
  let r = 1;
  for (const ch of changes) {
    if (!(ch.id in c.linear_in) || c.linear_counties?.[ch.id] !== undefined) return null;
    if (c.linear_in[ch.id] === 0) return null;
    r *= ch.value / c.linear_in[ch.id];
  }
  return r;
}

/**
 * Route 2: a grid value at the chosen values of some grid ids (others at mid). Exact at the
 * levels, linear interpolation between adjacent levels, null outside the low-high range.
 */
export function gridValue(
  grid: Grid,
  register: Record<string, RegisterValues>,
  values: Record<string, number>,
): { value: number; exact: boolean } | null {
  type Pick = Array<{ level: Level; weight: number }>;
  const picks: Pick[] = [];
  let exact = true;
  for (const id of grid.params) {
    const entry = register[id];
    if (!(id in values)) {
      picks.push([{ level: 'mid', weight: 1 }]);
      continue;
    }
    const v = values[id];
    const pts = LEVEL_ORDER.map((lv) => ({ level: lv, x: entry[lv] as number })).sort((a, b) => a.x - b.x);
    const hit = pts.find((p) => close(p.x, v));
    if (hit) {
      picks.push([{ level: hit.level, weight: 1 }]);
      continue;
    }
    let found: Pick | null = null;
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i];
      const b = pts[i + 1];
      if (a.x < v && v < b.x) {
        const t = (v - a.x) / (b.x - a.x);
        found = [
          { level: a.level, weight: 1 - t },
          { level: b.level, weight: t },
        ];
        break;
      }
    }
    if (!found) return null;
    exact = false;
    picks.push(found);
  }
  let total = 0;
  const walk = (i: number, key: string[], w: number) => {
    if (i === grid.params.length) {
      const cell = grid.cells[key.join('|')];
      if (cell === undefined) throw new Error(`grid cell missing: ${key.join('|')}`);
      total += w * cell;
      return;
    }
    for (const p of picks[i]) walk(i + 1, [...key, `${grid.params[i]}=${p.level}`], w * p.weight);
  };
  walk(0, [], 1);
  return { value: total, exact };
}

const REASONS = {
  unchanged: 'The register default: no assumption changed.',
  multiplicative:
    'Exact: these assumptions multiply the result, so the page rescales the engine’s own numbers with the engine’s arithmetic.',
  gridExact: 'Exact: the engine computed this combination of assumptions in advance.',
  gridInterp:
    'Interpolated between results the engine computed at the low, middle and high values; the command line gives the exact value.',
  tornado: 'Exact: the engine computed this one-at-a-time change in advance (the tornado bar).',
  caseScaled: 'Exact: the selected case rescaled by assumptions that multiply the result.',
  caseNa:
    'Not computed in the browser: a case combines here only with assumptions that multiply the result. The command line runs any assumption at the register default.',
  na: 'Not computed in the browser: this combination of assumptions needs the engine. The command line gives the exact value.',
  outside: 'Not computed in the browser: the value is outside the low-to-high range the engine precomputed.',
};

/**
 * The middle increment (permits) for one scenario after the user's assumption changes, under the
 * selected case. `caseKey` is a key of the scenario's `cases` block ("register_default" is the
 * headline).
 */
export function adjust(
  s: RescaleScenario,
  register: Record<string, RegisterValues>,
  settings: Record<string, Choice>,
  caseKey = 'register_default',
): Adjusted {
  const changes = resolveChanges(s, register, settings);
  const c = s.components;
  const base = caseKey === 'register_default' ? c.increment_mid_permits : s.cases[caseKey]?.estimate_permits.mid;
  if (base === undefined) {
    return { value: null, exactness: 'not_available', route: 'none', changes, reason: `No case "${caseKey}".` };
  }
  if (changes.length === 0) {
    return { value: base, exactness: 'unchanged', route: caseKey === 'register_default' ? 'none' : 'case', changes, reason: REASONS.unchanged };
  }
  const linear = changes.filter((ch) => isMultiplicative(s, ch.id) && typeof ch.value === 'number') as Array<{ id: string; value: number }>;
  const other = changes.filter((ch) => !isMultiplicative(s, ch.id));

  if (caseKey !== 'register_default') {
    const r = other.length === 0 ? uniformRatio(c, linear) : null;
    if (r === null) return { value: null, exactness: 'not_available', route: 'case', changes, reason: REASONS.caseNa };
    return { value: base * r, exactness: 'exact', route: 'case', changes, reason: REASONS.caseScaled };
  }

  // 1. only multiplicative ids
  if (other.length === 0) {
    const v = rescaleMultiplicative(c, linear);
    if (v === null) return { value: null, exactness: 'not_available', route: 'multiplicative', changes, reason: REASONS.na };
    return { value: v, exactness: 'exact', route: 'multiplicative', changes, reason: REASONS.multiplicative };
  }

  // 2. the grid covers every non-multiplicative change
  const grid = s.grid;
  if (grid && other.every((ch) => grid.params.includes(ch.id) && typeof ch.value === 'number')) {
    const r = uniformRatio(c, linear);
    if (r === null) return { value: null, exactness: 'not_available', route: 'grid', changes, reason: REASONS.na };
    const g = gridValue(grid, register, Object.fromEntries(other.map((ch) => [ch.id, ch.value as number])));
    if (g === null) return { value: null, exactness: 'not_available', route: 'grid', changes, reason: REASONS.outside };
    return {
      value: g.value * r,
      exactness: g.exact ? 'exact' : 'interpolated',
      route: 'grid',
      changes,
      reason: g.exact ? REASONS.gridExact : REASONS.gridInterp,
    };
  }

  // 3. one other id at its low or high end: the tornado bar
  if (other.length === 1 && (other[0].level === 'low' || other[0].level === 'high')) {
    const bar = s.tornado.find((b) => b.id === other[0].id);
    const r = uniformRatio(c, linear);
    if (bar && r !== null) {
      const v = (other[0].level === 'low' ? bar.at_low : bar.at_high) * r;
      return { value: v, exactness: 'exact', route: 'tornado', changes, reason: REASONS.tornado };
    }
  }
  return { value: null, exactness: 'not_available', route: 'none', changes, reason: REASONS.na };
}

/** The command that computes any setting exactly with the engine (decision 25). */
export function cliCommand(state: string, settings: Record<string, Choice>): string {
  const parts = Object.entries(settings)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, ch]) => ('level' in ch ? `--level ${id}=${ch.level}` : `--set ${id}=${ch.value}`));
  return ['uv run hre run --state', state, ...parts].join(' ');
}
