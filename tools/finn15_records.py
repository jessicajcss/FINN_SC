#!/usr/bin/env python3
"""tools/finn15_records.py - FINN v1.5 records inside Santa Catarina, 2002-2020.

Sources, in order of priority:
1. AUTHORS_DIR: the authors' per-year files `data_finn_<year>/filtered_points_<year>_MODIS_v1.5_converted_within_grid*.txt`
   (original R scripts, June 2025, step "converted_within_grid": FINN v1.5 GEOS-Chem annual files, MODIS, rows inside the
   grid box, species in tonnes, AREA in m2; uploaded by the authors on 9 Nov 2026 to after_08112026read/data; not
   distributed). Lines are parsed one by one: header lines, lines with the wrong number of fields and exact duplicate
   lines are counted and dropped (the 2009 file has its header in line 7,643 and a truncated first line). The 2020 file
   keeps the source URL before DAY, separated by a tab.
2. NCAR_DIR (optional): the same layout written by tools/finn15_raw_to_grid.py from the NCAR FINN v1.5 annual files
   downloaded by the authors on 11 Nov 2026 (2002, 2015, 2016, 2017; not distributed). Used for a year whose authors'
   file is missing (2002) or identical to the file of another year (2016 and 2017 are copies of 2015). When both
   sources exist and differ, the second one is reported as a check (columns check_*; 2015).
Points are assigned to the IBGE 2024 municipalities by point in polygon (data/inputs/SC_Municipios_2024.shp).
Usage: python tools/finn15_records.py AUTHORS_DIR [NCAR_DIR]
-> data/external/finn15_SC_records_2002_2020.csv and data/external/finn15_SC_records_2002_2020_files.csv (file check)
"""
import hashlib, io, sys
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRCS = [Path(a) for a in sys.argv[1:]]
LABEL = ["authors", "ncar"]
KEEP = ["DAY", "GENVEG", "AREA", "CO2", "CO", "PM25", "NO", "NO2", "SO2", "NH3", "CH4", "OC", "BC", "LONGI", "LATI"]
shp = gpd.read_file(ROOT / "data" / "inputs" / "SC_Municipios_2024.shp", columns=["CD_MUN"]).to_crs(4674)


def read_file(f):
    raw = f.read_bytes(); h = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    hdr_line = next(l for l in lines if "DAY," in l and "LONGI" in l)
    url = "\t" in hdr_line
    cols = hdr_line.split("\t")[-1].split(",")
    good, n_hdr, n_bad = [], 0, 0
    for l in lines:
        if "DAY," in l and "LONGI" in l:
            n_hdr += 1; continue
        body = l.split("\t")[-1] if url else l
        if body.count(",") + 1 != len(cols):
            n_bad += 1; continue
        good.append(body)
    n_dup = len(good) - len(set(good))
    d = pd.read_csv(io.StringIO("\n".join([",".join(cols)] + list(dict.fromkeys(good)))))
    d.columns = [c.strip() for c in d.columns]
    pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.LONGI, d.LATI), crs=4674)
    s = gpd.sjoin(pts, shp[["CD_MUN", "geometry"]], how="inner", predicate="within")
    s = s[~s.index.duplicated()]
    return h, s, dict(file=f.name, sha256=h[:16], lines=len(lines), header_lines=n_hdr, malformed_lines=n_bad,
                      duplicate_lines=n_dup, records_box=len(d), records_SC=len(s), CO2_SC_t=s.CO2.sum())


rows, info, seen = [], [], {}
for y in range(2002, 2021):
    cands = []
    for k, src in enumerate(SRCS):
        fs = sorted((src / f"data_finn_{y}").glob(f"filtered_points_{y}_MODIS_v1.5_converted_within_grid*.txt"))
        if fs:
            cands.append((LABEL[k], fs[0]))
    rec, used = dict(year=y, source="", status="missing"), None
    for lab, f in cands:
        h, s, meta = read_file(f)
        if h in seen and seen[h] != y:
            rec.setdefault("rejected", f"{lab}: {f.name} identical to {seen[h]}")
            continue
        if used is None:
            used = (lab, s); seen[h] = y
            rec.update(meta); rec.update(source=lab, status="ok")
        else:
            rec.update(check_source=lab, check_file=f.name, check_records_SC=meta["records_SC"],
                       check_CO2_SC_t=meta["CO2_SC_t"])
    if used is not None:
        s = used[1][KEEP + ["CD_MUN"]].copy(); s.insert(0, "year", y); rows.append(s)
    info.append(rec)
    print({k: v for k, v in rec.items() if k in ("year", "source", "status", "records_SC", "CO2_SC_t", "rejected",
                                                  "check_records_SC", "check_CO2_SC_t")})
out = ROOT / "data" / "external" / "finn15_SC_records_2002_2020.csv"
pd.concat(rows, ignore_index=True).to_csv(out, index=False)
pd.DataFrame(info).to_csv(ROOT / "data" / "external" / "finn15_SC_records_2002_2020_files.csv", index=False)
print("->", out.relative_to(ROOT))
