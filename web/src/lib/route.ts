// The view lives in the URL hash, so a link restores it exactly (share links, step 5):
//   #/<page>?st=NH&sc=adu&case=50-1&set=builder_response_override:high,fee_cut_share:0.3&show=adu,fees
// `tour=N` opens the site tour at stop N (the tour keeps its place here, never in browser storage).
// Hash routing needs no server rewrite rules, so it works on GitHub Pages, Docker and http.server.
import type { Choice } from '../engine/rescale.ts';
import { LEVELS, SCENARIOS, type Level, type ScenarioName } from '../types/results.ts';

export const PAGES = ['explore', 'scenario', 'data', 'methods', 'validation', 'about', 'brief'] as const;
export type Page = (typeof PAGES)[number];

/** A user's choice for one register id: a named level or (for multiplicative ids) any number (the engine's type). */
export type { Choice };
export type Settings = Record<string, Choice>;

/** The user-case grid: share newly affected (percent) by delay (years), as the engine's cases block names them. */
export const SHARES = [25, 50, 100] as const;
export const DELAYS = [0, 1, 2] as const;

export type CaseSel =
  | { kind: 'register_default' }
  | { kind: 'no_change' }
  | { kind: 'after_horizon' }
  | { kind: 'eligible'; share: (typeof SHARES)[number]; delay: (typeof DELAYS)[number] };

export interface View {
  page: Page;
  state: string | null;
  scenario: ScenarioName;
  caseSel: CaseSel;
  settings: Settings;
  show: ScenarioName[];
  /** The open tour stop (1-based); 0 when the tour is closed. */
  tour: number;
}

export const DEFAULT_VIEW: View = {
  page: 'explore',
  state: null,
  scenario: 'adu',
  caseSel: { kind: 'register_default' },
  settings: {},
  show: [...SCENARIOS],
  tour: 0,
};

/** The key of a case in a scenario's `cases` block. */
export function caseKey(c: CaseSel): string {
  switch (c.kind) {
    case 'register_default':
      return 'register_default';
    case 'no_change':
      return 'no_change';
    case 'after_horizon':
      return 'after_horizon';
    case 'eligible':
      return `eligible_${c.share}_delay_${c.delay}`;
  }
}

/** The case as the `case=` query value; null for the register default (left out of the link). */
export function encodeCase(c: CaseSel): string | null {
  switch (c.kind) {
    case 'register_default':
      return null;
    case 'no_change':
      return 'none';
    case 'after_horizon':
      return 'after';
    case 'eligible':
      return `${c.share}-${c.delay}`;
  }
}

function decodeCase(s: string | null): CaseSel {
  if (!s) return { kind: 'register_default' };
  if (s === 'none') return { kind: 'no_change' };
  if (s === 'after') return { kind: 'after_horizon' };
  const m = /^(25|50|100)-([012])$/.exec(s);
  if (!m) return { kind: 'register_default' };
  return { kind: 'eligible', share: Number(m[1]) as 25 | 50 | 100, delay: Number(m[2]) as 0 | 1 | 2 };
}

function encodeSettings(s: Settings): string | null {
  const parts = Object.entries(s)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, c]) => `${id}:${'level' in c ? c.level : String(c.value)}`);
  return parts.length ? parts.join(',') : null;
}

function decodeSettings(s: string | null): Settings {
  const out: Settings = {};
  if (!s) return out;
  for (const part of s.split(',')) {
    const [id, raw] = part.split(':');
    if (!id || raw === undefined || !/^[a-z0-9_]+$/.test(id)) continue;
    if ((LEVELS as readonly string[]).includes(raw)) out[id] = { level: raw as Level };
    else if (raw !== '' && Number.isFinite(Number(raw))) out[id] = { value: Number(raw) };
  }
  return out;
}

export function parseHash(hash: string): View {
  const h = hash.replace(/^#\/?/, '');
  const [path, query = ''] = h.split('?');
  const q = new URLSearchParams(query);
  const page = (PAGES as readonly string[]).includes(path) ? (path as Page) : 'explore';
  const st = q.get('st');
  const sc = q.get('sc');
  const show = (q.get('show') ?? '')
    .split(',')
    .filter((x): x is ScenarioName => (SCENARIOS as readonly string[]).includes(x));
  return {
    page,
    state: st && /^[A-Z]{2}$/.test(st) ? st : null,
    scenario: sc && (SCENARIOS as readonly string[]).includes(sc) ? (sc as ScenarioName) : 'adu',
    caseSel: decodeCase(q.get('case')),
    settings: decodeSettings(q.get('set')),
    show: show.length ? show : [...SCENARIOS],
    tour: /^[1-9]$/.test(q.get('tour') ?? '') ? Number(q.get('tour')) : 0,
  };
}

export function buildHash(v: View): string {
  const q = new URLSearchParams();
  if (v.state) q.set('st', v.state);
  if (v.page === 'scenario' || v.scenario !== 'adu') q.set('sc', v.scenario);
  const c = encodeCase(v.caseSel);
  if (c) q.set('case', c);
  const s = encodeSettings(v.settings);
  if (s) q.set('set', s);
  if (v.show.length && v.show.length < SCENARIOS.length) q.set('show', v.show.join(','));
  if (v.tour) q.set('tour', String(v.tour));
  const qs = q.toString().replace(/%3A/g, ':').replace(/%2C/g, ',');
  return `#/${v.page}${qs ? `?${qs}` : ''}`;
}
