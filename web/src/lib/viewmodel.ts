// What the pages show for one state, derived from its results file and the user's view: the
// selected case's increment and total, the user's assumption changes, and the compare table's
// ranking. Pure functions (no React), so the rules are tested in viewmodel.test.ts.
import { adjust, type Adjusted, type RegisterValues } from '../engine/rescale.ts';
import { caseKey, type CaseSel, type Settings } from './route.ts';
import { type LMH, type Outcome, type Results, type ScenarioName, type TornadoBar } from '../types/results.ts';

export interface ScenarioView {
  name: ScenarioName;
  label: string;
  formula: string;
  benchmark: LMH & { outcome: Outcome; interpretation: string };
  caseKey: string;
  caseLabel: string;
  status: string;
  share: number;
  delay: number;
  /** The increment in permits under the selected case (the register default unless a case is chosen). */
  increment: LMH;
  total: LMH;
  /** Increment x completed homes per permit (shown beside ADU permits). */
  homes: LMH;
  adjusted: Adjusted;
  /** Middle increment / middle baseline: a secondary label only (permits first). */
  shareOfBaseline: number;
  lawNote: string;
  humanReview: string | null;
  lawSource: string;
  zeroNote: string | null;
  mover: TornadoBar | null;
}

function scale(x: LMH, f: number): LMH {
  return { low: x.low * f, mid: x.mid * f, high: x.high * f };
}

export function humanReviewText(h: unknown): string | null {
  if (h === null || h === undefined || h === false) return null;
  if (typeof h === 'string') return h;
  if (typeof h === 'object' && h !== null && 'status' in h) {
    const o = h as { status?: string; by?: string | null; date?: string | null };
    if (o.status === 'done' || o.status === 'complete' || o.status === 'reviewed') {
      return `reviewed${o.by ? ` by ${o.by}` : ''}${o.date ? ` on ${o.date}` : ''}`;
    }
    return `human review ${o.status ?? 'pending'}`;
  }
  return String(h);
}

export function scenarioView(
  r: Results,
  name: ScenarioName,
  register: Record<string, RegisterValues>,
  settings: Settings,
  caseSel: CaseSel,
): ScenarioView {
  const s = r.scenarios[name];
  const key = caseKey(caseSel);
  const cs = s.cases[key] ?? s.cases.register_default;
  const increment = key === 'register_default' ? s.increment.estimate : cs.estimate_permits;
  const base = r.baseline.state;
  const inc = s.increment.estimate;
  // homes per permit is one factor per scenario; read it at mid first (the most digits), then high, low
  const homesRatio = (['mid', 'high', 'low'] as const).map((lv) => (inc[lv] ? s.increment.completed_homes_equivalent[lv] / inc[lv] : null)).find(
    (x): x is number => x !== null,
  ) ?? 1;
  const zero = [...(s.factors.notes ?? []), ...s.notes].find((n) => /^No block group within/.test(n)) ?? null;
  return {
    name,
    label: s.label,
    formula: s.formula,
    benchmark: s.benchmark,
    caseKey: key,
    caseLabel: cs.label,
    status: key === 'register_default' ? s.increment.status : cs.status,
    share: key === 'register_default' ? s.increment.newly_affected_share : cs.newly_affected_share,
    delay: cs.delay_years,
    increment,
    total: { low: base.low + increment.low, mid: base.mid + increment.mid, high: base.high + increment.high },
    homes: scale(increment, homesRatio),
    adjusted: adjust(s, register, settings, key),
    shareOfBaseline: base.mid ? increment.mid / base.mid : 0,
    lawNote: s.increment.current_law.note,
    humanReview: humanReviewText(s.increment.current_law.human_review),
    lawSource: s.increment.current_law.source,
    zeroNote: zero,
    mover: s.tornado[0] ?? null,
  };
}

export interface Flip {
  above: ScenarioName;
  below: ScenarioName;
  level: 'low' | 'high';
}

/**
 * Rank scenarios by their middle increment (all in permits, so comparable), largest first, and
 * list every pair whose order reverses at the low or high end (ties are not reversals).
 */
export function rankIncrements(rows: Array<{ name: ScenarioName; increment: LMH }>): {
  order: ScenarioName[];
  flips: Flip[];
} {
  const order = [...rows].sort((a, b) => b.increment.mid - a.increment.mid || a.name.localeCompare(b.name));
  const flips: Flip[] = [];
  for (let i = 0; i < order.length; i++) {
    for (let j = i + 1; j < order.length; j++) {
      const a = order[i];
      const b = order[j];
      if (!(a.increment.mid > b.increment.mid)) continue;
      for (const level of ['low', 'high'] as const) {
        if (a.increment[level] < b.increment[level]) flips.push({ above: a.name, below: b.name, level });
      }
    }
  }
  return { order: order.map((r) => r.name), flips };
}

export function registerLookup(entries: RegisterValues[]): Record<string, RegisterValues> {
  return Object.fromEntries(entries.map((e) => [e.id, e]));
}
