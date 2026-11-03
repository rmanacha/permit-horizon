"""FHFA House Price Index, county, annual, all-transactions (developmental).

URL: https://www.fhfa.gov/hpi/download/annual/hpi_at_county.xlsx
Five title rows, then a header: State | County | FIPS code | Year | Annual Change (%) |
HPI | HPI with 1990 base | HPI with 2000 base. Small cells are blank or ".".
The FIPS column is mixed type; it is zero-padded to five characters here.

Required attribution: "This product uses FHFA data but is neither endorsed nor
certified by FHFA." Cite as "Source: FHFA HPI". "FHFA HPI" is a registered
trademark and stays out of the product name.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from hre.data.cache import fetch, raw_dir

FHFA_URL = "https://www.fhfa.gov/hpi/download/annual/hpi_at_county.xlsx"
LICENSE = ("Freely available from FHFA; cite 'Source: FHFA HPI'. This product uses FHFA data but "
           "is neither endorsed nor certified by FHFA.")
VINTAGE = "annual through 2025 (file updated 2026-03-31)"
YEARS = tuple(str(y) for y in range(2015, 2026))


def fhfa_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "fhfa" / "hpi_at_county.xlsx"


def fetch_fhfa(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        FHFA_URL, fhfa_path(data_dir), source="fhfa", license=LICENSE, vintage=VINTAGE, force=force,
        notes="County all-transactions index, developmental, not seasonally adjusted; base 100 at "
              "the county's first recorded year; missing cells dropped.",
    )


def load_fhfa(state_fips: str, data_dir: Path | None = None, years: tuple[str, ...] = YEARS) -> dict[str, dict[str, float]]:
    """county fips -> {year: HPI} for one state, keeping only ``years`` with a numeric value."""
    wb = openpyxl.load_workbook(fhfa_path(data_dir), read_only=True)
    ws = wb[wb.sheetnames[0]]
    out: dict[str, dict[str, float]] = {}
    header: dict[str, int] | None = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            if row and row[0] == "State" and "Year" in row:
                header = {str(h): i for i, h in enumerate(row) if h is not None}
            continue
        if not row or row[header["FIPS code"]] is None:
            continue
        fips = str(row[header["FIPS code"]]).split(".")[0].zfill(5)
        if not fips.startswith(state_fips):
            continue
        year = str(row[header["Year"]]).split(".")[0]
        if year not in years:
            continue
        hpi = row[header["HPI"]]
        if isinstance(hpi, (int, float)):
            out.setdefault(fips, {})[year] = round(float(hpi), 2)
    wb.close()
    return out
