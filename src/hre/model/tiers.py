"""ADU completion rates by home-value tier (decision 33).

California cities were split into five tiers by ACS median home value (Los Angeles
excluded); each tier's rate is its home-weighted ADU completions per detached home
per year, 2023-2025 (HCD APR Table A2). The four cut points and fifteen rates are in
the register (``adu_value_bound_1..4``, ``adu_rate_tier_1..5``), written by
``hre validate --adu-tiers --write-register`` (src/hre/validation/calibrate_adu_tiers.py).

A county gets the rate of its tier: tier 1 is a median value up to bound 1, tier 5
above bound 4. A county with no ACS median value gets tier 3 and a note.

The method follows Adam Ruege's ``download_data.py --california-adu`` as described
in his v2.0 register (inclusive quintiles of city median values, Los Angeles left
out, home-weighted tier rate, low and high from the first- to third-quartile city
spread around the median city); re-derived here because his source has not arrived.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params

N_TIERS = 5
TIER_IDS = tuple(f"adu_rate_tier_{k}" for k in range(1, N_TIERS + 1))


def tier_bounds(params: Params) -> np.ndarray:
    return np.array([params["adu_value_bound_1"], params["adu_value_bound_2"],
                     params["adu_value_bound_3"], params["adu_value_bound_4"]], dtype=float)


def tier_for(values: Any, bounds: Any) -> Any:
    """Tier 1-5 for each value; ``values <= bound_k`` puts a value in tier k or below.

    Missing values (None or NaN) get 0, which callers treat as "no value: use tier 3".
    """
    b = np.asarray(bounds, dtype=float)
    v = np.array([np.nan if x is None else x for x in np.atleast_1d(values)], dtype=float)
    t = np.searchsorted(b, v, side="left") + 1
    t = np.where(np.isnan(v), 0, t)
    return int(t[0]) if np.ndim(values) == 0 else t


def tier_rates(params: Params, level: str | None = None) -> np.ndarray:
    """The five tier rates at the selected level (or a named level)."""
    if level is None:
        return np.array([params[i] for i in TIER_IDS], dtype=float)
    return np.array([params.level_value(i, level) for i in TIER_IDS], dtype=float)


def county_adu_rates(median_values: list[int | None], params: Params,
                     level: str | None = None) -> dict[str, Any]:
    """Per county: tier, annual completions per detached home, and notes."""
    tiers = tier_for(list(median_values), tier_bounds(params))
    used = np.where(tiers == 0, 3, tiers)
    rates = tier_rates(params, level)[used - 1]
    notes = ["no ACS median home value: tier 3 used" if t == 0 else "" for t in tiers]
    return {"tier": used, "rate": rates, "notes": notes, "outcome": "completed_homes"}
