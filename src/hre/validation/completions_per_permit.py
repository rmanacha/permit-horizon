"""Completions per permit by structure type, from the Census NRC annual tables (decision 68).

    ratio(series, type, a..b) = sum of completions a..b / sum of permits a..b

Permits: units authorized in permit-issuing places. Completions: two series, in
permit-issuing areas (like for like with our BPS baseline) and in all areas (what the
research session used). Cumulative sums over 30 and 15 years absorb the one-to-two-year
lag from permit to completion except at the ends of the window.

Register rule (decision 70): mid and high = the permit-area ratio for 1995-2024; low =
the permit-area ratio for 2010-2024. The 2-4 entry uses the all-structures ratio, because
the published 2-4 completion series is not a completion rate: the Survey of
Construction reclassifies townhouses that permit offices filed as multifamily into
one-unit structures (Census, "Data Relationships between Permits, Starts, and
Completions"), so 2-4 completions run at about 40% of 2-4 permits and one-unit
completions slightly above one-unit permits. The total is unaffected by reclassification.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

from hre.data.fetch_nrc import FILES, NRC_BASE, RELATIONSHIPS_URL

PERIODS = ((1995, 2024), (2010, 2024))
TYPES = {"u1": "1 unit", "u24": "2 to 4 units", "u5": "5 units or more", "total": "All structures"}
SERIES = {"completions_permit_areas": "permit-issuing areas", "completions_all_areas": "all areas"}
# register id -> NRC column used for its value
REGISTER = {"completions_per_permit_1unit": "u1", "completions_per_permit_2to4": "total",
            "completions_per_permit_5plus": "u5"}
RESEARCH = {"completions_per_permit_1unit": (0.99, 1.03), "completions_per_permit_2to4": (0.89, 0.94),
            "completions_per_permit_5plus": (0.75, 0.79)}   # (2010-2024, 1995-2024), all areas


def cumulative(nrc: dict, series: str, col: str, a: int, b: int) -> dict[str, float] | None:
    """Sum of completions and permits over a..b and their ratio; None if a year is missing."""
    comp = [nrc[series].get(y, {}).get(col) for y in range(a, b + 1)]
    perm = [nrc["permits"].get(y, {}).get(col) for y in range(a, b + 1)]
    if any(v is None for v in comp + perm):
        return None
    c, p = sum(comp), sum(perm)
    return {"completions": c, "permits": p, "ratio": c / p}


def ratio_table(nrc: dict) -> dict[tuple[str, str, int, int], dict[str, float] | None]:
    return {(s, col, a, b): cumulative(nrc, s, col, a, b)
            for s in SERIES for col in TYPES for a, b in PERIODS}


def register_values(table: dict) -> dict[str, dict[str, float]]:
    out = {}
    for pid, col in REGISTER.items():
        full = table[("completions_permit_areas", col, 1995, 2024)]["ratio"]
        recent = table[("completions_permit_areas", col, 2010, 2024)]["ratio"]
        out[pid] = {"low": round(recent, 2), "mid": round(full, 2), "high": round(full, 2)}
    return out


def _arith(t: dict[str, float]) -> str:
    return f"{t['completions']:,.1f} / {t['permits']:,.1f} = {t['ratio']:.4f}"


def register_citation(pid: str, table: dict) -> str:
    col = REGISTER[pid]
    full = table[("completions_permit_areas", col, 1995, 2024)]
    recent = table[("completions_permit_areas", col, 2010, 2024)]
    allp = table[("completions_all_areas", col, 1995, 2024)]
    head = (f"{NRC_BASE}/{FILES['completions_permit_areas']} and {FILES['permits']}, sheet Annual, "
            f"United States column '{TYPES[col]}' (thousands): cumulative completions in permit-issuing "
            f"areas / cumulative units authorized, 1995-2024 {_arith(full)} (mid, high); 2010-2024 "
            f"{_arith(recent)} (low). All-area completions ({FILES['completions_all_areas']}) give "
            f"{allp['ratio']:.4f} for 1995-2024, the research value; they add homes built where no "
            "permit is needed, which never enter our permit baseline.")
    if pid == "completions_per_permit_2to4":
        u24 = table[("completions_all_areas", "u24", 1995, 2024)]
        head += (f" NRC does publish 2-4 unit completions, but the ratio ({_arith(u24)}) is not a "
                 "completion rate: the Survey of Construction reclassifies townhouses that permit "
                 f"offices filed as multifamily into one-unit structures ({RELATIONSHIPS_URL}), so the "
                 "all-structures ratio, which reclassification cannot move, is used.")
    return head + " Computed by hre validate --nrc (docs/evidence/completions_per_permit.md)."


def write_register(table: dict, path: Path, accessed: str) -> None:
    """Rewrite the three entries' values, levels, source and citation, keeping everything else."""
    text = path.read_text(encoding="utf-8")
    vals = register_values(table)
    for pid in REGISTER:
        start = text.index(f"  - id: {pid}\n")
        end = text.index("\n\n", start)
        block = text[start:end]
        v = vals[pid]
        for lv in ("low", "mid", "high"):
            block = re.sub(rf"\n    {lv}: [^\n]+", f"\n    {lv}: {v[lv]:.2f}", block, count=1)
        block = re.sub(r"\n    sources:\n(      [^\n]+\n)+", "\n    sources:\n" + _sources(pid, accessed), block,
                       count=1)
        cite = _wrap(register_citation(pid, table), 6)
        block = re.sub(r"(\n    citation: >-\n)(      [^\n]+\n)+", lambda m, c=cite: m.group(1) + c, block, count=1)
        block = re.sub(r"\n    levels: [^\n]+",
                       f'\n    levels: {{low: "{v["low"]:.2f}", mid: "{v["mid"]:.2f}", high: "{v["high"]:.2f}"}}',
                       block, count=1)
        text = text[:start] + block + text[end:]
    path.write_text(text, encoding="utf-8")


