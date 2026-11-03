# Parking scenario: no minimum parking requirements for new homes

Code: `src/hre/model/scenarios/parking.py`. Register ids: `builder_response_override`,
`parking_required_spaces`, `parking_built_share`, `parking_cost_per_space`, `new_home_price_ratio`,
`parking_low_density_factor`; NZLUD `parking_median` per metro from the processed input.

**The formula on the slide:** permits = baseline 5+ permits × builder response × (required spaces
× (1 − share still built) × cost per space ÷ new-home price) × density factor.

## Steps

1. **Required spaces:** the metro's NZLUD `parking_median` (the mean over its municipalities of
   the median spaces required per home) where the county's CBSA is covered; else 1 per home.
2. **Saving per home:** spaces × (1 − share still built: 0.60 Seattle / 0.79 Buffalo / 1.00 where
   minimums did not bind) × cost per structured space ($29,000 / $52,000 / $73,000, UCLA 2026).
   Surface parking costs are not modeled; where parking is cheap surface parking the density factor
   carries the difference (decision 71).
3. **Price:** county median value × 1.25 (new homes sell above the median home).
4. **Response:** the measured builder response, 0 / 0.75 / 2.84% more homes over five years per
   1% cost cut (decisions 61, 67; `builder_response.md`), applied to the baseline's permits in
   buildings of 5 or more homes.
5. **Density factor:** counties outside the central counties of metropolitan areas get 0 / 50% /
   100% of the response (Sohoni and Lee 2025: car-oriented low-density cities changed little).

Outcome `cost_response_proxy`, already in permits (conversion 1). The per-county composite of
elasticities is kept as the **geography check** (`factors.geography_check`): supply-constrained
metros respond less (Rockingham 0.33, Hillsborough 0.43, non-metro 0.48% per 1%).

## New Hampshire, worked

- 7,260 baseline permits in 5+ unit buildings. Hillsborough: NZLUD Manchester-Nashua 1.795 spaces ×
  0.21 × $52,000 = $19,606, which is 3.71% of a $528,312 new home (421,100 × 1.2546); its 2,205
  baseline 5+ permits × 0.75 × 0.0371 = **61 permits**. Rockingham (Boston metro, 1.91 spaces) 58; Strafford (outlying,
  density 0.5) 25. State: **157 permits** (0 to 2,477); total 24,407.
- Adam's v2.0 NH: 0 / 100 / 400, with 1 space per home everywhere and no density factor.
- Grid: `scenarios.parking.grid` has the increment for all 81 combinations of response, share still
  built, cost per space and price ratio, for the front-end's toggles.

## Limits shown with the result

- The builder response is measured for cost changes in general, not for parking; the low end is no response.
- Where parking is cheap surface parking, builders keep building it; counties outside metropolitan
  cores get half the response at mid.
- Results are statewide; the model does not say which places will build.
