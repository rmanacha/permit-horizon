// Plain SVG bar charts (decision 79: no chart library). Colors and type come from tokens.css
// through class names; every bar carries its number as text.
import { fmtCount } from '../lib/format.ts';

const W = 760;

export interface RangeRow {
  key: string;
  label: string;
  low: number;
  mid: number;
  high: number;
}

/** Horizontal bars to the middle value, with a line from low to high. */
export function RangeChart({ rows, unit, ariaLabel }: { rows: RangeRow[]; unit: string; ariaLabel: string }) {
  const rowH = 34;
  const top = 8;
  const labelW = 210;
  const valueW = 190;
  const x0 = labelW;
  const x1 = W - valueW;
  const max = Math.max(1, ...rows.map((r) => r.high));
  const x = (v: number) => x0 + (Math.max(0, v) / max) * (x1 - x0);
  const h = top + rows.length * rowH + 28;
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel}>
      {rows.map((r, i) => {
        const y = top + i * rowH;
        const cy = y + rowH / 2;
        return (
          <g key={r.key}>
            <text className="chart-label" x={labelW - 10} y={cy} textAnchor="end" dominantBaseline="middle">
              {r.label}
            </text>
            <rect className="chart-bar" x={x0} y={cy - 8} width={Math.max(0, x(r.mid) - x0)} height={16} />
            <line className="chart-range" x1={x(r.low)} x2={x(r.high)} y1={cy} y2={cy} />
            <line className="chart-range" x1={x(r.low)} x2={x(r.low)} y1={cy - 6} y2={cy + 6} />
            <line className="chart-range" x1={x(r.high)} x2={x(r.high)} y1={cy - 6} y2={cy + 6} />
            <text className="chart-value" x={x1 + 10} y={cy} dominantBaseline="middle">
              {fmtCount(r.mid)} ({fmtCount(r.low)} to {fmtCount(r.high)})
            </text>
          </g>
        );
      })}
      <line className="chart-axis" x1={x0} x2={x1} y1={h - 24} y2={h - 24} />
      <text className="chart-tick" x={x0} y={h - 8} textAnchor="start">
        0
      </text>
      <text className="chart-tick" x={x1} y={h - 8} textAnchor="end">
        {fmtCount(max)} {unit}
      </text>
    </svg>
  );
}

export interface TornadoRow {
  key: string;
  label: string;
  atLow: number;
  atHigh: number;
  base: number;
  note?: string;
}

/** One bar per assumption from its result at the low end to its result at the high end. */
export function TornadoChart({ rows, unit, ariaLabel }: { rows: TornadoRow[]; unit: string; ariaLabel: string }) {
  const rowH = 40;
  const top = 10;
  const labelW = 330;
  const valueW = 130;
  const MAX_LABEL = 38; // characters that fit the label column at the chart's type size
  const x0 = labelW;
  const x1 = W - valueW;
  const values = rows.flatMap((r) => [r.atLow, r.atHigh, r.base]);
  const lo = Math.min(0, ...values);
  const hi = Math.max(1, ...values);
  const x = (v: number) => x0 + ((v - lo) / (hi - lo)) * (x1 - x0);
  const h = top + rows.length * rowH + 30;
  const base = rows[0]?.base ?? 0;
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel}>
      {rows.map((r, i) => {
        const y = top + i * rowH;
        const cy = y + rowH / 2;
        const a = Math.min(r.atLow, r.atHigh);
        const b = Math.max(r.atLow, r.atHigh);
        return (
          <g key={r.key}>
            <text className="chart-label" x={labelW - 10} y={cy - 6} textAnchor="end" dominantBaseline="middle">
              {r.label.length > MAX_LABEL ? `${r.label.slice(0, MAX_LABEL - 1).trimEnd()}…` : r.label}
              <title>{r.label}</title>
            </text>
            {r.note && (
              <text className="chart-sublabel" x={labelW - 10} y={cy + 9} textAnchor="end" dominantBaseline="middle">
                {r.note}
              </text>
            )}
            <rect className="chart-bar-alt" x={x(a)} y={cy - 9} width={Math.max(1, x(b) - x(a))} height={18} />
            <text className="chart-value" x={x1 + 10} y={cy} dominantBaseline="middle">
              {fmtCount(r.atLow)} to {fmtCount(r.atHigh)}
            </text>
          </g>
        );
      })}
      <line className="chart-base" x1={x(base)} x2={x(base)} y1={top - 4} y2={h - 26} />
      <text className="chart-tick" x={x(base)} y={h - 8} textAnchor="middle">
        middle {fmtCount(base)} {unit}
      </text>
    </svg>
  );
}

/** Vertical bars by year (middle), with a line from low to high. */
export function YearChart({ years, low, mid, high, unit, ariaLabel }: {
  years: number[];
  low: number[];
  mid: number[];
  high: number[];
  unit: string;
  ariaLabel: string;
}) {
  const h = 230;
  const top = 26;
  const bottom = 34;
  const left = 20;
  const colW = (W - left * 2) / Math.max(1, years.length);
  const max = Math.max(1, ...high);
  const y = (v: number) => top + (1 - Math.max(0, v) / max) * (h - top - bottom);
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel}>
      {years.map((yr, i) => {
        const cx = left + colW * i + colW / 2;
        return (
          <g key={yr}>
            <rect className="chart-bar" x={cx - colW * 0.3} y={y(mid[i])} width={colW * 0.6} height={Math.max(0, h - bottom - y(mid[i]))} />
            <line className="chart-range" x1={cx} x2={cx} y1={y(low[i])} y2={y(high[i])} />
            <line className="chart-range" x1={cx - 6} x2={cx + 6} y1={y(high[i])} y2={y(high[i])} />
            <line className="chart-range" x1={cx - 6} x2={cx + 6} y1={y(low[i])} y2={y(low[i])} />
            <text className="chart-value" x={cx} y={Math.max(12, y(high[i]) - 6)} textAnchor="middle">
              {fmtCount(mid[i])}
            </text>
            <text className="chart-tick" x={cx} y={h - 12} textAnchor="middle">
              {yr}
            </text>
          </g>
        );
      })}
      <line className="chart-axis" x1={left} x2={W - left} y1={h - bottom} y2={h - bottom} />
      <text className="chart-tick" x={left} y={14}>
        {unit} per year (bars: middle; lines: low to high)
      </text>
    </svg>
  );
}
