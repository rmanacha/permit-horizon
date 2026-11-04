"""Command line: ``hre fetch``, ``hre build``, ``hre validate``.

    hre fetch --state NH            download every Tier-1 input NH needs (manifests written)
    hre fetch --all                 the same for the 50 states and DC
    hre fetch --hcd                 the California HCD Table A2 file (295 MB)
    hre build --state NH            write data/processed/NH.json from the cache
    hre build --state ZZ --data-dir data/sample   the offline demo (make demo)
    hre build --hcd                 write data/processed/CA_hcd_adu.json
    hre validate --aclf --states NH,UT,AZ,CA      the address-count doubling check
    hre validate --processed data/processed/NH.json   check a file against the schema
    hre validate --baseline         the baseline backtest (both band rules) -> docs/evidence/
    hre validate --adu-tiers        ADU value tiers + 1,000-split city check (needs make hcd)
    hre validate --nrc --fetch      completions per permit by structure type (Census NRC)
    hre validate --overview         sanity review of results/*.json -> docs/evidence/results_overview.md
    hre validate --law-coverage     current-law coverage shares -> docs/evidence/current_law_coverage.md
    hre validate --law-quotes --fetch   every current-law quote checked against its page
    hre run --state NH --scenarios baseline           results/NH.json (three-layer schema)
    hre run --all                   results/{ST}.json for every jurisdiction with a processed file
    hre export --out web/public/results/   the web bundle (results, index, registers, meta)
    hre export --register-md        the assumption register as a Markdown table

``DATA_DIR`` (or ``--data-dir``) moves the raw cache; manifests always go to
``data/manifests``. Nothing needs an API key.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Annotated, Any

import typer

from hre.data.cache import load_dotenv
from hre.data.states import ALL_STATES, lookup

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)


def _states(state: str | None, all_states: bool) -> list[str]:
    if all_states:
        return list(ALL_STATES)
    if not state:
        raise typer.BadParameter("pass --state XX or --all")
    return [s.strip().upper() for s in state.split(",") if s.strip()]


def _data_dir(data_dir: Path | None) -> Path | None:
    import os

    load_dotenv()
    if data_dir is not None:
        os.environ["DATA_DIR"] = str(data_dir)
        return data_dir
    return None


@app.command()
def fetch(
    state: Annotated[str | None, typer.Option("--state", help="USPS code, or several comma-separated")] = None,
    all_states: Annotated[bool, typer.Option("--all", help="every state and DC")] = False,
    hcd: Annotated[bool, typer.Option("--hcd", help="also fetch California HCD Table A2 (295 MB)")] = False,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", help="raw cache root (default data/raw)")] = None,
    force: Annotated[bool, typer.Option("--force", help="re-download even if the cached file matches")] = False,
) -> None:
    """Download the Tier-1 inputs for one or more states, writing provenance manifests."""
    from hre.data import (
        fetch_aclf,
        fetch_acs,
        fetch_bps,
        fetch_cbsa,
        fetch_cenpop,
        fetch_ct_crosswalk,
        fetch_fhfa,
        fetch_gazetteer,
        fetch_hcd,
        fetch_nzlud,
        fetch_pep,
        fetch_rail_supplement,
        fetch_transit,
    )

    dd = _data_dir(data_dir)
    codes = _states(state, all_states) if (state or all_states) else []
    t0 = time.time()
    if codes:
        typer.echo("national files: gazetteer, cbsa, bps, pep, acs, fhfa, nzlud")
        fetch_gazetteer.fetch_gazetteer(dd, force=force)
        fetch_cbsa.fetch_cbsa(dd, force=force)
        fetch_bps.fetch_bps(dd, force=force)
        fetch_pep.fetch_pep(dd, force=force)
        fetch_acs.fetch_acs(dd, force=force)
        fetch_fhfa.fetch_fhfa(dd, force=force)
        fetch_nzlud.fetch_nzlud(dd, force=force)
    for code in codes:
        st = lookup(code)
        if st.synthetic:
            raise typer.BadParameter(f"{st.usps} is the synthetic demo state; nothing to fetch")
        typer.echo(f"{st.usps}: cenpop, aclf ({len(fetch_aclf.VINTAGES)} vintages), transit stops, ntd")
        fetch_cenpop.fetch_cenpop(st.fips, dd, force=force)
        if st.fips == fetch_ct_crosswalk.CT_FIPS:
            fetch_ct_crosswalk.fetch_ct_crosswalk(dd, force=force)
        fetch_aclf.fetch_aclf(st, dd, force=force)
        counties = fetch_gazetteer.load_counties(st.fips, dd)
        fetch_transit.fetch_ntm_stops(st, counties, dd, force=force)
        fetch_transit.fetch_ntd_modes(st, dd, force=force)
        fetch_rail_supplement.fetch_rail_supplement(st.fips, dd, force=force)
        from hre.adapters import registry

        a = registry.get(st.usps)
        if a is not None and a.enabled:
            p = registry.fetch(st.usps, Path("data/processed"))
            typer.echo(f"{st.usps}: parcel adapter counts -> {p}")
        elif a is not None:
            typer.echo(f"{st.usps}: parcel adapter disabled ({a.rules.get('disabled_reason', '')[:80]}...)")
    if hcd:
        typer.echo("hcd: California APR Table A2 (about 295 MB)")
        fetch_hcd.fetch_hcd(dd, force=force)
    typer.echo(f"done in {time.time() - t0:.0f}s; manifests in data/manifests/")


@app.command()
def build(
    state: Annotated[str | None, typer.Option("--state", help="USPS code, or several comma-separated")] = None,
    all_states: Annotated[bool, typer.Option("--all", help="every state and DC")] = False,
    hcd: Annotated[bool, typer.Option("--hcd", help="build the California ADU table from HCD Table A2")] = False,
    data_dir: Annotated[Path | None, typer.Option("--data-dir", help="raw cache root (default data/raw)")] = None,
    out: Annotated[Path, typer.Option("--out", help="output folder")] = Path("data/processed"),
    lenient: Annotated[bool, typer.Option("--lenient", help="build with missing sources, noting each")] = False,
) -> None:
    """Assemble data/processed/{ST}.json (validated against src/hre/schema.py)."""
    from hre.build.build_state_inputs import MissingSource, write_state
    from hre.data import fetch_hcd

    dd = _data_dir(data_dir)
    codes = _states(state, all_states) if (state or all_states) else []
    for code in codes:
        t0 = time.time()
        try:
            dest, s = write_state(code, dd, out, lenient=lenient)
        except MissingSource as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=2) from e
        if s.get("adapter") not in (None, "none"):
            typer.echo(f"   parcel adapter: {s['adapter']}")
        typer.echo(f"{s['state']}: {s['counties']} counties, {s['block_groups']} block groups, "
                   f"{s['major_stops']} major stops, {s['bg_within_half_mile']} block groups within "
                   f"half a mile; permits latest year {s['permits_latest_year_total']:,}; "
                   f"address counts {s['aclf']}; {s['bytes']:,} bytes -> {dest} ({time.time() - t0:.1f}s)")
        for r in s["aclf_ratios"]:
            typer.echo(f"   aclf {r['vintage']}: {r['aclf_total']:>12,} / PEP {r['pep_reference'] or 0:>12,} "
                       f"= {r['ratio']}  ({r['method']})")
        if s["ntd_rail_agencies"]:
            typer.echo("   NTD rail/ferry agencies: " + "; ".join(s["ntd_rail_agencies"]))
    if hcd:
        t0 = time.time()
        dest = fetch_hcd.write_hcd_outputs(dd, out)
        table = json.loads(dest.read_text())
        typer.echo(f"hcd: {len(table['rows'])} jurisdiction-years -> {dest} ({time.time() - t0:.0f}s)")
        for y in sorted(table["statewide"]):
            d, r = table["statewide"][y], table["statewide_raw"].get(y, {})
            typer.echo(f"   {y}: permitted {d['permitted']:>7,} (raw {r.get('permitted', 0):>7,})  "
                       f"completed {d['completed']:>7,} (raw {r.get('completed', 0):>7,})")


@app.command()
def validate(
    aclf: Annotated[bool, typer.Option("--aclf", help="run the Address Count doubling check")] = False,
    states: Annotated[str | None, typer.Option("--states", help="comma-separated USPS codes")] = None,
    all_states: Annotated[bool, typer.Option("--all", help="every state and DC")] = False,
    do_fetch: Annotated[bool, typer.Option("--fetch", help="download missing ACLF and PEP files first")] = False,
    write: Annotated[Path | None, typer.Option("--write", help="write the ratio table as Markdown here")] = None,
    processed: Annotated[Path | None, typer.Option("--processed", help="a processed JSON to validate")] = None,
    baseline: Annotated[bool, typer.Option("--baseline", help="backtest the baseline under both band rules")] = False,
    adu_tiers: Annotated[bool, typer.Option("--adu-tiers", help="calibrate ADU value tiers from HCD Table A2 + ACS")] = False,
    nrc: Annotated[bool, typer.Option("--nrc", help="completions per permit from the Census NRC annual tables")] = False,
    overview: Annotated[bool, typer.Option("--overview", help="sanity review of results/*.json -> docs/evidence/results_overview.md")] = False,
    law_coverage: Annotated[bool, typer.Option("--law-coverage", help="recompute current-law coverage shares -> docs/evidence/current_law_coverage.md")] = False,
    law_quotes: Annotated[bool, typer.Option("--law-quotes", help="check every current-law quote against its page -> docs/evidence/current_law_quotes.md")] = False,
    law_dir: Annotated[Path | None, typer.Option("--law-dir", help="with --law-quotes or --law-coverage: a folder of current-law files other than the register")] = None,
    write_register: Annotated[bool, typer.Option("--write-register", help="with --baseline, --adu-tiers or --nrc: write results into parameters.yaml")] = False,
    data_dir: Annotated[Path | None, typer.Option("--data-dir")] = None,
) -> None:
    """Checks: the ACLF doubling ratio, a processed file against the schema, or the baseline backtest."""
    from hre.schema import validate as validate_schema

    dd = _data_dir(data_dir)
    if law_quotes:
        import datetime as dt

        from hre.current_law.loader import HERE as LAW_DIR
        from hre.validation import law_quotes as lq

        rows = lq.check(law_dir or LAW_DIR, fetch=do_fetch, data_dir=dd)
        dest = write or Path("docs/evidence/current_law_quotes.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(lq.render_markdown(rows, dt.date.today().isoformat()), encoding="utf-8")
        for r in rows:
            if r["found"] is not True:
                typer.echo(f"{r['state']} {r['scenario']} {r['where']}: {r['status']} ({r['url']})")
        n_found = sum(1 for r in rows if r["found"])
        typer.echo(f"{n_found} of {len(rows)} quotes found; wrote {dest}")
        if any(r["found"] is False for r in rows):
            raise typer.Exit(code=1)
        return
    if law_coverage:
        import datetime as dt

        from hre.current_law import coverage as cov
        from hre.current_law.loader import HERE as LAW_DIR
        from hre.data.fetch_acs import fetch_acs

        if do_fetch:
            fetch_acs(dd, tables=("b01003", "b25024"))
            cov.fetch_place_gazetteer(dd)
        try:
            rows = cov.check_files(law_dir or LAW_DIR, dd)
        except FileNotFoundError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=2) from e
        dest = write or Path("docs/evidence/current_law_coverage.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cov.render_markdown(rows, dt.date.today().isoformat()), encoding="utf-8")
        for r in rows:
            typer.echo(f"{r['state']} {r['scenario']}: {cov.sentence(r['detail'])} "
                       f"(stored {r['stored']:.4f}: {'match' if r['ok'] else 'MISMATCH'})")
        typer.echo(f"wrote {dest}")
        if not all(r["ok"] for r in rows):
            raise typer.Exit(code=1)
        return
    if overview:
        import datetime as dt

        from hre.validation import results_overview as ov

        dest = write or Path("docs/evidence/results_overview.md")
        try:
            n = ov.write(Path("results"), dest, dt.date.today().isoformat())
        except FileNotFoundError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=2) from e
        typer.echo(f"wrote {dest} ({n} jurisdictions)")
        return
    if nrc:
        import datetime as dt

        from hre.assumptions.loader import PARAMETERS_PATH
        from hre.data import fetch_nrc
        from hre.validation import completions_per_permit as cpp

        today = dt.date.today().isoformat()
        if do_fetch:
            fetch_nrc.fetch_nrc(dd)
        if not all(fetch_nrc.nrc_path(k, dd).exists() for k in fetch_nrc.FILES):
            typer.echo("NRC tables not cached; run with --fetch", err=True)
            raise typer.Exit(code=2)
        data = fetch_nrc.load_nrc(dd)
        table = cpp.ratio_table(data)
        dest = write or Path("docs/evidence/completions_per_permit.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cpp.render_markdown(table, max(data["permits"]), today), encoding="utf-8")
        for pid, v in cpp.register_values(table).items():
            typer.echo(f"{pid}: low {v['low']:.2f}, mid {v['mid']:.2f}, high {v['high']:.2f} "
                       f"(research {cpp.RESEARCH[pid][0]:.2f} / {cpp.RESEARCH[pid][1]:.2f})")
        typer.echo(f"wrote {dest}")
        if write_register:
            cpp.write_register(table, PARAMETERS_PATH, today)
            typer.echo(f"wrote 3 completions-per-permit entries into {PARAMETERS_PATH}")
        return
    if adu_tiers:
        import datetime as dt

        from hre.assumptions.loader import PARAMETERS_PATH
        from hre.validation import calibrate_adu_tiers as cal

        today = dt.date.today().isoformat()
        cities = cal.load_cities(Path("data/processed"), dd)
        fit = cal.fit_without_la(cities)
        with_la, without_la = cal.split_check(cities, True), cal.split_check(cities, False)
        dest = write or Path("docs/evidence/adu_tiers.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cal.render_markdown(cities, fit, with_la, without_la, today), encoding="utf-8")
        typer.echo(f"cities: {len(cities.name)} (LA included in the count, excluded from the fit)")
        typer.echo("bounds: " + ", ".join(f"${b:,.0f}" for b in fit.bounds))
        for k in range(5):
            typer.echo(f"   tier {k + 1}: {fit.n_cities[k]} cities, {100 * fit.low[k]:.3f}% / "
                       f"{100 * fit.mid[k]:.3f}% / {100 * fit.high[k]:.3f}% a year")
        typer.echo(f"split check: {with_la['inside']}/{with_la['splits']} inside with LA "
                   f"(median {with_la['median_ratio']:.2f}x mid); {without_la['inside']}/"
                   f"{without_la['splits']} without LA (median {without_la['median_ratio']:.2f}x)")
        typer.echo(f"wrote {dest}")
        if write_register:
            names = cities.name
            la = names.index(cal.LA)
            la_rate = cities.completed[la] / (3 * cities.detached[la])
            block = cal.register_block(fit, len(names) - 1, la_rate, today)
            cal.write_register_tiers(block, PARAMETERS_PATH)
            typer.echo(f"wrote 4 bounds and 15 rates into {PARAMETERS_PATH}")
        return
    if baseline:
        import datetime as dt

        from hre.assumptions.loader import PARAMETERS_PATH
        from hre.validation import backtest_baseline as bt

        if do_fetch:
            bt.fetch_series(dd)
        panel = bt.load_panel(dd)
        if sum(len(s) for s in panel.values()) == 0:
            typer.echo("no BPS state files cached; run with --fetch", err=True)
            raise typer.Exit(code=2)
        r = bt.run_backtest(panel)
        dest = write or Path("docs/evidence/baseline_backtest.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(bt.render_markdown(r, dt.date.today().isoformat()), encoding="utf-8")
        o, a = r["ours"], r["adam"]["runs"]
        m = r["methods"]["mean3"]
        typer.echo(f"methods: 3-yr mean x 5, {m['n']} runs, median abs error {m['mdape']:.1%}")
        typer.echo(f"rule A (ours): P10 {o['p10']:.4f}, P90 {o['p90']:.4f}; estimation "
                   f"{o['estimation']['inside']}/{o['estimation']['n']} inside; test 2016-2020 "
                   f"{o['test']['inside']}/{o['test']['n']} inside")
        typer.echo(f"rule B (Adam): {a['inside']}/{a['n']} inside, {a['above']} above, {a['below']} below")
        typer.echo(f"wrote {dest}")
        if write_register:
            bt.write_register_band(r, PARAMETERS_PATH)
            typer.echo(f"wrote baseline_band_ratio into {PARAMETERS_PATH}")
        return
    if processed is not None:
        problems = validate_schema(json.loads(Path(processed).read_text(encoding="utf-8")))
        if problems:
            typer.echo(f"{processed}: {len(problems)} problem(s)")
            for p in problems[:50]:
                typer.echo("  " + p)
            raise typer.Exit(code=1)
        typer.echo(f"{processed}: valid")
    if aclf:
        from hre.data import fetch_aclf, fetch_gazetteer, fetch_pep

        codes = _states(states, all_states)
        if do_fetch:
            fetch_gazetteer.fetch_gazetteer(dd)
            fetch_pep.fetch_pep(dd)
        lines = ["| State | Vintage | Published ACLF total | PEP reference | Ratio | Reference method |",
                 "|---|---|---|---|---|---|"]
        verdicts = []
        for code in codes:
            st = lookup(code)
            if do_fetch:
                fetch_aclf.fetch_aclf(st, dd)
            gaz = fetch_gazetteer.load_counties(st.fips, dd)
            pep = fetch_pep.load_pep(st.name, gaz, dd)
            years = sorted({y for s in pep.values() for y in s})
            pep_state = {y: sum(s.get(y, 0) for s in pep.values()) for y in years}
            rows = fetch_aclf.ratio_table(fetch_aclf.load_aclf(st, dd), pep_state)
            ok, why = fetch_aclf.doubling_check(rows)
            verdicts.append((st.usps, ok, why))
            for r in rows:
                lines.append(f"| {st.usps} | {r['vintage']} | {r['aclf_total']:,} | "
                             f"{(r['pep_reference'] or 0):,} | {r['ratio']} | {r['method']} |")
            typer.echo(f"{st.usps}: {'PASS' if ok else 'FAIL'} ({why})")
            for r in rows:
                typer.echo(f"   {r['vintage']}: {r['aclf_total']:>12,} / {(r['pep_reference'] or 0):>12,} = {r['ratio']}")
        lines.append("")
        lines.append("| State | Verdict | Reason |")
        lines.append("|---|---|---|")
        lines.extend(f"| {u} | {'PASS' if ok else 'FAIL'} | {why} |" for u, ok, why in verdicts)
        n_pass = sum(1 for _, ok, _ in verdicts if ok)
        typer.echo(f"{n_pass} of {len(verdicts)} states pass the 2.0 +/- 0.05 check")
        if write is not None:
            write.parent.mkdir(parents=True, exist_ok=True)
            write.write_text("\n".join(lines) + "\n", encoding="utf-8")
            typer.echo(f"wrote {write}")
    if not aclf and processed is None:
        typer.echo("nothing to do: pass --aclf, --processed, --baseline, --adu-tiers, --nrc, --overview, --law-coverage or --law-quotes", err=True)
        raise typer.Exit(code=2)


UNROUNDED = ("components",)   # the exact-rescale block the web page multiplies (results_schema.md)


def _round_floats(obj, digits: int = 4):
    """Round every float for a readable results file (the engine itself never rounds).

    ``components`` stays unrounded: the web page rescales from it, and rounding there would turn
    an exact rescale into an approximate one (tod_rate_per_home 0.000117 would read 0.0001).
    """
    if isinstance(obj, float):
        return round(obj, digits)
    if isinstance(obj, dict):
        return {k: (v if k in UNROUNDED else _round_floats(v, digits)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, digits) for v in obj]
    return obj


def _git_sha() -> str:
    import subprocess

    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@app.command()
def run(
    state: Annotated[str | None, typer.Option("--state", help="USPS code (ZZ is the synthetic demo state)")] = None,
    all_states: Annotated[bool, typer.Option("--all", help="every state and DC with a processed file")] = False,
    scenarios: Annotated[str, typer.Option("--scenarios", help="comma-separated, or 'all' (baseline + five)")] = "all",
    out: Annotated[Path | None, typer.Option("--out", help="results file (default results/{ST}.json; one state only)")] = None,
    out_dir: Annotated[Path, typer.Option("--out-dir", help="folder for results/{ST}.json")] = Path("results"),
    processed_dir: Annotated[Path, typer.Option("--processed-dir", help="folder with {ST}.json")] = Path("data/processed"),
    data_dir: Annotated[Path | None, typer.Option("--data-dir", help="build the inputs in memory from this raw folder (e.g. data/sample) instead of reading the processed file")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="one line per state")] = False,
    set_values: Annotated[list[str] | None, typer.Option(
        "--set", help="a user value for one register id, held in every assumption set: --set fee_cut_share=0.3 "
                      "(repeatable; the page's 'run any value' route)")] = None,
    set_levels: Annotated[list[str] | None, typer.Option(
        "--level", help="one register id at its low, mid or high value in every set: --level ramp_adu=high "
                        "(repeatable)")] = None,
) -> None:
    """Run the engine for one state (or all) and write the results JSON (docs/methods/results_schema.md)."""
    from hre.model.run import KNOWN_SCENARIOS

    overrides = _parse_overrides(set_values or [], set_levels or [])
    wanted = list(KNOWN_SCENARIOS) if scenarios.strip() == "all" else [s.strip() for s in scenarios.split(",") if s.strip()]
    if all_states:
        codes = [c for c in ALL_STATES if (processed_dir / f"{c}.json").exists()]
        missing = [c for c in ALL_STATES if c not in codes]
        if missing:
            typer.echo(f"no processed file for {len(missing)} jurisdictions: {', '.join(missing)} "
                       "(run 'hre fetch --all' and 'hre build --all')", err=True)
        failed = []
        t0 = time.time()
        for code in codes:
            try:
                _run_one(code, wanted, out_dir / f"{code}.json", processed_dir, None, quiet=True,
                         overrides=overrides)
            except typer.Exit:
                failed.append(code)
        typer.echo(f"ran {len(codes) - len(failed)} of {len(codes)} jurisdictions in {time.time() - t0:.1f}s "
                   f"-> {out_dir}/")
        if failed or missing:
            raise typer.Exit(code=1)
        return
    if not state:
        raise typer.BadParameter("pass --state XX or --all")
    code = state.strip().upper()
    _run_one(code, wanted, out or out_dir / f"{code}.json", processed_dir, data_dir, quiet=quiet,
             overrides=overrides)


def _parse_overrides(values: list[str], levels: list[str]) -> dict[str, dict[str, Any]]:
    """``--set id=number`` and ``--level id=low|mid|high`` -> {"set": {...}, "level": {...}}."""
    from hre.assumptions.loader import load_entries

    entries = load_entries()
    out: dict[str, dict[str, Any]] = {"set": {}, "level": {}}
    for kind, items in (("set", values), ("level", levels)):
        for item in items:
            pid, sep, raw = item.partition("=")
            pid, raw = pid.strip(), raw.strip()
            if not sep or not pid or not raw:
                raise typer.BadParameter(f"--{kind} takes id=value, got {item!r}")
            if pid not in entries:
                raise typer.BadParameter(f"--{kind}: {pid!r} is not in the register (src/hre/assumptions/parameters.yaml)")
            if pid in out["set"] or pid in out["level"]:
                raise typer.BadParameter(f"{pid!r} is given twice")
            if kind == "level":
                if raw not in ("low", "mid", "high"):
                    raise typer.BadParameter(f"--level {pid}: the level must be low, mid or high, got {raw!r}")
                out["level"][pid] = raw
            else:
                try:
                    out["set"][pid] = float(raw)
                except ValueError as e:
                    raise typer.BadParameter(f"--set {pid}: {raw!r} is not a number (use --level for a "
                                             "named level, e.g. a ramp)") from e
    return out


def _run_one(code: str, wanted: list[str], dest: Path, processed_dir: Path, data_dir: Path | None,
             quiet: bool = False, overrides: dict[str, dict[str, Any]] | None = None) -> None:
    import datetime as dt
    import hashlib

    from hre.assumptions.loader import (
        ELASTICITIES_PATH,
        PARAMETERS_PATH,
        load_elasticities,
        load_params,
    )
    from hre.current_law.loader import current_strength, register_digest
    from hre.current_law.schema import SCENARIOS as LAW_SCENARIOS
    from hre.data.fetch_bps import VINTAGE as BPS_VINTAGE
    from hre.data.fetch_hcd import VINTAGE as HCD_VINTAGE
    from hre.data.fetch_nrc import VINTAGE as NRC_VINTAGE
    from hre.model.run import run_state, validate_results
    from hre.schema import StateInputs

    st = lookup(code)
    if data_dir is not None:
        from hre.build.build_state_inputs import build_state

        si, _ = build_state(code, data_dir)
        text = si.to_json()
        input_ref = f"built in memory from {data_dir}"
    else:
        src = processed_dir / f"{code}.json"
        if not src.exists():
            typer.echo(f"{src} not found; run 'make data STATE={code}' first", err=True)
            raise typer.Exit(code=2)
        text = src.read_text(encoding="utf-8")
        input_ref = str(src)
    inputs = StateInputs.from_json(text)
    params = load_params()
    user = {k: v for k, v in (overrides or {}).items() if v}
    if user:
        # A named level becomes that level's register value, so it holds in every assumption set
        # exactly as a --set value does (Params.all_at keeps user values).
        values = {**{pid: params.level_value(pid, lv) for pid, lv in user.get("level", {}).items()},
                  **user.get("set", {})}
        params = params.with_values(values)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    input_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    param_sha = digest(PARAMETERS_PATH)
    git_sha = _git_sha()
    user_key = json.dumps(user, sort_keys=True) if user else ""
    meta = {
        "build_id": f"{git_sha[:7]}-{hashlib.sha256((input_sha + param_sha + user_key).encode()).hexdigest()[:8]}",
        "vintages": {**inputs.vintages, "bps_state_backtest": f"state annual files 1980-2025, {BPS_VINTAGE}",
                     "hcd_adu_tiers": f"HCD APR Table A2, {HCD_VINTAGE} (tier rates in the register)",
                     "nrc": f"Census New Residential Construction, {NRC_VINTAGE} (completions per permit in the register)"},
        "git_sha": git_sha,
        "run_date": dt.date.today().isoformat(),
        "input": input_ref,
        "input_sha256": input_sha,
        "schema_version": inputs.schema_version,
    }
    if user:
        meta["overrides"] = {**user, "reading": ("User values from hre run --set / --level, held in every "
                                                 "assumption set; not the register default.")}
    registers = {
        "parameters": {"path": "src/hre/assumptions/parameters.yaml", "sha256": param_sha,
                       "entries": len(params.entries),
                       "levels": ("all mid unless a case says otherwise" if not user else
                                  "all mid unless a case says otherwise, except the user values in meta.overrides")},
        "elasticities": {"path": "src/hre/assumptions/elasticities.yaml", "sha256": digest(ELASTICITIES_PATH)},
        "current_law": {"path": f"src/hre/current_law/{code}.yaml", "sha256": register_digest(code)},
    }
    law = {s: current_strength(code, s) for s in LAW_SCENARIOS}
    results = run_state(inputs, params, wanted, meta, registers, state_name=st.name, law=law,
                        elasticities=load_elasticities())
    problems = validate_results(results)
    if problems:
        typer.echo(f"{code}: results failed the schema check:\n  " + "\n  ".join(problems), err=True)
        raise typer.Exit(code=1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(_round_floats(results), indent=1, allow_nan=False) + "\n", encoding="utf-8")
    b = results["baseline"]["state"]
    typer.echo(f"{code}: baseline {b['low']:,.0f} / {b['mid']:,.0f} / {b['high']:,.0f} permits "
               f"{results['baseline']['forecast_years'][0]}-{results['baseline']['forecast_years'][-1]} "
               f"(low / mid / high); build {meta['build_id']} -> {dest}")
    if quiet:
        return
    for line in results["baseline"]["narrative"]:
        typer.echo("   " + line)
    typer.echo("   Shown beside it (20-year swing band, alternative_band):")
    for line in results["baseline"]["alternative_band"]["narrative"]:
        typer.echo("     " + line)
    for name, s in results["scenarios"].items():
        e = s["increment"]["estimate"]
        typer.echo(f"   {name}: increment {e['low']:,.0f} / {e['mid']:,.0f} / {e['high']:,.0f} permits "
                   f"(benchmark {s['benchmark']['mid']:,.0f} {s['benchmark']['outcome']})")
    if "combined" in results:
        e = results["combined"]["increment"]["estimate"]
        typer.echo(f"   combined (illustration): {e['low']:,.0f} / {e['mid']:,.0f} / {e['high']:,.0f} permits")


@app.command()
def export(
    register_md: Annotated[bool, typer.Option("--register-md", help="the assumption register as Markdown")] = False,
    out: Annotated[Path | None, typer.Option("--out", help="with --register-md: a file; otherwise the web bundle folder")] = None,
    results_dir: Annotated[Path, typer.Option("--results-dir", help="folder of results/{ST}.json")] = Path("results"),
) -> None:
    """The web bundle (results, index, registers, meta) or the register as Markdown."""
    from hre.assumptions.loader import register_markdown

    if not register_md:
        from hre.export import export_bundle

        dest = out or Path("web/public/results")
        try:
            meta = export_bundle(results_dir, dest)
        except (FileNotFoundError, ValueError) as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=1) from e
        typer.echo(f"wrote {meta['jurisdictions']} results files, index.json, registers.json, meta.json -> {dest}/")
        return
    text = register_markdown()
    if out is None:
        typer.echo(text)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        typer.echo(f"wrote {out} ({text.count(chr(10)) - 6} parameters)")


def main() -> None:  # pragma: no cover
    sys.exit(app())


if __name__ == "__main__":  # pragma: no cover
    main()
