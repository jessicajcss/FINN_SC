"""Golden-value tests: every number below is printed in the manuscript (v5, "Artigo_Queimadas_v5")
or in the inventory report (v2, "inventario_queimadas_v2"), with the rounding used in the text.
The tests read results/ (run `make analysis` or `python python/run_analysis.py` first).
Section references: M = manuscript v5; R = report v2; S = supplementary material v2 (section and figure numbers of
manuscript v3.2: docs/results_map.md).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"
pytestmark = pytest.mark.skipif(not (TAB / "events.csv.gz").is_file(), reason="run the analysis first")


def r(x, d):
    return round(float(x), d)


@pytest.fixture(scope="module")
def st():
    return pd.read_csv(TAB / "state_counts.csv")


@pytest.fixture(scope="module")
def mv(st):
    return st[st.sensor == "MODIS+VIIRS"].set_index("year")


# ---------------------------------------------------------------- counting units (M 2.6; R 3)
def test_2025_records_detections_events(mv):
    assert (mv.records[2025], mv.detections[2025], mv.events[2025], mv.events_screened[2025]) == (8581, 5489, 5160, 5121)


def test_screened_events_series(mv):
    exp = [6441, 5810, 4852, 3549, 8296, 6590, 5441, 6561, 8212, 6825, 5233, 4940, 5365, 5121]
    assert mv.events_screened.loc[2012:2025].tolist() == exp
    e = mv.events_screened
    assert (r(100 * (e[2023] / e[2020] - 1), 1), r(100 * (e[2024] / e[2023] - 1), 1), r(100 * (e[2025] / e[2024] - 1), 1)) == (-39.8, 8.6, -4.5)
    assert (round(e.loc[2022:2025].mean()), round(e.loc[2022:2025].std(ddof=1))) == (5165, 180)
    assert round(e.loc[2012:2025].mean()) == 5945


def test_screening_summary():
    s = pd.read_csv(TAB / "screening_summary.csv")
    one = s[s.R_km == 1.0]
    assert one.flagged_events.min() == 0 and one.flagged_events.max() == 61
    assert r(one.flagged_pct.max(), 1) == 0.9 and int(one.loc[one.flagged_pct.idxmax(), "year"]) == 2021
    assert r(one.co2_pct.max(), 1) == 2.5 and int(one.loc[one.co2_pct.idxmax(), "year"]) == 2020
    assert r(s[s.R_km == 0.75].flagged_pct.max(), 1) == 0.8 and r(s[s.R_km == 1.5].flagged_pct.max(), 1) == 1.2
    sid = one[one.year >= 2021].municipalities.fillna("")
    assert all("Siderópolis" in x for x in sid)


# ---------------------------------------------------------------- Table 2 and trends (M 3; R 3)
TABLE2 = {2012: [4152972, 247588, 29115, 13960, 6150, 10819, 4426, 111241, 1642, 2487],
          2016: [5938838, 350668, 41608, 19971, 8871, 15120, 6196, 156333, 2370, 3581],
          2020: [6631365, 423900, 50584, 24703, 8726, 18750, 7849, 190737, 2647, 4153],
          2024: [3676750, 231746, 27741, 13458, 4954, 10129, 4221, 104198, 1417, 2310],
          2025: [3554771, 226368, 27070, 13153, 4711, 9944, 4151, 102019, 1368, 2240]}


def test_table2():
    t = pd.read_csv(TAB / "table2_state_emissions_2012_2025.csv", index_col=0)
    for y, vals in TABLE2.items():
        assert t.loc[y].round(0).astype(int).tolist() == vals


def test_emission_changes():
    t = pd.read_csv(TAB / "table2_state_emissions_2012_2025.csv", index_col=0)
    up = 100 * (t.loc[2024] / t.loc[2023] - 1)
    dn = 100 * (t.loc[2025] / t.loc[2024] - 1)
    assert (r(up.min(), 1), up.idxmin(), r(up.max(), 1), up.idxmax()) == (9.8, "NH3", 11.2, "NOXasNO")
    assert (r(dn.max(), 1), dn.idxmax(), r(dn.min(), 1), dn.idxmin()) == (-1.7, "NH3", -4.9, "NOXasNO")
    assert (r(dn.CO2, 1), r(dn.CO, 1), r(dn.PM25, 1)) == (-3.3, -2.3, -2.4)
    assert r(up.CO2, 1) == 10.6
    assert t.idxmax().to_dict() == {c: (2016 if c == "NOXasNO" else 2020) for c in t.columns}


def test_viirs_effect():
    v = pd.read_csv(TAB / "viirs_effect.csv")
    a = v[v.version == "v2.5"].set_index("year")
    assert (r(a.events_ratio.min(), 1), a.events_ratio.idxmin(), r(a.events_ratio.max(), 1), a.events_ratio.idxmax()) == (3.6, 2021, 4.8, 2014)
    assert (r(a.area_km2_inc_pct.min(), 1), r(a.area_km2_inc_pct.max(), 1)) == (40.7, 59.1)
    assert (r(a.CO2_inc_pct.min(), 1), r(a.CO2_inc_pct.max(), 1)) == (39.6, 56.2)
    b = v[v.version == "v2.5.1"].set_index("year")
    assert (r(b.events_ratio[2022], 1), r(b.events_ratio[2023], 1)) == (3.9, 4.0)
    assert (r(b.CO2_inc_pct[2022], 1), r(b.CO2_inc_pct[2023], 1)) == (44.4, 43.1)


def test_mann_kendall():
    m = pd.read_csv(TAB / "mann_kendall.csv").set_index(["variable", "period"])
    full = m.xs("2012-2025", level="period")
    assert (r(full.tau.min(), 2), r(full.tau.max(), 2)) == (-0.12, -0.03) and r(full.p.min(), 2) == 0.58
    assert (round(full.sen["events"]), round(full.sen["area_km2"]), round(full.sen["CO2_t"]), round(full.sen["PM25_t"])) == (-46, -35, -35265, -123)
    assert r(m.xs("2012-2021", level="period").p.min(), 2) == 0.21


# ---------------------------------------------------------------- 2025 municipalities and mesoregions (M 3; R 3-4)
@pytest.fixture(scope="module")
def mun():
    return pd.read_csv(TAB / "municipal_2025.csv").set_index("municipio")


def test_municipal_events_2025(mun):
    e = mun.events.sort_values(ascending=False)
    assert (e > 0).sum() == 277 and (e >= 100).sum() == 9
    assert e.head(9).to_dict() == {"Lages": 429, "São Joaquim": 340, "Capão Alto": 182, "Água Doce": 169,
                                   "Bom Jardim da Serra": 144, "São José do Cerrito": 142, "Curitibanos": 137,
                                   "Painel": 120, "Campos Novos": 110}
    me = pd.read_csv(TAB / "municipal_events_by_year.csv")
    e24 = me[me.year == 2024].set_index("mun_event").events
    assert (e24 >= 100).sum() == 10 and (e24["Campo Belo do Sul"], e24["Lebon Régis"], e24["Curitibanos"]) == (114, 108, 83)
    assert (r(100 * (429 / e24["Lages"] - 1), 1), r(100 * (340 / e24["São Joaquim"] - 1), 1)) == (-31.5, -20.7)


def test_table3_and_shares():
    t = pd.read_csv(TAB / "mesoregion_2025.csv", index_col=0)
    assert t.loc["Serrana", ["CO2", "PM25", "NOXasNO", "NMOC"]].round(0).astype(int).tolist() == [1652580, 12204, 2300, 45813]
    assert t.loc["Oeste Catarinense", ["CO2", "PM25"]].round(0).astype(int).tolist() == [940032, 7156]
    assert t.loc["Grande Florianópolis", "CO2"].round(0) == 99673
    sp = ["CO2", "CO", "PM25", "OC", "NOXasNO", "CH4", "NH3", "NMOC", "BC", "SO2"]
    sh = 100 * t[sp] / t[sp].sum()
    so = sh.loc["Serrana"] + sh.loc["Oeste Catarinense"]
    assert (r(sh.loc["Serrana", "CO2"], 1), r(so.CO2, 1), r(so.min(), 1), r(so.max(), 1)) == (46.5, 72.9, 70.5, 75.4)
    assert (int(t.events["Serrana"]), int(t.events["Oeste Catarinense"])) == (2333, 1255)
    assert (r(t.PM25["Serrana"] / t.PM25["Oeste Catarinense"], 1), r(t.PM25["Serrana"] / t.PM25["Vale do Itajaí"], 1)) == (1.7, 5.3)


def test_area_and_leaders(mun):
    assert r(mun.area_km2.sum(), 0) == 2242
    a = mun.area_km2.round(1)
    assert (a["Lages"], a["São Joaquim"], a["São José do Cerrito"], a["Água Doce"], a["Capão Alto"]) == (181.1, 121.3, 91.8, 90.2, 79.8)
    p = mun.pct_area_municipio.round(1)
    assert (p["São José do Cerrito"], p["Lages"], p["Água Doce"], p["São Joaquim"], p["Capão Alto"]) == (9.7, 6.9, 6.8, 6.4, 6.0)
    lead = {c: mun[c].idxmax() for c in ["CO2", "CO", "PM25", "NOXasNO", "NMOC", "BC", "SO2", "OC", "CH4", "NH3"]}
    assert all(lead[c] == "Lages" for c in ["CO2", "CO", "PM25", "NOXasNO", "NMOC", "BC", "SO2"])
    assert all(lead[c] == "Lebon Régis" for c in ["OC", "CH4", "NH3"])
    assert mun.CO2.sort_values(ascending=False).index[:5].tolist() == ["Lages", "São José do Cerrito", "Lebon Régis", "Curitibanos", "São Joaquim"]
    pm = mun.PM25.sort_values(ascending=False)
    assert pm[pm > 500].index.tolist() == ["Lages", "Lebon Régis", "Curitibanos", "São José do Cerrito", "São Joaquim",
                                           "Capão Alto", "Água Doce", "Caçador", "Cerro Negro", "Correia Pinto"]


# ---------------------------------------------------------------- vegetation partition (M 3; R 4)
def test_genveg():
    g = pd.read_csv(TAB / "genveg_partition.csv").set_index(["period", "GENVEG"])
    a = g.loc["2012-2025"]
    assert (r(a.area_pct[1], 1), r(a.area_pct[4], 1), r(a.area_pct[2], 1), r(a.area_pct[9], 1)) == (46.3, 31.9, 20.2, 1.6)
    assert (r(a.CO2_pct[4], 1), r(a.PM25_pct[4], 1), r(a.biomassa_kg_m2[4], 2), r(a.biomassa_kg_m2[1], 2)) == (55.0, 74.1, 1.73, 0.54)
    b = g.loc["2025"]
    assert (r(b.area_pct[4], 1), r(b.CO2_pct[4], 1), r(b.PM25_pct[4], 1)) == (34.4, 59.2, 77.3)


# ---------------------------------------------------------------- MapBiomas (M 2.7, 3; R 2, 4, 8)
def test_mapbiomas():
    from scipy import stats
    d = pd.read_csv(TAB / "mapbiomas_state.csv", index_col=0)
    assert (r(d.ratio.median(), 1), r(d.ratio.min(), 1), r(d.ratio.max(), 1)) == (17.2, 13.3, 37.7)
    assert (r(stats.pearsonr(d.finn, d.mb)[0], 2), r(stats.spearmanr(d.finn, d.mb)[0], 2)) == (0.77, 0.75)
    e = d.drop(index=2012)
    assert (r(stats.pearsonr(e.finn, e.mb)[0], 2), r(stats.spearmanr(e.finn, e.mb)[0], 2)) == (0.85, 0.88)
    m = pd.read_csv(TAB / "mapbiomas_agreement_by_year.csv")
    assert (r(m.spearman.min(), 2), r(m.spearman.max(), 2)) == (0.47, 0.73)


# ---------------------------------------------------------------- climate (M 3; R 4)
def test_climate():
    c = pd.read_csv(TAB / "climate_correlations.csv").set_index(["resposta", "preditor"])
    ev = c.loc["eventos", "precip_mm_fs"]
    assert (r(ev.rho, 2), r(ev.p, 3), r(ev.p_holm, 3)) == (-0.68, 0.007, 0.035)
    assert (r(c.loc[("area_FINN", "precip_mm_fs"), "rho"], 2), r(c.loc[("CO2", "precip_mm_fs"), "rho"], 2)) == (-0.71, -0.71)
    oni = c.xs("ONI_fs", level="preditor").loc[["eventos", "area_FINN", "CO2"]]
    assert (r(oni.rho.min(), 2), r(oni.rho.max(), 2), r(oni.rho_dif.min(), 2), r(oni.rho_dif.max(), 2)) == (-0.53, -0.51, -0.65, -0.58)
    vpd = c.xs("VPD_kPa_fs", level="preditor").loc[["eventos", "area_FINN", "CO2"]]
    assert (r(vpd.rho.min(), 2), r(vpd.rho.max(), 2)) == (0.48, 0.56)
    mb = c.loc["area_MapBiomas"]
    assert (r(mb.rho["precip_mm_fs"], 2), r(mb.p["precip_mm_fs"], 2), r(mb.rho["ONI_fs"], 2), r(mb.p["ONI_fs"], 2)) == (-0.48, 0.10, -0.50, 0.08)


# ---------------------------------------------------------------- land cover (M 3; R 4)
def test_landcover():
    s = pd.read_csv(TAB / "landcover_spearman.csv").set_index(["resposta", "cobertura"])
    d = s.loc["ev_1225_100km2_yr"]
    # all 295 municipalities (MapBiomas Collection 10.1); 277-municipality file: 0.38, -0.24, 0.10, 0.08
    assert (r(d.rho["silviculture"], 2), r(d.rho["forest"], 2), r(d.rho["grassland"], 2), r(d.p["grassland"], 2)) == (0.42, -0.25, 0.13, 0.03)
    sem = pd.read_csv(TAB / "landcover_sem.csv")
    k = sem[(sem.response == "ev_1225_100km2_yr") & (sem.W == "knn6")].set_index("term")
    # log(y) instead of log(y + 0.1); 295 municipalities, n = 294 in the model (Governador Celso Ramos,
    # zero density, excluded). 277 municipalities, log(y): Moran 0.31 / -0.005 / 0.49; effects 35, 29, 22, 12 %; AIC 409.7 -> 340.5
    assert int(k.n.iloc[0]) == 294
    assert (r(k.moran_ols.iloc[0], 2), r(k.moran_sem.iloc[0], 3), r(k.p_moran_sem.iloc[0], 2)) == (0.32, 0.002, 0.44)
    assert [round(k.effect_10pp_pct[t]) for t in ["grassland", "silviculture", "pasture", "agriculture"]] == [37, 35, 24, 15]
    assert (r(k.aic_ols.iloc[0], 1), r(k.aic_sem.iloc[0], 1), r(k.lam.iloc[0], 2)) == (492.4, 415.9, 0.67)
    c = sem[(sem.response == "CO2_per_event") & (sem.W == "knn6")].set_index("term")
    assert int(c.n.iloc[0]) == 288        # (277-municipality file: n = 276, silviculture +27 %)
    assert r(c.effect_10pp_pct["silviculture"], 0) == 28 and r(c.effect_10pp_pct["agriculture"], 0) == -11


# ---------------------------------------------------------------- kernel density (M 2.6, 3; R 3)
def test_kde():
    p = TAB / "kde_2025_bandwidths.csv"
    if not p.is_file():
        pytest.skip("run R/analysis/kde_events.R")
    bw = pd.read_csv(p).set_index("selector").sigma_m
    assert (r(bw["ppl"] / 1000, 1), r(bw["CvL"] / 1000, 1), r(bw["scott"] / 1000, 1)) == (2.8, 8.8, 21.7)
    g = pd.read_csv(TAB / "kde_2025_grid.csv")
    assert r(g.ev_100km2.max(), 1) == 52.8
    top = g[g.ev_100km2 >= g.ev_100km2.quantile(0.99)].meso.value_counts(normalize=True)
    assert (r(100 * top["Serrana"], 1), r(100 * top["Oeste Catarinense"], 1)) == (93.6, 6.4)


# ---------------------------------------------------------------- report-only indicators (R 4, Appendix A)
def test_report_indicators():
    log = (ROOT / "results" / "logs" / "a08_report_indicators.txt").read_text(encoding="utf-8")
    assert "CV 28.3%" in log and "0.728 (n = 277" in log and "median 478 t" in log
    i = pd.read_csv(TAB / "intensity_per_event_2025.csv").set_index("municipio")
    assert (round(i.CO2_per_event["São Joaquim"]), round(i.CO2_per_event["Lebon Régis"]), int(i.events["Lebon Régis"])) == (415, 2118, 70)


def test_emission_factor_check():
    e = pd.read_csv(TAB / "emission_factor_check.csv")
    assert e.ratio.between(0.995, 1.005).all()
