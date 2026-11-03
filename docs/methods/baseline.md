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

The alternative rule (Adam Ruege's v2.0: the slowest and fastest five-year totals of the prior 20 years, each over their average) is reproduced and compared in the backtest: 181 of 255 inside on his origins, 87% on the 2016-2020 origins with a narrower band.

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
