"""Transit-oriented density scenario: more homes allowed near rail, streetcar and ferry stops.

    stock change = homes in block groups within 0.5 mile of a major stop x rate per home x 5 years;
    increment = that x market adjustment x newly affected share x ramp;
    permits = increment / completed homes per permit (5+ units)

Exposure: housing units in block groups whose 2020 center of population lies within
``tod_distance_miles`` of a rail, streetcar or ferry stop (decision 48; a quarter mile is
the low end). Bus rapid transit cannot be identified, so it is not counted. Rate: Kestelman's
Los Angeles citywide estimate (mid), zero after Chicago (low), Stacy et al.'s broad-reform
association (high); the local boundary rate is a diagnostic only. Market adjustment against
Los Angeles's median value. Outcome ``stock_change``: homes added to the stock, so permits =
homes / completions per permit for 5+ unit buildings.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.scenarios.common import Core, Spec, flat_years, market_adjustment, run_scenario
from hre.schema import StateInputs

IDS = ("tod_rate_per_home", "tod_distance_miles", "ramp_tod")   # conversion held at mid (see SPEC)


def near_homes(state: StateInputs, miles: float, field: str = "housing_units") -> np.ndarray:
    """[counties] homes (or another block-group count) within ``miles`` of a major stop."""
    idx = {c.fips: j for j, c in enumerate(state.counties)}
    out = np.zeros(len(state.counties))
    for b in state.block_groups:
        d = b.dist_major_stop_miles
        if d is not None and d <= miles and b.county_fips in idx:
            out[idx[b.county_fips]] += getattr(b, field) or 0
    return out


def core(state: StateInputs, params: Params, ctx: dict[str, Any]) -> Core:
    miles = float(params["tod_distance_miles"])
    exp = near_homes(state, miles)
    horizon = int(params["horizon_years"])
    mkt = market_adjustment([c.median_value for c in state.counties], float(params["tod_source_city_value"]), params)
    cpp = float(params["completions_per_permit_5plus"])
    notes = [] if exp.any() else [(f"No block group within {miles} mile of a rail, streetcar or ferry stop: "
                                  "the TOD exposure is zero.")]
    return Core(
        benchmark_by_year=flat_years(exp * float(params["tod_rate_per_home"]), horizon),
        market=mkt,
        conversion=1.0 / cpp,
        homes_per_permit=cpp,
        factors={"exposure": exp.tolist(), "exposure_label": f"homes within {miles} mile of a major stop",
                 "distance_miles": miles, "rate": float(params["tod_rate_per_home"]), "market": mkt.tolist(),
                 "notes": notes},
    )


def diagnostics(state: StateInputs, params: Params, ctx: dict[str, Any]) -> dict[str, Any]:
    p = params.all_at("mid")
    horizon = int(p["horizon_years"])
    half = near_homes(state, 0.5).sum()
    quarter = near_homes(state, 0.25).sum()
    return {
        "homes_within_half_mile": float(half),
        "homes_within_quarter_mile": float(quarter),
        "boundary_rate_case": {"rate": float(p["tod_boundary_rate"]),
                               "five_year_stock_change": float(half * float(p["tod_boundary_rate"]) * horizon),
                               "note": "Kestelman's local boundary estimate; may include homes that moved "
                                       "from nearby areas, so it is not added anywhere."},
    }


SPEC = Spec(
    name="tod",
    label="Transit-oriented density near rail and ferry stops",
    outcome="stock_change",
    ids=IDS,
    ramp_id="ramp_tod",
    core=core,
    formula=("stock change = homes within half a mile of a rail or ferry stop x rate per home x 5 years; "
             "increment = that x market adjustment x newly affected share x ramp; permits = homes / 0.79"),
    interpretation=("The whole-area housing response measured around Los Angeles transit, transferred to "
                    "this state's homes near rail and ferry stops."),
    conversion_text=("Homes added / completed homes per permit for 5+ unit buildings (Census NRC, 0.79 at "
                     "mid): about five permits for every four homes completed."),
    limits=(
        ("Bus rapid transit cannot be identified in the National Transit Map, so only rail, streetcar and "
        "ferry stops count."),
        ("In Los Angeles applications rose sharply but new supply did not (Kestelman); in Chicago permits did "
        "not rise (Freemark), so the low end is zero."),
        "Results are statewide; the model does not say which places will build.",
    ),
    always=("value_ratio_exponent",),
    linear=("tod_rate_per_home",),
    diagnostics=diagnostics,
)


def run_tod(state: StateInputs, params: Params, law: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    return run_scenario(SPEC, state, params, ctx, law)
