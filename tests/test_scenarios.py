"""The five scenarios on the synthetic state ZZ, by hand, plus the brief's properties.

ZZ: Alder County (99001, central metro, median value $350,000, 12,000 detached homes) and
Birch County (99003, outside any CBSA, $250,000, 8,000 detached). No current-law file, so
every scenario's newly affected share is 1.
"""

import copy

import numpy as np
import pytest

from hre.model.baseline import baseline
from hre.model.run import DEFAULT_LAW, run_state, scenario_context, validate_results
from hre.model.scenarios import SPECS, fees
from hre.model.scenarios.common import evaluate, level_set, run_scenario

META = {"build_id": "x", "vintages": {}, "git_sha": "x", "run_date": "2026-11-03"}
ALL = ["baseline", "adu", "missing_middle", "tod", "parking", "fees"]


@pytest.fixture(scope="module")
def zz_results(zz_state, params):
    return run_state(zz_state, params, ALL, META, {}, state_name="Zetaland")


@pytest.fixture(scope="module")
def ctx(zz_state, params):
    return scenario_context(zz_state, params, baseline(zz_state, params))


def test_results_validate_and_layers_are_ordered(zz_results):
    assert validate_results(zz_results) == []
    for name, s in zz_results["scenarios"].items():
        for layer in (s["benchmark"], s["increment"]["estimate"], s["total"]["estimate"]):
            assert layer["low"] <= layer["mid"] <= layer["high"], name
        assert s["increment"]["outcome"] == "permits" and s["increment"]["can_add_to_baseline"]
        assert s["benchmark"]["outcome"] != "permits" or name == "baseline"


def test_adu_by_hand(zz_results, params):
    s = zz_results["scenarios"]["adu"]
    rate = params["adu_rate_tier_1"]                       # both counties are tier 1 (<= $430,100)
    assert s["benchmark"]["mid"] == pytest.approx(20000 * rate * 5)
    ramp_sum = sum(params["ramp_adu"])                       # 0.25 + 0.40 + 0.55 + 0.70 + 0.85 = 2.75
    native = 20000 * rate * ramp_sum
    assert s["increment"]["native"]["mid"] == pytest.approx(native)
    assert s["increment"]["estimate"]["mid"] == pytest.approx(native * params["adu_permits_per_completion"])
    # high set: Alder is central, so it takes Seattle's plateau as completions: 0.0058 / 1.18
    alder_high = s["benchmark"]["by_county"][0]["high"]
    assert alder_high == pytest.approx(12000 * 0.0058 / params["adu_permits_per_completion"] * 5)


def test_missing_middle_by_hand(zz_results, params):
    s = zz_results["scenarios"]["missing_middle"]
    bench = 12000 * 0.8 * 0.001705 * 0.9 * 5               # only Alder is central
    assert s["benchmark"]["mid"] == pytest.approx(bench)
    market = (350000 / 581500) ** 0.5
    assert s["increment"]["estimate"]["mid"] == pytest.approx(bench * market)
    assert s["benchmark"]["by_county"][1]["mid"] == 0.0     # Birch is not in a metro
    # high: the gross ceiling times the net-new factor (0.83), code penalty 1.0, share 0.9
    assert s["benchmark"]["high"] == pytest.approx(12000 * 0.9 * 0.004 * 0.83 * 1.0 * 5)


def test_tod_by_hand(zz_results, params):
    s = zz_results["scenarios"]["tod"]
    homes = 600 + 450                                        # Alder block groups within 0.5 mile
    assert s["benchmark"]["mid"] == pytest.approx(homes * 0.000117 * 5)
    market = (350000 / 921200) ** 0.5
    assert s["increment"]["estimate"]["mid"] == pytest.approx(homes * 0.000117 * 5 * market / 0.79)


def test_parking_by_hand(zz_results, params, ctx):
    s = zz_results["scenarios"]["parking"]
    u5 = ctx["baseline_by_type"][:, 3]
    alder = u5[0] * 0.75 * (1.5 * 0.21 * 52000) / (350000 * 1.2546)          # NZLUD 1.5 spaces
    birch = u5[1] * 0.75 * (1.0 * 0.21 * 52000) / (250000 * 1.2546) * 0.5    # fallback 1 space, density 0.5
    assert s["increment"]["estimate"]["mid"] == pytest.approx(alder + birch)
    assert s["factors"]["spaces_source"] == ["NZLUD 99900", "register fallback"]


