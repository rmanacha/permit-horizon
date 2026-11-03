"""Current-law register schema (decision 38): what each state's law already does.

One YAML file per state, ``src/hre/current_law/{ST}.yaml``; ``_template.yaml``
shows every field. Per scenario (adu, missing_middle, tod, parking, fees):

    record:          {law, summary, quote, url, accessed, in_effect}
    features:        [{id, challenge_requirement, observed_position, status,
                       sources[{title, url, locator, quote, accessed}], limitations[]}]
    current_strength: 0..1, the share of the benchmark reform already in law
    strength_rationale: one or two sentences
    human_review:    {status: pending | reviewed, by, date}

Feature status values (Adam Ruege's v2.0 schema): ``supported_with_limits``,
``differs``, ``not_yet_effective``, ``unknown``.

``strength_from_features`` is the documented starting rule (decision 62): each
benchmark feature counts equally; ``supported_with_limits`` counts 1, every other
status 0. A file may set a different ``current_strength`` only with a rationale
that says why; the engine uses the stored value.
"""

from __future__ import annotations

from typing import Any

SCENARIOS = ("adu", "missing_middle", "tod", "parking", "fees")
FEATURE_STATUSES = ("supported_with_limits", "differs", "not_yet_effective", "unknown")
REVIEW_STATUSES = ("pending", "reviewed")
STATUS_WEIGHT = {"supported_with_limits": 1.0, "differs": 0.0, "not_yet_effective": 0.0, "unknown": 0.0}
DEFAULT_NOTE = "No statewide law found; local permissions unverified."


def strength_from_features(features: list[dict[str, Any]]) -> float:
    if not features:
        return 0.0
    return sum(STATUS_WEIGHT[f["status"]] for f in features) / len(features)


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
        if not isinstance(f.get("limitations", []), list):
            p.append(f"{where}: limitations must be a list")
    cs = s.get("current_strength")
    if not isinstance(cs, (int, float)) or isinstance(cs, bool) or not 0.0 <= cs <= 1.0:
        p.append(f"{name}: current_strength must be a number in [0, 1]")
    if not s.get("strength_rationale"):
        p.append(f"{name}: missing strength_rationale")
    hr = s.get("human_review")
    if not isinstance(hr, dict) or hr.get("status") not in REVIEW_STATUSES:
        p.append(f"{name}: human_review.status must be one of {REVIEW_STATUSES}")
    elif hr["status"] == "reviewed" and not (hr.get("by") and hr.get("date")):
        p.append(f"{name}: a reviewed entry needs human_review.by and .date")
    return p


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
