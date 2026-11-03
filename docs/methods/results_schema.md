# Results schema (`results/{ST}.json`)

Written by `hre run --state XX` (or `hre run --all`) (`src/hre/model/run.py`), checked by `validate_results` before it is written; the web front-end (Phase 4) reads only this file. `results_schema_version` is `"1"`. Floats are rounded to 4 decimals when written; the engine never rounds. Every number sits under an `outcome` label from the fixed set in `src/hre/schema.py`: `permits`, `net_permits`, `completed_homes`, `stock_change`, `cost_response_proxy`.

## Top level

| Field | Meaning |
|---|---|
| `results_schema_version` | `"1"` |
| `meta` | `state`, `state_fips`, `build_id` (git short sha + hash of input and register), `git_sha` (`-dirty` if tracked files were modified), `run_date`, `input` and `input_sha256` (the processed file), `schema_version` (input schema), `vintages` (every input vintage, including the BPS backtest files and the HCD file behind the ADU tiers) |
| `baseline` | the baseline block below |
| `scenarios` | `{name: scenario block}` for `adu`, `missing_middle`, `tod`, `parking`, `fees` (below); `cross_check` and `combined` sit beside it |
| `registers_used` | path and sha256 of `parameters.yaml` (and how many entries), `elasticities.yaml`, and `current_law/{ST}.yaml` (`sha256: null` when the state has no file) |
| `no_llm` | "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py." |

## `baseline`

| Field | Meaning |
|---|---|
| `outcome` | `permits` |
| `horizon_years`, `window_years`, `forecast_years` | 5; the three data years averaged; the five forecast years |
| `county[]` | per county: `fips`, `name`, `low`, `mid`, `high`, `by_type{u1,u2,u34,u5}` (mid), `recent_annual{year: units}` |
| `state` | `low`, `mid`, `high`, `by_type`, `by_year[{year, low, mid, high}]` (flat: point ÷ 5) |
| `band_rule` | `name` (`empirical_p10_p90`), `low_ratio`, `high_ratio`, `reading`, `applied_to_counties`, `coverage_by_period[]` (`origins` [first, last], `runs`, `inside`, `above`, `below`, `share_inside`: the fixed band on origins 1990-99, 2000-04, 2005-10, 2011-15, 2016-20), `coverage_realtime` (`origins`, `runs`, `inside`, `share_inside`, `origins_under_5pct`: the band refitted each year on closed windows only), `reading_history` (the second reading sentence, decision 66), `source`, `alternative`. Added in Phase 3 step 0 as new keys; `results_schema_version` stays "1" because nothing read version-1 files yet (the front-end starts in Phase 4) |
| `method`, `notes[]`, `narrative[]` | one-line method; county-years with no BPS row; 2-3 template sentences |
| `alternative_band` | the 20-year swing band (Adam Ruege's rule), shown in its own section: `available`; when true `outcome`, `credit`, `low`, `mid` (the last five years' total), `high`, `low_ratio`, `high_ratio`, `average_five_year_total`, `slowest_window` and `fastest_window` (`[first year, last year, total]`), `point_years`, `history`, `how_built`, `how_it_did`, `why_not_headline`, `applied_to_counties` (always false), `narrative[]`; when false, `reason` |

## `cross_check.housing_units_pep` (decisions 56, 68)

"Census housing-unit estimates: net change since April 2020", shown beside the permit
baseline and never added to it (`outcome` `stock_change`, `can_add_to_baseline` false).
Built by `hre.model.crosscheck.pep_cross_check` from the processed input's
`housing_units_pep` (input schema 3 keeps the April 1 2020 estimates base as `"2020-04"`).

| Field | Meaning |
|---|---|
| `label`, `measure`, `source` | what the panel shows and where it comes from |
| `available` | false when no county has both an April 2020 base and a July estimate |
| `end_year` | the latest July 1 estimate used (2025 for Vintage 2025) |
| `county[]` | `fips`, `name`, `april_2020`, `july_{end_year}`, `end_year`, `net_change`, `change_share` |
| `state` | `april_2020`, `end`, `net_change`, `change_share`, summed over the counties listed |
| `caveat` | "These estimates are built partly from building permits, so they are a consistency view, not an independent measurement of homes added." |
| `narrative[]` | one template sentence plus the caveat |
| `notes[]` | counties left out and why |

NH (Vintage 2025): 638,800 in April 2020, 662,160 in July 2025, +23,360 (+3.7%); the 2021-2025
permit total was 24,225.

## Scenario block (`scenarios.<name>`, Phase 3)

