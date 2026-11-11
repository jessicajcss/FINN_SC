"""Values introduced in the revision round (co-authors' review of manuscript v.6, 2026-10-19; manuscript v.6.1 and
Supplementary Material v3.3). Tables written by python/analysis/a11_coauthor_review.py and
R/analysis/kde_sensitivity_annual.R.
"""
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_seasonality_shares():
    s = pd.read_csv(TAB / "seasonality_by_mesoregion.csv").set_index("region")
    assert r(s.loc["Santa Catarina", "jul_nov"], 1) == 72.1          # manuscript section 2.8
    assert r(s.loc["Santa Catarina", "jul_sep"], 1) == 60.0          # sections 2.8 and 4
    assert (r(s.loc["Serrana", "jul_sep"], 1), r(s.loc["Serrana", "jul_nov"], 1)) == (74.9, 84.0)
    assert r(s.loc["Serrana", "m08"], 1) == 49.1
    assert int(s.loc["Sul Catarinense", "peak_month"]) == 8


def test_largest_area_2020():
    m = pd.read_csv(TAB / "max_area_2020.csv")
    assert m.municipality.iloc[0] == "Lages" and r(m.finn_area_km2.iloc[0], 0) == 407 and r(m.share_pct.iloc[0], 1) == 9.8
    assert m.municipality.iloc[1] == "São Joaquim" and r(m.finn_area_km2.iloc[1], 0) == 201


def test_mesoregion_area_metrics():
    m = pd.read_csv(TAB / "mesoregion_area_metrics_2025.csv").set_index("mesorregiao")
    assert r(m.loc["Serrana", "area_share_pct"], 1) == 23.3 and r(m.loc["Serrana", "events_share_pct"], 1) == 45.6
    assert [r(m.loc[k, "co2_t_per_km2"], 0) for k in ["Serrana", "Oeste Catarinense", "Sul Catarinense",
                                                      "Grande Florianópolis"]] == [74, 34, 27, 14]
    assert r(m.loc["Serrana", "finn_area_pct_of_meso"], 1) == 4.8
    assert r(m.loc["Serrana", "co2_t_per_event"], 0) == 708


def test_mesoregion_density_tests():
    t = pd.read_csv(TAB / "mesoregion_density_tests.csv")
    kw = t[(t.test == "kruskal") & (t.response == "2025")].iloc[0]
    assert r(kw.stat, 1) == 68.2 and kw.p < 0.001
    d = t[(t.test == "dunn") & (t.response == "2025")]
    sul = d[((d.group1 == "Serrana") & (d.group2 == "Sul Catarinense"))].iloc[0]
    assert r(sul.p_holm, 2) == 0.21
    others = d[(d.group1 == "Serrana") | (d.group2 == "Serrana")]
    assert (others[~((others.group1 == "Sul Catarinense") | (others.group2 == "Sul Catarinense"))].p_holm < 0.001).all()
    sem = t[(t.test == "sem_vs_Serrana") & (t.response == "mean_2012_2025")].set_index("group1")
    assert sem.loc["Vale do Itajaí", "p"] < 0.05 and (sem.drop("Vale do Itajaí").p > 0.05).all()


def test_climate_without_el_nino_years():
    c = pd.read_csv(TAB / "climate_correlations_sensitivity.csv")
    s = c[(c.excluded == "2015 2023") & (c.preditor == "precip_mm_fs")].set_index("resposta")
    assert [r(s.loc[k, "rho"], 2) for k in ["eventos", "area_FINN", "CO2"]] == [-0.56, -0.60, -0.60]
    assert (s.loc[["eventos", "area_FINN", "CO2"], "p_holm"] >= 0.19).all()
    a = c[(c.excluded == "none") & (c.preditor == "precip_mm_fs") & (c.resposta == "eventos")].iloc[0]
    assert (r(a.rho_loo_min, 2), r(a.rho_loo_max, 2)) == (-0.80, -0.62)


def test_viirs_increment_vs_modis_activity():
    from scipy import stats
    v = pd.read_csv(TAB / "viirs_increment.csv")
    rho, p = stats.spearmanr(v.CO2_inc_pct, v.modis_events)
    assert (r(rho, 2), r(p, 3)) == (-0.59, 0.045)


