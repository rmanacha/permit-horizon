"""Builder response: hand-computed cases and Adam's NH fee example."""

import numpy as np
import pytest

from hre.assumptions.loader import load_elasticities
from hre.model.response import (
    builder_response,
    county_supply_elasticity,
    quantity_change,
    resolve_response,
    stock_route_response,
)


def test_composite_by_hand():
    # 1.75 x 0.65 / (1.75 + 0.65) = 0.473958; x 1.2 x 0.75 = 0.426563
    assert builder_response(1.75, -0.65, 1.2, 0.75) == pytest.approx(0.4265625)
    # perfectly inelastic supply: nothing moves
    assert builder_response(0.0, -0.65, 1.2, 0.75) == 0.0
    arr = builder_response(np.array([0.75, 1.61]), -0.65, 1.0, 1.0)
    assert arr == pytest.approx([0.75 * 0.65 / 1.4, 1.61 * 0.65 / 2.26])


def test_stock_route_matches_adams_high():
    assert stock_route_response(0.3, 0.5, 0.0529) == pytest.approx(2.8355, abs=1e-4)


def test_quantity_change_nh_fee_example():
    # Adam's NH mid: 22,690 x 0.75 x 25,000 / (402,500 x 1.2546) = 842.5
    homes = quantity_change(22689.68, 25000, 402500 * 1.2546, 0.75)
    assert homes == pytest.approx(842.48, abs=0.05)
    assert quantity_change(1000, 0, 400000, 0.75) == 0.0
    assert quantity_change(np.array([1000.0, 1000.0]), 25000, np.array([0.0, 500000.0]), 1.0) == \
        pytest.approx([0.0, 50.0])


def test_override_is_primary_and_low_is_zero(params):
    r = resolve_response(params)
    assert (r["route"], r["value"]) == ("override", 0.75)
    assert resolve_response(params.at({"builder_response_override": "low"}))["value"] == 0.0
    assert resolve_response(params.at({"builder_response_override": "high"}))["value"] == 2.84


def test_composite_route_when_override_not_primary(params, zz_state):
    entries = {k: dict(v) for k, v in params.entries.items()}
    entries["builder_response_override"]["primary"] = False
    p2 = type(params)(entries)
    eps, origin = county_supply_elasticity(zz_state, p2, *load_elasticities())
    assert origin == ["metro_default", "nonmetro_default"]   # CBSA 99900 is not in Saiz
    assert list(eps) == [1.75, 3.0]
    r = resolve_response(p2, eps)
    assert r["route"] == "composite"
    assert r["value"] == pytest.approx([1.75 * 0.65 / 2.4 * 0.9, 3.0 * 0.65 / 3.65 * 0.9])


def test_saiz_scaling_at_low(params, zz_state):
    _by_cbsa, by_county = load_elasticities()
    eps_low, _ = county_supply_elasticity(zz_state, params.at({"supply_elasticity_metro_default": "low"}),
                                          {"99900": 0.75}, by_county)
    assert eps_low[0] == pytest.approx(0.75 * 0.6 / 1.75)
