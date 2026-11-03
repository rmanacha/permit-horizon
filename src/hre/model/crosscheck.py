"""Cross-check panel: Census housing-unit estimates, net change since April 2020 (decision 56).

    net_change = July 1 estimate of the latest year - April 1 2020 estimates base

by county and summed to the state, from ``housing_units_pep`` in the processed input
(Population Estimates Program, Vintage 2025). Shown beside the permit baseline, never
added to it: the estimates are built partly from building permits (plus mobile-home
shipments and an estimated loss rate), so this is a consistency view, not an
independent measurement. Outcome label ``stock_change``.
"""

from __future__ import annotations

from typing import Any

from hre.schema import StateInputs

APRIL_2020_KEY = "2020-04"   # same key the PEP fetcher writes (the engine never imports the pipeline)
LABEL = "Census housing-unit estimates: net change since April 2020"
CAVEAT = ("These estimates are built partly from building permits, so they are a consistency view, "
          "not an independent measurement of homes added.")


def pep_cross_check(state: StateInputs) -> dict[str, Any]:
    counties, notes = [], []
    tot_base = tot_end = 0
    end_year = None
    for c in state.counties:
        pep = c.housing_units_pep
        years = sorted(k for k in pep if k.isdigit())
        if APRIL_2020_KEY not in pep or not years:
            notes.append(f"{c.fips} {c.name}: no April 2020 base or July estimate in the input")
            continue
        last = years[-1]
        end_year = last if end_year is None else min(end_year, last)
        base, end = pep[APRIL_2020_KEY], pep[last]
        tot_base += base
        tot_end += end
        counties.append({"fips": c.fips, "name": c.name, "april_2020": base, f"july_{last}": end,
                         "end_year": int(last), "net_change": end - base,
                         "change_share": (end - base) / base if base else None})
    available = bool(counties)
    return {
        "label": LABEL,
        "available": available,
        "outcome": "stock_change",
        "can_add_to_baseline": False,
        "measure": "July 1 estimate of the latest year minus the April 1 2020 estimates base",
        "end_year": int(end_year) if end_year else None,
        "county": counties,
        "state": ({"april_2020": tot_base, "end": tot_end, "net_change": tot_end - tot_base,
                   "change_share": (tot_end - tot_base) / tot_base if tot_base else None}
                  if available else None),
        "caveat": CAVEAT,
        "source": "Census Population Estimates, CO-EST2025-HU.xlsx (Vintage 2025); decision 56",
        "notes": notes,
    }
