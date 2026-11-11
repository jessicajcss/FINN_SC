#!/usr/bin/env python3
"""tools/finn15_raw_to_grid.py - NCAR FINN v1.5 GEOS-Chem annual file -> records in the Santa Catarina grid box, in tonnes.

Input: a FINN v1.5 GEOS-Chem annual file as distributed by NSF NCAR ACOM (https://www.acom.ucar.edu/Data/fire/), either
the .tar.gz archive, a .txt.gz file or the extracted .txt file. Header: DAY,TIME,GENVEG,LATI,LONGI,AREA,CO2,CO,...,PM25;
fields padded with blanks.
Output: <out_dir>/data_finn_<year>/filtered_points_<year>_MODIS_v1.5_converted_within_grid_ncar.txt with the columns
DAY,TIME,GENVEG,AREA,CO2,CO,NO,NO2,SO2,NH3,CH4,OC,BC,PM25,LONGI,LATI (AREA in m2, species in tonnes per record), the
layout read by tools/finn15_records.py.
Grid box: longitude -54.2 to -47.1, latitude -30.3 to -23.8 (it contains the extent of the authors' converted files,
-53.99 to -47.34 and -30.04 to -24.02 in 2015); the State is selected later by point in polygon.
Units: gases are converted with factor = molar mass (g/mol) x 1e-6 and OC, BC and PM2.5 with 1e-3, the factors of the
authors' converted files (gases in mol/day and aerosols in kg/day, as in python/finn_sc/convert_units.py). Check of
11 Nov 2026: the 2015 NCAR file converted with this tool reproduces all 3,537 rows of the authors' 2015 file (same DAY,
TIME, GENVEG and coordinates) with these factors.
Usage: python tools/finn15_raw_to_grid.py <raw file> <year> <out_dir>
"""
import gzip, io, sys, tarfile
from pathlib import Path

BOX = dict(lon=(-54.2, -47.1), lat=(-30.3, -23.8))
FACTOR = {"CO2": 44.01e-6, "CO": 28.01e-6, "NO": 30.01e-6, "NO2": 46.01e-6, "SO2": 64.07e-6, "NH3": 17.03e-6,
          "CH4": 16.04e-6, "OC": 1e-3, "BC": 1e-3, "PM25": 1e-3}
OUT_COLS = ["DAY", "TIME", "GENVEG", "AREA"] + list(FACTOR) + ["LONGI", "LATI"]


def lines_of(path):
    p = str(path)
    if p.endswith(".tar.gz") or p.endswith(".tgz"):
        tf = tarfile.open(p, mode="r|gz")
        for m in tf:
            if m.isfile() and m.name.lower().endswith(".txt"):
                for b in tf.extractfile(m):
                    yield b.decode("ascii", errors="replace")
                return
        raise SystemExit("no .txt member in " + p)
    opener = gzip.open if p.endswith(".gz") else open
    with opener(p, "rt", encoding="ascii", errors="replace") as fh:
        yield from fh


def main(raw, year, out_dir):
    it = lines_of(raw)
    header = [c.strip() for c in next(it).split(",")]
    ix = {c: i for i, c in enumerate(header)}
    n_in = n_out = 0
    out = Path(out_dir) / f"data_finn_{year}"
    out.mkdir(parents=True, exist_ok=True)
    fn = out / f"filtered_points_{year}_MODIS_v1.5_converted_within_grid_ncar.txt"
    with open(fn, "w", newline="\n") as fo:
        fo.write(",".join(OUT_COLS) + "\n")
        for line in it:
            f = line.split(",")
            if len(f) < len(header):
                continue
            n_in += 1
            try:
                lat = float(f[ix["LATI"]]); lon = float(f[ix["LONGI"]])
            except ValueError:
                continue
            if not (BOX["lat"][0] <= lat <= BOX["lat"][1] and BOX["lon"][0] <= lon <= BOX["lon"][1]):
                continue
            row = [str(int(float(f[ix["DAY"]]))), str(int(float(f[ix["TIME"]]))), str(int(float(f[ix["GENVEG"]]))),
                   repr(float(f[ix["AREA"]]))]
            row += [repr(float(f[ix[s]]) * k) for s, k in FACTOR.items()]
            row += [f[ix["LONGI"]].strip(), f[ix["LATI"]].strip()]
            fo.write(",".join(row) + "\n")
            n_out += 1
    print(f"{year}: {n_in:,} records read, {n_out:,} in the grid box -> {fn}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
