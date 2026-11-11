"""a20_finn15_correction.py - FINN v1.5 inventories of Santa Catarina with and without the FINNv1 next-day continuations,
and check that the FINN v2.5 / v2.5.1 records of this inventory contain no such continuations (2026-11-09).

FINNv1 (Wiedinmyer et al., 2011, Sect. 2) counts each MODIS detection between about 30 N and 30 S for two days, the second
at half of its original size, unless the pixel is detected again; FINN v2.5 keeps this rule only between about 23.5 N and
23.5 S (Wiedinmyer et al., 2023, Sect. 2.1). The 2020 FINN v1.5 records of SC were classified in a17 as original
detections or next-day continuations (results/tables/finn15_v25_2020_records.csv, column role).
1. Earlier state inventory (LCQAR, 2022; data/external/legacy_finn15_lcqar_2020.csv) against the FINN v1.5 records of
   2020: all records (as published) and original detections only (continuations removed).
2. BRAIN 2020 (Hoinaski et al., 2024; daily cells in results/brain_2020/tables/brain_cells_daily_t.csv.gz) against the
   same two sets of FINN v1.5 records, cell by cell in the 4 km cells entirely inside SC, with the finn2cmaq rules of
   tools/brain_cells_and_finn15_check.py (records with AREA < 50 m2 dropped; days missing in BRAIN 2020 excluded).
   BRAIN 2019 equals the FINN v1.5 2019 annual file x 1.01 (results/brain_2019/tables/processing_checks.csv); its
   correction needs the 2019 FINN v1.5 records, which are not in the repository.
3. FINN v2.5 and v2.5.1 records of this inventory (2003-2025, MODIS and MODIS+VIIRS): day-location pairs at the same
   coordinates as a pair of the previous day, and those with half of its CO2 (the signature of a continuation).
4. Teixeira et al. (2025): FINN v1.5 annual totals of SC, 2002-2017 (Table C.1 of their supplement,
   data/external/teixeira2025_tableC1_SC_finn15.csv) against the FINN v2.5 MODIS totals of this inventory (2003-2017,
   same detection source, other version); the yearly ratios are compared with the 2020 ratios FINN v1.5 / FINN v2.5
   MODIS with all records and with the original detections only. The FINN v1.5 records of each year are in part 7.
5. FINN v1.5 records of 2019 (data/external/finn15_2019_SC_records.csv, tools/finn15_2019_records.py): next-day
   continuations classified with the rule of a17, and BRAIN 2019 compared with all records and with the original
   detections, as in part 2.
6. The authors' aggregated file of 5 Feb 2026 (data/external/legacy_aggregated_emissions_all_2026-02-05.csv; municipality,
   year, sensor and version; FINN v1.5 2003 and 2005-2020, FINN v2.5 and v2.5.1 as in this inventory) against the
   records of this inventory, the FINN v1.5 records of 2019 and 2020, and Table C.1 of Teixeira et al. (2025).
7. FINN v1.5 records of SC, 2002-2020 (data/external/finn15_SC_records_2002_2020.csv, tools/finn15_records.py; the
   authors' files, except 2002, 2016 and 2017, taken from the NCAR annual files through tools/finn15_raw_to_grid.py
   because the authors' file of 2002 is missing and those of 2016 and 2017 are copies of 2015): next-day
   continuations by year with the rule of a17, totals with and without them against Teixeira et al. (2025) Table C.1,
   and the ratio to FINN v2.5 MODIS with and without them.
Outputs: results/tables/finn15_lcqar_2020_correction.csv, brain2020_finn15_correction.csv,
continuation_check_finn25.csv, teixeira2025_vs_finn25_modis.csv, finn15_2019_correction.csv,
legacy_aggregated_check.csv, finn15_2002_2020_correction.csv; log a20_finn15_correction.txt.
"""
import sys
import numpy as np
import pandas as pd
from _setup import ROOT, TAB, Log, load_records

sys.path.insert(0, str(ROOT / "notebooks"))
import brain_core as bc  # noqa: E402

