// Community Solutions design system: StatCallout (big-number block). className replaces style.
import type { ReactNode } from 'react';

export interface StatCalloutProps {
  value: ReactNode;
  label: ReactNode;
  source?: ReactNode;
  tone?: 'sky' | 'navy' | 'sand' | 'white' | 'lime';
  align?: 'left' | 'center';
  className?: string;
}

export function StatCallout({ value, label, source, tone = 'sky', align = 'left', className }: StatCalloutProps) {
  return (
    <div className={['ds-stat', `ds-stat--${tone}`, `ds-stat--${align}`, className ?? ''].filter(Boolean).join(' ')}>
      <div className="ds-stat__value">{value}</div>
      <div className="ds-stat__label">{label}</div>
      {source && <div className="ds-stat__source">{source}</div>}
    </div>
  );
}
