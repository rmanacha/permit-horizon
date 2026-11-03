"""Orchestrator: one state's results file in the three-layer schema.

Pure: the caller (``hre run``) reads the processed input with
``StateInputs.from_json``, loads the registers, collects meta (git sha, run date,
digests) and writes the file. Layout and field meanings: docs/methods/results_schema.md.

    {results_schema_version, meta{...}, baseline{...},
     scenarios{<name>{benchmark{low,mid,high,outcome,interpretation},
                      increment{status,estimate,assumptions[],outcome,can_add_to_baseline},
                      total{estimate,pairing_rule}, cases{...}, tornado[],
                      joint{favorable,unfavorable}, narrative[]}},
     registers_used{...}, no_llm}

Phase 2 fills the baseline; ``scenarios`` is empty until Phase 3 adds the formulas.
"""

from __future__ import annotations

import math
from typing import Any

from hre.model.baseline import baseline
from hre.model.drivers import NO_LLM_STATEMENT, alternative_band_narrative, baseline_narrative
from hre.model.params import Params
from hre.schema import OUTCOMES, StateInputs

RESULTS_SCHEMA_VERSION = "1"
KNOWN_SCENARIOS = ("baseline", "adu", "missing_middle", "tod", "parking", "fees")
SCENARIO_KEYS = ("benchmark", "increment", "total", "cases", "tornado", "joint", "narrative")


def run_state(state: StateInputs, params: Params, scenarios: list[str], meta: dict[str, Any],
              registers_used: dict[str, Any], state_name: str | None = None) -> dict[str, Any]:
    unknown = [s for s in scenarios if s not in KNOWN_SCENARIOS]
    if unknown:
        raise ValueError(f"unknown scenarios {unknown}; known: {KNOWN_SCENARIOS}")
    not_yet = [s for s in scenarios if s != "baseline"]
    if not_yet:
        raise NotImplementedError(f"scenario formulas arrive in Phase 3: {not_yet}")
    b = baseline(state, params)
    b["narrative"] = baseline_narrative(b, state_name or state.state)
    b["alternative_band"]["narrative"] = alternative_band_narrative(b["alternative_band"],
                                                                    state_name or state.state)
    return {
        "results_schema_version": RESULTS_SCHEMA_VERSION,
        "meta": {"state": state.state, "state_fips": state.state_fips, **meta},
        "baseline": b,
        "scenarios": {},
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
