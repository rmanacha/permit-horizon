"""Tables in the submission documents, generated from the files that decide them.

A generated block in a Markdown file sits between two markers:

    <!-- BEGIN generated:core-assumptions -->
    ...
    <!-- END generated:core-assumptions -->

``make docs`` (``uv run python -m hre.docs``) rewrites every block, and the two generated pages
(``docs/methods/register.md`` and the tables of ``docs/evidence/validation.md``);
``uv run python -m hre.docs --check`` and ``tests/test_docs.py`` fail when any of them differs
from what its source gives now. Sources: the assumption register
(``src/hre/assumptions/parameters.yaml``), the current-law files (``src/hre/current_law/{ST}.yaml``),
the validation ledger (``validation/ledger.yaml``) and the committed results bundle
(``web/public/results/``). No number inside a block is typed by hand; text outside the blocks is.
"""

from __future__ import annotations

import datetime as dt
import functools
import json
import re
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from hre.assumptions.loader import load_entries, register_markdown
from hre.current_law.schema import coverage_value, gate_open
from hre.validation import ledger

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "web" / "public" / "results"
LAW_DIR = REPO / "src" / "hre" / "current_law"
REGISTER_MD = REPO / "docs" / "methods" / "register.md"
VALIDATION_MD = REPO / "docs" / "evidence" / "validation.md"
SBOM_PATH = REPO / "docs" / "sbom" / "sbom.spdx.json"
UV_LOCK = REPO / "uv.lock"
NPM_LOCK = REPO / "web" / "package-lock.json"
DOCUMENTS = ("docs/MODEL_AND_ASSUMPTIONS.md", "docs/POLICY_SCENARIO_COMPARISON.md", "docs/DISCLOSURES.md")

# Licences the project accepts for any dependency: permissive only, no copyleft (MPL, LGPL, GPL,
# AGPL, EUPL, EPL, CDDL). Python-2.0 is the PSF-style licence; CC0-1.0 a public-domain dedication.
PERMISSIVE = frozenset({"MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "Apache-2.0", "Zlib",
                        "CC0-1.0", "Python-2.0", "PSF-2.0", "Unlicense", "BlueOak-1.0.0"})
# The SBOM asserts no licence for GitHub Actions; each one's repository states MIT (GitHub API,
# /repos/{owner}/{repo}/license, read 2026-11-04). They run only on GitHub's CI machines.
ACTION_LICENCES = {"actions/checkout": "MIT", "actions/setup-python": "MIT", "actions/setup-node": "MIT",
                   "actions/upload-pages-artifact": "MIT", "actions/deploy-pages": "MIT",
                   "astral-sh/setup-uv": "MIT"}
PROJECT_NAMES = {"permit-horizon", "com.github.rmanacha/permit-horizon", "rmanacha/permit-horizon"}

SHOWCASE = ("UT", "NH", "AZ")
REFORMS = ("adu", "missing_middle", "tod", "parking", "fees")
REFORM_NAMES = {"adu": "ADUs", "missing_middle": "Missing middle", "tod": "Transit-oriented density",
                "parking": "No parking minimums", "fees": "Fees cut in half"}
SHORT_NAMES = {"adu": "ADUs", "missing_middle": "missing middle", "tod": "transit density",
               "parking": "parking", "fees": "fees"}
USED_BY = {"all": "all", "baseline": "baseline", "adu": "ADU", "missing_middle": "missing middle",
           "tod": "transit", "parking": "parking", "fees": "fees"}
UNITS = {"permits": "permits", "net_permits": "net permits (after demolitions)",
         "completed_homes": "completed homes", "stock_change": "homes added to the stock",
         "cost_response_proxy": "cost-response permits"}
