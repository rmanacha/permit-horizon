// Fixed site text that is not a model result (edit freely; numbers never live here).
export const REPO_URL = 'https://github.com/rmanacha/permit-horizon';
export const SITE_URL = 'https://rmanacha.github.io/permit-horizon/';
export const doc = (path: string) => `${REPO_URL}/blob/main/${path}`;

export const TEAM = [
  { name: 'Rishabh Manacha', role: 'Team Leader and main engineer', org: 'Community Solutions' },
];
export const TEAM_NOTE = 'Teammates to be listed.';
// Test counts shown on the About page; scripts/check_submission.py fails when they differ from a run.
export const TEST_COUNTS = { python: 325, web: 30 };
export const CREDITS = [
  'Adam Ruege, a teammate, built an earlier prototype (Housing Reform Estimator v2.0). The 20-year swing range, the ADU home-value tiers, several register entries and the New Hampshire ADU law record are ported from it with attribution, marked in place.',
];

export const DOCS = [
  { label: 'README and the command contract', path: 'README.md' },
  { label: 'Model and assumptions overview', path: 'docs/MODEL_AND_ASSUMPTIONS.md' },
  { label: 'Policy scenario comparison', path: 'docs/POLICY_SCENARIO_COMPARISON.md' },
  { label: 'Data provenance', path: 'docs/DATA_PROVENANCE.md' },
  { label: 'Disclosures (AI tools, services, licences)', path: 'docs/DISCLOSURES.md' },
  { label: 'Judge guide: where each part of the challenge is answered', path: 'docs/JUDGE_GUIDE.md' },
  { label: 'Current law: how a state law becomes a strength', path: 'docs/methods/current_law.md' },
  { label: 'Validation ledger: every check, hits and misses', path: 'docs/evidence/validation.md' },
  { label: 'How this website works', path: 'docs/methods/ui.md' },
  { label: 'The results bundle the website reads', path: 'docs/methods/results_schema.md' },
  { label: 'Baseline backtest evidence', path: 'docs/evidence/baseline_backtest.md' },
  { label: 'Glossary', path: 'docs/GLOSSARY.md' },
  { label: 'Licence (Apache-2.0)', path: 'LICENSE' },
];

export const EXCLUDED_PARCELS =
  "Parcel counts replace the Census count of detached homes only where a county's parcel data agree with it within 30%: seven Utah counties (Utah Housing Unit Inventory) and Maricopa and Pinal counties in Arizona (county assessors). Only county totals are used; no parcel records, owner names or addresses. Every other county uses Census surveys (the American Community Survey and the 2020 Census). New Hampshire's statewide parcel data wait on confirmation of their terms of use.";
