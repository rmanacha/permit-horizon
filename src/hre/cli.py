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
    hre run --state NH --scenarios baseline           results/NH.json (three-layer schema)
    hre export --register-md        the assumption register as a Markdown table

``DATA_DIR`` (or ``--data-dir``) moves the raw cache; manifests always go to
``data/manifests``. Nothing needs an API key.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Annotated

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
        fetch_fhfa,
        fetch_gazetteer,
        fetch_hcd,
        fetch_nzlud,
        fetch_pep,
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
        fetch_aclf.fetch_aclf(st, dd, force=force)
        counties = fetch_gazetteer.load_counties(st.fips, dd)
        fetch_transit.fetch_ntm_stops(st, counties, dd, force=force)
        fetch_transit.fetch_ntd_modes(st, dd, force=force)
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
    write_register: Annotated[bool, typer.Option("--write-register", help="with --baseline or --adu-tiers: write results into parameters.yaml")] = False,
    data_dir: Annotated[Path | None, typer.Option("--data-dir")] = None,
) -> None:
    """Checks: the ACLF doubling ratio, a processed file against the schema, or the baseline backtest."""
    from hre.schema import validate as validate_schema

    dd = _data_dir(data_dir)
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
        typer.echo("nothing to do: pass --aclf, --processed, --baseline or --adu-tiers", err=True)
        raise typer.Exit(code=2)


@app.command()
def export(
    register_md: Annotated[bool, typer.Option("--register-md", help="the assumption register as Markdown")] = False,
    out: Annotated[Path | None, typer.Option("--out", help="write here instead of printing")] = None,
) -> None:
    """Export registers for documentation (Phase 6 builds the full docs from these)."""
    from hre.assumptions.loader import register_markdown

    if not register_md:
        typer.echo("nothing to do: pass --register-md", err=True)
        raise typer.Exit(code=2)
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
