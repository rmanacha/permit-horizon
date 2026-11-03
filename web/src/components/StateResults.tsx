// Loads one state's results file (lazily, only when that state is opened) and hands it on.
import type { ReactNode } from 'react';
import { loadState, useAsync } from '../data/load.ts';
import type { Results } from '../types/results.ts';
import { useShared } from '../app/context.tsx';

export function StateResults({ state, children }: { state: string; children: (r: Results) => ReactNode }) {
  const { index } = useShared();
  const known = index.states.some((s) => s.state === state);
  const res = useAsync(known ? state : null, () => loadState(state));
  if (!known) return <p className="error-message">There is no results file for “{state}”. Choose a state above.</p>;
  if (res.error) return <p className="error-message" role="alert">{res.error}</p>;
  if (!res.data || res.data.meta.state !== state) return <p className="status-message">Loading {state}…</p>;
  return <>{children(res.data)}</>;
}

/** A page that needs a state shows a short prompt until one is chosen. */
export function NeedState({ what }: { what: string }) {
  return (
    <div className="note">
      <p>Choose a state at the top of the page to see {what}.</p>
    </div>
  );
}
