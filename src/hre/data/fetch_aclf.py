"""Census Address Count Listing Files: housing units on the master address list, by block.

URL pattern:
https://www2.census.gov/geo/pvs/addcountlisting/{folder}/{FIPS}_{StateNameNoSpaces}_AddressBlockCountList_{mmyyyy}.txt
Pipe-delimited, one row per 2020 block:
STATE|COUNTY|TRACT|BLOCK|BLOCK_GEOID|TOTAL HOUSING UNITS|TOTAL GROUP QUARTERS
(the June 2022 file adds group-quarters detail columns; the 2026 file uses
underscores in the header). Summed to county here.

The trap (decision 28, verified 2026-11-03): from the July 2023 release on, the
published housing-unit column sums to about twice the state's housing stock
(NH 639,087 in June 2022, then 1,295,974 in July 2023 and 1,334,294 in July
2026, against a 2020 Census count of 638,795). This module computes, for every
vintage, the ratio of the published total to the Census Population Estimates
housing-unit figure for the matching date. The build stores the series only when
every vintage from July 2023 on has a ratio of 2.0 +/- 0.05, and then stores
the published value divided by two with a note saying so. Never used in the
headline metric; it is the "homes actually added to the address list" panel.
"""

from __future__ import annotations

from pathlib import Path

from hre.data.cache import fetch, raw_dir
from hre.data.states import StateRef

ACLF_BASE = "https://www2.census.gov/geo/pvs/addcountlisting"
LICENSE = "U.S. Census Bureau, public domain (U.S. government work)"
# (folder, mmyyyy) in release order. Key form used everywhere else: "YYYY-MM".
VINTAGES: tuple[tuple[str, str], ...] = (
    ("2020", "062022"),
    ("2023", "072023"),
    ("2023", "122023"),
    ("2024", "072024"),
    ("2024", "122024"),
    ("2025", "072025"),
    ("2025", "122025"),
    ("2026", "072026"),
)
DOUBLED_FROM = "2023-07"      # first vintage whose published column reads double
RATIO_LOW, RATIO_HIGH = 1.95, 2.05

# The decision (2026-11-03, decision 46): the halved series is stored only when the
# doubling check passed for EVERY state. It did not: 37 of 51 states passed, the July
# 2023 ratio ranged from 1.894 (UT) to 2.013 (WV) and the July 2026 ratio from 1.979
# (SD) to 2.110 (DC), rising over time in fast-growing states and drifting above 2 in
# slow-growing ones. So the series is excluded everywhere. Evidence:
# docs/evidence/aclf_ratio_check_all_states.md. Flip this to True only after rerunning
# `hre validate --aclf --all --fetch` and finding every state within the band.
SERIES_APPROVED = False
EXCLUDED_NOTE = (
    "address_units: Address Count Listing Files excluded (decision 46). The published "
    "TOTAL HOUSING UNITS column reads about double from July 2023 on, but the ratio to "
    "Census Population Estimates was not a constant 2.0 across states (1.894 to 2.110; 37 of "
    "51 states within 2.0 +/- 0.05), so halving it is not a safe correction. See "
    "docs/DATA_PROVENANCE.md and docs/evidence/aclf_ratio_check_all_states.md."
)


def vintage_key(mmyyyy: str) -> str:
    return f"{mmyyyy[2:]}-{mmyyyy[:2]}"


def aclf_filename(state: StateRef, mmyyyy: str) -> str:
    return f"{state.fips}_{state.name_nospace}_AddressBlockCountList_{mmyyyy}.txt"


def aclf_path(state: StateRef, mmyyyy: str, data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "aclf" / aclf_filename(state, mmyyyy)


def aclf_url(state: StateRef, folder: str, mmyyyy: str) -> str:
    return f"{ACLF_BASE}/{folder}/{aclf_filename(state, mmyyyy)}"


def fetch_aclf(
    state: StateRef, data_dir: Path | None = None, vintages: tuple[tuple[str, str], ...] = VINTAGES,
    force: bool = False,
) -> list[Path]:
    notes = ("Block-level housing-unit counts from the Master Address File. From July 2023 on the "
             "published TOTAL HOUSING UNITS column sums to about twice the housing stock; see "
             "docs/DATA_PROVENANCE.md and hre validate --aclf. The July 2023 and 2024 files exclude "
             "transitory units.")
    out = []
    for folder, mm in vintages:
        out.append(fetch(aclf_url(state, folder, mm), aclf_path(state, mm, data_dir), source="aclf",
                         license=LICENSE, vintage=vintage_key(mm), notes=notes, force=force))
    return out


def county_totals(path: Path) -> dict[str, int]:
    """Sum TOTAL HOUSING UNITS to county fips (5 digits) for one file."""
    out: dict[str, int] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        header = [h.strip().upper().replace(" ", "_") for h in f.readline().rstrip("\n").split("|")]
        try:
            si, ci, ui = header.index("STATE"), header.index("COUNTY"), header.index("TOTAL_HOUSING_UNITS")
        except ValueError as e:
            raise ValueError(f"{path}: unexpected header {header}") from e
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) <= ui or not parts[ui].strip():
                continue
            fips = parts[si].strip().zfill(2) + parts[ci].strip().zfill(3)
            out[fips] = out.get(fips, 0) + int(parts[ui])
    return out


