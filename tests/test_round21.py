"""Values introduced after the authors' comments on the abstract of the English manuscript v7 (2026-11-07):
python/analysis/a16_v71_review.py."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_climate_per_event():
    R = pd.read_csv(TAB / "climate_per_event_spearman.csv").set_index("response")
    assert [r(R.loc[v, "rho"], 2) for v in ("events", "CO2", "CO2_per_event_t", "area_per_event_km2")] == [-0.68, -0.71, -0.44, -0.67]
    assert [r(R.loc[v, "p"], 3) for v in ("events", "CO2", "CO2_per_event_t", "area_per_event_km2")] == [0.007, 0.004, 0.118, 0.009]


def test_area_ratio_screened():
    K = pd.read_csv(TAB / "area_ratio_screened.csv")
    assert len(K) == 13
    assert [r(K.ratio_all_mb.median(), 1), r(K.ratio_screened_mb.median(), 1)] == [17.2, 17.2]
    assert [r(K.ratio_all_mcd.median(), 1), r(K.ratio_screened_mcd.median(), 1)] == [34.4, 34.4]
    assert r(K.flagged_area_pct.median(), 2) == 0.11 and r(K.flagged_area_pct.max(), 1) == 1.8


def test_municipal_top_2020_versions():
    T = pd.read_csv(TAB / "municipal_top_2020_versions.csv")
    top5 = lambda p: list(T[(T["product"] == p) & (T["rank"] <= 5)].sort_values("rank").municipality)
    assert top5("FINN v1.5 MODIS")[:2] == ["Lages", "Caçador"]
    assert top5("FINN v2.5 MODIS+VIIRS") == ["Lages", "São Joaquim", "Caçador", "Ponte Alta do Norte", "Bom Jardim da Serra"]
