# Parcel adapters: state data that replaces a national count where the two agree

Code: `src/hre/adapters/` (`base.py` the contract and the tolerance rule, `arcgis.py` the count
queries, `registry.py`, one module and one rules file per state in `rules/`). Decision 39.

## What an adapter does

The ADU and missing-middle estimates start from the number of detached single-family homes in
each county, which the national pipeline takes from the American Community Survey (ACS B25024,
a survey estimate). Some states and counties publish parcel data that count single-family lots
directly. An adapter brings that count in, county by county, under three rules:

1. **Counts only.** The adapter asks the parcel service to do the counting (an ArcGIS query with
   grouped or distinct counts) and receives one number per county. It never requests parcel rows,
   owner names, mailing addresses or street addresses, and nothing but the counts is written to
   disk (`data/processed/{st}_parcels_summary.json`). Several of these services do carry owner and
   mailing fields (Pinal and Maricopa in Arizona, New Hampshire's CAMA table); the query never names them.
2. **The tolerance rule.** A county's parcel count replaces the ACS count only when the two are
   within 30% of each other. Otherwise the ACS count stays and the county is listed under
   `excluded_counties` with its ratio. A source that covers half a county, or codes homes
   differently, cannot move a state result by itself.
3. **Provenance in the state file.** `hre build` writes an `adapter` block into
   `data/processed/{ST}.json`: the sources (dataset, area, selection rule, licence text,
   documentation URL, access date), each county's ACS count, parcel count and ratio, which counties
   changed, and which were excluded and why. Each changed county also carries a note.

```
uv run hre fetch --state UT     # runs the count query (one request), writes the summary and data/manifests/ut_hui.json
uv run hre build --state UT     # applies it: "parcel adapter: 7 counties from parcels, 3 kept ACS"
```

## The three states

| State | Source | Selection rule | Licence | Status |
|---|---|---|---|---|
| Utah | Housing Unit Inventory (WFRC, MAG, UGRC) | type and subtype `single_family`, one feature per parcel | CC BY 4.0 | used |
| Arizona | Maricopa County Assessor parcels; Pinal County TaxParcels | Arizona Department of Revenue use codes 0100 to 0179, distinct parcel numbers | none stated ("free to download" is not a licence; Maricopa bars commercial resale) | used, county totals only |
| New Hampshire | NH Parcel Mosaic CAMA table (DRA via GRANIT) | state land use code 11, Single Family Home | none stated; "estimation/planning purposes only" | **disabled** until GRANIT confirms that county counts may be published |

All three rules are ported from Adam Ruege's v2.0 `parcel_sources` records and were re-run against
the live services on 2026-11-03; his county counts reproduce (Utah exactly; Maricopa 1,220,587
against his 1,220,654 and Pinal 161,927 against 161,932, the services having been updated since).

## The 30% rule, re-derived on these states

| County | ACS detached | Parcel count | Ratio | Decision |
|---|---|---|---|---|
| Davis, UT | 90,107 | 88,083 | 0.98 | parcels |
| Morgan, UT | 3,667 | 3,686 | 1.01 | parcels |
| Salt Lake, UT | 268,749 | 240,491 | 0.89 | parcels |
| Tooele, UT | 20,167 | 21,749 | 1.08 | parcels |
| Utah, UT | 135,062 | 147,317 | 1.09 | parcels |
| Washington, UT | 60,218 | 53,794 | 0.89 | parcels |
| Weber, UT | 70,800 | 67,197 | 0.95 | parcels |
| Box Elder, UT | 16,376 | 8,903 | 0.54 | ACS (the inventory covers part of the county) |
| Summit, UT | 16,654 | 568 | 0.03 | ACS (partial coverage) |
| Wasatch, UT | 12,415 | 222 | 0.02 | ACS (partial coverage) |
| Maricopa, AZ | 1,209,586 | 1,220,587 | 1.01 | parcels |
| Pinal, AZ | 141,489 | 161,927 | 1.14 | parcels |

Every county the source covers in full lies within 15% of the ACS (0.89 to 1.14); every partly
covered county is at 0.54 or below. Any threshold between 15% and 46% sorts them the same way, so
30%, in the middle of that gap, is kept. Adam's New Hampshire counts (his payload, not re-run here
because of the terms question) ran 0.82 to 0.96, inside the rule.

## Why New Hampshire is not used yet

The CAMA table states no licence; its only terms are that the data are "for estimation/planning
purposes only and are not intended for legal use". Ten derived county counts published in a public
repository may be fine under that, but the owner (the NH Department of Revenue Administration)
has not said so. The adapter is written and tested, `rules/nh.yaml` has `enabled: false`, and
`hre fetch` refuses to query while it is off. The email asking GRANIT is in
`docs/evidence/nh_granit_terms.md`; the reply goes there too. Until then New Hampshire uses the
ACS in all ten counties, and the website's data page says so.

## Adding a state in under an hour

1. Find a parcel or housing-unit service that covers whole counties and has a land-use or
   structure-type field. Read its licence and terms; record them word for word.
2. Write `src/hre/adapters/rules/{st}.yaml`:

```yaml
state: XX
enabled: true
tolerance: 0.30
layer: https://example.gov/arcgis/rest/services/Parcels/FeatureServer/0
where: "LANDUSE = 'SFR'"
group_by: COUNTY_NAME
sources:
  - dataset: "Example County Assessor parcels"
    area: "the counties it covers"
    rule: "land use SFR, one feature per parcel"
    license_text: "exact words of the licence or terms"
    documentation_url: https://example.gov/about-the-data
    accessed: "YYYY-MM-DD"
```

3. Add a three-line `fetch` module (copy `ut.py` for a grouped count by county, `az.py` for one
   count query per county) and register it in `registry.py`.
4. `uv run hre fetch --state XX && uv run hre build --state XX`; read the ratios it prints.
5. Add the manifest's title to `SOURCE_TITLES` and the state to `ONLY_FOR` in `src/hre/export.py`
   (the data page lists the source), commit, and regenerate the bundle.

Tests (`tests/test_adapters.py`): the tolerance rule, a dummy adapter's round trip through the
state file and its schema, a summary with an unknown county failing loudly, every rules file
declaring its sources and naming no owner or mailing field, and Utah's rules on a cached sample.