def load_aclf(state: StateRef, data_dir: Path | None = None) -> dict[str, dict[str, int]]:
    """vintage key ("2022-06") -> {county fips: published units} for every file present."""
    out: dict[str, dict[str, int]] = {}
    for _, mm in VINTAGES:
        p = aclf_path(state, mm, data_dir)
        if p.exists():
            out[vintage_key(mm)] = county_totals(p)
    return out


# -- the ratio check ---------------------------------------------------------------


def pep_reference(pep_by_year: dict[str, int], vintage: str) -> tuple[float | None, str]:
    """PEP housing units for a vintage date, with the method used.

    July files match the July 1 estimate of the same year. December files sit
    5/12 of the way to the next July 1 estimate (interpolated). Dates after the
    last PEP year extend the last annual change (extrapolated).
    """
    pep_by_year = {y: v for y, v in pep_by_year.items() if y.isdigit()}   # July 1 keys only
    if not pep_by_year:
        return None, "no PEP"
    year, month = int(vintage[:4]), int(vintage[5:7])
    years = sorted(int(y) for y in pep_by_year)
    last = years[-1]

    def pep(y: int) -> float:
        return float(pep_by_year[str(y)])

    def growth() -> float:
        return pep(last) - pep(last - 1) if last - 1 in years else 0.0

    frac = max(0.0, (month - 7) / 12.0)
    if year in years and frac == 0:
        return pep(year), "exact (July 1 estimate)"
    if year in years and year + 1 in years:
        return pep(year) + frac * (pep(year + 1) - pep(year)), "interpolated between July 1 estimates"
    if year in years:
        return pep(year) + frac * growth(), "extrapolated from the last annual change"
    if year > last:
        return pep(last) + ((year - last) + frac) * growth(), "extrapolated from the last annual change"
    return None, "before PEP coverage"


def ratio_table(aclf: dict[str, dict[str, int]], pep_by_year: dict[str, int]) -> list[dict]:
    """One row per vintage: published total, PEP reference, ratio, method."""
    rows = []
    for vintage in sorted(aclf):
        total = sum(aclf[vintage].values())
        ref, method = pep_reference(pep_by_year, vintage)
        rows.append({
            "vintage": vintage,
            "aclf_total": total,
            "pep_reference": round(ref) if ref is not None else None,
            "ratio": round(total / ref, 4) if ref else None,
            "method": method,
        })
    return rows


def doubling_check(rows: list[dict], low: float = RATIO_LOW, high: float = RATIO_HIGH) -> tuple[bool, str]:
    """True when every vintage from DOUBLED_FROM on has ratio within [low, high].

    Also requires at least one such vintage, and that the pre-2023 vintage (if
    present) is close to 1.0, so a state with a genuinely doubled stock cannot
    pass by accident.
    """
    later = [r for r in rows if r["vintage"] >= DOUBLED_FROM]
    earlier = [r for r in rows if r["vintage"] < DOUBLED_FROM]
    if not later:
        return False, "no vintage from July 2023 on"
    bad = [r for r in later if r["ratio"] is None or not (low <= r["ratio"] <= high)]
    if bad:
        return False, "ratio outside 2.0 +/- 0.05 for " + ", ".join(
            f"{r['vintage']} ({r['ratio']})" for r in bad)
    odd = [r for r in earlier if r["ratio"] is None or not (0.9 <= r["ratio"] <= 1.1)]
    if odd:
        return False, "pre-2023 vintage not near 1.0: " + ", ".join(
            f"{r['vintage']} ({r['ratio']})" for r in odd)
    return True, "every vintage from July 2023 on is 2.0 +/- 0.05 of PEP"


def halved_series(aclf: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Divide every county value by two for vintages from DOUBLED_FROM on."""
    out: dict[str, dict[str, int]] = {}
    for vintage, by_fips in aclf.items():
        if vintage >= DOUBLED_FROM:
            out[vintage] = {f: round(v / 2) for f, v in by_fips.items()}
        else:
            out[vintage] = dict(by_fips)
    return out


HALVED_NOTE = (
    "address_units: for vintages from 2023-07 on, the published TOTAL HOUSING UNITS column was "
    "divided by two. Every vintage from July 2023 on summed to 2.0 +/- 0.05 times the Census "
    "Population Estimates housing-unit figure for the same date (hre validate --aclf), while the "
    "June 2022 file matched the 2020 Census. The 2023 and 2024 files exclude transitory units. "
    "Cross-check series only; never part of the headline permit metric."
)
