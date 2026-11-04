// Types for the precomputed results bundle in public/results/ (the contract is
// docs/methods/results_schema.md; src/data/bundle.test.ts checks every committed file against
// the keys used here). The page reads these files and never computes a result from inputs.

export type Level = 'low' | 'mid' | 'high';
export const LEVELS: readonly Level[] = ['low', 'mid', 'high'];

export interface LMH {
  low: number;
  mid: number;
  high: number;
}

/** The unit a number is in. Numbers with different labels are never added or ranked together. */
export type Outcome = 'permits' | 'net_permits' | 'completed_homes' | 'stock_change' | 'cost_response_proxy';

export type ScenarioName = 'adu' | 'missing_middle' | 'tod' | 'parking' | 'fees';
export const SCENARIOS: readonly ScenarioName[] = ['adu', 'missing_middle', 'tod', 'parking', 'fees'];

export interface CountyRange extends LMH {
  fips: string;
  name: string;
}

export interface BandPeriod {
  origins: [number, number];
  runs: number;
  inside: number;
  above: number;
  below: number;
  share_inside: number;
}

export interface BandRule {
  name: string;
  low_ratio: number;
  high_ratio: number;
  reading: string;
  applied_to_counties: string;
  coverage_by_period: BandPeriod[];
  coverage_realtime: {
    origins: [number, number];
    runs: number;
    inside: number;
    share_inside: number;
    origins_under_5pct: number[];
  };
  reading_history: string;
  source: string;
  alternative: string;
}

export interface AlternativeBand {
  name?: string;
  available: boolean;
  reason?: string;
  outcome?: Outcome;
  credit?: string;
  low?: number;
  mid?: number;
  high?: number;
  low_ratio?: number;
  high_ratio?: number;
  average_five_year_total?: number;
  slowest_window?: [number, number, number];
  fastest_window?: [number, number, number];
  point_years?: [number, number];
  history?: [number, number];
  how_built?: string;
  how_it_did?: string;
  why_not_headline?: string;
  narrative?: string[];
}

export interface BaselineCounty extends CountyRange {
  by_type: Record<string, number>;
  recent_annual: Record<string, number>;
}

export interface Baseline {
  outcome: 'permits';
  horizon_years: number;
  window_years: number[];
  forecast_years: number[];
  county: BaselineCounty[];
  state: LMH & { by_type: Record<string, number>; by_year: Array<LMH & { year: number }> };
  band_rule: BandRule;
  alternative_band: AlternativeBand;
  method: string;
  notes: string[];
  narrative: string[];
}

export interface CaseBlock {
  label: string;
  status: string;
  newly_affected_share: number;
  delay_years: number;
  ramp: string;
  estimate: LMH;
  by_year: Record<Level, number[]>;
  assumptions: string[];
  outcome: Outcome;
  can_add_to_baseline: boolean;
  estimate_permits: LMH;
}

export interface TornadoBar {
  id: string;
  label: string;
  base: number;
  at_low: number;
  at_high: number;
  swing: number;
  low_text: string;
  high_text: string;
  favorable_end: 'low' | 'high';
}

export interface JointCase {
  direction: 'favorable' | 'unfavorable';
  value: number;
  levels: Record<string, Level>;
  settings: string[];
  reading: string;
}

export interface Components {
  formula: string;
  increment_mid_permits: number;
  linear_in: Record<string, number>;
  linear_counties: Record<string, string[]>;
  newly_affected_share: number;
  ramp_mid: number[];
  conversion_mid: number;
  by_county: Array<{ fips: string; benchmark_mid: number; market: number; increment_mid_permits: number }>;
}

export interface Grid {
  params: string[];
  levels: Level[];
  outcome: 'permits';
  cells: Record<string, number>;
}

export interface CurrentLawRef {
  current_strength: number;
  source: string;
  note: string;
  human_review: string | boolean | null;
  file: string | null;
}

export interface GeographyCheck {
  composite_per_county: number[];
  reading: string;
}

export interface Scenario {
  label: string;
  formula: string;
  benchmark: LMH & {
    outcome: Outcome;
    interpretation: string;
    by_county: CountyRange[];
    by_year: Record<Level, number[]>;
  };
  increment: {
    status: string;
    estimate: LMH;
    outcome: 'permits';
    can_add_to_baseline: boolean;
    native: LMH & { outcome: Outcome };
    conversion: { factor: LMH; text: string };
    completed_homes_equivalent: LMH;
    newly_affected_share: number;
    current_law: CurrentLawRef;
    ramp: { id: string; years: Record<Level, number[]> };
    by_year: Record<Level, number[]>;
    by_county: CountyRange[];
    years: number[];
    assumptions: string[];
  };
  total: { estimate: LMH; outcome: 'permits'; pairing_rule: string };
  cases: Record<string, CaseBlock>;
  tornado: TornadoBar[];
  joint: { favorable: JointCase; unfavorable: JointCase };
  factors: Record<string, unknown> & {
    notes?: string[];
    exposure?: number[];
    exposure_label?: string;
    geography_check?: GeographyCheck | null;
    response?: number;
  };
  components: Components;
  grid: Grid | null;
  diagnostics: Record<string, unknown>;
  limits: string[];
  notes: string[];
  band_ids: string[];
  levels_used: Record<Level, Record<string, string>>;
  narrative: string[];
}

