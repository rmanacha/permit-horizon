# Command contract for Permit Horizon.
#
# The README documents the commands a stranger runs from a clean checkout.
# The organizers' CI (.github/workflows/ci.yml) runs scripts/setup.sh and
# scripts/test.sh, which call the targets below, so there is one definition
# of each command.
#
# Requires: uv (https://docs.astral.sh/uv/). uv downloads the pinned Python
# itself (.python-version) and never touches the system Python.

.PHONY: setup test run lint demo data validate-aclf hcd results backtest adu-tiers nrc register-md results-all export web web-dev test-web law-check ledger docs pages sbom check

STATE ?= NH
PORT ?= 8080

setup:   ## Install the exact pinned environment from uv.lock into .venv
	uv sync --frozen --all-extras

test:    ## Run the automated tests (offline; nothing is downloaded)
	uv run pytest -q

lint:    ## Static checks (style and common bugs)
	uv run ruff check .

demo:    ## Build the synthetic demo state ZZ from committed fixtures, no network
	uv run hre build --state ZZ --data-dir data/sample
	uv run hre validate --processed data/processed/ZZ.json
	uv run hre run --state ZZ --data-dir data/sample --out results/ZZ.json

data:    ## Fetch and build one state: make data STATE=NH
	uv run hre fetch --state $(STATE)
	uv run hre build --state $(STATE)
	uv run hre validate --processed data/processed/$(STATE).json

validate-aclf:  ## Address Count Listing File doubling check for the showcase states
	uv run hre validate --aclf --states NH,UT,AZ,CA --fetch --write docs/evidence/aclf_ratio_check.md

hcd:     ## Fetch California HCD Table A2 (295 MB) and build the de-duplicated ADU table
	uv run hre fetch --hcd
	uv run hre build --hcd

results: ## Run the engine for one state (baseline and five scenarios): make results STATE=NH
	uv run hre run --state $(STATE)

results-all: ## Run every jurisdiction with a processed file -> results/{ST}.json
	uv run hre run --all --quiet

export:  ## The web bundle for the front-end -> web/public/results/ (committed, decision 74)
	uv run hre export --out web/public/results/

backtest: ## Baseline backtest, both band rules -> docs/evidence/baseline_backtest.md
	uv run hre validate --baseline --fetch

adu-tiers: ## ADU value tiers + city-split check (needs make hcd) -> docs/evidence/adu_tiers.md
	uv run hre validate --adu-tiers

nrc:     ## Completions per permit from Census NRC -> docs/evidence/completions_per_permit.md
	uv run hre validate --nrc --fetch

law-check: ## Every current-law quote against its page, and every coverage share (network) -> docs/evidence/current_law_*.md
	uv run hre validate --law-quotes --fetch
	uv run hre validate --law-coverage --fetch

ledger:  ## The validation ledger as tables -> docs/evidence/validation.md (no network)
	uv run hre validate --ledger

register-md: ## The assumption register as Markdown -> docs/methods/register.md
	uv run hre export --register-md --out docs/methods/register.md

docs:    ## Rewrite every generated table in the docs from its source (register, current law, ledger, bundle)
	uv run python -m hre.docs

check:   ## The submission checklist item by item (STRICT=1 for the submission run: pending items fail)
	uv run python scripts/check_submission.py $(if $(STRICT),--strict,)

sbom:    ## Save GitHub's SBOM (the "Export SBOM" document) -> docs/sbom/sbom.spdx.json (network; after CI's dependency-graph job)
	uv run python scripts/fetch_sbom.py

pages:   ## Print the two page-limited docs to PDF (Chrome) and store the counts -> docs/evidence/page_counts.json
	uv run --with markdown==3.8 python scripts/count_pages.py

web:     ## Build the static site -> web/dist (Node 22.18+; installs the locked npm packages first)
	cd web && npm ci --no-audit --no-fund && npm run build

web-dev: ## Development server with live reload at http://localhost:5173 (after make web once)
	cd web && npm run dev

test-web: ## Web checks: unit tests, style and licence rules, the rescale equality test vs hre run --set
	cd web && npm test && npm run equality

run:     ## Build the site when Node is installed, then serve web/dist at http://localhost:8080
	@if command -v npm >/dev/null 2>&1; then $(MAKE) web; \
	elif [ -f web/dist/index.html ]; then echo "Node not found: serving the web/dist already built"; \
	else echo "Node is not installed and web/dist does not exist: install Node 22.18+ (https://nodejs.org), or run 'docker compose up', or open https://rmanacha.github.io/permit-horizon/"; exit 1; fi
	@echo "Permit Horizon: open http://localhost:$(PORT)/ (Ctrl-C stops the server)"
	uv run python -m http.server $(PORT) --bind 127.0.0.1 --directory web/dist