L = Log("a20_finn15_correction")
V = pd.read_csv(TAB / "finn15_v25_2020_records.csv")
o, c = V[V.role == "original"], V[V.role == "continuation"]

# ------------------------------------------------------------------ 1. LCQAR (2022) vs FINN v1.5 2020
L("1. Earlier state inventory (LCQAR, 2022) vs FINN v1.5 records of 2020 in SC")
lc = pd.read_csv(ROOT / "data/external/legacy_finn15_lcqar_2020.csv").set_index("source").loc["lcqar_2022_report"]
rows = []
for var, lab in (("CO2", "CO2_t"), ("CO", "CO_t"), ("PM25", "PM25_t")):
    a, k = V[var].sum(), o[var].sum()
    rows.append(dict(metric=var + " (t)", LCQAR_2022=lc[lab], finn15_all_records=a, finn15_original_detections=k,
                     LCQAR_over_all=lc[lab] / a, LCQAR_over_original=lc[lab] / k, continuation_share=1 - k / a))
rows.append(dict(metric="count (LCQAR: focos de calor)", LCQAR_2022=lc["count"], finn15_all_records=len(V),
                 finn15_original_detections=len(o), LCQAR_over_all=lc["count"] / len(V),
                 LCQAR_over_original=lc["count"] / len(o), continuation_share=len(c) / len(V)))
area_field = V.AREA.sum() / 1e6
area_eff = (o.AREA.sum() + 0.5 * c.AREA.sum()) / 1e6
rows.append(dict(metric="area field, km2 (LCQAR: about 4.1 thousand km2)", LCQAR_2022=np.nan,
                 finn15_all_records=area_field, finn15_original_detections=o.AREA.sum() / 1e6,
                 LCQAR_over_all=np.nan, LCQAR_over_original=np.nan, continuation_share=c.AREA.sum() / V.AREA.sum()))
rows.append(dict(metric="area entering the emissions, km2", LCQAR_2022=np.nan, finn15_all_records=area_eff,
                 finn15_original_detections=o.AREA.sum() / 1e6, LCQAR_over_all=np.nan, LCQAR_over_original=np.nan,
                 continuation_share=0.5 * c.AREA.sum() / (o.AREA.sum() + 0.5 * c.AREA.sum())))
T1 = pd.DataFrame(rows)
T1.to_csv(TAB / "finn15_lcqar_2020_correction.csv", index=False)
for r in T1.itertuples():
    L(f"   {r.metric}: LCQAR {r.LCQAR_2022:,.1f}; FINN v1.5 all {r.finn15_all_records:,.1f}; originals "
      f"{r.finn15_original_detections:,.1f}; LCQAR/all {r.LCQAR_over_all:.4f}; LCQAR/originals {r.LCQAR_over_original:.4f}; "
      f"continuation share {r.continuation_share:.4f}")
L(f"   NOx: LCQAR 38,037 t vs NO + NO2 of all records 37,962 t (legacy table); NOx is not in the per-record file, so the "
  f"corrected NOx is not computed")

# version and Figure 9 factors with and without the continuations
I = pd.read_csv(TAB / "inventory_comparison_2020.csv").set_index("inventory")
v25m, v25mv = I.loc["FINN v2.5 MODIS, 2020", "CO2_Mt"], I.loc["FINN v2.5 MODIS+VIIRS, 2020", "CO2_Mt"]
L(f"   FINN v1.5 / FINN v2.5 MODIS (CO2, 2020): all records {V.CO2.sum() / 1e6 / v25m:.3f}; originals {o.CO2.sum() / 1e6 / v25m:.3f}")
L(f"   FINN v1.5 / FINN v2.5 MODIS+VIIRS (CO2, 2020; Figure 9): all records {V.CO2.sum() / 1e6 / v25mv:.3f}; "
  f"originals {o.CO2.sum() / 1e6 / v25mv:.3f}")

