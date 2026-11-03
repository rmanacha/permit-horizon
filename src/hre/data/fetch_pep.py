"""Census Population Estimates Program: annual housing-unit estimates by county, 2020-2025.

URL: https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU.xlsx
Layout: title rows, a header row starting "Geographic Area", a year row
(None, None, 2020, ..., 2025), then ".Belknap County, New Hampshire" rows with
the April 1 2020 base in column B and July 1 estimates in C onward. Names carry a
leading dot; we join to FIPS through the Gazetteer by normalised name.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from hre.data.cache import fetch, raw_dir
from hre.data.fetch_gazetteer import normalize_name

PEP_URL = (
    "https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/"
    "CO-EST2025-HU.xlsx"
)
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"
VINTAGE = "2025 (Vintage 2025 estimates, July 1 2020 to July 1 2025)"


def pep_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "pep" / "CO-EST2025-HU.xlsx"


def fetch_pep(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        PEP_URL, pep_path(data_dir), source="pep", license=LICENSE, vintage=VINTAGE, force=force,
        notes="Housing-unit estimates are built partly from building permits, so they are not "
              "independent of BPS; used as stock denominators and as the reference for the "
              "Address Count Listing File ratio check.",
    )


def read_pep(data_dir: Path | None = None) -> dict[tuple[str, str], dict[str, int]]:
    """(normalised county name, normalised state name) -> {"2020": n, ..., "2025": n}."""
    wb = openpyxl.load_workbook(pep_path(data_dir), read_only=True)
    ws = wb[wb.sheetnames[0]]
    years: list[str] | None = None
    out: dict[tuple[str, str], dict[str, int]] = {}
    for row in ws.iter_rows(values_only=True):
        if not row:
            continue
        if years is None:
            if row[0] is None and any(isinstance(v, int) for v in row):
                years = [str(v) if isinstance(v, int) else "" for v in row]
            continue
        label = row[0]
        if not isinstance(label, str) or not label.startswith("."):
            continue
        name, _, state = label[1:].rpartition(", ")
        if not state:
            continue
        series = {}
        for j, year in enumerate(years):
            if year and isinstance(row[j], (int, float)):
                series[year] = int(row[j])
        out[(normalize_name(name), normalize_name(state))] = series
    wb.close()
    if not out:
        raise ValueError(f"no county rows read from {pep_path(data_dir)}")
    return out


def load_pep(state_name: str, counties: list[dict], data_dir: Path | None = None) -> dict[str, dict[str, int]]:
    """county fips -> {year: housing units}, joined to the Gazetteer county list by name."""
    table = read_pep(data_dir)
    sn = normalize_name(state_name)
    out: dict[str, dict[str, int]] = {}
    for c in counties:
        key = (normalize_name(c["name"]), sn)
        if key in table:
            out[c["fips"]] = table[key]
    return out
