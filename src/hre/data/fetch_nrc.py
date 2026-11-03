"""Census New Residential Construction (NRC): annual units authorized and completed.

Files (keyless; the "Annual" sheet of each workbook, thousands of units):
- ``permits_cust.xlsx``: units authorized in permit-issuing places (Building Permits Survey)
- ``comps_permits_cust.xlsx``: units completed in permit-issuing areas (Survey of Construction)
- ``comps_cust.xlsx``: units completed in all areas, including places that need no permit

Layout: title rows, a header row starting "Year", a row naming the columns
(Total, 1 unit, 2 to 4 units, 5 units or more for the United States, then regions),
then one row per year with the year in column A. "(NA)" marks a missing cell.

Why two completion files: our baseline counts permits in permit-issuing places, so the
like-for-like conversion uses completions in the same places. All-area completions add
the homes built where no permit is needed (about 2.5% of the total, nearly all
single-family, per Census's "Data Relationships between Permits, Starts, and
Completions"), which pushes the one-unit ratio above 1. Both are kept so the
difference is visible in docs/evidence/completions_per_permit.md.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import openpyxl

from hre.data.cache import fetch, raw_dir

NRC_BASE = "https://www.census.gov/construction/nrc/xls"
FILES = {
    "permits": "permits_cust.xlsx",
    "completions_permit_areas": "comps_permits_cust.xlsx",
    "completions_all_areas": "comps_cust.xlsx",
}
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"
VINTAGE = "annual series through 2025, as posted 2026"
RELATIONSHIPS_URL = "https://www.census.gov/construction/pdf/nrc_relationships.pdf"
COLUMNS = ("total", "u1", "u24", "u5")   # United States columns B to E


def nrc_path(key: str, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "nrc" / FILES[key]


def fetch_nrc(data_dir: Path | None = None, force: bool = False) -> dict[str, Path]:
    out = {}
    for key, name in FILES.items():
        out[key] = fetch(
            f"{NRC_BASE}/{name}", nrc_path(key, data_dir), source="nrc", license=LICENSE,
            vintage=VINTAGE, force=force,
            notes="Annual sheet, United States columns. Permits cover permit-issuing places; "
                  "completions come from the Survey of Construction, which reclassifies townhouses "
                  f"that permit offices filed as multifamily into one-unit structures ({RELATIONSHIPS_URL}).",
        )
    return out


def _num(x: object) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def read_annual(path: Path) -> dict[int, dict[str, float | None]]:
    """year -> {"total", "u1", "u24", "u5"} in thousands of units (None where "(NA)")."""
    with warnings.catch_warnings():   # the workbooks carry a print header openpyxl cannot parse
        warnings.simplefilter("ignore", UserWarning)
        return _read_annual(path)


def _read_annual(path: Path) -> dict[int, dict[str, float | None]]:
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Annual"]
    out: dict[int, dict[str, float | None]] = {}
    started = False
    for row in ws.iter_rows(values_only=True):
        if not row:
            continue
        if not started:
            started = isinstance(row[0], str) and row[0].strip() == "Year"
            continue
        y = row[0]
        if isinstance(y, str) and y[:4].isdigit():
            y = int(y[:4])
        if not isinstance(y, int):
            continue
        out[y] = {k: _num(row[1 + i]) for i, k in enumerate(COLUMNS)}
    wb.close()
    if not out:
        raise ValueError(f"no annual rows read from {path}")
    return out


def load_nrc(data_dir: Path | None = None) -> dict[str, dict[int, dict[str, float | None]]]:
    return {key: read_annual(nrc_path(key, data_dir)) for key in FILES}
