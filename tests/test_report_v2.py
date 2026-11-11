"""Golden values printed only in the inventory report v2 (inventario_queimadas_v2, 2026-10-03) and not
already covered by test_results_golden.py. Section numbers refer to the report (R).
The tests read results/ (run `python python/run_analysis.py` first)."""
import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"
LOG = ROOT / "results" / "logs"
EXT = ROOT / "data" / "external"
pytestmark = pytest.mark.skipif(not (TAB / "events.csv.gz").is_file(), reason="run the analysis first")


def r(x, d):
    return round(float(x), d)


@pytest.fixture(scope="module")
def mun():
    return pd.read_csv(TAB / "municipal_2025.csv").set_index("municipio")


def test_state_area_and_co2_changes():
    """R Resumo, 3 and 4: area -4,3% (2024 to 2025); CO2 2,30 Mt (2015) to 6,63 Mt (2020); about -50% 2020 to 2023;
    Spearman events vs area 0,996."""
    s = pd.read_csv(TAB / "series_state_all_products.csv")
    mv = s[s.sensor == "MODIS+VIIRS"].set_index("year")
    assert r(100 * (mv.area_km2[2025] / mv.area_km2[2024] - 1), 1) == -4.3
    assert (r(mv.CO2[2015] / 1e6, 2), r(mv.CO2[2020] / 1e6, 2), r(mv.CO2[2025] / 1e6, 2)) == (2.30, 6.63, 3.55)
    assert r(100 * (mv.CO2[2023] / mv.CO2[2020] - 1), 0) == -50
    assert "rho = 0.996 (n = 14)" in (LOG / "a02_series_trends.txt").read_text(encoding="utf-8")


def test_municipal_shares_and_densities(mun):
    """R 3 and 4: Lages + Sao Joaquim = 15,0% of events, 10,3% of CO2, 22,1% of the Serrana CO2; top-3 = 951 events
    (18,6%); highest event densities."""
    ev, co2 = mun.events, mun.CO2
    two = ["Lages", "São Joaquim"]
    assert (r(100 * ev[two].sum() / ev.sum(), 1), r(100 * co2[two].sum() / co2.sum(), 1)) == (15.0, 10.3)
    serr = co2[mun.mesorregiao == "Serrana"].sum()
    assert r(100 * co2[two].sum() / serr, 1) == 22.1
    top3 = ev.sort_values(ascending=False).head(3)
    assert top3.index.tolist() == ["Lages", "São Joaquim", "Capão Alto"] and top3.sum() == 951
    assert r(100 * top3.sum() / ev.sum(), 1) == 18.6
    at = pd.read_csv(EXT / "sc_municipios_2024_atributos.csv").set_index("NM_MUN")
    dens = (100 * ev / at.AREA_KM2.reindex(ev.index)).round(1).sort_values(ascending=False)
    assert dens.head(4).to_dict() == {"São Joaquim": 18.0, "Cerro Negro": 17.2, "Lages": 16.3, "Painel": 16.3}
    assert r(mun.NMOC["Lages"], 0) == 5160


def test_profiles_co2_per_event():
    """R Resumo, 4 and Appendix A: CO2 per event (2025) and FINN temperate-forest share by municipality."""
    i = pd.read_csv(TAB / "intensity_per_event_2025.csv").set_index("municipio")
    cpe = i.CO2_per_event.round(0).astype(int)
    assert {k: cpe[k] for k in ["São Joaquim", "Lages", "Painel", "Curitibanos", "São José do Cerrito", "Lebon Régis"]} == \
        {"São Joaquim": 415, "Lages": 526, "Painel": 404, "Curitibanos": 1046, "São José do Cerrito": 1103, "Lebon Régis": 2118}
    sh = (100 * i.finn_forest4_share).round(1)
    assert (sh["Lebon Régis"], sh["Curitibanos"], sh["São José do Cerrito"], sh["São Joaquim"], sh["Lages"]) == (72.7, 48.3, 36.8, 12.0, 15.5)
    assert r(i.CO2_per_event["Lebon Régis"] / i.CO2_per_event["São Joaquim"], 1) == 5.1
    log = (LOG / "a08_report_indicators.txt").read_text(encoding="utf-8")
    for s in ("median 478 t (IQR 315-896)", ">= 5 screened events: 192", "state mean 693 t", "rho = 0.67",
              "0.744 (n = 295", "top-10 municipalities hold 34.8%", "21 municipalities hold half",
              "GENVEG 1: n = 2920; CO2 per event median 127 t", "GENVEG 4: n = 1363; CO2 per event median 461 t",
              "range 28.2-34.8, median 32.2"):
        assert s in log, s
    med = [float(x) for x in re.findall(r"area median (\d\.\d+) km2", log)]
    assert len(med) == 4 and r(min(med), 2) == 0.12 and r(max(med), 2) == 0.14


def test_mapbiomas_area_per_event_and_mesoregions():
    """R Resumo and 4: MapBiomas area per FINN event (2012-2024) and mesoregion shares of burned area."""
    pe = pd.read_csv(TAB / "mapbiomas_area_per_event.csv").set_index("NM_MUN").mb_km2_per_event
    assert (r(pe["Lebon Régis"], 3), r(pe["Curitibanos"], 3), r(pe["São José do Cerrito"], 3)) == (0.021, 0.015, 0.004)
    assert (r(pe["São Joaquim"], 3), r(pe["Lages"], 3)) == (0.054, 0.082)
    log = (LOG / "a05_mapbiomas_comparison.txt").read_text(encoding="utf-8")
    assert "'Serrana': 44.4" in log and "'Serrana': 65.6" in log


