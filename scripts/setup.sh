#!/usr/bin/env sh
# Install dependencies and prepare the environment. CI runs this first.
# Single source of truth is the Makefile; this wrapper exists because the
# organizers' CI workflow looks for scripts/setup.sh.
set -eu
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi
make setup
