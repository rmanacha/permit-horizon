"""Missing-middle scenario: duplexes to fourplexes allowed on single-family lots.

    net permits = detached homes in central metro counties x single-family-only share x rate per lot
                  (x net-new factor when the rate is the gross ceiling) x code penalty x 5 years;
    increment = that x market adjustment x newly affected share x ramp

Exposure (decision 57): single-family detached homes in counties with ``metro_role ==
"central"``; all metropolitan counties are a sensitivity in ``diagnostics``. Block-group
land area is null, so there is no density threshold. Rate: Portland's Residential Infill
Project, net of demolitions (mid), a zero stress case (low) and the R2.5 gross ceiling
(high). Market adjustment: clip((county value / Portland value) ** gamma, bounds).
Outcome ``net_permits``; it is already in permits, so the conversion is 1.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.scenarios.common import Core, Spec, flat_years, market_adjustment, run_scenario
from hre.schema import StateInputs

IDS = ("mm_rate_per_lot", "mm_sf_only_share", "mm_net_new_factor", "mm_code_penalty", "ramp_missing_middle")


def eligible(state: StateInputs, rule: str = "central") -> np.ndarray:
    if rule == "central":
        return np.array([c.metro_role == "central" for c in state.counties])
    return np.array([c.cbsa_type == "metropolitan" for c in state.counties])


def exposure(state: StateInputs, rule: str = "central", removed: Any = 0.0) -> np.ndarray:
    sf = np.array([c.sf_detached or 0 for c in state.counties], dtype=float)
    return np.maximum(np.where(eligible(state, rule), sf, 0.0) - removed, 0.0)


def lot_rate(params: Params) -> tuple[float, bool]:
    """The rate per lot and whether it was converted from gross (the high end is gross)."""
    rate = float(params["mm_rate_per_lot"])
    gross = params.level_of("mm_rate_per_lot") in params.entry("mm_rate_per_lot").get("gross_at", [])
    return (rate * float(params["mm_net_new_factor"]), True) if gross else (rate, False)


def core(state: StateInputs, params: Params, ctx: dict[str, Any], rule: str = "central") -> Core:
    exp = exposure(state, rule, ctx.get("mm_exposure_removed", 0.0))
    rate, from_gross = lot_rate(params)
    per_lot = float(params["mm_sf_only_share"]) * rate * float(params["mm_code_penalty"])
    horizon = int(params["horizon_years"])
    mkt = market_adjustment([c.median_value for c in state.counties], float(params["mm_source_city_value"]), params)
    notes = [] if exp.any() else ["No central metropolitan county: the missing-middle exposure is zero."]
    return Core(
        benchmark_by_year=flat_years(exp * per_lot, horizon),
        market=mkt,
        conversion=1.0,
        homes_per_permit=float(params["completions_per_permit_2to4"]),
        factors={"exposure": exp.tolist(), "exposure_label": "detached homes in central metropolitan counties",
                 "eligible": eligible(state, rule).tolist(), "rate_per_lot": rate, "rate_from_gross": from_gross,
                 "sf_only_share": float(params["mm_sf_only_share"]),
                 "code_penalty": float(params["mm_code_penalty"]), "market": mkt.tolist(), "notes": notes},
    )


def diagnostics(state: StateInputs, params: Params, ctx: dict[str, Any]) -> dict[str, Any]:
    """Comparison rates on the same exposure chain (mid), and the all-metro sensitivity; never in the band."""
    p = params.all_at("mid")
    exp = exposure(state).sum()
    chain = float(p["mm_sf_only_share"]) * float(p["mm_code_penalty"]) * int(p["horizon_years"])
    out = {lab: {"rate": float(p[pid]), "five_year_units": exp * float(p[pid]) * chain}
           for lab, pid in (("Minneapolis gross", "mm_diag_minneapolis_gross"),
                            ("Spokane, Austin, Charlotte", "mm_diag_cluster"),
                            ("Arlington completed or under construction", "mm_diag_arlington"))}
    allm = core(state, p, {}, rule="metropolitan")
    out["all metropolitan counties (sensitivity)"] = {
        "exposure": float(sum(allm.factors["exposure"])),
        "five_year_benchmark": float(allm.benchmark_by_year.sum())}
    return out


SPEC = Spec(
    name="missing_middle",
    label="Missing middle: two to four homes on single-family lots",
    outcome="net_permits",
    ids=IDS,
    ramp_id="ramp_missing_middle",
    core=core,
    formula=("net permits = detached homes in central metro counties x single-family-only share x rate per lot "
             "x code penalty x 5 years; increment = that x market adjustment x newly affected share x ramp"),
    interpretation=("What Portland's first year of middle housing would mean on this state's single-family "
                    "lots in central metropolitan counties, before any market adjustment."),
    conversion_text="Already in permits (net of demolitions), so the conversion is 1; the net count leaves "
                    "out homes demolished to make room, which a gross permit count would include.",
    limits=(
        ("A county boundary does not say which lots are eligible; some western central counties are mostly "
        "empty land."),
        "The rate comes from one city's first year; Minneapolis saw almost no net effect and Arlington far less.",
        "Permits are not completions; about 92 of every 100 permitted homes are completed (Census NRC).",
        "Results are statewide; the model does not say which places will build.",
    ),
    always=("value_ratio_exponent",),
    linear=("mm_sf_only_share", "mm_code_penalty"),
    diagnostics=diagnostics,
)


def run_missing_middle(state: StateInputs, params: Params, law: dict[str, Any],
                       ctx: dict[str, Any]) -> dict[str, Any]:
    return run_scenario(SPEC, state, params, ctx, law)
