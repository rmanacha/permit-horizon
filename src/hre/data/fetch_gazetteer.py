"""Census Gazetteer county file: the county list, names, land area, internal points.

URL: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_counties_national.zip
Pipe-delimited inside a zip: USPS|GEOID|GEOIDFQ|ANSICODE|NAME|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG
Connecticut appears as its nine planning regions (09110 to 09190).
"""

from __future__ import annotations

import io
import unicodedata
import zipfile
from pathlib import Path

from hre.data.cache import fetch, raw_dir

GAZ_YEAR = "2025"
GAZ_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    f"{GAZ_YEAR}_Gazetteer/{GAZ_YEAR}_Gaz_counties_national.zip"
)
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"


def gazetteer_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "gazetteer" / f"{GAZ_YEAR}_Gaz_counties_national.zip"


def fetch_gazetteer(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        GAZ_URL, gazetteer_path(data_dir), source="gazetteer", license=LICENSE,
        vintage=GAZ_YEAR, force=force,
        notes="County names, land area (sq mi) and internal points; used as the county "
              "index every other source is joined to by FIPS.",
    )


def _read_text(path: Path) -> str:
    """Read the pipe-delimited table from the zip (or a bare .txt for fixtures)."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith(".txt"))
            raw = z.read(name)
    else:
        raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def normalize_name(name: str) -> str:
    """Accent-free, case-folded, single-spaced name for joining across sources."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return " ".join(ascii_only.casefold().split())


def load_counties(state_fips: str, data_dir: Path | None = None) -> list[dict]:
    """Counties of one state: fips, name, land_sqmi, intpt_lat, intpt_lon, sorted by fips."""
    path = gazetteer_path(data_dir)
    if not path.exists() and path.with_suffix(".txt").exists():
        path = path.with_suffix(".txt")
    text = _read_text(path)
    rows: list[dict] = []
    for i, line in enumerate(io.StringIO(text)):
        parts = [p.strip() for p in line.rstrip("\n").split("|")]
        if i == 0:
            header = parts
            idx = {h: j for j, h in enumerate(header)}
            continue
        if len(parts) < len(header):
            continue
        geoid = parts[idx["GEOID"]]
        if not geoid.startswith(state_fips):
            continue
        rows.append(
            {
                "fips": geoid,
                "name": parts[idx["NAME"]],
                "land_sqmi": float(parts[idx["ALAND_SQMI"]]),
                "intpt_lat": float(parts[idx["INTPTLAT"]]),
                "intpt_lon": float(parts[idx["INTPTLONG"]]),
            }
        )
    rows.sort(key=lambda r: r["fips"])
    if not rows:
        raise ValueError(f"no counties with state FIPS {state_fips} in {path}")
    return rows
