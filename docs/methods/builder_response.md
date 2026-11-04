# Builder response (parking and fees)

Code: `src/hre/model/response.py`. Parameters: `builder_response_override`, `supply_elasticity_metro_default`, `supply_elasticity_nonmetro`, `demand_elasticity`, `fee_pass_through`, `adjustment_share_5yr`, `new_home_price_ratio`, `stock_supply_elasticity`, `stock_realization_share` (and `us_housing_growth_5yr`, the register's denominator for the high end); Saiz table `src/hre/assumptions/elasticities.yaml`.

**What it answers:** how many more homes get built over five years when a reform cuts a builder's cost. The unit is *percent more homes over five years per 1% fall in cost relative to the price of a new home*. An elasticity is already "percent per percent", so a response of 0.75 means a 1% cost cut adds 0.75% to five years' permits.

    additional homes = baseline permits × response × (cost cut ÷ new-home price)
    new-home price   = county median value × new_home_price_ratio (1.25)

## Route 1, primary: the measured response (decision 61)

`builder_response_override`, ported with its locators and arithmetic from Adam Ruege's v2.0:

| Level | Value | Source and arithmetic |
|---|---|---|
| Low | 0 | Mayer and Somerville (2000), p. 653: the impact-fee coefficient is not statistically different from zero |
| Mid | 0.75 | Mayer and Somerville (2000), p. 651: a 1% price rise gives a temporary 15% rise in construction over six quarters, read as 15% of one quarter spread over 20 quarters: 0.15 ÷ 20 = 0.75% of five years' building |
| High | 2.84 | Baum-Snow and Han (2024): unit supply elasticity 0.3, half within five years, over U.S. housing growth of 5.29% (July 2020 to July 2025): 0.3 × 0.5 ÷ 0.0529 = 2.84 |

Why primary: each end is one cited sentence a judge can check, the low end is the null result the evidence actually contains, and the numbers are already in "share of five years' building".

## Route 2, diagnostic: the composite of elasticities

    response = ε_s × |ε_d| ÷ (ε_s + |ε_d|) × pass-through × five-year adjustment share

This is the textbook share of a supply shift that shows up as quantity, times how much of a fee reaches the price (1.2) and how much of the response lands within five years (0.75). ε_s comes from Saiz (2010) Table VI by metro (Salt Lake 0.75, Phoenix 1.61, Boston 0.86), else 1.75 for other metro counties and 3.0 elsewhere; |ε_d| = 0.65 (Albouy, Ehrlich and Liu).

Worked example, a metro county outside Saiz's 95 (Hillsborough NH): 1.75 × 0.65 ÷ 2.40 = 0.474; × 1.2 × 0.75 = **0.43% per 1%**. Rockingham NH (Boston, 0.86): 0.333. Salt Lake (0.75): 0.313. Carroll NH (non-metro, 3.0): 0.481.

Why it is not primary: Saiz's elasticities describe the housing **stock** (1970-2000); reading the composite as a share of five years' **flow** mixes units. It is kept because it shows the geographic pattern (tight metros respond less), and it sits inside route 1's range.

## Route 3, diagnostic: the stock-elasticity route

    stock elasticity × realization share ÷ national five-year growth = 0.3 × 0.5 ÷ 0.0529 = 2.84

This is how route 1's high end is built. Taken alone it says a 1% cost cut adds 2.84% to five years' building, about four times the mid. It is reported as a diagnostic and never widens the band beyond route 1's high.

## Cross-check: Adam's NH fee example

Fee cut $25,000 (half of the challenge's $50,000). NH median value $402,500 (ACS state), new-home price 402,500 × 1.2546 = $504,977, so the cut is 4.95% of the price. Adam's baseline middle 22,690:

    22,690 × 0.75 × 25,000 ÷ 504,977 = 842 additional homes    (his payload: 842.48)

With our permit baseline (24,250) and the same price: 24,250 × 0.75 × 0.0495 = 900. Low = 0; high = 24,250 × 2.84 × 0.0495 = 3,410. `tests/test_response.py` reproduces the 842. Phase 3 applies the formula county by county with each county's median value.

## Limits

No study measures a cut near $25,000 per unit; the range runs from "no response" to a long-run supply response. Fees can also buy off exclusionary rules (Burge and Ihlanfeldt 2006), which this module does not model.
