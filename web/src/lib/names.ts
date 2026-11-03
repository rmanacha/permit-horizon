import type { ScenarioName } from '../types/results.ts';

/** Short names for chart rows and table headers (the full label comes from the results file). */
export const SHORT: Record<ScenarioName, string> = {
  adu: 'ADUs by right',
  missing_middle: 'Missing middle',
  tod: 'Transit-oriented density',
  parking: 'No parking minimums',
  fees: 'Fees cut in half',
};

export const SCENARIO_TERM: Record<ScenarioName, string> = {
  adu: 'adu',
  missing_middle: 'missing-middle',
  tod: 'tod',
  parking: 'parking-minimum',
  fees: 'fees',
};
