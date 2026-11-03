"""Census Building Permits Survey (BPS): county and state annual files.

County: https://www2.census.gov/econ/bps/County/co{YYYY}a.txt (1990 to 2025)
State:  https://www2.census.gov/econ/bps/State/st{YYYY}a.txt  (1980 to 2025)
Place:  https://www2.census.gov/econ/bps/Place/{Region} Region/{xx}{YYYY}a.txt (on demand)

Layout (same since 1990): two header rows and a blank row, then CSV rows.
County columns: survey date, state FIPS, county FIPS, region, division, county
name (padded), then for 1-unit, 2-unit, 3-4 unit and 5+ unit buildings a
Bldgs / Units / Value triplet ("estimates with imputation": reported plus an
imputation for places that did not respond), then the same twelve columns
"reported only". We keep the imputed Units columns; the headline metric is
housing units authorised, not buildings or dollars.

Connecticut: legacy counties (09001 to 09015) through 2022, planning regions
(09110 to 09190) from 2023. Years up to 2022 are re-allocated to planning
regions in proportion to each region's share of the 2023 to 2025 total, by
structure type, and flagged in the county notes.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from hre.data.cache import fetch, raw_dir
from hre.schema import PERMIT_KEYS

BPS_BASE = "https://www2.census.gov/econ/bps"
LICENSE = "U.S. Census Bureau, public domain (U.S. government work); no license statement published"
COUNTY_YEARS = tuple(range(2016, 2026))
STATE_YEARS = tuple(range(1980, 2026))  # 1980s needed for the 20-year swing band (decision 69)
VINTAGE = "annual files as posted 2026 (2025 posted 2026-05-14)"

CT_LEGACY = tuple(f"09{c:03d}" for c in (1, 3, 5, 7, 9, 11, 13, 15))
CT_REGIONS = tuple(f"09{c:03d}" for c in range(110, 191, 10))
CT_SHARE_YEARS = ("2023", "2024", "2025")

# Column positions of the imputed Units cells (county file). 0 date, 1 state, 2 county,
# 3 region, 4 division, 5 name, then triplets Bldgs/Units/Value for 1, 2, 3-4, 5+.
_COUNTY_UNITS = {"u1": 7, "u2": 10, "u34": 13, "u5": 16}
# State file: 0 date, 1 state, 2 region, 3 division, 4 name, then the same triplets.
_STATE_UNITS = {"u1": 6, "u2": 9, "u34": 12, "u5": 15}


def bps_dir(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "bps"


def county_file(year: int, data_dir: Path | None = None) -> Path:
    return bps_dir(data_dir) / f"co{year}a.txt"


def state_file(year: int, data_dir: Path | None = None) -> Path:
    return bps_dir(data_dir) / f"st{year}a.txt"


def fetch_bps(
    data_dir: Path | None = None,
    county_years: tuple[int, ...] = COUNTY_YEARS,
    state_years: tuple[int, ...] = STATE_YEARS,
    force: bool = False,
) -> list[Path]:
    notes = (
        "Annual county and state files, 'estimates with imputation' block. Permits are "
        "authorisations, not completions; counties with no permit-issuing place are absent, "
        "not zero; Connecticut switches from counties to planning regions in 2023."
    )
    out = []
    for y in county_years:
        out.append(fetch(f"{BPS_BASE}/County/co{y}a.txt", county_file(y, data_dir), source="bps",
                         license=LICENSE, vintage=VINTAGE, notes=notes, force=force))
    for y in state_years:
        out.append(fetch(f"{BPS_BASE}/State/st{y}a.txt", state_file(y, data_dir), source="bps",
                         license=LICENSE, vintage=VINTAGE, notes=notes, force=force))
    return out


def _rows(text: str) -> list[list[str]]:
    """Skip the two header rows and the blank row; strip padding from every cell."""
    reader = csv.reader(io.StringIO(text))
    rows = [[c.strip() for c in r] for r in reader]
    body = [r for r in rows[2:] if r and any(r)]
    return body


def survey_year(code: str) -> str:
    """Four-digit year from the BPS survey-date cell.

    Three forms occur: ``202599`` (state files from 1999 on), ``2016`` (county
    files), and ``9099`` (state files 1980 to 1998: two-digit year then ``99``).
    Reading the first four characters of the last form gave ``"9099"`` for 1990,
    which Phase 2 caught when the backtest needed 1990 to 1998.
    """
    code = code.strip()
    if len(code) == 4 and code.isdigit() and code.endswith("99") and code[:2] not in ("19", "20"):
        return "19" + code[:2]
    return code[:4]


def _to_int(s: str) -> int:
    return int(s) if s not in ("", ".") else 0


def parse_county_file(path: Path) -> list[dict]:
    """Every county row: year, fips (5 digits), name, and the four Units cells."""
    text = path.read_text(encoding="latin-1")
    out = []
    for r in _rows(text):
        if len(r) < 18 or not r[1].isdigit():
            continue
        year = survey_year(r[0])
        fips = r[1].zfill(2) + r[2].zfill(3)
        out.append({"year": year, "fips": fips, "name": r[5],
                    **{k: _to_int(r[i]) for k, i in _COUNTY_UNITS.items()}})
    return out


def parse_state_file(path: Path) -> list[dict]:
    """Every state row: year, state_fips, and the four Units cells."""
    text = path.read_text(encoding="latin-1")
    out = []
    for r in _rows(text):
        if len(r) < 17 or not r[1].isdigit():
            continue
        out.append({"year": survey_year(r[0]), "state_fips": r[1].zfill(2),
                    **{k: _to_int(r[i]) for k, i in _STATE_UNITS.items()}})
    return out


def load_county_permits(
    state_fips: str, data_dir: Path | None = None, years: tuple[int, ...] = COUNTY_YEARS
) -> tuple[dict[str, dict[str, dict[str, int]]], dict[str, list[str]]]:
    """fips -> {year -> {u1,u2,u34,u5}} for one state, plus notes per fips.

    Years in which a county has no row are absent from its dictionary (BPS lists
    only counties with at least one permit-issuing place that year).
    """
    permits: dict[str, dict[str, dict[str, int]]] = {}
    for y in years:
        p = county_file(y, data_dir)
        if not p.exists():
            continue
        for row in parse_county_file(p):
            if row["fips"].startswith(state_fips):
                permits.setdefault(row["fips"], {})[row["year"]] = {k: row[k] for k in PERMIT_KEYS}
    notes: dict[str, list[str]] = {}
    if state_fips == "09":
        permits, notes = allocate_ct_legacy(permits)
    return permits, notes


def load_state_permits(
    state_fips: str, data_dir: Path | None = None, years: tuple[int, ...] = STATE_YEARS
) -> dict[str, dict[str, int]]:
    """year -> {u1,u2,u34,u5} from the state annual files (backtest series)."""
    out: dict[str, dict[str, int]] = {}
    for y in years:
        p = state_file(y, data_dir)
        if not p.exists():
            continue
        for row in parse_state_file(p):
            if row["state_fips"] == state_fips:
                out[row["year"]] = {k: row[k] for k in PERMIT_KEYS}
    return out


def allocate_ct_legacy(
    permits: dict[str, dict[str, dict[str, int]]],
) -> tuple[dict[str, dict[str, dict[str, int]]], dict[str, list[str]]]:
    """Spread Connecticut's legacy-county years over the nine planning regions.

    For each structure type, a region's share is its 2023-2025 units divided by
    the state's 2023-2025 units; legacy years are the statewide legacy total
    times that share, rounded, with the rounding remainder given to the largest
    region so the state total is preserved exactly.
    """
    regions = [f for f in CT_REGIONS if f in permits]
    legacy_years = sorted({y for f in CT_LEGACY if f in permits for y in permits[f]})
    notes: dict[str, list[str]] = {}
    if not regions or not legacy_years:
        return {f: v for f, v in permits.items() if f not in CT_LEGACY}, notes
    totals = {k: sum(permits[r].get(y, {}).get(k, 0) for r in regions for y in CT_SHARE_YEARS)
              for k in PERMIT_KEYS}
    out = {f: dict(v) for f, v in permits.items() if f not in CT_LEGACY}
    for y in legacy_years:
        state_total = {k: sum(permits.get(f, {}).get(y, {}).get(k, 0) for f in CT_LEGACY) for k in PERMIT_KEYS}
        alloc = {r: {} for r in regions}
        for k in PERMIT_KEYS:
            if totals[k] == 0:
                shares = {r: 1.0 / len(regions) for r in regions}
            else:
                shares = {r: sum(permits[r].get(yy, {}).get(k, 0) for yy in CT_SHARE_YEARS) / totals[k]
                          for r in regions}
            cells = {r: round(state_total[k] * shares[r]) for r in regions}
            remainder = state_total[k] - sum(cells.values())
            if remainder:
                biggest = max(regions, key=lambda r: shares[r])
                cells[biggest] += remainder
            for r in regions:
                alloc[r][k] = cells[r]
        for r in regions:
            out[r][y] = alloc[r]
    msg = (f"Connecticut {legacy_years[0]}-{legacy_years[-1]} permits were reported for legacy "
           f"counties; re-allocated to this planning region in proportion to its 2023-2025 share "
           f"of statewide permits by structure type (BPS switched geographies in 2023).")
    for r in regions:
        notes[r] = [msg]
    return out, notes


def five_plus_share(permits: dict[str, dict[str, int]], last_n: int = 5) -> float | None:
    """Share of permitted units in 5+ unit buildings over the latest ``last_n`` years with data."""
    years = sorted(permits)[-last_n:]
    total = sum(sum(permits[y].values()) for y in years)
    if total == 0:
        return None
    return sum(permits[y]["u5"] for y in years) / total
