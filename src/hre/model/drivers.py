"""Narrative drivers: fixed templates that turn a factor decomposition into 2-3 sentences.

No language model is used; all text comes from these templates. Each sentence is
filled from numbers the engine already computed, so the words can never say
something the numbers do not.

Rounding for display: below 1,000 to the nearest 10; otherwise to the nearest 100.
"""

from __future__ import annotations

from typing import Any

NO_LLM_STATEMENT = "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py."
TYPE_WORDS = {"u1": "single-family homes", "u2": "two-unit buildings", "u34": "three- and four-unit buildings",
              "u5": "buildings with five or more homes"}


def round_display(x: float) -> str:
    step = 10 if abs(x) < 1000 else 100
    return f"{round(x / step) * step:,.0f}"


def baseline_decomposition(b: dict[str, Any]) -> dict[str, Any]:
    """Factor shares behind the baseline: by county and by structure type."""
    total = b["state"]["mid"]
    counties = sorted(b["county"], key=lambda c: -c["mid"])
    top = counties[0] if counties else None
    by_type = b["state"]["by_type"]
    lead_type = max(by_type, key=by_type.get) if by_type else None
    return {
        "total": total,
        "top_county": top["name"] if top else None,
        "top_county_share": (top["mid"] / total) if top and total else 0.0,
        "top3_share": (sum(c["mid"] for c in counties[:3]) / total) if total else 0.0,
        "lead_type": lead_type,
        "lead_type_share": (by_type[lead_type] / total) if lead_type and total else 0.0,
        "five_plus_share": (by_type.get("u5", 0.0) / total) if total else 0.0,
    }


def baseline_narrative(b: dict[str, Any], state_name: str) -> list[str]:
    d = baseline_decomposition(b)
    y0, y1 = b["forecast_years"][0], b["forecast_years"][-1]
    w0, w1 = b["window_years"][0], b["window_years"][-1]
    s = b["state"]
    rule = b["band_rule"]
    out = [
        (f"If current rules continue, {state_name} would permit about {round_display(s['mid'])} homes "
        f"over {y0}-{y1}: the {w0}-{w1} average carried forward {b['horizon_years']} years."),
        (f"In 80% of past five-year periods the actual total fell between {rule['low_ratio']:.2f} and "
        f"{rule['high_ratio']:.2f} times this kind of estimate, which here means "
        f"{round_display(s['low'])} to {round_display(s['high'])}; that is a range from history, "
        f"not a probability."),
    ]
    if d["top_county"]:
        out.append(
            f"{d['top_county']} accounts for {d['top_county_share']:.0%} of the total, and "
            f"{TYPE_WORDS[d['lead_type']]} make up {d['lead_type_share']:.0%} of it.")
    return out