# ------------------------------------------------------------------ 2. BRAIN 2020 vs FINN v1.5 2020
L("2. BRAIN 2020 vs FINN v1.5 2020, 4 km cells entirely inside SC")
B = pd.read_csv(ROOT / "results/brain_2020/tables/brain_cells_daily_t.csv.gz", parse_dates=["date"])
FS = pd.read_csv(ROOT / "results/brain_2020/tables/cell_fraction_SC.csv")
interior = pd.MultiIndex.from_frame(FS.loc[FS.fSC >= 0.999, ["i", "j"]])
G = bc.Grid.from_attrs(bc.EXPECTED_GRID)
missing = {pd.Timestamp("2020-05-24"), pd.Timestamp("2020-12-06")}
v = V.copy()
v["date"] = pd.Timestamp("2020-01-01") + pd.to_timedelta(v.DAY.astype(int) - 1, unit="D")
v = v[(v.AREA >= bc.FINN2CMAQ_AREA_MIN) & ~v.date.isin(missing)]
parts = [v.assign(product="FINN v1.5 all records"), v[v.role == "original"].assign(product="FINN v1.5 original detections")]
C, n_out = bc.records_to_cells(pd.concat(parts, ignore_index=True)[["product", "date", "LONGI", "LATI", "CO", "PM25"]],
                               G, ["CO", "PM25"])
Bi = B[B.set_index(["i", "j"]).index.isin(interior) & ~B.date.isin(missing)]
out = []
for p, g in C.groupby("product"):
    r = bc.same_version_check(B[~B.date.isin(missing)], g, ["CO", "PM25"], interior)
    gi = g[g.set_index(["i", "j"]).index.isin(interior)]
    r.update(product=p, BRAIN_CO_t=Bi.CO.sum(), product_CO_t=gi.CO.sum(), BRAIN_over_product_CO=Bi.CO.sum() / gi.CO.sum(),
             BRAIN_PM25_t=Bi.PM25.sum(), product_PM25_t=gi.PM25.sum(),
             BRAIN_over_product_PM25=Bi.PM25.sum() / gi.PM25.sum())
    out.append(r)
T2 = pd.DataFrame(out)
cols = ["product"] + [x for x in T2.columns if x != "product"]
T2[cols].to_csv(TAB / "brain2020_finn15_correction.csv", index=False)
for r in T2.itertuples():
    L(f"   {r.product}: CO BRAIN {r.BRAIN_CO_t:,.0f} t vs {r.product_CO_t:,.0f} t (BRAIN/product {r.BRAIN_over_product_CO:.3f}); "
      f"PM2.5 {r.BRAIN_PM25_t:,.0f} vs {r.product_PM25_t:,.0f} t ({r.BRAIN_over_product_PM25:.3f}); "
      f"cell-day CO ratio median {r.CO_ratio_median:.3f}; share of BRAIN CO on common cell-days {r.share_BRAIN_CO_in_common:.3f}")
P = pd.read_csv(ROOT / "results/brain_2019/tables/processing_checks.csv")
L(f"   BRAIN 2019 / FINN v1.5 2019 annual file, every cell-day: median {P.ratio_median.iloc[0]:.4f} "
  f"({int(P.cell_days_both.iloc[0])} cell-days); correction not computed (2019 FINN v1.5 records not in the repository)")

# ------------------------------------------------------------------ 3. continuation signature in FINN v2.5 / v2.5.1
L("3. FINN v2.5 / v2.5.1 records of this inventory: same coordinates as on the previous day")
R = load_records()
res = []
for (yr, sen, ver), g in R.groupby(["year", "sensor", "version"]):
    a = g.groupby(["DAY", "LONGI", "LATI"]).CO2.sum().reset_index()
    b = a.copy(); b["DAY"] += 1
    m = a.merge(b, on=["DAY", "LONGI", "LATI"], suffixes=("", "_prev"))
    half = m[(m.CO2 / m.CO2_prev).between(0.49, 0.51)]
    res.append(dict(year=yr, sensor=sen, version=ver, day_location_pairs=len(a), same_location_previous_day=len(m),
                    of_which_half_CO2=len(half), CO2_t=a.CO2.sum(), CO2_same_location_t=m.CO2.sum(),
                    CO2_half_t=half.CO2.sum()))
