"""BRAIN fire emissions on the FINN_SC records: daily cell tables and the same-cell check of BRAIN 2020.

1. --cells YEAR CACHE_DIR: BRAIN daily cells (tonnes) from the cache of notebooks/BRAIN_FINN_comparison_SC.ipynb
   (cache_days/*.csv.gz and *.json), files on another grid excluded -> results/brain_YEAR/tables/brain_cells_daily_t.csv.gz
2. --check2020: BRAIN 2020 against FINN v1.5 2020 (data/external/finn15_2020_SC_records.csv) and FINN v2.5 MODIS and
   MODIS+VIIRS 2020 (data/derived/finn_sc_records_2003_2025.csv.gz), cell by cell in the cells entirely inside SC
   -> results/brain_2020/tables/check_cell_days_R1_finn15_finn25.csv
3. --check2019: the same check for BRAIN 2019 against FINN v2.5 MODIS and MODIS+VIIRS 2019 (control: in 2019 BRAIN equals
   the FINN v1.5 annual file x 1.01 in every cell-day, results/brain_2019/tables/processing_checks.csv)
   -> results/brain_2019/tables/check_cell_days_R1_finn25.csv
Run from the repository root: python tools/brain_cells_and_finn15_check.py --check2020 (or --check2019)
"""
import glob, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "notebooks"))
import brain_core as bc  # noqa: E402

SPEC_OLD = "finn2cmaq <= 2022-08-04 (BRAIN Table S3)"


def cells(year, cache):
    days = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(cache, "*.json")))]
    bad = {d["date"] for d in days if d.get("grid_mismatch")}
    parts = [pd.read_csv(p, parse_dates=["date"]) for p in sorted(glob.glob(os.path.join(cache, "*.csv.gz")))
             if os.path.basename(p)[:10] not in bad]
    raw = pd.concat([x for x in parts if len(x)], ignore_index=True)
    out = bc.brain_to_tonnes(raw, None, SPEC_OLD)
    dst = ROOT / f"results/brain_{year}/tables/brain_cells_daily_t.csv.gz"
    out.to_csv(dst, index=False, float_format="%.6g")
    print(year, "BRAIN cell-days:", len(out), "| days excluded (other grid):", sorted(bad), "->", dst.relative_to(ROOT))


def check(year):
    T = ROOT / f"results/brain_{year}/tables"
    B = pd.read_csv(T / "brain_cells_daily_t.csv.gz", parse_dates=["date"])
    FS = pd.read_csv(T / "cell_fraction_SC.csv")
    interior = pd.MultiIndex.from_frame(FS.loc[FS.fSC >= 0.999, ["i", "j"]])
    G = bc.Grid.from_attrs(bc.EXPECTED_GRID)
    missing = {pd.Timestamp("2020-05-24"), pd.Timestamp("2020-12-06")} if year == 2020 else set()
    days = (set(B.date.unique()) | set(pd.date_range(f"{year}-01-01", f"{year}-12-31"))) - missing
    rec = bc.load_records(ROOT / "data/derived/finn_sc_records_2003_2025.csv.gz", year)
    rec["PM25"] = rec["PM25"].astype(float)
    parts = [rec[["product", "date", "LONGI", "LATI", "CO", "PM25"]]]
    if year == 2020:
        v = pd.read_csv(ROOT / "data/external/finn15_2020_SC_records.csv")
        v["DAY"] = v["DAY"].astype(str).str.split("\t").str[-1].astype(int)     # the file keeps the source URL before DAY
        v["date"] = pd.Timestamp("2020-01-01") + pd.to_timedelta(v.DAY - 1, unit="D")
        v = v[v.AREA >= bc.FINN2CMAQ_AREA_MIN].assign(product="FINN v1.5 MODIS (annual file)")
        parts.insert(0, v[["product", "date", "LONGI", "LATI", "CO", "PM25"]])
    data = pd.concat(parts, ignore_index=True)
    data = data[data.date.isin(days)]
    C, n_out = bc.records_to_cells(data, G, ["CO", "PM25"])
    rows = []
    for p, g in C.groupby("product"):
        r = bc.same_version_check(B, g, ["CO", "PM25"], interior)
        b = B[B.set_index(["i", "j"]).index.isin(interior)].groupby("date").CO.sum()
        q = g[g.set_index(["i", "j"]).index.isin(interior)].groupby("date").CO.sum()
        r.update(fire_days_BRAIN=int((b > 0).sum()), fire_days_product=int((q > 0).sum()),
                 fire_days_both=len(set(b[b > 0].index) & set(q[q > 0].index)),
                 total_CO_ratio_BRAIN_over_product=float(B[B.set_index(["i", "j"]).index.isin(interior)].CO.sum()
                                                         / g[g.set_index(["i", "j"]).index.isin(interior)].CO.sum()))
        rows.append(dict(product=p, **r))
    out = pd.DataFrame(rows).set_index("product")
    out.to_csv(T / ("check_cell_days_R1_finn15_finn25.csv" if year == 2020 else "check_cell_days_R1_finn25.csv"))
    print(out.T.round(4).to_string())


if __name__ == "__main__":
    if sys.argv[1] == "--cells":
        cells(int(sys.argv[2]), sys.argv[3])
    elif sys.argv[1] == "--check2020":
        check(2020)
    elif sys.argv[1] == "--check2019":
        check(2019)
