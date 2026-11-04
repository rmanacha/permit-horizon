# Disclosures

What Permit Horizon was built with, what it depends on, and under which terms. The dependency table is generated from the SBOM GitHub exports for this repository (`docs/sbom/sbom.spdx.json`), so it lists exactly what the lock files pin.

# AI-Assisted Code Generation

**Tools.** The team used Claude Code (Anthropic) with the models Claude Fable 5.1 and Claude Opus 5.5 for planning, code generation, documentation drafting and source research (reading statutes and papers, checking quotes and locators). Commits written with it carry a `Co-Authored-By: Claude` line, so `git log` shows which ones. GitHub Copilot was not used in this repository.

**Terms.** Anthropic's consumer and commercial terms give the user Anthropic's rights, if any, in the outputs ([consumer terms](https://www.anthropic.com/legal/consumer-terms), [commercial terms](https://www.anthropic.com/legal/commercial-terms)). The team licenses the code under Apache-2.0 and is responsible for it.

**Review.** The team reviewed, tested and can explain all code in this repository, including the code written with AI assistance. Each phase of the work ended with a written report, and an independent review re-ran its tests, recomputed its key numbers by hand and read its output before the next phase started. More than 300 Python tests and 30 website tests run on every push; they recompute hand-worked examples, check every assumption for a source, recompute every current-law strength and compare the website's arithmetic with the engine. The methods notes in `docs/methods/` explain every module in plain language.

**No language model runs inside the tool.** Every sentence the website shows about a result is a fixed template filled with the engine's numbers (`src/hre/model/drivers.py`). The engine, the website and the downloads make no call to any AI service.

# Pretrained Models, Weights, and Embeddings

None. The tool uses no pretrained model, weights, embeddings or model library.

| Model / asset | Source | License / terms | Restrictions |
| ------------- | ------ | --------------- | ------------ |
| none | | | |

# External APIs and Hosted Services

**To use the tool:** none beyond a web host. The public site is served by GitHub Pages (free for public repositories). The page is static, sends nothing anywhere, sets no cookies and loads its fonts from its own folder. If Pages access lapsed, `make run` or `docker compose up` serves the same site from a copy of the repository.

**To rebuild the data** (not needed to use the tool or run the tests): the public download servers listed in [DATA_PROVENANCE.md](DATA_PROVENANCE.md). Every one is free and needs no key or account. Any of them could move or change a file, which is why every download's URL and SHA-256 are recorded in `data/manifests/`. The Census Data API is not used: it requires a key since May 2026, and every table the tool needs exists as a keyless bulk file.

**To develop:** GitHub (repository, Actions CI, CodeQL, Dependabot, the dependency graph), free for public repositories.

## Data terms that affect redistribution

Each dataset keeps its own terms; the code licence doesn't change them. The ones that limit what can be published:

| Dataset | Terms | How the tool complies |
|---|---|---|
| Utah Housing Unit Inventory (WFRC, MAG, UGRC) | Creative Commons Attribution 4.0 | County counts only, attributed on the data page and in the provenance |
| Maricopa County Assessor parcels; Pinal County TaxParcels | No licence stated (Maricopa: free to download, commercial resale needs a sublicence) | One count per county is used and published; no parcel row is downloaded or stored |
| NH Parcel Mosaic (NH DRA via GRANIT) | No licence stated; "estimation/planning purposes only" | Adapter disabled; New Hampshire uses the Census count of detached homes. A request to publish county counts is drafted in `docs/evidence/nh_granit_terms.md` and has not been sent |
| Amtrak GTFS (Shore Line East stations) | No licence published | Station coordinates only; the feed file isn't committed or redistributed |
| CTtransit GTFS | Revocable right to use and redistribute; no trademarks | Station coordinates only |
| FHFA House Price Index | Free; cite FHFA | "This product uses FHFA data but is neither endorsed nor certified by FHFA." |
| Census Bureau files | U.S. government works | "This product uses Census Bureau data but is neither endorsed nor certified by the Census Bureau." |

# Dependency Licenses

**The rule.** Every dependency, at run time or build time, must carry a permissive licence (MIT, ISC, BSD, Apache-2.0 or similar). No copyleft licence (GPL, AGPL, LGPL, MPL, EUPL) is accepted, with no exceptions. The SBOM is the source of truth; `tests/test_sbom.py` fails if it lists a package the lock files don't, misses one they do, or carries a licence outside the permissive list.

**Exceptions found and resolved.**

- **certifi (MPL-2.0)**, the certificate bundle the `requests` library depends on, was found in this review. `requests` was removed: downloads now use Python's standard library (`src/hre/data/net.py`) with the operating system's certificate store. The Census 2025 permit file and the Utah parcel count query were fetched again and match their recorded hashes and counts.
- **Vite 8** requires lightningcss (MPL-2.0), so the website stays on Vite 7, and Dependabot is told to skip Vite's major versions.

**Notes on the table.** GitHub's SBOM reads et-xmlfile's licence as "0BSD AND BSD-3-Clause AND MIT AND Python-2.0" (the package itself declares MIT; Python-2.0 is the permissive PSF-style licence). numpy bundles code under 0BSD, MIT, Zlib and CC0-1.0, all permissive. GitHub Actions have no licence in the SBOM; each action's repository states MIT, and they run only on GitHub's CI machines. `pypdf` (BSD-3-Clause) is the optional extra `law`, used only by the quote check (`hre validate --law-quotes`), with a floor of 6.21.4, the first release with no published advisory when it was added.

**Cross-checks.** `uv run --with pip-licenses==5.5.5 pip-licenses` over the locked Python environment reports the same 23 packages with the same licences, except certifi, which it reported as MPL-2.0 before the fix. Every installed website package's own `package.json` licence field reads MIT (20), Apache-2.0 (2), ISC (1) or BSD-3-Clause (1), and `web/scripts/licenses.test.mjs` checks all 94 lock-file entries for every platform on every push.

<!-- BEGIN generated:dependencies -->
| Package | Version | Licence (from the SBOM) | Where it is used |
|---|---|---|---|
| annotated-doc | 0.0.5 | MIT | runtime (engine and command line) |
| colorama | 0.4.6 | BSD-2-Clause AND BSD-3-Clause | runtime (engine and command line) |
| et-xmlfile | 2.0.0 | 0BSD AND BSD-3-Clause AND MIT AND Python-2.0 | runtime (engine and command line) |
| iniconfig | 2.3.1 | MIT | development only (tests, lint) |
| markdown-it-py | 4.2.0 | MIT | runtime (engine and command line) |
| mdurl | 0.1.2 | MIT | runtime (engine and command line) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | runtime (engine and command line) |
| openpyxl | 3.1.5 | MIT | runtime (engine and command line) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | development only (tests, lint) |
| pandas | 3.1.0 | BSD-3-Clause | optional extra `pipeline` |
| permit-horizon | 0.1.0 | Apache-2.0 | this project |
| pluggy | 1.7.0 | MIT | development only (tests, lint) |
| pygments | 2.21.0 | BSD-2-Clause | runtime (engine and command line) |
| pypdf | 6.21.4 | BSD-3-Clause | optional extra `law` |
| pyshp | 3.1.6 | MIT | runtime (engine and command line) |
| pytest | 9.2.0 | MIT | development only (tests, lint) |
| python-dateutil | 4.0.0 | BSD-3-Clause | optional extra `pipeline` |
| pyyaml | 6.0.3 | MIT | runtime (engine and command line) |
| rich | 15.0.0 | MIT | runtime (engine and command line) |
| ruff | 0.17.3 | MIT | development only (tests, lint) |
| shellingham | 1.5.4 | ISC | runtime (engine and command line) |
| typer | 0.27.3 | MIT | runtime (engine and command line) |
| tzdata | 2026.6 | Apache-2.0 | optional extra `pipeline` |
| react | 19.3.1 | MIT | website, served to the browser |
| react-dom | 19.3.1 | MIT | website, served to the browser |
| scheduler | 0.28.0 | MIT | website, served to the browser |
| @esbuild/* (26 platform builds; one is installed per machine) | 0.28.2 | MIT | website build only |
| @napi-rs/* (1 platform build) | 1.5.1 | MIT | website build only |
| @rollup/* (26 platform builds; one is installed per machine) | 4.67.4 | MIT | website build only |
| @types/estree | 1.0.10 | MIT | website build only |
| @types/node | 24.19.2 | MIT | website build only |
| @types/react | 19.3.0 | MIT | website build only |
| @types/react-dom | 19.3.0 | MIT | website build only |
| @typescript/* (20 platform builds; one is installed per machine) | 7.0.2 | Apache-2.0 | website build only |
| csstype | 3.2.3 | MIT | website build only |
| esbuild | 0.28.2 | MIT | website build only |
| fdir | 6.5.0 | MIT | website build only |
| fsevents | 2.3.3 | MIT | website build only |
| nanoid | 3.3.20 | MIT | website build only |
| picocolors | 1.1.1 | ISC | website build only |
| picomatch | 4.0.7 | MIT | website build only |
| postcss | 8.5.32 | MIT | website build only |
| rollup | 4.67.4 | MIT | website build only |
| source-map-js | 1.2.2 | BSD-3-Clause | website build only |
| tinyglobby | 0.2.17 | MIT | website build only |
| typescript | 7.0.2 | Apache-2.0 | website build only |
| undici-types | 7.24.6 | MIT | website build only |
| vite | 7.3.7 | MIT | website build only |
| actions/checkout | 7.*.* | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| actions/deploy-pages | 5.*.* | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| actions/setup-node | 7.*.* | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| actions/setup-python | 7.*.* | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| actions/upload-pages-artifact | 5.*.* | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| astral-sh/setup-uv | 10.3.3 | MIT (licence from the action's repository) | CI only (GitHub's machines); not shipped |
| com.github.rmanacha/permit-horizon | main | Apache-2.0 | this repository |

124 packages in docs/sbom/sbom.spdx.json (1 github, 6 githubactions, 94 npm, 23 pypi). Licences: MIT 89; Apache-2.0 24; BSD-3-Clause 4; ISC 2; 0BSD AND BSD-3-Clause AND MIT AND Python-2.0 1; Apache-2.0 OR BSD-2-Clause 1; BSD-2-Clause 1; BSD-2-Clause AND BSD-3-Clause 1; BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 1. Every licence is permissive.
<!-- END generated:dependencies -->

**Fonts** (served with the website from `web/public/fonts/`, licence texts beside the files, SHA-256 in `manifest.json`):

| Asset | Licence | Use | Notes |
|---|---|---|---|
| Raleway (The Raleway Project Authors) | SIL Open Font License 1.1 | served font files | a font licence; bundling with any software is allowed |
| Asap Condensed (The Asap Project Authors) | SIL Open Font License 1.1 | served font files | a font licence; bundling with any software is allowed |

# Generated or Copied Code

**From a teammate's prototype.** Parts of the model (register entries, the ADU tier calibration, the 20-year backtest rule, the Seattle holdout and the parcel rules) were first built in team member Adam Ruege's independent prototype, Housing Reform Estimator v2.0, during the coding period and ported into this repository with tests; no pre-existing open-source component declaration is needed for them. Ported content is marked where it lives: `ported_from: adam-v2.0` in the register and the current-law files, and credits in the module docstrings of `src/hre/validation/backtest_baseline.py` and `src/hre/validation/calibrate_adu_tiers.py`.

**The organizers' starter template** (`theturnout/housing-challenge-starter-template`, Apache-2.0) supplied the initial repository layout, the document headings, the CI skeleton and the security guidance.

**The Community Solutions design system** (2026 brand refresh) supplied the website's color, spacing and type tokens and the props of eight components, rewritten in TypeScript (`web/src/components/ds/`, `web/src/styles/tokens.css`), with the organization's permission. No logos, photography, slogans or the commercial Biro Script typeface are used.

Apart from these, the code was written for this repository.
