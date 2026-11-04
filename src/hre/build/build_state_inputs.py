"""Assemble ``data/processed/{ST}.json`` from the raw cache.

Every source is joined to the Gazetteer county list by 5-digit FIPS and to the
centers-of-population block-group list by 12-digit GEOID. Nothing here is a
model: the output is the data the engine starts from, with every caveat
written into ``notes`` rather than silently handled.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from hre.build.transit_proximity import nearest_stop_miles
from hre.data import (
    fetch_aclf,
    fetch_acs,
    fetch_bps,
    fetch_cbsa,
    fetch_cenpop,
    fetch_ct_crosswalk,
    fetch_fhfa,
    fetch_gazetteer,
    fetch_nzlud,
    fetch_pep,
    fetch_rail_supplement,
    fetch_transit,
)
from hre.data.states import StateRef, lookup
from hre.schema import BlockGroupInputs, CountyInputs, StateInputs, validate

HALF_MILE, QUARTER_MILE = 0.5, 0.25


class MissingSource(RuntimeError):
    """Raised when a required raw file is absent from the cache (run ``hre fetch`` first)."""


def required_files(state: StateRef, data_dir: Path | None) -> dict[str, Path]:
    files = {
        "gazetteer": fetch_gazetteer.gazetteer_path(data_dir),
        "cbsa": fetch_cbsa.cbsa_path(data_dir),
        "bps (latest county file)": fetch_bps.county_file(fetch_bps.COUNTY_YEARS[-1], data_dir),
        "pep": fetch_pep.pep_path(data_dir),
        "acs b25024": fetch_acs.table_path("b25024", data_dir),
        "acs b25001": fetch_acs.table_path("b25001", data_dir),
        "fhfa": fetch_fhfa.fhfa_path(data_dir),
        "cenpop": fetch_cenpop.cenpop_path(state.fips, data_dir),
        "transit stops": fetch_transit.stops_path(state.fips, data_dir),
        "nzlud": fetch_nzlud.nzlud_dir(data_dir) / "nzlud_msa.csv",
        "aclf (latest)": fetch_aclf.aclf_path(state, fetch_aclf.VINTAGES[-1][1], data_dir),
    }
    if state.fips == fetch_ct_crosswalk.CT_FIPS:
        files["ct block-group crosswalk"] = fetch_ct_crosswalk.crosswalk_path(data_dir)
    for feed in fetch_rail_supplement.feeds_for(state.fips):
        files[f"rail supplement ({feed.line})"] = fetch_rail_supplement.feed_path(feed, data_dir)
    return files


def _check_required(state: StateRef, data_dir: Path | None, lenient: bool) -> list[str]:
    missing = [f"{name}: {path}" for name, path in required_files(state, data_dir).items()
               if not path.exists() and not (name == "gazetteer" and path.with_suffix(".txt").exists())]
    if missing and not lenient:
        raise MissingSource("raw files missing from the cache (run `hre fetch --state "
                            f"{state.usps}` first, or pass --lenient):\n  " + "\n  ".join(missing))
    return missing


def _aclf_block(state: StateRef, data_dir: Path | None, pep: dict[str, dict[str, int]]):
    """Returns (series_by_vintage_by_fips, ratio_rows, decision_note)."""
    aclf = fetch_aclf.load_aclf(state, data_dir)
    if not aclf:
        return {}, [], "address_units: no Address Count Listing Files in the cache; series empty."
    years = sorted({y for s in pep.values() for y in s})
    pep_state = {y: sum(s.get(y, 0) for s in pep.values()) for y in years}
    rows = fetch_aclf.ratio_table(aclf, pep_state)
    ok, why = fetch_aclf.doubling_check(rows)
    if not fetch_aclf.SERIES_APPROVED:
        return {}, rows, fetch_aclf.EXCLUDED_NOTE
    if ok:
        return fetch_aclf.halved_series(aclf), rows, fetch_aclf.HALVED_NOTE
    return {}, rows, (f"address_units: Address Count Listing Files excluded for this state because the "
                      f"published total did not pass the doubling check ({why}); see docs/DATA_PROVENANCE.md.")


def build_state(code: str, data_dir: Path | None = None, *, lenient: bool = False) -> tuple[StateInputs, dict]:
    """Build one state's inputs. Returns (StateInputs, summary dict for the CLI)."""
    state = lookup(code)
    missing = _check_required(state, data_dir, lenient)
    notes: list[str] = [f"lenient build: missing {m}" for m in missing]

    gaz = fetch_gazetteer.load_counties(state.fips, data_dir)
    cbsa = fetch_cbsa.load_cbsa(data_dir) if fetch_cbsa.cbsa_path(data_dir).exists() else {}
    permits, bps_notes = fetch_bps.load_county_permits(state.fips, data_dir)
    history = {y: sum(v.values()) for y, v in sorted(fetch_bps.load_state_permits(state.fips, data_dir).items())}
    pep = fetch_pep.load_pep(state.name, gaz, data_dir) if fetch_pep.pep_path(data_dir).exists() else {}
    acs_county = fetch_acs.load_county_acs(state.fips, data_dir)
    fhfa = fetch_fhfa.load_fhfa(state.fips, data_dir) if fetch_fhfa.fhfa_path(data_dir).exists() else {}
    aclf_series, ratio_rows, aclf_note = _aclf_block(state, data_dir, pep)
    notes.append(aclf_note)

    counties: list[CountyInputs] = []
    for g in gaz:
        f = g["fips"]
        c = CountyInputs(fips=f, name=g["name"], land_sqmi=g["land_sqmi"])
        meta = cbsa.get(f)
        if meta:
            c.cbsa, c.cbsa_title, c.cbsa_type, c.metro_role = (
                meta["cbsa"], meta["cbsa_title"], meta["cbsa_type"], meta["metro_role"])
        c.permits = permits.get(f, {})
        c.permits_5plus_share_5yr = fetch_bps.five_plus_share(c.permits) if c.permits else None
        absent = [str(y) for y in fetch_bps.COUNTY_YEARS if str(y) not in c.permits]
        if absent and fetch_bps.county_file(fetch_bps.COUNTY_YEARS[-1], data_dir).exists():
            c.notes.append("permits: no BPS row (no permit-issuing place reported) for "
                           + ", ".join(absent) + "; treated as absent, not zero.")
        c.notes.extend(bps_notes.get(f, []))
        c.housing_units_pep = pep.get(f, {})
        if not c.housing_units_pep and pep:
            c.notes.append("housing_units_pep: county name did not join to the PEP table.")
        for k, v in acs_county.get(f, {}).items():
            setattr(c, k, v)
        c.hpi = fhfa.get(f, {})
        c.address_units = {v: by_fips.get(f, 0) for v, by_fips in aclf_series.items()}
        counties.append(c)

    bg_rows = fetch_cenpop.load_cenpop(state.fips, data_dir)
    if state.fips == fetch_ct_crosswalk.CT_FIPS and fetch_ct_crosswalk.crosswalk_path(data_dir).exists():
        bg_rows, unmatched = fetch_ct_crosswalk.remap_block_groups(
            bg_rows, fetch_ct_crosswalk.load_block_group_regions(data_dir))
        notes.append(f"block groups: {len(bg_rows) - len(unmatched)} of {len(bg_rows)} 2020 block groups "
                     "recoded from the legacy counties to the planning regions with the Census 2022 "
                     "town-to-2020-block-group relationship file (tract and block-group codes unchanged; "
                     "a block group in two regions goes to the one with more land).")
    acs_bg = fetch_acs.load_block_group_acs(state.fips, data_dir)
    stops = fetch_transit.load_major_stops(state.fips, data_dir)
    extra_stops, extra_notes = fetch_rail_supplement.load_supplement_stops(state.fips, data_dir)
    stops += extra_stops
    notes.extend(extra_notes)
    county_fips = {c.fips for c in counties}
    bgs: list[BlockGroupInputs] = []
    for r in bg_rows:
        if r["county_fips"] not in county_fips:
            notes.append(f"block group {r['geoid']} dropped: county {r['county_fips']} not in the Gazetteer.")
            continue
        a = acs_bg.get(r["geoid"], {})
        bgs.append(BlockGroupInputs(
            geoid=r["geoid"], county_fips=r["county_fips"], pop_center_lat=r["lat"],
            pop_center_lon=r["lon"], population=r["population"],
            housing_units=a.get("housing_units"), sf_detached=a.get("sf_detached"),
            units_5plus=a.get("units_5plus"),
        ))
    if bgs:
        dist = nearest_stop_miles([b.pop_center_lat for b in bgs], [b.pop_center_lon for b in bgs],
                                  [s["lat"] for s in stops], [s["lon"] for s in stops])
        for b, d in zip(bgs, dist, strict=True):
            if np.isnan(d):
                b.dist_major_stop_miles = None
                b.near_transit_half_mile = False
                b.near_transit_quarter_mile = False
            else:
                b.dist_major_stop_miles = round(float(d), 3)
                b.near_transit_half_mile = bool(b.dist_major_stop_miles <= HALF_MILE)
                b.near_transit_quarter_mile = bool(b.dist_major_stop_miles <= QUARTER_MILE)
    bg_acs_missing = sum(1 for b in bgs if b.housing_units is None)
    if bg_acs_missing:
        notes.append(f"{bg_acs_missing} of {len(bgs)} 2020 block groups have no ACS 2020-2024 row "
                     "(vintage mismatch); their housing fields are null.")
    if not stops:
        notes.append("transit: no major (rail, streetcar or ferry) stop found in the search box; "
                     "every block group is more than half a mile from one.")

    nzlud = fetch_nzlud.load_nzlud_msa(data_dir) if (fetch_nzlud.nzlud_dir(data_dir) / "nzlud_msa.csv").exists() else {}
    zoning = {c.cbsa: nzlud[c.cbsa] for c in counties if c.cbsa and c.cbsa in nzlud}
    unmatched = sorted({c.cbsa for c in counties if c.cbsa and c.cbsa not in nzlud})
    if unmatched and nzlud:
        notes.append("zoning_by_cbsa: no NZLUD metro row for CBSA " + ", ".join(unmatched)
                     + " (NZLUD uses 2010 codes and covers the 2006 Wharton sample).")

    si = StateInputs(
        state=state.usps, state_fips=state.fips,
        vintages={
            "bps": fetch_bps.VINTAGE, "acs": fetch_acs.VINTAGE, "pep": fetch_pep.VINTAGE,
            "aclf": ", ".join(sorted(aclf_series)) if aclf_series else "excluded",
            "cenpop": fetch_cenpop.VINTAGE, "fhfa": fetch_fhfa.VINTAGE, "cbsa": fetch_cbsa.VINTAGE,
            "nzlud": fetch_nzlud.VINTAGE, "gazetteer": fetch_gazetteer.GAZ_YEAR,
            "transit": "National Transit Map stops as cached (see data/manifests/transit.json)",
        },
        counties=counties, block_groups=bgs, zoning_by_cbsa=zoning, state_permits_history=history,
        notes=notes,
    )
    problems = validate(si.to_dict())
    if problems:
        raise ValueError("built StateInputs failed validation:\n  " + "\n  ".join(problems[:20]))
    summary = {
        "state": state.usps, "counties": len(counties), "block_groups": len(bgs),
        "major_stops": len(stops),
        "bg_within_half_mile": sum(1 for b in bgs if b.near_transit_half_mile),
        "permits_latest_year_total": sum(sum(c.permits[max(c.permits)].values()) for c in counties if c.permits),
        "aclf": "stored (halved from 2023-07)" if aclf_series else "excluded",
        "aclf_ratios": ratio_rows,
        "ntd_rail_agencies": [a["agency"] for a in fetch_transit.load_ntd_rail_agencies(state.fips, data_dir)],
    }
    return si, summary


