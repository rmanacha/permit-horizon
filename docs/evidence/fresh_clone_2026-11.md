# Fresh-clone reproduction, 2026-11-04

A stranger's first run: clone the public repository into an empty folder and use only the documented commands. Run on 2026-11-04 at commit `cf9553b`, with every cache empty so that nothing already installed on the machine could help: uv's package cache, uv's Python downloads (uv was told to use only a Python it downloads itself) and npm's cache all pointed at new, empty folders.

**Result: every step passed in 45 seconds of wall time**, including downloading Python 3.12 and every package.

| Step | Command | Exit | Seconds | What it printed |
|---|---|---|---|---|
| Clone | `git clone https://github.com/rmanacha/permit-horizon.git` | 0 | 1 | |
| Setup | `make setup` | 0 | 2 | downloaded cpython 3.12.13 (23.8 MiB); installed 22 packages |
| Test | `make test` | 0 | 31 | `322 passed, 2 skipped in 30.13s` |
| Demo | `make demo` | 0 | 2 | the synthetic state ZZ built from fixtures and run through the baseline and all five reforms |
| Website | `make web` | 0 | 3 | `npm ci`, type check, `vite v7.3.7`, 68 modules, built in 569 ms |
| Website tests | `make test-web` | 0 | 5 | `tests 30, pass 30, fail 0`; `12 comparisons in ZZ: all equal` |

The two skipped tests need downloaded data, by design: the current-law coverage recomputation ("ACS B01003 or the place Gazetteer not cached") and the all-states golden run ("no processed files"). `make data STATE=NH` and `make law-check` run them on a machine with the data.

## Machine

| | |
|---|---|
| Operating system | macOS 27.0.1 (26A434), Apple silicon (arm64) |
| uv | 0.11.29 |
| Node and npm | 24.14.1, 11.11.0 |
| make, git | GNU Make 3.81, git 2.54.0 |
| Caches after the run | uv packages 107 MB, Python 66 MB, npm 18 MB |

## Exact commands

```bash
ROOT=/path/to/an/empty/folder
export UV_CACHE_DIR="$ROOT/cache/uv" UV_PYTHON_INSTALL_DIR="$ROOT/cache/python" UV_PYTHON_PREFERENCE=only-managed
export npm_config_cache="$ROOT/cache/npm"
cd "$ROOT"
git clone https://github.com/rmanacha/permit-horizon.git repo
cd repo
make setup
make test
make demo
make web
make test-web
```

Each step was timed with the shell clock (whole seconds); its full output went to a log kept outside the repository.

## A second machine: CI and Docker on GitHub

This Mac has no Docker, so the container path is verified on GitHub's Ubuntu machines on every push. For the same commit `cf9553b` (2026-11-04):

| Job | Result | Started, finished (UTC) | Run |
|---|---|---|---|
| test: `scripts/setup.sh`, `uv lock --check`, lint, `scripts/test.sh`, `make demo`, `make web`, `make test-web` on a clean Ubuntu runner | success | 14:39:24, 14:40:11 | https://github.com/rmanacha/permit-horizon/actions/runs/41849728457/job/126642488403 |
| docker: `docker compose up --build`, requests for the site, the bundle and New Hampshire's results, the engine run inside the container | success | 14:39:25, 14:40:10 | https://github.com/rmanacha/permit-horizon/actions/runs/41849728457/job/126642489050 |
| CodeQL (Python, JavaScript and TypeScript, Actions) | success | 14:39:26, 14:40:52 | https://github.com/rmanacha/permit-horizon/actions/runs/41849728015 |

## What this does and does not show

It shows that `make setup`, `make test`, `make demo` and the website build that `make run` serves work from a clean copy with nothing cached, on macOS and on Ubuntu, and that the container builds and serves the site. It does not rebuild the data: `make data STATE=XX` downloads several hundred megabytes from public servers and is covered by the manifests in `data/manifests/`, which record every file's SHA-256.
