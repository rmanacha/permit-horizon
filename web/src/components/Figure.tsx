// Every chart has a table view (accessibility: color is never the only cue, and a screen reader
// or a reader who wants the numbers gets the table).
import { useState, type ReactNode } from 'react';

export function ChartTable({ title, chart, table, note }: { title: string; chart: ReactNode; table: ReactNode; note?: ReactNode }) {
  const [asTable, setAsTable] = useState(false);
  return (
    <figure className="chart-figure">
      <figcaption className="chart-caption">
        <span className="chart-title">{title}</span>
        <button type="button" className="link-button no-print" aria-pressed={asTable} onClick={() => setAsTable((t) => !t)}>
          {asTable ? 'Show as chart' : 'Show as table'}
        </button>
      </figcaption>
      {asTable ? table : chart}
      {note && <div className="chart-note">{note}</div>}
    </figure>
  );
}
