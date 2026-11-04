"""The validation ledger and frozen protocols: schema, hit-or-miss arithmetic, hashes that hold."""

import json

import pytest

from hre.validation import freeze, ledger


def test_committed_ledger_follows_its_rules():
    doc = ledger.load()
    assert doc["entries"], "validation/ledger.yaml has entries"
    assert ledger.problems(doc) == []
    classes = {e["evidence_class"] for e in doc["entries"]}
    assert {"internal_historical_check", "calibration", "frozen_holdout"} <= classes
    assert any(e["result"] == "miss" for e in doc["entries"]), "misses are kept"


def test_hit_and_miss_are_recomputed():
    bad = {"entries": [{**{k: "x" for k in ledger.REQUIRED}, "id": "a", "evidence_class": "calibration",
                        "result": "hit", "source": {"title": "t", "url": "https://e.gov"},
                        "prediction": {"low": 1, "mid": 2, "high": 3}, "actual": 4}]}
    assert any("result hit but actual 4" in p for p in ledger.problems(bad))
    bad["entries"][0]["result"] = "miss"
    assert ledger.problems(bad) == []


def test_frozen_protocol_round_trip(tmp_path):
    proto = {"place": "Testville", "years": [2023, 2025], "prediction": {"low": 10, "mid": 20, "high": 30}}
    sha = freeze.write_protocol("t1", proto, tmp_path)
    assert freeze.verify("t1", tmp_path) == sha
    with pytest.raises(FileExistsError):
        freeze.write_protocol("t1", proto, tmp_path)               # frozen means frozen
    r = freeze.write_result("t1", {"actual": 35}, tmp_path)
    assert r["protocol_sha256"] == sha and r["inside"] is False and r["actual_over_mid"] == 1.75
    p = tmp_path / "t1" / "protocol.json"
    p.write_text(p.read_text().replace("Testville", "Elsewhere"))
    with pytest.raises(ValueError):
        freeze.verify("t1", tmp_path)                              # an edit after the fact fails


def test_every_frozen_protocol_in_the_repo_still_has_its_hash():
    checks = [p.parent.name for p in freeze.VALIDATION_DIR.glob("*/protocol.json")]
    for c in checks:
        sha = freeze.verify(c)
        entry = next((e for e in ledger.load()["entries"] if (e.get("frozen") or {}).get("sha256") == sha), None)
        assert entry is not None, f"{c}: frozen protocol has no ledger entry"
        res = freeze.check_dir(c) / "result.json"
        if res.exists():
            assert json.loads(res.read_text())["protocol_sha256"] == sha
