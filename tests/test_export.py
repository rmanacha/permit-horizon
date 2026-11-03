"""hre export: the web bundle from results files (offline, on the synthetic state ZZ)."""

import json

from typer.testing import CliRunner

from hre.cli import app


def test_bundle_from_zz(sample_dir, tmp_path):
    res_dir, web = tmp_path / "results", tmp_path / "web"
    r = CliRunner().invoke(app, ["run", "--state", "ZZ", "--data-dir", str(sample_dir),
                                 "--out", str(res_dir / "ZZ.json"), "--quiet"])
    assert r.exit_code == 0, r.output
    r = CliRunner().invoke(app, ["export", "--results-dir", str(res_dir), "--out", str(web)])
    assert r.exit_code == 0, r.output
    assert sorted(p.name for p in web.iterdir()) == ["ZZ.json", "index.json", "meta.json", "registers.json"]
    zz = json.loads((web / "ZZ.json").read_text())
    assert zz["cross_check"]["housing_units_pep"]["state"]["net_change"] == 1500
    assert zz["baseline"]["band_rule"]["coverage_by_period"]
    assert zz["scenarios"]["parking"]["grid"]["cells"] and zz["scenarios"]["fees"]["components"]["linear_in"]
    row = json.loads((web / "index.json").read_text())["states"][0]
    assert row["state"] == "ZZ" and set(row["scenarios"]) == {"adu", "missing_middle", "tod", "parking", "fees"}
    reg = json.loads((web / "registers.json").read_text())
    assert len(reg["assumptions"]) >= 50 and "NH" in reg["current_law"]
    assert json.loads((web / "meta.json").read_text())["jurisdictions"] == 1


def test_export_refuses_an_invalid_results_file(tmp_path):
    (tmp_path / "NV.json").write_text("{}")
    r = CliRunner().invoke(app, ["export", "--results-dir", str(tmp_path), "--out", str(tmp_path / "w")])
    assert r.exit_code == 1 and "missing baseline" in r.output
