#!/usr/bin/env python3
"""a01 - fire events, detections and persistent-thermal-anomaly screening.

Input : data/derived/finn_sc_records_2003_2025.csv.gz (all FINN v2.5/v2.5.1 records inside SC)
Output: results/tables/events.csv.gz            one row per event (all products) + flag (R = 1 km)
        results/tables/state_counts.csv         records, detections, events, screened events
        results/tables/screening_summary.csv    MODIS+VIIRS, R = 0.75 / 1 / 1.5 km, by year
        results/tables/screening_flagged_detections.csv
        results/logs/a01_events_screening.txt
Manuscript (v3.2): sections 2.6, 3 and 4 (counting units, comparison with the 2020 inventory), Table S6.
Inventory report: sections 2-3.
"""
from _setup import CFG, TAB, Log, load_records
import pandas as pd
from finn_sc.events import build_events, flag_persistent, doy_to_month, EVENT_KEY, PRODUCT

L = Log("a01_events_screening")
S = CFG["analysis"]["screening"]
rec = load_records()
L("records:", len(rec), rec.groupby(["sensor", "version"]).year.agg(["min", "max", "size"]).to_dict("index"))

E = build_events(rec)
det, fl = flag_persistent(rec, S["radius_km"], S["min_days"])
E = E.merge(fl.assign(flag=True), on=EVENT_KEY, how="left")
E["flag"] = E.flag.fillna(False).astype(bool)
E.to_csv(TAB / "events.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})

st = rec.groupby(PRODUCT).size().rename("records").to_frame()
st["detections"] = rec.drop_duplicates(PRODUCT + ["DAY", "FIREID"]).groupby(PRODUCT).size()
st["events"] = E.groupby(PRODUCT).size()
st["events_screened"] = E[~E.flag].groupby(PRODUCT).size()
st["flagged_events"] = st.events - st.events_screened
st = st.reset_index().sort_values(["sensor", "version", "year"])
st.to_csv(TAB / "state_counts.csv", index=False)
L(st.to_string(index=False))
L(f"events with records in more than one municipality: {100 * (E.n_mun > 1).mean():.2f}% (all products)")
mv = E[E.sensor == "MODIS+VIIRS"]
L(f"MODIS+VIIRS 2012-2025: events with records in >1 municipality {100 * (mv.n_mun > 1).mean():.1f}%; "
  f"2025 {100 * (mv[mv.year == 2025].n_mun > 1).mean():.2f}%")

# sensitivity of the screening radius (MODIS+VIIRS series)
rows = []
co2 = mv.groupby(["year", "DAY", "POLYID"]).CO2.sum()
area = mv.groupby(["year", "DAY", "POLYID"]).area_m2.sum()
for R in sorted({S["radius_km"], *S["sensitivity_radii_km"]}):
    d_R, f_R = flag_persistent(rec, R, S["min_days"], sensors=("MODIS+VIIRS",))
    fk = f_R.set_index(["year", "DAY", "POLYID"]).index
    for y in sorted(mv.year.unique()):
        ky = fk[fk.get_level_values(0) == y]
        ev_y = int((mv.year == y).sum())
        fy = d_R[(d_R.year == y) & d_R.flag]
        rows.append(dict(R_km=R, year=y, events=ev_y, flagged_events=len(ky),
                         flagged_pct=100 * len(ky) / ev_y,
                         co2_pct=100 * co2.reindex(ky).sum() / co2.loc[y].sum(),
                         area_pct=100 * area.reindex(ky).sum() / area.loc[y].sum(),
                         max_days=int(d_R[d_R.year == y].ndays.max()),
                         municipalities=";".join(sorted(fy.NM_MUN.astype(str).unique()))))
    if R == S["radius_km"]:
        fd = d_R[d_R.flag].copy()
        fd["month"] = doy_to_month(fd.year, fd.DAY)
        fd.to_csv(TAB / "screening_flagged_detections.csv", index=False)
        for (y, m), g in fd.groupby(["year", "NM_MUN"]):
            L(f"  R={R} km {y} {m}: detections {len(g)}, days {g.DAY.nunique()}, months {g.month.nunique()}, "
              f"centre {g.lon.mean():.3f} {g.lat.mean():.3f}")
SS = pd.DataFrame(rows)
SS.to_csv(TAB / "screening_summary.csv", index=False)
for R, g in SS.groupby("R_km"):
    L(f"R = {R} km: flagged events per year {g.flagged_events.min()}-{g.flagged_events.max()}; "
      f"max share {g.flagged_pct.max():.2f}% ({int(g.loc[g.flagged_pct.idxmax(), 'year'])}); "
      f"max CO2 share {g.co2_pct.max():.2f}% ({int(g.loc[g.co2_pct.idxmax(), 'year'])})")
L("MODIS-only series, flagged events:", E[(E.sensor == "MODIS") & E.flag].groupby(["version", "year"]).size().to_dict())
L.save()
