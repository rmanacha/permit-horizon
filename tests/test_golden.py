"""Golden run on the synthetic state ZZ, and properties every results file must keep.

The golden file freezes the headline numbers of a full run on ZZ (committed fixtures, no
network). A formula change shows up here as a reviewed diff: regenerate with
``HRE_UPDATE_GOLDEN=1 uv run pytest tests/test_golden.py`` and commit the new file with the
reason in the message.
"""

import json
import os
from pathlib import Path

import pytest

from hre.data.states import ALL_STATES
from hre.model.run import run_state, validate_results
from hre.schema import OUTCOMES, StateInputs

GOLDEN = Path(__file__).parent / "golden" / "ZZ_headline.json"
META = {"build_id": "golden", "vintages": {}, "git_sha": "golden", "run_date": "golden"}
LV = ("low", "mid", "high")
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


def headline(r: dict) -> dict:
    out = {"baseline": {lv: round(r["baseline"]["state"][lv], 4) for lv in LV},
           "pep_net_change": r["cross_check"]["housing_units_pep"]["state"]["net_change"]}
    for name, s in r["scenarios"].items():
        out[name] = {"benchmark": {lv: round(s["benchmark"][lv], 4) for lv in LV},
                     "increment": {lv: round(s["increment"]["estimate"][lv], 4) for lv in LV},
                     "outcome": s["benchmark"]["outcome"],
                     "top_tornado": s["tornado"][0]["id"] if s["tornado"] else None}
    out["combined"] = {lv: round(r["combined"]["increment"]["estimate"][lv], 4) for lv in LV}
    return out


@pytest.fixture(scope="module")
def zz(zz_state, params):
    return run_state(zz_state, params, ["baseline", "adu", "missing_middle", "tod", "parking", "fees"],
                     META, {}, state_name="Zetaland")


def test_golden_zz(zz):
    got = headline(zz)
    if os.environ.get("HRE_UPDATE_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert _close(got, want), "ZZ headline numbers changed"


def _close(a, b, tol=1e-6) -> bool:
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) <= tol * max(1.0, abs(b))
    return a == b


def check_properties(r: dict) -> list[str]:
    """Properties from the Phase 3 brief that every results file must keep."""
    p = []
    for name, s in r["scenarios"].items():
        if s["benchmark"]["outcome"] not in OUTCOMES or s["increment"]["outcome"] != "permits":
            p.append(f"{name}: outcome labels")
        if s["increment"]["native"]["outcome"] != s["benchmark"]["outcome"]:
            p.append(f"{name}: the native increment must keep the benchmark's label")
        for layer in ("benchmark", "increment", "total"):
            d = s[layer] if layer == "benchmark" else s[layer]["estimate"]
            if not d["low"] <= d["mid"] <= d["high"]:
                p.append(f"{name}.{layer}: low <= mid <= high")
        if any(s["cases"]["no_change"]["estimate"][lv] != 0 for lv in LV):
            p.append(f"{name}: share 0 must give 0")
        if any(s["cases"]["after_horizon"]["estimate"][lv] != 0 for lv in LV):
            p.append(f"{name}: a reform after the horizon must give 0")
        if any(s["increment"]["estimate"][lv] < 0 for lv in LV):
            p.append(f"{name}: negative increment")
    c = r.get("combined")
    if c and any(c["increment"]["estimate"][lv] > c["sum_of_parts"][lv] + 1e-6 for lv in LV):
        p.append("combined exceeds the sum of the parts")
    return p


def test_properties_on_zz(zz):
    assert check_properties(zz) == []
    assert validate_results(zz) == []


@pytest.mark.slow
def test_every_processed_state_runs(params):
    from hre.assumptions.loader import load_elasticities
    from hre.current_law.loader import current_strength
    from hre.current_law.schema import SCENARIOS

    codes = [c for c in ALL_STATES if (PROCESSED / f"{c}.json").exists()]
    if not codes:
        pytest.skip("no processed files (run hre fetch --all and hre build --all)")
    el = load_elasticities()
    for code in codes:
        st = StateInputs.from_json((PROCESSED / f"{code}.json").read_text(encoding="utf-8"))
        law = {s: current_strength(code, s) for s in SCENARIOS}
        r = run_state(st, params, ["baseline", *SCENARIOS], META, {}, state_name=code, law=law, elasticities=el)
        assert validate_results(r) == [], code
        assert check_properties(r) == [], code
