"""Fee scenario: development and impact fees cut by half.

    permits = baseline permits x builder response x (fee cut / new-home price)
    fee cut = $50,000 x 50% (the challenge's premise)

Price: county median value x the new-home price ratio. Response: the measured override,
0 / 0.75 / 2.84% more homes over five years per 1% fall in cost relative to the new-home
price (decisions 61, 67). It is defined per 1% cost cut, so fee pass-through, a component
of the composite route, is not applied on top. The composite per county is kept as the
geography check. Low is zero: Mayer and Somerville found no significant impact-fee effect,
and Burge and Ihlanfeldt note that some fees buy approvals that let building happen.

Diagnostics outside the band: the same formula with a typical actual fee (half of NAHB's
$13,627); and the stock-elasticity route (stock x 0.3 x 0.5 x cut / price), which differs
from the flow route by a factor of about five because it applies a long-run stock
elasticity to the whole housing stock instead of to five years of building.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.response import quantity_change, resolve_response
from hre.model.scenarios.common import Core, Spec, run_scenario
from hre.schema import StateInputs

IDS = ("builder_response_override", "new_home_price_ratio", "ramp_immediate")


def fee_cut(params: Params) -> float:
    return float(params["total_fee_per_unit"]) * float(params["fee_cut_share"])


def price(state: StateInputs, params: Params) -> np.ndarray:
    return np.array([c.median_value or 0 for c in state.counties], dtype=float) * float(params["new_home_price_ratio"])


def homes_per_permit(params: Params, by_type: np.ndarray) -> float:
    """Completed homes per permit for the baseline's mix of structure types."""
    t = by_type.sum(axis=0)
    if t.sum() == 0:
        return float(params["completions_per_permit_1unit"])
    w = (t[0] * float(params["completions_per_permit_1unit"])
         + (t[1] + t[2]) * float(params["completions_per_permit_2to4"])
         + t[3] * float(params["completions_per_permit_5plus"]))
    return float(w / t.sum())


def core(state: StateInputs, params: Params, ctx: dict[str, Any], cut: float | None = None) -> Core:
    c = fee_cut(params) if cut is None else cut
    p = price(state, params)
    resp = resolve_response(params, ctx.get("eps_s"))
    base = ctx["baseline_by_type"].sum(axis=1)
    homes = quantity_change(base, c, p, resp["value"])
    horizon = int(params["horizon_years"])
    composite = resp.get("composite")
    return Core(
        benchmark_by_year=np.repeat((np.asarray(homes, dtype=float) / horizon)[None, :], horizon, axis=0),
        market=np.ones(len(state.counties)),
        conversion=1.0,
        homes_per_permit=homes_per_permit(params, ctx["baseline_by_type"]),
        factors={"baseline_permits": base.tolist(), "fee_cut": c, "new_home_price": p.tolist(),
                 "cut_share_of_price": np.divide(c, p, out=np.zeros_like(p), where=p > 0).tolist(),
                 "response": resp["value"], "response_route": resp["route"],
                 "geography_check": None if composite is None else {
                     "composite_per_county": np.atleast_1d(composite).tolist(),
                     "reading": "Composite of elasticities per county (diagnostic): supply-constrained metros "
                                "respond less."},
                 "notes": [f"{s.fips} {s.name}: no median value, so no price and no response"
                           for s in state.counties if not s.median_value]},
    )


def diagnostics(state: StateInputs, params: Params, ctx: dict[str, Any]) -> dict[str, Any]:
    pm = params.all_at("mid")
    flow = float(core(state, pm, ctx).benchmark_by_year.sum())
    actual_cut = float(pm["actual_fee_per_unit"]) * float(pm["fee_cut_share"])
    actual = {lv: float(core(state, pm.at({"builder_response_override": lv}), ctx, cut=actual_cut)
                        .benchmark_by_year.sum()) for lv in ("low", "mid", "high")}
    stock = np.array([ctx["stock"].get(s.fips, 0) for s in state.counties], dtype=float)
    p = price(state, pm)
    share = np.divide(fee_cut(pm), p, out=np.zeros_like(p), where=p > 0)
    stock_route = float((stock * float(pm["stock_supply_elasticity"]) * float(pm["stock_realization_share"])
                         * share).sum())
    return {
        "actual_fee_variant": {"fee_cut": actual_cut, "permits": actual,
                               "reading": "The same formula with half of a typical actual fee (NAHB's $13,627) "
                                          "instead of half of the challenge's $50,000."},
        "stock_route": {"homes": stock_route, "flow_route_mid": flow,
                        "ratio_to_flow": stock_route / flow if flow else None,
                        "reading": ("Stock route: housing stock x 0.3 x 0.5 x cut / price. It applies a long-run "
                                    "stock elasticity to the whole stock rather than to five years of building, "
                                    "so it runs several times the flow route; shown for comparison only.")},
    }


SPEC = Spec(
    name="fees",
    label="Development and impact fees cut in half",
    outcome="cost_response_proxy",
    ids=IDS,
    band=("builder_response_override",),
    ramp_id="ramp_immediate",
    core=core,
    formula="permits = baseline permits x builder response x (fee cut / new-home price); fee cut = $50,000 x 50%",
    interpretation=("A cost-response proxy: the extra permits if builders respond to a $25,000 lower cost per "
                    "home as the measured studies say they respond to cost and price changes."),
    conversion_text="Computed on permits, so the conversion is 1 (the response is a share of baseline permits).",
    limits=(
        ("The low end is zero: Mayer and Somerville found no significant impact-fee effect, and some fees buy "
        "the approvals that let building happen (Burge and Ihlanfeldt)."),
        "Few places charge $50,000; with a typical actual fee the cut is about a quarter as large.",
        "Results are statewide; the model does not say which places will build.",
    ),
    linear=("builder_response_override", "total_fee_per_unit", "fee_cut_share"),
    grid=("builder_response_override", "new_home_price_ratio"),
    diagnostics=diagnostics,
)


def run_fees(state: StateInputs, params: Params, law: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    return run_scenario(SPEC, state, params, ctx, law)
