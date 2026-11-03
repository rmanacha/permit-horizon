"""Baseline, hand-computed on the synthetic state ZZ (data/sample)."""

import pytest

from hre.model.baseline import baseline


def test_zz_point_by_hand(zz_state, params):
    b = baseline(zz_state, params)
    assert b["outcome"] == "permits"
    assert b["window_years"] == [2023, 2024, 2025] and b["forecast_years"] == [2026, 2027, 2028, 2029, 2030]
    alder, birch = b["county"]
    # Alder: 1-unit (170+180+190)/3 = 180, 2-unit 10, 3-4 unit 6, 5+ 80 per year; x 5
    assert alder["by_type"] == {"u1": 900.0, "u2": 50.0, "u34": 30.0, "u5": 400.0}
    assert alder["mid"] == 1380.0
    # Birch: 1-unit (54+56+58)/3 = 56, 2-unit 2; x 5
    assert birch["mid"] == 290.0
    assert b["state"]["mid"] == 1670.0


def test_zz_band_and_flat_years(zz_state, params):
    b = baseline(zz_state, params)
    lo = params.level_value("baseline_band_ratio", "low")
    hi = params.level_value("baseline_band_ratio", "high")
    assert b["state"]["low"] == pytest.approx(1670 * lo)
    assert b["state"]["high"] == pytest.approx(1670 * hi)
    assert b["county"][0]["low"] == pytest.approx(1380 * lo)       # state ratios applied to counties
    years = b["state"]["by_year"]
    assert [y["mid"] for y in years] == [334.0] * 5
    assert sum(y["high"] for y in years) == pytest.approx(b["state"]["high"])
    assert "not a probability" in b["band_rule"]["reading"]


def test_missing_county_year_counts_as_zero_and_is_noted(zz_state, params):
    import copy

    s = copy.deepcopy(zz_state)
    del s.counties[1].permits["2024"]
    b = baseline(s, params)
    assert b["county"][1]["mid"] == pytest.approx((54 + 58) / 3 * 5 + (2 + 2) / 3 * 5)
    assert any("Birch" in n and "2024" in n for n in b["notes"])


def test_window_from_register(zz_state, params):
    b = baseline(zz_state, params.with_values({"baseline_window_years": 1}))
    assert b["county"][0]["by_type"]["u1"] == 950.0   # 190 x 5


def test_swing_band_by_hand():
    from hre.model.baseline import swing_band

    hist = {str(y): 100 for y in range(2001, 2026)}
    hist["2010"], hist["2015"] = 50, 150
    b = swing_band(hist, 20, 5)
    windows = [sum(hist[str(y)] for y in range(a, a + 5)) for a in range(2006, 2022)]
    avg = sum(windows) / 16
    assert b["point"] == 500.0 and b["point_years"] == [2021, 2025]
    assert b["low"] == pytest.approx(500 * min(windows) / avg)
    assert b["high"] == pytest.approx(500 * max(windows) / avg)
    assert swing_band({str(y): 100 for y in range(2010, 2026)}, 20, 5) is None   # 16 years only


def test_engine_swing_band_equals_the_backtested_rule():
    import json
    from pathlib import Path

    from hre.model.baseline import swing_band
    from hre.validation.backtest_baseline import adam_runs

    d = json.loads((Path(__file__).parent / "fixtures" / "bps_state_totals_az_nh_ut.json").read_text())
    nh = d["states"]["33"]
    (run,) = adam_runs({"33": {int(y): float(v) for y, v in nh.items()}}, origins=(2020,))
    eng = swing_band({y: v for y, v in nh.items() if int(y) <= 2020}, 20, 5)
    assert (eng["point"], eng["low"], eng["high"]) == pytest.approx((run.point, run.low, run.high))


def test_alternative_band_is_separate_and_explained(zz_state, params):
    b = baseline(zz_state, params)
    alt = b["alternative_band"]
    assert alt["available"] and alt["applied_to_counties"] is False
    assert alt["low"] <= alt["mid"] <= alt["high"]
    assert b["state"]["mid"] == 1670.0                     # the headline is untouched
    assert "181 of 255" in alt["how_it_did"] and "headline" in alt["why_not_headline"]
    import copy

    short = copy.deepcopy(zz_state)
    short.state_permits_history = {}
    assert baseline(short, params)["alternative_band"]["available"] is False
