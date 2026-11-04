"""The validation ledger: every check of the model, with its evidence class, hit or miss.

``validation/ledger.yaml`` holds one entry per check (decision 37); ``hre export`` copies the
entries into ``registers.json`` ``validation_ledger.entries[]``, which the Validation page shows as
a table. Entry fields (the page reads them by these names):

    id, title, evidence_class, place, years, outcome, unit,
    prediction {low, mid, high}      numbers, or null where the check has no range
    actual                           a number, or null while pending
    actual_text                      optional words for the actual ("at least 516")
    result                           hit | miss | pending | not_a_test
    result_text                      one plain sentence
    frozen {sha256, protocol, commit}   for frozen checks: the protocol's hash, path and the
                                     commit that recorded it before any outcome was fetched
    source {title, url}
    independence, supports, does_not_support, next_check, credit (optional)

A hit is an actual inside [low, high]; the test suite recomputes every hit and miss.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[3]
LEDGER_PATH = REPO / "validation" / "ledger.yaml"
EVIDENCE_CLASSES = {
    "frozen_holdout": "Frozen holdout",
    "external_descriptive_check": "External check, outcome known beforehand",
    "prospective_holdout": "Prospective holdout, outcome not yet published",
    "internal_historical_check": "Historical check",
    "calibration": "Calibration, not a test",
    "calibration_context": "Calibration context",
    "literature_transfer": "Borrowed from studies, no test",
}
RESULTS = ("hit", "miss", "pending", "not_a_test")
REQUIRED = ("id", "title", "evidence_class", "place", "years", "outcome", "unit", "result",
            "result_text", "source", "independence", "supports", "does_not_support", "next_check")


def load(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"status": "no ledger file", "entries": []}
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def problems(doc: dict[str, Any]) -> list[str]:
    out: list[str] = []
    ids = set()
    for i, e in enumerate(doc.get("entries") or []):
        where = e.get("id", f"entries[{i}]")
        out += [f"{where}: missing {k}" for k in REQUIRED if e.get(k) in (None, "")]
        if e.get("id") in ids:
            out.append(f"{where}: duplicate id")
        ids.add(e.get("id"))
        if e.get("evidence_class") not in EVIDENCE_CLASSES:
            out.append(f"{where}: evidence_class {e.get('evidence_class')!r}")
        if e.get("result") not in RESULTS:
            out.append(f"{where}: result {e.get('result')!r}")
        src = e.get("source") or {}
        if not (src.get("title") and src.get("url")):
            out.append(f"{where}: source needs title and url")
        p, a = e.get("prediction"), e.get("actual")
        if e.get("result") in ("hit", "miss"):
            if not (isinstance(p, dict) and all(isinstance(p.get(k), (int, float)) for k in ("low", "high"))
                    and isinstance(a, (int, float))):
                out.append(f"{where}: a hit or miss needs prediction low/high and a numeric actual")
            elif (p["low"] <= a <= p["high"]) != (e["result"] == "hit"):
                out.append(f"{where}: result {e['result']} but actual {a} vs [{p['low']}, {p['high']}]")
        if e.get("evidence_class") in ("frozen_holdout", "prospective_holdout"):
            fz = e.get("frozen") or {}
            if not (fz.get("sha256") and fz.get("protocol")):
                out.append(f"{where}: a frozen check needs frozen.sha256 and frozen.protocol")
    return out


def for_export(path: Path = LEDGER_PATH) -> dict[str, Any]:
    doc = load(path)
    return {"status": doc.get("status", ""), "classes": EVIDENCE_CLASSES, "entries": doc.get("entries") or []}
