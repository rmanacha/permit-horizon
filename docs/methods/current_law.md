# Current law: what each state's statutes already do

Code: `src/hre/current_law/` (`schema.py` the rules, `loader.py` what the engine reads,
`coverage.py` the coverage arithmetic). Files: `src/hre/current_law/{ST}.yaml`, one per state,
blank form `_template.yaml`. Evidence: `docs/evidence/current_law_coverage.md`
(`uv run hre validate --law-coverage`).

## Why the register exists

Each reform has a **benchmark**: what the reform would produce if it were new everywhere. A
state that already has part of the reform in law gets only the rest of it. The **current
strength** is that part, a number from 0 (nothing in law) to 1 (the whole benchmark in law), and
the **increment over current law** is the benchmark times the newly affected share, 1 minus the
strength. Think of it as a dimmer switch: a state whose law already gives most of the reform
leaves the increment dim; a state with no law leaves it at full brightness.

The strength is never a judgment call typed into a cell. It comes from a feature table a
legislator can check line by line against the statute, the quote and the page it came from.

## Benchmark features, one row each

| Reform | Feature (id) | Benchmark requirement (challenge handbook) |
|---|---|---|
| ADU | one per lot (`adu_per_lot`, the gate) | Allow one ADU on a parcel with an existing single-family building. |
| | forms (`adu_forms`) | Allow detached and semi-detached ADUs. |
| | size (`adu_size`) | Allow ADUs of at least 600 square feet. |
| | parking (`adu_parking`) | Require no added parking for the ADU. |
| Missing middle | parcels (`mm_parcels`, the gate) | Apply the reform to parcels currently limited to single-family use. |
| | units (`mm_units`) | Allow two to six homes on each affected parcel. |
| | height (`mm_height`) | Allow buildings of up to three stories. |
| | envelope (`mm_envelope`) | Setbacks and lot coverage do not prevent two to six homes. |
| Transit-oriented density | density (`tod_density`, the gate) | Increase permitted height, floor area ratio, or both near major transit stops. |
| | geography (`tod_geography`) | Define major transit stops and justify the distance. |
| | parking (`tod_parking`) | Parking requirements near transit reduced or removed. |
| Parking | minimums (`parking_minimum`, the gate) | Reduce or remove parking minimums for new residential development. |
| | provision (`parking_provision`) | How much parking builders provide without a mandate. |
| Fees | level (`fees_level`) | Total fees of $50,000 per home for the comparison. |
| | cut (`fees_cut`, the gate) | Reduce total fees by 50%. |
| | categories (`fees_categories`) | Planning, environmental review, building and impact fees. |

The feature rows and ids are Adam Ruege's v2.0 schema (decision 38); his records seed the ADU
files and carry `ported_from: adam-v2.0` with a re-check date.

## Status of each feature

- `supported_with_limits`: the statute delivers the requirement, with limits written in the
  row (an owner-occupancy option, a lot-size floor, places not covered). The limits are shown
  beside the status on the website.
- `differs`: the statute does not deliver it (allows one added parking space where the
  benchmark requires none; allows two floors where it requires three), or no statute addresses it.
- `not_yet_effective`: enacted, with an effective date after 2030 or not yet fixed. A law that
  takes effect inside the 2026-2030 horizon instead carries its substantive status and
  `in_effect_from`, and counts for the share of the horizon it is in force.
- `unknown`: the text does not settle it, or the row is a modeling assumption rather than a
  legal rule (parking provision, the fee level).

## The strength rule (decisions 62 and 91)

```
strength = gate x feature share x coverage share
```

1. **Gate.** Each reform has one core feature (marked above). If it is not supported, nothing of
   the reform is in law and the strength is 0, whatever the other rows say. This is why a statute
   that lets towns allow ADUs but requires none scores 0, and why Utah's definition of station
   areas does not count without a density rule to apply in them.
2. **Feature share.** Every feature counts equally: 1 when supported with limits (times the share
   of 2026-2030 it is in force), 0 otherwise. This is the starting rule the planning window set in
   decision 62; New Hampshire's ADU law has three of four features, 0.75.
3. **Coverage share.** The share of the state's detached single-family homes inside the places
   the law binds (ACS 2020-2024), 1 when it binds every city, town and county. Arizona's ADU law
   binds cities and towns over 75,000 people and the areas outside any city: 79.89% of the
   state's 2,048,854 detached homes.

Worked: Arizona ADUs, 4 of 4 features × 0.7989 = 0.80; Utah ADUs, 2 of 4 × 1 = 0.50; New
Hampshire ADUs, 3 of 4 × 1 = 0.75; Arizona middle housing, 3 of 4 × 0.0523 = 0.04.

**Quantified strengths.** When a reform is a quantity rather than a list of permissions, a file
may store `strength_method: quantified` with the arithmetic in `strength_arithmetic`. The one
case so far is a parking cap: the parking estimate removes each county's required spaces per
home, so a statewide cap at one space has already removed the share 1 - 1/spaces of the
benchmark. New Hampshire: 0.43 (decision 93). The feature rule would have said 0.50.

