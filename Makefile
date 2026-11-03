# Command contract for Permit Horizon.
#
# The README documents the commands a stranger runs from a clean checkout.
# The organizers' CI (.github/workflows/ci.yml) runs scripts/setup.sh and
# scripts/test.sh, which call the targets below, so there is one definition
# of each command.
#
# Requires: uv (https://docs.astral.sh/uv/). uv downloads the pinned Python
# itself (.python-version) and never touches the system Python.

.PHONY: setup test run lint demo data validate-aclf hcd results backtest adu-tiers nrc register-md

STATE ?= NH

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

backtest: ## Baseline backtest, both band rules -> docs/evidence/baseline_backtest.md
	uv run hre validate --baseline --fetch

adu-tiers: ## ADU value tiers + city-split check (needs make hcd) -> docs/evidence/adu_tiers.md
	uv run hre validate --adu-tiers

nrc:     ## Completions per permit from Census NRC -> docs/evidence/completions_per_permit.md
	uv run hre validate --nrc --fetch

register-md: ## The assumption register as Markdown -> docs/methods/register.md
	uv run hre export --register-md --out docs/methods/register.md

run:     ## Start the tool (the web app arrives in Phase 4)
	@echo "Permit Horizon: the web app arrives in Phase 4. For now, run 'make demo' or 'make test'."
