"""Coverage: the share of a state's detached single-family homes inside the places a law binds.

A statewide law that binds only some jurisdictions (Arizona's ADU law: cities and towns of more
than 75,000 people plus the unincorporated parts of counties) already delivers its features in
those places only. The current-law strength multiplies the feature share by this coverage share
(docs/methods/current_law.md). Homes are ACS 2020-2024 5-year B25024 detached single-family homes;
populations for thresholds are ACS B01003; places are Census places (summary level 160), split
by county (155); a name ending in " CDP" is a census-designated place, which is unincorporated.

A rule, from a state file's ``coverage.rule`` (every key optional):

    places: all | none              incorporated places covered regardless of size (default all)
    above_population: 75000         only incorporated places with more people than this
    min_population: 10000           only incorporated places with at least this many people
    unincorporated: all | cdp | none   areas outside incorporated places (county-governed); cdp
                                    counts only census-designated places, a proxy for unincorporated
                                    urban areas (growth boundaries); default none
    cdp_min_population: 1000        with unincorporated: cdp, only CDPs this large
    counties: [013, 019]            restrict everything to these counties (3-digit codes)
    county_min_population: 15000    unincorporated areas covered only in counties this large
    exclude_subdivisions: [names]   towns (county subdivisions) that opted out, subtracted
    exclude_places: [names]         incorporated places the law does not reach ("Boston city")
    county_in_effect_from: {fips: YYYY-MM-DD}   counties the law reaches only from that date; their
                                    covered homes count the share of 2026-2030 it is in force
    exclude_tribal: true            subtract homes in American Indian areas (summary level 260)
    near_downtown_miles: 1          upper bound for a rule that reaches only the area around
                                    each covered place's downtown (see ``_near_downtown``)

    covered = homes in covered places + covered homes outside incorporated places
              - homes in tribal areas (if excluded) - homes in excluded towns; share = covered / total

Reads only cached files; ``fetch_place_gazetteer`` downloads the one extra file the downtown
bound needs. Nothing here runs inside ``hre run``: the share is computed once, written into the
state file with its arithmetic, and ``hre validate --law-coverage`` recomputes it.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from hre.current_law.schema import horizon_share
from hre.data.cache import fetch, raw_dir
from hre.data.fetch_acs import PREFIX_COUNTY, PREFIX_PLACE, load_geo_names, read_table, table_path
from hre.data.fetch_gazetteer import GAZ_YEAR, LICENSE, NOTES, _read_text

PREFIX_STATE = "0400000US"
PREFIX_PLACE_IN_COUNTY = "1550000US"
PREFIX_STATE_TRIBAL = "2600000US"   # "Arizona (part); Gila River Indian Reservation, AZ"
PREFIX_SUBDIVISION = "0600000US"     # county subdivisions: New England towns
PLACE_GAZ_URL = ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
                 f"{GAZ_YEAR}_Gazetteer/{GAZ_YEAR}_Gaz_place_national.zip")


def place_gazetteer_path(data_dir: Path | None = None) -> Path:
    return (data_dir or raw_dir()) / "gazetteer" / f"{GAZ_YEAR}_Gaz_place_national.zip"


def fetch_place_gazetteer(data_dir: Path | None = None) -> Path:
    return fetch(PLACE_GAZ_URL, place_gazetteer_path(data_dir), source="gazetteer", license=LICENSE,
                 vintage=GAZ_YEAR, notes=NOTES)


def _detached(prefix: str, data_dir: Path | None) -> dict[str, int]:
    """GEO_ID -> B25024_E002 (detached single-family homes) for one summary-level prefix."""
    rows = read_table("b25024", (prefix,), data_dir)
    return {g: (v[1] or 0) for g, v in rows.items()}


def _population(prefix: str, data_dir: Path | None) -> dict[str, int]:
    rows = read_table("b01003", (prefix,), data_dir)
    return {g: (v[0] or 0) for g, v in rows.items()}


def _place_land_sqmi(state_fips: str, data_dir: Path | None) -> dict[str, float]:
    text = _read_text(place_gazetteer_path(data_dir))
    out: dict[str, float] = {}
    header: list[str] = []
    for i, line in enumerate(text.splitlines()):
        parts = [p.strip() for p in line.split("|")]
        if i == 0:
            header = parts
            continue
        row = dict(zip(header, parts, strict=False))
        if row.get("GEOID", "").startswith(state_fips):
            out[row["GEOID"]] = float(row["ALAND_SQMI"])
    return out


def places(state_fips: str, data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Every Census place in the state: geoid, name, incorporated, population, detached homes."""
    names = load_geo_names(PREFIX_PLACE, state_fips, data_dir)
    homes = _detached(PREFIX_PLACE + state_fips, data_dir)
    pop = _population(PREFIX_PLACE + state_fips, data_dir) if table_path("b01003", data_dir).exists() else {}
    out = []
    for g, name in sorted(names.items()):
        full = PREFIX_PLACE + g
        out.append({"geoid": g, "name": name.rsplit(",", 1)[0],
                    "incorporated": not name.rsplit(",", 1)[0].endswith(" CDP"),
                    "population": pop.get(full), "detached": homes.get(full, 0)})
    return out


