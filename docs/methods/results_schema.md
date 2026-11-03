# Results schema (`results/{ST}.json`)

Written by `hre run --state XX --scenarios baseline` (`src/hre/model/run.py`), checked by `validate_results` before it is written; the web front-end (Phase 4) reads only this file. `results_schema_version` is `"1"`. Floats are rounded to 4 decimals when written; the engine never rounds. Every number sits under an `outcome` label from the fixed set in `src/hre/schema.py`: `permits`, `net_permits`, `completed_homes`, `stock_change`, `cost_response_proxy`.

## Top level

| Field | Meaning |
|---|---|
| `results_schema_version` | `"1"` |
| `meta` | `state`, `state_fips`, `build_id` (git short sha + hash of input and register), `git_sha` (`-dirty` if tracked files were modified), `run_date`, `input` and `input_sha256` (the processed file), `schema_version` (input schema), `vintages` (every input vintage, including the BPS backtest files and the HCD file behind the ADU tiers) |
| `baseline` | the baseline block below |
| `scenarios` | `{name: scenario block}`; empty in Phase 2, filled by Phase 3 for `adu`, `missing_middle`, `tod`, `parking`, `fees` |
| `registers_used` | path and sha256 of `parameters.yaml` (and how many entries), `elasticities.yaml`, and `current_law/{ST}.yaml` (`sha256: null` when the state has no file) |
| `no_llm` | "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py." |

## `baseline`

| Field | Meaning |
|---|---|
| `outcome` | `permits` |
| `horizon_years`, `window_years`, `forecast_years` | 5; the three data years averaged; the five forecast years |
| `county[]` | per county: `fips`, `name`, `low`, `mid`, `high`, `by_type{u1,u2,u34,u5}` (mid), `recent_annual{year: units}` |
| `state` | `low`, `mid`, `high`, `by_type`, `by_year[{year, low, mid, high}]` (flat: point ÷ 5) |
| `band_rule` | `name` (`empirical_p10_p90`), `low_ratio`, `high_ratio`, `reading`, `applied_to_counties`, `source`, `alternative` |
| `method`, `notes[]`, `narrative[]` | one-line method; county-years with no BPS row; 2-3 template sentences |
| `alternative_band` | the 20-year swing band (Adam Ruege's rule), shown in its own section: `available`; when true `outcome`, `credit`, `low`, `mid` (the last five years' total), `high`, `low_ratio`, `high_ratio`, `average_five_year_total`, `slowest_window` and `fastest_window` (`[first year, last year, total]`), `point_years`, `history`, `how_built`, `how_it_did`, `why_not_headline`, `applied_to_counties` (always false), `narrative[]`; when false, `reason` |

## Scenario block (Phase 3 fills it; the validator already enforces it)

    {benchmark{low, mid, high, outcome, interpretation},
     increment{status, estimate{low, mid, high}, assumptions[], outcome, can_add_to_baseline},
     total{estimate{low, mid, high}, pairing_rule},
     cases{<case_id>: {label, status, newly_affected_share, delay_years, ramp, estimate, by_year,
                       assumptions[], outcome, can_add_to_baseline}},
     tornado[{id, label, base, at_low, at_high, swing, low_text, high_text, favorable_end}],
     joint{favorable{value, levels, settings[], reading}, unfavorable{...}},
     narrative[]}

Rules the validator checks: low ≤ mid ≤ high everywhere; outcome labels from the fixed set; `can_add_to_baseline` only when the increment's outcome is `permits` (decision 30); every key above present. Case ids and statuses: `docs/methods/cases.md`. Tornado and joint cases: `docs/methods/sensitivity.md`.

## New Hampshire example (trimmed from `results/NH.json`, 2026-11-03)

```json
{
 "results_schema_version": "1",
 "meta": {
  "state": "NH",
  "state_fips": "33",
  "build_id": "00ac4bb-638b6e19",
  "git_sha": "00ac4bb6b156da8256fb080790f1a8c3c94e064f-dirty",
  "run_date": "2026-11-03",
  "input_sha256": "f6083c7185d904b6de69a049b813a45249e88c18106393de06fde5d09d151c4f",
  "vintages": {
   "bps": "annual files as posted 2026 (2025 posted 2026-05-14)",
   "acs": "ACS 5-year 2020-2024 (2024 release)",
   "hcd_adu_tiers": "HCD APR Table A2, resource last modified 2026-10-30 (tier rates in the register)"
  }
 },
 "baseline": {
  "outcome": "permits",
  "horizon_years": 5,
  "window_years": [
   2023,
   2024,
   2025
  ],
  "forecast_years": [
   2026,
   2027,
   2028,
   2029,
   2030
  ],
  "county": [
   {
    "fips": "33001",
    "name": "Belknap County",
    "low": 945.5105,
    "mid": 1765.0,
    "high": 2810.586,
    "by_type": {
     "u1": 1373.3333,
     "u2": 116.6667,
     "u34": 25.0,
     "u5": 250.0
    },
    "recent_annual": {
     "2023": 354.0,
     "2024": 282.0,
     "2025": 423.0
    }
   },
   "... 9 more"
  ],
  "state": {
   "low": 12990.725,
   "mid": 24250.0,
   "high": 38615.7,
   "by_type": {
    "u1": 15253.3333,
    "u2": 916.6667,
    "u34": 820.0,
    "u5": 7260.0
   },
   "by_year": [
    {
     "year": 2026,
     "low": 2598.145,
     "mid": 4850.0,
     "high": 7723.14
    },
    "... 4 more"
   ]
  },
  "band_rule": {
   "name": "empirical_p10_p90",
   "low_ratio": 0.5357,
   "high_ratio": 1.5924,
   "reading": "In 80% of past five-year periods (50 states and DC, forecast origins 1990-2015) the actual permit total fell inside this band. It is a statement about history, not a probability."
  },
  "narrative": [
   "If current rules continue, New Hampshire would permit about 24,300 homes over 2026-2030: the 2023-2025 average carried forward 5 years.",
   "In 80% of past five-year periods the actual total fell between 0.54 and 1.59 times this kind of estimate, which here means 13,000 to 38,600; that is a range from history, not a probability.",
   "Rockingham County accounts for 27% of the total, and single-family homes make up 63% of it."
  ]
 },
 "scenarios": {},
 "registers_used": {
  "parameters": {
   "path": "src/hre/assumptions/parameters.yaml",
   "entries": 30
  },
  "current_law": {
   "path": "src/hre/current_law/NH.yaml",
   "sha256": "b70e6b4436d9e73ae66505bd2bd9049ecd5f6b9d641ddd48e0b8f1b94578818b"
  }
 },
 "no_llm": "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py."
}
```