FEATURE_NAMES = {
    "adu_per_lot": "one ADU per lot", "adu_forms": "detached and attached", "adu_size": "600 sq ft",
    "adu_parking": "no added parking", "mm_parcels": "single-family lots", "mm_units": "two to six homes",
    "mm_height": "three stories", "mm_envelope": "setbacks fit", "tod_density": "more density",
    "tod_geography": "stops defined", "tod_parking": "less parking", "parking_minimum": "minimums cut",
    "parking_provision": "provision", "fees_level": "$50,000 level", "fees_cut": "fees cut 50%",
    "fees_categories": "all categories"}
STATUS_WORDS = {"supported_with_limits": "yes", "differs": "no", "not_yet_effective": "after 2030",
                "unknown": "unknown"}
CONFIDENCE_ORDER = ("low", "moderate", "high", "set_by_rules")

BEGIN = "<!-- BEGIN generated:{name} -->"
END = "<!-- END generated:{name} -->"
BLOCK = re.compile(r"<!-- BEGIN generated:(?P<name>[A-Za-z0-9-]+) -->\n(?P<body>.*?)"
                   r"<!-- END generated:(?P=name) -->", re.DOTALL)


# ------------------------------------------------------------------ sources


@functools.cache
def bundle(state: str) -> dict[str, Any]:
    return json.loads((BUNDLE / f"{state}.json").read_text(encoding="utf-8"))


@functools.cache
def state_names() -> dict[str, str]:
    index = json.loads((BUNDLE / "index.json").read_text(encoding="utf-8"))
    return {r["state"]: r["name"] for r in index["states"]}


@functools.cache
def law_files() -> dict[str, dict[str, Any]]:
    out = {}
    for p in sorted(LAW_DIR.glob("[A-Z][A-Z].yaml")):
        out[p.stem] = yaml.safe_load(p.read_text(encoding="utf-8"))
    return out


def clear_caches() -> None:
    for f in (bundle, state_names, law_files):
        f.cache_clear()


# ------------------------------------------------------------------ formatting


def _cell(s: Any) -> str:
    return " ".join(str(s).split()).replace("|", "/")


def _n(x: float) -> str:
    return f"{x:,.0f}"


def _range(e: dict[str, float]) -> str:
    return f"{_n(e['mid'])} ({_n(e['low'])} to {_n(e['high'])})"


def _review(h: dict[str, Any] | None) -> str:
    if not h or h.get("status") != "reviewed":
        return "pending"
    return f"reviewed by {h.get('by')} on {h.get('date')}"


# ------------------------------------------------------------------ Model and Assumptions blocks


def core_assumptions() -> str:
    """Every register entry: plain label, the three values, grade, why, and where it comes from."""
    lines = ["| Assumption (used by; grade, confidence) | Low / middle / high | Why this value | Sources |",
             "|---|---|---|---|"]
    for e in load_entries().values():
        lv = e["levels"]
        values = lv["mid"] + " (fixed)" if lv["low"] == lv["mid"] == lv["high"] else \
            f"{lv['low']} / {lv['mid']} / {lv['high']}"
        used = ", ".join(USED_BY.get(s, s) for s in e["scenarios"])
        src = "; ".join(f"[{_cell(s['title'])}]({s['url']})" for s in e["sources"])
        lines.append(f"| **{_cell(e['label'])}** ({used}; {e['grade']}, {e['confidence'].replace('_', ' ')}) | "
                     f"{_cell(values)} | {_cell(e['rationale'])} | {src} |")
    n = len(lines) - 2
    lines += ["", (f"{n} entries. The page, table or paragraph each value comes from, and the arithmetic word for word, "
                   "are in the full register ([docs/methods/register.md](methods/register.md)) and on the website's "
                   "Assumptions and data page.")]
    return "\n".join(lines)


def formulas() -> str:
    """One line per estimate, as the website shows it (the bundle's formula strings)."""
    r = bundle("NH")
    p = load_entries()["baseline_band_ratio"]
    lines = ["| Estimate | Unit of the evidence | Formula |", "|---|---|---|",
             (f"| Baseline | permits | {_cell(r['baseline']['method'])} Range: that total x {p['low']:g} "
              f"(low) to x {p['high']:g} (high). |")]
    for sc in REFORMS:
        s = r["scenarios"][sc]
        lines.append(f"| {_cell(s['label'])} | {UNITS[s['benchmark']['outcome']]} | {_cell(s['formula'])} |")
    return "\n".join(lines)


