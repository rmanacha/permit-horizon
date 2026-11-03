"""Connecticut 2020 block groups to the nine planning regions (Census relationship file).

URL: https://www2.census.gov/geo/docs/maps-data/data/rel2022/acs22_cousub22_blkgrp20_st09.txt
Pipe-delimited with a byte-order mark, one row per piece of a 2020 block group
that falls in a 2022 county subdivision (town):
OID_COUSUB_22|GEOID_COUSUB_22|...|GEOID_BLKGRP_20|...|AREALAND_PART|AREAWATER_PART

Why it is needed: in 2022 Connecticut replaced its eight legacy counties
(09001-09015) with nine planning regions (09110-09190). The 2020 centers of
population still carry the legacy county code, while the Gazetteer and the
ACS 2020-2024 use the planning regions, so without this file every Connecticut
block group failed the county join. A 2022 town GEOID starts with its planning
region's county code; tract and block-group codes did not change, so the new
block-group GEOID is the planning-region county code plus the old tract and
block group. Three of the 2,716 block groups straddle two regions (two are
water-only block groups in Long Island Sound); each goes to the region holding
most of its land area (water area breaks a tie).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from hre.data.cache import fetch, raw_dir

CT_FIPS = "09"
XWALK_URL = "https://www2.census.gov/geo/docs/maps-data/data/rel2022/acs22_cousub22_blkgrp20_st09.txt"
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"
VINTAGE = "2022 county subdivisions to 2020 block groups (ACS 2022 relationship files)"


def crosswalk_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "ct_crosswalk" / "acs22_cousub22_blkgrp20_st09.txt"


def fetch_ct_crosswalk(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        XWALK_URL, crosswalk_path(data_dir), source="ct_crosswalk", license=LICENSE,
        vintage=VINTAGE, force=force,
        notes="Maps each Connecticut 2020 block group (legacy county code) to the planning "
              "region it lies in, so it joins the Gazetteer and the ACS 2020-2024.",
    )


def load_block_group_regions(data_dir: Path | None = None) -> dict[str, str]:
    """2020 block-group GEOID (legacy county) -> planning-region county FIPS (5 digits)."""
    area: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    with open(crosswalk_path(data_dir), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="|"):
            bg, region = r["GEOID_BLKGRP_20"], r["GEOID_COUSUB_22"][:5]
            land, water = area[bg].get(region, (0, 0))
            area[bg][region] = (land + int(r["AREALAND_PART"]), water + int(r["AREAWATER_PART"]))
    if not area:
        raise ValueError(f"no rows read from {crosswalk_path(data_dir)}")
    return {bg: max(parts, key=lambda k: (parts[k], k)) for bg, parts in area.items()}


def remap_block_groups(rows: list[dict], regions: dict[str, str]) -> tuple[list[dict], list[str]]:
    """Rewrite legacy-county block groups to planning-region GEOIDs.

    Returns (rows, unmatched GEOIDs). A row whose GEOID is not in ``regions``
    is returned unchanged, so the build's county join still drops and notes it.
    """
    out, unmatched = [], []
    for r in rows:
        region = regions.get(r["geoid"])
        if region is None:
            unmatched.append(r["geoid"])
            out.append(r)
            continue
        geoid = region + r["geoid"][5:]
        out.append({**r, "geoid": geoid, "county_fips": region})
    out.sort(key=lambda x: x["geoid"])
    return out, unmatched
