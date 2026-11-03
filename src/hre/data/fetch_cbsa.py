"""OMB core-based statistical area delineation, July 2023 (county to CBSA, central/outlying).

URL: https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx
Sheet "List 1": two title rows, header on row 3, then one row per county:
CBSA Code | Metropolitan Division Code | CSA Code | CBSA Title | Metropolitan/Micropolitan
Statistical Area | Metropolitan Division Title | CSA Title | County/County Equivalent |
State Name | FIPS State Code | FIPS County Code | Central/Outlying County
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from hre.data.cache import fetch, raw_dir

CBSA_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/"
    "delineation-files/list1_2023.xlsx"
)
LICENSE = "OMB Bulletin 23-01 delineations distributed by the U.S. Census Bureau; public domain"
VINTAGE = "2023-07"


def cbsa_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "cbsa" / "list1_2023.xlsx"


def fetch_cbsa(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        CBSA_URL, cbsa_path(data_dir), source="cbsa", license=LICENSE, vintage=VINTAGE,
        force=force,
        notes="County membership in metropolitan and micropolitan statistical areas, with the "
              "central/outlying flag that defines the missing-middle exposure.",
    )


def load_cbsa(data_dir: Path | None = None) -> dict[str, dict]:
    """county fips -> {cbsa, cbsa_title, cbsa_type, metro_role} for every delineated county."""
    wb = openpyxl.load_workbook(cbsa_path(data_dir), read_only=True)
    ws = wb[wb.sheetnames[0]]
    out: dict[str, dict] = {}
    header: dict[str, int] | None = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            if row and row[0] == "CBSA Code":
                header = {str(h): i for i, h in enumerate(row) if h is not None}
            continue
        if not row or row[0] is None:
            continue
        sf = str(row[header["FIPS State Code"]]).zfill(2)
        cf = str(row[header["FIPS County Code"]]).zfill(3)
        kind = str(row[header["Metropolitan/Micropolitan Statistical Area"]])
        cbsa_type = "metropolitan" if kind.startswith("Metropolitan") else "micropolitan"
        central = str(row[header["Central/Outlying County"]]).strip().lower()
        if cbsa_type == "metropolitan":
            role = "central" if central == "central" else "outlying"
        else:
            role = "none"
        out[sf + cf] = {
            "cbsa": str(row[header["CBSA Code"]]).zfill(5),
            "cbsa_title": str(row[header["CBSA Title"]]),
            "cbsa_type": cbsa_type,
            "metro_role": role,
        }
    wb.close()
    if not out:
        raise ValueError(f"no delineation rows read from {cbsa_path(data_dir)}")
    return out
