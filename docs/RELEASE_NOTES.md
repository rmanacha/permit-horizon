# Permit Horizon v1.0.0-submission

The build submitted to the Housing Data and Technology Innovation Challenge (sponsored by Arnold Ventures, run by The Turnout).

Permit Horizon estimates how many more homes would get building permits over 2026-2030 if a state passed one of five reforms (ADUs by right, missing middle, transit-oriented density, no parking minimums, fees cut in half), compared with the laws it has today, for every state and DC. Every number carries its unit, its range, its sources and what current state law already provides.

**Open the tool:** https://rmanacha.github.io/permit-horizon/ (no account; nothing to install).

## What's in this release

- The website: pick a state, compare the five reforms in building permits, change any assumption and watch the result move, see the statute behind each state's current law, and download the tables or a one-page brief.
- The engine (`hre`): fetch, build and run any state from public data with one command each; every assumption in one register with its source, page and arithmetic.
- The documents: [Model & Assumptions Overview](MODEL_AND_ASSUMPTIONS.md), [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md), [Data Provenance](DATA_PROVENANCE.md), [Disclosures](DISCLOSURES.md), [Judge Guide](JUDGE_GUIDE.md) and the [Glossary](GLOSSARY.md).
- The validation ledger: every check of the model with hits and misses, and two frozen checks whose predictions were hashed and published before their outcomes were fetched.

## Check it yourself

```bash
git clone https://github.com/rmanacha/permit-horizon.git && cd permit-horizon
make setup     # the exact Python environment from uv.lock
make test      # the automated tests, offline
make run       # build the website and serve it at http://localhost:8080
make check     # the submission checklist, item by item
```

`docker compose up` serves the same site without Node. A cold-cache run of these commands took 45 seconds on 2026-11-04 (`docs/evidence/fresh_clone_2026-11.md`).

## Attached to this release

- `sbom.spdx.json`: the software bill of materials exported from GitHub's dependency graph (also at `docs/sbom/sbom.spdx.json`).
- `MODEL_AND_ASSUMPTIONS.pdf` and `POLICY_SCENARIO_COMPARISON.pdf`: the two page-limited documents as printed by `make pages`.

## Licence and disclosures

Apache-2.0. Every dependency is under a permissive licence. AI assistance (Claude Code) is disclosed in [DISCLOSURES.md](DISCLOSURES.md); no language model runs inside the tool. This product uses Census Bureau and FHFA data but is neither endorsed nor certified by either agency.
