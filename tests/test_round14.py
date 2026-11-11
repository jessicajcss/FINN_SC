"""Values introduced in the revision round (inventory report v5.1, 2026-10-30): recurrence of fire events in a 2 km grid and
land use and land cover (MapBiomas Collection 10, 2019; python/analysis/a13_recurrence_landcover.py) and the 2019
study-area map (tools/study_area_map.py with FIG1_YEAR=2019).
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_recurrence_grid_2km():
    g = pd.read_csv(TAB / "recurrence_grid_2km.csv")
    assert len(g) == 23806
    assert int(g.events.sum()) == 83236 - 335
    assert r(100 * (g.R >= 7).mean(), 1) == 7.8 and r(100 * (g.R == 0).mean(), 1) == 25.0
    assert g.R.between(0, 14).all() and (g.R_v25 <= 10).all() and (g.R_v251 <= 4).all()
    hi = g[g.R >= 7]
    assert r(100 * (hi.mesorregiao == "Serrana").mean(), 1) == 59.3
    assert r(100 * (g.mesorregiao == "Serrana").mean(), 1) == 23.4
    assert r(100 * (hi[hi.mesorregiao == "Serrana"].dominant == "grassland").mean(), 1) == 69.6   # report 5.1


def test_recurrence_by_dominant_cover():
    t = pd.read_csv(TAB / "recurrence_by_landcover.csv").set_index("dominant")
    assert r(t.loc["grassland", "pct_cells"], 1) == 6.1 and r(t.loc["grassland", "pct_of_high_cells"], 1) == 41.5
    assert r(t.loc["grassland", "selection_ratio_high"], 1) == 6.8 and r(t.loc["grassland", "pct_R_ge7"], 1) == 53.6
    assert r(t.loc["forest", "pct_cells"], 1) == 43.4 and r(t.loc["forest", "pct_of_high_cells"], 1) == 22.2
    assert r(t.loc["agriculture", "pct_of_high_cells"], 1) == 28.2 and r(t.loc["agriculture", "pct_of_events"], 1) == 37.1
    assert r(t.loc["plantation", "selection_ratio_high"], 2) == 0.44 and r(t.loc["plantation", "pct_of_events"], 1) == 7.7
    assert r(t.pct_cells.sum(), 6) == 100.0


def test_recurrence_spatial_error_models():
    s = pd.read_csv(TAB / "recurrence_sem.csv")
    m = s[(s.model == "2 km | events all | land cover 2019") & (s.term != "const")].set_index("term")
    assert (m.estimator == "GM_Error_Het").all()
    assert [r(m.loc[k, "odds_ratio_10pp"], 2) for k in ("grassland", "agriculture", "pasture", "plantation")] == \
        [1.39, 1.15, 1.11, 1.08]
    assert m.loc["other", "p"] > 0.05 and (m.drop(index="other").p < 0.001).all()
    f = s[(s.model == "5 km | events all | land cover 2019") & (s.term != "const")].set_index("term")
    assert (f.estimator == "ML_Error").all()
    assert r(f.loc["grassland", "odds_ratio_10pp"], 2) == 1.63 and r(f.loc["plantation", "odds_ratio_10pp"], 2) == 1.11


def test_recurrence_sensitivity():
    s = pd.read_csv(TAB / "recurrence_sensitivity.csv")
    k = s[(s.cell_km == 2) & (s.events == "no_recurrent_sites") & (s.landcover_year == 2019)].set_index("dominant")
    assert r(k.loc["grassland", "selection_ratio_high"], 1) == 7.1 and r(k.loc["plantation", "selection_ratio_high"], 2) == 0.32
    c = s[(s.cell_km == 2) & (s.events == "all") & (s.landcover_year == 2023)].set_index("dominant")
    assert r(c.loc["grassland", "selection_ratio_high"], 1) == 6.4
    for km, share in ((5, 66.5), (10, 95.0)):        # the count saturates in larger cells
        x = s[(s.cell_km == km) & (s.events == "all") & (s.landcover_year == 2019)]
        assert r((x.pct_R_ge7 * x.pct_cells).sum() / 100, 1) == share


def test_landcover_2019_mesoregion():
    d = pd.read_csv(TAB / "landcover2019_mesoregion.csv").set_index(["group", "mesorregiao"])
    assert r(d.loc[("grass", "Serrana"), "pct_of_group"], 1) == 97.7
    assert r(d.loc[("grass", "Serrana"), "pct_of_mesoregion"], 1) == 21.6
    assert r(d.loc[("silv", "Serrana"), "pct_of_group"], 1) == 37.5