T3 = pd.DataFrame(res)
T3.to_csv(TAB / "continuation_check_finn25.csv", index=False)
for (sen, ver), g in T3.groupby(["sensor", "version"]):
    L(f"   {ver} {sen} ({g.year.min()}-{g.year.max()}): {g.day_location_pairs.sum():,} day-location pairs; same location "
      f"as the previous day {g.same_location_previous_day.sum():,} ({g.CO2_same_location_t.sum() / g.CO2_t.sum():.4%} of CO2); "
      f"with half the CO2 {g.of_which_half_CO2.sum():,} ({g.CO2_half_t.sum() / g.CO2_t.sum():.4%} of CO2)")

# ------------------------------------------------------------------ 4. Teixeira et al. (2025) vs FINN v2.5 MODIS
L("4. Teixeira et al. (2025), FINN v1.5 2002-2017 (Table C.1), vs FINN v2.5 MODIS of this inventory, 2003-2017")
TX = pd.read_csv(ROOT / "data/external/teixeira2025_tableC1_SC_finn15.csv").set_index("year")
M = R[(R.sensor == "MODIS") & (R.version == "v2.5")].groupby("year")[["CO2", "CO", "PM25"]].sum()
yrs = [y for y in TX.index if y in M.index and y <= 2017]
v15_20 = {k: V[k].sum() for k in ("CO2", "CO", "PM25")}
o15_20 = {k: o[k].sum() for k in ("CO2", "CO", "PM25")}
m20 = M.loc[2020]
rows4 = []
for y in yrs:
    d = dict(year=y)
    for k in ("CO2", "CO", "PM25"):
        d[f"{k}_teixeira_t"] = TX.loc[y, f"{k}_t"]; d[f"{k}_finn25_modis_t"] = M.loc[y, k]
        d[f"{k}_ratio"] = TX.loc[y, f"{k}_t"] / M.loc[y, k]
    rows4.append(d)
for lab, ref in (("2020 benchmark, FINN v1.5 all records / FINN v2.5 MODIS", v15_20),
                 ("2020 benchmark, FINN v1.5 original detections / FINN v2.5 MODIS", o15_20)):
    d = dict(year=lab)
    for k in ("CO2", "CO", "PM25"):
        d[f"{k}_teixeira_t"] = ref[k]; d[f"{k}_finn25_modis_t"] = m20[k]; d[f"{k}_ratio"] = ref[k] / m20[k]
    rows4.append(d)
T4 = pd.DataFrame(rows4)
T4.to_csv(TAB / "teixeira2025_vs_finn25_modis.csv", index=False)
Y = T4[T4.year.apply(lambda x: isinstance(x, (int, np.integer)))]
from scipy.stats import spearmanr  # noqa: E402
for k in ("CO2", "CO", "PM25"):
    rho = spearmanr(Y[f"{k}_teixeira_t"], Y[f"{k}_finn25_modis_t"])
    b = T4[~T4.index.isin(Y.index)][f"{k}_ratio"].tolist()
    L(f"   {k}: Teixeira / FINN v2.5 MODIS, {Y.year.min()}-{Y.year.max()}: median {Y[f'{k}_ratio'].median():.3f} "
      f"(range {Y[f'{k}_ratio'].min():.3f}-{Y[f'{k}_ratio'].max():.3f}); Spearman rho between the annual series "
      f"{rho.statistic:.3f} (p = {rho.pvalue:.2g}); 2020 FINN v1.5 / FINN v2.5 MODIS: all records {b[0]:.3f}, "
      f"original detections {b[1]:.3f}")
for r in Y.itertuples():
    L(f"   {r.year}: CO2 ratio {r.CO2_ratio:.3f}; CO {r.CO_ratio:.3f}; PM2.5 {r.PM25_ratio:.3f}")

