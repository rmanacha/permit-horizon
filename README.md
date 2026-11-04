# Permit Horizon

A statewide housing reform estimator. Permit Horizon estimates how many more homes would get building permits over 2026-2030 if a state passed one of five reforms (accessory dwelling units by right, missing middle, transit-oriented density, no parking minimums, development fees cut in half), compared with the laws it has today. It covers all 50 states and DC, gives every number with its unit and a low-to-high range, and shows the source, the page and the arithmetic behind every assumption. Built for state legislators and their staff, for the Housing Data and Technology Innovation Challenge.

**Open it:** https://rmanacha.github.io/permit-horizon/ (no account, nothing to install). Or run it yourself with the three commands below.

Every reform comes out in three layers, each with its unit (its outcome label):

- the **benchmark**: what the reform produced where it was measured, moved to this state, in the source's own unit;
- the **increment over current law**: the part that would be new here, given what the state's statutes already allow, in building permits (the number to compare across reforms);
- the **total**: baseline plus increment.

## A ten-minute tour for reviewers

1. **Every state at once** (1 minute). Open the site: each state's no-change baseline and the five reforms together.
2. **Pick New Hampshire** (2 minutes): [#/explore?st=NH](https://rmanacha.github.io/permit-horizon/#/explore?st=NH). The baseline (24,250 permits over 2026-2030, with its range from history and the Census housing-unit estimates beside it) and a card per reform in three layers.
3. **Compare** (1 minute). Further down the same page, the five increments ranked in permits, with a warning wherever the order changes between the low, middle and high assumption sets.
4. **Change an assumption** (2 minutes): [#/scenario?st=NH&sc=fees&set=builder_response_override:high](https://rmanacha.github.io/permit-horizon/#/scenario?st=NH&sc=fees&set=builder_response_override:high). The fee cut with the builder response at its high end: the increment recomputes exactly in the page (934 to 3,535 permits), the tornado shows which assumption matters most, and every assumption shows its source and arithmetic.
5. **What the law already does** (1 minute): [#/scenario?st=NH&sc=adu](https://rmanacha.github.io/permit-horizon/#/scenario?st=NH&sc=adu). New Hampshire's ADU statute, quoted and linked, feature by feature against the benchmark: strength 0.75, so a quarter of the reform would be new.
6. **Data** (1.5 minutes): [#/data?st=NH](https://rmanacha.github.io/permit-horizon/#/data?st=NH). The full assumption register, every source with its release and licence, and the source we downloaded and then excluded.
7. **Validation** (1.5 minutes): [#/validation](https://rmanacha.github.io/permit-horizon/#/validation). The baseline backtest by period, and every check of the model with hits and misses, including two checks frozen and published before their outcomes were fetched.

Each link restores the exact view, so it can go in an email or a hearing memo. The site is static: it sends nothing anywhere and runs no model in the browser beyond the exact rescaling it labels.

## Command contract

These commands work from a clean checkout (`docs/evidence/fresh_clone_2026-11.md` has a timed run from an empty folder with empty caches).

| Step | Command | What it does |
| ---- | ------- | ------------ |
| Setup | `make setup` | Installs the exact pinned Python environment from `uv.lock` into `.venv`; downloads Python 3.12 if needed |
| Run | `make run` | Builds the website (Node 22.18+) and serves it at http://localhost:8080; without Node it serves an existing `web/dist` |
| Test | `make test` | The automated tests (pytest, offline, about a minute) |
| Demo | `make demo` | Builds the synthetic state `ZZ` from committed fixtures and runs the baseline and all five reforms, with no network |
| Data | `make data STATE=NH` | Downloads every input one state needs from keyless public sources and builds `data/processed/NH.json`; each file's URL and SHA-256 go to `data/manifests/` |
| Results | `make results STATE=NH` | Runs the engine for one state into `results/NH.json`; `make results-all export` runs every state and writes the committed web bundle `web/public/results/` |
| Web | `make web` | `npm ci` from `web/package-lock.json`, a type check and the production build into `web/dist`; `make web-dev` serves it with live reload |
| Web tests | `make test-web` | The website's tests, then the check that the page's arithmetic equals `hre run --set` |
| Docker | `docker compose up` | The same site at http://localhost:8080 from a container (verified in CI on every push) |
| Law check | `make law-check` | Every current-law quote searched for on its official page, and every coverage share recomputed (network) |
| Ledger | `make ledger` | The validation ledger as tables in `docs/evidence/validation.md` |
| Check | `make check` | The submission checklist, item by item (`make check STRICT=1` for the final run: pending items fail) |
| Any value | `uv run hre run --state UT --set builder_response_override=1.2` | Runs the engine with any assumption value (or `--level id=high`); the website shows this command for changes it doesn't compute itself |

Also: `make lint` (the static checks CI runs), `make docs` (rewrites the generated tables in the documents from their sources), `make pages` (prints the two page-limited documents to PDF and stores the counts), `make sbom` (saves GitHub's SBOM). `scripts/setup.sh`, `scripts/run.sh` and `scripts/test.sh` run setup, run and test for CI.

Environment: macOS or Linux (Windows through WSL), `make`, [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11 or newer, and [Node](https://nodejs.org) 22.18 or newer for the website (or Docker instead). Nothing is installed into the system Python, and no key or secret is needed; `.env.example` lists the two optional settings.

## Documentation

The submission documents:

- [Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md): what the tool does, every assumption, the method, limitations, sensitivity, users and non-uses (21 pages printed)
- [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md): the five reforms ranked for Utah, New Hampshire and Arizona, what drives them and what flips the ranking (4 pages)
- [Data Provenance](docs/DATA_PROVENANCE.md): every dataset with its source, release, licence, cleaning and limits, and the sources excluded
- [Disclosures](docs/DISCLOSURES.md): AI tools, services, data terms and every dependency's licence from the SBOM
- [Judge Guide](docs/JUDGE_GUIDE.md): where each part of the challenge is answered, and the submission checklist
- [Glossary](docs/GLOSSARY.md) and [what the tool cannot tell you](docs/methods/limits.md): the plain-language text the website shows
- [Release notes](docs/RELEASE_NOTES.md) and the [SBOM](docs/sbom/sbom.spdx.json)

Methods, one note per part of the model: [baseline](docs/methods/baseline.md); [ADUs](docs/methods/adu.md), [missing middle](docs/methods/missing_middle.md), [transit-oriented density](docs/methods/tod.md), [parking](docs/methods/parking.md), [fees](docs/methods/fees.md) and the [combined package](docs/methods/combined.md); [builder response](docs/methods/builder_response.md); [ADU value tiers](docs/methods/tiers.md); [cases](docs/methods/cases.md); [sensitivity](docs/methods/sensitivity.md); [current law](docs/methods/current_law.md); [parcel adapters](docs/methods/adapters.md); [transit proximity](docs/methods/transit.md); the [input schema](docs/methods/schema.md) and [results schema](docs/methods/results_schema.md); the full [assumption register](docs/methods/register.md); [the website](docs/methods/ui.md).

Evidence: [baseline backtest](docs/evidence/baseline_backtest.md), [ADU tiers and city splits](docs/evidence/adu_tiers.md), [completions per permit](docs/evidence/completions_per_permit.md), [results overview](docs/evidence/results_overview.md), [current-law quotes](docs/evidence/current_law_quotes.md) and [coverage](docs/evidence/current_law_coverage.md), the [review checklist for Utah, New Hampshire and Arizona](docs/evidence/current_law_review_ut_nh_az.md), the [validation ledger](docs/evidence/validation.md), the [Address Count Listing File check](docs/evidence/aclf_ratio_check_all_states.md), [security gates](docs/evidence/security_gates.md), the [fresh-clone run](docs/evidence/fresh_clone_2026-11.md), [page counts](docs/evidence/page_counts.json) and the [usability check form](docs/evidence/usability_check.md).

## Data

Every input is a keyless public download: Census Building Permits Survey, American Community Survey bulk files, Population Estimates, New Residential Construction, 2020 centers of population, the Gazetteer, OMB metro delineations, FHFA county house prices, the National Transit Map and National Transit Database, the National Zoning and Land Use Database, California HCD's ADU reports, county parcel counts for Utah and Arizona, and each state's statutes. Nothing large is committed; [data/README.md](data/README.md) explains the layout.

This product uses Census Bureau data but is neither endorsed nor certified by the Census Bureau. This product uses FHFA data but is neither endorsed nor certified by FHFA.

## Team

Rishabh Manacha (Team Leader), Community Solutions, with teammates to be listed here. All contributors agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).

## License

Apache License 2.0 ([LICENSE](LICENSE)), the challenge's recommended default: its express patent grant makes it the safest choice for a tool a state agency or another team may adopt and build on. Every dependency is under a permissive licence (MIT, ISC, BSD or Apache-2.0); [DISCLOSURES.md](docs/DISCLOSURES.md) lists each one, and a test fails if a copyleft licence enters the SBOM. Each dataset keeps its own terms ([DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md)).