One block per scenario (`adu`, `missing_middle`, `tod`, `parking`, `fees`), built by
`hre.model.scenarios.common.run_scenario` from the scenario's `Spec`. Every layer comes from one
function evaluated at the low, mid and high assumption sets, so the layers cannot disagree.

| Key | Meaning |
|---|---|
| `label`, `formula` | the scenario's name and its one-line formula (the slide line) |
| `benchmark` | `low`, `mid`, `high` in the source's unit; `outcome` (`completed_homes`, `net_permits`, `stock_change` or `cost_response_proxy`); `interpretation`; `by_county[]` {fips, name, low, mid, high}; `by_year` {low, mid, high: five numbers} |
| `increment` | `status` (`register_default`); `estimate` {low, mid, high} **in permits**; `outcome` `permits`; `can_add_to_baseline` true (after conversion); `native` {low, mid, high, outcome} before conversion; `conversion` {factor{low, mid, high}, text}; `completed_homes_equivalent` {low, mid, high}; `newly_affected_share`; `current_law` {current_strength, source, note, human_review, file}; `ramp` {id, years{low, mid, high}}; `by_year`, `by_county`, `years`, `assumptions[]` |
| `total` | `estimate` {low, mid, high} = baseline + increment, low with low; `outcome` `permits`; `pairing_rule` |
| `cases` | every named case (`docs/methods/cases.md`), each with `estimate` (native) and `estimate_permits` |
| `tornado[]` | one bar per assumption that moves the mid increment, largest swing first (`sensitivity.md`); gamma is swung for missing middle and TOD |
| `joint` | `favorable` and `unfavorable`: every assumption at its best (worst) end at once; starts from the high (low) set |
| `factors` | per-county inputs of the mid run (exposure, rate, tier, overlay, market, spaces, prices, response, `geography_check` for parking and fees, `notes`) |
| `components` | for exact in-page rescaling: `linear_in` {id: mid value} (the increment is proportional to these), `increment_mid_permits`, `newly_affected_share`, `ramp_mid`, `conversion_mid`, `by_county[]` {fips, benchmark_mid, market, increment_mid_permits}. New increment = old × new value ÷ old value for any `linear_in` id |
| `grid` | parking and fees only: `params`, `levels`, `cells` {"id=lv|id=lv|...": increment in permits} for every low/mid/high combination (parking 81 cells, fees 9) |
| `diagnostics` | outside every band: missing-middle comparison rates and the all-metro sensitivity; TOD quarter-mile count and boundary rate; fees actual-fee variant and stock route |
| `limits[]`, `notes[]`, `narrative[]` | the sentences a legislator must hear; data notes; four template sentences |
| `levels_used` | which level each register id took in the low, mid and high sets |

Rules the validator checks: low ≤ mid ≤ high in every layer; outcome labels from the fixed set;
`can_add_to_baseline` only when the outcome is `permits`; every key present. The property tests
(`tests/test_golden.py`) add: the native increment keeps the benchmark's label; share 0 and
"after the horizon" give 0; no negative increment; joint favorable ≥ high set; combined ≤ sum.

## `combined` (Phase 3 step 6; `combined.md`)

Present when all five scenarios ran: `label` ("If all five passed together (illustration)"),
`increment` {estimate{low, mid, high}, outcome `permits`, can_add_to_baseline}, `total`,
`parts_in_package` and `parts_alone` per level, `sum_of_parts`, `overlap_removed`, `adjustments`,
`rules[]`, `limits[]`. The validator refuses a package larger than the sum of its parts.

## The web bundle (`hre export --out web/public/results/`)

| File | Contents |
|---|---|
| `{ST}.json` | the results file exactly as `hre run` wrote it (compact JSON), for the 50 states and DC; the synthetic ZZ only when it is the only file (the demo) |
| `index.json` | `states[]`: state, name, fips, `baseline` {low, mid, high}, `pep_net_change_since_2020`, `scenarios` {name: {increment{low, mid, high}, status, newly_affected_share, benchmark_mid, benchmark_outcome}}, `combined` {low, mid, high} |
| `registers.json` | `assumptions[]` (every register entry), `current_law` {ST: file}, `current_law_default`, `validation_ledger` (placeholder until Phase 5) |
| `meta.json` | results schema version, jurisdictions, export date, run dates, git shas, input schema versions, register sha256, vintages, the no-language-model statement |

The bundle is committed (decision 74): after any change to the engine, the register or the
inputs, run `make results-all export` from a clean checkout and commit it; `tests/test_bundle.py`
fails CI when it is stale. Phase 4's Pages build only copies it.

