# Baseline: permits over the next five years if current rules continue

Code: `src/hre/model/baseline.py`. Evidence: `docs/evidence/baseline_backtest.md`. Parameters: `horizon_years`, `baseline_window_years`, `baseline_band_ratio` in `src/hre/assumptions/parameters.yaml`.

## Formula

For each county *c* and structure type *t* (1 unit, 2 units, 3-4 units, 5+ units), with Census Building Permits Survey units authorised (estimates with imputation) *P*:

    point[c, t] = mean(P[c, t, 2023], P[c, t, 2024], P[c, t, 2025]) × 5
    state point = sum over counties and types
    band        = point × 0.5357 (low)  to  point × 1.5924 (high)
    each year   = point ÷ 5 (flat)

The three years are the latest three in the processed file (`baseline_window_years` = 3); 5 is the challenge horizon. A county with no BPS row in a year (no permit-issuing place reported) counts as zero for that year and is listed in the results file's `notes`.

## The band, in plain language

0.5357 and 1.5924 are the 10th and 90th percentiles of *actual ÷ forecast* when this exact rule is rerun on every state and DC for every forecast origin 1990-2015. So: **in 80% of past five-year periods, the actual statewide total fell between 0.54 and 1.59 times what this rule would have said.** On 2016-2020 origins, which the fit never saw, 251 of 255 runs fell inside. The band is a summary of history, not a probability that the future lands inside. It was fitted on state totals; it is applied to counties too, where real errors are larger, and the results file says so.

## A second way to draw the range, shown beside the headline (decision 69)

The results file also carries `alternative_band`, in its own section and never mixed into the headline numbers. It is the rule from Adam Ruege's prototype, Housing Reform Estimator v2.0, computed exactly as he tested it:

    point = the state's permits in the last five years (2021-2025)
    low   = point × (slowest five-year total of the last 20 years ÷ average five-year total)
    high  = point × (fastest five-year total of the last 20 years ÷ average five-year total)

The 20 years are the state's own annual totals from the Census state files (`state_permits_history`). There are 16 overlapping five-year stretches between 2006 and 2025. It is state-level only.

**New Hampshire.** 2021-2025 permits: 24,225. The slowest stretch was 2009-2013 (12,387, 0.67 times the average stretch). The fastest was 2021-2025 itself (1.31 times). Range: 24,225 × 0.6677 = 16,174 to 24,225 × 1.3057 = 31,632. These ratios equal the ones in Adam's published NH range (15,149 and 29,627 around 22,690).

**How the two compare.**

| | Headline band (ours) | 20-year swing band (Adam's) |
|---|---|---|
| Starting point | 3-year average × 5 | last five years' total |
| How wide | same multipliers for every state, 0.54 to 1.59 | each state's own swings (NH 0.67 to 1.31, Utah 0.50 to 1.48) |
| Its promise | inside in 80% of past periods, by construction | none fixed; coverage is what history gives |
| Past record | 98% inside on 2016-2020 forecasts | 71% inside over his 255 runs; 87% on 2016-2020; 20 of 51 states after 2005 |
| Typical high ÷ low, 2016-2020 | 2.97 | 2.44 |
| NH today | 12,991 to 38,616 | 16,174 to 31,632 |

**Why ours is the headline.** It makes one checkable claim, and that claim held on years the fit never saw. It allows for a shock the size of 2008. Adam's band is narrower and fits each state's own history, which makes it a useful second view, but it missed most states in the bust. It was tested with its own starting point, so it is shown exactly as tested rather than grafted onto ours.

## Worked example: New Hampshire (`results/NH.json`)

| | 2023 | 2024 | 2025 | Mean | × 5 |
|---|---|---|---|---|---|
| NH state file, all units | 4,555 | 4,965 | 5,030 | 4,850 | **24,250** |

Sum of the ten counties: 24,250 (1 unit 15,253; 2 units 917; 3-4 units 820; 5+ units 7,260). Band: 24,250 × 0.5357 = 12,991 to 24,250 × 1.5924 = 38,616. Each year 2026-2030: 4,850 (band 2,598 to 7,723).

Belknap County: 354, 282 and 423 units in 2023-2025; mean 353 × 5 = 1,765 (band 946 to 2,811).

## Limits

- A no-change continuation, not a business-cycle forecast: a recession or boom outside the 1990-2015 history would fall outside the band.
- Permits are authorisations, not completions; conversions and many ADUs are not counted (Census BPS documentation).
- Connecticut's 2016-2022 county figures are an allocation to planning regions (decision 51).
