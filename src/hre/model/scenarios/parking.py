"""Parking scenario: no minimum parking requirements for new homes.

    permits = baseline 5+ permits x builder response x (saving per home / new-home price) x density factor
    saving per home = required spaces x (1 - share still built) x cost per structured space

Required spaces: the metro's NZLUD ``parking_median`` (mean of its municipalities' median
requirement per home) where the county's CBSA is covered, else the register fallback of 1.
Price: county median value x the new-home price ratio. Response: the measured override
(decisions 61, 67); the composite of elasticities per county is kept in ``factors`` as the
geography check. Counties that are not central to a metropolitan area get
``parking_low_density_factor`` of the response (car-oriented places change little).
Outcome ``cost_response_proxy``, computed on permits, so the conversion is 1.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.response import quantity_change, resolve_response
from hre.model.scenarios.common import Core, Spec
from hre.schema import StateInputs

IDS = ("builder_response_override", "parking_built_share", "parking_cost_per_space", "new_home_price_ratio",
       "parking_low_density_factor", "ramp_immediate")


def required_spaces(state: StateInputs, params: Params) -> tuple[np.ndarray, list[str]]:
    vals, origin = [], []
    for c in state.counties:
        z = state.zoning_by_cbsa.get(c.cbsa or "", {})
        if z.get("parking_median") is not None:
            vals.append(float(z["parking_median"]))
            origin.append(f"NZLUD {c.cbsa}")
        else:
            vals.append(float(params["parking_required_spaces"]))
            origin.append("register fallback")
    return np.array(vals), origin


def core(state: StateInputs, params: Params, ctx: dict[str, Any]) -> Core:
    spaces, origin = required_spaces(state, params)
    saving = spaces * (1.0 - float(params["parking_built_share"])) * float(params["parking_cost_per_space"])
    price = np.array([c.median_value or 0 for c in state.counties], dtype=float) * float(params["new_home_price_ratio"])
    resp = resolve_response(params, ctx.get("eps_s"))
    density = np.array([1.0 if c.metro_role == "central" else float(params["parking_low_density_factor"])
                        for c in state.counties])
    base = ctx["baseline_by_type"][:, 3]                       # 5+ unit permits over five years
    homes = quantity_change(base, saving, price, resp["value"]) * density
    horizon = int(params["horizon_years"])
    notes = [f"{c.fips} {c.name}: no median value, so no price and no response" for c in state.counties
             if not c.median_value]
    if not base.any():
        notes.append("No permits in 5+ unit buildings in the baseline: the parking response is zero.")
    return Core(
        benchmark_by_year=np.repeat((homes / horizon)[None, :], horizon, axis=0),
        market=np.ones(len(state.counties)),
        conversion=1.0,
        homes_per_permit=float(params["completions_per_permit_5plus"]),
        factors={"baseline_5plus_permits": base.tolist(), "required_spaces": spaces.tolist(),
                 "spaces_source": origin, "saving_per_home": saving.tolist(), "new_home_price": price.tolist(),
                 "saving_share_of_price": np.divide(saving, price, out=np.zeros_like(price), where=price > 0).tolist(),
                 "density_factor": density.tolist(), "response": resp["value"], "response_route": resp["route"],
                 "geography_check": _composite(resp), "notes": notes},
        linear_counties={"parking_low_density_factor": [c.metro_role != "central" for c in state.counties]},
    )


def _composite(resp: dict[str, Any]) -> Any:
    c = resp.get("composite")
    if c is None:
        return None
    return {"composite_per_county": np.atleast_1d(c).tolist(),
            "reading": "Composite of elasticities per county (diagnostic): supply-constrained metros respond less."}


SPEC = Spec(
    name="parking",
    label="No minimum parking requirements",
    outcome="cost_response_proxy",
    ids=IDS,
    band=("builder_response_override",),
    ramp_id="ramp_immediate",
    core=core,
    formula=("permits = baseline 5+ permits x builder response x (required spaces x (1 - share still built) x "
             "cost per space / new-home price) x density factor"),
    interpretation=("A cost-response proxy: the extra apartment permits if builders respond to the parking "
                    "they no longer must build as they respond to any cost cut."),
    conversion_text="Computed on permits, so the conversion is 1 (the response is a share of baseline permits).",
    limits=(
        ("The builder response is measured for cost changes in general, not for parking; the low end is no "
        "response."),
        ("Where parking is cheap surface parking, builders keep building it; counties outside metropolitan "
        "cores get half the response at mid."),
        "Results are statewide; the model does not say which places will build.",
    ),
    linear=("builder_response_override", "parking_cost_per_space", "parking_low_density_factor"),
    grid=("builder_response_override", "parking_built_share", "parking_cost_per_space", "new_home_price_ratio"),
)
