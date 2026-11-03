"""Baseline: permits over the next five years if current rules continue.

Point, per county and structure type (1, 2, 3-4, 5+ units):
    mean of the latest ``baseline_window_years`` annual BPS totals x ``horizon_years``.
The state total is the sum of the counties. The per-year series is flat (the
point divided by the horizon in each year): this is a no-change continuation,
not a business-cycle forecast.

Band: the point times the 10th and 90th percentile of actual / forecast from the
backtest (``baseline_band_ratio`` low and high, docs/evidence/baseline_backtest.md).
The ratios are estimated on state totals and applied to every county as well; a
county's own error is larger, which the results file says. The band reads "in 80%
of past five-year periods the actual total fell inside this band": a statement
about history, not a probability.

A county-year with no BPS row (no permit-issuing place reported that year) counts
as zero and is listed in ``notes``.

Arrays are shaped [years, counties] so every state runs in milliseconds.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from hre.model.params import Params
from hre.schema import PERMIT_KEYS, StateInputs

TYPE_LABELS = {"u1": "1 unit", "u2": "2 units", "u34": "3-4 units", "u5": "5+ units"}


def permit_years(state: StateInputs) -> list[str]:
    """Every year with at least one county row, sorted."""
    return sorted({y for c in state.counties for y in c.permits})


def permit_cube(state: StateInputs, years: list[str]) -> np.ndarray:
    """Units authorised, shaped [years, counties, 4 structure types]; missing rows are 0."""
    cube = np.zeros((len(years), len(state.counties), len(PERMIT_KEYS)), dtype=float)
    for j, c in enumerate(state.counties):
        for i, y in enumerate(years):
            cell = c.permits.get(y)
            if cell:
                cube[i, j, :] = [cell[k] for k in PERMIT_KEYS]
    return cube


def baseline_point(cube: np.ndarray, window: int, horizon: int) -> np.ndarray:
    """[counties, 4] five-year point: mean of the last ``window`` years x ``horizon``."""
    if cube.shape[0] < window:
        raise ValueError(f"need {window} years of permits, have {cube.shape[0]}")
    return cube[-window:].mean(axis=0) * horizon


def baseline(state: StateInputs, params: Params) -> dict[str, Any]:
    """The baseline block of the results file (outcome: permits)."""
    horizon = int(params["horizon_years"])
    window = int(params["baseline_window_years"])
    lo_ratio = float(params.level_value("baseline_band_ratio", "low"))
    hi_ratio = float(params.level_value("baseline_band_ratio", "high"))

    years = permit_years(state)
    win_years = years[-window:]
    cube = permit_cube(state, years)
    point = baseline_point(cube, window, horizon)            # [counties, 4]
    county_mid = point.sum(axis=1)                           # [counties]
    first = int(years[-1]) + 1
    forecast_years = [first + k for k in range(horizon)]
    annual = np.repeat((county_mid / horizon)[None, :], horizon, axis=0)  # [horizon, counties]

    missing = [f"{c.fips} {c.name}: no BPS row for {', '.join(y for y in win_years if y not in c.permits)}"
               for c in state.counties if any(y not in c.permits for y in win_years)]

    counties = []
    for j, c in enumerate(state.counties):
        counties.append({
            "fips": c.fips,
            "name": c.name,
            "low": float(county_mid[j] * lo_ratio),
            "mid": float(county_mid[j]),
            "high": float(county_mid[j] * hi_ratio),
            "by_type": {k: float(point[j, t]) for t, k in enumerate(PERMIT_KEYS)},
            "recent_annual": {y: float(cube[years.index(y), j].sum()) for y in win_years},
        })
    state_mid = float(county_mid.sum())
    state_annual = annual.sum(axis=1)
    return {
        "outcome": "permits",
        "horizon_years": horizon,
        "window_years": [int(y) for y in win_years],
        "forecast_years": forecast_years,
        "county": counties,
        "state": {
            "low": state_mid * lo_ratio,
            "mid": state_mid,
            "high": state_mid * hi_ratio,
            "by_type": {k: float(point[:, t].sum()) for t, k in enumerate(PERMIT_KEYS)},
            "by_year": [{"year": y, "low": float(v * lo_ratio), "mid": float(v),
                         "high": float(v * hi_ratio)} for y, v in zip(forecast_years, state_annual)],
        },
        "band_rule": {
            "name": "empirical_p10_p90",
            "low_ratio": lo_ratio,
            "high_ratio": hi_ratio,
            "reading": ("In 80% of past five-year periods (50 states and DC, forecast origins "
                        "1990-2015) the actual permit total fell inside this band. It is a "
                        "statement about history, not a probability."),
            "applied_to_counties": ("The ratios come from state totals and are applied to every "
                                    "county; a single county's past errors are larger."),
            "source": "docs/evidence/baseline_backtest.md",
            "alternative": "adam_20yr_min_max (reported in the backtest, not used here)",
        },
        "method": (f"Mean of {win_years[0]}-{win_years[-1]} Census BPS units authorised "
                   f"(estimates with imputation), by county and structure type, x {horizon}."),
        "notes": missing,
    }
