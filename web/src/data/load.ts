// Loads the committed bundle from public/results/ (never bundled into the JavaScript: each state
// file is fetched only when that state is opened). Results are cached for the session.
import { useEffect, useState } from 'react';
import type { BundleIndex, BundleMeta, Registers, Results } from '../types/results.ts';

const cache = new Map<string, Promise<unknown>>();

export function bundleUrl(file: string): string {
  return `${import.meta.env.BASE_URL}results/${file}`;
}

export function loadJSON<T>(file: string): Promise<T> {
  let p = cache.get(file) as Promise<T> | undefined;
  if (!p) {
    p = fetch(bundleUrl(file)).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${file} (HTTP ${r.status}).`);
      return r.json() as Promise<T>;
    });
    p.catch(() => cache.delete(file));
    cache.set(file, p);
  }
  return p;
}

export const loadIndex = () => loadJSON<BundleIndex>('index.json');
export const loadRegisters = () => loadJSON<Registers>('registers.json');
export const loadMeta = () => loadJSON<BundleMeta>('meta.json');
export const loadState = (st: string) => loadJSON<Results>(`${st}.json`);

export interface Async<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/** Runs a loader when its key changes; key null means "nothing to load". */
export function useAsync<T>(key: string | null, loader: () => Promise<T>): Async<T> {
  const [state, setState] = useState<Async<T>>({ data: null, error: null, loading: key !== null });
  useEffect(() => {
    if (key === null) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    let live = true;
    setState((s) => ({ data: s.data, error: null, loading: true }));
    loader().then(
      (data) => live && setState({ data, error: null, loading: false }),
      (e: unknown) => live && setState({ data: null, error: e instanceof Error ? e.message : String(e), loading: false }),
    );
    return () => {
      live = false;
    };
  }, [key]);
  return state;
}