def test_climate_report():
    """R 4, 7 and 8: CO2 vs fire-season climate (Spearman, Holm), wettest seasons, 2024 vs 2025 precipitation."""
    c = pd.read_csv(TAB / "climate_correlations.csv").set_index(["resposta", "preditor"]).loc["CO2"]
    assert (r(c.rho["precip_mm_fs"], 2), r(c.rho["soil_moist_fs"], 2), r(c.p_holm["precip_mm_fs"], 3), r(c.p_holm["soil_moist_fs"], 3)) == (-0.71, -0.70, 0.022, 0.022)
    assert (r(c.rho["VPD_kPa_fs"], 2), r(c.p["VPD_kPa_fs"], 3), r(c.p_holm["VPD_kPa_fs"], 3)) == (0.56, 0.035, 0.106)
    assert (r(c.rho["ONI_fs"], 2), r(c.p["ONI_fs"], 3), r(c.rho_dif["ONI_fs"], 2), r(c.p_dif["ONI_fs"], 3)) == (-0.51, 0.064, -0.65, 0.017)
    cl = pd.read_csv(EXT / "era5land_oni_SC_fire_season_2012_2025.csv").set_index("year")
    assert (round(cl.precip_mm_fs[2025]), round(cl.precip_mm_fs[2024])) == (718, 638)
    assert sorted(cl.precip_mm_fs.nlargest(2).index.tolist()) == [2015, 2023] and (cl.ONI_fs[[2015, 2023]] > 0.5).all()
    assert "Jul-Nov 72.1%" in (LOG / "a03_municipal_mesoregion.txt").read_text(encoding="utf-8")


def test_landcover_co2_per_event():
    """R 4 (box), 8 and Appendix A: CO2 per event vs land cover, 2012-2025."""
    s = pd.read_csv(TAB / "landcover_spearman.csv").set_index(["resposta", "cobertura"]).loc["CO2_per_event"]
    assert int(s.n.iloc[0]) == 288                  # 295 municipalities (277-municipality file: 276)
    assert (r(s.rho["finn_forest4_share"], 2), r(s.rho["silviculture"], 2), r(s.rho["agriculture"], 2)) == (0.85, 0.68, -0.62)
    sem = pd.read_csv(TAB / "landcover_sem.csv")
    k = sem[(sem.response == "CO2_per_event") & (sem.W == "knn6")].set_index("term")
    assert (r(k.moran_ols.iloc[0], 2), r(k.moran_sem.iloc[0], 3), r(k.p_moran_sem.iloc[0], 2), r(k.r2_ols.iloc[0], 3)) == (0.21, -0.004, 0.49, 0.622)
    assert (r(k.b_sem["silviculture"], 2), r(k.effect_10pp_pct["silviculture"], 1), r(k.effect_10pp_pct["agriculture"], 1)) == (2.44, 27.6, -10.9)
    assert (k.p_sem[["silviculture", "agriculture"]] < 0.001).all()
    assert "silviculture fraction vs FINN temperate-forest share of the municipal FINN area: rho = 0.53" in \
        (LOG / "a07_landcover.txt").read_text(encoding="utf-8")


def test_kde_report():
    """R 3 and 8: mean density by mesoregion, bandwidth sensitivity and location of the maximum."""
    p = TAB / "kde_2025_grid.csv"
    if not p.is_file():
        pytest.skip("run R/analysis/kde_events.R")
    g = pd.read_csv(p)
    m = g.groupby("meso").ev_100km2.mean().round(1)
    assert (m["Serrana"], m["Sul Catarinense"], m["Oeste Catarinense"], m["Norte Catarinense"], m["Vale do Itajaí"], m["Grande Florianópolis"]) == \
        (10.4, 5.4, 4.6, 3.0, 3.0, 2.3)
    log = (LOG / "kde_2025_summary.txt").read_text(encoding="utf-8")
    rs = {k: float(v.replace(",", ".")) for k, v in re.findall(r"sensitivity (\w+) \(sigma \d+ m\): Pearson r = ([\d,]+)", log)}
    within = [rs[k] for k in ("CvL", "fixed_2km", "fixed_4km", "fixed_8km")]
    assert (r(min(within), 2), r(max(within), 2)) == (0.83, 0.97)
    top = g.loc[g.ev_100km2.idxmax()]
    import geopandas as gpd
    from shapely.geometry import Point
    shp = gpd.read_file(ROOT / "data" / "inputs" / "SC_Municipios_2024.shp", encoding="cp1252")
    assert shp[shp.contains(Point(top.lon, top.lat))].NM_MUN.tolist() == ["Lages"]


def test_screening_2025_and_ef():
    """R 2: 39 events of 2025 flagged, all in Sideropolis; emission factors within 0,3% of Wiedinmyer et al. (2023)."""
    f = pd.read_csv(TAB / "screening_flagged_detections.csv")
    f25 = f[(f.year == 2025) & (f.sensor == "MODIS+VIIRS")]
    assert set(f25.NM_MUN) == {"Siderópolis"}
    assert "flagged events 39" in (LOG / "kde_2025_summary.txt").read_text(encoding="utf-8")
    e = pd.read_csv(TAB / "emission_factor_check.csv")
    assert (e.ratio - 1).abs().max() < 0.003