# ------------------------------------------------------------------ 5. FINN v1.5 2019 and BRAIN 2019
L("5. FINN v1.5 records of 2019 in SC: next-day continuations, and BRAIN 2019 with and without them")
W = pd.read_csv(ROOT / "data/external/finn15_2019_SC_records.csv")
W["key"] = list(zip(W.LONGI.round(5), W.LATI.round(5)))
pv = W[["DAY", "key", "CO2"]].copy(); pv["DAY"] += 1
pv = pv.groupby(["DAY", "key"], as_index=False).CO2.sum()
W = W.merge(pv.rename(columns={"CO2": "CO2_prev"}), on=["DAY", "key"], how="left")
W["role"] = np.where((W.CO2 / W.CO2_prev).between(0.45, 0.55), "continuation", "original")
w_o, w_c = W[W.role == "original"], W[W.role == "continuation"]
rows5 = [dict(metric=k, all_records=W[k].sum(), original_detections=w_o[k].sum(),
              continuation_share=w_c[k].sum() / W[k].sum()) for k in ("CO2", "CO", "PM25")]
rows5.append(dict(metric="records", all_records=len(W), original_detections=len(w_o), continuation_share=len(w_c) / len(W)))
L(f"   records {len(W)}: {len(w_o)} original detections, {len(w_c)} continuations; CO2 {W.CO2.sum():,.0f} t, "
  f"without continuations {w_o.CO2.sum():,.0f} t (continuation share {w_c.CO2.sum() / W.CO2.sum():.4f})")
B9 = pd.read_csv(ROOT / "results/brain_2019/tables/brain_cells_daily_t.csv.gz", parse_dates=["date"])
FS9 = pd.read_csv(ROOT / "results/brain_2019/tables/cell_fraction_SC.csv")
int9 = pd.MultiIndex.from_frame(FS9.loc[FS9.fSC >= 0.999, ["i", "j"]])
W["date"] = pd.Timestamp("2019-01-01") + pd.to_timedelta(W.DAY.astype(int) - 1, unit="D")
w = W[W.AREA >= bc.FINN2CMAQ_AREA_MIN]
C9, _ = bc.records_to_cells(pd.concat([w.assign(product="FINN v1.5 all records"),
                                       w[w.role == "original"].assign(product="FINN v1.5 original detections")],
                                      ignore_index=True)[["product", "date", "LONGI", "LATI", "CO", "PM25"]], G, ["CO", "PM25"])
Bi9 = B9[B9.set_index(["i", "j"]).index.isin(int9)]
for p, g in C9.groupby("product"):
    r = bc.same_version_check(B9, g, ["CO", "PM25"], int9)
    gi = g[g.set_index(["i", "j"]).index.isin(int9)]
    rows5.append(dict(metric=f"BRAIN 2019 / {p} (cells inside SC)", all_records=Bi9.CO.sum() / gi.CO.sum(),
                      original_detections=Bi9.PM25.sum() / gi.PM25.sum(), continuation_share=r["share_BRAIN_CO_in_common"]))
    L(f"   BRAIN 2019 / {p}: CO {Bi9.CO.sum():,.0f} / {gi.CO.sum():,.0f} t = {Bi9.CO.sum() / gi.CO.sum():.3f}; PM2.5 "
      f"{Bi9.PM25.sum() / gi.PM25.sum():.3f}; cell-day CO ratio median {r['CO_ratio_median']:.4f}; share of BRAIN CO on "
      f"common cell-days {r['share_BRAIN_CO_in_common']:.3f}")
T5 = pd.DataFrame(rows5)
T5.to_csv(TAB / "finn15_2019_correction.csv", index=False)
L("   (rows BRAIN 2019 / ...: column all_records = CO ratio, original_detections = PM2.5 ratio, "
  "continuation_share = share of BRAIN CO on common cell-days)")

# ------------------------------------------------------------------ 6. the authors' aggregated file of 5 Feb 2026
L("6. Authors' aggregated file (aggregated_emissions_all.csv, 5 Feb 2026) against this inventory, FINN v1.5 records "
  "and Teixeira et al. (2025)")
