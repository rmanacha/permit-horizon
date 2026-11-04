"""Predictions for frozen checks, from the same engine code as the forecasts.

``adu_place_prediction`` runs the ADU scenario's ``core`` (``hre.model.scenarios.adu``) on one
place treated as a county: its ACS 2020-2024 detached homes and median value, and the metro role
of the county it sits in, at the register's low, mid and high sets (``level_set`` over the
scenario's band ids, exactly as ``run_scenario`` does). The result is the benchmark at steady
state: completed ADUs a year, and permits a year (times the register's permits per completion).

``baseline_year_prediction`` reads the committed web bundle's baseline for one forecast year.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hre.assumptions.loader import load_params
from hre.data.fetch_acs import PREFIX_PLACE, load_geo_fields, load_geo_names
from hre.model.scenarios.adu import SPEC as ADU
from hre.model.scenarios.common import level_set
from hre.schema import CountyInputs, StateInputs

LEVELS = ("low", "mid", "high")


def place_inputs(state_fips: str, place_geoid: str, county: CountyInputs, data_dir: Path | None = None) -> CountyInputs:
    """A one-place 'county' with the place's ACS detached homes and median value."""
    fields = load_geo_fields(state_fips, PREFIX_PLACE, data_dir, tables=("b25024", "b25077"))[place_geoid]
    name = load_geo_names(PREFIX_PLACE, state_fips, data_dir)[place_geoid]
    return CountyInputs(fips=county.fips, name=name, cbsa=county.cbsa, cbsa_type=county.cbsa_type,
                        metro_role=county.metro_role, sf_detached=fields["sf_detached"],
                        median_value=fields["median_value"])


def adu_place_prediction(state: StateInputs, place: CountyInputs) -> dict[str, Any]:
    params = load_params()
    one = StateInputs(state=state.state, state_fips=state.state_fips, counties=[place])
    out: dict[str, Any] = {"place": place.name, "detached_homes": place.sf_detached,
                           "median_value": place.median_value, "metro_role": place.metro_role}
    for lv in LEVELS:
        p = level_set(params, ADU.band, lv)
        c = ADU.core(one, p, {})
        per_year = float(c.benchmark_by_year[0].sum())
        out[lv] = {"completions_per_year": per_year, "permits_per_year": per_year * c.conversion,
                   "rate": c.factors["rate"][0], "tier": c.factors["tier"][0],
                   "overlay": c.factors["overlay"][0], "permits_per_completion": c.conversion}
    return out


def baseline_year_prediction(bundle_dir: Path, year: int) -> dict[str, dict[str, float]]:
    """state -> {low, mid, high} permits for one forecast year, from web/public/results/{ST}.json."""
    out = {}
    for p in sorted(bundle_dir.glob("[A-Z][A-Z].json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        row = next(y for y in r["baseline"]["state"]["by_year"] if y["year"] == year)
        out[p.stem] = {k: float(row[k]) for k in LEVELS}
    return out