## New Hampshire scenario example (trimmed from `results/NH.json`, 2026-11-03)

The fee scenario, the combined package and the cross-check (lists cut to their first entry):

```json
{
 "scenarios": {
  "fees": {
   "label": "Development and impact fees cut in half",
   "formula": "permits = baseline permits x builder response x (fee cut / new-home price); fee cut = $50,000 x 50%",
   "benchmark": {
    "low": 0.0,
    "mid": 933.53,
    "high": 4434.9695,
    "outcome": "cost_response_proxy",
    "interpretation": "A cost-response proxy: the extra permits if builders respond to a $25,000 lower cost per home as the measured studies say they respond to cost and price chan...",
    "by_county": [
     {
      "fips": "33001",
      "name": "Belknap County",
      "low": 0.0,
      "mid": 70.3599,
      "high": 334.2625
     },
     "... 9 more"
    ],
    "by_year": {
     "low": [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
     ],
     "mid": [
      186.706,
      186.706,
      186.706,
      186.706,
      186.706
     ],
     "high": [
      886.9939,
      886.9939,
      886.9939,
      886.9939,
      886.9939
     ]
    }
   },
   "increment": {
    "status": "register_default",
    "estimate": {
     "low": 0.0,
     "mid": 933.53,
     "high": 4434.9695
    },
    "outcome": "permits",
    "can_add_to_baseline": true,
    "native": {
     "low": 0.0,
     "mid": 933.53,
     "high": 4434.9695,
     "outcome": "cost_response_proxy"
    },
    "conversion": {
     "factor": {
      "low": 1.0,
      "mid": 1.0,
      "high": 1.0
     },
     "text": "Computed on permits, so the conversion is 1 (the response is a share of baseline permits)."
    },
    "completed_homes_equivalent": {
     "low": 0.0,
     "mid": 869.4905,
     "high": 4130.7336
    },
    "newly_affected_share": 1.0,
    "current_law": {
     "current_strength": 0.0,
     "source": "default",
     "note": "No statewide law found; local permissions unverified.",
     "human_review": null,
     "file": "NH.yaml"
    },
    "ramp": {
     "id": "ramp_immediate",
     "years": {
      "low": [
       1.0,
       1.0,
       1.0,
       1.0,
       1.0
      ],
      "mid": [
       1.0,
       1.0,
       1.0,
       1.0,
       1.0
      ],
      "high": [
       1.0,
       1.0,
       1.0,
       1.0,
       1.0
      ]
     }
    },
    "by_year": {
     "low": [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
     ],
     "mid": [
      186.706,
      186.706,
      186.706,
      186.706,
      186.706
     ],
     "high": [
      886.9939,
      886.9939,
      886.9939,
      886.9939,
      886.9939
     ]
    },
    "by_county": [
     {
      "fips": "33001",
      "name": "Belknap County",
      "low": 0.0,
      "mid": 70.3599,
      "high": 334.2625
     },
     "... 9 more"
    ],
    "years": [
     2026,
     2027,
     2028,
     2029,
     2030
    ],
    "assumptions": [
     "Assumptions selected for this calculation; legal rights and the time needed to build still need local evidence.",
     "... 4 more"
    ]
   },
   "total": {
    "estimate": {
     "low": 12990.725,
     "mid": 25183.53,
     "high": 43050.6695
    },
    "outcome": "permits",
    "pairing_rule": "Baseline low plus increment low, mid plus mid, high plus high; no probability is assigned to this range."
   },
   "cases": {
    "register_default": {
     "label": "Register default: newly affected share from current law",
     "status": "register_default",
     "newly_affected_share": 1.0,
     "delay_years": 0,
     "ramp": "ramp_immediate",
     "estimate": {
      "low": 0.0,
      "mid": 933.53,
      "high": 4434.9695
     },
     "by_year": {
      "low": [
       0.0,
       0.0,
       0.0,
       0.0,
       0.0
      ],
      "mid": [
       186.706,
       186.706,
       186.706,
       186.706,
       186.706
      ],
      "high": [
       886.9939,
       886.9939,
       886.9939,
       886.9939,
       886.9939
      ]
     },
     "assumptions": [
      "Assumptions selected for this calculation; legal rights and the time needed to build still need local evidence.",
      "... 4 more"
     ],
     "outcome": "cost_response_proxy",
     "can_add_to_baseline": true,
     "estimate_permits": {
      "low": 0.0,
      "mid": 933.53,
      "high": 4434.9695
     }
    },
    "...": "14 more cases"
   },
   "tornado": [
    {
     "id": "builder_response_override",
     "label": "Builder response to lower costs",
     "base": 933.53,
     "at_low": 0.0,
     "at_high": 3534.9669,
     "swing": 3534.9669,
     "low_text": "0.00% per 1%",
     "high_text": "2.84% per 1%",
     "favorable_end": "high"
    },
    {
     "id": "new_home_price_ratio",
     "label": "New home price compared with the median home value",
     "base": 933.53,
     "at_low": 1171.2067,
     "at_high": 743.9067,
     "swing": 427.3,
     "low_text": "1.00",
     "high_text": "1.57",
     "favorable_end": "low"
    }
   ],
   "joint": {
    "favorable": {
     "direction": "favorable",
     "value": 4434.9695,
     "levels": {
      "builder_response_override": "high",
      "new_home_price_ratio": "low"
     },
     "settings": [
      "Builder response to lower costs: 2.84% per 1%",
      "New home price compared with the median home value: 1.00"
     ],
     "reading": "Every assumption at its most favorable end at once; an illustration of the extreme, not a likely outcome."
    },
    "unfavorable": {
     "direction": "unfavorable",
     "value": 0.0,
     "levels": {
      "builder_response_override": "low",
      "new_home_price_ratio": "high"
     },
     "settings": [
      "Builder response to lower costs: 0.00% per 1%",
      "New home price compared with the median home value: 1.57"
     ],
     "reading": "Every assumption at its least favorable end at once; an illustration of the extreme, not a likely outcome."
    }
   },
   "factors": {
    "baseline_permits": [
     1765.0,
     2098.3333,
     798.3333,
     596.6667,
     2150.0,
     "... 5 more"
    ],
    "fee_cut": 25000.0,
    "new_home_price": [
     470349.54,
     487913.94,
     351413.46,
     236993.94,
     432209.7,
     "... 5 more"
    ],
    "cut_share_of_price": [
     0.0532,
     0.0512,
     0.0711,
     0.1055,
     0.0578,
     "... 5 more"
    ],
    "response": 0.75,
    "response_route": "override",
    "geography_check": {
     "composite_per_county": [
      0.4808,
      0.4808,
      0.4808,
      0.4808,
      0.4808,
      "... 5 more"
     ],
     "reading": "Composite of elasticities per county (diagnostic): supply-constrained metros respond less."
    },
    "notes": []
   },
   "components": {
    "formula": "permits = baseline permits x builder response x (fee cut / new-home price); fee cut = $50,000 x 50%",
    "increment_mid_permits": 933.53,
    "linear_in": {
     "builder_response_override": 0.75,
     "total_fee_per_unit": 50000,
     "fee_cut_share": 0.5
    },
    "newly_affected_share": 1.0,
    "ramp_mid": [
     1.0,
     1.0,
     1.0,
     1.0,
     1.0
    ],
    "conversion_mid": 1.0,
    "by_county": [
     {
      "fips": "33001",
      "benchmark_mid": 70.3599,
      "market": 1.0,
      "increment_mid_permits": 70.3599
     },
     "... 9 more"
    ]
   },
   "grid": {
    "params": [
     "builder_response_override",
     "new_home_price_ratio"
    ],
    "levels": [
     "low",
     "... 2 more"
    ],
    "outcome": "permits",
    "cells": {
     "builder_response_override=low|new_home_price_ratio=low": 0.0,
     "builder_response_override=low|new_home_price_ratio=mid": 0.0,
     "builder_response_override=low|new_home_price_ratio=high": 0.0,
     "...": "6 more"
    }
   },
   "diagnostics": {
    "actual_fee_variant": {
     "fee_cut": 6813.5,
     "permits": {
      "low": 0.0,
      "mid": 254.4243,
      "high": 963.4199
     },
     "reading": "The same formula with half of a typical actual fee (NAHB's $13,627) instead of half of the challenge's $50,000."
    },
    "stock_route": {
     "homes": 5228.4605,
     "flow_route_mid": 933.53,
     "ratio_to_flow": 5.6007,
     "reading": "Stock route: housing stock x 0.3 x 0.5 x cut / price. It applies a long-run stock elasticity to the whole stock rather than to five years of building, so it ..."
    }
   },
   "limits": [
    "The low end is zero: Mayer and Somerville found no significant impact-fee effect, and some fees buy the approvals that let building happen (Burge and Ihlanfe...",
    "... 2 more"
   ],
   "notes": [],
   "levels_used": {
    "low": {
     "builder_response_override": "low",
     "new_home_price_ratio": "high",
     "ramp_immediate": "mid"
    },
    "mid": {
     "builder_response_override": "mid",
     "new_home_price_ratio": "mid",
     "ramp_immediate": "mid"
    },
    "high": {
     "builder_response_override": "high",
     "new_home_price_ratio": "low",
     "ramp_immediate": "mid"
    }
   },
   "narrative": [
    "Development and impact fees cut in half: the source policy's activity, transferred to New Hampshire, comes to about 930 additional permits (a cost-response p...",
    "... 3 more"
   ]
  }
 },
 "combined": {
  "label": "If all five passed together (illustration)",
  "increment": {
   "estimate": {
    "low": 34.8365,
    "mid": 2403.6402,
    "high": 11301.897
   },
   "outcome": "permits",
   "can_add_to_baseline": true,
   "status": "register_default"
  },
  "total": {
   "estimate": {
    "low": 13025.5615,
    "mid": 26653.6402,
    "high": 49917.597
   },
   "outcome": "permits",
   "pairing_rule": "Low with low, mid with mid, high with high; no probability is assigned."
  },
  "parts_in_package": {
   "low": {
    "adu": 34.8365,
    "missing_middle": 0.0,
    "tod": 0.0,
    "parking": 0.0,
    "fees": 0.0
   },
   "mid": {
    "adu": 276.6236,
    "missing_middle": 1033.1436,
    "tod": 3.0487,
    "parking": 157.2944,
    "fees": 933.53
   },
   "high": {
    "adu": 1840.9413,
    "missing_middle": 2514.6896,
    "tod": 34.734,
    "parking": 2476.5626,
    "fees": 4434.9695
   }
  },
  "parts_alone": {
   "low": {
    "adu": 34.8365,
    "missing_middle": 0.0,
    "tod": 0.0,
    "parking": 0.0,
    "fees": 0.0
   },
   "mid": {
    "adu": 276.898,
    "missing_middle": 1034.8581,
    "tod": 3.0487,
    "parking": 157.2944,
    "fees": 933.53
   },
   "high": {
    "adu": 1846.4942,
    "missing_middle": 2518.8629,
    "tod": 34.734,
    "parking": 2476.5626,
    "fees": 4434.9695
   }
  },
  "sum_of_parts": {
   "low": 34.8365,
   "mid": 2405.6293,
   "high": 11311.6232
  },
  "overlap_removed": {
   "low": 0.0,
   "mid": 1.989,
   "high": 9.7262
  },
  "adjustments": {
   "low": {
    "detached_homes_moved_from_missing_middle_to_tod": 0.0,
    "lots_removed_from_adu_exposure": 0.0
   },
   "mid": {
    "detached_homes_moved_from_missing_middle_to_tod": 302.0,
    "lots_removed_from_adu_exposure": 308.4011
   },
   "high": {
    "detached_homes_moved_from_missing_middle_to_tod": 302.0,
    "lots_removed_from_adu_exposure": 750.6536
   }
  },
  "rules": [
   "Detached homes within the transit distance of a rail or ferry stop count under transit-oriented density, not missing middle.",
   "... 3 more"
  ],
  "limits": [
   "An illustration, not a forecast of a package: reforms interact in ways no study has measured together. A teammate's earlier prototype does not combine them a...",
   "Results are statewide; the model does not say which places will build."
  ]
 },
 "cross_check": {
  "housing_units_pep": {
   "label": "Census housing-unit estimates: net change since April 2020",
   "available": true,
   "outcome": "stock_change",
   "can_add_to_baseline": false,
   "measure": "July 1 estimate of the latest year minus the April 1 2020 estimates base",
   "end_year": 2025,
   "county": [
    {
     "fips": "33001",
     "name": "Belknap County",
     "april_2020": 38251,
     "july_2025": 39998,
     "end_year": 2025,
     "net_change": 1747,
     "change_share": 0.0457
    },
    "... 9 more"
   ],
   "state": {
    "april_2020": 638800,
    "end": 662160,
    "net_change": 23360,
    "change_share": 0.0366
   },
   "caveat": "These estimates are built partly from building permits, so they are a consistency view, not an independent measurement of homes added.",
   "source": "Census Population Estimates, CO-EST2025-HU.xlsx (Vintage 2025); decision 56",
   "notes": [],
   "narrative": [
    "Census housing-unit estimates put New Hampshire's housing stock at 662,160 in July 2025, 23,400 more than in April 2020 (+3.7%).",
    "These estimates are built partly from building permits, so they are a consistency view, not an independent measurement of homes added."
   ]
  }
 }
}
```

## New Hampshire baseline example (trimmed from `results/NH.json`, 2026-11-03)

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
