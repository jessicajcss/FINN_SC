"""Values introduced in the revision round (inventory report v5.2, 2026-10-31): python/analysis/a14_validity_checks.py.
FINN vegetation class vs MapBiomas land cover at the event location, use vs availability of land cover by the events,
emission scenario with the mapped burned area, and robustness of the recurrence analysis of a13.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"


def r(x, k):
    return round(float(x), k)


def _row(X, subset, gv, variant="pixel 2019"):
    return X[(X.variant == variant) & (X.subset == subset) & (X.finn_genveg == gv)].iloc[0]


def test_finn_class_vs_mapbiomas():
    # dominant GENVEG with ties (6.0% of the events) assigned to the lowest code, as in a08 (deterministic)
    X = pd.read_csv(TAB / "finn_genveg_vs_mapbiomas.csv")
    q = _row(X, "State 2012-2025", "temperate_forest")
    assert int(q.events) == 21043 and r(q.pct_events_forest, 1) == 42.8 and r(q.pct_events_plantation, 1) == 32.7
    assert r(q.pct_CO2_forest, 1) == 43.1 and r(q.pct_CO2_plantation, 1) == 35.2
    b = _row(X, "Profile B 2012-2025", "temperate_forest")
    assert int(b.events) == 1148 and r(b.pct_events_plantation, 1) == 45.1 and r(b.pct_events_forest, 1) == 31.8
    assert r(b.pct_CO2_plantation, 1) == 45.7
    a = _row(X, "Profile A 2012-2025", "all")
    assert int(a.events) == 12412 and r(a.pct_events_grassland, 1) == 73.2
    w = _row(X, "Profile B 2012-2025", "temperate_forest", "5x5 window 2019")
    assert r(w.pct_events_plantation, 1) == 52.2


def test_use_availability():
    U = pd.read_csv(TAB / "event_landcover_use_availability.csv")
    u = U[(U.subset == "State 2012-2025") & (U.variant == "pixel 2019")].set_index("group")
    assert [r(u.loc[g, "use_availability_ratio"], 2) for g in ("forest", "grassland", "agriculture", "plantation")] == \
        [0.62, 3.37, 1.06, 1.28]
    assert r(u.loc["grassland", "pct_state_area"], 1) == 5.2


def test_mapped_area_scenario():
    S = pd.read_csv(TAB / "emission_scenario_mapped_area.csv").set_index("year")
    assert r(S.loc[2024, "CO2_mb_scenario_t"] / 1e6, 3) == 0.275 and r(S.loc[2024, "CO2_mcd_scenario_t"] / 1e6, 3) == 0.173
    assert r(S.CO2_mb_scenario_t.min() / 1e6, 2) == 0.11 and r(S.CO2_mb_scenario_t.max() / 1e6, 2) == 0.45


def test_recurrence_robustness():
    R = pd.read_csv(TAB / "recurrence_robustness.csv")
    b = R[R.check == "selection_ratio_block_bootstrap"].set_index("term")
    assert (r(b.loc["grassland", "lo95"], 2), r(b.loc["grassland", "hi95"], 2)) == (5.68, 8.36)
    assert (r(b.loc["plantation", "lo95"], 2), r(b.loc["plantation", "hi95"], 2)) == (0.31, 0.60)
    d = R[R.check == "GM_Error_Het distance band 10 km"].set_index("term")
    assert r(d.loc["grassland", "estimate"], 2) == 1.40 and r(d.loc["plantation", "estimate"], 2) == 1.05
