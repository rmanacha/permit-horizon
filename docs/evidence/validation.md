# Validation: every check of the model, hits and misses

Generated 2026-11-03 by `uv run hre validate --ledger` from `validation/ledger.yaml` (the same entries the website's Validation page shows). Frozen checks keep their protocol and hash in `validation/<check>/`; `tests/test_ledger.py` recomputes every hit and miss and re-hashes every protocol.

| Check | Evidence class | Place and years | Outcome | Model low / mid / high | Actual | Result |
|---|---|---|---|---|---|---|
| Baseline range, forecasts made in 2016 to 2020 | Historical check | 50 states and DC, forecast origins 2016-2020, outcomes through 2025 | five-year building permit totals that fell inside the baseline range (runs inside, of 255; the range promises at least 80% (204)) | 204 to 255 | 251 of 255 (98%) | hit |
| Baseline range, forecasts made in the 2005 to 2010 bust | Historical check | 50 states and DC, forecast origins 2005-2010 | five-year building permit totals that fell inside the baseline range (runs inside, of 306; the range promises at least 80% (245)) | 245 to 306 | 172 of 306 (56%) | miss |
| Baseline range, forecasts made in the 2011 to 2015 recovery | Historical check | 50 states and DC, forecast origins 2011-2015 | five-year building permit totals that fell inside the baseline range (runs inside, of 255; the range promises at least 80% (204)) | 204 to 255 | 190 of 255 (75%) | miss |
| Baseline range refitted each year with only the data available then | Historical check | 50 states and DC, forecast origins 2000-2020 | five-year building permit totals inside a range refitted each year on closed windows only (runs inside, of 1,071; the method promises 80% (857)) | 857 to 1,071 | 656 of 1,071 (61%) | miss |
| The 20-year swing range (Adam Ruege's rule), side by side | Historical check | 50 states and DC, Adam's 255 runs; and forecast origins 2016-2020 | five-year permit totals inside the slowest-to-fastest range of each state's prior 20 years (runs inside, of 255) | none | 181 of 255 (71%); 87% on origins 2016-2020 | not a test |
| ADU rates by home value, California city splits | Calibration, not a test | 457 California cities, ADU completions 2023-2025 | a held-out half of the cities' completions inside the low-to-high range fitted on the other half (splits inside, of 1,000) | none | 1,000 of 1,000 without Los Angeles; 975 with it | not a test |
| Seattle ADU completions, Adam Ruege's frozen check | Frozen holdout | Seattle, Washington, 2023-2025 | new attached and detached ADUs on finaled permits, by completion year (ADUs a year) | 206 / 361 / 644 | 851, 845 and 945 (880 a year) | miss |
| Austin ADU permits, frozen before the count was fetched | Frozen holdout | Austin, Texas, 2023-2025 | building permits for new secondary apartments (ADUs), city full-purpose jurisdiction, by year issued (ADU permits a year) | 139 / 394 / 1,217 | 247, 93 and 10 (117 a year) | miss |
| 2026 building permits in every state, frozen before they are published | Prospective holdout, outcome not yet published | 50 states and DC, 2026 | housing units authorized by building permits in 2026, each state inside its published 2026 range (states inside their 2026 range, of 51; a hit needs at least 41 (80%)) | 41 to 51 | not yet published (expected in the first half of 2027) | pending |
| Seattle's plateau as the ADU high case | Calibration, not a test | Seattle, Washington, 2022-2023 plateau | ADU permits per single-family home a year at the plateau (permits per 1,000 single-family homes a year) | none | 5.8 | not a test |
| Maine's first statewide year as the ADU low case | Calibration, not a test | Maine, 2025 | ADU permits in the first full year of the statewide law (permits per 1,000 single-family homes a year) | none | 0.95 (about 525 permits, 7% of the state's 2025 permits) | not a test |
| Missing-middle rates and the cities they came from | Calibration context | Portland, Minneapolis, Arlington, Spokane, Austin, Charlotte, 2020-2025 | middle-housing units permitted per 1,000 detached homes a year (units per 1,000 detached homes a year) | none | 0.3 to 0.6 (Minneapolis, Arlington); 1.8 to 2.0 (Spokane, Austin, Charlotte); 3.5 to 4 (Portland) | not a test |
| Parking, fees and transit density: borrowed responses | Borrowed from studies, no test | Studies elsewhere (national builder-response estimates; Los Angeles for transit), various | homes added per 1% cost cut; housing added near transit (see each method page) | none | not yet | not a test |

Totals: 1 hit, 5 miss, 1 pending, 6 not a test.

## What each check shows and does not

### Baseline range, forecasts made in 2016 to 2020

251 of 255 five-year totals fell inside the range, against the 80% it promises; 3 were above it and 1 below.

- Independence: The range's two numbers were fitted on forecasts made in 1990 to 2015; these later forecasts were never used in the fit. Their outcomes were already published, so this is a historical holdout, not a blind one.
- Supports: The range holds the size of a typical five-year surprise in recent years.
- Does not support: That the range will hold through a turn in the market (see the 2005-2010 row), or anything about the reforms.
- Next check: The 2026 permit totals, frozen before they are published.
- Source: [Baseline backtest (docs/evidence/baseline_backtest.md)](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/baseline_backtest.md)

### Baseline range, forecasts made in the 2005 to 2010 bust

Only 56% of the forecasts made in the bust held the real total; 125 of the 134 misses were below the range, because a range fitted on history does not foresee a collapse.

- Independence: These forecasts are inside the period the range was fitted on, so this measures how coverage moves with the market, not an out-of-sample test.
- Supports: A plain warning shown beside every baseline: in a downturn the real total can fall below the range.
- Does not support: A probability that 2026-2030 lands inside the range.
- Next check: Watch the 2026 totals against the range.
- Source: [Baseline backtest, coverage by period](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/baseline_backtest.md)

### Baseline range, forecasts made in the 2011 to 2015 recovery

75% of the forecasts made in the recovery held the real total, just short of the promise; 63 of the 65 misses were above the range.

- Independence: In the fitting period; shown for how coverage moves with the market.
- Supports: The range errs in both directions when the market turns.
- Does not support: A probability for the forecast period.
- Next check: The 2026 totals.
- Source: [Baseline backtest, coverage by period](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/baseline_backtest.md)

### Baseline range refitted each year with only the data available then

Built the way a forecaster in each year could have built it, the range held 61% of totals, and under 5% of the forecasts made in 2005 to 2008.

- Independence: Each year's range uses only five-year windows that had closed by then.
- Supports: A sober reading of the headline range: it describes past surprises, and a forecaster without hindsight would have been surprised more often.
- Does not support: A coverage promise for 2026-2030.
- Next check: The 2026 totals.
- Source: [Baseline backtest, real-time test](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/baseline_backtest.md)

### The 20-year swing range (Adam Ruege's rule), side by side

Reproduced exactly from Adam's design: 181 of 255 inside, 37 above, 37 below. It promises no fixed coverage, so it is shown beside the headline range rather than scored against a promise.

- Independence: A second way to draw the range on the same history.
- Supports: The trade-off between a wide range that rarely misses and a tight one that follows each state's own swings.
- Does not support: Choosing between them on one test window.
- Next check: Both rules on the 2026 totals.
- Source: [Baseline backtest, rule B](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/baseline_backtest.md)
- Credit: Rule designed by Adam Ruege (Housing Reform Estimator v2.0); his counts reproduced in this repository.

### ADU rates by home value, California city splits

The range holds a held-out half of California's cities every time without Los Angeles; when Los Angeles, about three times its tier's rate, lands in the held-out half, the total can exceed the high.

- Independence: The rates come from these cities, so this checks stability inside California, not transfer to other states.
- Supports: The tier rates are stable across random halves of California.
- Does not support: Accuracy in other states, or how many ADUs a new law adds.
- Next check: A frozen holdout outside California.
- Source: [ADU tiers and city-split check (docs/evidence/adu_tiers.md)](https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/adu_tiers.md)
- Credit: Split design from Adam Ruege's v2.0 (953 of 1,000 with Los Angeles in his version).

### Seattle ADU completions, Adam Ruege's frozen check

Seattle completed more than twice the middle estimate in each of the three years, and above the high every year (pooled 2,641 against 619 to 1,931). A city with Seattle's program outruns California's typical rate; this miss is why the high set now takes Seattle's plateau in central metropolitan counties, so Seattle is a calibration source from then on.

- Independence: Seattle outcomes were unused in Adam's calibration; his geography, years, outcome, denominator and predictions were frozen and hashed before he retrieved them. A convenience-selected retrospective holdout, not a pre-registered forecast.
- Supports: An honest transfer miss for a strong local ADU program.
- Does not support: A causal law effect, a statewide increment over current law, or a single correction factor.
- Next check: A frozen holdout in a place neither model has used (below).
- Source: [City of Seattle, detached ADU layer (and the attached ADU layer)](https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Detached_Accessory_Dwelling_Units_(DADUs)/FeatureServer/0)
- Frozen: `Adam Ruege's v2.0 archive: validation/seattle_adu_2023_2025/protocol.json (not in this repository)`, SHA-256 `b2a1649b5bc2c74c018321279f90dc866d4b89e88bb16f1fd554ee654dbf4259`
- Credit: Designed, frozen and run by Adam Ruege (Housing Reform Estimator v2.0, October 2026). His archive is not in this repository, so the hash is recorded as he reported it.

### Austin ADU permits, frozen before the count was fetched

A miss on the frozen rule: 117 permits a year against a range of 139 to 1,217. The first year, 2023 (247 permits), was inside the range at 0.63 times the middle; 2024 and 2025 fell far below it. The fall coincides with Austin's 2024 changes to its residential code, so the permit class frozen in advance may have stopped capturing ADUs; that has not been checked, and the score stands as frozen. A corrected outcome definition would be a new check, not a re-score.

- Independence: Austin was used in no ADU number in the model or in Adam's version. The place, years, outcome rule and prediction (the ADU scenario's own code on Austin's ACS detached homes and median value) were hashed and published before the counts were fetched; only the dataset's column names and category lists were read beforehand.
- Supports: An honest record that a California-rate benchmark sits above what one Texas city permitted, at least in the frozen permit class.
- Does not support: A conclusion about Texas, a causal effect of a state law, or a new rate; the outcome definition itself is in doubt for 2024 and 2025.
- Next check: A second frozen check in Austin with a definition that follows the 2024 code (all new units on lots with an existing house), and one in another state.
- Source: [City of Austin, Issued Construction Permits (public domain)](https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu)
- Frozen: `validation/austin_adu_2023_2025/protocol.json`, SHA-256 `a936174a1f8b321806c6fc648d6610a1ac82350c47db9a13e1d29db232fcfce9`, committed in `199a908`

### 2026 building permits in every state, frozen before they are published

Every state's 2026 low, middle and high (national middle 1,470,510 permits) was hashed and published on 2026-11-03, before any 2026 annual total existed. The range was built for five-year totals, so one year is a harsher test; that was written into the protocol in advance.

- Independence: Fully blind: the outcome did not exist when the prediction was frozen.
- Supports: When scored, a clean out-of-sample test of the baseline's first year.
- Does not support: Anything about the reforms.
- Next check: Score it when the Census publishes the 2026 annual file.
- Source: [Census Building Permits Survey, annual state file for 2026](https://www2.census.gov/econ/bps/State/)
- Frozen: `validation/bps_2026_states/protocol.json`, SHA-256 `d54a5013e7fb771f87e978a94f70cc636023bb77b339d476c7208cb40ccf85fc`, committed in `199a908`

### Seattle's plateau as the ADU high case

The high set uses this rate in central metropolitan counties where it exceeds the tier's high, so Seattle shapes the high case and cannot also test it.

- Independence: Used to set a register value.
- Supports: A high case that a strong program has actually reached.
- Does not support: That other cities will reach it.
- Next check: The frozen holdout below.
- Source: [Seattle OPCD ADU annual report, 2024](https://www.seattle.gov/documents/Departments/OPCD/OngoingInitiatives/EncouragingBackyardCottages/OPCD-ADUAnnualReport2024.pdf)

### Maine's first statewide year as the ADU low case

The low set uses this rate wherever it is below the tier's low, so Maine shapes the low case and cannot also test it.

- Independence: Used to set a register value.
- Supports: A low case taken from a real first year of a statewide law.
- Does not support: Later years in Maine or other states.
- Next check: Maine 2026, when published.
- Source: [Maine State Housing Authority, permit data blog](https://www.mainestatehousingdata.org/permits/blog)

### Missing-middle rates and the cities they came from

The middle rate is Portland's first year net of demolitions (1.7 per 1,000 a year) and the high is Portland's ceiling, so these cities are where the numbers came from; Minneapolis and Arlington show how low the outcome can be when other rules bind.

- Independence: Calibration sources and their neighbors; no frozen test yet.
- Supports: The range spans the outcomes measured so far.
- Does not support: A test of transfer, or completions.
- Next check: A city whose 2026-2027 middle-housing permits are frozen before they are published.
- Source: [Missing-middle method (docs/methods/missing_middle.md)](https://github.com/rmanacha/permit-horizon/blob/main/docs/methods/missing_middle.md)

### Parking, fees and transit density: borrowed responses

These three reforms use responses measured in other settings; no statewide outcome exists to test them against, and the tornado shows how much each assumption moves the result.

- Independence: None: borrowed estimates.
- Supports: A transparent mechanism with its sensitivity shown.
- Does not support: A validated statewide effect of any of the three reforms.
- Next check: A measured fee or parking change with a comparison group.
- Source: [Builder response method (docs/methods/builder_response.md)](https://github.com/rmanacha/permit-horizon/blob/main/docs/methods/builder_response.md)

<!-- narrative below is written by hand; hre validate --ledger keeps it -->
## Narrative (written 2026-11-04, Phase 5)

**Which checks prove what.** Only three checks were fixed in advance of their outcome. The 2026
state totals are fully blind: the outcome did not exist when every state's range was hashed and
published, and it will be scored in 2027. Austin was frozen and published before its count was
fetched, and nothing in the model came from Austin's ADUs. Adam Ruege's Seattle check was frozen
by him the same way for his version of the model. Everything else in the ledger is either a test
on history whose outcome was already known (the baseline rows) or a calibration source, which is
labeled as such because a number cannot test the place it came from.

**The baseline range.** On forecasts the fit never saw (2016-2020), 251 of 255 five-year totals
fell inside, against the 80% the range promises. But the same range held only 56% of the
forecasts made in the 2005-2010 bust and 75% in the recovery, and a forecaster refitting it each
year without hindsight would have held 61%. The range describes the size of past surprises; it
is not a probability, and in a turning market the real total can fall outside it. The website
says this beside every baseline.

**The two frozen ADU checks miss in opposite directions.** Seattle completed 880 ADUs a year in
2023-2025 against a middle of 361 (above the high every year). Austin issued 117 ADU permits a
year in the frozen permit class against a middle of 394 (below the low; the first year, 247, was
inside at 0.63 times the middle). A California-rate benchmark sits between a city with a strong
ADU program and one where local rules still bind. That is what the benchmark is meant to be (what
the source policy produced, moved to another place), and it is why the increment over current law,
not the benchmark, is the policy number. What the misses say about the range: the high case now
takes Seattle's plateau in central metropolitan counties (so Seattle is calibration from then on),
and the low case does not reach Austin's later years. Austin's 2024 and 2025 counts may also
reflect a change in how Austin classifies these permits after its 2024 code changes; that was not
checked, and the frozen score stands.

**No parameter was changed after these checks** (decision 96). The brief's rule is to change a
register value only when a check shows it clearly off, then relabel that check as calibration and
reserve another test, and never to tune to one city. Two frozen ADU checks that disagree in
direction, one with an outcome definition in doubt, are not grounds to move the tier rates.

**What would change the picture.** The 2026 state totals (2027). A second Austin check with an
outcome rule that follows its 2024 code (every new home on a lot with an existing house), frozen
before it is fetched. Maine's 2026 ADU permits, once the state reports them. A frozen
missing-middle check in a city whose 2026-2027 permits are not yet published.
