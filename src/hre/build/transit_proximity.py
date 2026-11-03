"""Distance from each block group's center of population to the nearest major transit stop.

Great-circle (haversine) distance on a sphere of radius 3,958.76 statute miles,
vectorised with numpy; the error against an ellipsoid is under 0.3 percent,
far below the block-group positional uncertainty. Block groups are processed in
chunks so a state with 23,000 block groups and 3,000 stops never allocates
more than a few million distances at once.
"""

from __future__ import annotations

import numpy as np

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Element-wise (broadcasting) great-circle distance in statute miles."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(x, dtype=float)) for x in (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def nearest_stop_miles(bg_lat, bg_lon, stop_lat, stop_lon, chunk: int = 2000) -> np.ndarray:
    """For each block group, the distance to the closest stop; NaN for every block group if no stops."""
    bg_lat, bg_lon = np.asarray(bg_lat, dtype=float), np.asarray(bg_lon, dtype=float)
    stop_lat, stop_lon = np.asarray(stop_lat, dtype=float), np.asarray(stop_lon, dtype=float)
    n = bg_lat.shape[0]
    out = np.full(n, np.nan)
    if stop_lat.size == 0 or n == 0:
        return out
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        d = haversine_miles(bg_lat[start:end, None], bg_lon[start:end, None], stop_lat[None, :], stop_lon[None, :])
        out[start:end] = d.min(axis=1)
    return out
