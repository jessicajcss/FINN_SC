"""Unit tests of the event / detection definitions and of the persistent-anomaly screening."""
import numpy as np
import pandas as pd
import pytest
from finn_sc.events import build_events, flag_persistent, distinct_days_within, doy_to_month


def _rec(rows):
    cols = ["year", "sensor", "version", "DAY", "POLYID", "FIREID", "GENVEG", "AREA", "LONGI", "LATI", "CO2", "NM_MUN"]
    return pd.DataFrame(rows, columns=cols)


def test_event_assignment_largest_area_and_ties():
    r = _rec([
        # event 1: two detections, two land-cover pieces, two municipalities; B holds the larger AREA
        (2025, "MODIS+VIIRS", "v2.5.1", 10, 1, 101, 1, 100.0, -50.0, -27.0, 1.0, "A"),
        (2025, "MODIS+VIIRS", "v2.5.1", 10, 1, 101, 4, 50.0, -50.0, -27.0, 2.0, "A"),
        (2025, "MODIS+VIIRS", "v2.5.1", 10, 1, 102, 1, 200.0, -50.1, -27.0, 3.0, "B"),
        # event 2: exact tie between C and D -> alphabetical order (C)
        (2025, "MODIS+VIIRS", "v2.5.1", 11, 2, 201, 1, 70.0, -51.0, -27.0, 1.0, "D"),
        (2025, "MODIS+VIIRS", "v2.5.1", 11, 2, 202, 1, 70.0, -51.0, -27.1, 1.0, "C"),
    ])
    E = build_events(r).set_index("POLYID")
    assert len(E) == 2
    assert E.loc[1, "mun_event"] == "B" and E.loc[1, "n_rows"] == 3 and E.loc[1, "n_det"] == 2
    assert E.loc[1, "area_m2"] == 350.0 and E.loc[1, "CO2"] == 6.0
    assert E.loc[2, "mun_event"] == "C"


def test_distinct_days_within_radius():
    # 16 days at the same point, plus one point 1.2 km to the north (outside a 1 km radius)
    lon = np.full(17, -49.0); lat = np.full(17, -28.0); lat[-1] += 1.2 / 111.2
    day = np.r_[np.arange(1, 17), 100]
    nd = distinct_days_within(lon, lat, day, 1.0)
    assert (nd[:16] == 16).all() and nd[16] == 1
    assert distinct_days_within(lon, lat, day, 1.5)[16] == 17


def test_flag_persistent_threshold():
    def rec_days(n):
        return _rec([(2025, "MODIS+VIIRS", "v2.5.1", d, d, 1000 + d, 1, 1.0, -49.0, -28.0, 1.0, "X") for d in range(1, n + 1)])
    _, f16 = flag_persistent(rec_days(16), 1.0, 16)
    _, f15 = flag_persistent(rec_days(15), 1.0, 16)
    assert len(f16) == 16 and len(f15) == 0


def test_doy_to_month_leap_year():
    assert list(doy_to_month([2024, 2025], [60, 60])) == [2, 3]     # 29 Feb 2024 vs 1 Mar 2025
