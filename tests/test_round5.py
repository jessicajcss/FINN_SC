"""Golden values added in review round 5 (manuscript v6 and inventory report v3, 2026-10-06):
counting units, comparison with the 2020 state inventory (LCQAR, 2022; FINN v1.5), kernel density of the
far west and north coast, and the Fisher-Jenks classes of Figure 6.
The tests read results/ (run `python python/run_analysis.py` first)."""
import re
from pathlib import Path

import numpy as np
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
def st():
    return pd.read_csv(TAB / "state_counts.csv").set_index(["year", "sensor", "version"])


def test_counting_units_2025(st):
    """Manuscript Discussion / report 3: 5,121 events would be 5,160 without screening (+0.8 %), 5,489 detections
    (+7.2 %) and 8,581 records (+67.6 %); Lages 429 events vs 670 records (+56 %)."""
    a = st.loc[(2025, "MODIS+VIIRS", "v2.5.1")]
    s = a.events_screened
    assert (r(100 * (a.events / s - 1), 1), r(100 * (a.detections / s - 1), 1), r(100 * (a.records / s - 1), 1)) == (0.8, 7.2, 67.6)
    m = pd.read_csv(TAB / "municipal_2025.csv").set_index("municipio")
    assert (int(m.events["Lages"]), int(m.records["Lages"])) == (429, 670)
    assert r(100 * (m.records["Lages"] / m.events["Lages"] - 1), 0) == 56


def test_events_with_several_detections():
    """Reply on the FINN polygon identifier: 20,766 of 124,602 events with >1 detection (all products);
    9,287 of 83,512 (11.1 %) in the MODIS+VIIRS series; 267 of 5,160 (5.2 %) in 2025."""
    e = pd.read_csv(TAB / "events.csv.gz")
    assert (len(e), int((e.n_det > 1).sum())) == (124602, 20766)
    mv = e[e.sensor == "MODIS+VIIRS"]
    assert (len(mv), int((mv.n_det > 1).sum()), r(100 * (mv.n_det > 1).mean(), 1)) == (83512, 9287, 11.1)
    y = mv[mv.year == 2025]
    assert (len(y), int((y.n_det > 1).sum()), r(100 * (y.n_det > 1).mean(), 1)) == (5160, 267, 5.2)


def test_lcqar_2020_and_finn_versions(st):
    """Manuscript Discussion / report 3: LCQAR (2022) 2020 totals within 0.4 % of the FINN v1.5 records of 2020 in SC;
    FINN v2.5 for 2020: 4.56 Mt (MODIS; 5,643 records; 1,971 events) and 6.63 Mt (MODIS+VIIRS; 15,727 records;
    8,212 events); v2.5 MODIS 65 % below v1.5; VIIRS +45 %; v1.5 records = MODIS detections;
    CO2 per km2 3.1 (v1.5) vs 1.6 kt (v2.5) with nearly equal area (4,135 vs 4,146 km2 with VIIRS)."""
    L = pd.read_csv(EXT / "legacy_finn15_lcqar_2020.csv").set_index("source")
    f, q = L.loc["finn15_sc_records"], L.loc["lcqar_2022_report"]
    diffs = [abs(q[c] / f[c] - 1) for c in ("count", "CO2_t", "CO_t", "PM25_t", "NOx_t")]
    assert max(diffs) < 0.004
    # manuscript wording: 0.2 % in the emissions and 0.3 % in the number of focos
    assert {r(100 * abs(q[c] / f[c] - 1), 1) for c in ("CO2_t", "CO_t", "PM25_t", "NOx_t")} == {0.2}
    assert r(100 * (q["count"] / f["count"] - 1), 1) == 0.3 and round(f.CO2_t) == 12883691
    assert (r(q.CO2_t / 1e6, 2), int(q["count"]), r(f.CO2_t / 1e6, 2), int(f["count"]), round(f.area_km2)) == (12.91, 4625, 12.88, 4609, 4135)
    s = pd.read_csv(TAB / "series_state_all_products.csv").set_index(["year", "sensor", "version"])
    mo, mv = s.loc[(2020, "MODIS", "v2.5")], s.loc[(2020, "MODIS+VIIRS", "v2.5")]
    assert (r(mo.CO2 / 1e6, 2), r(mv.CO2 / 1e6, 2)) == (4.56, 6.63)
    a, b = st.loc[(2020, "MODIS", "v2.5")], st.loc[(2020, "MODIS+VIIRS", "v2.5")]
    assert (int(a.records), int(a.events_screened), int(b.records), int(b.events_screened)) == (5643, 1971, 15727, 8212)
    assert r(100 * (mo.CO2 / f.CO2_t - 1), 0) == -65 and r(100 * (mv.CO2 / mo.CO2 - 1), 0) == 45
    # FINN v1.5: one record per MODIS detection; v2.5 MODIS keeps 2,689 detections; CO2 per unit area 3.1 vs 1.6 kt km-2
    assert int(f.day_location_combinations) == int(f["count"]) == 4609
    assert (int(a.detections), int(b.detections)) == (2689, 9953)
    assert (r(f.CO2_t / f.area_km2 / 1e3, 1), r(mo.CO2 / mo.area_km2 / 1e3, 1), r(mv.CO2 / mv.area_km2 / 1e3, 1)) == (3.1, 1.6, 1.6)
    assert (round(f.area_km2), round(mo.area_km2), round(mv.area_km2)) == (4135, 2800, 4146)
    assert r(100 * (mv.CO2 / f.CO2_t - 1), 1) == -48.5
    # vegetation code: FINN v1.5 put half of the 2020 area in code 3 (tropical forest in Wiedinmyer et al., 2023, Table 1);
    # FINN v2.5 puts SC forests in code 4 (temperate forest)
    assert (f.veg_code3_area_pct, f.veg_code3_CO2_pct, f.veg_code4_area_pct) == (50.2, 87.3, 0.4)
    assert r(f.veg_code3_CO2_pct * f.CO2_t / (f.veg_code3_area_pct * f.area_km2) / 1e3, 1) == 5.4   # kt CO2 per km2, code 3
    rec = pd.read_csv(ROOT / "data" / "derived" / "finn_sc_records_2003_2025.csv.gz", usecols=["year", "sensor", "version", "GENVEG", "AREA", "CO2"])
    x = rec[(rec.year == 2020) & (rec.sensor == "MODIS+VIIRS") & (rec.version == "v2.5")]
    g = x.groupby("GENVEG")[["AREA", "CO2"]].sum()
    assert (r(100 * g.AREA[4] / g.AREA.sum(), 1), r(100 * g.CO2[4] / g.CO2.sum(), 1), r(100 * g.AREA[3] / g.AREA.sum(), 1)) == (35.8, 59.5, 0.0)
    assert (r(g.CO2[4] / (g.AREA[4] / 1e6) / 1e3, 1)) == 2.7


