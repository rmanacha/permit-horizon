# Permit Horizon

A statewide housing reform estimator. Permit Horizon estimates how five state-level reforms (accessory dwelling units, missing middle, transit-oriented density, parking-minimum reduction, and a 50% development fee cut) change residential building permits over five years versus a baseline, for all 50 states and DC, with low, central, and high ranges. Built for the Housing Data and Technology Innovation Challenge; audience: state legislators and their staff.

## What this tool does

Status: Phase 4 (web front-end) complete. `hre fetch --state NH` downloads every input a state needs from keyless public sources and records a provenance manifest; `hre build --state NH` writes `data/processed/NH.json`, the canonical input file (`docs/methods/schema.md`). `hre run --state NH` writes `results/NH.json`: the five-year permit baseline by county and state with a band backtested on 35 years of permits (`docs/methods/baseline.md`), the five benchmark scenarios in three layers (benchmark in the source's unit, the increment over current law in permits, and the total), a labeled combined package, and a Census housing-unit cross-check. `hre run --all` and `hre export` produce the bundle the web app reads (`docs/methods/results_schema.md`). Every assumption lives in one register with its source, page locator and arithmetic (`docs/methods/register.md`). The website (Phase 4, `web/`, live at https://rmanacha.github.io/permit-horizon/) reads that bundle: pick a state, read the baseline and the three layers of each reform with their units, change any assumption or case and see the result update (exact where the assumption multiplies the result, labeled interpolated or sent to the command line otherwise), compare reforms, inspect the register, the sources and the backtest, download tables or a one-page brief, and share a link that restores the view ([how it works](docs/methods/ui.md)).

## Command contract

Fill in the exact commands a stranger would run. These three commands are what reviewers use to reproduce your tool, so they must work from a clean checkout. Use whatever tooling you like (Make, npm scripts, a justfile, shell scripts, or plain commands) — only the documented commands matter.

| Step  | Command                     | Notes |
| ----- | --------------------------- | ----- |
| Setup | `make setup` | Installs the exact pinned Python environment (`uv.lock`) into `.venv`; downloads Python 3.12 if needed |
| Demo  | `make demo`  | Builds the synthetic state `ZZ` from committed fixtures, no network, a few seconds; validates the output and runs the baseline and all five scenarios on it |
| Data  | `make data STATE=NH` | Downloads every input one state needs (about 600 MB the first time, mostly ACS bulk files) and builds `data/processed/NH.json` |
| Results | `make results STATE=NH` | Runs the engine for one state (`hre run`), writing `results/NH.json` (`docs/methods/results_schema.md`); `make results-all export` runs every state with a processed file and writes the web bundle to `web/public/results/`, which is committed (rerun from a clean checkout after any engine or register change; a test catches a stale bundle) |
| Run   | `make run`   | Builds the website (needs Node 22.18+) and serves it at http://localhost:8080 with Python's `http.server`; without Node it serves an existing `web/dist`. The same site is public at https://rmanacha.github.io/permit-horizon/ |
| Web   | `make web`   | `npm ci` from `web/package-lock.json`, a type check and `vite build` into `web/dist` (not committed; CI and GitHub Pages build it). `make web-dev` serves it with live reload |
| Docker | `docker compose up` | The same site at http://localhost:8080 from a container (Node builds it, Python serves it, the engine is installed); verified in CI on every push |
| Test  | `make test`  | Runs the automated tests with pytest (offline) |
| Web tests | `make test-web` | The website's tests (rescale, bundle contract, styles, licences, glossary) and the equality test of the page's arithmetic against `hre run --set` |
| Any value | `uv run hre run --state UT --set builder_response_override=1.2` | Runs the engine with a user value (or `--level id=high`), held in every assumption set; the website shows this command for changes it does not compute itself |

Environment assumptions: macOS or Linux (Windows via WSL), `make`, and [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11 or newer on your PATH; [Node](https://nodejs.org) 22.18 or newer for `make run`, `make web` and `make test-web` (or Docker instead). Nothing is installed into the system Python. `make lint` runs the static checks CI runs. The same three steps also run as `scripts/setup.sh`, `scripts/run.sh`, and `scripts/test.sh`, which is what CI calls.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

Everything comes from keyless public downloads: Census Building Permits Survey, ACS 5-year bulk files, Population Estimates, Address Count Listing Files, 2020 centers of population, the Gazetteer, OMB metro delineations, FHFA county house prices, the National Transit Map and National Transit Database, NZLUD zoning survey, and California HCD's ADU reports. `make data STATE=XX` fetches and builds one state; `data/manifests/` records the URL and SHA-256 of every file so a reviewer can confirm they hold the same bytes; nothing large is committed. See [data/README.md](data/README.md) for the layout and [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) for sources, vintages, licences, cleaning steps and known limits, including the two data traps this phase found (address counts that read double from 2023, and repeated ADU permits in California's reports).

## Documentation

- [Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md) — how the tool works and what it assumes
- [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md) — scenario ranking and drivers
- [Data Provenance](docs/DATA_PROVENANCE.md) — sources, licenses, and cleaning steps
- [Input schema](docs/methods/schema.md) — every field of `data/processed/{ST}.json` and where it comes from
- [Transit proximity](docs/methods/transit.md) — what counts as a major stop and how distance is measured
- [Assumption register](docs/methods/register.md) — every parameter with low/mid/high, source, locator, arithmetic, grade and confidence (`make register-md`)
- Methods: [baseline](docs/methods/baseline.md), scenarios ([ADU](docs/methods/adu.md), [missing middle](docs/methods/missing_middle.md), [transit-oriented density](docs/methods/tod.md), [parking](docs/methods/parking.md), [fees](docs/methods/fees.md), [combined package](docs/methods/combined.md)), [builder response](docs/methods/builder_response.md), [ADU value tiers](docs/methods/tiers.md), [cases](docs/methods/cases.md), [sensitivity](docs/methods/sensitivity.md), [results schema](docs/methods/results_schema.md)
- Evidence: [baseline backtest](docs/evidence/baseline_backtest.md) (both band rules, coverage by period, real-time test; `make backtest`), [ADU tiers and city-split check](docs/evidence/adu_tiers.md) (`make adu-tiers`), [completions per permit](docs/evidence/completions_per_permit.md) (`make nrc`), [results overview and sanity review](docs/evidence/results_overview.md) (`hre validate --overview`)
- [Current law](docs/methods/current_law.md) — what each state's statutes already do, how a strength is set (gate x features x coverage), the review checklist; evidence: [quotes checked against their pages](docs/evidence/current_law_quotes.md) and [coverage](docs/evidence/current_law_coverage.md) (`make law-check`)
- [Parcel adapters](docs/methods/adapters.md) — county counts of single-family parcels for Utah and Arizona, the 30% tolerance rule, and how to add a state
- [Validation ledger](docs/evidence/validation.md) — every check of the model, hits and misses, with frozen protocols in `validation/` (`make ledger`)
- [The website](docs/methods/ui.md) — the six pages, how assumption changes are computed without Python, when to use the command line
- [Glossary](docs/GLOSSARY.md) and [what the tool cannot tell you](docs/methods/limits.md) — the plain-language text the website shows
- [Disclosures](docs/DISCLOSURES.md) — AI tools, pretrained models, and external services
- [Presentation Guide](docs/PRESENTATION_GUIDE.md) — slide deck and demo video guidance

## License

This project is licensed under the **Apache License 2.0** (see [LICENSE](LICENSE)), the challenge's recommended default because its express patent grant is the safest choice for tools that may later be adopted or integrated downstream.

The challenge also permits **MIT**, **BSD 3-Clause**, and **BSD 2-Clause**. If you choose one of these instead, replace the LICENSE file with the full text of your chosen license and update this section. Copyleft licenses (GPL, AGPL, LGPL, MPL, EUPL) and public-domain dedications (CC0, the Unlicense) are **not** permitted for submission code. Your dependencies must also be permissively licensed — see docs/DISCLOSURES.md.

## Team

Rishabh Manacha (Team Leader), Community Solutions, with teammates to be listed here. All contributors agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).
