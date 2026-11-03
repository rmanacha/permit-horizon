"""Load the assumption register and the Saiz elasticity table.

    from hre.assumptions.loader import load_params
    params = load_params()                                  # every id at mid
    params = load_params(overrides={"builder_response_override": 1.0})
    params["horizon_years"]  -> 5

The YAML lives next to this file so an installed package carries it. The loader
checks every entry for the required fields (``check_entry``); a malformed register
fails at load time, not halfway through a run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hre.model.params import LEVELS, Params

HERE = Path(__file__).resolve().parent
PARAMETERS_PATH = HERE / "parameters.yaml"
ELASTICITIES_PATH = HERE / "elasticities.yaml"

REQUIRED = ("id", "label", "description", "unit", "low", "mid", "high", "scope", "scenarios",
            "grade", "confidence", "sources", "citation", "rationale", "transferability", "levels")
GRADES = ("A", "B", "C", "R")
CONFIDENCES = ("high", "moderate", "low", "set_by_rules")
SCOPES = ("global", "state", "county")
SCENARIOS = ("all", "baseline", "adu", "missing_middle", "tod", "parking", "fees")


def check_entry(e: dict[str, Any]) -> list[str]:
    """Problems with one register entry (empty list = fine)."""
    pid = e.get("id", "?")
    p = [f"{pid}: missing {k}" for k in REQUIRED if k not in e]
    if p:
        return p
    if e["grade"] not in GRADES:
        p.append(f"{pid}: grade {e['grade']!r} not in {GRADES}")
    if e["confidence"] not in CONFIDENCES:
        p.append(f"{pid}: confidence {e['confidence']!r} not in {CONFIDENCES}")
    if e["scope"] not in SCOPES:
        p.append(f"{pid}: scope {e['scope']!r} not in {SCOPES}")
    for s in e["scenarios"]:
        if s not in SCENARIOS:
            p.append(f"{pid}: scenario {s!r} not in {SCENARIOS}")
    if not e["sources"]:
        p.append(f"{pid}: no sources")
    for i, s in enumerate(e["sources"]):
        for k in ("title", "url", "locator", "accessed"):
            if not s.get(k):
                p.append(f"{pid}: sources[{i}] missing {k}")
        if s.get("url") and not str(s["url"]).startswith("https://"):
            p.append(f"{pid}: sources[{i}].url must be https")
    if "PLACEHOLDER" in str(e["citation"]):
        p.append(f"{pid}: citation is still a placeholder")
    for lv in LEVELS:
        if lv not in e["levels"]:
            p.append(f"{pid}: levels missing {lv}")
    vals = [e[lv] for lv in LEVELS]
    if all(isinstance(v, (int, float)) for v in vals):
        if not (min(vals[0], vals[2]) <= vals[1] <= max(vals[0], vals[2])):
            p.append(f"{pid}: mid {vals[1]} is not between low and high")
    elif all(isinstance(v, list) for v in vals):
        if len({len(v) for v in vals}) != 1:
            p.append(f"{pid}: low/mid/high lists differ in length")
    else:
        p.append(f"{pid}: low/mid/high must all be numbers or all be lists")
    if e.get("direction", 0) not in (-1, 0, 1):
        p.append(f"{pid}: direction must be -1, 0 or 1")
    if e.get("ported_from") not in (None, "adam-v2.0"):
        p.append(f"{pid}: ported_from must be 'adam-v2.0' when present")
    return p


def load_entries(path: Path = PARAMETERS_PATH) -> dict[str, dict[str, Any]]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    entries: dict[str, dict[str, Any]] = {}
    problems: list[str] = []
    for e in doc["parameters"]:
        problems.extend(check_entry(e))
        if e.get("id") in entries:
            problems.append(f"{e['id']}: duplicate id")
        entries[e["id"]] = e
    if problems:
        raise ValueError("assumption register problems:\n  " + "\n  ".join(problems))
    return entries


def load_params(path: Path = PARAMETERS_PATH, overrides: dict[str, Any] | None = None,
                levels: dict[str, str] | None = None) -> Params:
    """The register as a Params object; ``overrides`` sets user values, ``levels`` moves ids."""
    params = Params(load_entries(path))
    if levels:
        params = params.at(levels)
    if overrides:
        params = params.with_values(overrides)
    return params


def load_elasticities(path: Path = ELASTICITIES_PATH) -> tuple[dict[str, float], dict[str, float]]:
    """(value by 2023 CBSA code, value by county FIPS) from the Saiz table."""
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    by_cbsa: dict[str, float] = {}
    by_county: dict[str, float] = {}
    for m in doc["metros"]:
        for c in m.get("cbsa_2023", []):
            by_cbsa.setdefault(str(c), float(m["elasticity"]))
        for f in m.get("counties", []):
            by_county[str(f)] = float(m["elasticity"])
    return by_cbsa, by_county


def _fmt(v: Any) -> str:
    if isinstance(v, list):
        return "/".join(f"{x:g}" for x in v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def register_markdown(entries: dict[str, dict[str, Any]] | None = None) -> str:
    """The register as a Markdown table (used by docs and `hre export --register-md`)."""
    entries = entries if entries is not None else load_entries()
    lines = [
        "# Assumption register",
        "",
        ("Generated by `hre export --register-md` from `src/hre/assumptions/parameters.yaml`. "
        "Grades: A measured outcome from a comparable reform; B measured, less comparable; "
        "C projection or judgment; R set by the challenge rules or a design choice. "
        "Low, mid and high are assumption sets, not probabilities."),
        "",
        "| Parameter | Low | Mid | High | Unit | Grade | Confidence | Source and locator | Citation (with arithmetic) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in entries.values():
        src = "; ".join(f"[{s['title']}]({s['url']}), {s['locator']}" for s in e["sources"])
        ported = " (ported from Adam Ruege's v2.0)" if e.get("ported_from") else ""
        cite = " ".join(str(e["citation"]).split()).replace("|", "/")
        lines.append(
            f"| **{e['label']}** (`{e['id']}`){ported} | {_fmt(e['low'])} | {_fmt(e['mid'])} | "
            f"{_fmt(e['high'])} | {e['unit']} | {e['grade']} | {e['confidence']} | "
            f"{src.replace('|', '/')} | {cite} |")
    return "\n".join(lines) + "\n"
