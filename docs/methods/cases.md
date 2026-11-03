# Cases: what is new under current law

Code: `src/hre/model/cases.py`, `src/hre/current_law/`. Parameters: `ramp_adu`, `ramp_immediate`, `horizon_years`.

Every scenario has three layers (decision 30): the **benchmark** (source rate × exposure × 5 years, in the source's own unit), the **increment** over current law, and the **total** (baseline + increment, Phase 3). This module computes the increment.

## Formula

    increment in year k = newly affected share × benchmark in year k × ramp[k − delay]   (zero before the delay ends)
    newly affected share (register default) = 1 − current_strength from current_law/{ST}.yaml

A state with no statewide law on file has strength 0, so the whole benchmark counts, with the note "No statewide law found; local permissions unverified." (decision 31).

## Named cases

| Case | Share | Delay | Ramp | Status |
|---|---|---|---|---|
| `register_default` | 1 − current strength | 0 | the scenario's ramp (ADU: 25/40/55/70/85% mid) | `register_default` |
| `no_change` | 0 | | | `assumed_zero` |
| `after_horizon` | 1 | 5 years | | `assumed_zero` |
| `eligible_25/50/100_delay_0/1/2` | 25, 50 or 100% | 0, 1 or 2 years | none: the source rate right after the delay | `user_case` |

Low, mid and high pair like with like: the low benchmark with the low ramp. Each case carries its assumptions as plain sentences, its outcome label, and `can_add_to_baseline`, which is true only when the outcome is permits (the headline unit).

## Worked examples

- Delay only (Adam's case): NH ADU benchmark middle 2,046.2 over five years is 409.2 a year; a 1-year delay leaves 4 × 409.2 = **1,637.0**.
- Register default for NH ADUs: three of four benchmark features (one ADU per lot, attached or detached, at least 600 sq ft) are already in RSA 674:72, the fourth (no added parking) differs, so strength = 3 ÷ 4 = 0.75 and the newly affected share is 0.25. With a benchmark of 100 a year and the mid ramp: 0.25 × 100 × (0.25 + 0.40 + 0.55 + 0.70 + 0.85) = **68.75**.
- Hand case: 50% affected, 2-year delay, mid ramp, 100 a year: years 3-5 get 0.5 × 100 × 0.25, 0.40, 0.55 = 12.5 + 20 + 27.5 = **60**.

## The current-law register

Per state and scenario: the statute record (law, summary, quote, URL, access date, effective date), a feature-by-feature comparison with the challenge benchmark (`supported_with_limits`, `differs`, `not_yet_effective`, `unknown`, each with sources and quotes), `current_strength` with its rationale, and `human_review`. Template: `src/hre/current_law/_template.yaml`. Starting rule for the strength (decision 62): the share of benchmark features supported with limits; a file may differ only with a stated reason. NH's ADU entry is seeded from Adam Ruege's v2.0 record and was re-checked against the statute on 2026-11-03; human review is pending. Phase 5 fills ADU for every state and all five scenarios for UT, NH and AZ.
