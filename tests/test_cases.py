"""Cases: newly affected share x delay x ramp, by hand."""

import numpy as np
import pytest

from hre.model.cases import increment, named_cases

FLAT = np.full(5, 100.0)
ONES = [1.0] * 5


def test_share_zero_and_long_delay_give_zero():
    assert increment(FLAT, 0.0, 0, ONES).sum() == 0.0
    assert increment(FLAT, 1.0, 5, ONES).sum() == 0.0
    assert increment(FLAT, 1.0, 7, ONES).sum() == 0.0


def test_hand_computed_case():
    # 50% affected, 2-year delay, ramp 25/40/55/70/85%: years 3-5 get 0.25, 0.40, 0.55 of 100 x 0.5
    inc = increment(FLAT, 0.5, 2, [0.25, 0.40, 0.55, 0.70, 0.85])
    assert list(inc) == pytest.approx([0, 0, 12.5, 20.0, 27.5])
    assert inc.sum() == pytest.approx(60.0)


def test_delay_one_keeps_four_fifths_like_adam():
    # Adam's NH ADU middle 2,046.2 over five years -> 1,637.0 with a 1-year delay
    b = np.full(5, 2046.19811 / 5)
    assert increment(b, 1.0, 1, ONES).sum() == pytest.approx(1636.958488)


def test_county_shaped_benchmark():
    b = np.array([[10.0, 20.0]] * 5)          # [years, counties]
    inc = increment(b, 1.0, 1, ONES)
    assert inc.shape == (5, 2) and inc.sum(axis=0) == pytest.approx([40.0, 80.0])


def test_named_cases(params):
    bench = {lv: np.full(5, v) for lv, v in (("low", 50.0), ("mid", 100.0), ("high", 200.0))}
    cases = named_cases(bench, params, current_strength=0.75, strength_note="NH RSA 674:72.",
                        outcome="completed_homes", scenario_ramp_id="ramp_adu")
    d = cases["register_default"]
    assert d["status"] == "register_default" and d["newly_affected_share"] == 0.25
    # mid: 0.25 x 100 x (0.25+0.40+0.55+0.70+0.85) = 68.75
    assert d["estimate"]["mid"] == pytest.approx(68.75)
    # low pairs the low benchmark with the low ramp: 0.25 x 50 x (0.12+0.21+0.36+0.38+0.59)
    assert d["estimate"]["low"] == pytest.approx(0.25 * 50 * 1.66)
    assert cases["no_change"]["estimate"] == {"low": 0.0, "mid": 0.0, "high": 0.0}
    assert cases["after_horizon"]["estimate"]["high"] == 0.0
    assert cases["eligible_50_delay_1"]["estimate"]["mid"] == pytest.approx(0.5 * 100 * 4)
    assert all(c["can_add_to_baseline"] is False for c in cases.values())   # not yet in permits
    assert len(cases) == 12 and any("unchanged" in a for a in cases["no_change"]["assumptions"])


def test_permits_outcome_can_add(params):
    bench = {lv: np.full(5, 10.0) for lv in ("low", "mid", "high")}
    cases = named_cases(bench, params, 0.0, "No statewide law found.", "permits")
    assert cases["register_default"]["can_add_to_baseline"] is True
    assert cases["register_default"]["estimate"]["mid"] == pytest.approx(50.0)
