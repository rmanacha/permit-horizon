// The result after the user's assumption changes, with how it was computed.
import type { Adjusted } from '../engine/rescale.ts';
import { cliCommand } from '../engine/rescale.ts';
import type { Settings } from '../lib/route.ts';
import { ExactBadge } from './Badge.tsx';
import { Num } from './Num.tsx';

export function AdjustedResult({ a, state, settings, compact = false }: { a: Adjusted; state: string; settings: Settings; compact?: boolean }) {
  if (a.exactness === 'unchanged') return null;
  return (
    <div className={`adjusted adjusted-${a.exactness}`}>
      <p>
        <strong>With your assumptions:</strong>{' '}
        {a.value !== null ? <Num value={a.value} outcome="permits" /> : <span>not computed here</span>} (middle) <ExactBadge exactness={a.exactness} />
      </p>
      {!compact && <p className="small">{a.reason}</p>}
      {a.exactness !== 'exact' && (
        <p className="small">
          Exact value on the command line: <code>{cliCommand(state, settings)}</code>
        </p>
      )}
    </div>
  );
}
