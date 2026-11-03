"""Baseline backtest: both band rules, by hand and on a 3-state subset (AZ, NH, UT)."""

import json
from pathlib import Path

import pytest

from hre.validation import backtest_baseline as bt

FIXTURE = Path(__file__).parent / "fixtures" / "bps_state_totals_az_nh_ut.json"


@pytest.fixture(scope="module")
def panel():
    d = json.loads(FIXTURE.read_text())["states"]
    return {f: {int(y): float(v) for y, v in s.items()} for f, s in d.items()}


def test_mean3_run_by_hand():
    s = {"99": {y: 100.0 for y in range(2000, 2011)}}
    s["99"].update({2008: 90.0, 2009: 120.0, 2010: 150.0})
    s["99"].update({2011: 200.0, 2012: 200.0, 2013: 200.0, 2014: 200.0, 2015: 200.0})
    (run,) = bt.mean3_runs(s, (2010,))
    assert run.point == 600.0          # (90 + 120 + 150) / 3 x 5
    assert run.actual == 1000.0 and run.ratio == pytest.approx(1000 / 600)


def test_adam_rule_by_hand():
    # 25 years of 100 a year except one slow and one fast year inside the 20-year history
    s = {y: 100.0 for y in range(1981, 2006)}
    s[1990], s[1995] = 50.0, 150.0
    (run,) = bt.adam_runs({"99": s}, origins=(2000,))
    totals = [sum(s[y] for y in range(a, a + 5)) for a in range(1981, 1997)]
    avg = sum(totals) / 16
    assert run.point == 500.0
    assert run.low == pytest.approx(500 * min(totals) / avg)
    assert run.high == pytest.approx(500 * max(totals) / avg)
    assert run.position == "inside"


def test_percentiles_and_coverage_by_hand():
    runs = [bt.Run("99", 2000 + i, 100.0, float(a)) for i, a in enumerate(range(50, 160, 10))]
    lo, hi = bt.percentile_band(runs)          # ratios 0.5 .. 1.5 in steps of 0.1
    assert (lo, hi) == pytest.approx((0.6, 1.4))
    c = bt.coverage(bt.apply_band(runs, lo, hi))
    assert (c["inside"], c["above"], c["below"]) == (9, 1, 1)


def test_three_state_subset_reproduces(panel):
    r = bt.run_backtest(panel)
    assert r["methods"]["mean3"]["n"] == 66
    assert r["methods"]["mean3"]["mdape"] == pytest.approx(0.304291, abs=1e-6)
    assert r["ours"]["p10"] == pytest.approx(0.458453, abs=1e-6)
    assert r["ours"]["p90"] == pytest.approx(1.812254, abs=1e-6)
    assert r["ours"]["test"]["inside"] == 15
    a = r["adam"]["runs"]
    assert (a["n"], a["inside"], a["above"], a["below"]) == (15, 11, 2, 2)


def test_report_renders_both_rules(panel):
    md = bt.render_markdown(bt.run_backtest(panel), "2026-11-03")
    for text in ("Band rule A", "Band rule B", "not a probability", "Plain-language reading"):
        assert text in md
