"""Current-law register: schema, NH ADU worked example, and the documented default."""

import shutil

import yaml

from hre.current_law.loader import HERE, current_strength, register_digest
from hre.current_law.schema import DEFAULT_NOTE, strength_from_features, validate_state


def test_template_and_nh_files_follow_the_schema():
    nh = yaml.safe_load((HERE / "NH.yaml").read_text())
    assert validate_state(nh) == []
    tpl = yaml.safe_load((HERE / "_template.yaml").read_text())
    assert validate_state(tpl) == []


def test_nh_adu_worked_example():
    r = current_strength("NH", "adu")
    assert r["source"] == "register" and r["current_strength"] == 0.75
    assert r["newly_affected_share"] == 0.25
    assert r["human_review"]["status"] == "pending"
    assert strength_from_features(r["features"]) == 0.75
    assert "674-72" in r["record"]["url"]
    assert register_digest("NH") is not None


def test_missing_file_or_scenario_gives_the_default():
    r = current_strength("WY", "adu")
    assert (r["current_strength"], r["newly_affected_share"], r["note"]) == (0.0, 1.0, DEFAULT_NOTE)
    r = current_strength("NH", "fees")          # NH file exists, fees not assessed
    assert r["current_strength"] == 0.0 and r["file"] == "NH.yaml"


def test_incomplete_entry_falls_back_loudly(tmp_path):
    shutil.copy(HERE / "NH.yaml", tmp_path / "NH.yaml")
    doc = yaml.safe_load((tmp_path / "NH.yaml").read_text())
    del doc["scenarios"]["adu"]["features"][0]["sources"]
    doc["scenarios"]["adu"]["current_strength"] = 1.5
    (tmp_path / "NH.yaml").write_text(yaml.safe_dump(doc))
    r = current_strength("NH", "adu", tmp_path)
    assert r["current_strength"] == 0.0 and r["problems"]
    assert "incomplete" in r["note"]