**Rubric bands as a cross-check.** The brief's rubric (by-right statewide and equivalent 0.9 to
1.0; statewide with material limits 0.4 to 0.8; enabling or partial 0.1 to 0.3; none 0) is used
to check the rule's result, not to set it. Two systematic departures, both on purpose: an
enabling-only statute scores 0, not 0.1 to 0.3, because it requires nothing (the gate); and a law
that reaches few homes can fall below its band (Arizona middle housing, 0.04, at most 5% of homes).

## Coverage, measured

`coverage.rule` in a state file names the jurisdictions the law binds, and
`hre validate --law-coverage` recomputes the share from the cache and fails when it differs from
the stored `coverage.share`. The keys (all in `src/hre/current_law/coverage.py`):

| Key | Meaning | Used by |
|---|---|---|
| `above_population`, `min_population` | incorporated places over (or at least) a population | AZ, ID, NC, NV, OR, CO |
| `places: all / none` | every incorporated place, or none | AR, MA, MT, WV |
| `unincorporated: all / cdp / none` | land outside cities; `cdp` counts census-designated places only, a stand-in for unincorporated urban areas (growth boundaries) | AZ, NV, MA, CT; CO, OR, WA |
| `cdp_min_population`, `county_min_population` | only CDPs, or only counties, of that size | CO; NV, OR |
| `counties` | restrict everything to listed counties | CO (metropolitan planning areas), WA (Growth Management Act counties) |
| `county_in_effect_from` | counties the law reaches only later count their share of 2026-2030 | WA |
| `exclude_places`, `exclude_subdivisions` | named cities, or towns that opted out | MA (Boston), NC (coastal cities); CT (115 towns) |
| `exclude_tribal` | homes on tribal land | AZ, NV, CT |
| `near_downtown_miles` | upper bound for a rule that reaches only land near downtown | AZ middle housing | Places are Census places; a "CDP" is unincorporated and counts
with the areas outside cities. When a statute uses the decennial census for its threshold (Arizona,
A.R.S. 1-215), the ACS 2020-2024 set of places is compared with the 2020 Census set in the basis
text. A rule that reaches only the area near each downtown is an upper bound: a circle of radius
the rule's reach plus one mile at the place's average density of detached homes.

Where the census geography cannot express a law exactly, the file says which way the figure
leans (decision 95): CDPs stand in for urban growth areas (an over-count where rural CDPs lie
outside them), a county list over-counts towns outside a planning boundary, and Virginia's
exemption for localities with an earlier ordinance is not subtracted (an upper bound).
Connecticut's opt-out list is the only one that exists, an advocacy group's 2023 survey; no state
agency collected one. The denominator is always the state's detached homes, although the
missing-middle estimate is exposed only in central metropolitan counties; for a middle-housing law
the share of *exposed* homes the law reaches is therefore a little higher. In Arizona it is 5.46%
of the 1,963,420 exposed homes against 5.23% of all 2,048,854, and the strength is 0.04 either way;
the gap errs toward a larger increment. If a later state makes it material, use the scenario's
exposed stock as the denominator.

Limits: the share is statewide, so the engine applies one strength to every county; a county
with mostly uncovered towns gets the state's average. Local ordinances that go further than the
statute are not counted anywhere: the register measures state law only, and every card says so.

## Every quote is checked against its page

`uv run hre validate --law-quotes --fetch` fetches every cited page once and searches for each
quote word for word (`docs/evidence/current_law_quotes.md`); statutes published as PDFs are read
with the optional `law` extra (pypdf, decision 94). Three official sites cannot be read by a
script: California's leginfo refuses scripted requests, Indiana's code site draws its text with
JavaScript, and Connecticut's certificate chain fails Python's TLS check. Their quotes were read
by hand and are recorded with date and method in `docs/evidence/current_law_hand_checks.yaml`;
the check reports them as "checked by hand", never as found.

## What the website shows

The Scenario page prints the record (law, summary, quote with a link, in effect), the feature
table with limits and sources, and "Current strength X, so Y is newly affected" followed by
`strength_rationale` verbatim. That text, the feature rows and the record are written for
legislators: plain sentences, no decision numbers, no ids (a test rejects them). Internal notes
go in `notes` or in YAML comments, which the page never shows. A state or reform with no file
reads "No statewide law found; local permissions unverified." and strength 0.

## Review checklist (a policy teammate signs `human_review`)

For each reform in the file:

1. Open every source link; the quote appears on the page and the locator points to it.
2. The law citation, chapter number and effective dates match the official page.
3. Each feature's status follows the rules above; the limits name what the text does not deliver.
4. Coverage: the places the statute binds match the rule (population threshold and its census
   year, counties, exclusions).
5. The strength equals the rule (the tests enforce the arithmetic) or the quantified arithmetic
   is right and its reason is stated.
6. The rationale reads as plain sentences a legislator would accept.
7. Search for later amendments (the state legislature's session laws for 2025 and 2026).

Then set `human_review: {status: reviewed, by: <name>, date: <YYYY-MM-DD>}`; the card then
shows "reviewed by <name> on <date>". Nothing is marked reviewed by the software.

## Adding a state

Copy `_template.yaml` to `{ST}.yaml`, fill one reform from the official statute page, run
`uv run pytest -q tests/test_current_law.py` (schema, rule, plain text), commit, then regenerate
the bundle (`make results-all export` from a clean checkout) and commit it on its own. The
staleness test fails CI until the bundle is regenerated.
