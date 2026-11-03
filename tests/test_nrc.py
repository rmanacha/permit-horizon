"""Completions per permit from the Census NRC annual tables: parser, arithmetic, register writer."""

import shutil
from pathlib import Path

import openpyxl
import pytest

from hre.assumptions.loader import PARAMETERS_PATH, load_entries
from hre.data import fetch_nrc
from hre.validation import completions_per_permit as cpp

YEARS = range(1995, 2026)


def _workbook(path: Path, values: dict[int, tuple]) -> None:
    """The NRC layout: title rows, a 'Year' header, a column-name row, one row per year."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Annual"
    ws.append(["New Privately-Owned Housing Units ..."])
    ws.append(["(Thousands of units.)"])
    ws.append([])
    ws.append(["Annual data"])
    ws.append(["Year", "United States", None, None, None, "Northeast"])
    ws.append([None, "Total", "1 unit", "2 to 4\n units", "5 units\n or more", "Total"])
    for y, row in values.items():
        ws.append([y, *row, 1.0])
    ws.append(["Footnotes:"])
    wb.save(path)


@pytest.fixture
def nrc_dir(tmp_path):
    d = tmp_path / "raw"
    (d / "nrc").mkdir(parents=True)
    # permits: total 10, 1u 6, 2-4 1, 5+ 3 every year
    _workbook(fetch_nrc.nrc_path("permits", d), {y: (10.0, 6.0, 1.0, 3.0) for y in YEARS})
    # permit-area completions: 2-4 "(NA)" before 2000 (as in the real file)
    _workbook(fetch_nrc.nrc_path("completions_permit_areas", d),
              {y: (9.0, 6.3, "(NA)" if y < 2000 else 0.4, 2.4) for y in YEARS})
    _workbook(fetch_nrc.nrc_path("completions_all_areas", d), {y: (9.3, 6.6, 0.4, 2.4) for y in YEARS})
    return d


def test_parser_reads_years_and_na(nrc_dir):
    data = fetch_nrc.load_nrc(nrc_dir)
    assert sorted(data["permits"]) == list(YEARS)
    assert data["permits"][2024] == {"total": 10.0, "u1": 6.0, "u24": 1.0, "u5": 3.0}
    assert data["completions_permit_areas"][1996]["u24"] is None


def test_cumulative_ratio_by_hand(nrc_dir):
    t = cpp.ratio_table(fetch_nrc.load_nrc(nrc_dir))
    one = t[("completions_permit_areas", "u1", 1995, 2024)]
    assert one["completions"] == pytest.approx(30 * 6.3) and one["permits"] == pytest.approx(30 * 6.0)
    assert one["ratio"] == pytest.approx(1.05)
    assert t[("completions_permit_areas", "u24", 1995, 2024)] is None        # a missing year
    assert t[("completions_permit_areas", "u24", 2010, 2024)]["ratio"] == pytest.approx(0.4)
    v = cpp.register_values(t)
    assert v["completions_per_permit_2to4"] == {"low": 0.9, "mid": 0.9, "high": 0.9}   # total, not 2-4
    assert v["completions_per_permit_5plus"]["mid"] == 0.8


def test_register_writer_round_trip(nrc_dir, tmp_path):
    reg = tmp_path / "parameters.yaml"
    shutil.copy(PARAMETERS_PATH, reg)
    t = cpp.ratio_table(fetch_nrc.load_nrc(nrc_dir))
    cpp.write_register(t, reg, "2026-11-03")
    once = reg.read_text(encoding="utf-8")
    cpp.write_register(t, reg, "2026-11-03")
    assert reg.read_text(encoding="utf-8") == once                          # idempotent
    e = load_entries(reg)
    assert (e["completions_per_permit_1unit"]["low"], e["completions_per_permit_1unit"]["mid"]) == (1.05, 1.05)
    assert "comps_permits_cust.xlsx" in e["completions_per_permit_2to4"]["citation"]
    assert e["horizon_years"] == load_entries()["horizon_years"]            # others untouched


def test_committed_register_cites_the_nrc_files():
    e = load_entries()
    for pid in cpp.REGISTER:
        assert "permits_cust.xlsx" in e[pid]["citation"] and "=" in e[pid]["citation"]
        assert e[pid]["low"] <= e[pid]["mid"] <= e[pid]["high"]
