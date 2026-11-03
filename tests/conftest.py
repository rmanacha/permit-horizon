"""Shared fixtures: the committed synthetic state ZZ under data/sample (no network anywhere)."""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "data" / "sample"


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    assert (SAMPLE / "cenpop" / "CenPop2020_Mean_BG99.txt").exists(), "run scripts/make_sample_zz.py"
    return SAMPLE


@pytest.fixture(autouse=True)
def _isolated_manifests(tmp_path, monkeypatch):
    """Never let a test write into the tracked data/manifests folder."""
    monkeypatch.setenv("HRE_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "raw"))


@pytest.fixture(scope="session")
def zz_state(sample_dir):
    """The synthetic state ZZ built from the committed fixtures, read back through from_json."""
    from hre.build.build_state_inputs import build_state
    from hre.schema import StateInputs

    si, _ = build_state("ZZ", sample_dir)
    return StateInputs.from_json(si.to_json())


@pytest.fixture(scope="session")
def params():
    from hre.assumptions.loader import load_params

    return load_params()
