"""Tornado and joint cases on a small multiplicative model built from register entries."""

import pytest

from hre.model.sensitivity import joint_case, swingable, tornado

IDS = ["builder_response_override", "new_home_price_ratio", "fee_pass_through", "horizon_years"]


def fee_like(p):
    # homes = 10,000 x response x 25,000 x pass-through / (400,000 x price ratio)
    return 10_000 * p["builder_response_override"] * 25_000 * p["fee_pass_through"] / (
        400_000 * p["new_home_price_ratio"])


def test_swingable_skips_fixed_entries(params):
    assert swingable(params, IDS) == IDS[:3]


def test_tornado_ordered_and_deterministic(params):
    bars = tornado(params, fee_like, IDS)
    assert [b["id"] for b in bars] == ["builder_response_override", "fee_pass_through", "new_home_price_ratio"]
    assert bars == tornado(params, fee_like, IDS)
    top = bars[0]
    assert top["at_low"] == 0.0
    assert top["at_high"] == pytest.approx(10_000 * 2.84 * 25_000 * 1.2 / (400_000 * 1.2546))
    assert top["low_text"] == "0.00% per 1%"
    price = bars[2]
    assert price["favorable_end"] == "low"     # a cheaper new home makes the cut a bigger share


def test_joint_cases_bracket_every_swing(params):
    bars = tornado(params, fee_like, IDS)
    fav = joint_case(params, fee_like, "favorable", IDS)
    unfav = joint_case(params, fee_like, "unfavorable", IDS)
    assert all(fav["value"] >= max(b["at_low"], b["at_high"]) for b in bars)
    assert all(unfav["value"] <= min(b["at_low"], b["at_high"]) for b in bars)
    assert fav["value"] == pytest.approx(10_000 * 2.84 * 25_000 * 1.66 / (400_000 * 1.0))
    assert unfav["value"] == 0.0
    assert "not a likely outcome" in fav["reading"]
