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
    nrc: Annotated[bool, typer.Option("--nrc", help="completions per permit from the Census NRC annual tables")] = False,
    write_register: Annotated[bool, typer.Option("--write-register", help="with --baseline, --adu-tiers or --nrc: write results into parameters.yaml")] = False,
    data_dir: Annotated[Path | None, typer.Option("--data-dir")] = None,
) -> None:
    """Checks: the ACLF doubling ratio, a processed file against the schema, or the baseline backtest."""
    from hre.schema import validate as validate_schema

    dd = _data_dir(data_dir)
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
        typer.echo("nothing to do: pass --aclf, --processed, --baseline, --adu-tiers or --nrc", err=True)
        raise typer.Exit(code=2)


def _round_floats(obj, digits: int = 4):
    """Round every float for a readable results file (the engine itself never rounds)."""
    if isinstance(obj, float):
        return round(obj, digits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, digits) for k, v in obj.items()}
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
    state: Annotated[str, typer.Option("--state", help="USPS code (ZZ is the synthetic demo state)")],
    scenarios: Annotated[str, typer.Option("--scenarios", help="comma-separated; Phase 2: baseline")] = "baseline",
    out: Annotated[Path | None, typer.Option("--out", help="results file (default results/{ST}.json)")] = None,
    processed_dir: Annotated[Path, typer.Option("--processed-dir", help="folder with {ST}.json")] = Path("data/processed"),
    data_dir: Annotated[Path | None, typer.Option("--data-dir", help="build the inputs in memory from this raw folder (e.g. data/sample) instead of reading the processed file")] = None,
) -> None:
    """Run the engine for one state and write the results JSON (docs/methods/results_schema.md)."""
    import datetime as dt
    import hashlib

    from hre.assumptions.loader import ELASTICITIES_PATH, PARAMETERS_PATH, load_params
    from hre.current_law.loader import register_digest
    from hre.data.fetch_bps import VINTAGE as BPS_VINTAGE
    from hre.data.fetch_hcd import VINTAGE as HCD_VINTAGE
    from hre.model.run import run_state, validate_results
    from hre.schema import StateInputs

    code = state.strip().upper()
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
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    input_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    param_sha = digest(PARAMETERS_PATH)
    git_sha = _git_sha()
    meta = {
        "build_id": f"{git_sha[:7]}-{hashlib.sha256((input_sha + param_sha).encode()).hexdigest()[:8]}",
        "vintages": {**inputs.vintages, "bps_state_backtest": f"state annual files 1980-2025, {BPS_VINTAGE}",
                     "hcd_adu_tiers": f"HCD APR Table A2, {HCD_VINTAGE} (tier rates in the register)"},
        "git_sha": git_sha,
        "run_date": dt.date.today().isoformat(),
        "input": input_ref,
        "input_sha256": input_sha,
        "schema_version": inputs.schema_version,
    }
    registers = {
        "parameters": {"path": "src/hre/assumptions/parameters.yaml", "sha256": param_sha,
                       "entries": len(params.entries), "levels": "all mid unless a case says otherwise"},
        "elasticities": {"path": "src/hre/assumptions/elasticities.yaml", "sha256": digest(ELASTICITIES_PATH)},
        "current_law": {"path": f"src/hre/current_law/{code}.yaml", "sha256": register_digest(code)},
    }
    wanted = [s.strip() for s in scenarios.split(",") if s.strip()]
    try:
        results = run_state(inputs, params, wanted, meta, registers, state_name=st.name)
    except NotImplementedError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e
    problems = validate_results(results)
    if problems:
        typer.echo("results failed the schema check:\n  " + "\n  ".join(problems), err=True)
        raise typer.Exit(code=1)
    dest = out or Path("results") / f"{code}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(_round_floats(results), indent=1, allow_nan=False) + "\n", encoding="utf-8")
    b = results["baseline"]["state"]
    typer.echo(f"{code}: baseline {b['low']:,.0f} / {b['mid']:,.0f} / {b['high']:,.0f} permits "
               f"{results['baseline']['forecast_years'][0]}-{results['baseline']['forecast_years'][-1]} "
               f"(low / mid / high); build {meta['build_id']} -> {dest}")
    for line in results["baseline"]["narrative"]:
        typer.echo("   " + line)
    typer.echo("   Shown beside it (20-year swing band, alternative_band):")
    for line in results["baseline"]["alternative_band"]["narrative"]:
        typer.echo("     " + line)


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
