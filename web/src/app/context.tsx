// Two contexts: the view (page, state, case, assumption choices; mirrored in the URL hash) and the
// shared bundle files every page needs (index, registers, meta), loaded once.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { loadIndex, loadMeta, loadRegisters, useAsync } from '../data/load.ts';
import { buildHash, parseHash, type View } from '../lib/route.ts';
import type { BundleIndex, BundleMeta, Registers } from '../types/results.ts';

interface ViewApi {
  view: View;
  /** Change the view. Page changes add a history entry; option changes replace the current one. */
  update: (patch: Partial<View>, opts?: { push?: boolean }) => void;
  href: (patch: Partial<View>) => string;
}

const ViewContext = createContext<ViewApi | null>(null);

export function ViewProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState<View>(() => parseHash(window.location.hash));
  useEffect(() => {
    const onHash = () => setView(parseHash(window.location.hash));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const update = useCallback(
    (patch: Partial<View>, opts?: { push?: boolean }) => {
      const next = { ...view, ...patch };
      const hash = buildHash(next);
      const push = opts?.push ?? (patch.page !== undefined && patch.page !== view.page);
      if (push) window.history.pushState(null, '', hash);
      else window.history.replaceState(null, '', hash);
      setView(next);
      if (push) window.scrollTo(0, 0);
    },
    [view],
  );
  const href = useCallback((patch: Partial<View>) => buildHash({ ...view, ...patch }), [view]);
  const api = useMemo(() => ({ view, update, href }), [view, update, href]);
  return <ViewContext.Provider value={api}>{children}</ViewContext.Provider>;
}

export function useView(): ViewApi {
  const v = useContext(ViewContext);
  if (!v) throw new Error('useView outside ViewProvider');
  return v;
}

export interface Shared {
  index: BundleIndex;
  registers: Registers;
  meta: BundleMeta;
}

const SharedContext = createContext<Shared | null>(null);

export function SharedProvider({ children }: { children: ReactNode }) {
  const index = useAsync('index', loadIndex);
  const registers = useAsync('registers', loadRegisters);
  const meta = useAsync('meta', loadMeta);
  const error = index.error ?? registers.error ?? meta.error;
  if (error) {
    return (
      <p className="error-message" role="alert">
        The results bundle could not be loaded: {error}
      </p>
    );
  }
  if (!index.data || !registers.data || !meta.data) {
    return <p className="status-message">Loading the results bundle…</p>;
  }
  return (
    <SharedContext.Provider value={{ index: index.data, registers: registers.data, meta: meta.data }}>
      {children}
    </SharedContext.Provider>
  );
}

export function useShared(): Shared {
  const s = useContext(SharedContext);
  if (!s) throw new Error('useShared outside SharedProvider');
  return s;
}
