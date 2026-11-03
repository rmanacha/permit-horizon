# Disclosures

AI-assisted development is welcome. This document exists so reviewers can
confirm that your tool's code, models, services, and dependencies are compatible
with the challenge's open-source and downstream-use requirements. Disclose
material use; incidental use of a general coding assistant is lower risk but
should still be noted if its terms affect your submission.

# AI-Assisted Code Generation

[List any AI coding tools you used in a material way (e.g., for generating core
logic). Confirm that the tool's terms permit submitting and openly licensing the
generated output. You remain responsible for understanding, testing, and
securing all code you submit.]

Running notes until Phase 6 completes this document: Claude (Anthropic) was used
as a coding assistant for the pipeline (Phase 1) and the baseline engine, register
and validation code (Phase 2); every function has hand-computed tests and the team
reviews each phase report. Commits made with it carry a `Co-Authored-By: Claude`
line. No language model runs inside the tool: narrative text comes from fixed
templates in `src/hre/model/drivers.py`.

# Pretrained Models, Weights, and Embeddings

[List any pretrained models, model weights, embeddings, or model libraries your
tool incorporates or requires. For each, give the name, source, and the license
or terms that govern it. Flag any noncommercial, field-of-use, or
acceptable-use restrictions.]

| Model / asset | Source | License / terms | Restrictions |
| ------------- | ------ | --------------- | ------------ |
| [name] | [URL] | [license] | [none / noncommercial / etc.] |

# External APIs and Hosted Services

[List any API or hosted service your tool needs to function. Note whether there
is a free tier, whether access could lapse, and any terms limiting commercial,
government, or downstream use. Reviewers prioritize tools whose data and services
remain freely available to end users.]

# Dependency Licenses

[Confirm that your runtime dependencies are permissively licensed and compatible with closed-source downstream integration. Copyleft (GPL, AGPL, LGPL, MPL, EUPL), source-available-but-not-open-source, noncommercial, or unknown-license dependencies must be flagged here and resolved. Your SBOM (exported from GitHub's dependency graph) is the source of truth; summarize any exceptions.]

| Dependency | License | Runtime or dev-only | Notes |
| ---------- | ------- | ------------------- | ----- |
| [name] | [license] | [runtime / dev] | [ok / flagged] |

# Generated or Copied Code

[Note any code copied or adapted from external sources, and the license it came under. Ensure attribution requirements (e.g., an entry in NOTICE) are met.]

Internal origin (not an external source): Adam Ruege, a member of this team, built
an independent prototype, Housing Reform Estimator v2.0, during the coding period
(decision 43). Content ported from it keeps his locators and arithmetic and is
marked in place:

- Register entries with `ported_from: adam-v2.0` in `src/hre/assumptions/parameters.yaml`
  (builder response, new-home price ratio, horizon, fee premise, stock diagnostic, ramp case).
- The New Hampshire ADU current-law record in `src/hre/current_law/NH.yaml`
  (re-checked against RSA 674:72 on 2026-11-03).
- The baseline band rule B and the ADU tier method and city-split check, re-derived
  from his published descriptions (`src/hre/validation/backtest_baseline.py`,
  `src/hre/validation/calibrate_adu_tiers.py`), each credited in the module docstring.
