# ADU scenario: one accessory dwelling unit by right on every single-family lot

Code: `src/hre/model/scenarios/adu.py`. Register ids: `adu_rate_tier_1..5`, `adu_value_bound_1..4`,
`adu_overlay_seattle`, `adu_overlay_maine`, `ramp_adu`, `adu_permits_per_completion`.

**The formula on the slide:** ADUs completed = detached homes × tier rate × 5 years; increment =
that × newly affected share × ramp; permits = increment × HCD permits per completion.

## The three layers

| Layer | Unit | How |
|---|---|---|
| Benchmark | completed ADUs (`completed_homes`) | ACS single-family detached homes × the completion rate of California cities in the county's home-value tier (HCD APR Table A2 2023-2025, `tiers.md`) × 5 |
| Increment | completed ADUs, then permits | benchmark by year × (1 − current strength) × the ADU ramp (25/40/55/70/85% at mid); × HCD permits per completed ADU (1.00 / 1.18 / 1.40) |
| Total | permits | baseline + increment, low with low, high with high |

**Overlays (decision 33; rule decision 71).** In the high set a central metropolitan county takes the
larger of its tier high and Seattle's plateau (5.8 permits per 1,000 single-family homes, 0.0049
completions after ÷ 1.18); in the low set every county takes the smaller of its tier low and Maine's
first year (0.95 per 1,000, 0.00081 as completions). Seattle's rate was measured in a dense central
city, so rural counties keep their tier high.

**Market adjustment = 1.0**: the tiers already depend on home values. **Design modifiers** (owner
occupancy, ADU fees, discretionary review) are not separate factors: the benchmark uses the
challenge's terms, and a state's own rules enter through the current-law strength (decision 71).

## New Hampshire, worked (results run 2026-11-03)

- Exposure 410,440 detached homes. Nine counties are tier 1 (mid 0.0619% a year), Rockingham
  ($497,500) tier 2 (0.159%): Rockingham 89,774 × 0.00159 × 5 = 714 ADUs; the state benchmark is
  **420 / 1,707 / 6,135** completed ADUs (low / mid / high; the high includes the Seattle overlay in
  Hillsborough and Rockingham, the central counties).
- Current law: RSA 674:72 already provides three of the four benchmark features, so strength 0.75
  and a newly affected share of 0.25 (decision 62, human review pending).
- Increment at mid: 1,707 ÷ 5 × 0.25 × (0.25 + 0.40 + 0.55 + 0.70 + 0.85) = 235 completed ADUs;
  × 1.18 = **277 permits** (41 to 1,556; the joint favorable case, every assumption at its best end, is 1,846). Total **24,527** permits at mid.
- The assumption that moves it most: the tier 1 rate (0.011% to 0.132% a year gives 140 to 750).
- Adam Ruege's v2.0 NH benchmark was 700 / 2,000 / 4,700 with his tier rates (tier 1 mid 0.083%
  against our 0.062%, de-duplicated completions; `tiers.md`).

## Limits shown with the result

- The Census Building Permits Survey undercounts ADUs (conversions and many attached units are not
  new-building permits), so the baseline and this increment are not measured the same way.
- Rates come from California cities and, at the high end, Seattle; uptake elsewhere may be slower.
- Results are statewide; the model does not say which places will build.
- In a state with a statewide ADU law the baseline already carries current-law ADUs; the newly
  affected share removes that part.
