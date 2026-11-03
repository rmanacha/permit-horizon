"""Canonical input schema for Permit Horizon.

One state = one ``StateInputs`` = one file ``data/processed/{ST}.json``. The
pipeline (``hre build``) writes it; the engine (Phase 2) reads it. Plain
dataclasses, no third-party dependency, so both sides share one definition.

Conventions
- Every geographic code (state, county, block group) is a zero-padded string.
  "01" is Alabama; 1 is a bug.
- Year keys inside dictionaries are 4-character strings ("2025"), vintage keys
  are "YYYY-MM" ("2026-07"), so JSON round-trips exactly.
- ``None`` means "not available for this geography"; 0 means "measured zero".
- County arrays are aligned by ``fips``; block groups by ``geoid``.

See ``docs/methods/schema.md`` for what each field means and where it comes from.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from typing import Any

SCHEMA_VERSION = "3"  # 2: + state_permits_history (decision 69); 3: housing_units_pep gains "2020-04"

METRO_ROLES = ("central", "outlying", "none")
CBSA_TYPES = ("metropolitan", "micropolitan")
PERMIT_KEYS = ("u1", "u2", "u34", "u5")
PERMIT_YEARS = tuple(str(y) for y in range(2016, 2026))

# Outcome labels (decision 30). Every number the engine returns carries exactly
# one of these, so a permit is never silently added to a completed home.
OUTCOMES = ("permits", "net_permits", "completed_homes", "stock_change", "cost_response_proxy")


@dataclass
class CountyInputs:
    """Everything the engine needs about one county (or county equivalent)."""

    fips: str
    name: str
    cbsa: str | None = None
    cbsa_title: str | None = None
    cbsa_type: str | None = None
    metro_role: str = "none"
    permits: dict[str, dict[str, int]] = field(default_factory=dict)
    permits_5plus_share_5yr: float | None = None
    housing_units_pep: dict[str, int] = field(default_factory=dict)
    address_units: dict[str, int] = field(default_factory=dict)
    housing_units: int | None = None
    sf_detached: int | None = None
    sf_attached: int | None = None
    units_2_4: int | None = None
    units_5plus: int | None = None
    mobile: int | None = None
    owner_occupied: int | None = None
    renter_occupied: int | None = None
    vacant: int | None = None
    median_value: int | None = None
    median_rent: int | None = None
    hpi: dict[str, float] = field(default_factory=dict)
    land_sqmi: float | None = None
    supply_elasticity: float | None = None
    parcel_sf_count: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class BlockGroupInputs:
    """One Census block group: where its people are centred and what stands there."""

    geoid: str
    county_fips: str
    pop_center_lat: float
    pop_center_lon: float
    population: int
    housing_units: int | None = None
    sf_detached: int | None = None
    units_5plus: int | None = None
    land_sqmi: float | None = None
    dist_major_stop_miles: float | None = None
    near_transit_half_mile: bool | None = None
    near_transit_quarter_mile: bool | None = None


@dataclass
class StateInputs:
    """One state's complete input file."""

    state: str
    state_fips: str
    vintages: dict[str, str] = field(default_factory=dict)
    counties: list[CountyInputs] = field(default_factory=list)
    block_groups: list[BlockGroupInputs] = field(default_factory=list)
    zoning_by_cbsa: dict[str, dict[str, Any]] = field(default_factory=dict)
    state_permits_history: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, compact: bool = True) -> str:
        """Compact, sorted-keys JSON (stable diffs, small files)."""
        d = self.to_dict()
        if compact:
            return json.dumps(d, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return json.dumps(d, sort_keys=True, indent=1, allow_nan=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StateInputs:
        problems = validate(d)
        if problems:
            shown = "\n  ".join(problems[:20])
            more = f"\n  ... and {len(problems) - 20} more" if len(problems) > 20 else ""
            raise ValueError(f"StateInputs failed validation:\n  {shown}{more}")
        counties = [_from_dict(CountyInputs, c) for c in d["counties"]]
        bgs = [_from_dict(BlockGroupInputs, b) for b in d["block_groups"]]
        return cls(
            state=d["state"],
            state_fips=d["state_fips"],
            vintages=dict(d.get("vintages", {})),
            counties=counties,
            block_groups=bgs,
            zoning_by_cbsa=dict(d.get("zoning_by_cbsa", {})),
            state_permits_history=dict(d.get("state_permits_history", {})),
            notes=list(d.get("notes", [])),
            schema_version=str(d.get("schema_version", SCHEMA_VERSION)),
        )

    @classmethod
    def from_json(cls, text: str) -> StateInputs:
        return cls.from_dict(json.loads(text))

    # -- convenience ---------------------------------------------------------

    def county(self, fips: str) -> CountyInputs:
        for c in self.counties:
            if c.fips == fips:
                return c
        raise KeyError(fips)


def _from_dict(cls: type, d: dict[str, Any]) -> Any:
    names = {f.name for f in fields(cls)}
    unknown = set(d) - names
    if unknown:
        raise ValueError(f"{cls.__name__}: unknown fields {sorted(unknown)}")
    return cls(**d)


# -- validation ----------------------------------------------------------------


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_num(x: Any) -> bool:
    return (isinstance(x, (int, float))) and not isinstance(x, bool)


def _opt(check, x: Any) -> bool:
    return x is None or check(x)


def validate(d: dict[str, Any]) -> list[str]:
    """Return a list of problems (empty means valid). Never raises."""
    p: list[str] = []
    if not isinstance(d, dict):
        return ["top level is not an object"]
    for key in ("state", "state_fips", "counties", "block_groups"):
        if key not in d:
            p.append(f"missing top-level key {key!r}")
    if p:
        return p
    state, sfips = d["state"], d["state_fips"]
    if not (isinstance(state, str) and len(state) == 2 and state.isupper()):
        p.append(f"state must be a 2-letter upper-case code, got {state!r}")
    if not (isinstance(sfips, str) and len(sfips) == 2 and sfips.isdigit()):
        p.append(f"state_fips must be a 2-digit string, got {sfips!r}")
    if not isinstance(d.get("vintages", {}), dict):
        p.append("vintages must be an object")
    if not isinstance(d.get("notes", []), list):
        p.append("notes must be a list")
    if not isinstance(d.get("zoning_by_cbsa", {}), dict):
        p.append("zoning_by_cbsa must be an object")
    hist = d.get("state_permits_history", {})
    if not isinstance(hist, dict):
        p.append("state_permits_history must be an object")
    else:
        for year, units in hist.items():
            if not (isinstance(year, str) and len(year) == 4 and year.isdigit()):
                p.append(f"state_permits_history key {year!r} is not 'YYYY'")
            if not (_is_int(units) and units >= 0):
                p.append(f"state_permits_history[{year}] must be a non-negative int")
    if str(d.get("schema_version", SCHEMA_VERSION)) != SCHEMA_VERSION:
        p.append(f"schema_version {d.get('schema_version')!r} != {SCHEMA_VERSION!r}")

    counties = d["counties"]
    if not isinstance(counties, list):
        return p + ["counties must be a list"]
    seen_fips: set[str] = set()
    for i, c in enumerate(counties):
        where = f"counties[{i}]"
        if not isinstance(c, dict):
            p.append(f"{where} is not an object")
            continue
        fips = c.get("fips")
        if not (isinstance(fips, str) and len(fips) == 5 and fips.isdigit()):
            p.append(f"{where}.fips must be a 5-digit string, got {fips!r}")
        else:
            where = f"county {fips}"
            if isinstance(sfips, str) and not fips.startswith(sfips):
                p.append(f"{where}: fips does not start with state_fips {sfips}")
            if fips in seen_fips:
                p.append(f"{where}: duplicate fips")
            seen_fips.add(fips)
        if not isinstance(c.get("name"), str) or not c.get("name"):
            p.append(f"{where}: name must be a non-empty string")
        if c.get("metro_role") not in METRO_ROLES:
            p.append(f"{where}: metro_role must be one of {METRO_ROLES}, got {c.get('metro_role')!r}")
        if c.get("cbsa_type") is not None and c.get("cbsa_type") not in CBSA_TYPES:
            p.append(f"{where}: cbsa_type must be one of {CBSA_TYPES} or null")
        if not _opt(lambda x: isinstance(x, str) and len(x) == 5 and x.isdigit(), c.get("cbsa")):
            p.append(f"{where}: cbsa must be a 5-digit string or null")
        permits = c.get("permits", {})
        if not isinstance(permits, dict):
            p.append(f"{where}: permits must be an object")
        else:
            for year, cell in permits.items():
                if not (isinstance(year, str) and len(year) == 4 and year.isdigit()):
                    p.append(f"{where}: permits year key {year!r} is not 'YYYY'")
                if not isinstance(cell, dict) or set(cell) != set(PERMIT_KEYS):
                    p.append(f"{where}: permits[{year}] must have keys {PERMIT_KEYS}")
                    continue
                for k, v in cell.items():
                    if not (_is_int(v) and v >= 0):
                        p.append(f"{where}: permits[{year}][{k}] must be a non-negative int")
        for dict_field, want_int in (("housing_units_pep", True), ("address_units", True), ("hpi", False)):
            val = c.get(dict_field, {})
            if not isinstance(val, dict):
                p.append(f"{where}: {dict_field} must be an object")
                continue
            for k, v in val.items():
                if not isinstance(k, str):
                    p.append(f"{where}: {dict_field} key {k!r} must be a string")
                if want_int and not (_is_int(v) and v >= 0):
                    p.append(f"{where}: {dict_field}[{k}] must be a non-negative int")
                if not want_int and not _is_num(v):
                    p.append(f"{where}: {dict_field}[{k}] must be a number")
        for int_field in (
            "housing_units", "sf_detached", "sf_attached", "units_2_4", "units_5plus",
            "mobile", "owner_occupied", "renter_occupied", "vacant", "median_value",
            "median_rent", "parcel_sf_count",
        ):
            v = c.get(int_field)
            if not _opt(lambda x: _is_int(x) and x >= 0, v):
                p.append(f"{where}: {int_field} must be a non-negative int or null, got {v!r}")
        for num_field in ("permits_5plus_share_5yr", "land_sqmi", "supply_elasticity"):
            v = c.get(num_field)
            if not _opt(_is_num, v):
                p.append(f"{where}: {num_field} must be a number or null, got {v!r}")
        share = c.get("permits_5plus_share_5yr")
        if share is not None and not (0.0 <= share <= 1.0):
            p.append(f"{where}: permits_5plus_share_5yr must be within [0, 1]")
        if not isinstance(c.get("notes", []), list):
            p.append(f"{where}: notes must be a list")

    bgs = d["block_groups"]
    if not isinstance(bgs, list):
        return p + ["block_groups must be a list"]
    seen_geoid: set[str] = set()
    for i, b in enumerate(bgs):
        where = f"block_groups[{i}]"
        if not isinstance(b, dict):
            p.append(f"{where} is not an object")
            continue
        geoid = b.get("geoid")
        if not (isinstance(geoid, str) and len(geoid) == 12 and geoid.isdigit()):
            p.append(f"{where}.geoid must be a 12-digit string, got {geoid!r}")
        else:
            where = f"block group {geoid}"
            if geoid in seen_geoid:
                p.append(f"{where}: duplicate geoid")
            seen_geoid.add(geoid)
            cf = b.get("county_fips")
            if not (isinstance(cf, str) and geoid.startswith(cf) and len(cf) == 5):
                p.append(f"{where}: county_fips {cf!r} is not the first 5 digits of geoid")
            elif seen_fips and cf not in seen_fips:
                p.append(f"{where}: county_fips {cf} is not in counties[]")
        lat, lon = b.get("pop_center_lat"), b.get("pop_center_lon")
        if not (_is_num(lat) and -90 <= lat <= 90):
            p.append(f"{where}: pop_center_lat out of range: {lat!r}")
        if not (_is_num(lon) and -180 <= lon <= 180):
            p.append(f"{where}: pop_center_lon out of range: {lon!r}")
        if not (_is_int(b.get("population")) and b.get("population") >= 0):
            p.append(f"{where}: population must be a non-negative int")
        for int_field in ("housing_units", "sf_detached", "units_5plus"):
            if not _opt(lambda x: _is_int(x) and x >= 0, b.get(int_field)):
                p.append(f"{where}: {int_field} must be a non-negative int or null")
        for num_field in ("land_sqmi", "dist_major_stop_miles"):
            if not _opt(lambda x: _is_num(x) and x >= 0, b.get(num_field)):
                p.append(f"{where}: {num_field} must be a non-negative number or null")
        half, quarter = b.get("near_transit_half_mile"), b.get("near_transit_quarter_mile")
        for flag_name, flag in (("near_transit_half_mile", half), ("near_transit_quarter_mile", quarter)):
            if not _opt(lambda x: isinstance(x, bool), flag):
                p.append(f"{where}: {flag_name} must be true/false/null")
        if quarter is True and half is False:
            p.append(f"{where}: within a quarter mile but not within half a mile")
        dist = b.get("dist_major_stop_miles")
        if _is_num(dist) and isinstance(half, bool) and half != (dist <= 0.5):
            p.append(f"{where}: near_transit_half_mile disagrees with dist_major_stop_miles")
        if _is_num(dist) and isinstance(quarter, bool) and quarter != (dist <= 0.25):
            p.append(f"{where}: near_transit_quarter_mile disagrees with dist_major_stop_miles")
    return p
