"""ADU scenario: one accessory dwelling unit by right on every single-family lot.

    ADUs completed = detached homes x tier rate (by county median value) x 5 years;
    increment = that x newly affected share x ramp; permits = increment x HCD permits per completion

Exposure: ACS single-family detached homes by county (a parcel count replaces it in Phase 5
where an adapter supplies one within tolerance). Rate: the HCD Table A2 completion rate of
California cities in the county's home-value tier (``tiers.county_adu_rates``). Overlays
(decision 33, rule in decision 71): in the high set a central metropolitan county takes the
larger of its tier high and Seattle's plateau; in the low set every county takes the smaller
of its tier low and Maine's first year; both overlays are permit rates and are converted to
completions with the mid HCD permits per completion. Market adjustment 1.0: the tiers are
already price-dependent. Design modifiers (owner occupancy, ADU fees, discretionary review)
are not separate factors: the benchmark uses the challenge's terms, and a state's current
law enters through the newly affected share (decision 71).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.scenarios.common import Core, Spec, flat_years
from hre.model.tiers import TIER_IDS, county_adu_rates
from hre.schema import StateInputs


def core(state: StateInputs, params: Params, ctx: dict[str, Any]) -> Core:
    exposure = np.array([c.sf_detached or 0 for c in state.counties], dtype=float)
    exposure = exposure - ctx.get("adu_exposure_removed", 0.0)          # combined package only
    exposure = np.maximum(exposure, 0.0)
    t = county_adu_rates([c.median_value for c in state.counties], params)
    rate = np.array(t["rate"], dtype=float)
    ppc_mid = float(params.level_value("adu_permits_per_completion", "mid"))
    seattle = float(params["adu_overlay_seattle"]) / ppc_mid
    maine = float(params["adu_overlay_maine"]) / ppc_mid
    overlay = []
    for j, c in enumerate(state.counties):
        lv = params.level_of(TIER_IDS[int(t["tier"][j]) - 1])
        if lv == "high" and c.metro_role == "central" and seattle > rate[j]:
            rate[j], tag = seattle, "Seattle plateau"
        elif lv == "low" and maine < rate[j]:
            rate[j], tag = maine, "Maine first year"
        else:
            tag = ""
        overlay.append(tag)
    horizon = int(params["horizon_years"])
    notes = [f"{c.fips} {c.name}: {n}" for c, n in zip(state.counties, t["notes"]) if n]
    return Core(
        benchmark_by_year=flat_years(exposure * rate, horizon),
        market=np.ones(len(state.counties)),
        conversion=float(params["adu_permits_per_completion"]),
        homes_per_permit=1.0 / float(params["adu_permits_per_completion"]),
        factors={"exposure": exposure.tolist(), "exposure_label": "single-family detached homes (ACS B25024)",
                 "tier": [int(x) for x in t["tier"]], "rate": rate.tolist(), "overlay": overlay,
                 "rate_unit": "completed ADUs per detached home per year", "notes": notes},
    )


SPEC = Spec(
    name="adu",
    label="Accessory dwelling units by right",
    outcome="completed_homes",
    ids=(*TIER_IDS, "ramp_adu", "adu_permits_per_completion"),
    band=(*TIER_IDS, "ramp_adu"),
    ramp_id="ramp_adu",
    core=core,
    formula=("ADUs completed = detached homes x tier rate x 5 years; increment = that x newly affected "
             "share x ramp; permits = increment x HCD permits per completion"),
    interpretation=("What California cities with similar home values completed, transferred to this "
                    "state's detached homes; it does not subtract what current rules already produce."),
    conversion_text=("Completed ADUs x California HCD permits per completed ADU (two-year lag, 1.18 at "
                     "mid): some permits are never built, so a completed ADU stands for more than one permit."),
    limits=(
        ("The Census Building Permits Survey undercounts ADUs (conversions and many attached units are "
        "not new-building permits), so the baseline and this increment are not measured the same way."),
        "Rates come from California cities and, at the high end, Seattle; uptake elsewhere may be slower.",
        "Results are statewide; the model does not say which places will build.",
        ("In a state with a statewide ADU law the baseline already carries current-law ADUs; the newly "
        "affected share removes that part."),
    ),
    linear=("adu_permits_per_completion",),
)