def test_fees_by_hand(zz_results, ctx):
    s = zz_results["scenarios"]["fees"]
    base = ctx["baseline_by_type"].sum(axis=1)
    want = base[0] * 0.75 * 25000 / (350000 * 1.2546) + base[1] * 0.75 * 25000 / (250000 * 1.2546)
    assert s["increment"]["estimate"]["mid"] == pytest.approx(want)
    assert s["increment"]["estimate"]["low"] == 0.0          # Mayer and Somerville: no significant effect
    d = s["diagnostics"]
    assert d["actual_fee_variant"]["fee_cut"] == pytest.approx(0.5 * 13627)
    assert d["stock_route"]["ratio_to_flow"] > 1


def test_fees_reproduce_adams_nh_number(zz_state, params):
    """Adam's NH fee mid with his inputs: 22,690 x 0.75 x 25,000 / (402,500 x 1.2546) = 842."""
    s = copy.deepcopy(zz_state)
    s.counties = s.counties[:1]
    s.counties[0].median_value = 402500
    ctx = {"baseline_by_type": np.array([[22690.0, 0, 0, 0]]), "eps_s": None}
    c = fees.core(s, params.all_at("mid"), ctx)
    assert c.benchmark_by_year.sum() == pytest.approx(842, abs=0.5)


def test_increment_zero_when_current_law_is_full(zz_state, params, ctx):
    law = {**DEFAULT_LAW, "current_strength": 1.0, "source": "register"}
    for spec in SPECS.values():
        r = run_scenario(spec, zz_state, params, ctx, law)
        assert r["increment"]["estimate"] == {"low": 0.0, "mid": 0.0, "high": 0.0}, spec.name
        assert r["benchmark"]["mid"] >= 0                  # the benchmark is unchanged by current law


def test_cases_agree_with_the_increment(zz_results):
    for name, s in zz_results["scenarios"].items():
        d = s["cases"]["register_default"]["estimate_permits"]
        for lv in ("low", "mid", "high"):
            assert d[lv] == pytest.approx(s["increment"]["estimate"][lv]), name
        assert s["cases"]["after_horizon"]["estimate_permits"]["high"] == 0.0


def test_tod_no_stops_gives_zero_and_more_stops_more(zz_state, params, ctx):
    far = copy.deepcopy(zz_state)
    for b in far.block_groups:
        b.dist_major_stop_miles = 99.0
    assert evaluate(SPECS["tod"], far, params, ctx, 1.0)["permits"] == 0.0
    near = copy.deepcopy(zz_state)
    for b in near.block_groups:
        b.dist_major_stop_miles = 0.1
    base = evaluate(SPECS["tod"], zz_state, params, ctx, 1.0)["permits"]
    assert evaluate(SPECS["tod"], near, params, ctx, 1.0)["permits"] > base


def test_parking_zero_without_apartment_baseline(zz_state, params, ctx):
    c = dict(ctx)
    c["baseline_by_type"] = ctx["baseline_by_type"].copy()
    c["baseline_by_type"][:, 3] = 0.0
    assert evaluate(SPECS["parking"], zz_state, params, c, 1.0)["permits"] == 0.0


def test_monotone_in_the_rate(zz_state, params, ctx):
    for spec, pid in ((SPECS["missing_middle"], "mm_rate_per_lot"), (SPECS["tod"], "tod_rate_per_home"),
                      (SPECS["fees"], "builder_response_override")):
        lo, hi = (evaluate(spec, zz_state, params.with_values({pid: v}), ctx, 1.0)["permits"] for v in (0.001, 0.002))
        assert hi >= lo


def test_level_sets_follow_direction(params):
    s = level_set(params, ("parking_built_share", "builder_response_override"), "high")
    assert s.level_of("parking_built_share") == "low"       # direction -1: fewer spaces built raises the result
    assert s.level_of("builder_response_override") == "high"
