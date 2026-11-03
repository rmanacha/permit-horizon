"""Sensitivity: one-at-a-time tornado and the joint favorable / unfavorable cases.

``run_fn(params) -> float`` is any engine result (a scenario's five-year increment,
the baseline total). Starting from every parameter at mid:

- ``tornado``: each parameter swung to its low and then its high end, others at mid.
  Bars are ordered by the size of the swing (largest first), ties by parameter id,
  so the order is deterministic. Parameters that do not move the result are dropped.
- ``joint_case``: every parameter at the end that raised (favorable) or lowered
  (unfavorable) the result in its own swing, all at once. With the engine's
  multiplicative formulas the favorable case is at least as large as any single swing.

Low, mid and high are assumption sets, not probabilities; neither the tornado nor
the joint cases assign a likelihood (decision 32).
"""

from __future__ import annotations

from typing import Any, Callable  # noqa: UP035 (decision 42: the engine imports typing, not collections)

from hre.model.params import Params


def swingable(params: Params, ids: list[str] | None = None, always: tuple[str, ...] = ()) -> list[str]:
    """Register ids whose low and high differ and whose direction is not 0.

    ``always`` names direction-0 ids that are still swung (the price exponent gamma, whose
    effect changes sign with the county's home value, so no fixed direction fits it).
    """
    chosen = ids if ids is not None else list(params.entries)
    out = []
    for pid in chosen:
        e = params.entry(pid)
        if (e.get("direction", 0) != 0 or pid in always) and e["low"] != e["high"]:
            out.append(pid)
    return out


def tornado(params: Params, run_fn: Callable[[Params], float], ids: list[str] | None = None,
            tol: float = 1e-9, always: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    base_params = params.all_at("mid")
    base = float(run_fn(base_params))
    bars = []
    for pid in swingable(params, ids, always):
        lo = float(run_fn(base_params.at({pid: "low"})))
        hi = float(run_fn(base_params.at({pid: "high"})))
        if abs(hi - lo) <= tol and abs(lo - base) <= tol:
            continue
        e = params.entry(pid)
        bars.append({
            "id": pid,
            "label": e["label"],
            "base": base,
            "at_low": lo,
            "at_high": hi,
            "swing": abs(hi - lo),
            "low_text": params.display(pid, "low"),
            "high_text": params.display(pid, "high"),
            "favorable_end": "high" if hi >= lo else "low",
        })
    bars.sort(key=lambda b: (-b["swing"], b["id"]))
    return bars


def joint_case(params: Params, run_fn: Callable[[Params], float], direction: str = "favorable",
               ids: list[str] | None = None, always: tuple[str, ...] = (),
               bars: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """``bars`` lets a caller reuse a tornado it already computed."""
    if direction not in ("favorable", "unfavorable"):
        raise ValueError("direction must be 'favorable' or 'unfavorable'")
    bars = bars if bars is not None else tornado(params, run_fn, ids, always=always)
    levels = {}
    for b in bars:
        fav = b["favorable_end"]
        levels[b["id"]] = fav if direction == "favorable" else ("low" if fav == "high" else "high")
    value = float(run_fn(params.all_at("mid").at(levels)))
    return {
        "direction": direction,
        "value": value,
        "levels": levels,
        "settings": [f"{params.entry(pid)['label']}: {params.display(pid, lv)}" for pid, lv in levels.items()],
        "reading": ("Every assumption at its " + ("most" if direction == "favorable" else "least")
                    + " favorable end at once; an illustration of the extreme, not a likely outcome."),
    }
