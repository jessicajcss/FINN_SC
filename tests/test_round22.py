"""Values introduced after the authors' comments on the English manuscript v7.1 (2026-11-08):
python/analysis/a17_v72_review.py (FINN v1.5 two-day convention, land cover at the events by mesoregion,
mesoregion and municipal profiles) and python/analysis/a18_exports.py (Comex Stat exports, 2025)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_finn15_continuations():
    V = pd.read_csv(TAB / "finn15_v25_2020_records.csv")
    assert len(V) == 4609
    assert (V.role == "original").sum() == 2716 and (V.role == "continuation").sum() == 1893
    c = V[V.role == "continuation"]
    assert r(100 * c.CO2.sum() / V.CO2.sum(), 1) == 27.0
    assert c.ratio_prev.between(0.45, 0.55).all()


def test_finn15_decomposition():
    D = pd.read_csv(TAB / "finn15_v25_2020_decomposition.csv")
    assert [r(x / 1e6, 2) for x in D.CO2_t] == [12.88, 9.40, 9.31, 10.78, 4.56]
    assert [r(x, 3) for x in D.factor_vs_previous[1:]] == [0.730, 0.990, 1.159, 0.423]


def test_finn15_matched_forest():
    G = pd.read_csv(TAB / "finn15_v25_2020_genveg_matched.csv")
    f = G[(G.gv15 == 3) & (G.gv25 == 4)].iloc[0]
    assert int(f.n) == 704 and int(G[G.gv15 == 3].n.sum()) == 1084
    assert [r(f.t_CO2_per_km2_v15, 0), r(f.t_CO2_per_km2_v25, 0)] == [8535.0, 2597.0]


def test_event_landcover_serrana():
    X = pd.read_csv(TAB / "event_landcover_by_mesoregion.csv").set_index(["mesoregion", "group"])
    g = X.loc[("Serrana", "grassland")]
    assert [r(g.pct_events, 1), r(g.pct_area_classified, 1), r(g.pct_CO2, 1)] == [42.8, 21.6, 29.6]
    p = [X.loc[(m, "plantation")].use_availability_ratio for m in
         ("Grande Florianópolis", "Norte Catarinense", "Oeste Catarinense", "Sul Catarinense", "Vale do Itajaí")]
    assert r(min(p), 2) == 1.44 and r(max(p), 2) == 2.25


def test_profiles():
    M = pd.read_csv(TAB / "mesoregion_profile.csv").set_index("mesoregion")
    assert int(M.loc["State", "pop2022"]) == 7610361
    assert [r(M.loc["Serrana", c], 1) for c in ("agro_pct_of_vab2021", "grassland_pct_2023", "CO2_t_per_capita_2025")] == [19.9, 24.0, 3.9]
    Q = pd.read_csv(TAB / "municipal_profile_top2025.csv")
    assert len(Q) == 8
    s = M.loc["State"]
    assert r(100 * Q.area_km2.sum() / s.area_km2, 1) == 11.5 and r(100 * Q.pop2022.sum() / s.pop2022, 1) == 3.5
    assert r(100 * Q.events_2025.sum() / s.events_2025, 1) == 31.5 and r(100 * Q.CO2_kt_2025.sum() / s.CO2_kt_2025, 1) == 30.9


def test_exports_2025():
    G = pd.read_csv(TAB / "exports_2025_by_mesoregion.csv", index_col=0)
    s = G.loc["State"]
    assert r(s.usd / 1e6, 1) == 14951.6 and r(s.agri_pct, 1) == 57.6 and r(s.wood_pct, 1) == 11.2
    assert [r(G.loc["Serrana", c], 1) for c in ("pct_state", "wood_pct")] == [5.0, 72.8]
    assert r(G.loc["Vale do Itajaí", "pct_state"], 1) == 50.1
    M = pd.read_csv(TAB / "exports_2025_by_municipality.csv").set_index("NM_MUN")
    assert len(M) == 295 and int((M.usd > 0).sum()) == 215
    top = pd.read_csv(TAB / "municipal_profile_top2025.csv").municipality
    T = M.loc[top]
    assert r(T.usd.sum() / 1e6, 1) == 451.6 and r(100 * T.usd.sum() / s.usd, 1) == 3.0
    assert r(100 * T.usd_wood.sum() / T.usd.sum(), 1) == 68.8 and int((T.usd == 0).sum()) == 2


def test_continuation_rule_2020():
    """python/analysis/a19_v72_followup.py: next-day continuations of FINN v1.5 in 2020"""
    C = pd.read_csv(TAB / "finn15_2020_continuation_rule.csv").set_index("radius_km")
    assert C.loc[1.0, "continuations_with_same_day_detection"] == 0
    assert list(C.detections_without_continuation_with_next_day_detection) == [167, 418, 437]
    assert int(C.loc[1.0, "detections_without_continuation"]) == 823 and int(C.loc[1.0, "continuations"]) == 1893


def test_forest_class_scenario():
    """tropical instead of temperate forest class with the FINN v2.5 South America parameters"""
    S = pd.read_csv(TAB / "forest_class_scenario.csv").set_index(["case", "species"])
    assert r(S.loc[("2020 MODIS", "CO2"), "factor_tropical_vs_temperate"], 2) == 3.93
    assert r(S.loc[("2020 MODIS", "CO"), "factor_tropical_vs_temperate"], 2) == 2.76
    assert r(S.loc[("2020 MODIS", "CO2"), "scenario_total_t"] / 1e3, 0) == 12756
    assert r(S.loc[("2020 MODIS", "CO2"), "scenario_vs_reported"], 2) == 2.80
    assert r(S.loc[("2025 MODIS+VIIRS", "CO"), "scenario_vs_reported"], 2) == 2.32
    A = pd.read_csv(TAB / "forest_class_scenario_annual.csv")
    assert len(A) == 14 and [r(A.scenario_vs_reported.min(), 2), r(A.scenario_vs_reported.max(), 2)] == [2.42, 2.74]
    assert [r(A.temperate_forest_pct.min(), 1), r(A.temperate_forest_pct.max(), 1)] == [48.5, 59.5]


def test_finn15_correction_2020():
    """python/analysis/a20_finn15_correction.py: FINN v1.5 studies with and without the next-day continuations"""
    T = pd.read_csv(TAB / "finn15_lcqar_2020_correction.csv").set_index("metric")
    assert abs(T.loc["CO2 (t)", "LCQAR_over_all"] - 1.0020) < 5e-4
    assert abs(T.loc["CO2 (t)", "LCQAR_over_original"] - 1.3735) < 5e-4
    assert abs(T.loc["CO2 (t)", "continuation_share"] - 0.2705) < 5e-4
    B = pd.read_csv(TAB / "brain2020_finn15_correction.csv").set_index("product")
    assert abs(B.loc["FINN v1.5 all records", "BRAIN_over_product_CO"] - 0.875) < 1e-3
    assert abs(B.loc["FINN v1.5 original detections", "BRAIN_over_product_CO"] - 1.199) < 1e-3
    assert B.loc["FINN v1.5 original detections", "share_BRAIN_CO_in_common"] < 0.70
    C = pd.read_csv(TAB / "continuation_check_finn25.csv")
    assert C.day_location_pairs.sum() == 151443
    assert C.same_location_previous_day.sum() == 37 and C.of_which_half_CO2.sum() == 1


def test_teixeira2025_vs_finn25():
    """a20 part 4: Teixeira et al. (2025) Table C.1 (FINN v1.5) against FINN v2.5 MODIS, 2003-2017"""
    X = pd.read_csv(ROOT / "data" / "external" / "teixeira2025_tableC1_SC_finn15.csv")
    assert round(X.CO2_t.mean()) == 7818193 and round(X.CO_t.mean()) == 418649 and round(X.PM25_t.mean()) == 42173
    T = pd.read_csv(TAB / "teixeira2025_vs_finn25_modis.csv")
    y = T[T.year.str.fullmatch(r"\d{4}")]
    assert len(y) == 15 and abs(y.CO2_ratio.median() - 1.724) < 1e-3


def test_finn15_2019_and_legacy_file():
    """a20 parts 5 and 6: FINN v1.5 2019 continuations, BRAIN 2019, and the authors' aggregated file of 5 Feb 2026"""
    T = pd.read_csv(TAB / "finn15_2019_correction.csv").set_index("metric")
    assert T.loc["records", "all_records"] == 3491 and T.loc["records", "original_detections"] == 2042
    assert abs(T.loc["CO2", "continuation_share"] - 0.2751) < 5e-4
    assert abs(T.loc["BRAIN 2019 / FINN v1.5 all records (cells inside SC)", "all_records"] - 1.010) < 1e-3
    assert abs(T.loc["BRAIN 2019 / FINN v1.5 original detections (cells inside SC)", "all_records"] - 1.390) < 1e-3
    A = pd.read_csv(TAB / "legacy_aggregated_check.csv")
    x = A[A.reference == "this inventory (records)"]
    assert set(x[(x.CO2_ratio - 1).abs() > 1e-9].year) == {2011}
    t = A[A.reference.str.startswith("Teixeira")].set_index("year")
    assert all(abs(t.loc[y, "CO2_ratio"] - 1) < 1e-6 for y in (2003, 2005, 2006, 2007, 2008, 2009, 2011, 2012, 2013, 2014, 2015))
    assert t.loc[2016, "CO2_ratio"] < 0.21 and t.loc[2017, "CO2_ratio"] < 0.21


