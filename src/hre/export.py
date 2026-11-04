"""The web bundle: what the front-end reads (Phase 4's only interface; docs/methods/results_schema.md).

    hre export --out web/public/results/

writes, from the results files ``hre run --all`` produced:

    {ST}.json        the results file as written by hre run (baseline, cross_check, five
                     scenarios with components and the parking and fee grids, combined)
    index.json       one row per jurisdiction: baseline and every scenario's mid and range
    registers.json   the assumption register, every current-law file, the validation ledger,
                     and every data source from data/manifests/ (licence, access dates, URLs)
    meta.json        vintages, run date, git sha, schema versions, counts

Every results file is validated first; one that fails stops the export. The bundle is
committed (decision 74); ``tests/test_bundle.py`` fails when it was built from an older register.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from hre.assumptions.loader import PARAMETERS_PATH, load_entries
from hre.current_law.loader import HERE as LAW_DIR
from hre.data.states import lookup
from hre.model.drivers import NO_LLM_STATEMENT
from hre.model.params import LEVELS
from hre.model.run import RESULTS_SCHEMA_VERSION, validate_results
from hre.validation import ledger

MANIFESTS = Path(__file__).resolve().parents[2] / "data" / "manifests"

# Display names for the data sources page (one per manifest in data/manifests/), and which
# key of a results file's meta.vintages carries that source's vintage for the state.
SOURCE_TITLES = {
    "bps": ("Census Building Permits Survey, county and state annual files", "bps"),
    "acs": ("American Community Survey 5-year summary files", "acs"),
    "pep": ("Census Population Estimates, housing units by county", "pep"),
    "nrc": ("Census New Residential Construction, completions per permit", "nrc"),
    "cenpop": ("2020 Census centers of population by block group", "cenpop"),
    "gazetteer": ("Census Gazetteer, counties and places", "gazetteer"),
    "cbsa": ("OMB metropolitan and micropolitan area delineation", "cbsa"),
    "fhfa": ("FHFA House Price Index, county, annual", "fhfa"),
    "transit": ("National Transit Map stops and National Transit Database modes", "transit"),
    "nzlud": ("National Zoning and Land Use Database (NZLUD)", "nzlud"),
    "hcd": ("California HCD Annual Progress Report, Table A2 (ADU rates)", "hcd_adu_tiers"),
    "ct_crosswalk": ("Connecticut towns to 2020 block groups (Census relationship file)", None),
    "gtfs_ct_hartford_line": ("CTrail Hartford Line GTFS feed, stations only", None),
    "gtfs_amtrak": ("Amtrak GTFS feed, Shore Line East stations only", None),
    "aclf": ("Census Address Count Listing Files", "aclf"),
    "ut_hui": ("Utah Housing Unit Inventory (WFRC, MAG, UGRC), single-family parcels per county", None),
    "az_assessors": ("Maricopa and Pinal County assessor parcels, single-family parcels per county", None),
    "nh_granit": ("NH Parcel Mosaic CAMA table (NH DRA via GRANIT), single-family parcels per county", None),
}
ONLY_FOR = {"ct_crosswalk": ["CT"], "gtfs_ct_hartford_line": ["CT"], "gtfs_amtrak": ["CT"],
            "ut_hui": ["UT"], "az_assessors": ["AZ"], "nh_granit": ["NH"]}
NOT_IN_MODEL = {"aclf": ("Downloaded and checked, then excluded: from July 2023 the published "   # decision 46
                         "count reads about double the Census housing-unit estimates.")}


def _sources(manifest_dir: Path = MANIFESTS) -> list[dict[str, Any]]:
    """One row per manifest: what the data sources page shows (no file contents, no data)."""
    rows = []
    for p in sorted(manifest_dir.glob("*.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        files = m.get("files", {}) or {}
        title, vintage_key = SOURCE_TITLES.get(p.stem, (p.stem, None))
        where = []
        for f in files.values():
            url = str(f.get("url", "")).split("?")[0]
            base = url.rsplit("/", 1)[0] + "/" if url.count("/") > 3 else url
            if base and base not in where:
                where.append(base)
        fetched = sorted(str(f["fetched_at"])[:10] for f in files.values() if f.get("fetched_at"))
        rows.append({
            "id": p.stem, "title": title, "license": m.get("license"), "notes": m.get("notes"),
            "files": len(files), "where": where[:4],
            "accessed": [fetched[0], fetched[-1]] if fetched else None,
            "vintages": sorted({str(f["vintage"]) for f in files.values() if f.get("vintage")})[:6],
            "vintage_key": vintage_key, "only_for": ONLY_FOR.get(p.stem),
            "in_model": p.stem not in NOT_IN_MODEL, "why_not": NOT_IN_MODEL.get(p.stem),
            "manifest": f"data/manifests/{p.name}",
        })
    return rows


def _row(r: dict[str, Any]) -> dict[str, Any]:
    st = lookup(r["meta"]["state"])
    row: dict[str, Any] = {
        "state": st.usps, "name": st.name, "fips": st.fips,
        "baseline": {lv: r["baseline"]["state"][lv] for lv in LEVELS},
        "pep_net_change_since_2020": (r["cross_check"]["housing_units_pep"]["state"] or {}).get("net_change"),
        "scenarios": {},
    }
    for name, s in r["scenarios"].items():
        row["scenarios"][name] = {
            "increment": {lv: s["increment"]["estimate"][lv] for lv in LEVELS},
            "status": s["increment"]["status"],
            "newly_affected_share": s["increment"]["newly_affected_share"],
            "benchmark_mid": s["benchmark"]["mid"],
            "benchmark_outcome": s["benchmark"]["outcome"],
        }
    if "combined" in r:
        row["combined"] = {lv: r["combined"]["increment"]["estimate"][lv] for lv in LEVELS}
    return row


def registers() -> dict[str, Any]:
    laws = {}
    for p in sorted(LAW_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        laws[p.stem] = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {
        "assumptions": list(load_entries().values()),
        "current_law": laws,
        "current_law_default": "States and scenarios with no file default to current strength 0: "
                               "\"No statewide law found; local permissions unverified.\"",
        "validation_ledger": ledger.for_export(),
        "sources": _sources(),
    }


def export_bundle(results_dir: Path, out_dir: Path) -> dict[str, Any]:
    files = sorted(p for p in results_dir.glob("*.json") if p.stem.isalpha() and p.stem.isupper())
    real = [p for p in files if not lookup(p.stem).synthetic]
    files = real or files          # the synthetic demo state only when it is all there is (make demo)
    if not files:
        raise FileNotFoundError(f"no results files in {results_dir}; run 'hre run --all' first")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, metas = [], []
    for p in files:
        r = json.loads(p.read_text(encoding="utf-8"))
        problems = validate_results(r)
        if problems:
            raise ValueError(f"{p}: {problems[:5]}")
        (out_dir / p.name).write_text(json.dumps(r, separators=(",", ":"), allow_nan=False), encoding="utf-8")
        rows.append(_row(r))
        metas.append(r["meta"])
    (out_dir / "index.json").write_text(json.dumps({"states": rows}, indent=1), encoding="utf-8")
    (out_dir / "registers.json").write_text(json.dumps(registers(), indent=1, default=str), encoding="utf-8")
    meta = {
        "results_schema_version": RESULTS_SCHEMA_VERSION,
        "jurisdictions": len(rows),
        "export_date": dt.date.today().isoformat(),
        "run_dates": sorted({m["run_date"] for m in metas}),
        "git_shas": sorted({m["git_sha"] for m in metas}),
        "input_schema_versions": sorted({str(m.get("schema_version")) for m in metas}),
        "parameters_sha256": hashlib.sha256(PARAMETERS_PATH.read_bytes()).hexdigest(),
        "vintages": metas[0]["vintages"],
        "no_llm": NO_LLM_STATEMENT,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta
