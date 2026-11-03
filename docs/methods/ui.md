# The website: pages, how changes are computed, when to use the command line

The website in `web/` is a static site (Vite 7, React 19, TypeScript, in the Community Solutions design system) that reads the precomputed
results bundle committed in `web/public/results/` (decisions 25 and 74). It has no server and no
Python: the model runs ahead of time (`make results-all export`), and the page only reads its
output. Live copy: https://rmanacha.github.io/permit-horizon/ (deployed by
`.github/workflows/pages.yml` on every push to `main`).

## Run it

| Command | What it does |
|---|---|
| `make run` | Builds the site (when Node 22.18+ is installed) and serves `web/dist` at http://localhost:8080 with Python's `http.server`. Without Node it serves a `web/dist` that already exists, or says how to get one. |
| `make web` | `npm ci` (the exact packages in `web/package-lock.json`), a type check, and `vite build` into `web/dist`. `web/dist` is never committed; CI and Pages build it. |
| `make web-dev` | The development server with live reload at http://localhost:5173. |
| `make test-web` | The web tests (below), then the equality test against `hre run --set`. |
| `docker compose up` | Builds the image (Node builds the site, Python serves it, the engine is installed) and serves http://localhost:8080. Verified in CI on every push (job `docker`). |

## The six pages

Every page reads the same view from the address bar, so a copied link restores it:
`#/<page>?st=NH&sc=adu&case=50-1&set=builder_response_override:high,fee_cut_share:0.3&show=adu,fees`
(state, reform, case, assumption choices, reforms shown).

