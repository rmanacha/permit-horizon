"""Builder response: percent more homes over five years per 1% fall in cost.

One module for the parking and fee scenarios (decision 35). Units: an
elasticity is already "percent per percent", so a response of 0.75 means a 1%
cost cut (relative to the new-home price) adds 0.75% to five years' permits.

Three routes, documented in docs/methods/builder_response.md:

1. Primary (decision 61): ``builder_response_override`` from the register,
   0 / 0.75 / 2.84 % per 1% (Mayer and Somerville 2000 for low and mid,
   Baum-Snow and Han 2024 for high; ported from Adam Ruege's v2.0 with his
   locators and arithmetic). Used whenever the entry has ``primary: true``.

2. Composite (diagnostic, shown per county):
       eps_s * |eps_d| / (eps_s + |eps_d|) * pass_through * adjustment_share
   the textbook share of a supply shift that shows up as quantity, scaled by how
   much of a fee reaches the price and how much of the response arrives in five
   years. ``eps_s`` is Saiz's metro elasticity (elasticities.yaml) or the
   register default. Caution: Saiz measures the response of the housing STOCK;
   reading the composite as a share of five years' FLOW mixes units, which is
   why it is not the primary route.

3. Stock-elasticity diagnostic (Adam's): stock elasticity x realization share /
   national five-year growth = 0.3 x 0.5 / 0.0529 = 2.84 (the high end of route 1).

``quantity_change`` turns a response into homes:
       base_units x response x (cost_cut / price)
NH check (Adam's mid): 22,690 x 0.75 x 25,000 / (402,500 x 1.2546) = 842.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.schema import StateInputs


def builder_response(eps_s: Any, eps_d: float, pass_through: float, adjustment_share: float) -> Any:
    """Composite route: percent more homes over five years per 1% cost fall (array-friendly)."""
    s = np.asarray(eps_s, dtype=float)
    d = abs(float(eps_d))
    out = s * d / (s + d) * pass_through * adjustment_share
    return float(out) if out.ndim == 0 else out


def stock_route_response(stock_elasticity: float, realization_share: float, growth_5yr: float) -> float:
    """Stock-elasticity diagnostic: percent of five years' building per 1% cost fall."""
    return stock_elasticity * realization_share / growth_5yr


def quantity_change(base_units: Any, cost_cut: Any, price: Any, response: Any) -> Any:
    """Additional homes = base x response x (cost_cut / price). Zero where price is zero or missing."""
    base = np.asarray(base_units, dtype=float)
    cut = np.asarray(cost_cut, dtype=float)
    p = np.asarray(price, dtype=float)
    share = np.divide(cut, p, out=np.zeros(np.broadcast(cut, p).shape), where=p > 0)
    out = base * np.asarray(response, dtype=float) * share
    return float(out) if out.ndim == 0 else out


def county_supply_elasticity(state: StateInputs, params: Params, saiz_by_cbsa: dict[str, float],
                             saiz_by_county: dict[str, float]) -> tuple[np.ndarray, list[str]]:
    """Each county's supply elasticity and where it came from (for the composite route).

    Order: explicit county in the Saiz table; else the county's 2023 CBSA in the table;
    else the register default for metropolitan or other counties. At the low or high
    assumption set every value is scaled by the default's low/mid or high/mid ratio.
    """
    metro_mid = float(params.level_value("supply_elasticity_metro_default", "mid"))
    scale = float(params["supply_elasticity_metro_default"]) / metro_mid
    vals, origin = [], []
    for c in state.counties:
        if c.fips in saiz_by_county:
            vals.append(saiz_by_county[c.fips] * scale)
            origin.append("saiz_county")
        elif c.cbsa and c.cbsa in saiz_by_cbsa:
            vals.append(saiz_by_cbsa[c.cbsa] * scale)
            origin.append("saiz_cbsa")
        elif c.cbsa_type == "metropolitan":
            vals.append(float(params["supply_elasticity_metro_default"]))
            origin.append("metro_default")
        else:
            vals.append(float(params["supply_elasticity_nonmetro"]))
            origin.append("nonmetro_default")
    return np.array(vals), origin


def resolve_response(params: Params, eps_s: Any = None) -> dict[str, Any]:
    """The response the scenarios use, with the route named.

    Primary: the override entry (``primary: true``). The composite is computed alongside
    when county elasticities are given, so the results file can show both.
    """
    composite = None
    if eps_s is not None:
        composite = builder_response(eps_s, params["demand_elasticity"], params["fee_pass_through"],
                                     params["adjustment_share_5yr"])
    if params.entry("builder_response_override").get("primary", False):
        value = float(params["builder_response_override"])
        route = "override"
    else:
        if composite is None:
            raise ValueError("composite route needs county supply elasticities")
        value = composite
        route = "composite"
    return {
        "route": route,
        "value": value,
        "composite": composite,
        "stock_route": stock_route_response(params["stock_supply_elasticity"],
                                            params["stock_realization_share"],
                                            params["us_housing_growth_5yr"]),
        "unit": "percent more homes over 5 years per 1% fall in cost relative to the new-home price",
    }
