"""Current-law register schema (decision 38): what each state's law already does.

One YAML file per state, ``src/hre/current_law/{ST}.yaml``; ``_template.yaml``
shows every field. Per scenario (adu, missing_middle, tod, parking, fees):

    record:          {law, summary, quote, url, accessed, in_effect}
    features:        [{id, challenge_requirement, observed_position, status,
                       sources[{title, url, locator, quote, accessed}], limitations[],
                       in_effect_from (optional, YYYY-MM-DD)}]
    coverage:        {share, basis, rule (optional)}   optional; 1.0 when absent
    current_strength: 0..1, the share of the benchmark reform already in law
    strength_method: rule (default) | quantified
    strength_arithmetic: required when strength_method is quantified
    strength_rationale: plain sentences shown on the website
    human_review:    {status: pending | reviewed, by, date}
    notes:           optional; kept in the bundle, never shown on the page

Feature status values (Adam Ruege's v2.0 schema): ``supported_with_limits``,
``differs``, ``not_yet_effective``, ``unknown``. A feature enacted with an effective
date inside the 2026-2030 horizon carries its substantive status and ``in_effect_from``;
``not_yet_effective`` is for dates after the horizon or not yet fixed.

The strength rule (docs/methods/current_law.md; decisions 62 and 91):

    strength = gate x feature share x coverage share

* gate: the scenario's core feature (``GATES``) must be ``supported_with_limits``,
  otherwise nothing of the reform is in law and the strength is 0 (an enabling
  statute that lets towns allow ADUs but requires nothing scores 0);
* feature share: each benchmark feature counts equally; ``supported_with_limits``
  counts the share of the horizon it is in force (1 when in force before 2026), every
  other status 0 (``feature_share`` without dates is decision 62's starting rule);
* coverage share: the share of the state's detached single-family homes in the places
  the law binds (``hre.current_law.coverage``), 1 when it binds every jurisdiction.

A scenario whose reform is a quantity (a parking cap against the required spaces the
engine removes) may store a ``quantified`` strength with its arithmetic instead.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

SCENARIOS = ("adu", "missing_middle", "tod", "parking", "fees")
FEATURE_STATUSES = ("supported_with_limits", "differs", "not_yet_effective", "unknown")
REVIEW_STATUSES = ("pending", "reviewed")
STATUS_WEIGHT = {"supported_with_limits": 1.0, "differs": 0.0, "not_yet_effective": 0.0, "unknown": 0.0}
STRENGTH_METHODS = ("rule", "quantified")
DEFAULT_NOTE = "No statewide law found; local permissions unverified."
GATES = {"adu": "adu_per_lot", "missing_middle": "mm_parcels", "tod": "tod_density",
         "parking": "parking_minimum", "fees": "fees_cut"}
HORIZON_START, HORIZON_END = dt.date(2026, 1, 1), dt.date(2031, 1, 1)   # forecast years 2026-2030
RULE_TOLERANCE = 0.005        # stored strengths are rounded to two decimals
# Text the site shows verbatim to legislators must not carry internal references.
INTERNAL = re.compile(r"\bdecision \d|\bdecisions \d|\bphase \d|_[a-z]+_|\b[a-z]+_[a-z_]+\b", re.IGNORECASE)


def horizon_share(in_effect_from: str | None) -> float:
    """Share of the 2026-2030 horizon a feature in force from this date covers."""
    if not in_effect_from:
        return 1.0
    d = dt.date.fromisoformat(str(in_effect_from))
    start = max(d, HORIZON_START)
    if start >= HORIZON_END:
        return 0.0
    return (HORIZON_END - start).days / (HORIZON_END - HORIZON_START).days


def feature_share(features: list[dict[str, Any]]) -> float:
    if not features:
        return 0.0
    return sum(STATUS_WEIGHT[f["status"]] * horizon_share(f.get("in_effect_from"))
               for f in features) / len(features)


def gate_open(scenario: str, features: list[dict[str, Any]]) -> bool:
    gate = next((f for f in features if f.get("id") == GATES[scenario]), None)
    return gate is not None and gate.get("status") == "supported_with_limits"


def strength_by_rule(scenario: str, features: list[dict[str, Any]], coverage: float = 1.0) -> float:
    if not gate_open(scenario, features):
        return 0.0
    return feature_share(features) * coverage


def coverage_value(s: dict[str, Any]) -> float:
    cov = s.get("coverage")
    return float(cov["share"]) if isinstance(cov, dict) and "share" in cov else 1.0


def shown_text(s: dict[str, Any]) -> list[str]:
    """Every string the website shows from one scenario entry (for the plain-language check)."""
    out = [str(s.get("strength_rationale", ""))]
    rec = s.get("record") or {}
    out += [str(rec.get(k, "")) for k in ("law", "summary", "in_effect")]
    for f in s.get("features") or []:
        out += [str(f.get("challenge_requirement", "")), str(f.get("observed_position", ""))]
        out += [str(x) for x in f.get("limitations") or []]
    return out


def validate_scenario(name: str, s: Any) -> list[str]:
    p: list[str] = []
    if not isinstance(s, dict):
        return [f"{name}: not a mapping"]
    rec = s.get("record")
    if not isinstance(rec, dict):
        p.append(f"{name}: missing record")
    else:
        for k in ("law", "summary", "quote", "url", "accessed", "in_effect"):
            if not rec.get(k):
                p.append(f"{name}.record: missing {k}")
        if rec.get("url") and not str(rec["url"]).startswith("https://"):
            p.append(f"{name}.record.url must be https")
    feats = s.get("features")
    if not isinstance(feats, list) or not feats:
        p.append(f"{name}: features must be a non-empty list")
        feats = []
    for i, f in enumerate(feats):
        where = f"{name}.features[{i}]"
        for k in ("id", "challenge_requirement", "observed_position", "status", "sources"):
            if not f.get(k):
                p.append(f"{where}: missing {k}")
        if f.get("status") not in FEATURE_STATUSES:
            p.append(f"{where}: status {f.get('status')!r} not in {FEATURE_STATUSES}")
        for j, src in enumerate(f.get("sources") or []):
            for k in ("title", "url", "locator", "quote", "accessed"):
                if not src.get(k):
                    p.append(f"{where}.sources[{j}]: missing {k}")
            if src.get("url") and not str(src["url"]).startswith("https://"):
                p.append(f"{where}.sources[{j}].url must be https")
        if not isinstance(f.get("limitations", []), list):
            p.append(f"{where}: limitations must be a list")
        if f.get("in_effect_from") is not None:
            try:
                dt.date.fromisoformat(str(f["in_effect_from"]))
            except ValueError:
                p.append(f"{where}: in_effect_from must be YYYY-MM-DD")
    cov = s.get("coverage")
    cov_ok = isinstance(cov, dict) and isinstance(cov.get("share"), (int, float)) \
        and 0.0 <= float(cov["share"]) <= 1.0 and bool(cov.get("basis"))
    if cov is not None and not cov_ok:
        p.append(f"{name}: coverage needs a share in [0, 1] and a basis")
    cs = s.get("current_strength")
    if not isinstance(cs, (int, float)) or isinstance(cs, bool) or not 0.0 <= cs <= 1.0:
        p.append(f"{name}: current_strength must be a number in [0, 1]")
    method = s.get("strength_method", "rule")
    if method not in STRENGTH_METHODS:
        p.append(f"{name}: strength_method must be one of {STRENGTH_METHODS}")
    elif method == "quantified" and not s.get("strength_arithmetic"):
        p.append(f"{name}: a quantified strength needs strength_arithmetic")
    if not s.get("strength_rationale"):
        p.append(f"{name}: missing strength_rationale")
    hr = s.get("human_review")
    if not isinstance(hr, dict) or hr.get("status") not in REVIEW_STATUSES:
        p.append(f"{name}: human_review.status must be one of {REVIEW_STATUSES}")
    elif hr["status"] == "reviewed" and not (hr.get("by") and hr.get("date")):
        p.append(f"{name}: a reviewed entry needs human_review.by and .date")
    return p


def rule_problems(name: str, s: dict[str, Any]) -> list[str]:
    """A rule-method entry whose stored strength differs from the rule (checked in tests)."""
    if s.get("strength_method", "rule") != "rule" or not isinstance(s.get("features"), list):
        return []
    want = strength_by_rule(name, s["features"], coverage_value(s))
    got = float(s.get("current_strength", -1))
    if abs(want - got) > RULE_TOLERANCE:
        return [f"{name}: current_strength {got} but the rule gives {want:.4f}"]
    return []


def validate_state(doc: Any) -> list[str]:
    if not isinstance(doc, dict):
        return ["top level is not a mapping"]
    p = []
    st = doc.get("state")
    if not (isinstance(st, str) and len(st) == 2 and st.isupper()):
        p.append("state must be a 2-letter code")
    scen = doc.get("scenarios")
    if not isinstance(scen, dict):
        return p + ["scenarios must be a mapping"]
    for name, s in scen.items():
        if name not in SCENARIOS:
            p.append(f"unknown scenario {name!r}")
            continue
        p.extend(validate_scenario(name, s))
    return p
