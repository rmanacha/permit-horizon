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
