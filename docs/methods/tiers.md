# ADU completion rates by home-value tier

Code: `src/hre/model/tiers.py` (lookup), `src/hre/validation/calibrate_adu_tiers.py` (calibration). Evidence: `docs/evidence/adu_tiers.md`. Parameters: `adu_value_bound_1..4`, `adu_rate_tier_1..5`. Rebuild: `make hcd` then `hre validate --adu-tiers --write-register`.

**Idea (decision 33):** under one state law, California cities where homes are worth more completed more ADUs per detached home. A county anywhere gets the rate of California cities with a similar median home value.

## Formula

1. Cities: the 457 California cities in HCD Table A2's de-duplicated ADU rows (decision 50) with an ACS 2020-2024 median value, Los Angeles left out.
2. Bounds: the 20th, 40th, 60th and 80th percentiles of city median values: **$430,100; $618,840; $825,060; $1,160,300**.
3. Mid rate per tier = tier completions 2023-2025 ÷ (3 × tier detached homes).
4. Low and high = mid × (first-quartile city rate ÷ median city rate), and mid × (third-quartile ÷ median).
5. A county is in tier *k* when its median value is at most bound *k* (tier 5 above bound 4). A county with no median value uses tier 3 and gets a note.

| Tier | Median value | Low | Mid | High |
|---|---|---|---|---|
| 1 | up to $430,100 | 0.011% | 0.062% | 0.132% |
| 2 | $430,100 to $618,840 | 0.056% | 0.159% | 0.455% |
| 3 | $618,840 to $825,060 | 0.119% | 0.244% | 0.421% |
| 4 | $825,060 to $1,160,300 | 0.157% | 0.256% | 0.483% |
| 5 | above $1,160,300 | 0.132% | 0.271% | 0.379% |

Rates are ADUs completed per detached home per year. Tier 1's arithmetic (all tiers are in the register's `citation`): 92 cities, 1,424 completions over 767,389 detached homes: 1,424 ÷ (3 × 767,389) = 0.000619 a year.

## Worked example: New Hampshire

Nine counties are in tier 1 (median values $188,900 to $421,100) and Rockingham ($497,500) is in tier 2. Detached homes (ACS B25024): 320,666 in tier-1 counties, 89,774 in Rockingham.

    tier 1: 320,666 × 0.000619 × 5 =   992
    tier 2:  89,774 × 0.001591 × 5 =   714
    NH benchmark, mid                = 1,707 ADUs completed over five years (low 420, high 4,167)

This is the benchmark layer (what California's rates would produce on NH's detached homes). Phase 3 subtracts what NH's current law already allows (current strength 0.75, `src/hre/current_law/NH.yaml`) and applies the ramp. Adam's v2.0 gave 700 / 2,000 / 4,700 with his tier rates.

## Check: fit on half the cities, test on the other half

1,000 random halves (Los Angeles never in the fit). Without Los Angeles, the held-out half's actual 2023-2025 completions were inside the low-high range in **1,000 of 1,000** splits (median 0.99 times the mid). With Los Angeles in the pool, **975 of 1,000** (median 1.21); the misses come from Los Angeles, which completed ADUs at 0.914% a year, about three times its tier. Adam's run: 953 and 1,000. This checks calibration inside California; transfer to other states is tested by the frozen Seattle and Maine holdouts in Phase 5.

## Limits

California's law is mature and its prices are high; other states start slower (the ramp) and the Seattle plateau and Maine first year bracket the range in Phase 3. Detached homes are not eligible lots. City tiers describe an association, not a causal effect of value.
