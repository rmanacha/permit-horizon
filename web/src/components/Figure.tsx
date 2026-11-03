// Every chart has a table view (accessibility: color is never the only cue, and a screen reader
// or a reader who wants the numbers gets the table).
import { useState, type ReactNode } from 'react';
import { Button } from './ds/Button.tsx';

export function ChartTable({ title, chart, table, note }: { title: string; chart: ReactNode; table: ReactNode; note?: ReactNode }) {
  const [asTable, setAsTable] = useState(false);
  return (
    <figure className="chart-figure">
      <figcaption className="chart-caption">
        <span className="chart-title">{title}</span>
        <Button variant="ghost" size="sm" className="no-print" aria-pressed={asTable} onClick={() => setAsTable((t) => !t)}>
          {asTable ? 'Show as chart' : 'Show as table'}
        </Button>
      </figcaption>
      {asTable ? table : chart}
      {note && <div className="chart-note">{note}</div>}
    </figure>
  );
}