def _features_in_law(s: dict[str, Any]) -> str:
    feats = s.get("features") or []
    yes = [f for f in feats if f["status"] == "supported_with_limits"]
    dates = sorted({str(f["in_effect_from"]) for f in yes if f.get("in_effect_from")})
    text = f"{len(yes)} of {len(feats)}"
    return text + (f" (from {', '.join(dates)})" if dates else "")


def current_law_adu() -> str:
    """The ADU entry for all 51 jurisdictions: strength, its parts and the statute."""
    names = state_names()
    with_law, none = [], []
    for st, doc in law_files().items():
        s = (doc.get("scenarios") or {}).get("adu")
        if s is None or str(s["record"]["law"]).startswith("No statewide"):
            none.append(st)
            continue
        with_law.append((-float(s["current_strength"]), st, s))
    lines = [("| State | Strength (newly affected) | Benchmark features in law (core feature) | "
              "Detached homes the law reaches | Statute |"), "|---|---|---|---|---|"]
    above = enabling = 0
    for neg, st, s in sorted(with_law):
        strength = -neg
        gate = gate_open("adu", s["features"])
        above += strength > 0
        enabling += strength == 0
        lines.append(f"| {names.get(st, st)} | {strength:.2f} ({1 - strength:.0%}) | {_features_in_law(s)} "
                     f"(core: {'yes' if gate else 'no'}) | {coverage_value(s):.0%} | {_cell(s['record']['law'])} |")
    lines += ["", (f"{above} jurisdictions have part of the ADU benchmark in state law; {enabling} have an ADU statute "
              f"whose core feature (towns must allow one ADU per lot) is not required, so their strength is 0; "
              f"{len(none)} have no statewide ADU requirement (strength 0, the whole benchmark counts as new): "
              f"{', '.join(names.get(s, s) for s in none)}.")]
    return "\n".join(lines)


def current_law_showcase() -> str:
    """All five reforms for Utah, New Hampshire and Arizona, feature by feature."""
    names = state_names()
    out = []
    for st in SHOWCASE:
        doc = law_files()[st]
        out += [f"**{names[st]}**", "",
                "| Reform | Statute | Benchmark features in law | Coverage | Strength | Newly affected | Human review |",
                "|---|---|---|---|---|---|---|"]
        for sc in REFORMS:
            s = doc["scenarios"][sc]
            feats = "; ".join(
                f"{FEATURE_NAMES.get(f['id'], f['id'])}: {STATUS_WORDS[f['status']]}"
                + (f" from {f['in_effect_from']}" if f.get("in_effect_from") and f["status"] == "supported_with_limits"
                   else "")
                for f in s["features"])
            strength = float(s["current_strength"])
            how = " (quantified)" if s.get("strength_method") == "quantified" else ""
            out.append(f"| {REFORM_NAMES[sc]} | {_cell(s['record']['law'])} | {feats} | {coverage_value(s):.0%} | "
                       f"{strength:.2f}{how} | {1 - strength:.0%} | {_review(s.get('human_review'))} |")
        out.append("")
    return "\n".join(out).rstrip()


def validation_table() -> str:
    return "\n".join(ledger.summary_table(ledger.load()))


def sensitivity() -> str:
    """The two assumptions that move each showcase result most, and every assumption at once."""
    names = state_names()
    lines = [("| State | Reform | More permits than current law: middle (low to high set) | Largest single swing | "
              "Second largest | Every assumption at its worst to its best end |"), "|---|---|---|---|---|---|"]

    def bar(t: list[dict[str, Any]], i: int) -> str:
        if len(t) <= i:
            return "none"
        b = t[i]
        return (f"{_cell(b['label'])}: {_cell(b['low_text'])} to {_cell(b['high_text'])} gives "
                f"{_n(b['at_low'])} to {_n(b['at_high'])}")

    for st in SHOWCASE:
        for sc in REFORMS:
            s = bundle(st)["scenarios"][sc]
            j = s["joint"]
            lines.append(f"| {names[st]} | {REFORM_NAMES[sc]} | {_range(s['increment']['estimate'])} | "
                         f"{bar(s['tornado'], 0)} | {bar(s['tornado'], 1)} | "
                         f"{_n(j['unfavorable']['value'])} to {_n(j['favorable']['value'])} |")
    return "\n".join(lines)


