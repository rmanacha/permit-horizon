// Plain SVG bar charts (no chart library). Colors and type come from tokens.css through class
// names. Each chart has one series (increments in permits), so no legend: the title names it.
// Marks follow the dataviz rules: bars at most 24 units thick with a 4-unit rounded data end and
// a square baseline, 2-unit range lines with round caps, a solid hairline baseline, the value as
// text at the end of every bar, a hover readout over a hit area larger than the mark, and a
// table view beside every chart (Figure.tsx) for keyboard and screen-reader readers.
import { useState } from 'react';
import { fmtCount } from '../lib/format.ts';

const W = 760;
const R = 4; // rounded data end

/** A horizontal bar from x0 to x1 (x1 > x0), rounded at the x1 end only. */
function hbar(x0: number, x1: number, cy: number, h: number): string {
  const w = Math.max(0, x1 - x0);
  const r = Math.min(R, w, h / 2);
  const top = cy - h / 2;
  return `M${x0},${top} H${x0 + w - r} Q${x0 + w},${top} ${x0 + w},${top + r} V${top + h - r} Q${x0 + w},${top + h} ${x0 + w - r},${top + h} H${x0} Z`;
}

/** A floating bar rounded at both ends (tornado: neither end is a baseline). */
function hspan(x0: number, x1: number, cy: number, h: number): string {
  const w = Math.max(2, x1 - x0);
  const r = Math.min(R, w / 2, h / 2);
  const top = cy - h / 2;
  return `M${x0 + r},${top} H${x0 + w - r} Q${x0 + w},${top} ${x0 + w},${top + r} V${top + h - r} Q${x0 + w},${top + h} ${x0 + w - r},${top + h} H${x0 + r} Q${x0},${top + h} ${x0},${top + h - r} V${top + r} Q${x0},${top} ${x0 + r},${top} Z`;
}

/** A vertical column from the baseline up to y, rounded at the top only. */
function vbar(cx: number, w: number, y: number, base: number): string {
  const h = Math.max(0, base - y);
  const r = Math.min(R, h, w / 2);
  const x0 = cx - w / 2;
  return `M${x0},${base} V${y + r} Q${x0},${y} ${x0 + r},${y} H${x0 + w - r} Q${x0 + w},${y} ${x0 + w},${y + r} V${base} Z`;
}

function Tooltip({ x, y, text }: { x: number; y: number; text: string }) {
  const w = Math.min(W - 8, 16 + text.length * 7);
  const left = Math.max(4, Math.min(W - w - 4, x - w / 2));
  return (
    <g className="chart-tooltip" pointerEvents="none">
      <rect x={left} y={y - 30} width={w} height={24} />
      <text x={left + 8} y={y - 14}>
        {text}
      </text>
    </g>
  );
}

export interface RangeRow {
  key: string;
  label: string;
  low: number;
  mid: number;
  high: number;
}

/** Horizontal bars to the middle value, with a line from low to high. */
export function RangeChart({ rows, unit, ariaLabel }: { rows: RangeRow[]; unit: string; ariaLabel: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const rowH = 36;
  const barH = 16;
  const top = 34;
  const labelW = 210;
  const valueW = 190;
  const x0 = labelW;
  const x1 = W - valueW;
  const max = Math.max(1, ...rows.map((r) => r.high));
  const x = (v: number) => x0 + (Math.max(0, v) / max) * (x1 - x0);
  const h = top + rows.length * rowH + 28;
  const hv = hover === null ? null : rows[hover];
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel} onMouseLeave={() => setHover(null)}>
      {rows.map((r, i) => {
        const cy = top + i * rowH + rowH / 2;
        return (
          <g key={r.key} className="chart-row" onMouseEnter={() => setHover(i)}>
            <rect className="chart-hit" x={0} y={cy - rowH / 2} width={W} height={rowH} />
            <text className="chart-label" x={labelW - 12} y={cy} textAnchor="end" dominantBaseline="middle">
              {r.label}
            </text>
            <path className="chart-bar" d={hbar(x0, x(r.mid), cy, barH)} />
            <line className="chart-range" x1={x(r.low)} x2={x(r.high)} y1={cy} y2={cy} />
            <line className="chart-range" x1={x(r.low)} x2={x(r.low)} y1={cy - 6} y2={cy + 6} />
            <line className="chart-range" x1={x(r.high)} x2={x(r.high)} y1={cy - 6} y2={cy + 6} />
            <text className="chart-value" x={x1 + 12} y={cy} dominantBaseline="middle">
              {fmtCount(r.mid)} ({fmtCount(r.low)} to {fmtCount(r.high)})
            </text>
          </g>
        );
      })}
      <line className="chart-base" x1={x0} x2={x0} y1={top - 4} y2={h - 24} />
      <line className="chart-axis" x1={x0} x2={x1} y1={h - 24} y2={h - 24} />
      <text className="chart-tick" x={x0} y={h - 8} textAnchor="start">
        0
      </text>
      <text className="chart-tick" x={x1} y={h - 8} textAnchor="end">
        {fmtCount(max)} {unit}
      </text>
      {hv && hover !== null && (
        <Tooltip
          x={x(hv.mid)}
          y={top + hover * rowH + 4}
          text={`${hv.label}: middle ${fmtCount(hv.mid)} ${unit}; low ${fmtCount(hv.low)}, high ${fmtCount(hv.high)}`}
        />
      )}
    </svg>
  );
}

