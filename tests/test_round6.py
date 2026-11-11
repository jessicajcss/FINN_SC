"""Values introduced in the revision round (manuscript v7, Supplementary Material v3, report v4).

* lag-1 autocorrelation of the annual series tested by Mann-Kendall (manuscript section 2.6);
* land-cover models on log(y) instead of log(y + 0.1) (manuscript sections 2.8 and 3; Table S8);
* Earth Engine notebook for the land-cover fractions of all 295 municipalities.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from finn_sc.stats import lag1_autocorrelation

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def test_lag1_autocorrelation_known_value():
    # deviations -2..2: sum of products (2 + 0 + 0 + 2) / sum of squares 10
    assert lag1_autocorrelation([1, 2, 3, 4, 5]) == pytest.approx(0.4)
    assert lag1_autocorrelation([1, -1, 1, -1, 1, -1]) < 0


def test_lag1_of_trend_series():
    mk = pd.read_csv(TAB / "mann_kendall.csv").set_index(["variable", "period"])
    full = mk.xs("2012-2025", level="period")
    assert [r(full.r1[v], 2) for v in ["events", "area_km2", "CO2_t", "PM25_t"]] == [0.11, 0.22, 0.22, 0.22]
    # all inside the approximate 95 % range of white noise for n = 14, (-1 +/- 1.96 sqrt(n - 2)) / (n - 1)
    n = 14
    lo, hi = (-1 - 1.96 * np.sqrt(n - 2)) / (n - 1), (-1 + 1.96 * np.sqrt(n - 2)) / (n - 1)
    assert ((full.r1 > lo) & (full.r1 < hi)).all()


def test_landcover_models_use_plain_log():
    sem = pd.read_csv(TAB / "landcover_sem.csv")
    assert set(sem.response) == {"ev_1225_100km2_yr", "CO2_per_event"}       # 2025-density model removed
    d = pd.read_csv(TAB / "landcover_municipal.csv").dropna(subset=["grassland"])
    zero = d.ev_1225_100km2_yr <= 0                                          # log undefined: excluded from the models
    assert d.loc[zero, "NM_MUN"].tolist() == ["Governador Celso Ramos"]
    d = d[~zero]
    X = np.column_stack([np.ones(len(d)), d[["grassland", "pasture", "agriculture", "silviculture"]].values])
    b = np.linalg.lstsq(X, np.log(d.ev_1225_100km2_yr.values), rcond=None)[0]
    k = sem[(sem.response == "ev_1225_100km2_yr") & (sem.W == "knn6")].set_index("term")
    assert np.allclose(b, k.b_ols[["const", "grassland", "pasture", "agriculture", "silviculture"]].values, atol=1e-8)
    q = sem[(sem.response == "ev_1225_100km2_yr") & (sem.W == "queen")].set_index("term")
    assert [round(q.effect_10pp_pct[t]) for t in ["grassland", "silviculture", "pasture", "agriculture"]] == [37, 34, 27, 16]
    assert (r(q.moran_ols.iloc[0], 2), r(q.lam.iloc[0], 2), r(q.aic_sem.iloc[0], 1)) == (0.36, 0.70, 401.7)


def test_landcover_notebook_matches_recipe():
    nb = json.loads((ROOT / "gee" / "mapbiomas_lulc_fractions_all295.ipynb").read_text(encoding="utf-8"))
    src = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    recipe = (ROOT / "gee" / "mapbiomas_lulc_fractions.py").read_text(encoding="utf-8")
    grab = lambda text, name: re.search(rf'"{name}":\s*(\[[^\]]*\])', text).group(1).replace(" ", "")
    for g in ["forest", "grassland", "pasture", "agriculture", "silviculture"]:
        assert grab(src, g) == grab(recipe, g), g
    assert "SCALE_M = 100" in src and "TILE_SCALE = 4" in src and "YEAR_LULC = 2023" in src
    cfg = (ROOT / "config" / "config.yml").read_text(encoding="utf-8")
    assert "mapbiomas_lulc2023_SC_municipal_fractions_all295.csv" in cfg and "mapbiomas_lulc2023_SC_municipal_fractions_all295.csv" in src


def test_landcover_fractions_all_295_municipalities():
    """gee/mapbiomas_lulc_fractions_all295.ipynb, run on 2026-10-07 (Colab; executed copy in
    gee/mapbiomas_lulc_fractions_all295_run_2026-10-07.ipynb): MapBiomas Collection 10.1, 2023."""
    import hashlib
    p = ROOT / "data" / "external" / "mapbiomas_lulc2023_SC_municipal_fractions_all295.csv"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == "f8ca0995f3574224261e76e11c42af959d45e35c7268459d1159cb016df17654"
    n = pd.read_csv(p)
    G = ["forest", "grassland", "pasture", "agriculture", "silviculture"]
    mu = pd.read_csv(ROOT / "data" / "external" / "sc_municipios_2024_atributos.csv")
    assert len(n) == 295 and set(n.code_muni) == set(mu.CD_MUN)
    assert set(n.collection_id) == {10.1} and set(n.year) == {2023}
    assert (n[G].sum(axis=1) <= 1 + 1e-9).all()
    old = pd.read_csv(ROOT / "data" / "external" / "mapbiomas_lulc2023_SC_municipal_fractions.csv")
    m = n.merge(old, on="municipality", suffixes=("", "_old"))
    assert len(m) == 277                                    # the archived file is reproduced
    assert max((m[g] - m[g + "_old"]).abs().max() for g in G) < 1e-12      # identical up to float rounding
    lc = pd.read_csv(TAB / "landcover_municipal.csv")
    assert len(lc) == 295 and [round(lc[g].mean() * 100, 1) for g in G] == [37.1, 1.7, 10.4, 37.1, 7.8]
