# Data Provenance

Every dataset Permit Horizon uses, where it comes from, which release we hold,
under what terms, what we did to it, and what it cannot tell you. The code
licence (Apache-2.0) does not relicense any of this data; each row carries its
own terms. No raw data is committed: `data/manifests/<source>.json` records the
URL, SHA-256, size, fetch time and vintage of every file we downloaded, and
`hre fetch` reproduces the download (see `data/README.md`).

Access date for every row: **2026-11-03** (first full fetch), unless noted.
Every source is a keyless public download; no API key or account is required.

# Dataset Inventory

| Dataset | Source | Version / vintage | Access date | License / terms | Category |
| ------- | ------ | ----------------- | ----------- | --------------- | -------- |
| Building Permits Survey, county and state annual files | U.S. Census Bureau, `https://www2.census.gov/econ/bps/County/co{YYYY}a.txt` and `.../State/st{YYYY}a.txt` | county 2016-2025, state 1990-2025 (2025 posted 2026-05-14) | 2026-11-03 | U.S. government work, public domain; no licence statement published | public |
| American Community Survey 5-year, table-based summary files B25001, B25002, B25003, B25004, B25024, B25034, B25064, B25077 and the geography file | U.S. Census Bureau, `https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-{table}.dat` | 2020-2024 (2024 release) | 2026-11-03 | public domain; catalog entry tagged CC0 1.0 | public |
| Population Estimates, housing units by county | U.S. Census Bureau, `https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU.xlsx` | Vintage 2025 (July 1 2020 to July 1 2025) | 2026-11-03 | public domain | public |
| New Residential Construction, annual units authorized and completed (United States, by units in structure) | U.S. Census Bureau, `https://www.census.gov/construction/nrc/xls/permits_cust.xlsx`, `comps_permits_cust.xlsx`, `comps_cust.xlsx` | annual series through 2025 | 2026-11-03 | public domain | public |
| Address Count Listing Files (block-level housing-unit counts from the Master Address File) | U.S. Census Bureau, `https://www2.census.gov/geo/pvs/addcountlisting/{year}/{FIPS}_{State}_AddressBlockCountList_{mmyyyy}.txt` | 062022, 072023, 122023, 072024, 122024, 072025, 122025, 072026 | 2026-11-03 | public domain | public |
| 2020 centers of population by block group | U.S. Census Bureau, `https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/CenPop2020_Mean_BG{SS}.txt` | 2020 Census | 2026-11-03 | public domain | public |
| Gazetteer, counties | U.S. Census Bureau, `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_counties_national.zip` | 2025 | 2026-11-03 | public domain | public |
| Core-based statistical area delineation | OMB Bulletin 23-01 via Census, `https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx` | July 2023 | 2026-11-03 | public domain | public |
| House Price Index, county, annual, all-transactions | Federal Housing Finance Agency, `https://www.fhfa.gov/hpi/download/annual/hpi_at_county.xlsx` | through 2025 (updated 2026-03-31) | 2026-11-03 | freely available; cite "Source: FHFA HPI". **This product uses FHFA data but is neither endorsed nor certified by FHFA.** "FHFA HPI" is a registered trademark and is not part of our product name | public |
| National Transit Map, stops | Bureau of Transportation Statistics (NTAD), `https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0` | feeds compiled September 2026 (per-stop `download_date` in the manifest) | 2026-11-03 | public domain for 1,237 of 1,239 agency feeds, CC-BY-3.0 US for 2; attribution to BTS/NTAD | public |
| National Transit Database, annual service by mode | U.S. DOT, `https://data.transportation.gov/resource/wwdp-t4re.json` | report year 2024 | 2026-11-03 | public domain | public |
| National Zoning and Land Use Database (NZLUD), metro and municipal tables | Mleczko and Desmond, `https://github.com/mtmleczko/nzlud` (`nzlud_msa.csv`, `nzlud_muni.csv`) | 2019-2022 survey, repository main branch | 2026-11-03 | MIT | third-party (academic) |
| Housing Element Annual Progress Report, Table A2 | California HCD via data.ca.gov, `https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/fe505d9b-8c36-42ba-ba30-08bc4f34e022/download/tablea2.csv` | resource last modified 2026-10-30 (report years 2018-2025) | 2026-11-03 | data.ca.gov shows "License not specified"; HCD's APR data page states the data are public with no restrictions on use; provenance retained | public (state) |
| Synthetic demo state `ZZ` | this repository, `scripts/make_sample_zz.py` | n/a | n/a | Apache-2.0 (invented numbers, no real place) | team-created |

