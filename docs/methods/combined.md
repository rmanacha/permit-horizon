# Combined package: "if all five passed together (illustration)"

Code: `src/hre/model/combine.py`. Results: the top-level `combined` block of every results
file in which all five scenarios ran.

## Why it exists, and why it is labeled an illustration

Legislators ask what happens if a bill does all of it. No study has measured these five reforms
together, so the package is an arithmetic illustration with explicit overlap rules, not a
forecast. A teammate's earlier prototype (Adam Ruege's Housing Reform Estimator v2.0) does not
combine reforms at all and says so ("the results cannot be added across reforms"); the results
file quotes that in `combined.limits`.

## Rules (applied at the same assumption set: low with low, mid with mid, high with high)

1. **Transit first.** Detached homes in block groups within the TOD distance of a rail, streetcar
   or ferry stop, in central metropolitan counties, leave the missing-middle exposure: those lots
   are counted under transit-oriented density.
2. **Missing middle before ADUs.** Lots redeveloped as middle housing (the scenario's net units
   divided by Portland's 3.35 units per lot, register `mm_units_per_lot`) leave the ADU exposure.
3. **One builder response for parking and fees.** On an apartment permit the parking saving and
   the fee cut are one cost cut, and the response is applied once. The response is proportional
   to the cut, so this equals parking plus fees exactly; the rule is stated so nobody counts the
   saving twice or applies the response to a product of the two.
4. **Totals only in permits.** Each scenario's converted increment is added; native units
   (completed homes, stock change, net permits) are never added to one another.

The code asserts that the package is never larger than the sum of the parts, and the results
validator checks it again.

## Worked example: New Hampshire (results run 2026-11-03)

| Set | ADU | Missing middle | TOD | Parking | Fees | Sum of parts | Package |
|---|---|---|---|---|---|---|---|
| Low | 34.8 | 0 | 0 | 0 | 0 | 34.8 | 34.8 |
| Mid, alone | 276.9 | 1,034.9 | 3.0 | 157.3 | 933.5 | 2,405.6 | |
| Mid, in the package | 276.6 | 1,033.1 | 3.0 | 157.3 | 933.5 | | **2,403.6** |
| High, alone | 1,846.5 | 2,518.9 | 34.7 | 2,476.6 | 4,435.0 | 11,311.6 | |
| High, in the package | 1,840.9 | 2,514.7 | 34.7 | 2,476.6 | 4,435.0 | | **11,301.9** |

At mid, rule 1 moves 302 detached homes near New Hampshire's few rail and ferry stops out of the
missing-middle exposure (1,034.9 to 1,033.1 permits), and rule 2 removes about 308 redeveloped
lots from the 410,440 detached homes that could add an ADU (276.9 to 276.6). The overlap is small
in New Hampshire because little housing sits near rail; in a state with large transit-served
central counties rule 1 moves far more. Rules 3 and 4 change nothing numerically and exist so the
sum is done in one unit and the cost cut is counted once.
