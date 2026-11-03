# Transit-oriented density: more homes allowed near rail, streetcar and ferry stops

Code: `src/hre/model/scenarios/tod.py`. Register ids: `tod_rate_per_home`, `tod_distance_miles`,
`tod_source_city_value`, `value_ratio_exponent`, `market_adjustment_bounds`, `ramp_tod`,
`completions_per_permit_5plus`; diagnostic `tod_boundary_rate`.

**The formula on the slide:** stock change = homes within half a mile of a rail or ferry stop ×
rate per home × 5 years; increment = that × market adjustment × newly affected share × ramp;
permits = homes ÷ 0.79.

## Stops and distance

A major stop is a National Transit Map stop served by tram, streetcar or light rail, subway, rail or
ferry (decision 48); bus rapid transit cannot be identified and is not counted. Exposure = housing
units in block groups whose 2020 center of population is within the distance of a stop: 0.5 mile
(Massachusetts 40A §3A, FTA's 15-minute walk, Los Angeles's program), 0.25 mile in the low set.

**SB 79 tiers (documented, not modeled).** California's SB 79 (effective July 1, 2026) sets a TOD
zone within ½ mile of a stop with standards by tier: within 200 feet, Tier 1 (heavy rail) 95 ft /
160 units per acre / FAR 4.5 and Tier 2 (light rail, BRT) 85 ft / 140 / 4.0; within ¼ mile 75 / 120
/ 3.5 and 65 / 100 / 3.0; ¼ to ½ mile 65 / 100 / 3.0 and 55 / 80 / 2.5 (MTC summary, April 2026).
The model's quarter-mile low set corresponds to SB 79's inner tier; the rates do not vary by tier
because no study measures production by tier.

## The three layers

| Layer | Unit | How |
|---|---|---|
| Benchmark | homes added to the stock (`stock_change`) | homes near stops × rate per home a year (0 Chicago / 0.0117% Kestelman LA citywide / 0.133% Stacy et al.) × 5 |
| Increment | homes, then permits | × market adjustment (county value ÷ Los Angeles's $921,200, γ 0.5, bounds 0.5-1.5) × (1 − current strength) × ramp; ÷ completed homes per permit for 5+ unit buildings (0.79, Census NRC) |
| Total | permits | baseline + increment |

## New Hampshire, worked

- 6,371 homes within half a mile (808 within a quarter mile), in eight block groups, the same
  figure Adam's build found (decision 48).
- Benchmark mid 6,371 × 0.000117 × 5 = **3.7 homes** (0 to 42.5); increment **3 permits** (0 to 35).
- Diagnostic: Kestelman's local boundary rate (0.338% a year, may include relocation) would give
  108 homes; it is not added anywhere.

**Why TOD is near zero in New Hampshire:** the rate is per home near a station, and New Hampshire
has very few homes near rail; the mid rate itself is small because in Los Angeles applications rose
but new supply barely did (Kestelman), and in Chicago permits did not rise at all (Freemark).

## Limits shown with the result

- Bus rapid transit cannot be identified in the National Transit Map, so only rail, streetcar and
  ferry stops count.
- In Los Angeles applications rose sharply but new supply did not (Kestelman); in Chicago permits
  did not rise (Freemark), so the low end is zero.
- Results are statewide; the model does not say which places will build.