export interface TornadoRow {
  key: string;
  label: string;
  atLow: number;
  atHigh: number;
  base: number;
  lowText?: string;
  highText?: string;
  note?: string;
}

/** One bar per assumption from its result at the low end to its result at the high end. */
export function TornadoChart({ rows, unit, ariaLabel }: { rows: TornadoRow[]; unit: string; ariaLabel: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const rowH = 42;
  const barH = 18;
  const top = 34;
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
  const hv = hover === null ? null : rows[hover];
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel} onMouseLeave={() => setHover(null)}>
      {rows.map((r, i) => {
        const cy = top + i * rowH + rowH / 2;
        const a = Math.min(r.atLow, r.atHigh);
        const b = Math.max(r.atLow, r.atHigh);
        return (
          <g key={r.key} className="chart-row" onMouseEnter={() => setHover(i)}>
            <rect className="chart-hit" x={0} y={cy - rowH / 2} width={W} height={rowH} />
            <text className="chart-label" x={labelW - 12} y={cy - (r.note ? 7 : 0)} textAnchor="end" dominantBaseline="middle">
              {r.label.length > MAX_LABEL ? `${r.label.slice(0, MAX_LABEL - 1).trimEnd()}…` : r.label}
            </text>
            {r.note && (
              <text className="chart-sublabel" x={labelW - 12} y={cy + 10} textAnchor="end" dominantBaseline="middle">
                {r.note}
              </text>
            )}
            <path className="chart-bar" d={hspan(x(a), x(b), cy, barH)} />
            <text className="chart-value" x={x1 + 12} y={cy} dominantBaseline="middle">
              {fmtCount(r.atLow)} to {fmtCount(r.atHigh)}
            </text>
          </g>
        );
      })}
      <line className="chart-base" x1={x(base)} x2={x(base)} y1={top - 4} y2={h - 26} />
      <text className="chart-tick" x={x(base)} y={h - 8} textAnchor="middle">
        middle {fmtCount(base)} {unit}
      </text>
      {hv && hover !== null && (
        <Tooltip
          x={(x(hv.atLow) + x(hv.atHigh)) / 2}
          y={top + hover * rowH + 4}
          text={`${fmtCount(hv.atLow)} ${unit} at ${hv.lowText ?? 'the low end'}; ${fmtCount(hv.atHigh)} at ${hv.highText ?? 'the high end'}`}
        />
      )}
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
  const [hover, setHover] = useState<number | null>(null);
  const h = 240;
  const top = 44;
  const bottom = 34;
  const left = 20;
  const colW = (W - left * 2) / Math.max(1, years.length);
  const barW = Math.min(24, colW * 0.4);
  const max = Math.max(1, ...high);
  const base = h - bottom;
  const y = (v: number) => top + (1 - Math.max(0, v) / max) * (base - top);
  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={ariaLabel} onMouseLeave={() => setHover(null)}>
      {years.map((yr, i) => {
        const cx = left + colW * i + colW / 2;
        return (
          <g key={yr} className="chart-row" onMouseEnter={() => setHover(i)}>
            <rect className="chart-hit" x={cx - colW / 2} y={top - 20} width={colW} height={base - top + 40} />
            <path className="chart-bar" d={vbar(cx, barW, y(mid[i]), base)} />
            <line className="chart-range" x1={cx} x2={cx} y1={y(low[i])} y2={y(high[i])} />
            <line className="chart-range" x1={cx - 6} x2={cx + 6} y1={y(high[i])} y2={y(high[i])} />
            <line className="chart-range" x1={cx - 6} x2={cx + 6} y1={y(low[i])} y2={y(low[i])} />
            <text className="chart-value" x={cx + barW / 2 + 8} y={y(mid[i]) + 4} textAnchor="start">
              {fmtCount(mid[i])}
            </text>
            <text className="chart-tick" x={cx} y={h - 12} textAnchor="middle">
              {yr}
            </text>
          </g>
        );
      })}
      <line className="chart-axis" x1={left} x2={W - left} y1={base} y2={base} />
      <text className="chart-tick" x={left} y={16}>
        {unit} per year (bars: middle; lines: low to high)
      </text>
      {hover !== null && (
        <Tooltip
          x={left + colW * hover + colW / 2}
          y={Math.max(36, y(high[hover]) - 4)}
          text={`${years[hover]}: middle ${fmtCount(mid[hover])} ${unit}; low ${fmtCount(low[hover])}, high ${fmtCount(high[hover])}`}
        />
      )}
    </svg>
  );
}
