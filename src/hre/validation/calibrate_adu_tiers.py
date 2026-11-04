"""Calibrate the ADU home-value tiers from HCD Table A2 and ACS place values.

Ports the logic of Adam Ruege's ``download_data.py --california-adu`` (Housing
Reform Estimator v2.0) as his register describes it; his source archive has not
arrived (decision 43), so the steps below are re-derived and every difference
from his published numbers is reported in docs/evidence/adu_tiers.md.

1. Cities: every incorporated California city that appears in the de-duplicated
   HCD ADU table (``data/processed/CA_hcd_adu.json``, decision 50) and has an ACS
   2020-2024 median home value (B25077) and a detached-home count (B25024).
   County (unincorporated) jurisdictions are left out. HCD names are matched to
   Census place names; seven need an alias (``ALIASES``).
2. Completions: the city's de-duplicated ADU completions in report years 2023-2025;
   a city with no row in a year counts zero for that year.
3. Rate: completions / (3 x detached homes), per detached home per year.
4. Tier bounds: inclusive quintiles (numpy linear interpolation) of city median
   values, Los Angeles excluded (it alone would set its tier's rate).
5. Tier rate (mid): sum of completions / (3 x sum of detached homes) over the tier's
   cities (home-weighted). Low and high: mid x (first-quartile city rate / median
   city rate) and mid x (third-quartile / median), "the spread from the first- to
   third-quartile city, relative to its median city, around that rate".
6. City-split check: 1,000 random halves (seed ``SEED``); fit steps 4-5 on one half
   (always without LA), predict the other half's three-year completions at low, mid
   and high; count splits where the actual total is inside. Run with LA in the pool
   and without it. Adam's run: 953 of 1,000 with LA (median 1.31x the middle),
   1,000 of 1,000 without (0.98x).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from hre.data.fetch_acs import PREFIX_PLACE, load_geo_names, load_place_acs

YEARS = (2023, 2024, 2025)
LA = "LOS ANGELES"
SEED = 20261103
N_SPLITS = 1000
ALIASES = {
    "CATHEDRAL": "cathedral city", "SAINT HELENA": "st helena", "VENTURA": "san buenaventura ventura",
    "CARMEL": "carmel by the sea", "AMADOR": "amador city",
    "PASO ROBLES": "el paso de robles paso robles", "ANGELS CAMP": "angels",
}


@dataclass(frozen=True)
class Cities:
    name: list[str]
    value: np.ndarray        # ACS median home value
    detached: np.ndarray     # ACS single-family detached homes
    completed: np.ndarray    # HCD ADU completions over YEARS (de-duplicated)


def _key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def load_cities(processed_dir: Path = Path("data/processed"), data_dir: Path | None = None) -> Cities:
    """Join the HCD ADU table to ACS place values (needs `make hcd` and the ACS cache)."""
    table = json.loads((processed_dir / "CA_hcd_adu.json").read_text(encoding="utf-8"))
    names = load_geo_names(PREFIX_PLACE, "06", data_dir)
    acs = load_place_acs("06", data_dir)
    places: dict[str, str] = {}
    for geoid, nm in names.items():
        m = re.match(r"^(.*) (city|town), California$", nm)
        if m:
            places[_key(m.group(1))] = geoid
    completed: dict[str, int] = {}
    for r in table["rows"]:
        j = r["jurisdiction"]
        if j.endswith(" COUNTY"):
            continue
        completed.setdefault(j, 0)
        if r["year"] in YEARS:
            completed[j] += int(r["completed"])
    out_n, out_v, out_d, out_c = [], [], [], []
    unmatched = []
    for j in sorted(completed):
        geoid = places.get(ALIASES.get(j, _key(j)))
        if geoid is None:
            unmatched.append(j)
            continue
        a = acs.get(geoid, {})
        if not a.get("median_value") or not a.get("sf_detached"):
            continue
        out_n.append(j)
        out_v.append(a["median_value"])
        out_d.append(a["sf_detached"])
        out_c.append(completed[j])
    if unmatched:
        raise ValueError(f"HCD jurisdictions with no Census place: {unmatched}")
    return Cities(out_n, np.array(out_v, float), np.array(out_d, float), np.array(out_c, float))


@dataclass(frozen=True)
class TierFit:
    bounds: np.ndarray        # 4 cut points
    mid: np.ndarray           # 5 home-weighted rates
    low: np.ndarray
    high: np.ndarray
    n_cities: np.ndarray      # per tier
    detached: np.ndarray      # per tier
    completed: np.ndarray     # per tier
    q1: np.ndarray            # first-quartile, median, third-quartile city rate per tier
    q2: np.ndarray
    q3: np.ndarray


def assign(values: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    """Tier index 0-4 (value <= bound k goes to tier k), same rule as hre.model.tiers."""
    return np.searchsorted(bounds, values, side="left")


def fit_tiers(value: np.ndarray, detached: np.ndarray, completed: np.ndarray,
              years: int = len(YEARS)) -> TierFit:
    bounds = np.percentile(value, [20, 40, 60, 80])
    t = assign(value, bounds)
    rate = completed / (years * detached)
    mid, low, high, n, det, comp, q1s, q2s, q3s = ([] for _ in range(9))
    for k in range(5):
        sel = t == k
        m = completed[sel].sum() / (years * detached[sel].sum())
        q1, q2, q3 = np.percentile(rate[sel], [25, 50, 75])
        mid.append(m)
        low.append(m * q1 / q2 if q2 > 0 else 0.0)
        high.append(m * q3 / q2 if q2 > 0 else m)
        n.append(int(sel.sum()))
        det.append(detached[sel].sum())
        comp.append(completed[sel].sum())
        q1s.append(q1)
        q2s.append(q2)
        q3s.append(q3)
    a = np.array
    return TierFit(bounds, a(mid), a(low), a(high), a(n), a(det), a(comp), a(q1s), a(q2s), a(q3s))


def fit_without_la(c: Cities) -> TierFit:
    keep = np.array([n != LA for n in c.name])
    return fit_tiers(c.value[keep], c.detached[keep], c.completed[keep])


def predict(fit: TierFit, value: np.ndarray, detached: np.ndarray, years: int = len(YEARS)) -> dict:
    t = assign(value, fit.bounds)
    return {lv: float((detached * getattr(fit, lv)[t]).sum() * years) for lv in ("low", "mid", "high")}


def split_check(c: Cities, include_la: bool, n_splits: int = N_SPLITS, seed: int = SEED) -> dict:
    """Fit on a random half (without LA), predict the other half; count totals inside."""
    names = np.array(c.name)
    pool = np.arange(len(names)) if include_la else np.flatnonzero(names != LA)
    rng = np.random.default_rng(seed)
    inside, ratios, la_held = 0, [], 0
    half = len(pool) // 2
    for _ in range(n_splits):
        perm = rng.permutation(pool)
        train, test = perm[:half], perm[half:]
        train = train[names[train] != LA]
        fit = fit_tiers(c.value[train], c.detached[train], c.completed[train])
        pred = predict(fit, c.value[test], c.detached[test])
        actual = float(c.completed[test].sum())
        inside += pred["low"] <= actual <= pred["high"]
        ratios.append(actual / pred["mid"])
        la_held += bool((names[test] == LA).any())
    r = np.array(ratios)
    return {"splits": n_splits, "inside": int(inside), "median_ratio": float(np.median(r)),
            "min_ratio": float(r.min()), "max_ratio": float(r.max()), "la_in_test": la_held,
            "cities": len(pool)}


# ---------------------------------------------------------------- register and report

ADAM = {  # Adam Ruege's v2.0 register (payload, build v2.0-a3d61961fd76), for comparison only
    "bounds": [453700, 647820, 847440, 1201720],
    "mid": [0.000828, 0.001601, 0.002773, 0.002492, 0.002905],
    "low": [0.000181, 0.000818, 0.001481, 0.001422, 0.001566],
    "high": [0.001819, 0.003951, 0.004766, 0.004440, 0.004102],
    "cities": [81, 80, 81, 80, 81],
}


def _money(x: float) -> str:
    return f"${x:,.0f}"


def register_block(fit: TierFit, n_cities: int, la_rate: float, run_date: str) -> str:
    """YAML for the 9 tier entries (replaces the generated block in parameters.yaml)."""
    src = ("      - title: California HCD Annual Progress Report Table A2 (ADU rows), de-duplicated (decision 50)\n"
           "        url: https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year\n"
           "        locator: \"report years 2023-2025, UNIT_CAT == ADU, certificates of occupancy; data/processed/CA_hcd_adu.json\"\n"
           f"        accessed: \"{run_date}\"\n"
           "      - title: ACS 2020-2024 five-year, tables B25077 (median value) and B25024 (units in structure), California places\n"
           "        url: https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/\n"
           "        locator: \"place summary level 160, B25077_E001 and B25024_E002\"\n"
           f"        accessed: \"{run_date}\"\n"
           "      - title: Permit Horizon ADU tier calibration (docs/evidence/adu_tiers.md)\n"
           "        url: https://github.com/rmanacha/permit-horizon/blob/main/docs/evidence/adu_tiers.md\n"
           "        locator: \"tier table and city-split check\"\n"
           f"        accessed: \"{run_date}\"\n")
    out = ["  # ---- ADU value tiers (generated by `hre validate --adu-tiers --write-register`; do not edit by hand)\n"]
    for k in range(4):
        b = fit.bounds[k]
        out.append(
            f"  - id: adu_value_bound_{k + 1}\n"
            f"    label: Home value tier {k + 1} upper bound\n"
            f"    description: Counties with a median home value up to this amount (and above the previous bound) get tier {k + 1}'s ADU rate.\n"
            f"    unit: dollars, median value of owner-occupied homes\n"
            f"    low: {b:.0f}\n    mid: {b:.0f}\n    high: {b:.0f}\n"
            f"    scope: county\n    scenarios: [adu]\n    grade: R\n    confidence: high\n    direction: 0\n"
            f"    sources:\n{src}"
            f"    citation: >-\n"
            f"      Inclusive quintiles (numpy linear interpolation) of the median home values of {n_cities} California\n"
            f"      cities, Los Angeles left out: the {20 * (k + 1)}th percentile is {_money(b)}. Computed by\n"
            f"      `hre validate --adu-tiers` on {run_date}.\n"
            f"    rationale: Five groups of about {n_cities // 5} cities by home value.\n"
            f"    transferability: A county's median value places it beside California cities of similar value.\n"
            f"    levels: {{low: \"{_money(b)}\", mid: \"{_money(b)}\", high: \"{_money(b)}\"}}\n")
    for k in range(5):
        lo_b = "0" if k == 0 else _money(fit.bounds[k - 1])
        hi_b = "and above" if k == 4 else f"to {_money(fit.bounds[k])}"
        out.append(
            f"  - id: adu_rate_tier_{k + 1}\n"
            f"    label: ADU completions per detached home per year, tier {k + 1} (median value {lo_b} {hi_b})\n"
            f"    description: Home-weighted ADU completion rate of the tier's California cities, 2023-2025; applied to a county's detached homes.\n"
            f"    unit: ADUs completed per single-family detached home per year\n"
            f"    low: {fit.low[k]:.6f}\n    mid: {fit.mid[k]:.6f}\n    high: {fit.high[k]:.6f}\n"
            f"    scope: county\n    scenarios: [adu]\n    grade: B\n    confidence: moderate\n    direction: 1\n"
            f"    sources:\n{src}"
            f"    citation: >-\n"
            f"      {fit.n_cities[k]} cities, {fit.completed[k]:,.0f} ADU completions 2023-2025 over {fit.detached[k]:,.0f}\n"
            f"      detached homes: {fit.completed[k]:,.0f} / (3 x {fit.detached[k]:,.0f}) = {fit.mid[k]:.6f} per year (mid).\n"
            f"      City rates: first quartile {fit.q1[k]:.6f}, median {fit.q2[k]:.6f}, third quartile {fit.q3[k]:.6f};\n"
            f"      low = {fit.mid[k]:.6f} x {fit.q1[k]:.6f} / {fit.q2[k]:.6f} = {fit.low[k]:.6f}; high = {fit.mid[k]:.6f} x\n"
            f"      {fit.q3[k]:.6f} / {fit.q2[k]:.6f} = {fit.high[k]:.6f}. Los Angeles ({100 * la_rate:.3f}% a year) is left\n"
            f"      out because it alone would set its tier's rate. Adam Ruege's v2.0 value for this tier:\n"
            f"      {ADAM['mid'][k]:.6f} (raw completions, 403 cities).\n"
            f"    rationale: Under the same state law, California cities where homes are worth more completed more ADUs per detached home.\n"
            f"    transferability: California's mature ADU law and high prices; other states start slower (ramp) and the Seattle and Maine overlays bracket it.\n"
            f"    levels: {{low: \"{100 * fit.low[k]:.3f}%\", mid: \"{100 * fit.mid[k]:.3f}%\", high: \"{100 * fit.high[k]:.3f}%\"}}\n")
    out.append("  # ---- end ADU value tiers\n")
    return "".join(out)


def write_register_tiers(block: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    start_tag = "  # ---- ADU value tiers"
    end_tag = "  # ---- end ADU value tiers\n"
    if start_tag in text:
        a = text.index(start_tag)
        b = text.index(end_tag) + len(end_tag)
        text = text[:a] + block + text[b:]
    else:
        text = text.rstrip("\n") + "\n\n" + block
    path.write_text(text, encoding="utf-8")


def render_markdown(c: Cities, fit: TierFit, with_la: dict, without_la: dict, run_date: str) -> str:
    names = np.array(c.name)
    la = names == LA
    la_rate = float(c.completed[la].sum() / (3 * c.detached[la].sum())) if la.any() else float("nan")
    n = int((~la).sum())
    L = [
        "# ADU completion rates by home-value tier (California HCD Table A2)",
        "",
        (f"Generated by `hre validate --adu-tiers` on {run_date}. Code: "
        "`src/hre/validation/calibrate_adu_tiers.py`; engine lookup: `src/hre/model/tiers.py`."),
        "",
        (f"Cities: {n} incorporated California cities in the de-duplicated HCD ADU table with an ACS "
        "2020-2024 median value and detached-home count (Los Angeles shown separately). Completions: "
        "report years 2023-2025, de-duplicated by the Phase 1 rule (decision 50). Rate = completions ÷ "
        "(3 × detached homes), per detached home per year."),
        "",
        "## Tiers (written into the register)",
        "",
        "| Tier | Median value | Cities | Detached homes | ADU completions 2023-25 | Low | Mid | High | Adam v2.0 mid (low-high) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for k in range(5):
        rng = (f"up to {_money(fit.bounds[0])}" if k == 0 else
               f"above {_money(fit.bounds[3])}" if k == 4 else
               f"{_money(fit.bounds[k - 1])} to {_money(fit.bounds[k])}")
        L.append(f"| {k + 1} | {rng} | {fit.n_cities[k]} | {fit.detached[k]:,.0f} | {fit.completed[k]:,.0f} | "
                 f"{100 * fit.low[k]:.3f}% | **{100 * fit.mid[k]:.3f}%** | {100 * fit.high[k]:.3f}% | "
                 f"{100 * ADAM['mid'][k]:.3f}% ({100 * ADAM['low'][k]:.3f}-{100 * ADAM['high'][k]:.3f}%) |")
    L += [
        "",
        (f"Los Angeles: {c.completed[la].sum():,.0f} completions over {c.detached[la].sum():,.0f} detached homes "
        f"= {100 * la_rate:.3f}% a year, about three times its tier's rate (Adam: 0.938%, raw completions)."),
        "",
        ("Arithmetic for each rate (mid = tier completions ÷ (3 × tier detached homes); low and high scale the mid "
        "by the first- and third-quartile city rate over the median city rate) is in each register entry's "
        "`citation`."),
        "",
        "Bounds, Adam v2.0: " + ", ".join(_money(b) for b in ADAM["bounds"]) + " (403 cities). Ours: "
        + ", ".join(_money(b) for b in fit.bounds) + f" ({n} cities). Differences: we use de-duplicated "
        "completions (his Los Angeles rate matches the raw series) and every city in the HCD ADU table with an "
        "ACS value; his city filter is not documented in the payload.",
        "",
        "## City-split check (1,000 random halves)",
        "",
        ("Fit the tiers on a random half of the cities (Los Angeles never in the fit), predict the other half's "
        "2023-2025 completions at the low, mid and high rates, and count the splits whose actual total is "
        f"inside the low-high range. Seed {SEED}."),
        "",
        "| Pool | Cities | Splits inside | Median actual ÷ mid | Range of actual ÷ mid | Splits with LA held out | Adam v2.0 |",
        "|---|---|---|---|---|---|---|",
        (f"| With Los Angeles | {with_la['cities']} | {with_la['inside']} of {with_la['splits']} | "
        f"{with_la['median_ratio']:.2f} | {with_la['min_ratio']:.2f} to {with_la['max_ratio']:.2f} | "
        f"{with_la['la_in_test']} | 953 of 1,000; median 1.31 (0.69 to 2.08) |"),
        (f"| Without Los Angeles | {without_la['cities']} | {without_la['inside']} of {without_la['splits']} | "
        f"{without_la['median_ratio']:.2f} | {without_la['min_ratio']:.2f} to {without_la['max_ratio']:.2f} | "
        f"0 | 1,000 of 1,000; median 0.98 |"),
        "",
        ("Reading: the range is wide enough to hold a held-out half of California's cities in "
        f"{without_la['inside'] / without_la['splits']:.0%} of splits without Los Angeles; when Los Angeles lands "
        "in the held-out half, its rate (about three times its tier) can push the total above the high end. "
        "This is a calibration check inside California, not a test of transfer to other states; the frozen "
        "Seattle holdout (Phase 5) is that test."),
        "",
    ]
    return "\n".join(L)
