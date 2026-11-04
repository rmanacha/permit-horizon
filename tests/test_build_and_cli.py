"""End to end on the fixture state: build, validate, round-trip, determinism, and the CLI."""

import json

import pytest
from typer.testing import CliRunner

from hre.build.build_state_inputs import MissingSource, build_state, load_processed, write_state
from hre.cli import app
from hre.schema import StateInputs, validate


def test_build_zz_end_to_end(sample_dir):
    si, summary = build_state("ZZ", sample_dir)
    assert validate(si.to_dict()) == []
    assert summary["counties"] == 2 and summary["block_groups"] == 10 and summary["major_stops"] == 3
    assert summary["bg_within_half_mile"] == 3
    alder = si.county("99001")
    assert alder.metro_role == "central" and alder.cbsa == "99900" and alder.land_sqmi == 500.0
    assert alder.permits["2025"] == {"u1": 190, "u2": 10, "u34": 6, "u5": 80}
    assert alder.housing_units_pep["2025"] == 21000 and alder.sf_detached == 12000
    assert alder.hpi["2025"] == pytest.approx(100 * 1.05**12, abs=0.05)
    birch = si.county("99003")
    assert birch.metro_role == "none" and birch.cbsa is None
    assert any("2017" in n for n in birch.notes)  # no BPS row that year, flagged not zeroed
    assert si.zoning_by_cbsa["99900"]["parking_median"] == 1.5
    bgs = {b.geoid: b for b in si.block_groups}
    assert bgs["990010001001"].near_transit_quarter_mile and bgs["990010001001"].near_transit_half_mile
    assert bgs["990010001002"].near_transit_half_mile and not bgs["990010001002"].near_transit_quarter_mile
    assert not bgs["990010001003"].near_transit_half_mile          # bus stop ignored
    assert not bgs["990010002001"].near_transit_half_mile          # entrance ignored
    assert bgs["990030002002"].near_transit_quarter_mile           # ferry
    assert bgs["990030002002"].housing_units is None and bgs["990010001001"].housing_units == 600
    assert any("no ACS" in n for n in si.notes)


def test_aclf_excluded_by_decision_46(sample_dir):
    from hre.data import fetch_aclf

    assert fetch_aclf.SERIES_APPROVED is False
    si, summary = build_state("ZZ", sample_dir)
    rows = summary["aclf_ratios"]
    assert rows[0]["vintage"] == "2022-06" and rows[-1]["vintage"] == "2026-07"  # still computed and reported
    assert si.county("99001").address_units == {} and summary["aclf"] == "excluded"
    assert any("decision 46" in n for n in si.notes)


def test_aclf_halved_when_approved(sample_dir, monkeypatch):
    """If the series is ever re-approved, a passing state gets the halved values and the note."""
    from hre.data import fetch_aclf

    monkeypatch.setattr(fetch_aclf, "SERIES_APPROVED", True)
    si, summary = build_state("ZZ", sample_dir)
    alder = si.county("99001")
    assert summary["aclf"].startswith("stored")
    assert alder.address_units["2026-07"] == 42500 // 2 and alder.address_units["2022-06"] == 20350
    assert any("divided by two" in n for n in si.notes)


def test_write_is_deterministic_and_small(sample_dir, tmp_path):
    p1, s1 = write_state("ZZ", sample_dir, tmp_path / "a")
    p2, _s2 = write_state("ZZ", sample_dir, tmp_path / "b")
    assert p1.read_bytes() == p2.read_bytes() and s1["bytes"] < 50_000
    text = p1.read_text()
    assert '"block_groups":[{"' in text and text.endswith("}\n")  # compact, sorted keys
    again = load_processed(p1)
    assert again == StateInputs.from_json(text)


def test_missing_source_is_loud(tmp_path):
    with pytest.raises(MissingSource, match="hre fetch"):
        build_state("ZZ", tmp_path / "empty")


def test_cli_build_validate_and_fetch_refusal(sample_dir, tmp_path):
    runner = CliRunner()
    r = runner.invoke(app, ["build", "--state", "ZZ", "--data-dir", str(sample_dir), "--out", str(tmp_path)])
    assert r.exit_code == 0, r.output
    assert "2 counties, 10 block groups" in r.output and (tmp_path / "ZZ.json").exists()
    r = runner.invoke(app, ["validate", "--processed", str(tmp_path / "ZZ.json")])
    assert r.exit_code == 0 and "valid" in r.output
    bad = json.loads((tmp_path / "ZZ.json").read_text())
    bad["counties"][0]["fips"] = 99001
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    r = runner.invoke(app, ["validate", "--processed", str(tmp_path / "bad.json")])
    assert r.exit_code == 1 and "5-digit" in r.output
    r = runner.invoke(app, ["fetch", "--state", "ZZ", "--data-dir", str(tmp_path / "raw")])
    assert r.exit_code != 0 and "synthetic" in (r.output + str(r.exception))


def test_cli_build_hcd_offline(sample_dir, tmp_path):
    runner = CliRunner()
    r = runner.invoke(app, ["build", "--hcd", "--data-dir", str(sample_dir), "--out", str(tmp_path)])
    assert r.exit_code == 0, r.output
    table = json.loads((tmp_path / "CA_hcd_adu.json").read_text())
    assert table["statewide"]["2023"]["permitted"] == 2 and table["statewide_raw"]["2023"]["permitted"] == 3