AG = pd.read_csv(ROOT / "data/external/legacy_aggregated_emissions_all_2026-02-05.csv", low_memory=False).dropna(subset=["year"])
AG["year"] = AG.year.astype(int)
rows6 = []
a = AG[AG.version != "v1.5"].groupby(["version", "sensor", "year"]).agg(n=("focos", "sum"), CO2=("CO2", "sum"))
b = R.groupby(["version", "sensor", "year"]).agg(n=("CO2", "size"), CO2=("CO2", "sum"))
j = a.join(b, lsuffix="_file", rsuffix="_ref", how="outer")
for (ver, sen, yr), x in j.iterrows():
    rows6.append(dict(version=ver, sensor=sen, year=yr, reference="this inventory (records)", count_file=x.n_file,
                      count_ref=x.n_ref, CO2_file_t=x.CO2_file, CO2_ref_t=x.CO2_ref, CO2_ratio=x.CO2_file / x.CO2_ref))
mm = pd.concat([AG[AG.version != "v1.5"].groupby(["version", "sensor", "year", "CD_MUN"]).CO2.sum().rename("f"),
                R.groupby(["version", "sensor", "year", "CD_MUN"]).CO2.sum().rename("r")], axis=1).fillna(0)
bad = mm[(mm.f - mm.r).abs() >= 1e-3].reset_index()
L(f"   FINN v2.5 / v2.5.1, municipality x year x configuration: {len(mm)} rows, {len(mm) - len(bad)} equal to this "
  f"inventory within 0.001 t; different: {bad.groupby(['version', 'sensor', 'year']).size().to_dict()} "
  f"(file / inventory {(bad.f / bad.r).min():.6f} to {(bad.f / bad.r).max():.6f})")
V15 = AG[AG.version == "v1.5"].groupby("year").agg(n=("focos", "sum"), CO2=("CO2", "sum"), CO=("CO", "sum"), PM25=("PM25", "sum"))
ref15 = {2019: (len(W), W.CO2.sum()), 2020: (len(V), V.CO2.sum())}
for yr in sorted(set(V15.index) | set(TX.index)):
    f = V15.loc[yr] if yr in V15.index else None
    if yr in ref15:
        rows6.append(dict(version="v1.5", sensor="MODIS", year=yr, reference="FINN v1.5 records in SC (this repository)",
                          count_file=f.n, count_ref=ref15[yr][0], CO2_file_t=f.CO2, CO2_ref_t=ref15[yr][1],
                          CO2_ratio=f.CO2 / ref15[yr][1]))
    if yr in TX.index:
        rows6.append(dict(version="v1.5", sensor="MODIS", year=yr, reference="Teixeira et al. (2025), Table C.1",
                          count_file=f.n if f is not None else np.nan, count_ref=np.nan,
                          CO2_file_t=f.CO2 if f is not None else np.nan, CO2_ref_t=TX.loc[yr, "CO2_t"],
                          CO2_ratio=(f.CO2 / TX.loc[yr, "CO2_t"]) if f is not None else np.nan))
T6 = pd.DataFrame(rows6)
T6.to_csv(TAB / "legacy_aggregated_check.csv", index=False)
x = T6[(T6.version == "v1.5") & T6.reference.str.startswith("Teixeira")]
for r in x.itertuples():
    L(f"   v1.5 {r.year}: file CO2 {r.CO2_file_t:,.0f} t vs Teixeira {r.CO2_ref_t:,.0f} t (ratio {r.CO2_ratio:.4f})")
same = [y for y in (2016, 2017) if y in V15.index and abs(V15.loc[y, "CO2"] - V15.loc[2015, "CO2"]) < 1e-6]
L(f"   FINN v1.5 years of the file identical to 2015: {same}; years missing from the file: "
  f"{sorted(set(range(2002, 2021)) - set(V15.index))}")
for r in T6[T6.reference.str.startswith("FINN v1.5 records")].itertuples():
    L(f"   v1.5 {r.year}: file {int(r.count_file)} records, CO2 {r.CO2_file_t:,.1f} t; records in this repository "
      f"{int(r.count_ref)}, CO2 {r.CO2_ref_t:,.1f} t")

