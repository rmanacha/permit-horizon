# Command contract for Permit Horizon.
#
# The README documents exactly three commands a stranger runs from a clean
# checkout: setup, run, test. The organizers' CI (.github/workflows/ci.yml)
# runs scripts/setup.sh and scripts/test.sh, which call the targets below, so
# there is one definition of each command.
#
# Requires: uv (https://docs.astral.sh/uv/). uv downloads the pinned Python
# itself (.python-version) and never touches the system Python.

.PHONY: setup test run lint

setup:   ## Install the exact pinned environment from uv.lock into .venv
	uv sync --frozen --all-extras

test:    ## Run the automated tests
	uv run pytest -q

run:     ## Start the tool (the web app arrives in Phase 4)
	@echo "Permit Horizon: the web app arrives in Phase 4. For now, run 'make test'."

lint:    ## Static checks (style and common bugs)
	uv run ruff check .
