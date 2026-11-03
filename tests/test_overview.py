"""hre validate --overview: the tables render and hand-written observations survive a rerun."""

import json

from hre.model.run import run_state
from hre.validation import results_overview as ov

META = {"build_id": "x", "vintages": {}, "git_sha": "x", "run_date": "x"}


def test_render_and_keep_observations(zz_state, params, tmp_path):
    r = run_state(zz_state, params, ["baseline", "adu", "missing_middle", "tod", "parking", "fees"], META, {})
    r["meta"]["state"] = "NH"                       # load() skips the synthetic state, so relabel it
    (tmp_path / "res").mkdir()
    (tmp_path / "res" / "NH.json").write_text(json.dumps(r))
    dest = tmp_path / "overview.md"
    assert ov.write(tmp_path / "res", dest, "2026-11-03") == 1
    text = dest.read_text()
    assert "| NH | 1,670 |" in text and "## 4. New Hampshire against Adam Ruege's v2.0" in text
    dest.write_text(text + "1. A hand-written observation.\n")
    ov.write(tmp_path / "res", dest, "2026-11-04")
    again = dest.read_text()
    assert again.count(ov.MARKER) == 1 and again.endswith("1. A hand-written observation.\n")
    assert "on 2026-11-04" in again
