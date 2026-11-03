"""ACS 5-year 2020-2024 table-based summary files (keyless bulk download).

URL pattern:
https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-{table}.dat
Pipe-delimited, one file per table, every geography from nation to block group:
GEO_ID|B25024_E001|B25024_M001|B25024_E002|...  (E = estimate, M = margin)

GEO_ID prefixes: 0500000US county, 1500000US block group, 1600000US place.
Files are 16 to 48 MB each; they are streamed line by line and only the rows
for the requested state are kept. Never commit them.

Tables and the fields they feed (see docs/methods/schema.md):
B25001 total units; B25002 occupancy (E003 vacant); B25003 tenure (E002 owner,
E003 renter); B25004 vacancy status; B25024 units in structure (E002 detached,
E003 attached, E004 2 units, E005 3-4, E006-E009 5+, E010 mobile); B25034 year
built; B25064 median gross rent; B25077 median value.
"""

from __future__ import annotations

from pathlib import Path

from hre.data.cache import fetch, raw_dir

ACS_YEAR = "2024"
ACS_BASE = f"https://www2.census.gov/programs-surveys/acs/summary_file/{ACS_YEAR}/table-based-SF"
ACS_TABLES = ("b25001", "b25002", "b25003", "b25004", "b25024", "b25034", "b25064", "b25077")
GEOS_FILE = f"Geos{ACS_YEAR}5YR.txt"
LICENSE = "U.S. Census Bureau, public domain; catalog entry tagged CC0 1.0"
VINTAGE = f"ACS 5-year 2020-{ACS_YEAR} ({ACS_YEAR} release)"

PREFIX_COUNTY = "0500000US"
PREFIX_BLOCK_GROUP = "1500000US"
PREFIX_PLACE = "1600000US"

# Jam values the summary files use for "not available"; anything this negative is null.
_JAM_THRESHOLD = -222222221


def acs_dir(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "acs"


def table_path(table: str, data_dir: Path | None = None) -> Path:
    return acs_dir(data_dir) / f"acsdt5y{ACS_YEAR}-{table}.dat"


def geos_path(data_dir: Path | None = None) -> Path:
    return acs_dir(data_dir) / GEOS_FILE


def fetch_acs(
    data_dir: Path | None = None, tables: tuple[str, ...] = ACS_TABLES, geos: bool = True,
    force: bool = False,
) -> list[Path]:
    notes = ("Table-based 5-year summary files; block-group margins of error are large and are "
             "not stored; tracts and block groups are 2020 vintage; Connecticut in planning regions.")
    out = []
    for t in tables:
        out.append(fetch(f"{ACS_BASE}/data/5YRData/acsdt5y{ACS_YEAR}-{t}.dat", table_path(t, data_dir),
                         source="acs", license=LICENSE, vintage=VINTAGE, notes=notes, force=force))
    if geos:
        out.append(fetch(f"{ACS_BASE}/documentation/{GEOS_FILE}", geos_path(data_dir), source="acs",
                         license=LICENSE, vintage=VINTAGE, notes=notes, force=force))
    return out


def _cell(s: str) -> int | None:
    s = s.strip()
    if s in ("", ".", "null", "NULL"):
        return None
    try:
        v = int(float(s))
    except ValueError:
        return None
    return None if v <= _JAM_THRESHOLD else v


def read_table(table: str, prefixes: tuple[str, ...], data_dir: Path | None = None) -> dict[str, list[int | None]]:
    """GEO_ID -> list of estimates (E001, E002, ...) for rows whose GEO_ID starts with a prefix."""
    path = table_path(table, data_dir)
    out: dict[str, list[int | None]] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("|")
        est_idx = [i for i, h in enumerate(header) if h.endswith(tuple(f"_E{n:03d}" for n in range(1, 60)))]
        for line in f:
            if not line.startswith(prefixes):
                continue
            parts = line.rstrip("\n").split("|")
            out[parts[0]] = [_cell(parts[i]) for i in est_idx]
    return out


def _fields_from_tables(rows: dict[str, dict[str, list[int | None]]]) -> dict[str, int | None]:
    """Map raw estimate lists to schema field names. Missing tables give None."""

    def e(table: str, n: int) -> int | None:
        vals = rows.get(table)
        return vals[n - 1] if vals and len(vals) >= n else None

    def add(*vals: int | None) -> int | None:
        present = [v for v in vals if v is not None]
        return sum(present) if present else None

    return {
        "housing_units": e("b25001", 1),
        "sf_detached": e("b25024", 2),
        "sf_attached": e("b25024", 3),
        "units_2_4": add(e("b25024", 4), e("b25024", 5)),
        "units_5plus": add(e("b25024", 6), e("b25024", 7), e("b25024", 8), e("b25024", 9)),
        "mobile": e("b25024", 10),
        "owner_occupied": e("b25003", 2),
        "renter_occupied": e("b25003", 3),
        "vacant": e("b25002", 3),
        "median_value": e("b25077", 1),
        "median_rent": e("b25064", 1),
    }


def load_geo_fields(
    state_fips: str, prefix: str, data_dir: Path | None = None,
    tables: tuple[str, ...] = ("b25001", "b25002", "b25003", "b25024", "b25064", "b25077"),
) -> dict[str, dict[str, int | None]]:
    """geoid (digits after the prefix) -> schema fields, for one state and one summary level."""
    full_prefix = prefix + state_fips
    per_table = {t: read_table(t, (full_prefix,), data_dir) for t in tables if table_path(t, data_dir).exists()}
    geoids = sorted({g for t in per_table.values() for g in t})
    out: dict[str, dict[str, int | None]] = {}
    for g in geoids:
        rows = {t: per_table[t][g] for t in per_table if g in per_table[t]}
        out[g[len(prefix):]] = _fields_from_tables(rows)
    return out


def load_county_acs(state_fips: str, data_dir: Path | None = None) -> dict[str, dict[str, int | None]]:
    return load_geo_fields(state_fips, PREFIX_COUNTY, data_dir)


def load_block_group_acs(state_fips: str, data_dir: Path | None = None) -> dict[str, dict[str, int | None]]:
    return load_geo_fields(state_fips, PREFIX_BLOCK_GROUP, data_dir, tables=("b25001", "b25024"))


def load_place_acs(state_fips: str, data_dir: Path | None = None) -> dict[str, dict[str, int | None]]:
    return load_geo_fields(state_fips, PREFIX_PLACE, data_dir, tables=("b25001", "b25024", "b25077"))


def load_geo_names(prefix: str, state_fips: str, data_dir: Path | None = None) -> dict[str, str]:
    """geoid -> NAME from the Geos file, for one summary-level prefix and state."""
    path = geos_path(data_dir)
    out: dict[str, str] = {}
    full = prefix + state_fips
    with open(path, encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("|")
        gi, ni = header.index("GEO_ID"), header.index("NAME")
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) > max(gi, ni) and parts[gi].startswith(full):
                out[parts[gi][len(prefix):]] = parts[ni]
    return out