export interface Combined {
  label: string;
  increment: { estimate: LMH; outcome: 'permits'; can_add_to_baseline: boolean; status: string };
  total: { estimate: LMH; outcome: 'permits'; pairing_rule: string };
  parts_in_package: Record<Level, Record<ScenarioName, number>>;
  parts_alone: Record<Level, Record<ScenarioName, number>>;
  sum_of_parts: LMH;
  overlap_removed: LMH;
  adjustments: Record<Level, Record<string, number>>;
  rules: string[];
  limits: string[];
}

export interface CrossCheckCounty {
  fips: string;
  name: string;
  april_2020: number;
  end_year: number;
  net_change: number;
  change_share: number;
  [july: string]: number | string;
}

export interface CrossCheck {
  label: string;
  available: boolean;
  outcome: 'stock_change';
  can_add_to_baseline: false;
  measure: string;
  end_year: number;
  county: CrossCheckCounty[];
  state: { april_2020: number; end: number; net_change: number; change_share: number } | null;
  caveat: string;
  source: string;
  notes: string[];
  narrative: string[];
}

export interface ResultsMeta {
  state: string;
  state_fips: string;
  build_id: string;
  vintages: Record<string, string>;
  git_sha: string;
  run_date: string;
  input: string;
  input_sha256: string;
  schema_version: string;
}

export interface Results {
  results_schema_version: string;
  meta: ResultsMeta;
  baseline: Baseline;
  scenarios: Record<ScenarioName, Scenario>;
  cross_check: { housing_units_pep: CrossCheck };
  combined?: Combined;
  registers_used: Record<string, { path: string; sha256?: string | null; entries?: number; levels?: string }>;
  no_llm: string;
}

export interface IndexRow {
  state: string;
  name: string;
  fips: string;
  baseline: LMH;
  pep_net_change_since_2020: number | null;
  scenarios: Record<
    ScenarioName,
    { increment: LMH; status: string; newly_affected_share: number; benchmark_mid: number; benchmark_outcome: Outcome }
  >;
  combined?: LMH;
}

export interface BundleIndex {
  states: IndexRow[];
}

export interface SourceRef {
  title: string;
  url: string;
  locator?: string;
  quote?: string;
  accessed?: string;
}

/** One entry of src/hre/assumptions/parameters.yaml, as exported to registers.json. */
export interface RegisterEntry {
  id: string;
  label: string;
  description: string;
  unit: string;
  low: number | number[];
  mid: number | number[];
  high: number | number[];
  scope: string;
  scenarios: string[];
  grade: string;
  confidence: string;
  direction: number;
  sources: SourceRef[];
  citation: string;
  rationale: string;
  transferability?: string;
  levels?: Partial<Record<Level, string>>;
  ported_from?: string;
  [extra: string]: unknown;
}

export interface LawFeature {
  id: string;
  challenge_requirement: string;
  observed_position: string;
  status: string;
  sources: SourceRef[];
  limitations?: string[];
}

export interface LawScenario {
  record: {
    law: string;
    summary: string;
    quote: string;
    url: string;
    accessed: string;
    in_effect: string;
  };
  features: LawFeature[];
  current_strength: number;
  strength_rationale: string;
  human_review?: unknown;
  [extra: string]: unknown;
}

export interface LawFile {
  state: string;
  scenarios: Partial<Record<ScenarioName, LawScenario>>;
  [extra: string]: unknown;
}

export interface DataSource {
  id: string;
  title: string;
  license: string | null;
  notes: string | null;
  files: number;
  where: string[];
  accessed: [string, string] | null;
  vintages: string[];
  vintage_key: string | null;
  only_for: string[] | null;
  in_model: boolean;
  why_not: string | null;
  manifest: string;
}

/** One check in the validation ledger (src/hre/validation/ledger.py has the field rules). */
export interface LedgerEntry {
  id: string;
  title: string;
  evidence_class: string;
  place: string;
  years: string;
  outcome: string;
  unit: string;
  prediction?: { low: number | null; mid: number | null; high: number | null } | null;
  actual?: number | null;
  actual_text?: string | null;
  result: 'hit' | 'miss' | 'pending' | 'not_a_test';
  result_text: string;
  frozen?: { sha256: string; protocol: string; commit?: string | null } | null;
  source: { title: string; url: string };
  independence: string;
  supports: string;
  does_not_support: string;
  next_check: string;
  credit?: string | null;
}

export interface Registers {
  assumptions: RegisterEntry[];
  current_law: Record<string, LawFile>;
  current_law_default: string;
  validation_ledger: { status: string; classes?: Record<string, string>; entries: LedgerEntry[] };
  sources: DataSource[];
}

export interface BundleMeta {
  results_schema_version: string;
  jurisdictions: number;
  export_date: string;
  run_dates: string[];
  git_shas: string[];
  input_schema_versions: string[];
  parameters_sha256: string;
  vintages: Record<string, string>;
  no_llm: string;
}
