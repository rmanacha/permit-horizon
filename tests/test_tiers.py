"""ADU value tiers: lookup rule, fitting arithmetic and the city-split check, on synthetic cities."""

import numpy as np
import pytest

from hre.model.tiers import county_adu_rates, tier_for
from hre.validation import calibrate_adu_tiers as cal

BOUNDS = [100.0, 200.0, 300.0, 400.0]


def test_tier_lookup_edges():
    assert list(tier_for([50, 100, 100.01, 250, 400, 401], BOUNDS)) == [1, 1, 2, 3, 4, 5]
    assert tier_for(150, BOUNDS) == 2
    assert list(tier_for([None, 50], BOUNDS)) == [0, 1]


def test_county_rates_from_register(params):
    r = county_adu_rates([300000, None, 2_000_000], params)
    assert list(r["tier"]) == [1, 3, 5]
    assert r["rate"][0] == params["adu_rate_tier_1"] and r["rate"][2] == params["adu_rate_tier_5"]
    assert "tier 3" in r["notes"][1] and r["outcome"] == "completed_homes"
    low = county_adu_rates([300000], params, level="low")
    assert low["rate"][0] == params.level_value("adu_rate_tier_1", "low")


def _cities(n_per_tier=4, la=False, uniform=False):
    """Tier k (k=0..4) cities: value 100k*(k+1)+i, 1,000 detached homes, rate 0.001*(k+1) a year
    (or 0.002 everywhere when ``uniform``)."""
    names, vals, det, comp = [], [], [], []
    for k in range(5):
        for i in range(n_per_tier):
            names.append(f"C{k}{i}")
            vals.append(100_000 * (k + 1) + i)
            det.append(1000.0)
            comp.append(3 * 1000 * (0.002 if uniform else 0.001 * (k + 1)))
    if la:
        names.append(cal.LA)
        vals.append(250_000)
        det.append(1000.0)
        comp.append(3 * 1000 * 0.03)     # ten times any tier
    return cal.Cities(names, np.array(vals, float), np.array(det), np.array(comp))


def test_fit_by_hand():
    c = _cities()
    fit = cal.fit_tiers(c.value, c.detached, c.completed)
    assert list(fit.n_cities) == [4, 4, 4, 4, 4]
    assert fit.mid == pytest.approx([0.001, 0.002, 0.003, 0.004, 0.005])
    assert fit.low == pytest.approx(fit.mid) and fit.high == pytest.approx(fit.mid)   # no spread
    # quintile cut 1 = 20th percentile of the 20 values (linear interpolation)
    assert fit.bounds[0] == pytest.approx(np.percentile(c.value, 20))


def test_fit_spread_by_hand():
    # one tier: city rates 0.001, 0.002, 0.003, 0.004 with equal homes
    v = np.array([1.0, 2, 3, 4] * 5) + np.repeat(np.arange(5) * 10, 4)
    comp = np.tile([3.0, 6.0, 9.0, 12.0], 5)
    fit = cal.fit_tiers(v, np.full(20, 1000.0), comp)
    mid = 30 / (3 * 4000)                      # 0.0025
    q1, q2, q3 = np.percentile([0.001, 0.002, 0.003, 0.004], [25, 50, 75])
    assert fit.mid[0] == pytest.approx(mid)
    assert fit.low[0] == pytest.approx(mid * q1 / q2) and fit.high[0] == pytest.approx(mid * q3 / q2)


def test_la_is_never_fitted_and_split_logic():
    assert cal.fit_without_la(_cities(la=True)).mid == pytest.approx([0.001, 0.002, 0.003, 0.004, 0.005])
    c = _cities(la=True, uniform=True)   # every split predicts exactly unless LA is held out
    without = cal.split_check(c, include_la=False, n_splits=50, seed=1)
    assert without["inside"] == 50 and without["median_ratio"] == pytest.approx(1.0)
    with_la = cal.split_check(c, include_la=True, n_splits=50, seed=1)
    # LA held out pushes the actual total above a zero-spread range; otherwise inside
    assert with_la["inside"] == 50 - with_la["la_in_test"]
    assert 0 < with_la["la_in_test"] < 50


def test_register_block_round_trips():
    import yaml

    from hre.assumptions.loader import check_entry

    c = _cities()
    fit = cal.fit_tiers(c.value, c.detached, c.completed)
    block = cal.register_block(fit, 20, 0.01, "2026-11-03")
    entries = yaml.safe_load("parameters:\n" + block)["parameters"]
    assert len(entries) == 9
    for e in entries:
        assert check_entry(e) == [], e["id"]