def test_kde_far_west_and_north_coast():
    """Manuscript Discussion: mean kernel density west of 52.5 W = 2.6 and in the Norte Catarinense east of 49.5 W = 1.7
    events per 100 km2, against 5.4 in the state."""
    p = TAB / "kde_2025_grid.csv"
    if not p.is_file():
        pytest.skip("run R/analysis/kde_events.R")
    g = pd.read_csv(p)
    assert r(g[g.lon < -52.5].ev_100km2.mean(), 1) == 2.6
    assert r(g[(g.meso == "Norte Catarinense") & (g.lon > -49.5)].ev_100km2.mean(), 1) == 1.7
    m = g.ev_100km2.mean()   # 'about half and one third of the state mean'
    assert r(g[g.lon < -52.5].ev_100km2.mean() / m, 2) == 0.49 and r(g[(g.meso == "Norte Catarinense") & (g.lon > -49.5)].ev_100km2.mean() / m, 2) == 0.31
    assert r(g.ev_100km2.mean(), 1) == 5.4


def test_figure6_fisher_jenks_reproduces_original_breaks():
    """Figure 6 (original layout): Fisher-Jenks on the 2025 municipal CO2 and CO reproduces the class limits of the
    authors' first version of the figure (CO2 10329/31410/71909/149038; CO 797/2178/4109/6885)."""
    log = (LOG / "a10_figures.txt").read_text(encoding="utf-8")
    co2 = re.search(r"Figure 6 CO2: Fisher-Jenks upper limits \[(.*?)\]", log).group(1)
    co = re.search(r"Figure 6 CO: Fisher-Jenks upper limits \[(.*?)\]", log).group(1)
    nums = lambda s: [round(float(x)) for x in s.split(",")]
    assert nums(co2)[:4] == [10329, 31410, 71909, 149038]
    assert nums(co)[:4] == [797, 2178, 4109, 6885]


def test_study_area_land_cover_shares():
    """Study-area figure: shares of the classified area of SC in 2019 (MapBiomas Collection 10, 60 m overview)."""
    a = pd.read_csv(EXT / "mapbiomas_c10_lulc2019_SC_class_areas.csv")
    a = a[a.class_id > 0]
    assert abs(a.pct_classified.sum() - 100) < 0.01
    g = lambda ids: r(a[a.class_id.isin(ids)].pct_classified.sum(), 1)
    assert (g([3, 5, 49]), g([21]), g([39, 40, 41]), g([9]), g([15]), g([12]), g([24]), g([33, 31])) == \
        (40.2, 17.3, 13.2, 10.5, 9.9, 5.2, 1.9, 1.4)


def test_study_area_mesoregion_land_cover():
    """Section 2.1: grassland concentrated in the Serrana, rice in the Sul, temporary crops and mosaic in the Oeste (2019)."""
    p = TAB / "landcover2019_mesoregion.csv"
    if not p.is_file():
        pytest.skip("run tools/study_area_map.py")
    d = pd.read_csv(p).set_index(["group", "mesorregiao"])
    assert r(d.pct_of_group[("grass", "Serrana")], 1) == 97.7 and r(d.pct_of_mesoregion[("grass", "Serrana")], 1) == 21.6
    assert r(d.pct_of_group[("silv", "Serrana")], 1) == 37.5
    assert r(d.pct_of_group[("crop", "Oeste Catarinense")], 1) == 45.3 and r(d.pct_of_group[("mosaic", "Oeste Catarinense")], 1) == 41.3
    assert r(d.pct_of_mesoregion[("forest", "Grande Florianópolis")], 1) == 62.1 and r(d.pct_of_mesoregion[("forest", "Vale do Itajaí")], 1) == 53.9
