import type { BundleIndex, ScenarioName } from '../types/results.ts';

/** Short names for chart rows and table headers (the full label comes from the results file). */
export const SHORT: Record<ScenarioName, string> = {
  adu: 'ADUs by right',
  missing_middle: 'Missing middle',
  tod: 'Transit-oriented density',
  parking: 'No parking minimums',
  fees: 'Fees cut in half',
};

/** The state's display name from index.json, or its code when the index has no row for it. */
export function stateName(index: BundleIndex, st: string): string {
  return index.states.find((s) => s.state === st)?.name ?? st;
}

export const SCENARIO_TERM: Record<ScenarioName, string> = {
  adu: 'adu',
  missing_middle: 'missing-middle',
  tod: 'tod',
  parking: 'parking-minimum',
  fees: 'fees',
};
