"""Baseline backtest on the Census BPS state annual files, 1980-2025.

Ported from ``planning/research/scratch/backtest.py`` (the research script behind
``evidence_base.md`` section 7), typed and tested, plus the two band rules:

Rule A, ours (decision 29)
    point = mean of the last 3 years x 5 (the engine's baseline rule);
    ratio = actual five-year total / point for every state and forecast origin;
    band  = point x [P10, P90] of the ratios, estimated on origins 1990-2015 and
    tested on origins 2016-2020 (out of sample).

Rule B, Adam Ruege's (Housing Reform Estimator v2.0, decision 29's alternative)
    point = the last five years' total; band = point x (slowest, fastest) / average,
    where slowest, fastest and average are taken over the rolling five-year totals of
    the prior 20 years. His run: 181 of 255 inside, 37 above, 37 below, worst origin
    2005 with 20 of 51 inside. Adam's ``src/estimator/backtest.py`` has not arrived
    (decision 43's archive), so the rule was re-derived from his payload text and the
    variant that reproduces his counts exactly was kept (docs/evidence/baseline_backtest.md);
    the reproduction credits his design.

Vocabulary. A forecast *origin* T is the last year of data the forecast uses; the
five-year window is T+1..T+5. Adam calls T the "start year"; this module says
origin to avoid confusing it with the first forecast year.

Jurisdictions: the 50 states and DC. Territories (Puerto Rico, Virgin Islands under
code 52 in 2007-2021) are excluded, which is why the method table has 1,122 runs
where the research script had 1,123.
"""

from __future__ import annotations

import math
import re
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from hre.data import fetch_bps
from hre.data.states import ALL_STATES, lookup
from hre.model.drivers import band_period_reading, band_realtime_reading

YEARS = tuple(range(1980, 2026))
HORIZON = 5
WINDOW = 3
EST_ORIGINS = tuple(range(1990, 2016))
TEST_ORIGINS = tuple(range(2016, 2021))
ADAM_ORIGINS = (2000, 2005, 2010, 2015, 2020)
ADAM_HISTORY = 20
PERCENTILES = (10.0, 90.0)
# Origin groups for coverage by period (decision 66): calm 1990s, early 2000s, the bust,
# the recovery, the out-of-sample test window.
PERIODS = ((1990, 1999), (2000, 2004), (2005, 2010), (2011, 2015), (2016, 2020))
PERIOD_LABELS = {(1990, 1999): "1990s", (2000, 2004): "early 2000s", (2005, 2010): "the bust",
                 (2011, 2015): "the recovery", (2016, 2020): "test window, never fitted"}
REALTIME_ORIGINS = tuple(range(2000, 2021))
REALTIME_GROUPS = ((2000, 2004), (2005, 2010), (2011, 2015), (2016, 2020))

Panel = dict[str, dict[int, float]]   # state fips -> year -> total units authorised


# ---------------------------------------------------------------- data


def state_fips_51() -> list[str]:
    return [lookup(s).fips for s in ALL_STATES]


def fetch_series(data_dir: Path | None = None) -> None:
    """Download any missing state annual file 1980-2025 (small; manifests recorded)."""
    fetch_bps.fetch_bps(data_dir, county_years=(), state_years=YEARS)


def load_panel(data_dir: Path | None = None, years: tuple[int, ...] = YEARS,
               states: list[str] | None = None) -> Panel:
    """Total units authorised (1 + 2 + 3-4 + 5+) by state and year, from the cached files."""
    keep = set(states or state_fips_51())
    panel: Panel = {f: {} for f in keep}
    for y in years:
        path = fetch_bps.state_file(y, data_dir)
        if not path.exists():
            continue
        for row in fetch_bps.parse_state_file(path):
            if row["state_fips"] in keep and int(row["year"]) == y:
                panel[row["state_fips"]][y] = float(row["u1"] + row["u2"] + row["u34"] + row["u5"])
    return panel


# ---------------------------------------------------------------- forecasting methods


