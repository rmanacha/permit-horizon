# Fee scenario: development and impact fees cut in half

Code: `src/hre/model/scenarios/fees.py`. Register ids: `total_fee_per_unit`, `fee_cut_share`,
`builder_response_override`, `new_home_price_ratio`, `actual_fee_per_unit`; diagnostics
`stock_supply_elasticity`, `stock_realization_share`.

**The formula on the slide:** permits = baseline permits × builder response × (fee cut ÷ new-home
price); fee cut = $50,000 × 50% = $25,000.

## Why the low end is zero

Mayer and Somerville (2000) found the impact-fee coefficient not statistically different from zero,
and Burge and Ihlanfeldt (2006) found that some fees buy the approvals that let building happen; a
fee cut can therefore mean nothing for construction. The mid (0.75% per 1%) is Mayer and
Somerville's price response read over five years; the high (2.84%) is Baum-Snow and Han's unit
elasticity 0.3, half realized within five years, over 5.29% national growth. Both quotes are carried
from Adam's v2.0 record pending access (register citation).

**No pass-through on top.** The response is defined per 1% fall in cost relative to the new-home
price (decision 61), so the fee pass-through (NAHB $1.20 per $1) belongs to the composite route only.

## New Hampshire, worked

- 24,250 baseline permits. Hillsborough: $25,000 ÷ $528,312 = 4.73%; × 0.75 = 3.55% of its 4,810
  permits ≈ 171. State: **934 permits** (0 to 3,535; joint favorable 4,435); total 25,184.
- **Reproducing Adam's number:** with his inputs (22,690 permits, statewide median $402,500 × 1.2546)
  the same formula gives 22,690 × 0.75 × 25,000 ÷ 504,977 = **842**, his published mid
  (`tests/test_scenarios.py::test_fees_reproduce_adams_nh_number`). Ours is higher because our
  baseline is the 3-year mean of permits (24,250, not his 22,690 address-count pace) and each county
  uses its own price (cheaper counties respond more per dollar).
- **Actual-fee variant:** half of NAHB's national average fee ($13,627 ÷ 2 = $6,814) gives 254 permits
  at mid (0 to 963): few places charge $50,000.
- **Stock route (diagnostic):** housing stock × 0.3 × 0.5 × cut ÷ price = 5,228 homes, 5.6 times the
  flow route. It applies a long-run stock elasticity to the whole housing stock rather than to five
  years of building, which is why it is shown for comparison only.

## Limits shown with the result

- The low end is zero: Mayer and Somerville found no significant impact-fee effect, and some fees
  buy the approvals that let building happen (Burge and Ihlanfeldt).
- Few places charge $50,000; with a typical actual fee the cut is about a quarter as large.
- Results are statewide; the model does not say which places will build.
