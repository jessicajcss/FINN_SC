"""Values introduced in the revision round (Earth Engine notebooks of the co-authors' review, run by the authors on
2026-10-21; manuscript v.6.2 and Supplementary Material v3.4). Tables written by python/analysis/a12_gee_review_outputs.py
and tools/study_area_map.py.
"""
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"
EXT = ROOT / "data" / "external"


def r(x, k):
    return round(float(x), k)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_inputs_are_the_authors_exports():
    # SHA-256 printed by the notebooks in Colab (gee/*_run_2026-10-21.ipynb)
    assert sha(EXT / "mcd64a1_SC_municipal_km2_2012_2024.csv").startswith("48f3c2f94005cdd3")
    assert sha(EXT / "era5land_SC_serrana_monthly_2012_2025.csv").startswith("f459206e2eb413ff")


def test_mcd64a1_state_series():
    s = pd.read_csv(TAB / "mcd64a1_comparison_state.csv").set_index("year")
    assert (r(s.mcd_km2.min(), 1), r(s.mcd_km2.max(), 1)) == (35.5, 238.2)
    assert (s.mcd_km2 < s.mb_km2).all()
    assert (r((s.mcd_km2 / s.mb_km2).min() * 100, 0), r((s.mcd_km2 / s.mb_km2).max() * 100, 0)) == (32, 78)
    assert (int(s.municipalities_mcd.min()), int(s.municipalities_mcd.max())) == (22, 41)
    assert (int(s.municipalities_mb.min()), int(s.municipalities_mb.max())) == (116, 194)


def test_mcd64a1_summary():
    m = pd.read_csv(TAB / "mcd64a1_comparison_summary.csv").set_index("metric").value
    assert r(m.median_finn_over_mcd, 1) == 34.4 and r(m.median_mb_over_mcd, 1) == 1.9 and r(m.median_finn_over_mb, 1) == 17.2
    assert r(m.state_pearson_mcd_mb, 2) == 0.87 and m.state_pearson_p_mcd_mb < 0.001
    assert r(m.state_pearson_mcd_finn, 2) == 0.62 and r(m.state_pearson_p_mcd_finn, 3) == 0.023
    assert (r(m.municipal_spearman_min_mcd_finn, 2), r(m.municipal_spearman_max_mcd_finn, 2)) == (0.21, 0.44)
    assert (r(m.municipal_total_spearman_mcd_mb, 2), r(m.municipal_total_spearman_mcd_finn, 2)) == (0.66, 0.55)
    assert (r(m.serrana_share_pct_mcd, 1), r(m.serrana_share_pct_mb, 1), r(m.serrana_share_pct_finn, 1)) == (68.8, 65.6, 44.4)
    assert (r(m.change_2020_2023_pct_mcd, 1), r(m.change_2023_2024_pct_mcd, 1)) == (-60.7, 211.6)


def test_climate_serrana():
    c = pd.read_csv(TAB / "climate_serrana_correlations.csv")
    c = c[c.predictor == "precip_mm"].set_index(["response", "climate", "period"]).sort_index()
    assert r(c.loc[("State events", "Santa Catarina", "Jul-Nov"), "rho"], 2) == -0.68          # = a06 (manuscript)
    assert r(c.loc[("State events", "Serrana", "Jul-Nov"), "rho"], 2) == -0.63
    assert r(c.loc[("State events", "Serrana", "Jul-Nov"), "p_holm"], 2) == 0.05
    s = c.loc[("State events", "Santa Catarina", "Jul-Sep")]
    assert (r(s.rho, 2), r(s.p_holm, 3)) == (-0.72, 0.014)
    assert (r(s.rho_without_2015_2023, 2), r(s.p_without_2015_2023, 3)) == (-0.60, 0.039)
    v = c.loc[("Serrana events", "Serrana")]
    assert (r(v.loc["Jul-Nov", "rho"], 2), r(v.loc["Jul-Sep", "rho"], 2)) == (-0.49, -0.55)
    assert (v.p_holm > 0.15).all()
    assert r(c.loc[("State events", "Serrana", "Jul-Nov"), "rho_without_2015_2023"], 2) == -0.47


def test_landcover_2023_figure1():
    f = pd.read_csv(TAB / "landcover_figure1_2019_2023.csv").set_index("group")
    assert [r(f.loc[g, "2023"], 1) for g in ("forest", "mosaic", "temporary_crops", "silviculture", "pasture",
                                              "grassland", "urban")] == [39.2, 18.1, 12.9, 10.8, 8.6, 5.8, 2.4]
    assert f.difference_pp.abs().max() < 1.35
    m = pd.read_csv(TAB / "landcover2023_mesoregion.csv").set_index(["group", "mesorregiao"])
    assert r(m.loc[("grass", "Serrana"), "pct_of_group"], 1) == 97.2 and r(m.loc[("grass", "Serrana"), "pct_of_mesoregion"], 1) == 24.0
    assert r(m.loc[("silv", "Serrana"), "pct_of_group"], 1) == 37.5
    assert r(m.loc[("crop", "Oeste Catarinense"), "pct_of_group"], 1) == 46.3
    assert r(m.loc[("mosaic", "Oeste Catarinense"), "pct_of_group"], 1) == 38.0
    assert (r(m.loc[("forest", "Grande Florianópolis"), "pct_of_mesoregion"], 1),
            r(m.loc[("forest", "Vale do Itajaí"), "pct_of_mesoregion"], 1)) == (59.3, 53.4)
