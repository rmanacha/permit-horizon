"""Saiz (2010) Table VI transcription and its county mapping."""

import yaml

from hre.assumptions.loader import ELASTICITIES_PATH, load_elasticities


def test_table_has_95_metros_ranked_and_sorted():
    metros = yaml.safe_load(ELASTICITIES_PATH.read_text())["metros"]
    assert [m["rank"] for m in metros] == list(range(1, 96))
    vals = [m["elasticity"] for m in metros]
    assert vals == sorted(vals) and vals[0] == 0.60 and vals[-1] == 5.45


def test_brief_checks_salt_lake_and_maricopa():
    by_cbsa, by_county = load_elasticities()
    assert by_cbsa["41620"] == 0.75   # Salt Lake City (Salt Lake County 49035)
    assert by_cbsa["38060"] == 1.61   # Phoenix-Mesa (Maricopa 04013)
    assert by_county["12011"] == 0.65 and by_county["53053"] == 1.21  # Fort Lauderdale, Tacoma