def _near_downtown(p: dict[str, Any], land: dict[str, float], miles: float) -> float:
    """Upper bound on a place's detached homes within ``miles`` of its downtown.

    The covered area is taken as a circle of radius ``miles`` + 1 around a downtown point (a
    downtown up to one mile across, plus the reach the law sets), holding the place's average
    density of detached homes. Downtowns hold fewer detached homes per square mile than the
    rest of a city, so the true count is lower.
    """
    area = land.get(p["geoid"])
    if not area:
        return float(p["detached"])
    circle = math.pi * (miles + 1.0) ** 2
    return p["detached"] * min(1.0, circle / area)


def _parts(state_fips: str, data_dir: Path | None) -> list[tuple[str, str, int]]:
    """(place geoid, county code, detached homes) for every place-in-county part (summary level 155)."""
    rows = _detached(PREFIX_PLACE_IN_COUNTY + state_fips, data_dir)
    out = []
    for g, v in rows.items():
        code = g[len(PREFIX_PLACE_IN_COUNTY):]          # SS PPPPP CCC
        out.append((code[:7], code[7:10], v))
    return out


def _subdivisions(state_fips: str, data_dir: Path | None) -> dict[str, tuple[str, int]]:
    """County subdivision (town) geoid -> (short name, detached homes); New England towns live here."""
    names = load_geo_names(PREFIX_SUBDIVISION, state_fips, data_dir)
    homes = _detached(PREFIX_SUBDIVISION + state_fips, data_dir)
    return {g: (n.split(",")[0], homes.get(PREFIX_SUBDIVISION + g, 0)) for g, n in names.items()}


