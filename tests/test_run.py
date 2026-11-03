"""Orchestrator, results schema, drivers templates and the hre run command (on ZZ)."""

import json
import time

import pytest
from typer.testing import CliRunner

from hre.cli import app
from hre.model.drivers import NO_LLM_STATEMENT, baseline_decomposition, round_display
from hre.model.run import run_state, validate_results

META = {"build_id": "test", "vintages": {"bps": "x"}, "git_sha": "abc", "run_date": "2026-11-03"}


def test_zz_results_match_the_schema(zz_state, params):
    r = run_state(zz_state, params, ["baseline"], META, {"parameters": {}}, state_name="Zetaland")
    assert validate_results(r) == []
    assert r["scenarios"] == {} and r["no_llm"] == NO_LLM_STATEMENT
    assert r["meta"]["state"] == "ZZ" and r["baseline"]["state"]["mid"] == 1670.0
    json.dumps(r, allow_nan=False)


def test_validator_catches_problems(zz_state, params):
    r = run_state(zz_state, params, ["baseline"], META, {})
    r["baseline"]["outcome"] = "homes"
    r["baseline"]["state"]["low"] = 1e9
    r["scenarios"]["fees"] = {"benchmark": {"low": 1, "mid": 2, "high": 3, "outcome": "cost_response_proxy"},
                              "increment": {"outcome": "cost_response_proxy", "can_add_to_baseline": True}}
    problems = " | ".join(validate_results(r))
    assert "outcome" in problems and "low <= mid <= high" in problems
    assert "missing tornado" in problems and "can_add_to_baseline needs outcome 'permits'" in problems


def test_unknown_and_future_scenarios(zz_state, params):
    with pytest.raises(ValueError):
        run_state(zz_state, params, ["housing_vouchers"], META, {})
    with pytest.raises(NotImplementedError):
        run_state(zz_state, params, ["baseline", "adu"], META, {})


def test_narrative_templates(zz_state, params):
    r = run_state(zz_state, params, ["baseline"], META, {}, state_name="Zetaland")
    text = " ".join(r["baseline"]["narrative"])
    assert "about 1,700 homes over 2026-2030" in text
    assert "not a probability" in text and "Alder County accounts for 83%" in text
    d = baseline_decomposition(r["baseline"])
    assert d["top_county_share"] == pytest.approx(1380 / 1670)
    assert round_display(944) == "940" and round_display(24250) == "24,300"


def test_engine_is_fast(zz_state, params):
    t0 = time.perf_counter()
    for _ in range(51):
        run_state(zz_state, params, ["baseline"], META, {})
    assert time.perf_counter() - t0 < 2.0


def test_cli_run_zz_offline(sample_dir, tmp_path):
    out = tmp_path / "ZZ.json"
    res = CliRunner().invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir),
                                   "--scenarios", "baseline", "--out", str(out)])
    assert res.exit_code == 0, res.output
    r = json.loads(out.read_text())
    assert validate_results(r) == [] and r["meta"]["build_id"]
    assert r["registers_used"]["parameters"]["entries"] >= 30
    res = CliRunner().invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir),
                                   "--scenarios", "baseline,fees", "--out", str(out)])
    assert res.exit_code == 2
