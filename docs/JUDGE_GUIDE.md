# Judge Guide

Where each part of the challenge is answered: a file in this repository, a section of a document, or a screen of the website. Website links open the exact view (state, reform, assumptions) on https://rmanacha.github.io/permit-horizon/; the same views work from `make run` at http://localhost:8080/.

## Transparency and explainability

| What a judge looks for | Where it is answered |
|---|---|
| Every assumption stated, with its value and why | [Model & Assumptions Overview](MODEL_AND_ASSUMPTIONS.md), "Core Assumptions and Their Rationale" (eight assumptions in words, all 55 register entries in a generated table); the full register with page locators and arithmetic, [docs/methods/register.md](methods/register.md); the website's [Assumptions and data page](https://rmanacha.github.io/permit-horizon/#/data?st=NH) |
| How the tool is built and how a number is made | Overview, "Methodological Approach" (logic-flow figure, one formula per reform, New Hampshire worked through); [the website note](methods/ui.md); `src/hre/` (one module per part, named as in the methods notes) |
| What data each state has, what was used and why | The website's [data page for each state](https://rmanacha.github.io/permit-horizon/#/data?st=UT) (sources, releases, licences; parcel counts where a state has them: seven Utah counties, Maricopa and Pinal in Arizona; New Hampshire on the Census count and why); [Data Provenance](DATA_PROVENANCE.md) |
| Sources a reader can retrieve | `data/manifests/` (URL, size, SHA-256 and date of every downloaded file); a URL and locator on every register entry; every current-law quote checked against its official page ([docs/evidence/current_law_quotes.md](evidence/current_law_quotes.md), `make law-check`) |
| Sensitivity | Overview, "Sensitivity Notes" (the two largest swings for every reform in three states); the tornado and the joint cases on every [scenario page](https://rmanacha.github.io/permit-horizon/#/scenario?st=NH&sc=missing_middle) |
| Readable by a legislator, with a technical companion | [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md) (four pages, no jargon), the website's glossary beside every term ([docs/GLOSSARY.md](GLOSSARY.md)); the Overview and `docs/methods/` are the companion |
| A well-annotated model | Docstrings in every module; the register's `citation` field holds the arithmetic for each value; [docs/methods/](methods/) has one note per module |
| The team can explain the code, including AI-assisted code | [Disclosures](DISCLOSURES.md), "AI-Assisted Code Generation"; the tests that recompute hand-worked examples (`tests/test_scenarios.py`, `tests/test_golden.py`) |

## Replicability and scalability

| What a judge looks for | Where it is answered |
|---|---|
| Why this licence | [README](../README.md), "License"; [LICENSE](../LICENSE) (Apache-2.0) |
| Modular, documented code | `src/hre/data` (one fetcher per source), `build`, `model` (engine and one module per reform), `current_law`, `adapters`, `validation`; [docs/methods/](methods/) |
| Clear data requirements; alternative data can plug in | [Input schema](methods/schema.md) (every field of the per-state input file); [parcel adapters](methods/adapters.md), "Adding a state in under an hour"; the blank current-law form `src/hre/current_law/_template.yaml`; any assumption value through `hre run --set` |
| Assumptions kept apart from mechanics | All values in `src/hre/assumptions/parameters.yaml`; the engine reads them by id, and `tests/test_register.py` fails if code uses a value the register lacks |
| Tests that go past the minimum | More than 300 Python tests and 30 website tests: hand-worked examples, golden results for every state, every current-law strength recomputed, the page's arithmetic checked against the engine to one part in a billion, the bundle checked against the code that made it |
| One-command setup, and CI | `make setup`, `make test`, `make run` ([README](../README.md), "Command contract"); [.github/workflows/ci.yml](../.github/workflows/ci.yml); a timed run from an empty folder, [docs/evidence/fresh_clone_2026-11.md](evidence/fresh_clone_2026-11.md) |
| Pinned, current dependencies with no open vulnerability | `uv.lock`, `web/package-lock.json`; [docs/evidence/security_gates.md](evidence/security_gates.md) (no advisory for any of the 116 pinned versions; every Dependabot item resolved); the [SBOM](sbom/sbom.spdx.json) |

## Usability

| What a judge looks for | Where it is answered |
|---|---|
| A clear interface | The website's [Explore page](https://rmanacha.github.io/permit-horizon/#/explore?st=NH): one state, its baseline, five reform cards |
| Easy comparison of scenarios | The compare table on Explore (increments ranked in permits, flip warnings); the [one-page brief](https://rmanacha.github.io/permit-horizon/#/brief?st=NH); the Policy Scenario Comparison |
| Clear labels, instructions and outputs | Every number carries its outcome label; CSV and JSON downloads with an outcome column; [the website note](methods/ui.md) |
| Fast and stable | A static site with no server and no model in the browser; phone width supported; the equality test in `make test-web` |
| Plain-language terms | The glossary beside each term and on the [Methods and limits page](https://rmanacha.github.io/permit-horizon/#/methods); [docs/GLOSSARY.md](GLOSSARY.md) |

## Methodological soundness

| What a judge looks for | Where it is answered |
|---|---|
| Economic and land-use logic | Overview, "Core Assumptions" and "Methodological Approach"; [builder response](methods/builder_response.md); each reform's methods note |
| Parameters with a basis | Each register entry's grade (measured, derived, judgment, set by rule), confidence, source, locator and arithmetic ([register](methods/register.md)) |
| Sensible ranges | Low and high sets come from each source's own evidence range; the tornado and joint cases cover the rest ([sensitivity](methods/sensitivity.md)) |
| Internal consistency | Numbers in different units are never added or ranked; the combined package's four overlap rules ([combined](methods/combined.md)); the results validator in `src/hre/model/run.py` |
| Tests that show the code does what the method says | `tests/test_scenarios.py` and `tests/test_golden.py` (formulas against hand arithmetic), `tests/test_current_law.py` (every strength from its features), `web/scripts/rescale_equality.mjs` |

## Policy insight

| What a judge looks for | Where it is answered |
|---|---|
| What drives the differences | Policy Scenario Comparison, "What Drives the Differences"; "the assumption that moves this most" on every reform card |
| Which assumptions matter most, with evidence | Policy Scenario Comparison, "Which Assumptions Matter Most" (every single assumption that reorders the top two reforms in each state); the tornado |
| What the model can't say, and where it applies | [Limits](methods/limits.md) on the website's Methods and limits page; Policy Scenario Comparison, "What the Tool Cannot Say"; Overview, "Intended Users and Appropriate Use Cases" |
| Works for states with thin data | All 50 states and DC run from national public data; New Hampshire, with no usable parcel data and little transit, is a showcase state on the national path; state parcel data are optional and used only within 30% of the Census count |

## The parts of this tool a judge may ask about

| Item | Where |
|---|---|
| Outcome labels | Every number in `web/public/results/` carries one (permits, net permits, completed homes, homes added to the stock, cost-response permits); [the website note](methods/ui.md), "Rules the code enforces"; `make check` verifies the bundle |
| The register-default increment | The headline case: the newly affected share comes from the state's current law, with the reform's phase-in and no delay ([cases](methods/cases.md); the case picker on Explore) |
| The current-law register | `src/hre/current_law/{ST}.yaml` (51 files, 63 entries); [how a strength is set](methods/current_law.md); the generated tables in the Overview; the law card on each [scenario page](https://rmanacha.github.io/permit-horizon/#/scenario?st=AZ&sc=adu) |
| Frozen check: Austin ADU permits, 2023-2025 | `validation/austin_adu_2023_2025/`: `protocol.json`, its SHA-256 in `protocol.sha256` (`a936174a1f8b321806c6fc648d6610a1ac82350c47db9a13e1d29db232fcfce9`, committed in `199a908`), and `result.json` (a miss: 117 permits a year against 139 to 1,217) |
| Frozen check: every state's 2026 permits | `validation/bps_2026_states/`: `protocol.json` and its SHA-256 (`d54a5013e7fb771f87e978a94f70cc636023bb77b339d476c7208cb40ccf85fc`, committed in `199a908`); pending until the Census posts the 2026 file in 2027 |
| Frozen check: Seattle ADU completions (a teammate's prototype) | The hash as reported, `b2a1649b5bc2c74c018321279f90dc866d4b89e88bb16f1fd554ee654dbf4259`; the protocol lives in that prototype's archive, which isn't in this repository |
| The push-then-fetch rule | A frozen check is scored only after CI has finished on the commit holding its protocol hash, and the result records that run. Austin's protocol was committed, pushed and its outcome fetched inside one minute (commit 00:54:54 UTC, CI start 00:55:00 on 2026-11-04), so its order rests on the session record; the 2026 check follows the rule |
| The validation ledger | `validation/ledger.yaml`, [docs/evidence/validation.md](evidence/validation.md), the [Validation page](https://rmanacha.github.io/permit-horizon/#/validation): 13 checks with evidence classes, 1 hit, 5 misses, 1 pending |
| The Census housing-unit estimates panel | Beside every baseline on Explore (net change in homes since April 2020; never added to the forecast, because the estimates are partly built from the same permits) |
| Address Count Listing Files, excluded | [docs/evidence/aclf_ratio_check_all_states.md](evidence/aclf_ratio_check_all_states.md) (the published totals run 1.89 to 2.11 times the housing stock from July 2023); Data Provenance, "Excluded Sources"; `make validate-aclf` reruns it |
| `make demo` | Builds the synthetic state ZZ from committed fixtures and runs everything offline in a few seconds |

## Submission checklist

Status on 2026-11-04. `make check` re-verifies every automated item; `make check STRICT=1` is the final run before submitting.

Eligibility gates:

- [x] Reproducible setup from documented commands (README, "Command contract"; fresh-clone run)
- [x] Automated tests covering core logic, with a documented run command (`make test`, `make test-web`; CI)
- [x] No committed secrets; secret scanning on (history scan in `docs/evidence/security_gates.md`); the owner confirms zero alerts on the GitHub page
- [x] Dependabot and CodeQL on, no unaddressed critical or high finding (no advisory for any pinned version); the owner confirms the alert counts
- [x] Approved licence: Apache-2.0
- [x] Public GitHub repository: https://github.com/rmanacha/permit-horizon
- [x] SBOM exported: `docs/sbom/sbom.spdx.json`, checked against both lock files
- [ ] SBOM attached to the release `v1.0.0-submission` (the owner creates the release)

Deliverables:

- [x] Interactive tool, working (`make run`, Docker)
- [ ] Interactive tool at its public address (the owner turns on GitHub Pages)
- [ ] Slide deck, 30 slides or fewer, PDF (next phase)
- [ ] Demo video, 5 minutes, viewable without an account (next phase)
- [x] Model & Assumptions Overview, 25 pages or fewer (21)
- [x] Source code in a public repository
- [x] Policy Scenario Comparison, 4 pages or fewer (4)

Scope and disclosures:

- [x] Baseline and all five benchmark scenarios, at the state level, over five years, with the outcome (building permits) chosen and justified
- [x] Fee scenario at $50,000 a home cut by 50%
- [x] Data provenance documented
- [x] AI tools, models, services and dependencies disclosed
- [ ] Human review signed for the 15 Utah, New Hampshire and Arizona current-law records (a policy teammate)