| Page | What it shows | Bundle keys |
|---|---|---|
| **Explore** | Without a state: every state's baseline and package (from `index.json`). With a state: the baseline card (middle, range, `band_rule.reading` and `reading_history`), the Census housing-unit cross-check (never added), the case picker, five reform cards in three layers (benchmark in its own unit; increment in permits with its status badge, share and delay, the ADU completed-homes equivalent, the current-law note and human-review flag; total), the assumption that moves each result most (`tornado[0]`), the compare table (increments ranked, all in permits; a warning row for every pair whose order flips at the low or high end; the package as an unranked illustration with its rules), and downloads. | `baseline`, `cross_check.housing_units_pep`, `scenarios.*.{benchmark, increment, total, cases, tornado, factors.notes}`, `combined` |
| **Scenario detail** | The formula and exposure; every assumption that moves the result, with low/middle/high controls, a value box where the page can compute any value, its source, locator, grade, confidence and arithmetic; the result under the user's assumptions and how it was computed; the increment by year; the cases table (25/50/100% by 0/1/2-year delay, plus "starts after the five years" and "no change") with each case's assumption sentences; joint favorable and unfavorable cases; the tornado (ADU permits per completion labeled as a unit conversion); what the law already allows (statute, quote, effective date, link, feature table, strength, human review); the parking and fee geography check; diagnostics; limits. | `scenarios.*`, `registers.json` `assumptions` and `current_law` |
| **Assumptions and data** | The full register with level selectors; every data source for the state (vintage, licence, access date, download folders, manifest); parcel data (none in this version); sources downloaded and excluded (the Address Count Listing Files); the county housing-unit estimates with their caveat. | `registers.json` `assumptions`, `sources`; `meta.vintages`; `cross_check` |
| **Methods and limits** | The no-language-model statement (read from `meta.json`), one formula line per estimate, how the page computes changes, what the tool cannot tell you (`docs/methods/limits.md`), the states with current-law files, and the glossary (`docs/GLOSSARY.md`). | `no_llm`, `baseline.method`, `scenarios.*.formula` |
| **Validation** | The backtest: coverage by period (hits, above, below), the real-time test, the history reading; the 20-year swing range under its own heading, never on the headline (decision 69); the validation ledger (empty until Phase 5). | `band_rule.coverage_by_period`, `coverage_realtime`, `baseline.alternative_band`, `registers.json` `validation_ledger` |
| **About** | Team and credits, the build (commit, schema versions, register fingerprint, the state's build id, vintages), how to run it, links to the documents, licence and privacy. | `meta.json`, `meta.build_id` |

A printable one-page brief (`#/brief`) and three downloads (the view as CSV and JSON; the county
table in long form with `outcome` and `caveats` columns) sit on Explore. Downloads are built in
the browser; nothing is sent anywhere.

## Rules the code enforces

- **Every number carries its outcome label** (`permits`, `net permits`, `completed homes`,
  `homes added to the stock`, `cost-response permits`), and numbers with different labels are
  never added or ranked together. Permits come first; a share of the baseline is a secondary
  label only, because it reads high in states that build slowly.
- **One place for styling**: colors, spacing and fonts live only in `web/src/styles/tokens.css`;
  components carry class names, never inline styles (`scripts/style_rules.test.mjs`).
- **The Community Solutions design system** (2026 brand refresh, decision 76): `tokens.css` holds
  its tokens, with the site's own names mapped onto them; Raleway (headings 900, body 400) and
  Asap Condensed Bold (eyebrows, buttons, tags, labels) are self-hosted in `web/public/fonts/`
  from the official Google Fonts files, with their SIL Open Font License texts and a manifest
  (`scripts/fonts.test.mjs` checks every file's SHA-256); the components the pages use (Button, Tag,
  Card, StatCallout, Tabs, Select, Input, Checkbox) are ported to TypeScript in
  `web/src/components/ds/` with their props checked against the system's own declarations
  (`scripts/ds-reference/index.d.ts`, `scripts/ds_props.test.mjs`). Square corners, flat surfaces,
  2px navy form borders, 4px sky rules on section tops and the active tab, a 1200px container.
  Contrast rule: running text is Charcoal or Navy; Sky is for fills, rules and large headings;
  text on bright fills is Navy. No logos, slogans, photography or Biro Script.
- **Charts** (`web/src/components/charts.tsx`): plain SVG, one series per chart (increments in
  Sky, range lines in Navy, a solid baseline), the value as text on every bar, a hover readout,
  and a table view. The palette was checked with the dataviz validator: Sky is 2.3:1 on white and
  Lime too light to read as a mark, so the text labels and table carry the numbers and the
  combined package is tagged in the compare table rather than drawn as a bar (decision 89).
- **Licences**: every npm package, on every platform, must be MIT, ISC, BSD or Apache-2.0
  (`scripts/licenses.test.mjs` reads `package-lock.json`). `npx license-checker --summary` on the
  installed tree on 2026-11-03: MIT 19, Apache-2.0 2, ISC 1, BSD-3-Clause 1 (23 packages, plus the
  site itself, Apache-2.0). Vite 8 is avoided because it requires lightningcss (MPL-2.0).
- **Accessibility basics**: semantic headings and landmarks, a skip link, labels on every control
  (each level button names its assumption and value), visible keyboard focus, a table view for every
  chart, and text beside every bar so color is never the only cue.

## How the page changes an estimate without Python (`web/src/engine/rescale.ts`)

When a user moves an assumption, the page recomputes the middle increment of each reform from what
the engine exported, and labels how:

1. **Multiplicative assumptions, exact.** `components.linear_in` lists the ids each county's
   increment is proportional to; new = Σ county increment × new value ÷ old value, and an id in
   `components.linear_counties` multiplies only the counties listed (parking's density factor
   applies outside central metropolitan counties). Any typed value works. The `components` block
   is written unrounded for this.
2. **Parking and fee grids.** The engine ran every low/mid/high combination of their assumptions
   (81 and 9 cells), so levels are a lookup (exact) and a value between two levels is interpolated
   linearly and labeled **interpolated**.
3. **One other assumption at its low or high end**: the tornado bar, which the engine computed
   exactly, times any multiplicative changes.
4. **Anything else** is not computed in the browser; the page shows the command that computes it,
   for example `uv run hre run --state UT --set builder_response_override=1.2` or
   `--level ramp_adu=high` (repeatable; the results file records the values in `meta.overrides`).

A selected case (share and delay) combines only with multiplicative changes (case × ratio, exact);
the combined package is shown at the register default only.

**Checks.** `web/src/engine/rescale.test.ts` reproduces every tornado bar and all 4,590 grid
cells in the 51 committed state files. `web/scripts/rescale_equality.mjs` (`make test-web`) runs
`hre run` for NH, UT and the demo state ZZ, applies three sets of multiplicative changes in
TypeScript, runs `hre run --set/--level` with the same values and compares every reform: 36
comparisons on 2026-11-03, the largest relative difference 4e-16 (the test allows 1e-9); the
lookup routes agree to the 4 decimals the bundle stores. CI runs ZZ (no processed state files
there); NH and UT run wherever `data/processed/` exists. `tests/test_rescale_contract.py` checks
the same contract inside the Python suite.

## When to use the command line

The page covers the register's low, middle and high values, any value of a multiplicative
assumption, and values between levels for the parking and fee assumptions. For anything else (a
custom ADU rate, two non-multiplicative assumptions at once, a case combined with them), run
`uv run hre run --state XX --set id=value` from a clone after `make setup` and `make data STATE=XX`;
it writes `results/XX.json` with the same layout.

## Where the text comes from

Results sentences come from the bundle (fixed templates in `src/hre/model/drivers.py`). Site
text that is not a result lives in Markdown: the glossary in `docs/GLOSSARY.md` and the limits in
`docs/methods/limits.md`, turned into `web/src/content/*.json` by `cd web && npm run content`
(`scripts/content.test.mjs` fails when they drift). Team, credits and document links are in
`web/src/content/site.ts`.

## Tests (`make test-web`)

| File | What it checks |
|---|---|
| `src/engine/rescale.test.ts` | the rescale reproduces every tornado bar and grid cell in all 51 states; interpolation, typed values, cases, the county-scoped factor, the command text |
| `src/data/bundle.test.ts` | every committed bundle file has the keys and types the site reads |
| `src/lib/viewmodel.test.ts`, `route.test.ts`, `format.test.ts`, `downloads.test.ts` | cases, rankings and flip warnings; share links round-trip; number formats and labels; every download row has an outcome |
| `scripts/style_rules.test.mjs`, `licenses.test.mjs`, `content.test.mjs` | no inline styles or stray colors; permissive licences only; glossary and limits in step with their Markdown |
| `scripts/ds_props.test.mjs`, `fonts.test.mjs` | the design-system port keeps the system's props; the fonts are the manifest's files with their licences |
| `scripts/rescale_equality.mjs` | the page's arithmetic against `hre run --set` |
