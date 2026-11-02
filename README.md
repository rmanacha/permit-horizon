<!--
==============================================================================
HOW TO USE THIS TEMPLATE (delete this comment block once you've read it)

1. Click "Use this template" on GitHub to create your own PUBLIC repository.
2. Read docs/REPO_SETUP_GUIDE.md and turn on the repository security settings (secret scanning, push protection, code scanning). These are settings, not files, so the template cannot enable them for you.
3. Replace every [bracketed placeholder] below with your project's details.
4. Fill in the "Command contract" so anyone can set up, run, and test your tool with the exact commands you list.
5. Work through SUBMISSION_CHECKLIST.md before you submit.

This template is language-agnostic. Use Python, JavaScript, Go, R, or anything else. The files here are configuration and documentation only; nothing forces a particular language or framework on you.
==============================================================================
-->

# [Project name]

[One or two sentences: what your tool does and who it is for. Example: "A state-level simulator that estimates how many additional homes a set of pro-housing reforms could unlock in [state], with a county-level breakdown."]

## What this tool does

[Short description of the tool, the state(s) it covers, and the benchmark policy scenarios it addresses. List which of the five benchmark scenarios you implemented (at least three are required).]

## Command contract

Fill in the exact commands a stranger would run. These three commands are what reviewers use to reproduce your tool, so they must work from a clean checkout. Use whatever tooling you like (Make, npm scripts, a justfile, shell scripts, or plain commands) — only the documented commands matter.

| Step  | Command                     | Notes |
| ----- | --------------------------- | ----- |
| Setup | `[e.g., pip install -r requirements.txt]` | Installs dependencies |
| Run   | `[e.g., python app.py]`     | Starts the tool |
| Test  | `[e.g., pytest]`            | Runs the automated tests |

If there any assumptions on the environment required to run these commands, list them explicitly. Submissions with complicated build processes should provide a Dockerfile as a convenience.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

[How to obtain the data your tool uses. Do not commit raw or large data — see data/README.md. Point to the datasets and describe any download or preparation steps. Full provenance goes in docs/DATA_PROVENANCE.md.]

## Documentation

- [Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md) — how the tool works and what it assumes
- [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md) — scenario ranking and drivers
- [Data Provenance](docs/DATA_PROVENANCE.md) — sources, licenses, and cleaning steps
- [Disclosures](docs/DISCLOSURES.md) — AI tools, pretrained models, and external services
- [Presentation Guide](docs/PRESENTATION_GUIDE.md) — slide deck and demo video guidance

## License

This project is licensed under the **Apache License 2.0** (see [LICENSE](LICENSE)), the challenge's recommended default because its express patent grant is the safest choice for tools that may later be adopted or integrated downstream.

The challenge also permits **MIT**, **BSD 3-Clause**, and **BSD 2-Clause**. If you choose one of these instead, replace the LICENSE file with the full text of your chosen license and update this section. Copyleft licenses (GPL, AGPL, LGPL, MPL, EUPL) and public-domain dedications (CC0, the Unlicense) are **not** permitted for submission code. Your dependencies must also be permissively licensed — see docs/DISCLOSURES.md.

## Team

[List team members. All contributors must agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).]
