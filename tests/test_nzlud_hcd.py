"""NZLUD metro table and the HCD Table A2 de-duplication rule on the fixture."""

from hre.data import fetch_hcd, fetch_nzlud


def test_nzlud_msa(sample_dir):
    msa = fetch_nzlud.load_nzlud_msa(sample_dir)
    assert msa["99900"]["parking_median"] == 1.5 and msa["99900"]["adu"] == 0.666666667
    assert msa["99900"]["responses"] == 3 and msa["99900"]["min_lot_size"] == 1
    muni = fetch_nzlud.load_nzlud_muni(sample_dir)
    assert muni["0102956"]["mf_per"] == 0.285714286  # leading zero restored


def test_project_key_preference():
    assert fetch_hcd.project_key("Zeta City", "001-001-001", "B21-1", "1 Main St") == "ZETACITY|P:001001001"
    assert fetch_hcd.project_key("Zeta City", "", "T-9", "2 Side St") == "ZETACITY|T:T9"
    assert fetch_hcd.project_key("Zeta City", None, None, "3 Twin Ct") == "ZETACITY|A:3TWINCT"
    assert fetch_hcd.project_key("Zeta City", "NA", "", "") is None


def test_hcd_dedup_rule(sample_dir):
    table = fetch_hcd.build_hcd_table(sample_dir / "hcd" / "tablea2.csv")
    s, raw = table["statewide"], table["statewide_raw"]
    # Raw report-year sums double count the repeated permit and completion rows.
    assert {y: v["permitted"] for y, v in raw.items() if v["permitted"]} == {"2021": 1, "2022": 2, "2023": 3, "2024": 2}
    assert {y: v["completed"] for y, v in raw.items() if v["completed"]} == {"2022": 1, "2023": 1, "2025": 1}
    # De-duplicated: each project counted once per stage, at its first active year.
    assert {y: v["permitted"] for y, v in s.items() if v["permitted"]} == {"2021": 1, "2022": 1, "2023": 2, "2024": 2}
    assert {y: v["completed"] for y, v in s.items() if v["completed"]} == {"2022": 1, "2025": 1}
    assert {y: v["entitled"] for y, v in s.items() if v["entitled"]} == {"2021": 1}
    rows = {(r["jurisdiction"], r["year"]): r for r in table["rows"]}
    assert rows[("ALDER COUNTY", 2025)]["completed"] == 1 and rows[("ZETA CITY", 2023)]["permitted"] == 2
    assert all(r["jurisdiction"] != "SFD" for r in table["rows"])
