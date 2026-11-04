"""Combined package: "if all five passed together (illustration)" (decision 45: first to cut).

Rules, each applied at the same assumption set (low with low, high with high):

1. Transit first: the detached homes in block groups within the TOD distance of a major
   stop leave the missing-middle exposure (those lots are counted under TOD).
2. Missing middle before ADUs: the lots redeveloped under missing middle (its net units
   divided by Portland's 3.35 units per lot) leave the ADU exposure.
3. Parking and fees share one builder response: the parking saving and the fee cut are one
   cost cut on each apartment permit, applied once. The response is linear in the cut, so
   this equals parking plus fees exactly; the rule is stated so nobody counts it twice.
4. Totals only in permits (each scenario's converted increment); native units are not mixed.

Result <= sum of the parts, asserted. Adam Ruege's v2.0 does not combine reforms ("the
results cannot be added across reforms"); this view is labeled an illustration for that reason.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.model.scenarios import SPECS
from hre.model.scenarios.common import LEVEL_KEYS, evaluate, level_set
from hre.model.scenarios.tod import near_homes
from hre.schema import StateInputs

LABEL = "If all five passed together (illustration)"
RULES = (
    ("Detached homes within the transit distance of a rail or ferry stop count under transit-oriented "
    "density, not missing middle."),
    "Lots redeveloped as missing middle (net units / 3.35 units per lot) cannot also get an ADU.",
    ("The parking saving and the fee cut are one cost cut on each apartment permit, applied once "
    "(the response is proportional to the cut, so this equals the sum of the two)."),
    "Totals are added only in permits, after each scenario's conversion.",
)
LIMITS = (
    ("An illustration, not a forecast of a package: reforms interact in ways no study has measured "
    "together. A teammate's earlier prototype does not combine them at all: \"the results cannot be "
    "added across reforms.\""),
    "Results are statewide; the model does not say which places will build.",
)


def combined(state: StateInputs, params: Params, ctx: dict[str, Any], law: dict[str, dict[str, Any]]) -> dict[str, Any]:
    shares = {n: 1.0 - float(law.get(n, {}).get("current_strength", 0.0)) for n in SPECS}
    est, parts, solo, adj = {}, {}, {}, {}
    for lv in LEVEL_KEYS:
        p = {n: level_set(params, s.band, lv) for n, s in SPECS.items()}
        alone = {n: evaluate(s, state, p[n], ctx, shares[n])["permits"] for n, s in SPECS.items()}
        miles = float(p["tod"]["tod_distance_miles"])
        central = np.array([c.metro_role == "central" for c in state.counties])
        tod_sf = near_homes(state, miles, "sf_detached") * central
        mm = evaluate(SPECS["missing_middle"], state, p["missing_middle"], {**ctx, "mm_exposure_removed": tod_sf},
                      shares["missing_middle"])
        lots = mm["inc"].sum(axis=0) / float(params["mm_units_per_lot"])
        adu = evaluate(SPECS["adu"], state, p["adu"], {**ctx, "adu_exposure_removed": lots}, shares["adu"])
        got = {"adu": adu["permits"], "missing_middle": mm["permits"], "tod": alone["tod"],
               "parking": alone["parking"], "fees": alone["fees"]}
        est[lv] = float(sum(got.values()))
        parts[lv], solo[lv] = got, alone
        adj[lv] = {"detached_homes_moved_from_missing_middle_to_tod": float(tod_sf.sum()),
                   "lots_removed_from_adu_exposure": float(lots.sum())}
        if est[lv] > sum(alone.values()) + 1e-9:
            raise AssertionError(f"combined {est[lv]} exceeds the sum of the parts {sum(alone.values())}")
    base = ctx["baseline_state"]
    return {
        "label": LABEL,
        "outcome": "permits",     # every number in the block (parts, sums, overlaps) is in permits
        "increment": {"estimate": est, "outcome": "permits", "can_add_to_baseline": True,
                      "status": "register_default"},
        "total": {"estimate": {lv: base[lv] + est[lv] for lv in LEVEL_KEYS}, "outcome": "permits",
                  "pairing_rule": "Low with low, mid with mid, high with high; no probability is assigned."},
        "parts_in_package": parts,
        "parts_alone": solo,
        "sum_of_parts": {lv: float(sum(solo[lv].values())) for lv in LEVEL_KEYS},
        "overlap_removed": {lv: float(sum(solo[lv].values()) - est[lv]) for lv in LEVEL_KEYS},
        "adjustments": adj,
        "rules": list(RULES),
        "limits": list(LIMITS),
    }