def _sources(pid: str, accessed: str) -> str:
    col = REGISTER[pid]
    lines = [
        "      - title: Census Bureau, New Residential Construction, units completed in permit-issuing areas",
        f"        url: {NRC_BASE}/{FILES['completions_permit_areas']}",
        f'        locator: "Sheet Annual, United States, {TYPES[col]}, 1995-2024"',
        f'        accessed: "{accessed}"',
        "      - title: Census Bureau, New Residential Construction, units authorized in permit-issuing places",
        f"        url: {NRC_BASE}/{FILES['permits']}",
        f'        locator: "Sheet Annual, United States, {TYPES[col]}, 1995-2024"',
        f'        accessed: "{accessed}"',
    ]
    if pid == "completions_per_permit_2to4":
        lines += ["      - title: Census Bureau, Data Relationships between Permits, Starts, and Completions",
                  f"        url: {RELATIONSHIPS_URL}",
                  '        locator: "p. 1, Changes after the issuance of permits: Reclassification"',
                  f'        accessed: "{accessed}"']
    return "\n".join(lines) + "\n"


def _wrap(text: str, indent: int, width: int = 96) -> str:
    return "\n".join(textwrap.wrap(text, width=width, initial_indent=" " * indent,
                                    subsequent_indent=" " * indent)) + "\n"


def render_markdown(table: dict, last_year: int, run_date: str) -> str:
    vals = register_values(table)
    L = [
        "# Completions per permit, by structure type (Census NRC)",
        "",
        (f"Generated by `hre validate --nrc` on {run_date} from the Census New Residential Construction "
         f"annual tables (series through {last_year}): `{FILES['permits']}` (units authorized in "
         f"permit-issuing places), `{FILES['completions_permit_areas']}` (units completed in "
         f"permit-issuing areas) and `{FILES['completions_all_areas']}` (units completed in all areas), "
         f"{NRC_BASE}/. Manifest: `data/manifests/nrc.json`. Code: "
         "`src/hre/validation/completions_per_permit.py`."),
        "",
        "Ratio = cumulative completions ÷ cumulative permits over the period (thousands of units).",
        "",
        "| Completions series | Structure | Period | Completions | Permits | Ratio |",
        "|---|---|---|---|---|---|",
    ]
    for s, sname in SERIES.items():
        for col, cname in TYPES.items():
            for a, b in PERIODS:
                t = table[(s, col, a, b)]
                if t is None:
                    L.append(f"| {sname} | {cname} | {a}-{b} | n/a | n/a | n/a |")
                else:
                    L.append(f"| {sname} | {cname} | {a}-{b} | {t['completions']:,.1f} | "
                             f"{t['permits']:,.1f} | {t['ratio']:.4f} |")
    L += [
        "",
        "## Register values (decision 70)",
        "",
        "| Register entry | NRC column | Low (2010-2024) | Mid and high (1995-2024) | Research (low / mid, all areas) |",
        "|---|---|---|---|---|",
    ]
    for pid, col in REGISTER.items():
        v, r = vals[pid], RESEARCH[pid]
        L.append(f"| `{pid}` | {TYPES[col]} | {v['low']:.2f} | {v['mid']:.2f} | {r[0]:.2f} / {r[1]:.2f} |")
    L += [
        "",
        "## Reading",
        "",
        ("- **Like for like.** The baseline counts permits in permit-issuing places, so the conversion "
         "uses completions in the same places. All-area completions add homes built where no permit is "
         "needed (about 2.5% of all homes, nearly all single-family, per Census), which is why the "
         "research session's one-unit ratio was above 1."),
        ("- **Two to four units.** Census publishes 2-4 unit completions, but they are not a completion "
         "rate: permit offices often file townhouses as multifamily, and the Survey of Construction "
         f"reclassifies them as one-unit structures ({RELATIONSHIPS_URL}, p. 1). The 2-4 entry therefore "
         "uses the all-structures ratio, which reclassification cannot move."),
        ("- **Five or more units.** About a fifth of apartment units permitted are never completed or are "
         "re-permitted; the two completion series agree because almost no apartments are built outside "
         "permit-issuing places."),
        ("- **Low end.** 2010-2024 includes the slow recovery, when more permits lapsed and apartment "
         "pipelines lengthened; the window's last years are still under construction, which also lowers "
         "it."),
        "",
    ]
    return "\n".join(L)