# ------------------------------------------------------------------ Policy Scenario Comparison blocks


def _increments(st: str) -> dict[str, dict[str, Any]]:
    out = {}
    for sc in REFORMS:
        inc = bundle(st)["scenarios"][sc]["increment"]
        if inc["outcome"] != "permits":
            raise ValueError(f"{st} {sc}: an increment that is not in permits cannot be ranked")
        out[sc] = inc
    return out


def _confidence(st: str, sc: str) -> str:
    """The weakest register confidence among the assumptions that set the scenario's range."""
    entries = load_entries()
    levels = [entries[i]["confidence"] for i in bundle(st)["scenarios"][sc]["band_ids"]]
    return min(levels, key=CONFIDENCE_ORDER.index).replace("_", " ")


def ranking(st: str) -> str:
    r = bundle(st)
    inc = _increments(st)
    base = r["baseline"]["state"]
    order = sorted(REFORMS, key=lambda sc: (-inc[sc]["estimate"]["mid"], REFORMS.index(sc)))
    lines = [f"Baseline, no change: {_range(base)} permits over 2026-2030.", "",
             ("| Rank | Reform | More permits than current law, 2026-2030: middle (low to high) | Middle as a share "
              "of the baseline | Already in state law |"), "|---|---|---|---|---|"]
    for k, sc in enumerate(order, 1):
        e = inc[sc]["estimate"]
        s = float(inc[sc]["current_law"]["current_strength"])
        law = "none" if s == 0 else f"{s:.0%}, so {1 - s:.0%} is new"
        lines.append(f"| {k} | {REFORM_NAMES[sc]} | {_range(e)} | {e['mid'] / base['mid']:.1%} | {law} |")
    c = r["combined"]["increment"]["estimate"]
    conf = sorted({_confidence(st, sc) for sc in REFORMS}, key=CONFIDENCE_ORDER.index)
    lines += ["", (f"If all five passed together (an illustration with overlaps removed, not ranked): {_range(c)} "
                   f"permits. Register confidence in the evidence behind these ranges: {', '.join(conf)}.")]
    return "\n".join(lines)


