"""California HCD Annual Progress Report, Table A2 (new units by project), for ADU rates.

Dataset: https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
Resource "APR Table A2" (CSV, about 295 MB, refreshed Oct 2026). One row per
project per **report year**: JURIS_NAME, CNTY_NAME, YEAR, APN, STREET_ADDRESS,
JURS_TRACKING_ID, UNIT_CAT (ADU, SFD, MH, 2 to 4, 5+ ...), NO_ENTITLEMENTS,
BP_ISSUE_DT1, NO_BUILDING_PERMITS, CO_ISSUE_DT1, NO_OTHER_FORMS_OF_READINESS
(the data dictionary defines it as "Number of Units Issued Certificates of
Occupancy"), plus income splits and addresses. Only the aggregate columns are
read; addresses never leave the raw cache.

The trap (evidence base, trap 1): a project is reported again in every year it
has activity, and often re-reported with the same stage, so summing a stage
column by report year double-counts 9 to 23 percent of ADU rows.

De-duplication rule (recorded in docs/DATA_PROVENANCE.md):
1. Keep rows with UNIT_CAT == "ADU".
2. Project key = (jurisdiction, APN) when an APN is present; else (jurisdiction,
   tracking id); else (jurisdiction, street address); rows with none of the
   three are kept as unique.
3. Within one report year, rows with the same key are summed (two ADUs on one
   lot are two units).
4. Across years, each key contributes its entitlement units once (the first
   report year with entitlements > 0), its permit units once (the first year
   with permits > 0), and its completion units once (the first year with
   completions > 0). Later repeats are dropped.
Raw (pre-rule) totals are kept beside the de-duplicated ones so the effect is visible.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

from hre.data.cache import fetch, raw_dir

HCD_URL = ("https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/"
           "fe505d9b-8c36-42ba-ba30-08bc4f34e022/download/tablea2.csv")
LICENSE = ("California HCD open data; data.ca.gov lists 'License not specified'; HCD's APR data "
           "page states no restrictions on use. Provenance retained.")
VINTAGE = "resource last modified 2026-10-30"
USECOLS = ["JURIS_NAME", "CNTY_NAME", "YEAR", "APN", "STREET_ADDRESS", "JURS_TRACKING_ID", "UNIT_CAT",
           "NO_ENTITLEMENTS", "NO_BUILDING_PERMITS", "NO_OTHER_FORMS_OF_READINESS"]
_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def hcd_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "hcd" / "tablea2.csv"


def fetch_hcd(data_dir: Path | None = None, force: bool = False) -> Path:
    return fetch(
        HCD_URL, hcd_path(data_dir), source="hcd", license=LICENSE, vintage=VINTAGE, force=force,
        notes="Table A2 by project and report year; ADU rows only are used; projects repeat across "
              "report years and are de-duplicated by (jurisdiction, APN | tracking id | address).",
    )


def _norm(s: object) -> str:
    """Upper-case alphanumerics only; pandas NaN and None become empty."""
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return ""
    return _NON_ALNUM.sub("", str(s).upper())


def project_key(juris: str, apn: object, tracking: object, address: object) -> str | None:
    j = _norm(juris)
    for tag, val in (("P", apn), ("T", tracking), ("A", address)):
        v = _norm(val)
        if v and v not in ("NA", "NAN", "NONE", "NULL", "0"):
            return f"{j}|{tag}:{v}"
    return None


def dedupe_adu(df):
    """Apply the rule above. Returns (deduped_by_juris_year, raw_by_juris_year) DataFrames."""
    import pandas as pd

    adu = df[df["UNIT_CAT"].astype(str).str.strip().str.upper() == "ADU"].copy()
    for col in ("NO_ENTITLEMENTS", "NO_BUILDING_PERMITS", "NO_OTHER_FORMS_OF_READINESS"):
        adu[col] = pd.to_numeric(adu[col], errors="coerce").fillna(0).astype(int).clip(lower=0)
    adu["YEAR"] = pd.to_numeric(adu["YEAR"], errors="coerce").astype("Int64")
    adu = adu.dropna(subset=["YEAR"])
    adu["YEAR"] = adu["YEAR"].astype(int)
    adu["JURIS_NAME"] = adu["JURIS_NAME"].astype(str).str.strip().str.upper()
    adu["CNTY_NAME"] = adu["CNTY_NAME"].astype(str).str.strip()
    adu = adu.rename(columns={"NO_ENTITLEMENTS": "entitled", "NO_BUILDING_PERMITS": "permitted",
                              "NO_OTHER_FORMS_OF_READINESS": "completed"})
    stages = ["entitled", "permitted", "completed"]
    raw = adu.groupby(["JURIS_NAME", "CNTY_NAME", "YEAR"], as_index=False)[stages].sum()

    adu["key"] = [project_key(j, a, t, s) for j, a, t, s in
                  zip(adu["JURIS_NAME"], adu["APN"], adu["JURS_TRACKING_ID"], adu["STREET_ADDRESS"], strict=True)]
    keyed = adu[adu["key"].notna()]
    unkeyed = adu[adu["key"].isna()]
    # Step 3: sum within (key, year). Step 4: first year with activity per stage.
    per_year = keyed.groupby(["key", "JURIS_NAME", "CNTY_NAME", "YEAR"], as_index=False)[stages].sum()
    per_year = per_year.sort_values(["key", "YEAR"])
    group = ["JURIS_NAME", "CNTY_NAME", "YEAR"]
    parts = []
    for stage in stages:
        active = per_year[per_year[stage] > 0]
        first = active.drop_duplicates(subset=["key"], keep="first")
        parts.append(first.groupby(group, as_index=False)[stage].sum())
    parts.append(unkeyed.groupby(group, as_index=False)[stages].sum())
    # Concatenate the per-stage aggregates (never merge: a join on jurisdiction-year would
    # multiply rows) and sum again; absent stage columns are zero.
    out = pd.concat(parts, ignore_index=True)
    for stage in stages:
        out[stage] = out[stage].fillna(0).astype(int) if stage in out else 0
    dedup = out.groupby(group, as_index=False)[stages].sum()
    return dedup, raw


def read_adu_rows(path: Path):
    """Stream the CSV with the standard library and keep only ADU rows and the columns we use.

    The file is about 295 MB with 70 columns; streaming row by row keeps memory
    near the size of the ADU subset (a few hundred thousand short rows).
    """
    import pandas as pd

    csv.field_size_limit(1 << 24)
    kept: dict[str, list] = {c: [] for c in USECOLS}
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("UNIT_CAT") or "").strip().upper() != "ADU":
                continue
            for c in USECOLS:
                v = row.get(c)
                kept[c].append(v if v not in ("", None) else None)
    return pd.DataFrame(kept, columns=USECOLS, dtype=object)


def build_hcd_table(path: Path) -> dict:
    """Clean ADU table: per jurisdiction-year rows plus statewide totals, raw and de-duplicated."""
    df = read_adu_rows(path)
    dedup, raw = dedupe_adu(df)
    stages = ["entitled", "permitted", "completed"]
    rows = [{"jurisdiction": r.JURIS_NAME, "county": r.CNTY_NAME, "year": int(r.YEAR),
             "entitled": int(r.entitled), "permitted": int(r.permitted), "completed": int(r.completed)}
            for r in dedup.itertuples(index=False)]
    by_year = dedup.groupby("YEAR")[stages].sum()
    raw_by_year = raw.groupby("YEAR")[stages].sum()
    statewide = {str(int(y)): {s: int(by_year.loc[y, s]) for s in stages} for y in by_year.index}
    statewide_raw = {str(int(y)): {s: int(raw_by_year.loc[y, s]) for s in stages} for y in raw_by_year.index}
    return {
        "source": "California HCD APR Table A2, ADU rows (UNIT_CAT == 'ADU')",
        "dedup_rule": ("project key = (jurisdiction, APN | tracking id | street address); rows summed "
                       "within a report year; each key counted once per stage at its first active year"),
        "statewide": statewide,
        "statewide_raw": statewide_raw,
        "rows": rows,
    }


def write_hcd_outputs(data_dir: Path | None, out_dir: Path) -> Path:
    table = build_hcd_table(hcd_path(data_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "CA_hcd_adu.json"
    dest.write_text(json.dumps(table, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return dest