# ------------------------------------------------------------------ 7. FINN v1.5 2002-2020, with and without continuations
L("7. FINN v1.5 records of SC 2002-2020: next-day continuations by year, Teixeira et al. (2025), FINN v2.5 MODIS")
F15 = pd.read_csv(ROOT / "data/external/finn15_SC_records_2002_2020.csv")
FI = pd.read_csv(ROOT / "data/external/finn15_SC_records_2002_2020_files.csv")
for r in FI[FI.status != "ok"].itertuples():
    L(f"   {r.year}: {r.status} -> excluded")
for r in FI[FI.source == "ncar"].itertuples():
    L(f"   {r.year}: NCAR annual file ({r.file})" + (f"; {r.rejected}" if isinstance(getattr(r, 'rejected', None), str) else ""))
for r in FI[FI.check_source.notna()].itertuples():
    L(f"   {r.year}: check with the {r.check_source} file: {int(r.check_records_SC)} records, CO2 {r.check_CO2_SC_t:,.1f} t "
      f"(used: {int(r.records_SC)} records, CO2 {r.CO2_SC_t:,.1f} t)")
for r in FI[(FI.status == "ok") & ((FI.duplicate_lines > 0) | (FI.malformed_lines > 0))].itertuples():
    L(f"   {r.year}: {int(r.duplicate_lines)} duplicate lines and {int(r.malformed_lines)} malformed lines dropped")
rows7 = []
for yr, g in F15.groupby("year"):
    g = g.copy()
    g["key"] = list(zip(g.LONGI.round(5), g.LATI.round(5)))
    p = g[["DAY", "key", "CO2"]].copy(); p["DAY"] += 1
    p = p.groupby(["DAY", "key"], as_index=False).CO2.sum()
    g = g.merge(p.rename(columns={"CO2": "CO2_prev"}), on=["DAY", "key"], how="left")
    cont = (g.CO2 / g.CO2_prev).between(0.45, 0.55)
    d = dict(year=yr, records=len(g), continuations=int(cont.sum()))
    for k in ("CO2", "CO", "PM25"):
        d[f"{k}_all_t"] = g[k].sum(); d[f"{k}_original_t"] = g.loc[~cont, k].sum()
        d[f"{k}_continuation_share"] = g.loc[cont, k].sum() / g[k].sum()
        if yr in TX.index:
            d[f"{k}_teixeira_t"] = TX.loc[yr, f"{k}_t"]
            d[f"{k}_teixeira_over_all"] = TX.loc[yr, f"{k}_t"] / d[f"{k}_all_t"]
        if yr in M.index:
            d[f"{k}_all_over_finn25_modis"] = d[f"{k}_all_t"] / M.loc[yr, k]
            d[f"{k}_original_over_finn25_modis"] = d[f"{k}_original_t"] / M.loc[yr, k]
    rows7.append(d)
T7 = pd.DataFrame(rows7)
T7.to_csv(TAB / "finn15_2002_2020_correction.csv", index=False)
for r in T7.itertuples():
    tx = f"; Teixeira / all records {r.CO2_teixeira_over_all:.4f}" if pd.notna(getattr(r, "CO2_teixeira_over_all", np.nan)) else ""
    L(f"   {r.year}: {r.records} records, {r.continuations} continuations ({r.CO2_continuation_share:.1%} of CO2); CO2 all "
      f"{r.CO2_all_t / 1e6:.3f} Mt, without continuations {r.CO2_original_t / 1e6:.3f} Mt{tx}; v1.5/v2.5 MODIS "
      f"{r.CO2_all_over_finn25_modis:.2f} -> {r.CO2_original_over_finn25_modis:.2f}")
L(f"   continuation share of CO2, {T7.year.min()}-{T7.year.max()} ({len(T7)} years): median "
  f"{T7.CO2_continuation_share.median():.1%} (range {T7.CO2_continuation_share.min():.1%}-{T7.CO2_continuation_share.max():.1%})")
L.save()
