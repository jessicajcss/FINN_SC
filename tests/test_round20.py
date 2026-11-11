"""Values introduced in the adversarial review of the English manuscript v7 (2026-11-06): python/analysis/a15_v7_review.py."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_sen_slope_ci_and_exact_mk():
    S = pd.read_csv(TAB / "sen_slope_ci.csv").set_index(["variable", "period"])
    c = S.loc[("CO2", "2012-2025")]
    assert int(c.S) == -7 and r(c.p_exact, 3) == 0.747
    assert [r(c.ci_low_pct_mean, 1), r(c.ci_high_pct_mean, 1)] == [-5.4, 3.4]
    e = S.loc[("events", "2012-2025")]
    assert [r(e.sen, 0), r(e.ci_low, 0), r(e.ci_high, 0)] == [-46, -275, 132]
    assert [r(S.loc[(v, "2012-2021")].p_exact, 3) for v in ("events", "area_km2", "CO2", "PM25")] == [0.291, 0.216, 0.291, 0.216]
    c10 = S.loc[("CO2", "2012-2021")]
    assert [r(c10.ci_low_pct_mean, 1), r(c10.ci_high_pct_mean, 1)] == [-3.3, 11.9]


def test_climate_version_robustness():
    C = pd.read_csv(TAB / "climate_version_robustness.csv")
    v = C[(C.predictor == "precip_mm_fs") & C.test.str.startswith("Spearman")].set_index("response")
    assert [r(v.loc[y, "rho"], 2) for y in ("events", "area_km2", "CO2")] == [-0.65, -0.71, -0.67]
    pr = C[(C.predictor == "precip_mm_fs") & C.test.str.startswith("partial")].set_index("response")
    assert [r(pr.loc[y, "rho"], 2) for y in ("events", "area_km2", "CO2")] == [-0.59, -0.63, -0.64]
    assert pr.p.max() < 0.034


def test_viirs_increment_independent():
    V = pd.read_csv(TAB / "viirs_increment_independent.csv")
    q = V[(V.years.str.startswith("2012-2023")) & (V.y == "CO2_inc_pct")].set_index("x")
    assert r(q.loc["MODIS events (shared denominator)", "rho"], 2) == -0.59
    assert r(q.loc["MapBiomas Fire area", "rho"], 2) == -0.34 and r(q.loc["MapBiomas Fire area", "p"], 2) == 0.28
    assert r(q.loc["MCD64A1 area", "rho"], 2) == -0.03


def test_municipal_scenario():
    M = pd.read_csv(TAB / "emission_scenario_mapped_area_municipal.csv").set_index("year")
    assert r(M.loc[2024, "CO2_mb_state_scale_t"] / 1e6, 3) == 0.275
    assert r(M.loc[2024, "CO2_mb_municipal_scale_t"] / 1e6, 3) == 0.254
    assert r(M.mb_municipal_over_state.min(), 2) == 0.77 and r(M.mb_municipal_over_state.max(), 2) == 0.92
    assert r(M.CO2_mb_municipal_scale_t.min() / 1e6, 2) == 0.09 and r(M.CO2_mb_municipal_scale_t.max() / 1e6, 2) == 0.38


def test_sensitivity_factors():
    F = pd.read_csv(TAB / "sensitivity_factors.csv")
    g = F.groupby("item").value
    assert [r(g.min()["interannual"], 2), r(g.max()["interannual"], 2)] == [0.55, 1.58]
    assert [r(g.min()["modis_only"], 2), r(g.max()["modis_only"], 2)] == [0.64, 0.72]
    assert r(g.max()["finn_v15"], 2) == 1.94
    assert [r(g.min()["mapbiomas_area"], 3), r(g.max()["mapbiomas_area"], 3)] == [0.027, 0.075]
