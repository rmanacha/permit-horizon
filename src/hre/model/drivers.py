"""Narrative drivers: fixed templates that turn a factor decomposition into 2-3 sentences.

No language model is used; all text comes from these templates. Each sentence is
filled from numbers the engine already computed, so the words can never say
something the numbers do not.

Rounding for display: below 1,000 to the nearest 10; otherwise to the nearest 100;
halves round away from zero (24,250 shows as 24,300).
"""

from __future__ import annotations

import math
from typing import Any

NO_LLM_STATEMENT = "No language model is used; all text comes from fixed templates in src/hre/model/drivers.py."
TYPE_WORDS = {"u1": "single-family homes", "u2": "two-unit buildings", "u34": "three- and four-unit buildings",
              "u5": "buildings with five or more homes"}


def round_display(x: float) -> str:
    step = 10 if abs(x) < 1000 else 100
    return f"{math.copysign(math.floor(abs(x) / step + 0.5) * step, x):,.0f}"   # halves round up


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


def alternative_band_narrative(alt: dict[str, Any], state_name: str) -> list[str]:
    """Sentences for the separate "another way to draw the range" section (Adam's swing rule)."""
    if not alt.get("available"):
        return [f"The 20-year swing range is not available for {state_name}: {alt['reason']}."]
    p0, p1 = alt["point_years"]
    h0, h1 = alt["history"]
    s0, s1, _ = alt["slowest_window"]
    f0, f1, _ = alt["fastest_window"]
    return [
        (f"Another way to draw the range, from a teammate's earlier prototype: start from "
         f"{state_name}'s {p0}-{p1} permits ({round_display(alt['mid'])}) and stretch them by the "
         f"state's own slowest five years ({s0}-{s1}, {alt['low_ratio']:.2f} times the {h0}-{h1} "
         f"average) and fastest ({f0}-{f1}, {alt['high_ratio']:.2f} times): "
         f"{round_display(alt['low'])} to {round_display(alt['high'])}."),
        alt["how_it_did"],
    ]


def band_period_reading(by_period: list[dict[str, Any]]) -> str:
    """The second band sentence (decision 66), filled from the coverage-by-period table."""
    d = {tuple(c["origins"]): c["share_inside"] for c in by_period}
    calm = [v for k, v in d.items() if k not in ((2005, 2010), (2011, 2015))]
    return (f"Coverage was {d[(2005, 2010)]:.0%} at origins 2005-2010, the bust, and {d[(2011, 2015)]:.0%} at "
            f"2011-2015, the recovery, against {min(calm):.0%} to {max(calm):.0%} in other periods; a band "
            "fitted on history does not foresee a turn in the market.")


def band_realtime_reading(rt: dict[str, Any]) -> str:
    """The real-time test in one sentence, from the register's ``coverage_realtime`` record."""
    a, b = rt["origins"]
    s = f"Refitted each year on closed windows only, the band covered {rt['share_inside']:.0%} of {a}-{b} runs"
    w = rt.get("origins_under_5pct") or []
    return s + (f" and under 5% at origins {w[0]}-{w[-1]}." if w else ".")


def cross_check_narrative(xc: dict[str, Any], state_name: str) -> list[str]:
    """One sentence for the "net change since April 2020" panel, plus the caveat."""
    if not xc.get("available"):
        return [f"Census housing-unit estimates are not available for {state_name} in this input."]
    s = xc["state"]
    return [
        (f"Census housing-unit estimates put {state_name}'s housing stock at {s['end']:,} in July "
         f"{xc['end_year']}, {round_display(s['net_change'])} more than in April 2020 "
         f"({s['change_share']:+.1%})."),
        xc["caveat"],
    ]


OUTCOME_WORDS = {"permits": "permits", "net_permits": "permits net of demolitions",
                 "completed_homes": "completed homes", "stock_change": "homes added to the housing stock",
                 "cost_response_proxy": "additional permits (a cost-response proxy)"}


def _lower_first(s: str) -> str:
    """Lower-case the first letter for mid-sentence use, but keep acronyms (ADU, TOD) as they are."""
    return s[0].lower() + s[1:] if len(s) > 1 and s[1].islower() else s


def scenario_narrative(res: dict[str, Any], state_name: str) -> list[str]:
    """Four template sentences: benchmark, increment, the assumption that moves it most, one limit."""
    b, inc = res["benchmark"], res["increment"]
    e = inc["estimate"]
    share = inc["newly_affected_share"]
    out = [
        (f"{res['label']}: the source policy's activity, transferred to {state_name}, comes to about "
         f"{round_display(b['mid'])} {OUTCOME_WORDS[b['outcome']]} over five years "
         f"({round_display(b['low'])} to {round_display(b['high'])} across the low and high assumption sets)."),
        (f"Over current law the register default counts {share:.0%} of it as newly affected"
         + ("" if share == 1 else f" (current strength {1 - share:.2f})")
         + f", which gives about {round_display(e['mid'])} more permits "
         f"({round_display(e['low'])} to {round_display(e['high'])}), labeled as an assumption set, not a "
         "probability."),
    ]
    if res["tornado"]:
        t = res["tornado"][0]
        out.append(f"The assumption that moves this most is {_lower_first(t['label'])}: from {t['low_text']} to "
                   f"{t['high_text']} the increment runs {round_display(t['at_low'])} to "
                   f"{round_display(t['at_high'])} permits.")
    out.append(res["limits"][0])
    return out
