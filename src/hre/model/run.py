"""Orchestrator: one state's results file in the three-layer schema.

Pure: the caller (``hre run``) reads the processed input with
``StateInputs.from_json``, loads the registers, collects meta (git sha, run date,
digests) and writes the file. Layout and field meanings: docs/methods/results_schema.md.

    {results_schema_version, meta{...}, baseline{...}, cross_check{housing_units_pep{...}},
     scenarios{<name>{benchmark{low,mid,high,outcome,interpretation},
                      increment{status,estimate,assumptions[],outcome,can_add_to_baseline},
                      total{estimate,pairing_rule}, cases{...}, tornado[],
                      joint{favorable,unfavorable}, narrative[]}},
     registers_used{...}, no_llm}

Phase 2 filled the baseline; Phase 3 fills ``scenarios`` (one module per scenario under
``hre.model.scenarios``) and the combined package.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from hre.model.baseline import baseline
from hre.model.combine import combined as combined_package
from hre.model.crosscheck import pep_cross_check
from hre.model.drivers import (
    NO_LLM_STATEMENT,
    alternative_band_narrative,
    baseline_narrative,
    cross_check_narrative,
    scenario_narrative,
)
from hre.model.params import LEVELS, Params
from hre.model.response import county_supply_elasticity
from hre.model.scenarios import SPECS
from hre.model.scenarios.common import run_scenario
from hre.schema import OUTCOMES, PERMIT_KEYS, StateInputs

RESULTS_SCHEMA_VERSION = "1"
KNOWN_SCENARIOS = ("baseline", *SPECS)
SCENARIO_KEYS = ("benchmark", "increment", "total", "cases", "tornado", "joint", "narrative")


DEFAULT_LAW = {"current_strength": 0.0, "newly_affected_share": 1.0, "source": "default",
               "note": "No statewide law found; local permissions unverified.", "human_review": None, "file": None}


def scenario_context(state: StateInputs, params: Params, b: dict[str, Any],
                     elasticities: tuple[dict[str, float], dict[str, float]] | None = None) -> dict[str, Any]:
    """What every scenario reads besides the inputs: baseline arrays, elasticities, stock."""
    ctx: dict[str, Any] = {
        "forecast_years": b["forecast_years"],
        "baseline_state": {k: b["state"][k] for k in LEVELS},
        "baseline_by_type": np.array([[c["by_type"][k] for k in PERMIT_KEYS] for c in b["county"]], dtype=float),
        "stock": {c.fips: c.housing_units_pep[max(k for k in c.housing_units_pep if k.isdigit())]
                  for c in state.counties if any(k.isdigit() for k in c.housing_units_pep)},
        "eps_s": None,
    }
    if elasticities is not None:
        ctx["eps_s"], ctx["eps_origin"] = county_supply_elasticity(state, params, *elasticities)
    return ctx


def run_state(state: StateInputs, params: Params, scenarios: list[str], meta: dict[str, Any],
              registers_used: dict[str, Any], state_name: str | None = None,
              law: dict[str, dict[str, Any]] | None = None,
              elasticities: tuple[dict[str, float], dict[str, float]] | None = None,
              combined: bool = True) -> dict[str, Any]:
    """``law`` maps scenario -> current_law.loader.current_strength(...) (missing -> strength 0);
    ``elasticities`` is (saiz_by_cbsa, saiz_by_county) for the composite geography check."""
    unknown = [s for s in scenarios if s not in KNOWN_SCENARIOS]
    if unknown:
        raise ValueError(f"unknown scenarios {unknown}; known: {KNOWN_SCENARIOS}")
    name = state_name or state.state
    b = baseline(state, params)
    b["narrative"] = baseline_narrative(b, name)
    b["alternative_band"]["narrative"] = alternative_band_narrative(b["alternative_band"], name)
    ctx = scenario_context(state, params, b, elasticities)
    out_sc: dict[str, Any] = {}
    for sc in (s for s in KNOWN_SCENARIOS if s in scenarios and s != "baseline"):
        res = run_scenario(SPECS[sc], state, params, ctx, (law or {}).get(sc, DEFAULT_LAW))
        res["narrative"] = scenario_narrative(res, name)
        out_sc[sc] = res
    combo = None
    if combined and all(sc in out_sc for sc in SPECS):
        combo = combined_package(state, params, ctx, {sc: (law or {}).get(sc, DEFAULT_LAW) for sc in SPECS})
    xc = pep_cross_check(state)
    xc["narrative"] = cross_check_narrative(xc, name)
    return {
        "results_schema_version": RESULTS_SCHEMA_VERSION,
        "meta": {"state": state.state, "state_fips": state.state_fips, **meta},
        "baseline": b,
        "cross_check": {"housing_units_pep": xc},
        "scenarios": out_sc,
        **({"combined": combo} if combo else {}),
        "registers_used": registers_used,
        "no_llm": NO_LLM_STATEMENT,
    }


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _band(where: str, d: Any, p: list[str]) -> None:
    if not isinstance(d, dict) or not all(k in d for k in ("low", "mid", "high")):
        p.append(f"{where}: needs low, mid, high")
        return
    if not all(_finite(d[k]) for k in ("low", "mid", "high")):
        p.append(f"{where}: low/mid/high must be finite numbers")
    elif not d["low"] <= d["mid"] <= d["high"]:
        p.append(f"{where}: low <= mid <= high violated")


def validate_results(r: Any) -> list[str]:
    """Problems with a results dict (empty = matches docs/methods/results_schema.md)."""
    p: list[str] = []
    if not isinstance(r, dict):
        return ["top level is not an object"]
    for k in ("results_schema_version", "meta", "baseline", "scenarios", "registers_used", "no_llm"):
        if k not in r:
            p.append(f"missing {k}")
    if p:
        return p
    if r["results_schema_version"] != RESULTS_SCHEMA_VERSION:
        p.append("results_schema_version mismatch")
    for k in ("state", "build_id", "vintages", "git_sha", "run_date"):
        if k not in r["meta"]:
            p.append(f"meta: missing {k}")
    b = r["baseline"]
    if b.get("outcome") not in OUTCOMES:
        p.append(f"baseline.outcome {b.get('outcome')!r} not in {OUTCOMES}")
    _band("baseline.state", b.get("state"), p)
    for i, c in enumerate(b.get("county", [])):
        _band(f"baseline.county[{i}]", c, p)
    if not b.get("county"):
        p.append("baseline.county is empty")
    years = b.get("state", {}).get("by_year", [])
    if len(years) != b.get("horizon_years"):
        p.append("baseline.state.by_year must have one entry per horizon year")
    for y in years:
        _band(f"baseline.state.by_year[{y.get('year')}]", y, p)
    if not isinstance(b.get("band_rule"), dict) or "reading" not in b["band_rule"]:
        p.append("baseline.band_rule must explain the band")
    elif not b["band_rule"].get("coverage_by_period") or "reading_history" not in b["band_rule"]:
        p.append("baseline.band_rule needs coverage_by_period and reading_history (decision 66)")
    if not b.get("narrative"):
        p.append("baseline.narrative is empty")
    alt = b.get("alternative_band")
    if not isinstance(alt, dict) or "available" not in alt:
        p.append("baseline.alternative_band missing")
    elif alt["available"]:
        _band("baseline.alternative_band", alt, p)
        if alt.get("outcome") not in OUTCOMES:
            p.append("baseline.alternative_band.outcome not in the fixed set")
        if alt.get("applied_to_counties") is not False:
            p.append("baseline.alternative_band is state-level only")
    xc = r.get("cross_check", {}).get("housing_units_pep") if isinstance(r.get("cross_check"), dict) else None
    if not isinstance(xc, dict) or "caveat" not in xc:
        p.append("cross_check.housing_units_pep missing (decision 68)")
    elif xc.get("can_add_to_baseline") or xc.get("outcome") != "stock_change":
        p.append("cross_check.housing_units_pep is a stock_change view, never added to the baseline")
    elif xc.get("available") and not _finite(xc["state"]["net_change"]):
        p.append("cross_check.housing_units_pep.state.net_change must be a finite number")
    if "combined" in r:
        c = r["combined"]
        _band("combined.increment.estimate", c.get("increment", {}).get("estimate"), p)
        for lv in ("low", "mid", "high"):
            if c["increment"]["estimate"][lv] > c["sum_of_parts"][lv] + 1e-6:
                p.append(f"combined {lv} exceeds the sum of the parts")
    for name, s in r["scenarios"].items():
        if name not in KNOWN_SCENARIOS:
            p.append(f"unknown scenario {name}")
            continue
        for k in SCENARIO_KEYS:
            if k not in s:
                p.append(f"scenarios.{name}: missing {k}")
        bench = s.get("benchmark", {})
        if bench.get("outcome") not in OUTCOMES:
            p.append(f"scenarios.{name}.benchmark.outcome not in {OUTCOMES}")
        _band(f"scenarios.{name}.benchmark", bench, p)
        inc = s.get("increment", {})
        if inc.get("outcome") is not None and inc.get("outcome") not in OUTCOMES:
            p.append(f"scenarios.{name}.increment.outcome not in {OUTCOMES}")
        if inc.get("can_add_to_baseline") and inc.get("outcome") != "permits":
            p.append(f"scenarios.{name}: can_add_to_baseline needs outcome 'permits'")
    return p