def test_finn15_2002_2020_correction():
    """a20 part 7: FINN v1.5 records 2002-2020 (2002, 2016 and 2017 from the NCAR annual files, 11 Nov 2026), next-day
    continuations by year, Teixeira et al. (2025) Table C.1"""
    T = pd.read_csv(TAB / "finn15_2002_2020_correction.csv").set_index("year")
    assert list(T.index) == list(range(2002, 2021))
    FI = pd.read_csv(ROOT / "data" / "external" / "finn15_SC_records_2002_2020_files.csv").set_index("year")
    assert set(FI.index[FI.source == "ncar"]) == {2002, 2016, 2017}
    assert int(FI.loc[2015, "check_records_SC"]) == int(FI.loc[2015, "records_SC"]) == 860
    assert abs(FI.loc[2015, "check_CO2_SC_t"] - FI.loc[2015, "CO2_SC_t"]) < 1e-6
    t = T.dropna(subset=["CO2_teixeira_over_all"])
    assert len(t) == 16 and ((t.CO2_teixeira_over_all - 1).abs() < 2e-4).sum() == 15
    assert abs(T.loc[2016, "CO2_teixeira_over_all"] - 0.9964) < 1e-3
    assert T.CO2_continuation_share.between(0.26, 0.33).all()
    assert abs(T.CO2_continuation_share.min() - 0.270) < 1e-3 and abs(T.CO2_continuation_share.max() - 0.324) < 1e-3
    assert int(T.loc[2020, "continuations"]) == 1893 and int(T.loc[2019, "continuations"]) == 1449
