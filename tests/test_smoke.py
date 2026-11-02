"""Smoke tests: the package installs, imports, and declares one version."""

import re
import tomllib
from pathlib import Path

import hre


def test_package_imports_with_docstring():
    assert hre.__doc__ is not None
    assert "Permit Horizon" in hre.__doc__


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", hre.__version__)


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    assert data["project"]["version"] == hre.__version__
