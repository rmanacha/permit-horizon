"""The exact-rescale contract the web page relies on: components x ratio equals a rerun.

For every scenario and every id in ``components.linear_in``, rescaling the mid increment county
by county (an id in ``linear_counties`` multiplies only the counties listed there) at the
register's low and high values must equal running the engine with that value, which is what
``hre run --set`` does. The web page's TypeScript does the same arithmetic
(web/src/engine/rescale.ts); web/scripts/rescale_equality.mjs checks it against real runs.
"""

import json

import pytest
from typer.testing import CliRunner

from hre.cli import app
from hre.model.run import run_state

META = {"build_id": "x", "vintages": {}, "git_sha": "x", "run_date": "2026-11-03"}
SCENARIOS = ("adu", "missing_middle", "tod", "parking", "fees")


def rescale(comp: dict, pid: str, new: float) -> float:
    """The page's arithmetic, in Python: new = old x value / old value, county by county."""
    old = comp["linear_in"][pid]
    scoped = comp["linear_counties"].get(pid)
    return sum(c["increment_mid_permits"] * (new / old if scoped is None or c["fips"] in scoped else 1.0)
               for c in comp["by_county"])


def run(state, params, name):
    return run_state(state, params, ["baseline", name], META, {}, state_name="Zetaland")["scenarios"][name]


@pytest.fixture(scope="module")
def base(zz_state, params):
    return run_state(zz_state, params, ["baseline", *SCENARIOS], META, {}, state_name="Zetaland")


def test_county_terms_add_up_to_the_increment(base):
    for name, s in base["scenarios"].items():
        comp = s["components"]
        total = sum(c["increment_mid_permits"] for c in comp["by_county"])
        assert total == pytest.approx(comp["increment_mid_permits"], rel=1e-12, abs=1e-12), name
        assert comp["increment_mid_permits"] == s["increment"]["estimate"]["mid"]


@pytest.mark.parametrize("name", SCENARIOS)
def test_rescale_equals_a_rerun_for_every_linear_id(zz_state, params, base, name):
    comp = base["scenarios"][name]["components"]
    assert comp["linear_in"], f"{name} has no linear id"
    for pid in comp["linear_in"]:
        for new in (params.level_value(pid, "low"), params.level_value(pid, "high"), comp["linear_in"][pid] * 0.37):
            rerun = run(zz_state, params.with_values({pid: new}), name)["increment"]["estimate"]["mid"]
            assert rescale(comp, pid, new) == pytest.approx(rerun, rel=1e-9, abs=1e-9), (name, pid, new)


def test_density_factor_scales_only_counties_outside_central_metros(zz_state, base):
    comp = base["scenarios"]["parking"]["components"]
    central = {c.fips for c in zz_state.counties if c.metro_role == "central"}
    assert comp["linear_counties"]["parking_low_density_factor"]
    assert not central & set(comp["linear_counties"]["parking_low_density_factor"])


def test_a_user_value_holds_in_every_assumption_set(zz_state, params):
    s = run(zz_state, params.with_values({"builder_response_override": 2.0}), "fees")
    est = s["increment"]["estimate"]
    assert est["low"] == est["mid"] == est["high"] > 0      # the response is the fee scenario's only band id
    assert s["levels_used"]["mid"]["builder_response_override"] == "user"


def test_hre_run_set_and_level(sample_dir, tmp_path):
    runner = CliRunner()
    base, user = tmp_path / "base.json", tmp_path / "user.json"
    r = runner.invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir), "--out", str(base), "--quiet"])
    assert r.exit_code == 0, r.output
    r = runner.invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir), "--out", str(user), "--quiet",
                            "--set", "fee_cut_share=0.3", "--level", "adu_permits_per_completion=high"])
    assert r.exit_code == 0, r.output
    b, u = json.loads(base.read_text()), json.loads(user.read_text())
    assert "overrides" not in b["meta"]
    assert u["meta"]["overrides"]["set"] == {"fee_cut_share": 0.3}
    assert u["meta"]["overrides"]["level"] == {"adu_permits_per_completion": "high"}
    assert u["meta"]["build_id"] != b["meta"]["build_id"]
    fb, fu = b["scenarios"]["fees"]["components"], u["scenarios"]["fees"]["components"]
    assert rescale(fb, "fee_cut_share", 0.3) == pytest.approx(fu["increment_mid_permits"], rel=1e-9)
    ab, au = b["scenarios"]["adu"]["components"], u["scenarios"]["adu"]["components"]
    assert rescale(ab, "adu_permits_per_completion", 1.4) == pytest.approx(au["increment_mid_permits"], rel=1e-9)
    # components are written unrounded (the rest of the file keeps 4 decimals)
    assert fb["increment_mid_permits"] != round(fb["increment_mid_permits"], 4)
    for bad in (["--set", "not_an_id=1"], ["--set", "fee_cut_share"], ["--level", "ramp_adu=max"],
                ["--set", "ramp_adu=fast"]):
        r = runner.invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir), "--out",
                                str(tmp_path / "x.json"), "--quiet", *bad])
        assert r.exit_code != 0, bad
