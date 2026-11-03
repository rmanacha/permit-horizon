"""The web bundle: what the front-end reads (Phase 4's only interface; docs/methods/results_schema.md).

    hre export --out web/public/results/

writes, from the results files ``hre run --all`` produced:

    {ST}.json        the results file as written by hre run (baseline, cross_check, five
                     scenarios with components and the parking and fee grids, combined)
    index.json       one row per jurisdiction: baseline and every scenario's mid and range
    registers.json   the assumption register, every current-law file, the validation ledger
    meta.json        vintages, run date, git sha, schema versions, counts

Every results file is validated first; one that fails stops the export. The bundle is
git-ignored (results for real states are never committed); CI or ``make export`` rebuilds it.
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
from hre.model.run import RESULTS_SCHEMA_VERSION, validate_results

LEVELS = ("low", "mid", "high")


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
        "validation_ledger": {"status": "placeholder; Phase 5 fills it (decision 37)", "entries": []},
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
        "no_llm": "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py.",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta
