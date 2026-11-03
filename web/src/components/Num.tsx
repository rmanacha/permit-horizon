// Every number from the bundle is shown with its outcome label (decision 30).
import { fmtCount, OUTCOME_LABELS, outcomeLabel } from '../lib/format.ts';
import type { LMH, Outcome } from '../types/results.ts';
import { Term } from './Term.tsx';

export function Label({ outcome, linked = true }: { outcome: Outcome | string; linked?: boolean }) {
  const meta = (OUTCOME_LABELS as Record<string, { glossary: string }>)[outcome];
  const text = outcomeLabel(outcome);
  if (!linked || !meta) return <span className="num-label">{text}</span>;
  return (
    <span className="num-label">
      <Term term={meta.glossary}>{text}</Term>
    </span>
  );
}

export function Num({ value, outcome, linked = true }: { value: number; outcome: Outcome | string; linked?: boolean }) {
  return (
    <span className="num">
      <span className="num-value">{fmtCount(value)}</span> <Label outcome={outcome} linked={linked} />
    </span>
  );
}

/** "range 41 to 1,556 permits" for an assumption-set range. */
export function RangeText({ v, outcome }: { v: LMH; outcome: Outcome | string }) {
  return (
    <span className="range-text">
      range {fmtCount(v.low)} to {fmtCount(v.high)} {outcomeLabel(outcome)}
    </span>
  );
}