def _apply_adapter(si: StateInputs, out_dir: Path) -> str:
    """Parcel counts where the state has an enabled adapter and its summary is on disk (decision 39)."""
    from hre.adapters import registry

    a = registry.get(si.state)
    if a is None:
        return "none"
    if not a.enabled:
        si.notes.append(f"adapter {si.state} disabled: {a.rules.get('disabled_reason', '')}")
        return "disabled"
    if not a.summary_path(out_dir).exists():
        si.notes.append(f"adapter {si.state}: no {a.summary_path(out_dir).name}; run hre fetch --state "
                        f"{si.state}. ACS counts kept.")
        return "summary missing"
    a.enrich(si, out_dir)
    problems = validate(si.to_dict())
    if problems:
        raise ValueError("StateInputs failed validation after the adapter:\n  " + "\n  ".join(problems[:20]))
    return f"{len(si.adapter['used_counties'])} counties from parcels, {len(si.adapter['excluded_counties'])} kept ACS"


def write_state(code: str, data_dir: Path | None = None, out_dir: Path = Path("data/processed"),
                *, lenient: bool = False) -> tuple[Path, dict]:
    si, summary = build_state(code, data_dir, lenient=lenient)
    summary["adapter"] = _apply_adapter(si, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{si.state}.json"
    dest.write_text(si.to_json() + "\n", encoding="utf-8")
    summary["path"] = str(dest)
    summary["bytes"] = dest.stat().st_size
    return dest, summary


def load_processed(path: Path) -> StateInputs:
    return StateInputs.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