Tables B25004 (vacancy status) and B25034 (year built) are downloaded and
cached for later phases but no field of the processed file is built from them yet.

# Cleaning and Preparation

All steps are code in `src/hre/data/` (one module per source) and
`src/hre/build/build_state_inputs.py`; the output is `data/processed/{ST}.json`
(fields in `docs/methods/schema.md`). Geographic codes are kept as zero-padded
strings throughout; every join is on FIPS or GEOID, never on names, except the
PEP spreadsheet, which has no codes and is joined by accent-stripped name.

**Building Permits Survey.** The two header rows and blank row are skipped; the
"estimates with imputation" block (reported plus the Census imputation for
non-responding places) is used; units, not buildings or valuation, are kept for
1, 2, 3-4 and 5+ unit structures. The share of units in 5+ buildings over the
latest five years is computed per county. **Connecticut**: BPS reported the
eight legacy counties through 2022 and the nine planning regions from 2023; for
2016-2022 the statewide legacy total, by structure type, is allocated to each
planning region in proportion to its share of the 2023-2025 statewide total,
with the rounding remainder given to the largest region, and the county notes
say so. A county with no row in a year (no permit-issuing place reported) is
recorded as absent, not zero, with a note.

**ACS.** Files are streamed line by line and only rows for the requested state
and summary level are kept (county, block group; places for California).
Jam values (negative sentinels for "not available") become null. Units in
structure: detached, attached, 2 to 4 (columns 4 and 5 summed), 5 or more
(columns 6 to 9 summed), mobile; boats, RVs and vans are not stored. Margins of
error are not stored.

**PEP.** Rows with a leading dot are counties; the April 1 2020 base column is
dropped and the July 1 estimates for 2020 to 2025 are kept.

**Address Count Listing Files.** Summed from blocks to counties for each
vintage, with the header normalised (the 2026 file uses underscores; the 2022
file has extra group-quarters columns). See "Known Limitations" for the
doubling finding and the decision it forced.

**Centers of population.** The four code columns are concatenated to a 12-digit
block-group GEOID; latitude, longitude and 2020 population are kept.

**Transit.** Every stop in a bounding box 1.5 degrees around the state's
county internal points is saved; at build time a stop is "major" when its GTFS
route types include 0 (tram, streetcar, light rail), 1 (subway), 2 (rail) or 4
(ferry) and its location type is a stop, platform or station (entrances,
nodes and boarding areas dropped). Distance from each block group's center of
population to the nearest major stop is the haversine great-circle distance in
statute miles. Method and limits: `docs/methods/transit.md`.

**OMB delineation.** County to CBSA, with `metro_role` "central" or "outlying"
only inside metropolitan statistical areas; micropolitan counties are "none".

**FHFA HPI.** Five title rows skipped; FIPS zero-padded; years 2015-2025 kept;
blank or "." cells dropped. The index is the county's own series with base 100
at its first recorded year.

**NZLUD.** Metro values (`parking_median`, `parking_mode`, `adu`,
`min_lot_size`, `responses`) are attached to each county's CBSA code. NZLUD
uses 2010 CBSA codes; codes that changed by 2023 do not match and the state
notes list them. The metro file has no multifamily-share column.

