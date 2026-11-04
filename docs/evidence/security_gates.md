# Security gates, 2026-11-04

The challenge's pass/fail gates for security: no committed secrets with secret scanning on, Dependabot and CodeQL on with no unaddressed critical or high finding, and pinned, current dependencies. This page records what was checked, how, and what is left for the repository owner, whose sign-in the alert pages need.

## What was verified without a sign-in

| Gate | Status | How it was checked |
|---|---|---|
| CodeQL runs on every push | yes | GitHub's default setup (the "CodeQL" workflow) analyses Python, JavaScript and TypeScript, and the workflow files; all three passed on every pushed commit of this phase, for example https://github.com/rmanacha/permit-horizon/actions/runs/41849728015 |
| Dependabot on | yes | "Dependabot Updates" and "Dependency Graph" workflows active; `.github/dependabot.yml` covers GitHub Actions, uv, npm and Docker |
| Private vulnerability reporting | on | `GET /repos/rmanacha/permit-horizon/private-vulnerability-reporting` returns `{"enabled": true}` |
| Known vulnerabilities in pinned packages | none | All 116 exact versions in `uv.lock` (22 packages besides the project) and `web/package-lock.json` (94 entries) sent to the OSV database (`api.osv.dev/v1/querybatch`, the open database GitHub's advisories feed): no advisory for any of them |
| Secrets in the history | none | All 85 commits searched for AWS, GitHub, Slack, Google, Anthropic and OpenAI key patterns and private-key headers: 0 matches. No `.env`, key, certificate or credentials file was ever committed; the only environment file is `.env.example`, which holds no values |
| Dependencies pinned | yes | `uv sync --frozen` from `uv.lock` (CI also runs `uv lock --check`), `npm ci` from `web/package-lock.json`, Docker base images by digest, actions by version |
| Copyleft dependencies | none | `tests/test_sbom.py` checks every licence in the stored SBOM; certifi (MPL-2.0) was removed with `requests` in this phase |

## Dependabot items and their resolution

| Item | Resolution |
|---|---|
| 67 alerts on `pypdf` 5.9.0 (raised when the quote checker first locked it) | Resolved by the floor `pypdf>=6.21.4` (commit `772812f`); OSV lists no advisory for 6.21.4. To confirm: the Dependabot page should show them under Closed, as fixed |
| Pull request "Bump node from 24-slim to 26-slim" (Dockerfile) | Not taken: the container builds the site with the same Node 24 that CI and Pages use, and Node 24 has security support until April 2028. Digest and minor updates still come through; `.github/dependabot.yml` now skips Node's major versions. Close the pull request with that reason |
| Pull request "Bump @types/node from 24.19.2 to 26.6.6 in /web" | Not taken: the type definitions follow the Node major the site runs on (24). `.github/dependabot.yml` now skips its major versions. Close the pull request with that reason |
| Vite 8 | Skipped since the website was built: it requires lightningcss (MPL-2.0) |

## For the repository owner: four pages to open and one block to fill in

Each page needs the owner's sign-in. Expected counts are all zero.

1. **Code scanning**: https://github.com/rmanacha/permit-horizon/security/code-scanning. Read the number beside "Open" at the top of the list.
2. **Dependabot**: https://github.com/rmanacha/permit-horizon/security/dependabot. Read the "Open" count; then click "Closed" and check that the pypdf alerts read "Fixed".
3. **Secret scanning**: https://github.com/rmanacha/permit-horizon/security/secret-scanning. Read the "Open" count.
4. **Settings**: https://github.com/rmanacha/permit-horizon/settings/security_analysis. Check that Dependabot alerts, secret scanning (Secret Protection), push protection and private vulnerability reporting are enabled, and that CodeQL analysis says "Default setup".
5. Close the two Dependabot pull requests above with the reason given (https://github.com/rmanacha/permit-horizon/pulls), then write the counts below and commit. `make check` reads this block; `make check STRICT=1` fails until every line is filled and every count is 0 (or the line says why a finding is justified).

<!-- filled in by the repository owner -->
- Code scanning open alerts: 0
- Dependabot open alerts: 0
- Secret scanning open alerts: 0
- Push protection: on
- Checked by and date: Rishabh Manacha, 2026-11-05
