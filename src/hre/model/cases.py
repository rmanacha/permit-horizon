"""Increment over current law: newly affected share x delay x ramp (decisions 30, 31).

    increment_year[k] = share x benchmark_year[k] x ramp_after_delay[k]
    ramp_after_delay[k] = 0 for k < delay, else ramp[k - delay]       (k = 0..horizon-1)

``benchmark_by_year`` is the steady-state source activity in each horizon year
(the benchmark layer divided over the years), as an array [years] or [years, counties].

Named cases (Adam Ruege's v2.0 policy cases, plus our register default):
- ``register_default``: share = 1 - current_strength from current_law/{ST}.yaml
  (0 strength, so share 1, where no statewide law is on file), the scenario's ramp,
  no delay. Status ``register_default``.
- ``no_change``: share 0. ``after_horizon``: the reform starts when the window ends,
  so zero. Status ``assumed_zero``.
- ``eligible_25 / 50 / 100`` with delay 0, 1 or 2 years, source rate right after the
  delay (no ramp). Status ``user_case``. A 1-year delay keeps 4/5 of the benchmark.

Low, mid and high pair like with like: the low benchmark with the low ramp, and so on.
``can_add_to_baseline`` is true only when the outcome is the headline unit (permits).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params

LEVEL_KEYS = ("low", "mid", "high")


def increment(benchmark_by_year: Any, newly_affected_share: float, delay_years: int, ramp: Any) -> np.ndarray:
    """Activity added by the reform in each horizon year (same shape as the benchmark)."""
    b = np.asarray(benchmark_by_year, dtype=float)
    years = b.shape[0]
    r = np.asarray(ramp, dtype=float)
    if r.shape[0] < years:
        raise ValueError(f"ramp has {r.shape[0]} years, horizon needs {years}")
    if not 0.0 <= newly_affected_share <= 1.0:
        raise ValueError("newly_affected_share must be within [0, 1]")
    d = max(0, int(delay_years))
    eff = np.zeros(years)
    if d < years:
        eff[d:] = r[: years - d]
    shape = (years,) + (1,) * (b.ndim - 1)
    return newly_affected_share * b * eff.reshape(shape)


def _case_list(scenario_ramp_id: str) -> list[dict[str, Any]]:
    cases = [
        {"id": "register_default", "label": "Register default: newly affected share from current law",
         "status": "register_default", "share": None, "delay": 0, "ramp": scenario_ramp_id},
        {"id": "no_change", "label": "Hypothetical: no change to current policy",
         "status": "assumed_zero", "share": 0.0, "delay": 0, "ramp": "ramp_immediate"},
        {"id": "after_horizon", "label": "Hypothetical: implementation starts after five years",
         "status": "assumed_zero", "share": 1.0, "delay": None, "ramp": "ramp_immediate"},
    ]
    for pct in (25, 50, 100):
        for d in (0, 1, 2):
            cases.append({"id": f"eligible_{pct}_delay_{d}",
                          "label": f"Hypothetical: {pct}% newly affected, {d}-year delay, then the source rate",
                          "status": "user_case", "share": pct / 100, "delay": d, "ramp": "ramp_immediate"})
    return cases


def _assumptions(case: dict[str, Any], share: float, delay: int, strength_note: str, outcome: str) -> list[str]:
    s = [("Assumptions selected for this calculation; legal rights and the time needed to build still "
          "need local evidence.")]
    if case["status"] == "register_default":
        s.append(f"Newly affected share {share:.0%} = 1 - current strength from the current-law register. "
                 f"{strength_note}")
        s.append("Activity builds up over the years following the scenario's ramp from the register.")
    elif case["id"] == "no_change":
        s.append("This case assumes the reform leaves current rules unchanged.")
    elif case["id"] == "after_horizon":
        s.append("This case assumes the reform starts when the five-year window ends or later.")
    else:
        s.append(f"The user assumes {share:.0%} of the measured homes or lots are newly affected.")
        s.append(f"No activity for {delay} year(s), then a constant rate from the source evidence.")
    s.append("The source rate applies to the selected group without reducing construction elsewhere.")
    s.append(f"Outcome kept in the source's unit ({outcome}); a permit is not assumed to become a home.")
    return s


def named_cases(benchmark_by_year: dict[str, Any], params: Params, current_strength: float,
                strength_note: str, outcome: str, scenario_ramp_id: str = "ramp_immediate") -> dict[str, Any]:
    """Every named case for one scenario: {case_id: {status, estimate{low,mid,high}, ...}}.

    ``benchmark_by_year`` maps low/mid/high to arrays [years] (or [years, counties]).
    """
    horizon = int(params["horizon_years"])
    out: dict[str, Any] = {}
    for case in _case_list(scenario_ramp_id):
        share = (1.0 - float(current_strength)) if case["share"] is None else float(case["share"])
        delay = horizon if case["delay"] is None else int(case["delay"])
        est, by_year = {}, {}
        for lv in LEVEL_KEYS:
            ramp = params.level_value(case["ramp"], lv)
            inc = increment(benchmark_by_year[lv], share, delay, ramp)
            yearly = inc if inc.ndim == 1 else inc.sum(axis=1)
            est[lv] = float(yearly.sum())
            by_year[lv] = [float(x) for x in yearly]
        out[case["id"]] = {
            "label": case["label"],
            "status": case["status"],
            "newly_affected_share": share,
            "delay_years": delay,
            "ramp": case["ramp"],
            "estimate": est,
            "by_year": by_year,
            "assumptions": _assumptions(case, share, delay, strength_note, outcome),
            "outcome": outcome,
            "can_add_to_baseline": outcome == "permits",
        }
    return out
