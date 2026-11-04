// Number formatting and outcome labels. Every result on the page is shown with its outcome
// label (decision 30): use outcomeLabel() beside every number from the bundle.
import type { Outcome } from '../types/results.ts';

const whole = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

/** A count of permits or homes: whole numbers with separators; "under 1" for a small non-zero. */
export function fmtCount(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return 'n/a';
  if (n !== 0 && Math.abs(n) < 0.5) return n > 0 ? 'under 1' : 'about −0';
  return whole.format(Math.round(n));
}

/** A share (0.137 -> "13.7%"): one decimal below 10%, none above. */
export function fmtShare(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return 'n/a';
  const pct = x * 100;
  if (pct !== 0 && Math.abs(pct) < 0.05) return pct > 0 ? 'under 0.1%' : 'about −0%';
  const digits = Math.abs(pct) < 10 ? 1 : 0;
  return `${pct.toFixed(digits)}%`;
}

/** A plain number for parameters (a ratio, a rate, dollars handled by the register's own text). */
export function fmtNumber(n: number, digits = 4): string {
  if (Number.isInteger(n)) return whole.format(n);
  return new Intl.NumberFormat('en-US', { maximumSignificantDigits: digits }).format(n);
}

export const OUTCOME_LABELS: Record<Outcome, { short: string; glossary: string }> = {
  permits: { short: 'permits', glossary: 'outcome-permits' },
  net_permits: { short: 'net permits', glossary: 'outcome-net-permits' },
  completed_homes: { short: 'completed homes', glossary: 'outcome-completed-homes' },
  stock_change: { short: 'homes added to the stock', glossary: 'outcome-stock-change' },
  cost_response_proxy: { short: 'cost-response permits', glossary: 'outcome-cost-response-proxy' },
};

export function outcomeLabel(o: Outcome | string): string {
  return (OUTCOME_LABELS as Record<string, { short: string }>)[o]?.short ?? o;
}

export const STATUS_LABELS: Record<string, string> = {
  register_default: 'Register default',
  user_case: 'User case',
  assumed_zero: 'Assumed zero',
};

export function statusLabel(s: string): string {
  return STATUS_LABELS[s] ?? s;
}

/** "a, b and c" */
export function joinWords(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}
