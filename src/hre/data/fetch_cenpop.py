"""Census 2020 centers of population by block group (one CSV per state).

URL: https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/CenPop2020_Mean_BG{SS}.txt
CSV with a byte-order mark: STATEFP,COUNTYFP,TRACTCE,BLKGRPCE,POPULATION,LATITUDE,LONGITUDE
New Hampshire has 997 rows. Chosen over TIGER internal points (decision 36):
plain text, no shapefile library, and "where the people are" is the right
point for a half-mile transit test.
"""

from __future__ import annotations

import csv
from pathlib import Path

from hre.data.cache import fetch, raw_dir

CENPOP_BASE = "https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp"
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"
VINTAGE = "2020 Census"


def cenpop_path(state_fips: str, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "cenpop" / f"CenPop2020_Mean_BG{state_fips}.txt"


def fetch_cenpop(state_fips: str, data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        f"{CENPOP_BASE}/CenPop2020_Mean_BG{state_fips}.txt", cenpop_path(state_fips, data_dir),
        source="cenpop", license=LICENSE, vintage=VINTAGE, force=force,
        notes="Population-weighted mean centre of each 2020 block group; the origin of every "
              "transit-distance measurement.",
    )


def load_cenpop(state_fips: str, data_dir: Path | None = None) -> list[dict]:
    """Rows: geoid (12 digits), county_fips, population, lat, lon; sorted by geoid."""
    path = cenpop_path(state_fips, data_dir)
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            geoid = r["STATEFP"].zfill(2) + r["COUNTYFP"].zfill(3) + r["TRACTCE"].zfill(6) + r["BLKGRPCE"]
            out.append({
                "geoid": geoid,
                "county_fips": geoid[:5],
                "population": int(r["POPULATION"]),
                "lat": float(r["LATITUDE"]),
                "lon": float(r["LONGITUDE"]),
            })
    out.sort(key=lambda x: x["geoid"])
    if not out:
        raise ValueError(f"no block groups read from {path}")
    return out
