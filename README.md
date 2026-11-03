# Permit Horizon

A statewide housing reform estimator. Permit Horizon estimates how five state-level reforms (accessory dwelling units, missing middle, transit-oriented density, parking-minimum reduction, and a 50% development fee cut) change residential building permits over five years versus a baseline, for all 50 states and DC, with low, central, and high ranges. Built for the Housing Data and Technology Innovation Challenge; audience: state legislators and their staff.

## What this tool does

Status: Phase 1 (data pipeline) complete. `hre fetch --state NH` downloads every input a state needs from keyless public sources and records a provenance manifest; `hre build --state NH` writes `data/processed/NH.json`, the canonical input file (`docs/methods/schema.md`). The engine, scenarios and web app arrive in later phases; this section will list the scenarios implemented and the showcase states (Utah, New Hampshire, Arizona) as they land.

## Command contract

Fill in the exact commands a stranger would run. These three commands are what reviewers use to reproduce your tool, so they must work from a clean checkout. Use whatever tooling you like (Make, npm scripts, a justfile, shell scripts, or plain commands) — only the documented commands matter.

| Step  | Command                     | Notes |
| ----- | --------------------------- | ----- |
| Setup | `make setup` | Installs the exact pinned Python environment (`uv.lock`) into `.venv`; downloads Python 3.12 if needed |
| Demo  | `make demo`  | Builds the synthetic state `ZZ` from committed fixtures, no network, about one second; validates the output |
| Data  | `make data STATE=NH` | Downloads every input one state needs (about 600 MB the first time, mostly ACS bulk files) and builds `data/processed/NH.json` |
| Run   | `make run`   | Starts the tool (placeholder until the web app lands in Phase 4) |
| Test  | `make test`  | Runs the automated tests with pytest (offline) |

Environment assumptions: macOS or Linux (Windows via WSL), `make`, and [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11 or newer on your PATH. Nothing is installed into the system Python. `make lint` runs the static checks CI runs. The same three steps also run as `scripts/setup.sh`, `scripts/run.sh`, and `scripts/test.sh`, which is what CI calls.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

Everything comes from keyless public downloads: Census Building Permits Survey, ACS 5-year bulk files, Population Estimates, Address Count Listing Files, 2020 centers of population, the Gazetteer, OMB metro delineations, FHFA county house prices, the National Transit Map and National Transit Database, NZLUD zoning survey, and California HCD's ADU reports. `make data STATE=XX` fetches and builds one state; `data/manifests/` records the URL and SHA-256 of every file so a reviewer can confirm they hold the same bytes; nothing large is committed. See [data/README.md](data/README.md) for the layout and [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) for sources, vintages, licences, cleaning steps and known limits, including the two data traps this phase found (address counts that read double from 2023, and repeated ADU permits in California's reports).

## Documentation

- [Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md) — how the tool works and what it assumes
- [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md) — scenario ranking and drivers
- [Data Provenance](docs/DATA_PROVENANCE.md) — sources, licenses, and cleaning steps
- [Input schema](docs/methods/schema.md) — every field of `data/processed/{ST}.json` and where it comes from
- [Transit proximity](docs/methods/transit.md) — what counts as a major stop and how distance is measured
- [Disclosures](docs/DISCLOSURES.md) — AI tools, pretrained models, and external services
- [Presentation Guide](docs/PRESENTATION_GUIDE.md) — slide deck and demo video guidance

## License

This project is licensed under the **Apache License 2.0** (see [LICENSE](LICENSE)), the challenge's recommended default because its express patent grant is the safest choice for tools that may later be adopted or integrated downstream.

The challenge also permits **MIT**, **BSD 3-Clause**, and **BSD 2-Clause**. If you choose one of these instead, replace the LICENSE file with the full text of your chosen license and update this section. Copyleft licenses (GPL, AGPL, LGPL, MPL, EUPL) and public-domain dedications (CC0, the Unlicense) are **not** permitted for submission code. Your dependencies must also be permissively licensed — see docs/DISCLOSURES.md.

## Team

Rishabh Manacha (Team Leader), Community Solutions, with teammates to be listed here. All contributors agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).
