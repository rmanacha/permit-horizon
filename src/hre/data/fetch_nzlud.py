"""National Zoning and Land Use Database (NZLUD), MIT licence, 2019 survey of zoning codes.

Repository: https://github.com/mtmleczko/nzlud
Files: nzlud_msa.csv (metro level, keyed by 2010 CBSA code) and nzlud_muni.csv
(municipal, GEOID loses leading zeros in the CSV; zero-padded to 7 here).
Values are natural-language extractions from zoning codes (noisy); coverage
follows the 2006 Wharton survey sample, thin outside metros.
"""

from __future__ import annotations

import csv
from pathlib import Path

from hre.data.cache import fetch, raw_dir

NZLUD_BASE = "https://raw.githubusercontent.com/mtmleczko/nzlud/main"
LICENSE = "MIT (https://github.com/mtmleczko/nzlud/blob/main/LICENSE)"
VINTAGE = "2019-2022 survey, repository main branch"
MSA_FIELDS = ("parking_median", "parking_mode", "adu", "min_lot_size", "responses")


def nzlud_dir(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "nzlud"


def fetch_nzlud(data_dir: Path | None = None, force: bool = False) -> list[Path]:
    notes = ("Zoning-code extraction, 2019; MSA file keyed by 2010 CBSA codes, municipal file by "
             "place GEOID (leading zeros restored). No multifamily-share column at MSA level.")
    out = []
    for name in ("nzlud_msa.csv", "nzlud_muni.csv"):
        out.append(fetch(f"{NZLUD_BASE}/{name}", nzlud_dir(data_dir) / name, source="nzlud",
                         license=LICENSE, vintage=VINTAGE, notes=notes, force=force))
    return out


def _num(s: str) -> float | None:
    s = (s or "").strip()
    if s in ("", "NA", "NaN", "."):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return int(v) if v.is_integer() else v


def load_nzlud_msa(data_dir: Path | None = None) -> dict[str, dict]:
    """cbsa (5-digit, 2010 codes) -> {cbsa_name, parking_median, parking_mode, adu, min_lot_size, responses}."""
    path = nzlud_dir(data_dir) / "nzlud_msa.csv"
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            cbsa = (r.get("cbsa10") or "").strip().zfill(5)
            if not cbsa.isdigit():
                continue
            out[cbsa] = {"cbsa_name": r.get("cbsaname10"), **{k: _num(r.get(k, "")) for k in MSA_FIELDS}}
    return out


def load_nzlud_muni(data_dir: Path | None = None) -> dict[str, dict]:
    """place GEOID (7 digits) -> {statename, place, mf_per, parking_median, adu, min_lot_size}."""
    path = nzlud_dir(data_dir) / "nzlud_muni.csv"
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            geoid = (r.get("GEOID") or "").strip().zfill(7)
            out[geoid] = {
                "statename": r.get("statename"), "place": r.get("place"),
                "mf_per": _num(r.get("mf_per", "")), "parking_median": _num(r.get("parking_median", "")),
                "adu": _num(r.get("adu", "")), "min_lot_size": _num(r.get("min_lot_size", "")),
            }
    return out