def coverage_share(state_fips: str, rule: dict[str, Any], data_dir: Path | None = None) -> dict[str, Any]:
    """Apply ``rule`` (module docstring) to the state's cached ACS counts, county by county."""
    state_total = _detached(PREFIX_STATE + state_fips, data_dir).get(PREFIX_STATE + state_fips, 0)
    if not state_total:
        raise FileNotFoundError(f"no ACS B25024 row for state {state_fips}; run hre fetch first")
    ps = {p["geoid"]: p for p in places(state_fips, data_dir)}
    inc = [p for p in ps.values() if p["incorporated"]]
    needs_pop = any(k in rule for k in ("above_population", "min_population", "cdp_min_population",
                                        "county_min_population"))
    if needs_pop and any(p["population"] is None for p in ps.values()):
        raise FileNotFoundError("population thresholds need ACS B01003; run hre validate --law-coverage --fetch")
    counties = {k[-3:]: v for k, v in county_detached(state_fips, data_dir).items()}   # 3-digit codes
    wanted = {str(c)[-3:] for c in rule["counties"]} if "counties" in rule else set(counties)
    if rule.get("exclude_tribal") and "counties" in rule:
        raise ValueError("exclude_tribal works statewide only (tribal areas are not split by county here)")
    county_pop = {}
    if "county_min_population" in rule:
        county_pop = {g[len(PREFIX_COUNTY) + 2:]: v for g, v in
                      _population(PREFIX_COUNTY + state_fips, data_dir).items()}

    excluded_names = {n.strip().casefold() for n in rule.get("exclude_places", [])}
    unknown = excluded_names - {p["name"].casefold() for p in inc}
    if unknown:
        raise ValueError(f"places not found: {sorted(unknown)}")

    def place_covered(p: dict[str, Any]) -> bool:
        if rule.get("places", "all") == "none" or p["name"].casefold() in excluded_names:
            return False
        if "above_population" in rule and not p["population"] > rule["above_population"]:
            return False
        return not ("min_population" in rule and not p["population"] >= rule["min_population"])

    def cdp_covered(p: dict[str, Any]) -> bool:
        return not p["incorporated"] and p["population"] is not None \
            and p["population"] >= rule.get("cdp_min_population", 0)

    covered_ids = {p["geoid"] for p in inc if place_covered(p)}
    near = "near_downtown_miles" in rule
    land = _place_land_sqmi(state_fips, data_dir) if near else {}
    place_homes = 0.0
    outside_covered = 0
    outside_total = 0
    late = {str(k)[-3:]: horizon_share(v) for k, v in (rule.get("county_in_effect_from") or {}).items()}
    for c in sorted(counties):
        parts = [(g, v) for g, cc, v in _parts(state_fips, data_dir) if cc == c]
        inc_parts = sum(v for g, v in parts if g in ps and ps[g]["incorporated"])
        outside = counties[c] - inc_parts
        outside_total += outside
        if c not in wanted:
            continue
        w = late.get(c, 1.0)              # a county the law reaches only later counts its share of 2026-2030
        if not near:
            place_homes += w * sum(v for g, v in parts if g in covered_ids)
        unin = rule.get("unincorporated", "none")
        if "county_min_population" in rule and county_pop.get(c, 0) < rule["county_min_population"]:
            unin = "none"
        if unin == "all":
            outside_covered += w * outside
        elif unin == "cdp":
            outside_covered += w * sum(v for g, v in parts if g in ps and cdp_covered(ps[g]))
    if near:
        place_homes = sum(_near_downtown(ps[g], land, float(rule["near_downtown_miles"])) for g in covered_ids)
    tribal = 0
    if rule.get("exclude_tribal"):
        tribal = sum(v for g, v in _detached(PREFIX_STATE_TRIBAL, data_dir).items() if g.endswith(state_fips))
        outside_covered = max(0, outside_covered - tribal)
    excluded_towns: list[dict[str, Any]] = []
    if rule.get("exclude_subdivisions"):
        names = {n.strip().casefold() for n in rule["exclude_subdivisions"]}
        subs = _subdivisions(state_fips, data_dir)
        excluded_towns = [{"name": n, "detached": v} for n, v in subs.values()
                          if n.casefold().removesuffix(" town").removesuffix(" city") in names
                          or n.casefold() in names]
        missing = names - {t["name"].casefold().removesuffix(" town").removesuffix(" city") for t in excluded_towns} \
            - {t["name"].casefold() for t in excluded_towns}
        if missing:
            raise ValueError(f"county subdivisions not found: {sorted(missing)}")
    covered = place_homes + outside_covered - sum(t["detached"] for t in excluded_towns)
    share = covered / state_total
    uncovered = sorted((p for p in inc if p["geoid"] not in covered_ids), key=lambda p: -p["detached"])
    return {
        "share": round(share, 4),
        "state_detached": state_total,
        "covered_places": len(covered_ids),
        "covered_place_homes": round(place_homes),
        "incorporated_places": len(inc),
        "homes_outside_incorporated": outside_total,
        "tribal_homes_excluded": tribal,
        "covered_outside_homes": round(outside_covered),
        "excluded_subdivisions": excluded_towns,
        "largest_uncovered": [{"name": p["name"], "population": p["population"], "detached": p["detached"]}
                              for p in uncovered[:5]],
        "largest_covered": [{"name": ps[g]["name"], "population": ps[g]["population"], "detached": ps[g]["detached"]}
                            for g in sorted(covered_ids, key=lambda g: -ps[g]["detached"])[:5]],
        "rule": rule,
    }