def test_inventory_comparison_and_decomposition():
    c = pd.read_csv(TAB / "inventory_comparison_2020.csv").set_index("inventory")
    assert int(c.loc["FINN v1.5, 2020", "count"]) == 4609 and r(c.loc["FINN v1.5, 2020", "CO2_Mt"], 2) == 12.88
    assert r(c.loc["FINN v2.5 MODIS+VIIRS, 2020", "CO2_t_per_km2"], 0) == 1599
    d = pd.read_csv(TAB / "inventory_decomposition_2020.csv").set_index("type")
    cf_a = (d.area_v25_km2 * d.co2_t_per_km2_v15).sum() / 1e6
    cf_b = (d.area_v15_km2 * d.co2_t_per_km2_v25).sum() / 1e6
    assert (r(cf_a, 2), r(cf_b, 2)) == (9.83, 7.90)


def test_mesoregion_density_2020_2025():
    from scipy import stats
    q = pd.read_csv(TAB / "mesoregion_density_2020_2025.csv").set_index("mesorregiao")
    assert r(q.loc["Serrana", "v15_records_2020_per_100km2"], 2) == 9.23
    assert r(q.loc["Serrana", "v15_records_2020_share_pct"], 1) == 44.7
    rho = stats.spearmanr(q.v15_records_2020_per_100km2, q.v251_mv_events_2025_per_100km2)[0]
    assert r(rho, 2) == 0.94


def test_recurrent_sites_and_silviculture():
    x = pd.read_csv(TAB / "recurrent_sites_silviculture.csv").set_index("excluded_sites_min_days")
    assert [r(x.loc[k, "rho_silviculture"], 2) for k in (0, 8, 4)] == [0.42, 0.41, 0.37]
    assert [r(x.loc[k, "events_removed_pct"], 1) for k in (8, 4)] == [1.7, 9.0]


def test_sul_agriculture_split():
    s = pd.read_csv(TAB / "sul_agriculture_split.csv").set_index("group")
    hi = s.loc["agriculture >= 40%"]
    assert int(hi.municipalities) == 21 and r(hi.mar_jun_pct, 1) == 49.4 and r(hi.finn_cropland_area_pct, 1) == 28.2


def test_landcover_2019_vs_2023():
    t = pd.read_csv(TAB / "landcover_2019_vs_2023.csv")
    assert t.difference_pp.abs().max() <= 1.33


@pytest.mark.skipif(not (TAB / "kde_annual_summary.csv").is_file(), reason="run R/analysis/kde_sensitivity_annual.R")
def test_kde_bandwidths_and_annual_maps():
    a = pd.read_csv(TAB / "kde_2025_sensitivity_mesoregion.csv")
    s = a[a.meso == "Serrana"].set_index("selector")
    assert (s.rank_mean == 1).all()
    assert r(s.loc["ppl", "share_top1"] * 100, 1) == 93.6 and r(s.share_top1.min() * 100, 1) == 66.7
    b = pd.read_csv(TAB / "kde_annual_summary.csv")
    top = b.loc[b.groupby("year").mean_density.idxmax()].set_index("year").meso
    assert top.loc[2012] == "Sul Catarinense" and (top.loc[2013:] == "Serrana").all()
    sr = b[b.meso == "Serrana"].set_index("year").share_top1 * 100
    assert (r(sr.loc[2014:].min(), 1), r(sr.loc[2014:].max(), 1)) == (63.6, 98.1)


def test_simplified_mesh_for_earth_engine():
    import geopandas as gpd
    s = gpd.read_file(ROOT / "gee" / "SC_municipios_2024_simplified.gpkg")
    assert len(s) == 295 and s.CD_MUN.is_unique and str(s.crs.to_epsg()) == "4326"
    assert s.groupby("mesorregiao").size().to_dict() == {"Grande Florianópolis": 21, "Norte Catarinense": 26,
                                                          "Oeste Catarinense": 118, "Serrana": 30,
                                                          "Sul Catarinense": 46, "Vale do Itajaí": 54}
    assert len(s.to_json()) < 5e6          # well below the 10 MB limit of an Earth Engine request