**HCD Table A2 (California ADUs).** Only rows with `UNIT_CAT == "ADU"` are
used, and only the aggregate columns (entitlements, building permits,
certificates of occupancy, the data dictionary's "Number of Units Issued
Certificates of Occupancy"); street addresses and coordinates stay in the raw
cache and never enter an output. **De-duplication rule**, because a project is
re-reported in every year it has activity and often re-reported at the same
stage (9 to 23 percent of ADU rows per year repeat an earlier row):

1. Project key = (jurisdiction, APN) when an APN is present; otherwise
   (jurisdiction, local tracking id); otherwise (jurisdiction, street address);
   rows with none of the three are kept as unique.
2. Within one report year, rows with the same key are summed (two ADUs on one
   lot are two units).
3. Across years, each key contributes its entitlement units once (first report
   year with entitlements > 0), its permit units once (first year with permits
   > 0) and its completion units once (first year with completions > 0). Later
   repeats are dropped.

Effect on the statewide series (this vintage; raw = summed by report year):

| Report year | Permitted, raw | Permitted, de-duplicated | Completed, raw | Completed, de-duplicated |
|---|---|---|---|---|
| 2018 | 9,008 | 9,008 | 3,316 | 3,316 |
| 2019 | 15,086 | 13,100 | 6,428 | 6,357 |
| 2020 | 16,041 | 12,957 | 8,601 | 8,221 |
| 2021 | 24,640 | 20,731 | 10,806 | 10,304 |
| 2022 | 31,805 | 25,294 | 15,000 | 13,842 |
| 2023 | 35,720 | 27,749 | 18,548 | 17,532 |
| 2024 | 39,074 | 29,647 | 21,470 | 20,017 |
| 2025 | 41,973 | 31,228 | 24,416 | 22,526 |

HCD's own ADU handbook reports 30,354 ADU permits for 2024; the de-duplicated
figure is 2.3 percent below it and the raw figure 29 percent above it. The
2025 report year is provisional (jurisdictions revise). The output
`data/processed/CA_hcd_adu.json` carries both series per jurisdiction-year.

**New Residential Construction.** Only the `Annual` sheet's United States columns are read
(thousands of units; `(NA)` becomes missing). Completions per permit = cumulative completions ÷
cumulative permits over 1995-2024 and 2010-2024, with completions in permit-issuing areas so
that both sides cover the same places as our BPS baseline; all-area completions are reported
beside them. The 2-4 unit completion series is shown but not used: the Survey of Construction
reclassifies townhouses that permit offices filed as multifamily into one-unit structures
(Census, "Data Relationships between Permits, Starts, and Completions"). Output:
`docs/evidence/completions_per_permit.md` and three register entries (`hre validate --nrc`).

# Known Limitations

**Address Count Listing Files read double from July 2023 on.** Verified on
2026-11-03 for every state: the published `TOTAL HOUSING UNITS` column in the
June 2022 file equals the 2020 Census housing-unit count (New Hampshire
638,795), but from the July 2023 file on it sums to roughly twice the state's
housing stock (New Hampshire 1,295,974 in July 2023 and 1,334,294 in July
2026, against Census Population Estimates of 653,193 and about 667,000). We
computed, for every state and vintage, the ratio of the published total to the
PEP housing-unit estimate for the same date (July files exact; December files
interpolated; July 2026 extrapolated one year beyond PEP). Rule set in advance
(Phase 1 brief, decision 28): store the series divided by two only if every
state's ratio from July 2023 on is 2.0 ± 0.05; otherwise store nothing.
Result: the ratio is not a constant 2.0. It starts well below 2 in fast-growing
states and rises toward 2.0 by 2026 (Utah 1.894 in July 2023, 2.001 in July
2026; Arizona 1.938 to 1.991; New Hampshire 1.984 to 2.001; California 1.970
to 1.993). Across all 50 states and DC, 37 pass the band and 14 do not: the July 2023 ratio runs from 1.894 (Utah) to 2.013 (West Virginia), and by July 2026 from 1.979 (South Dakota) to 2.110 (DC), low where housing grows fastest and above 2 where it grows slowest, while the June 2022 file matches the 2020 Census count in every state (ratio 0.94 to 1.00 against the 2022 estimate) A series whose halved value lags the estimated
stock by up to five percent and then catches up would overstate recent growth
exactly where growth is fastest, so **the series is excluded from
`data/processed/{ST}.json` for every state** (`address_units` is empty and the
state notes say why). The full ratio tables are in
`docs/evidence/aclf_ratio_check.md` (NH, UT, AZ, CA) and
`docs/evidence/aclf_ratio_check_all_states.md`; the check reruns with
`make validate-aclf`. The July 2023 and July 2024 files also exclude transitory
units. If the Census Bureau documents the change in what the column counts,
the decision can be revisited by setting `SERIES_APPROVED` in
`src/hre/data/fetch_aclf.py` after rerunning the check.

**Permits are not homes.** BPS counts units authorised by permits; some are
never built, and conversions and many ADUs are never permitted as new units.
Non-permit areas are excluded (under one percent of units nationally, more in
some states). Non-respondents are imputed. Names are truncated to 30
characters, so joins use FIPS.

**Connecticut's 2023 geography change** (above) means its 2016-2022 county
permits are an allocation, not an observation.

**ACS block-group estimates carry large margins of error.** They are used only
summed over many block groups (homes within half a mile of a major stop),
never singly. Block groups are 2020 geography; the 2020-2024 ACS uses the same
geography, and for New Hampshire and Utah every center-of-population block
group has an ACS row.

**Block-group land area is not available** without the TIGER shapefiles we
chose not to download (decision 36); `land_sqmi` is null for block groups and
present for counties.

**Transit:** bus rapid transit cannot be identified in GTFS and is not
counted; service frequency is unknown; only stops in current feeds appear.
Details in `docs/methods/transit.md`.

**FHFA county HPI** is developmental, all-transactions, not seasonally
adjusted, and blank for small counties in early years.

**NZLUD** is a natural-language extraction from zoning codes, thin outside the
2006 Wharton survey metros, keyed by 2010 CBSA codes, and has no multifamily
share at the metro level.

**PEP housing-unit estimates are built partly from building permits**, so
they are not independent of BPS; they are used as stock denominators and as the
reference in the address-count check, not as an outcome.

**HCD Table A2** is self-reported by jurisdictions; the latest report year is
provisional; counties and cities are separate jurisdictions (Los Angeles
County is the unincorporated area, not the county total).

# Restricted, Sensitive, or Personal Data

No dataset in Phase 1 involves individuals or households. The processed files
hold county and block-group aggregates from published Census tables. HCD
Table A2 lists projects with street addresses and coordinates; only
jurisdiction-year sums of ADU units leave the raw cache, and the raw file is
never committed. No parcel data is used yet; when parcel adapters arrive
(Phase 5), owner and mailing columns are dropped at ingest and only counts are
written, as the working agreement requires.

# Excluded Sources

Considered and rejected on licence or access grounds (details in the planning
workspace, `research/data_sources.md`):

- **National Zoning Atlas**: terms bar downloading, reproduction and
  scraping; bulk data is sold. Replaced by NZLUD (MIT).
- **HUD aggregated USPS vacancy data**: registered users only, "proprietary
  USPS data". Replaced by ACS vacancy tables.
- **Transitland API**: non-commercial licence and quotas. Replaced by the
  National Transit Map.
- **Legacy Microsoft building footprints**: ODbL (share-alike). Not needed.
- **Tennessee statewide parcels**: automated downloads prohibited.
- **Wharton Residential Land Use Regulation Index 2018**: no stated terms;
  not redistributed.
- **Impact-fee schedules**: no open national dataset; fees are a user-supplied
  parameter with a documented default (Phase 2).
- **Census API**: requires a key since May 2026; every table we need exists as
  a keyless bulk file, so the key is not used.
