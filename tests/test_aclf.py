"""Address Count Listing Files: county sums, the PEP reference, and the doubling check."""

import pytest

from hre.data import fetch_aclf
from hre.data.states import lookup

PEP = {"2020": 30000, "2021": 30300, "2022": 30600, "2023": 30900, "2024": 31200, "2025": 31500}


def test_county_totals_handle_both_header_styles(sample_dir):
    zz = lookup("ZZ")
    old = fetch_aclf.county_totals(fetch_aclf.aclf_path(zz, "062022", sample_dir))
    new = fetch_aclf.county_totals(fetch_aclf.aclf_path(zz, "072026", sample_dir))
    assert old == {"99001": 20350, "99003": 10200}
    assert new == {"99001": 42500, "99003": 21200}
    assert fetch_aclf.aclf_filename(lookup("NH"), "072026") == "33_NewHampshire_AddressBlockCountList_072026.txt"
    assert fetch_aclf.aclf_url(lookup("NH"), "2020", "062022").endswith("/2020/33_NewHampshire_AddressBlockCountList_062022.txt")


def test_load_aclf_keys(sample_dir):
    series = fetch_aclf.load_aclf(lookup("ZZ"), sample_dir)
    assert list(series) == ["2022-06", "2023-07", "2023-12", "2024-07", "2024-12", "2025-07", "2025-12", "2026-07"]


@pytest.mark.parametrize(
    "vintage, expected, method",
    [
        ("2023-07", 30900.0, "exact"),
        ("2023-12", 30900 + 5 / 12 * 300, "interpolated"),
        ("2025-12", 31500 + 5 / 12 * 300, "extrapolated"),
        ("2026-07", 31800.0, "extrapolated"),
        ("2019-07", None, "before"),
    ],
)
def test_pep_reference(vintage, expected, method):
    value, how = fetch_aclf.pep_reference(PEP, vintage)
    assert how.startswith(method)
    assert value == pytest.approx(expected) if expected is not None else value is None


def test_doubling_check_passes_on_fixture(sample_dir):
    rows = fetch_aclf.ratio_table(fetch_aclf.load_aclf(lookup("ZZ"), sample_dir), PEP)
    ok, why = fetch_aclf.doubling_check(rows)
    assert ok, why
    assert rows[0]["ratio"] == pytest.approx(0.998, abs=0.001)
    assert all(1.95 <= r["ratio"] <= 2.05 for r in rows[1:])


def test_doubling_check_fails_when_ratios_vary():
    rows = [{"vintage": "2022-06", "ratio": 1.0}, {"vintage": "2023-07", "ratio": 1.89},
            {"vintage": "2026-07", "ratio": 2.0}]
    ok, why = fetch_aclf.doubling_check(rows)
    assert not ok and "2023-07 (1.89)" in why
    ok, why = fetch_aclf.doubling_check([{"vintage": "2022-06", "ratio": 1.0}])
    assert not ok and "no vintage" in why
    ok, why = fetch_aclf.doubling_check([{"vintage": "2022-06", "ratio": 2.0}, {"vintage": "2026-07", "ratio": 2.0}])
    assert not ok and "pre-2023" in why


def test_halved_series():
    series = {"2022-06": {"99001": 101}, "2023-07": {"99001": 201}, "2026-07": {"99001": 400}}
    out = fetch_aclf.halved_series(series)
    assert out == {"2022-06": {"99001": 101}, "2023-07": {"99001": 100}, "2026-07": {"99001": 200}}