def benchmarks() -> str:
    names = state_names()
    lines = ["| Reform | Unit of the evidence (rows are not comparable) | " + " | ".join(names[s] for s in SHOWCASE) + " |",
             "|---|---|" + "---|" * len(SHOWCASE)]
    for sc in REFORMS:
        unit = UNITS[bundle(SHOWCASE[0])["scenarios"][sc]["benchmark"]["outcome"]]
        cells = []
        for st in SHOWCASE:
            b = bundle(st)["scenarios"][sc]["benchmark"]
            if UNITS[b["outcome"]] != unit:
                raise ValueError(f"{sc}: benchmark units differ between states")
            cells.append(_range(b))
        lines.append(f"| {REFORM_NAMES[sc]} | {unit} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def top_two(values: dict[str, float]) -> tuple[str, str]:
    """The two reforms with the largest values (ties keep the reform order)."""
    order = sorted(values, key=lambda sc: (-values[sc], REFORMS.index(sc)))
    return order[0], order[1]


def _top_text(pair: tuple[str, str]) -> str:
    return f"{SHORT_NAMES[pair[0]]}, then {SHORT_NAMES[pair[1]]}"


def flips() -> str:
    """Which changes reorder the top two reforms in each showcase state, one change at a time."""
    names = state_names()
    mids, incs, bars = {}, {}, {}
    for st in SHOWCASE:
        incs[st] = _increments(st)
        mids[st] = {sc: incs[st][sc]["estimate"]["mid"] for sc in REFORMS}
        for sc in REFORMS:
            for b in bundle(st)["scenarios"][sc]["tornado"]:
                bars.setdefault(b["id"], {}).setdefault(st, {})[sc] = b

    def cells(values: dict[str, dict[str, float]]) -> list[str]:
        return [_top_text(top_two(values[st])) if top_two(values[st]) != top_two(mids[st]) else "same"
                for st in SHOWCASE]

    head = "| What changes (everything else at the middle) | " + " | ".join(names[s] for s in SHOWCASE) + " |"
    lines = [head, "|---|" + "---|" * len(SHOWCASE),
             "| Nothing: the middle assumptions | " + " | ".join(_top_text(top_two(mids[s])) for s in SHOWCASE) + " |"]
    for lv, label in (("low", "Every range at its low set"), ("high", "Every range at its high set")):
        lines.append(f"| {label} | " + " | ".join(cells({st: {sc: incs[st][sc]["estimate"][lv] for sc in REFORMS}
                                                          for st in SHOWCASE})) + " |")
    rows = []
    for pid, by_st in bars.items():
        first = next(iter(next(iter(by_st.values())).values()))
        swing = max(b["swing"] for per in by_st.values() for b in per.values())
        for end in ("low", "high"):
            values = {st: {sc: (by_st.get(st, {}).get(sc, {}).get(f"at_{end}", mids[st][sc])) for sc in REFORMS}
                      for st in SHOWCASE}
            row = cells(values)
            if any(c != "same" for c in row):
                rows.append((-swing, pid, end, f"| {_cell(first['label'])}: {_cell(first[f'{end}_text'])} | "
                                               + " | ".join(row) + " |"))
    lines += [r for *_, r in sorted(rows)]
    return "\n".join(lines)


# ------------------------------------------------------------------ Disclosures: dependencies from the SBOM


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def sbom_packages(path: Path = SBOM_PATH) -> list[dict[str, str]]:
    """Every package in the stored SBOM: ecosystem, name, version, licence as GitHub concluded it."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for p in doc["packages"]:
        purl = next((r["referenceLocator"] for r in p.get("externalRefs") or []
                     if r.get("referenceType") == "purl"), "")
        eco = purl.split("/", 1)[0].removeprefix("pkg:") if purl else "github"
        lic = p.get("licenseConcluded") or p.get("licenseDeclared") or "NOASSERTION"
        out.append({"ecosystem": eco, "name": p["name"], "version": str(p.get("versionInfo", "")), "licence": lic})
    return out


def licence_tokens(expr: str) -> set[str]:
    """The licence ids in an SPDX expression, without the AND, OR and WITH operators."""
    return set(re.findall(r"[A-Za-z0-9.+-]+", expr)) - {"AND", "OR", "WITH"}


def licence_for(pkg: dict[str, str]) -> tuple[str, str]:
    """(licence shown, note): the SBOM's licence, or the stated one where the SBOM asserts none."""
    if pkg["name"] in PROJECT_NAMES:
        return "Apache-2.0", "this project"
    if pkg["ecosystem"] == "githubactions":
        return ACTION_LICENCES.get(pkg["name"], "NOASSERTION"), "licence from the action's repository"
    return pkg["licence"], ""


def licence_problems(path: Path = SBOM_PATH) -> list[str]:
    bad = []
    for pkg in sbom_packages(path):
        lic, _ = licence_for(pkg)
        if not licence_tokens(lic) <= PERMISSIVE:
            bad.append(f"{pkg['ecosystem']}:{pkg['name']} {pkg['version']}: {lic}")
    return bad


def uv_packages() -> dict[str, tuple[str, str]]:
    """uv.lock: normalized name -> (version, role) where role is runtime, an extra, or dev."""
    lock = tomllib.loads(UV_LOCK.read_text(encoding="utf-8"))
    pkgs = {_norm(p["name"]): p for p in lock["package"]}
    root = next(p for p in lock["package"] if p["name"] == "permit-horizon")

    def closure(names: list[str], seen: set[str]) -> set[str]:
        todo, got = [_norm(n) for n in names], set()
        while todo:
            n = todo.pop()
            if n in got or n in seen:
                continue
            got.add(n)
            todo += [_norm(d["name"]) for d in pkgs[n].get("dependencies", [])]
        return got

    roles: dict[str, str] = {"permit-horizon": "this project"}
    runtime = closure([d["name"] for d in root.get("dependencies", [])], set())
    roles |= dict.fromkeys(runtime, "runtime (engine and command line)")
    taken = set(roles)
    for extra, deps in sorted(root.get("optional-dependencies", {}).items()):
        got = closure([d["name"] for d in deps], taken)
        roles |= dict.fromkeys(got, f"optional extra `{extra}`")
        taken |= got
    for group, deps in sorted(root.get("dev-dependencies", {}).items()):
        got = closure([d["name"] for d in deps], taken)
        roles |= dict.fromkeys(got, "development only (tests, lint)")
        taken |= got
    return {n: (str(pkgs[n]["version"]), roles.get(n, "not reached")) for n in pkgs}


def npm_packages() -> dict[tuple[str, str], str]:
    """web/package-lock.json: (name, version) -> role (served to the browser, or build only)."""
    lock = json.loads(NPM_LOCK.read_text(encoding="utf-8"))
    out = {}
    for key, p in lock["packages"].items():
        if not key:
            continue
        name = key.split("node_modules/")[-1]
        out[(name, str(p["version"]))] = "website build only" if p.get("dev") else "website, served to the browser"
    return out


def dependencies() -> str:
    """The dependency table for the disclosures: every SBOM package with its licence and where it runs."""
    pkgs = sbom_packages()
    py = uv_packages()
    npm = npm_packages()
    rows: list[tuple[int, str, str, str, str]] = []
    groups: dict[str, list[dict[str, str]]] = {}
    for pkg in pkgs:
        lic, note = licence_for(pkg)
        if pkg["ecosystem"] == "pypi":
            role = py.get(_norm(pkg["name"]), ("", "not in uv.lock"))[1]
            order = 0
        elif pkg["ecosystem"] == "npm":
            role = npm.get((pkg["name"], pkg["version"]), "not in package-lock.json")
            order = 1 if "served" in role else 2
            scope = pkg["name"].split("/")[0]
            platform_build = scope == "@esbuild" or (
                scope.startswith("@") and pkg["name"].split("/")[1].startswith(("rollup-", "typescript-", "lzma-")))
            if platform_build:
                groups.setdefault(scope, []).append(pkg)
                continue
        elif pkg["ecosystem"] == "githubactions":
            role, order = "CI only (GitHub's machines); not shipped", 3
        else:
            role, order = "this repository", 4
        shown = lic + (f" ({note})" if note and note != "this project" else "")
        rows.append((order, pkg["name"].lower(), f"| {pkg['name']} | {pkg['version']} | {shown} | {role} |", lic, role))
    for scope, members in sorted(groups.items()):
        lics = sorted({m["licence"] for m in members})
        vers = sorted({m["version"] for m in members})
        builds = f"{len(members)} platform build" + ("s; one is installed per machine" if len(members) > 1 else "")
        row = (f"| {scope}/* ({builds}) | "
               f"{', '.join(vers)} | {', '.join(lics)} | website build only |")
        rows.append((2, scope, row, ", ".join(lics), "build"))
    lines = ["| Package | Version | Licence (from the SBOM) | Where it is used |", "|---|---|---|---|"]
    lines += [r[2] for r in sorted(rows)]
    eco: dict[str, int] = {}
    for pkg in pkgs:
        eco[pkg["ecosystem"]] = eco.get(pkg["ecosystem"], 0) + 1
    counts = ", ".join(f"{v} {k}" for k, v in sorted(eco.items()))
    lics: dict[str, int] = {}
    for pkg in pkgs:
        lic, _ = licence_for(pkg)
        lics[lic] = lics.get(lic, 0) + 1
    lic_text = "; ".join(f"{k} {v}" for k, v in sorted(lics.items(), key=lambda kv: (-kv[1], kv[0])))
    problems = licence_problems()
    lines += ["", (f"{len(pkgs)} packages in docs/sbom/sbom.spdx.json ({counts}). Licences: {lic_text}. "
                   + ("Every licence is permissive." if not problems else f"Not permissive: {'; '.join(problems)}."))]
    return "\n".join(lines)


BLOCKS: dict[str, Callable[[], str]] = {
    "core-assumptions": core_assumptions,
    "formulas": formulas,
    "current-law-adu": current_law_adu,
    "current-law-showcase": current_law_showcase,
    "validation-ledger": validation_table,
    "sensitivity": sensitivity,
    "benchmarks": benchmarks,
    **{f"ranking-{st}": functools.partial(ranking, st) for st in SHOWCASE},
    "flips": flips,
    "dependencies": dependencies,
}


# ------------------------------------------------------------------ render, check, write


def render_text(text: str) -> str:
    def fill(m: re.Match[str]) -> str:
        name = m.group("name")
        if name not in BLOCKS:
            raise KeyError(f"unknown generated block {name!r}")
        return f"{BEGIN.format(name=name)}\n{BLOCKS[name]().rstrip()}\n{END.format(name=name)}"

    return BLOCK.sub(fill, text)


def block_names(text: str) -> list[str]:
    return [m.group("name") for m in BLOCK.finditer(text)]


def _validation_now(current: str) -> str:
    keep = current.split(ledger.MARKER, 1)[1] if ledger.MARKER in current else ""
    m = re.search(r"Generated (\S+) by", current)
    return ledger.render_markdown(ledger.load(), m.group(1) if m else dt.date.today().isoformat(), keep)


def problems() -> list[str]:
    """Every generated table that differs from its source, as one line each."""
    out = []
    for rel in DOCUMENTS:
        p = REPO / rel
        text = p.read_text(encoding="utf-8")
        fresh = render_text(text)
        if fresh != text:
            now = {m.group("name"): m.group(0) for m in BLOCK.finditer(fresh)}
            stale = [m.group("name") for m in BLOCK.finditer(text) if m.group(0) != now.get(m.group("name"))]
            out.append(f"{rel}: generated blocks out of date: {', '.join(stale)} (run 'make docs')")
    if REGISTER_MD.read_text(encoding="utf-8") != register_markdown():
        out.append("docs/methods/register.md differs from parameters.yaml (run 'make docs')")
    current = VALIDATION_MD.read_text(encoding="utf-8")
    if _validation_now(current) != current:
        out.append("docs/evidence/validation.md differs from validation/ledger.yaml (run 'make docs')")
    return out


def write_all() -> list[str]:
    changed = []
    for rel in DOCUMENTS:
        p = REPO / rel
        text = p.read_text(encoding="utf-8")
        fresh = render_text(text)
        if fresh != text:
            p.write_text(fresh, encoding="utf-8")
            changed.append(rel)
    reg = register_markdown()
    if REGISTER_MD.read_text(encoding="utf-8") != reg:
        REGISTER_MD.write_text(reg, encoding="utf-8")
        changed.append(str(REGISTER_MD.relative_to(REPO)))
    current = VALIDATION_MD.read_text(encoding="utf-8")
    if _validation_now(current) != current:
        ledger.write_markdown(VALIDATION_MD, dt.date.today().isoformat())
        changed.append(str(VALIDATION_MD.relative_to(REPO)))
    return changed


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--check" in argv:
        found = problems()
        for line in found:
            print(line)
        print("generated docs: " + ("out of date" if found else "all in step with their sources"))
        return 1 if found else 0
    changed = write_all()
    print("rewrote " + ", ".join(changed) if changed else "generated docs already up to date")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
