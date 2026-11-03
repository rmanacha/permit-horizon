# The processed input file: `data/processed/{ST}.json`

`hre build --state NH` writes one JSON file per state. The engine reads only this
file, so it is the whole "data requirement" of the model: a judge who wants to
plug in a different dataset replaces one field here and reruns. The shape is
defined once, in `src/hre/schema.py`, as plain Python dataclasses with a
validator; `hre build` refuses to write a file that fails validation.

Conventions:

- Geographic codes are **strings with leading zeros** (`"01"` Alabama, `"33001"`
  Belknap County NH, `"330019651001"` a block group). Numbers would silently drop
  the zero.
- Year keys are `"2025"`; vintage keys are `"2026-07"` (year-month).
- `null` means "not available for this geography"; `0` means "measured zero".
- Counties are aligned by `fips`; block groups by `geoid`. Every block group's
  `county_fips` must appear in `counties`.
- JSON is written compact with sorted keys, so two builds of the same inputs
  produce byte-identical files.

## Top level (`StateInputs`)

| Field | Meaning | Source |
|---|---|---|
| `state` | USPS code, e.g. `"NH"` | fixed table in `src/hre/data/states.py` |
| `state_fips` | 2-digit FIPS, e.g. `"33"` | same |
| `schema_version` | `"1"` | bumped when a field changes meaning |
| `vintages` | which release of each source went in, e.g. `{"bps": "2025", "acs": "2020-2024 (2024 release)"}` | each fetcher |
| `counties` | list of `CountyInputs` (below), one per county equivalent | |
| `block_groups` | list of `BlockGroupInputs` (below) | |
| `zoning_by_cbsa` | metro-level zoning survey values keyed by CBSA code (NZLUD) | `fetch_nzlud.py` |
| `notes` | state-level caveats in plain English (Connecticut's county break, excluded series) | `build_state_inputs.py` |

## County (`CountyInputs`)

| Field | Meaning | Source and rule |
|---|---|---|
| `fips` | 5-digit county FIPS | Gazetteer |
| `name` | county name | Gazetteer (BPS truncates names to 30 characters, so never join on names) |
| `cbsa`, `cbsa_title`, `cbsa_type` | the core-based statistical area the county belongs to (`"metropolitan"`, `"micropolitan"`, or `null` when outside every CBSA) | OMB July 2023 delineation (`list1_2023.xlsx`) |
| `metro_role` | `"central"` or `"outlying"` **within a metropolitan statistical area**, else `"none"`. Micropolitan counties are `"none"` because the missing-middle scenario transfers a rate measured in metropolitan central counties. | same |
| `permits` | `{"2016": {"u1", "u2", "u34", "u5"}, ...}`: housing units authorised by building permits, by structure size (1 unit, 2 units, 3 to 4 units, 5 or more), "estimates with imputation" block | Census Building Permits Survey county annual files `co{YYYY}a.txt` |
| `permits_5plus_share_5yr` | share of permitted units in 5+ unit buildings over the latest five years with data (the parking-scenario exposure); `null` if the county permitted nothing | computed from `permits` |
| `housing_units_pep` | `{"2020": n, ..., "2025": n}`: July 1 housing-unit estimates | Census Population Estimates `CO-EST2025-HU.xlsx` (the `"2020"` key is the July 1 2020 estimate, not the April 1 base) |
| `address_units` | `{"2022-06": n, "2023-07": n, ...}`: housing units on the Census master address list, summed from blocks. **From July 2023 on the published column is divided by two** (see `docs/DATA_PROVENANCE.md`, "Address Count Listing Files"); when the state fails the ratio check the dictionary is empty and `notes` says why | Census Address Count Listing Files |
| `housing_units` | total housing units (ACS B25001) | ACS 5-year 2020-2024 bulk files |
| `sf_detached`, `sf_attached`, `units_2_4`, `units_5plus`, `mobile` | units in structure: 1 detached; 1 attached; 2 to 4 (B25024 columns 4 + 5); 5 or more (columns 6 to 9); mobile homes (column 10). Boats, RVs and vans (column 11) are not stored | ACS B25024 |
| `owner_occupied`, `renter_occupied` | tenure (B25003 columns 2, 3) | ACS |
| `vacant` | vacant units (B25002 column 3) | ACS |
| `median_value` | median value of owner-occupied units, dollars (B25077) | ACS |
| `median_rent` | median gross rent, dollars (B25064) | ACS |
| `hpi` | `{"2015": x, ..., "2025": x}`: FHFA all-transactions house price index, county, base 100 at the county's first year; years with a missing value are absent | FHFA `hpi_at_county.xlsx` |
| `land_sqmi` | land area in square miles | Gazetteer |
| `supply_elasticity` | `null` in Phase 1; Phase 2 fills it from the register | |
| `parcel_sf_count` | `null` in Phase 1; Phase 5 adapters fill it (counts only, no parcel rows) | |
| `notes` | county-level caveats, e.g. "no permit-issuing place in BPS for 2017" | |

ACS margins of error are not stored. County estimates are reliable; block-group
estimates carry large margins and are used only for the transit-proximity
exposure, where they are summed over many block groups.

## Block group (`BlockGroupInputs`)

| Field | Meaning | Source and rule |
|---|---|---|
| `geoid` | 12-digit block-group code (state 2 + county 3 + tract 6 + block group 1) | 2020 centers of population |
| `county_fips` | first five digits of `geoid` | |
| `pop_center_lat`, `pop_center_lon` | the 2020 **center of population**: the point where the block group's residents balance, which is where a half-mile transit test should be measured from (a geometric centroid of a large rural block group can be miles from anyone) | Census `CenPop2020_Mean_BG{SS}.txt` |
| `population` | 2020 Census population | same file |
| `housing_units`, `sf_detached`, `units_5plus` | as for counties (B25001, B25024) for the block group, 2020-2024 ACS; `null` when the ACS has no row for a 2020 block group | ACS bulk, rows `1500000US...` |
| `land_sqmi` | `null` in Phase 1: the Census publishes no block-group gazetteer, and we chose not to download TIGER shapefiles (decision 36). Add via `pyshp` on the TIGER DBF if a block-group density is ever needed | |
| `dist_major_stop_miles` | great-circle distance from the center of population to the nearest **major transit stop** (rail of any kind, streetcar, ferry; not bus), in statute miles; `null` when the state build found no major stop within its search box | `transit_proximity.py` (haversine, numpy) on National Transit Map stops |
| `near_transit_half_mile`, `near_transit_quarter_mile` | `dist_major_stop_miles <= 0.5` / `<= 0.25`; `false` (not `null`) when no stop exists, because "no rail within half a mile" is a measured fact | same |

## Zoning by CBSA (`zoning_by_cbsa`)

Keyed by 5-digit CBSA code, values from the National Zoning and Land Use
Database metro file (`nzlud_msa.csv`, 2019 survey): `parking_median` (minimum
off-street parking spaces per unit, median across responding municipalities),
`parking_mode`, `adu` (share of municipalities allowing ADUs by right),
`min_lot_size` (share with a minimum lot size rule), `responses` (how many
municipalities answered), `cbsa_name` (as of the 2010 codes NZLUD uses). The
metro file has no multifamily-share column; `mf_per` exists only for
municipalities and is left for Phase 2 to aggregate if needed.

## A real example

A trimmed NH snippet from a real build is in the Phase 1 report
(`planning/phases/reports/phase-1-report.md`); the demo state `ZZ` built by
`make demo` has the same shape with two counties and ten block groups.
