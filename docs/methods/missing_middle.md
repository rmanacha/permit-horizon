# Missing-middle scenario: two to four homes allowed on single-family lots

Code: `src/hre/model/scenarios/missing_middle.py`. Register ids: `mm_rate_per_lot`,
`mm_sf_only_share`, `mm_net_new_factor`, `mm_code_penalty`, `mm_source_city_value`,
`value_ratio_exponent`, `market_adjustment_bounds`, `ramp_missing_middle`; diagnostics
`mm_diag_minneapolis_gross`, `mm_diag_cluster`, `mm_diag_arlington`.

**The formula on the slide:** net permits = detached homes in central metro counties ×
single-family-only share × rate per lot × code penalty × 5 years; increment = that × market
adjustment × newly affected share × ramp.

## The three layers

| Layer | Unit | How |
|---|---|---|
| Benchmark | permits net of demolitions (`net_permits`) | detached homes in counties with `metro_role == "central"` (decision 57) × single-family-only share (0.7 / 0.8 / 0.9) × rate per lot (0 / 0.1705% / 0.4% a year, Portland) × code penalty for 3+ units (0.8 / 0.9 / 1.0) × 5. The high rate is Portland's gross ceiling and is multiplied by the net-new factor (0.69 / 0.76 / 0.83) |
| Increment | permits | benchmark by year × market adjustment × (1 − current strength) × ramp (mid: from year 1, because the rate is Portland's first year; low: Auckland's build-up) |
| Total | permits | baseline + increment; net permits enter as permits (conversion 1) |

**Market adjustment (decision 34):** clip((county median value ÷ $581,500) ^ γ, 0.5, 1.5), with
Portland's ACS 2020-2024 median value and γ = 0.5. γ stays at 0.5 in the low, mid and high sets
because its effect changes sign with the county's value (cheaper than Portland: γ = 0 raises the
result; dearer: it lowers it); the tornado swings it from 0 to 1 (decision 71).

## New Hampshire, worked

- Central metropolitan counties: Hillsborough (100,545 detached homes) and Rockingham (89,774):
  190,319. Benchmark mid: 190,319 × 0.8 × 0.001705 × 0.9 × 5 = **1,168** net permits (0 to 2,083; the high is the gross ceiling × 0.76 net-new).
- Market adjustment: Hillsborough (421,100 ÷ 581,500)^0.5 = 0.851, Rockingham 0.925. Increment
  mid: 617.1 × 0.851 + 551.0 × 0.925 = **1,035 permits** (0 to 1,845; joint favorable 2,843). Total 25,285.
- No current-law file for missing middle in NH yet (Phase 5), so the newly affected share is 1.
- Diagnostics on the same chain, never in the band: Minneapolis gross 430, the
  Spokane/Austin/Charlotte cluster 1,302, Arlington 178; all metropolitan counties as the
  exposure (adds Strafford): benchmark 1,359.
- Adam's v2.0 NH: 0 / 1,600 / 3,800 (190,319 × 0.001705 × 5 = 1,622, without a single-family-only
  share, code penalty or market adjustment).

## Limits shown with the result

- A county boundary does not say which lots are eligible; some western central counties are
  mostly empty land.
- The rate comes from one city's first year; Minneapolis saw almost no net effect and Arlington far less.
- Permits are not completions; about 92 of every 100 permitted homes are completed (Census NRC).
- Results are statewide; the model does not say which places will build.
