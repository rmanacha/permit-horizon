"""Connecticut block groups recoded from legacy counties to planning regions (offline, tiny fixtures)."""

import shutil

import pytest

from hre.build.build_state_inputs import MissingSource, build_state
from hre.data import fetch_ct_crosswalk

HEADER = ("OID_COUSUB_22|GEOID_COUSUB_22|NAMELSAD_COUSUB_22|AREALAND_COUSUB_22|AREAWATER_COUSUB_22|"
          "MTFCC_COUSUB_22|CLASSFP_COUSUB_22|FUNCSTAT_COUSUB_22|OID_BLKGRP_20|GEOID_BLKGRP_20|"
          "NAMELSAD_BLKGRP_20|AREALAND_BLKGRP_20|AREAWATER_BLKGRP_20|MTFCC_BLKGRP_20|FUNCSTAT_BLKGRP_20|"
          "AREALAND_PART|AREAWATER_PART")


def _write_crosswalk(data_dir, pieces):
    """pieces: (town GEOID 2022, block group GEOID 2020, land part, water part)."""
    lines = [HEADER] + [f"1|{town}|Town|0|0|G4040|T1|A|2|{bg}|Block Group|0|0|G5030|S|{land}|{water}"
                        for town, bg, land, water in pieces]
    path = fetch_ct_crosswalk.crosswalk_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_regions_take_the_largest_land_share(tmp_path):
    _write_crosswalk(tmp_path, [
        ("0911001080", "090135281001", 7_000, 600),        # whole block group in one town
        ("0914000000", "090093431011", 3_600_000, 0),      # straddles two regions: land decides
        ("0917000000", "090093431011", 160, 0),
        ("0912000000", "090019900000", 0, 230_000),        # water-only: water decides
        ("0919000000", "090019900000", 0, 194_000),
        ("0911002060", "090030001001", 400, 0),            # two towns, same region: parts add up
        ("0911003060", "090030001001", 500, 0),
    ])
    regions = fetch_ct_crosswalk.load_block_group_regions(tmp_path)
    assert regions == {"090135281001": "09110", "090093431011": "09140",
                       "090019900000": "09120", "090030001001": "09110"}


def test_remap_keeps_tract_and_block_group_codes():
    rows = [{"geoid": "090135281001", "county_fips": "09013", "population": 5},
            {"geoid": "090010101001", "county_fips": "09001", "population": 7}]
    out, unmatched = fetch_ct_crosswalk.remap_block_groups(rows, {"090135281001": "09110"})
    assert unmatched == ["090010101001"]
    assert out[0] == {"geoid": "090010101001", "county_fips": "09001", "population": 7}  # left for the join to drop
    assert out[1] == {"geoid": "091105281001", "county_fips": "09110", "population": 5}


@pytest.fixture
def legacy_zz(sample_dir, tmp_path, monkeypatch):
    """ZZ with its centers of population under 'legacy' counties 011/013, standing in for Connecticut."""
    data = tmp_path / "sample"
    shutil.copytree(sample_dir, data)
    cenpop = data / "cenpop" / "CenPop2020_Mean_BG99.txt"
    lines = cenpop.read_text(encoding="utf-8-sig").splitlines()
    legacy = [lines[0]] + [ln.replace("99,001,", "99,011,").replace("99,003,", "99,013,") for ln in lines[1:]]
    cenpop.write_text("﻿" + "\n".join(legacy) + "\n", encoding="utf-8")
    pieces = []
    for ln in legacy[1:]:
        st, co, tract, bg = ln.split(",")[:4]
        region = {"011": "99001", "013": "99003"}[co]
        pieces.append((region + "00100", st + co + tract + bg, 1_000, 0))
    _write_crosswalk(data, pieces)
    reference, _ = build_state("ZZ", sample_dir)  # before the switch: the untouched ZZ build
    monkeypatch.setattr(fetch_ct_crosswalk, "CT_FIPS", "99")
    return data, reference


def test_build_recodes_legacy_block_groups(legacy_zz):
    data, reference = legacy_zz
    si, summary = build_state("ZZ", data)
    assert summary["block_groups"] == 10 and summary["bg_within_half_mile"] == 3
    assert si.to_dict()["block_groups"] == reference.to_dict()["block_groups"]
    assert any("10 of 10 2020 block groups recoded" in n for n in si.notes)
    assert not any("not in the Gazetteer" in n for n in si.notes)


def test_build_needs_the_crosswalk(legacy_zz):
    data, _ = legacy_zz
    fetch_ct_crosswalk.crosswalk_path(data).unlink()
    with pytest.raises(MissingSource, match="crosswalk"):
        build_state("ZZ", data)
    si, summary = build_state("ZZ", data, lenient=True)
    assert summary["block_groups"] == 0
    assert sum("not in the Gazetteer" in n for n in si.notes) == 10
