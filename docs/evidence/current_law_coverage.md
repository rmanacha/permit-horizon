# Current-law coverage: the share of detached homes a statewide law binds

Generated 2026-11-03 by `uv run hre validate --law-coverage` from the cached ACS 2020-2024 5-year files (B25024 detached homes, B01003 population; places, places by county, and American Indian areas by state) and the 2025 place Gazetteer. Method: `docs/methods/current_law.md`; code: `src/hre/current_law/coverage.py`.

| State | Reform | Rule | Arithmetic | Share | Stored | Match |
|---|---|---|---|---|---|---|
| AZ | adu | above_population 75000, unincorporated all, exclude_tribal True | 1,203,063 detached homes in 15 covered places + 433,794 outside incorporated places (after removing 46,822 on tribal land) = 79.9% of 2,048,854 | 0.7989 | 0.7989 | yes |
| AZ | missing_middle | min_population 75000, unincorporated none, near_downtown_miles 1 | 107,133 detached homes in 15 covered places = 5.2% of 2,048,854 | 0.0523 | 0.0523 | yes |

## Largest places on each side of the line

- **AZ adu**: covered: Phoenix city (1,642,323 people, 390,242 homes); Tucson city (547,073 people, 128,374 homes); Mesa city (511,764 people, 122,978 homes); Gilbert town (280,262 people, 82,000 homes); Chandler city (280,136 people, 76,175 homes). Not covered: Lake Havasu City city (58,359 people, 27,055 homes); Maricopa city (67,163 people, 22,396 homes); Queen Creek town (71,867 people, 22,226 homes); Marana town (56,938 people, 20,671 homes); Oro Valley town (48,162 people, 17,534 homes).
- **AZ missing_middle**: covered: Phoenix city (1,642,323 people, 390,242 homes); Tucson city (547,073 people, 128,374 homes); Mesa city (511,764 people, 122,978 homes); Gilbert town (280,262 people, 82,000 homes); Chandler city (280,136 people, 76,175 homes). Not covered: Lake Havasu City city (58,359 people, 27,055 homes); Maricopa city (67,163 people, 22,396 homes); Queen Creek town (71,867 people, 22,226 homes); Marana town (56,938 people, 20,671 homes); Oro Valley town (48,162 people, 17,534 homes).

Notes: a place whose Census name ends in "CDP" is unincorporated and is counted with the areas outside cities and towns. Tribal areas are assumed to lie outside incorporated places. A downtown rule's figure is an upper bound (see the rule's basis in the state file).