def county_detached(state_fips: str, data_dir: Path | None = None) -> dict[str, int]:
    """County FIPS -> detached homes (for per-county checks in the evidence page)."""
    rows = _detached(PREFIX_COUNTY + state_fips, data_dir)
    return {g[len(PREFIX_COUNTY):]: v for g, v in rows.items()}


def sentence(r: dict[str, Any]) -> str:
    """The arithmetic in one line, for the evidence page."""
    parts = [f"{r['covered_place_homes']:,} detached homes in {r['covered_places']} covered places"]
    if r["covered_outside_homes"]:
        parts.append(f"{r['covered_outside_homes']:,} outside incorporated places")
    s = " + ".join(parts)
    if r["tribal_homes_excluded"]:
        s += f" (after removing {r['tribal_homes_excluded']:,} on tribal land)"
    towns = r.get("excluded_subdivisions") or []
    if towns:
        s += f" - {sum(t['detached'] for t in towns):,} in the {len(towns)} towns the law does not reach"
    return f"{s} = {r['share']:.1%} of {r['state_detached']:,}"


def check_files(law_dir: Path, data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Recompute every stored coverage share that carries a rule (``hre validate --law-coverage``)."""
    import yaml

    from hre.data.states import lookup

    rows = []
    for p in sorted(law_dir.glob("[A-Z][A-Z].yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for name, s in (doc.get("scenarios") or {}).items():
            cov = s.get("coverage") if isinstance(s, dict) else None
            if not isinstance(cov, dict) or not isinstance(cov.get("rule"), dict):
                continue
            r = coverage_share(lookup(doc["state"]).fips, cov["rule"], data_dir)
            rows.append({"state": doc["state"], "scenario": name, "stored": float(cov["share"]),
                         "computed": r["share"], "ok": abs(float(cov["share"]) - r["share"]) <= 0.0005,
                         "detail": r})
    return rows


def render_markdown(rows: list[dict[str, Any]], today: str) -> str:
    out = [
        "# Current-law coverage: the share of detached homes a statewide law binds",
        "",
        (f"Generated {today} by `uv run hre validate --law-coverage` from the cached ACS 2020-2024 "
        "5-year files (B25024 detached homes, B01003 population; places, places by county, and "
        "American Indian areas by state) and the 2025 place Gazetteer. Method: "
        "`docs/methods/current_law.md`; code: `src/hre/current_law/coverage.py`."),
        "",
        "| State | Reform | Rule | Arithmetic | Share | Stored | Match |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        rule = ", ".join(f"{k} {v}" for k, v in r["detail"]["rule"].items())
        out.append(f"| {r['state']} | {r['scenario']} | {rule} | {sentence(r['detail'])} | "
                   f"{r['computed']:.4f} | {r['stored']:.4f} | {'yes' if r['ok'] else 'NO'} |")
    out += ["", "## Largest places on each side of the line", ""]
    for r in rows:
        d = r["detail"]
        cov = "; ".join(f"{p['name']} ({p['population']:,} people, {p['detached']:,} homes)"
                        for p in d["largest_covered"])
        unc = "; ".join(f"{p['name']} ({p['population']:,} people, {p['detached']:,} homes)"
                        for p in d["largest_uncovered"]) or "none"
        out += [f"- **{r['state']} {r['scenario']}**: covered: {cov}. Not covered: {unc}."]
    out += ["", ("Notes: a place whose Census name ends in \"CDP\" is unincorporated and is counted with "
            "the areas outside cities and towns. Tribal areas are assumed to lie outside incorporated "
            "places. A downtown rule's figure is an upper bound (see the rule's basis in the state file).")]
    return "\n".join(out) + "\n"
