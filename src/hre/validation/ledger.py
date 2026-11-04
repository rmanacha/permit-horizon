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


MARKER = "<!-- narrative below is written by hand; hre validate --ledger keeps it -->"


def _fmt(x: Any) -> str:
    if x is None:
        return ""
    return f"{x:,.0f}" if isinstance(x, (int, float)) and abs(x) >= 10 else f"{x:g}"


def summary_table(doc: dict[str, Any]) -> list[str]:
    """The ledger as one table and a totals line (validation.md and the Model and Assumptions Overview)."""
    rows = doc.get("entries") or []
    out = [
        "| Check | Evidence class | Place and years | Outcome | Model low / mid / high | Actual | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in rows:
        p = e.get("prediction") or {}
        pred = (f"{_fmt(p.get('low'))} / {_fmt(p.get('mid'))} / {_fmt(p.get('high'))}" if p.get("mid") is not None
                else (f"{_fmt(p.get('low'))} to {_fmt(p.get('high'))}" if p else "none"))
        actual = e.get("actual_text") or _fmt(e.get("actual")) or "not yet"
        out.append(f"| {e['title']} | {EVIDENCE_CLASSES[e['evidence_class']]} | {e['place']}, {e['years']} | "
                   f"{e['outcome']} ({e['unit']}) | {pred} | {actual} | {e['result'].replace('_', ' ')} |")
    counts = {k: sum(1 for e in rows if e["result"] == k) for k in RESULTS}
    out += ["", (f"Totals: {counts['hit']} hit, {counts['miss']} miss, {counts['pending']} pending, "
            f"{counts['not_a_test']} not a test.")]
    return out


def render_markdown(doc: dict[str, Any], today: str, keep: str = "") -> str:
    """docs/evidence/validation.md: the ledger as tables, then the hand-written narrative kept as is."""
    rows = doc.get("entries") or []
    out = [
        "# Validation: every check of the model, hits and misses",
        "",
        (f"Generated {today} by `uv run hre validate --ledger` from `validation/ledger.yaml` (the same entries the "
        "website's Validation page shows). Frozen checks keep their protocol and hash in `validation/<check>/`; "
        "`tests/test_ledger.py` recomputes every hit and miss and re-hashes every protocol."),
        "",
        *summary_table(doc),
        "", "## What each check shows and does not", "",
    ]
    for e in rows:
        fz = e.get("frozen") or {}
        out += [f"### {e['title']}", "", e["result_text"], "",
                f"- Independence: {e['independence']}", f"- Supports: {e['supports']}",
                f"- Does not support: {e['does_not_support']}", f"- Next check: {e['next_check']}",
                f"- Source: [{e['source']['title']}]({e['source']['url']})"]
        if fz:
            out.append(f"- Frozen: `{fz['protocol']}`, SHA-256 `{fz['sha256']}`"
                       + (f", committed in `{str(fz['commit'])[:7]}`" if fz.get("commit") else ""))
        if e.get("credit"):
            out.append(f"- Credit: {e['credit']}")
        out.append("")
    out += [MARKER, keep.strip() if keep.strip() else "## Narrative\n\n(to be written)", ""]
    return "\n".join(out)


def write_markdown(dest: Path, today: str, path: Path = LEDGER_PATH) -> int:
    keep = ""
    if dest.exists() and MARKER in dest.read_text(encoding="utf-8"):
        keep = dest.read_text(encoding="utf-8").split(MARKER, 1)[1]
    doc = load(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_markdown(doc, today, keep), encoding="utf-8")
    return len(doc.get("entries") or [])