def _trend(vals: list[float], n: int) -> list[float]:
    k = len(vals)
    xs = list(range(k))
    mx, my = sum(xs) / k, sum(vals) / k
    b = sum((x - mx) * (v - my) for x, v in zip(xs, vals)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    return [max(0.0, a + b * (k - 1 + h)) for h in range(1, n + 1)]


METHODS: dict[str, tuple[str, Callable[[list[float]], list[float]]]] = {
    "last1": ("Last year x 5", lambda v: [v[-1]] * 5),
    "mean3": ("3-yr mean x 5", lambda v: [sum(v[-3:]) / 3] * 5),
    "mean5": ("5-yr mean x 5", lambda v: [sum(v[-5:]) / 5] * 5),
    "mean10": ("10-yr mean x 5", lambda v: [sum(v[-10:]) / 10] * 5),
    "trend10": ("10-yr linear trend", lambda v: _trend(v[-10:], 5)),
}


def method_table(panel: Panel, origins: tuple[int, ...] = tuple(range(1999, 2021)),
                 history: int = 10) -> dict[str, dict[str, float]]:
    """evidence_base.md section 7: each method's error on the five-year total."""
    out: dict[str, dict[str, float]] = {}
    for key, (label, fn) in METHODS.items():
        apes, signed = [], []
        for s in panel.values():
            for t in origins:
                if not all(y in s for y in range(t - history + 1, t + HORIZON + 1)):
                    continue
                hist = [s[y] for y in range(t - history + 1, t + 1)]
                act = sum(s[y] for y in range(t + 1, t + HORIZON + 1))
                if act <= 0 or sum(hist[-5:]) == 0:
                    continue
                fc = sum(fn(hist))
                apes.append(abs(fc - act) / act)
                signed.append((fc - act) / act)
        a = np.array(apes)
        out[key] = {"label": label, "n": len(a), "mdape": float(np.median(a)),
                    "within25": float(np.mean(a <= 0.25)), "within50": float(np.mean(a <= 0.5)),
                    "bias_median": float(np.median(signed))}
    return out


# ---------------------------------------------------------------- rule A (ours)


@dataclass(frozen=True)
class Run:
    state: str
    origin: int
    point: float
    actual: float
    low: float = math.nan
    high: float = math.nan

    @property
    def ratio(self) -> float:
        return self.actual / self.point

    @property
    def ape(self) -> float:
        return abs(self.point - self.actual) / self.actual

    @property
    def position(self) -> str:
        if self.actual < self.low:
            return "below"
        if self.actual > self.high:
            return "above"
        return "inside"


def mean3_runs(panel: Panel, origins: tuple[int, ...]) -> list[Run]:
    """The engine's rule on every state and origin with complete data."""
    runs = []
    for f in sorted(panel):
        s = panel[f]
        for t in origins:
            need = range(t - WINDOW + 1, t + HORIZON + 1)
            if not all(y in s for y in need):
                continue
            point = sum(s[y] for y in range(t - WINDOW + 1, t + 1)) / WINDOW * HORIZON
            actual = sum(s[y] for y in range(t + 1, t + HORIZON + 1))
            if point > 0 and actual > 0:
                runs.append(Run(f, t, point, actual))
    return runs


def percentile_band(runs: list[Run], q: tuple[float, float] = PERCENTILES) -> tuple[float, float]:
    """P10 and P90 of actual / forecast (numpy's default linear interpolation)."""
    r = np.array([x.ratio for x in runs])
    lo, hi = np.percentile(r, q)
    return float(lo), float(hi)


def apply_band(runs: list[Run], lo: float, hi: float) -> list[Run]:
    return [Run(x.state, x.origin, x.point, x.actual, x.point * lo, x.point * hi) for x in runs]


# ---------------------------------------------------------------- rule B (Adam's)


def adam_runs(panel: Panel, origins: tuple[int, ...] = ADAM_ORIGINS,
              history: int = ADAM_HISTORY) -> list[Run]:
    """Point = last five years' total; band = point x (min, max) / mean of rolling 5-yr totals."""
    runs = []
    for f in sorted(panel):
        s = panel[f]
        for t in origins:
            if not all(y in s for y in range(t - history + 1, t + HORIZON + 1)):
                continue
            totals = [sum(s[y] for y in range(a, a + HORIZON))
                      for a in range(t - history + 1, t - HORIZON + 2)]
            avg = sum(totals) / len(totals)
            point = sum(s[y] for y in range(t - HORIZON + 1, t + 1))
            actual = sum(s[y] for y in range(t + 1, t + HORIZON + 1))
            runs.append(Run(f, t, point, actual, point * min(totals) / avg, point * max(totals) / avg))
    return runs


# ---------------------------------------------------------------- summaries


def coverage(runs: list[Run]) -> dict[str, float]:
    pos = [x.position for x in runs]
    n = len(runs)
    width = [x.high / x.low for x in runs if x.low > 0]
    return {"n": n, "inside": pos.count("inside"), "above": pos.count("above"),
            "below": pos.count("below"), "share_inside": pos.count("inside") / n if n else math.nan,
            "mdape": float(np.median([x.ape for x in runs])) if runs else math.nan,
            "miss_vs_point": (float(np.median([abs(x.point - x.actual) / x.point for x in runs]))
                              if runs else math.nan),
            "median_width": float(np.median(width)) if width else math.nan}


def by_origin(runs: list[Run]) -> dict[int, dict[str, float]]:
    return {t: coverage([x for x in runs if x.origin == t]) for t in sorted({x.origin for x in runs})}


def coverage_by_period(panel: Panel, lo: float, hi: float,
                       periods: tuple[tuple[int, int], ...] = PERIODS) -> list[dict]:
    """The fixed band (point x lo to x hi) applied to every origin, grouped by period."""
    runs = apply_band(mean3_runs(panel, tuple(range(periods[0][0], periods[-1][1] + 1))), lo, hi)
    out = []
    for a, b in periods:
        c = coverage([x for x in runs if a <= x.origin <= b])
        out.append({"origins": [a, b], "label": PERIOD_LABELS.get((a, b), ""), **c})
    return out


def realtime_test(panel: Panel, origins: tuple[int, ...] = REALTIME_ORIGINS,
                  first_fit: int = EST_ORIGINS[0]) -> dict:
    """Refit P10/P90 at each origin t on origins first_fit..t-5 only (windows already closed).

    This is what a forecaster standing at t could have drawn: the band uses no year after t.
    """
    rows, every = [], []
    for t in origins:
        fit = mean3_runs(panel, tuple(range(first_fit, t - HORIZON + 1)))
        lo, hi = percentile_band(fit)
        runs = apply_band(mean3_runs(panel, (t,)), lo, hi)
        every += runs
        rows.append({"origin": t, "fit_runs": len(fit), "p10": lo, "p90": hi, **coverage(runs)})
    groups = [{"origins": [a, b], **coverage([x for x in every if a <= x.origin <= b])}
              for a, b in REALTIME_GROUPS]
    return {"by_origin": rows, "overall": coverage(every), "groups": groups}


def run_backtest(panel: Panel) -> dict:
    """Everything docs/evidence/baseline_backtest.md reports."""
    est = mean3_runs(panel, EST_ORIGINS)
    lo, hi = percentile_band(est)
    test = apply_band(mean3_runs(panel, TEST_ORIGINS), lo, hi)
    est_b = apply_band(est, lo, hi)
    adam = adam_runs(panel)
    adam_test = adam_runs(panel, TEST_ORIGINS)
    return {
        "states": len(panel),
        "years": (min(y for s in panel.values() for y in s), max(y for s in panel.values() for y in s)),
        "methods": method_table(panel),
        "methods_post2010": method_table(panel, tuple(range(2010, 2021))),
        "ours": {"p10": lo, "p90": hi, "estimation": coverage(est_b), "test": coverage(test),
                 "estimation_by_origin": by_origin(est_b), "test_by_origin": by_origin(test),
                 "by_period": coverage_by_period(panel, lo, hi), "realtime": realtime_test(panel)},
        "adam": {"runs": coverage(adam), "by_origin": by_origin(adam),
                 "test": coverage(adam_test), "test_by_origin": by_origin(adam_test)},
    }


def register_citation(r: dict) -> str:
    o = r["ours"]
    return (f"docs/evidence/baseline_backtest.md, band rule A: for the 50 states and DC and forecast "
            f"origins 1990-2015 ({o['estimation']['n']:,} runs), actual five-year permits / (3-year mean "
            f"x 5) has 10th percentile {o['p10']:.4f} and 90th percentile {o['p90']:.4f} (numpy linear "
            f"interpolation). Out of sample, origins 2016-2020: {o['test']['inside']} of "
            f"{o['test']['n']} inside ({o['test']['share_inside']:.0%}). Example: a 10,000-permit point "
            f"gives a band of {10000 * o['p10']:,.0f} to {10000 * o['p90']:,.0f}.")


def write_register_band(r: dict, path: Path) -> None:
    """Write P10, P90 and the citation into the baseline_band_ratio entry, keeping comments."""
    text = path.read_text(encoding="utf-8")
    start = text.index("  - id: baseline_band_ratio")
    end = text.index("\n  - id:", start + 10)
    block = text[start:end]
    o = r["ours"]
    block = re.sub(r"\n    low: [^\n]+", f"\n    low: {o['p10']:.4f}", block, count=1)
    block = re.sub(r"\n    high: [^\n]+", f"\n    high: {o['p90']:.4f}", block, count=1)
    block = re.sub(r"(\n    citation: >-\n)(      [^\n]+\n)+",
                   lambda m: m.group(1) + _wrap(register_citation(r), 6), block, count=1)
    est, test = o["estimation"], o["test"]
    block = re.sub(r"\n    coverage: [^\n]+", (
        f"\n    coverage: {{estimation_runs: {est['n']}, estimation_share_inside: {est['share_inside']:.4f}, "
        f"test_runs: {test['n']}, test_inside: {test['inside']}, test_share_inside: "
        f"{test['share_inside']:.4f}, test_median_width: {test['median_width']:.4f}}}"), block, count=1)
    block = re.sub(r"\n    coverage_by_period: [^\n]+", "\n    coverage_by_period: " + _period_flow(o["by_period"]),
                   block, count=1)
    rec = realtime_record(o["realtime"])
    block = re.sub(r"\n    coverage_realtime: [^\n]+", (
        f"\n    coverage_realtime: {{origins: {rec['origins']}, runs: {rec['runs']}, inside: {rec['inside']}, "
        f"share_inside: {rec['share_inside']:.4f}, origins_under_5pct: {rec['origins_under_5pct']}, "
        f"groups: {_period_flow(o['realtime']['groups'])}}}"), block, count=1)
    text = text[:start] + block + text[end:]
    a, at = r["adam"]["runs"], r["adam"]["test"]
    start = text.index("  - id: baseline_alt_band_history_years")
    end = text.index("\n  - id:", start + 10)
    alt = re.sub(r"\n    coverage: [^\n]+", (
        f"\n    coverage: {{runs: {a['n']}, inside: {a['inside']}, above: {a['above']}, below: {a['below']}, "
        f"test_runs: {at['n']}, test_share_inside: {at['share_inside']:.4f}, test_median_width: "
        f"{at['median_width']:.4f}}}"), text[start:end], count=1)
    path.write_text(text[:start] + alt + text[end:], encoding="utf-8")


def realtime_record(rt: dict) -> dict:
    """The register's (and results file's) summary of the real-time test."""
    ov = rt["overall"]
    return {"origins": [REALTIME_ORIGINS[0], REALTIME_ORIGINS[-1]], "runs": ov["n"], "inside": ov["inside"],
            "share_inside": ov["share_inside"],
            "origins_under_5pct": [c["origin"] for c in rt["by_origin"] if c["share_inside"] < 0.05]}


def _period_flow(rows: list[dict]) -> str:
    """One-line YAML flow list of {origins, runs, inside, above, below, share_inside}."""
    return "[" + ", ".join(
        f"{{origins: [{r['origins'][0]}, {r['origins'][1]}], runs: {r['n']}, inside: {r['inside']}, "
        f"above: {r['above']}, below: {r['below']}, share_inside: {r['share_inside']:.4f}}}"
        for r in rows) + "]"


def _wrap(text: str, indent: int, width: int = 96) -> str:
    return "\n".join(textwrap.wrap(text, width=width, initial_indent=" " * indent,
                                    subsequent_indent=" " * indent)) + "\n"


# ---------------------------------------------------------------- report


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render_markdown(r: dict, run_date: str) -> str:
    o, a = r["ours"], r["adam"]
    y0, y1 = r["years"]
    L = [
        "# Baseline backtest: how often the real five-year total fell inside the band",
        "",
        (f"Generated by `hre validate --baseline` on {run_date} from the Census Building Permits Survey "
        f"state annual files {y0}-{y1} (units authorised, estimates with imputation; "
        f"https://www2.census.gov/econ/bps/State/), {r['states']} jurisdictions (50 states and DC). "
        "Code: `src/hre/validation/backtest_baseline.py`."),
        "",
        ("**How to read this.** A forecast *origin* is the last year of data a forecast uses; the "
        "forecast covers the next five years. For every state and origin we compute the baseline the "
        "way the tool does today and compare it with what was actually permitted. The bands below are "
        "assumption sets fitted to history. \"Inside in 80% of past periods\" is a count of past "
        "periods, not a probability that the future lands inside."),
        "",
        "## 1. Which simple forecast to use (reproduces evidence_base.md section 7)",
        "",
        "Origins 1999-2020, ten years of history required, error of the five-year total.",
        "",
        "| Method | Runs | Median absolute error | Within ±25% | Within ±50% | Median bias |",
        "|---|---|---|---|---|---|",
    ]
    for m in r["methods"].values():
        L.append(f"| {m['label']} | {m['n']:,} | {_pct(m['mdape'])} | {m['within25']:.0%} | "
                 f"{m['within50']:.0%} | {100 * m['bias_median']:+.1f}% |")
    p = r["methods_post2010"]["mean3"]
    L += [
        "",
        (f"Post-2010 origins, 3-year mean: {p['n']} runs, median absolute error {_pct(p['mdape'])}, "
        f"{p['within25']:.0%} within ±25%, median bias {100 * p['bias_median']:+.1f}% (under-forecast "
        "in the recovery). The research script counted 1,123 runs because it kept one Virgin Islands "
        "series (BPS code 52); excluding territories gives the counts above, and every rate matches "
        "the research table to the rounding shown there."),
        "",
        ("The tool uses the 3-year mean (`baseline_window_years` = 3): within 3 points of the best "
        "method, and one unusual year moves it a third as much as the last-year rule."),
        "",
        "## 2. Band rule A (ours): empirical 10th and 90th percentiles of actual ÷ forecast",
        "",
        (f"Fitted on origins {EST_ORIGINS[0]}-{EST_ORIGINS[-1]} ({o['estimation']['n']:,} runs): "
        f"**P10 = {o['p10']:.4f}, P90 = {o['p90']:.4f}**. The band is the baseline point × "
        f"{o['p10']:.3f} to × {o['p90']:.3f}. These two numbers are written into the register as "
        "`baseline_band_ratio` (locator: this document)."),
        "",
        "| Window | Runs | Inside | Above | Below | Share inside | Median abs. error of the point | Median high ÷ low |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, c in (("Estimation, origins 1990-2015 (in sample)", o["estimation"]),
                    ("Test, origins 2016-2020 (out of sample)", o["test"])):
        L.append(f"| {name} | {c['n']} | {c['inside']} | {c['above']} | {c['below']} | "
                 f"{c['share_inside']:.0%} | {_pct(c['mdape'])} | {c['median_width']:.2f} |")
    L += ["", "By origin (rule A):", "",
          "| Origin | Runs | Inside | Above | Below | Share inside | Median abs. error |",
          "|---|---|---|---|---|---|---|"]
    for t, c in {**o["estimation_by_origin"], **o["test_by_origin"]}.items():
        tag = " (test)" if t in TEST_ORIGINS else ""
        L.append(f"| {t}{tag} | {c['n']} | {c['inside']} | {c['above']} | {c['below']} | "
                 f"{c['share_inside']:.0%} | {_pct(c['mdape'])} |")
    L += ["", "### Coverage by period: the same fixed band on every origin 1990-2020", "",
          ("Decision 66. The band is fitted once (origins 1990-2015) and laid over every origin. "
           "In-sample periods are shown too, because the point is how coverage moves with the market, "
           "not whether the fit is honest overall."), "",
          "| Origins | Period | Runs | Inside | Above | Below | Share inside |",
          "|---|---|---|---|---|---|---|"]
    for c in o["by_period"]:
        L.append(f"| {c['origins'][0]}-{c['origins'][1]} | {c['label']} | {c['n']} | {c['inside']} | "
                 f"{c['above']} | {c['below']} | {c['share_inside']:.0%} |")
    rt = o["realtime"]
    L += ["", "### Real-time test: refit the band each year on closed windows only", "",
          ("At each origin t from 2000 to 2020 the 10th and 90th percentiles are refitted on origins "
           f"{EST_ORIGINS[0]} to t-5, the only five-year windows a forecaster at t could already score, and "
           "applied to t. No year after t is used."), "",
          "| Origin | Fit runs | P10 | P90 | Runs | Inside | Above | Below | Share inside |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in rt["by_origin"]:
        L.append(f"| {c['origin']} | {c['fit_runs']} | {c['p10']:.3f} | {c['p90']:.3f} | {c['n']} | "
                 f"{c['inside']} | {c['above']} | {c['below']} | {c['share_inside']:.0%} |")
    ov = rt["overall"]
    L += ["", (f"Overall, origins 2000-2020: **{ov['inside']} of {ov['n']} inside ({ov['share_inside']:.0%})**, "
               f"{ov['above']} above, {ov['below']} below."), "",
          "| Origins | Runs | Inside | Above | Below | Share inside |", "|---|---|---|---|---|---|"]
    for c in rt["groups"]:
        L.append(f"| {c['origins'][0]}-{c['origins'][1]} | {c['n']} | {c['inside']} | {c['above']} | "
                 f"{c['below']} | {c['share_inside']:.0%} |")
    L += ["", band_period_reading(o["by_period"]) + " " + band_realtime_reading(realtime_record(rt))]
    ac = a["runs"]
    worst = min(a["by_origin"].items(), key=lambda kv: kv[1]["share_inside"])
    L += [
        "",
        "## 3. Band rule B (Adam Ruege's v2.0): slowest and fastest five-year totals of the prior 20 years",
        "",
        ("Point = the last five years' total. Band = point × (slowest ÷ average) to point × (fastest ÷ "
        "average), over the rolling five-year totals of the 20 years up to the origin. Origins "
        f"{', '.join(map(str, ADAM_ORIGINS))}, as in his run."),
        "",
        (f"Reproduction: **{ac['inside']} of {ac['n']} inside ({ac['share_inside']:.0%}), {ac['above']} above, "
        f"{ac['below']} below**; worst origin {worst[0]} with {worst[1]['inside']} of {worst[1]['n']} inside "
        f"and a median miss of {_pct(worst[1]['miss_vs_point'])} (|forecast − actual| ÷ forecast, his "
        f"measure; {_pct(worst[1]['mdape'])} measured against the actual). Adam's payload reports 181 of 255, 37 "
        "above, 37 below, worst start year 2005 with 20 of 51 inside and a median miss of 39%."),
        "",
        "| Origin | Runs | Inside | Above | Below | Share inside | Median abs. error | Median high ÷ low |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t, c in a["by_origin"].items():
        L.append(f"| {t} | {c['n']} | {c['inside']} | {c['above']} | {c['below']} | "
                 f"{c['share_inside']:.0%} | {_pct(c['mdape'])} | {c['median_width']:.2f} |")
    at = a["test"]
    L += [
        "",
        "## 4. The two rules side by side on the same test origins (2016-2020)",
        "",
        "| Rule | Runs | Share inside | Above | Below | Median high ÷ low |",
        "|---|---|---|---|---|---|",
        (f"| A, ours (P10/P90 fitted 1990-2015) | {o['test']['n']} | {o['test']['share_inside']:.0%} | "
        f"{o['test']['above']} | {o['test']['below']} | {o['test']['median_width']:.2f} |"),
        (f"| B, Adam's 20-year min/max | {at['n']} | {at['share_inside']:.0%} | {at['above']} | "
        f"{at['below']} | {at['median_width']:.2f} |"),
        "",
        "## 5. Which band is the headline, and why both are shown",
        "",
        ("The tool's headline band is rule A. Rule B is shown beside it in every results file "
        "(`baseline.alternative_band`), in its own section, computed exactly as tested here: the last "
        "five years' total stretched by the state's own slowest and fastest five years of the past 20 "
        "(decision 69). Rule A makes one checkable promise (inside in 80% of past periods) that held out "
        "of sample and allows for a shock the size of 2008. Rule B is narrower and follows each state's "
        "own history, but it promises no fixed coverage and missed most states after 2005. Showing both "
        "lets a reader see the trade-off between a wide band that rarely misses and a tight band that "
        "sometimes does."),
        "",
        "## 6. Plain-language reading",
        "",
        (f"- In {o['estimation']['share_inside']:.0%} of past five-year periods from origins 1990-2015, "
        f"the actual statewide permit total fell between {o['p10']:.2f} and {o['p90']:.2f} times the "
        "3-year-mean baseline (80% by construction: that is how the band was fitted)."),
        (f"- On origins 2016-2020, which the fit never saw, {o['test']['share_inside']:.0%} of actual "
        f"totals fell inside ({o['test']['inside']} of {o['test']['n']}); {o['test']['above']} were "
        f"above the band and {o['test']['below']} below."),
        (f"- Adam's rule put {ac['share_inside']:.0%} of his {ac['n']} runs inside; its band is set by each "
        "state's own swings, so it is narrow in steady states and wide in boom-and-bust states."),
        ("- Neither band is a probability. Both are summaries of how far five-year building has strayed "
        "from a simple continuation in the past; a recession or a boom outside that history would "
        "fall outside."),
        ("- The band is fitted on state totals and applied to counties as well; a single county's "
        "error is larger, and the results file says so."),
        "",
    ]
    return "\n".join(L)
