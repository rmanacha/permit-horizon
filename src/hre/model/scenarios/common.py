"""Shared machinery for the five benchmark scenarios (Phase 3; decisions 30, 31, 32).

Every scenario module supplies a ``Spec``: the register ids it reads, its outcome label,
its ramp, and a ``core`` function that, at whatever levels ``params`` holds, returns

    benchmark_by_year [years, counties]   steady-state source activity in the source's unit
    market [counties]                     the market adjustment (1.0 where none applies)
    conversion                            native unit -> permits (the headline unit)
    homes_per_permit                      completed homes per permit, for the "homes" view

From that one function everything else follows, so the layers can never disagree:

    benchmark  = sum of benchmark_by_year                                  (native unit)
    increment  = sum of benchmark_by_year x market x share x ramp          (native unit)
                 x conversion                                              (permits)
    total      = baseline + increment in permits, low with low, high with high

Low, mid and high are assumption sets (decision 72): the parameters that carry the source
evidence's range (``Spec.band``: the source rate with its paired ramp, or the builder
response) move to the end that lowers (low) or raises (high) the result, using each register
entry's ``direction``; every other parameter stays at mid. The tornado swings every id one at
a time, and the joint cases move all of them at once, so the joint favorable case is the
widest view and the band is the evidence range. Direction-0 entries are swung only when named
in ``Spec.always`` (the price exponent gamma, whose effect changes sign with the county's
value). Nothing here is a probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable  # noqa: UP035 (decision 42: the engine imports typing, not collections)

import numpy as np

from hre.model.cases import increment, named_cases
from hre.model.params import Params
from hre.model.sensitivity import joint_case, tornado
from hre.schema import StateInputs

LEVEL_KEYS = ("low", "mid", "high")


@dataclass
class Core:
    benchmark_by_year: np.ndarray
    market: np.ndarray
    conversion: float
    homes_per_permit: float
    factors: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Spec:
    name: str
    label: str
    outcome: str
    ids: tuple[str, ...]
    band: tuple[str, ...]
    ramp_id: str
    formula: str
    interpretation: str
    conversion_text: str
    limits: tuple[str, ...]
    core: Callable[[StateInputs, Params, dict[str, Any]], Core]
    always: tuple[str, ...] = ()
    linear: tuple[str, ...] = ()
    grid: tuple[str, ...] = ()
    diagnostics: Callable[[StateInputs, Params, dict[str, Any]], dict[str, Any]] | None = None


def level_set(params: Params, ids: tuple[str, ...], level: str) -> Params:
    """Every id at the end that lowers (``low``) or raises (``high``) the result; all at mid for mid."""
    base = params.all_at("mid")
    if level == "mid":
        return base
    want = {}
    for pid in ids:
        d = params.entry(pid).get("direction", 0)
        if d == 0:
            continue
        want[pid] = level if d > 0 else ("high" if level == "low" else "low")
    return base.at(want)


def market_adjustment(values: list[int | None], source_value: float, params: Params) -> np.ndarray:
    """clip((county median value / source city value) ** gamma, bounds); 1.0 where no value."""
    gamma = float(params["value_ratio_exponent"])
    lo = float(params.level_value("market_adjustment_bounds", "low"))
    hi = float(params.level_value("market_adjustment_bounds", "high"))
    v = np.array([source_value if x is None else x for x in values], dtype=float)
    return np.clip((v / source_value) ** gamma, lo, hi)


def flat_years(per_year: np.ndarray, horizon: int) -> np.ndarray:
    """[counties] annual activity -> [horizon, counties]."""
    return np.repeat(np.asarray(per_year, dtype=float)[None, :], horizon, axis=0)


def evaluate(spec: Spec, state: StateInputs, params: Params, ctx: dict[str, Any], share: float) -> dict[str, Any]:
    """The register-default increment at the levels ``params`` holds (also the tornado's run_fn)."""
    c = spec.core(state, params, ctx)
    ramp = params[spec.ramp_id]
    inc = increment(c.benchmark_by_year * c.market[None, :], share, 0, ramp)     # [years, counties]
    native = float(inc.sum())
    return {"core": c, "inc": inc, "native": native, "permits": native * c.conversion,
            "benchmark": float(c.benchmark_by_year.sum())}


def _lv(d: dict[str, Any]) -> dict[str, float]:
    return {k: float(d[k]) for k in LEVEL_KEYS}


def run_scenario(spec: Spec, state: StateInputs, params: Params, ctx: dict[str, Any],
                 law: dict[str, Any]) -> dict[str, Any]:
    """One scenario's block of the results file (docs/methods/results_schema.md)."""
    strength = float(law.get("current_strength", 0.0))
    share = 1.0 - strength
    sets = {lv: level_set(params, spec.band, lv) for lv in LEVEL_KEYS}
    ev = {lv: evaluate(spec, state, sets[lv], ctx, share) for lv in LEVEL_KEYS}
    years = ctx["forecast_years"]
    names = [(c.fips, c.name) for c in state.counties]

    bench_county = [{"fips": f, "name": n, **{lv: float(ev[lv]["core"].benchmark_by_year[:, j].sum())
                                              for lv in LEVEL_KEYS}}
                    for j, (f, n) in enumerate(names)]
    inc_county = [{"fips": f, "name": n, **{lv: float(ev[lv]["inc"][:, j].sum() * ev[lv]["core"].conversion)
                                            for lv in LEVEL_KEYS}}
                  for j, (f, n) in enumerate(names)]
    native = {lv: ev[lv]["native"] for lv in LEVEL_KEYS}
    permits = {lv: ev[lv]["permits"] for lv in LEVEL_KEYS}
    conv = {lv: ev[lv]["core"].conversion for lv in LEVEL_KEYS}
    homes = {lv: permits[lv] * ev[lv]["core"].homes_per_permit for lv in LEVEL_KEYS}

    cases = named_cases({lv: ev[lv]["core"].benchmark_by_year * ev[lv]["core"].market[None, :]
                         for lv in LEVEL_KEYS}, params, strength, law.get("note", ""), spec.outcome,
                        spec.ramp_id)
    for cs in cases.values():
        cs["estimate_permits"] = {lv: cs["estimate"][lv] * conv[lv] for lv in LEVEL_KEYS}
        cs["can_add_to_baseline"] = True       # after conversion to permits

    run_fn = lambda p: evaluate(spec, state, p, ctx, share)["permits"]
    bars = tornado(params, run_fn, list(spec.ids) + list(spec.always), always=spec.always)
    base = ctx["baseline_state"]
    mid = ev["mid"]
    return {
        "label": spec.label,
        "formula": spec.formula,
        "benchmark": {**_lv({lv: ev[lv]["benchmark"] for lv in LEVEL_KEYS}), "outcome": spec.outcome,
                      "interpretation": spec.interpretation, "by_county": bench_county,
                      "by_year": {lv: [float(x) for x in ev[lv]["core"].benchmark_by_year.sum(axis=1)]
                                  for lv in LEVEL_KEYS}},
        "increment": {
            "status": "register_default",
            "estimate": _lv(permits),
            "outcome": "permits",
            "can_add_to_baseline": True,
            "native": {**_lv(native), "outcome": spec.outcome},
            "conversion": {"factor": _lv(conv), "text": spec.conversion_text},
            "completed_homes_equivalent": _lv(homes),
            "newly_affected_share": share,
            "current_law": {k: law.get(k) for k in ("current_strength", "source", "note", "human_review", "file")},
            "ramp": {"id": spec.ramp_id, "years": {lv: list(sets[lv][spec.ramp_id]) for lv in LEVEL_KEYS}},
            "by_year": {lv: [float(x) * conv[lv] for x in ev[lv]["inc"].sum(axis=1)] for lv in LEVEL_KEYS},
            "by_county": inc_county,
            "years": years,
            "assumptions": cases["register_default"]["assumptions"],
        },
        "total": {"estimate": {lv: base[lv] + permits[lv] for lv in LEVEL_KEYS}, "outcome": "permits",
                  "pairing_rule": ("Baseline low plus increment low, mid plus mid, high plus high; no "
                                   "probability is assigned to this range.")},
        "cases": cases,
        "tornado": bars,
        "joint": {d: joint(spec, params, run_fn, bars, d) for d in ("favorable", "unfavorable")},
        "factors": mid["core"].factors,
        "components": components(spec, state, params, mid, share),
        "grid": grid(spec, state, params, ctx, share) if spec.grid else None,
        "diagnostics": spec.diagnostics(state, params, ctx) if spec.diagnostics else {},
        "limits": list(spec.limits),
        "notes": list(mid["core"].factors.get("notes", [])),
        "band_ids": list(spec.band),
        "levels_used": {lv: {pid: sets[lv].level_of(pid) for pid in spec.ids} for lv in LEVEL_KEYS},
    }


def joint(spec: Spec, params: Params, run_fn: Callable[[Params], float], bars: list[dict[str, Any]],
          direction: str) -> dict[str, Any]:
    """Every assumption at its most (least) favorable end at once.

    Starts from the high (low) assumption set, so an id that does not move the result at mid
    (the net-new factor only bites on the gross high rate) still sits at its favorable end, then
    takes each tornado bar's measured end, which also places gamma.
    """
    start = level_set(params, spec.ids, "high" if direction == "favorable" else "low")
    levels = {pid: start.level_of(pid) for pid in spec.ids if params.entry(pid).get("direction", 0) != 0}
    for b in bars:
        fav = b["favorable_end"]
        levels[b["id"]] = fav if direction == "favorable" else ("low" if fav == "high" else "high")
    j = joint_case(params, run_fn, direction, bars=bars)
    value = float(run_fn(params.all_at("mid").at(levels)))
    return {**j, "value": value, "levels": levels,
            "settings": [f"{params.entry(pid)['label']}: {params.display(pid, lv)}" for pid, lv in levels.items()]}


def components(spec: Spec, state: StateInputs, params: Params, mid: dict[str, Any], share: float) -> dict[str, Any]:
    """What the front-end needs to rescale the mid increment exactly when one parameter moves.

    For every id in ``linear`` the increment is proportional to the value, so
    new = old x new_value / old_value. Other ids need a grid cell or a rerun.
    """
    c = mid["core"]
    return {
        "formula": spec.formula,
        "increment_mid_permits": mid["permits"],
        "linear_in": {pid: params[pid] for pid in spec.linear},
        "newly_affected_share": share,
        "ramp_mid": list(params[spec.ramp_id]),
        "conversion_mid": c.conversion,
        "by_county": [{"fips": s.fips, "benchmark_mid": float(c.benchmark_by_year[:, j].sum()),
                       "market": float(c.market[j]),
                       "increment_mid_permits": float(mid["inc"][:, j].sum() * c.conversion)}
                      for j, s in enumerate(state.counties)],
    }


def grid(spec: Spec, state: StateInputs, params: Params, ctx: dict[str, Any], share: float) -> dict[str, Any]:
    """Increment (permits) for every low/mid/high combination of the ``grid`` ids, others at mid."""
    ids = list(spec.grid)
    cells: dict[str, float] = {}

    def rec(i: int, chosen: dict[str, str]) -> None:
        if i == len(ids):
            key = "|".join(f"{k}={v}" for k, v in chosen.items())
            cells[key] = evaluate(spec, state, params.all_at("mid").at(chosen), ctx, share)["permits"]
            return
        for lv in LEVEL_KEYS:
            rec(i + 1, {**chosen, ids[i]: lv})

    rec(0, {})
    return {"params": ids, "levels": list(LEVEL_KEYS), "outcome": "permits", "cells": cells}
