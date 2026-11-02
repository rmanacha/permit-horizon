#!/usr/bin/env sh
# Run the automated tests. CI runs this; it exits non-zero on failure.
set -eu
make test
