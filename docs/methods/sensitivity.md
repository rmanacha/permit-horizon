# Sensitivity: which assumption moves the result most

Code: `src/hre/model/sensitivity.py`. Every parameter is in `src/hre/assumptions/parameters.yaml` with a low, mid and high end and display text for each.

Low, mid and high are **assumption sets**, not probabilities (decision 32). There is no Monte Carlo: drawing thousands of samples from judgment ranges would print percentiles that look like probabilities the evidence cannot support.

## Tornado (one at a time)

Start with every parameter at mid. Swing one parameter to its low end, then its high end, others at mid; record the result at each end. Bars are ordered by the size of the swing, largest first, ties by parameter id, so the order never changes between runs. Parameters that do not move the result are left out, and so are fixed entries (rules, bounds).

## Joint favorable and unfavorable cases

Set every parameter at once to the end that raised the result in its own swing (favorable), or the end that lowered it (unfavorable). With the engine's multiplicative formulas the favorable case is at least as large as any single swing. It is an illustration of the extreme, not a likely outcome.

## Worked example (the fee formula, `tests/test_sensitivity.py`)

    homes = 10,000 × response × 25,000 × pass-through ÷ (400,000 × price ratio)

At mid: 10,000 × 0.75 × 25,000 × 1.2 ÷ (400,000 × 1.2546) = 448.

| Parameter | At low | At high | Swing |
|---|---|---|---|
| Builder response (0 / 0.75 / 2.84) | 0 | 1,698 | 1,698 |
| Fee pass-through (1.0 / 1.2 / 1.66) | 374 | 620 | 246 |
| New-home price ratio (1.00 / 1.25 / 1.57) | 563 | 357 | 205 |

Joint favorable: response 2.84, pass-through 1.66, price ratio 1.00: 10,000 × 2.84 × 25,000 × 1.66 ÷ 400,000 = 2,947. Joint unfavorable: response 0, so 0.

Phase 3 runs the tornado and joint cases for each scenario's five-year increment and stores them in the results file (`tornado[]`, `joint{favorable, unfavorable}`).

## Which assumptions move in the low and high sets (Phase 3, decision 72)

Each scenario names its **band** parameters, the ones that carry the source evidence's range:
the source rate with its paired ramp (ADU tier rates and ramp, missing-middle rate and ramp,
TOD rate and ramp) or the builder response (parking, fees). Only these move in the low and
high sets; every other parameter (single-family-only share, code penalty, spaces still built,
cost per space, price ratio, conversion factors, gamma) stays at mid there and is explored in
the tornado and the joint cases. So the three views nest: the tornado shows one assumption at a
time, the band shows the evidence range, and the joint favorable and unfavorable cases show
every assumption at its extreme at once (always at least as wide as the band; a property test
checks it). Adam Ruege's v2.0 reads the same way (NH parking high 400, joint favorable 1,300).
