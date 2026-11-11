"""brain_core.py - BRAIN (FINN v1.5 via finn2cmaq) vs FINN_SC records, same grid and region.

Every rule that reproduces how the BRAIN fire files were built comes from the code
that built them, read on 2026-11-01:
  * finn2cmaq (B. Henderson, https://github.com/barronh/finn2cmaq), commit 88bb2f6
    (2022-08-04): scripts/txt2daily.py, scripts/daily2hourly3d.py, aux/tpro.txt,
    aux/layerfrac.csv, aux/gc12_to_cb6r3_ae7.txt, run_nrt.sh. The species list of that
    commit is the list of Table S3 of Hoinaski et al. (2024, ESSD 16, 2385-2405).
  * PseudoNetCDF 3.5.0 and 3.2.2 (ll2ij, ij2ll, IOAPI map definition), the library
    finn2cmaq uses to put each FINN fire on the CMAQ grid.
Grid of the BRAIN d02 domain (SC_2019): attributes of the BRAIN MEGAN file
MEGANv31.SC_2019.CB6X.2020015.BDSNP.ncf (same dataset, same grid).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import itertools
import json
import os
import re
import shutil
import tarfile
import time
import urllib.parse as up
import zipfile
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

__version__ = "1.1.1"

# ---------------------------------------------------------------------------
# 0. Constants copied from the sources named above
# ---------------------------------------------------------------------------
EXPECTED_GRID = dict(GDTYP=7, P_ALP=0.0, P_BET=0.0, P_GAM=-54.856998443603516,
                     XCENT=-54.856998443603516, YCENT=0.0, XORIG=-105999.8125,
                     YORIG=-3507558.25, XCELL=4000.0, YCELL=4000.0, NCOLS=233, NROWS=243)
GRID_KEYS = list(EXPECTED_GRID)

# PseudoNetCDF uses IOAPI_ISPH when set, otherwise 6370000 m ("consistent with WRF").
IOAPI_SPHERE_RADIUS = 6370000.0

# finn2cmaq aux/tpro.txt: hour1..hour24 in LOCAL time; finn2cmaq always uses the FIRST row.
# Before 2022-09-16 the first row was profile 210; afterwards it is 1008.
TPRO = {
    210: [0.00533091933213] * 7 + [0.020116676725, 0.04023335345, 0.0704083685375,
          0.100583383625, 0.130758398713, 0.1609334138, 0.170991752163, 0.12070006035,
          0.0704083685375, 0.04023335345] + [0.00533091933213] * 7,
    1008: [0.6, 0.6, 0.6, 0.6, 0.6, 0.65, 0.75, 0.9, 1.1, 1.25, 1.45, 1.6, 1.8, 1.75, 1.7,
           1.55, 1.35, 1.1, 0.9, 0.75, 0.65, 0.6, 0.6, 0.6],
    500: [0.0] * 8 + [0.0416208104052, 0.0416208104052, 0.0833416708354, 0.0833416708354,
          0.125062531266, 0.166683341671, 0.125062531266, 0.0833416708354, 0.0833416708354,
          0.0833416708354, 0.0416208104052, 0.0416208104052] + [0.0] * 4,
}
# finn2cmaq aux/layerfrac.csv (first 20 rows; identical in every commit). The fractions sum to 1.01.
DEFAULT_LAYERFRAC = [0.125, 0.125] + [0.05] * 8 + [0.04] * 9 + [0.0]

# finn2cmaq aux/gc12_to_cb6r3_ae7.txt: PM speciation (fractions of FINN PM25, per kg -> g).
SPECIATION = {
    "finn2cmaq <= 2022-08-04 (BRAIN Table S3)": dict(
        f_so4=0.0126, f_no3=0.0013, marker=None,
        pm_vars=["POC", "PEC", "PSO4", "PNO3", "PMOTHR"]),
    "finn2cmaq >= 2022-08-05 (SPECIATE 91102)": dict(
        f_so4=0.0126015, f_no3=0.001323, marker="PNCOM",
        pm_vars=["POC", "PNCOM", "PEC", "PSO4", "PNO3", "PNH4", "PCL", "PAL", "PCA", "PFE",
                 "PMG", "PMN", "PK", "PSI", "PNA", "PTI", "PMOTHR"]),
}
GAS_VARS = ["CO", "NO", "NO2", "SO2", "NH3", "ECH4"]   # moles/s ; ECH4 = FINN CH4 in finn2cmaq
BASE_PM_VARS = ["POC", "PEC", "PSO4", "PNO3", "PMOTHR"]  # g/s

# Species compared and the column of the FINN_SC records (tonnes) that matches each one.
SPECIES = ["CO", "NOx", "SO2", "NH3", "CH4", "PM25", "OC", "BC"]   # PM10 is added when the files hold PMC
OURS_COLUMN = dict(CO="CO", NOx="NOXasNO", SO2="SO2", NH3="NH3", CH4="CH4",
                   PM25="PM25", OC="OC", BC="BC", PM10="PM10")
SPECIES_LABEL = dict(CO="CO", NOx="NOx (as NO)", SO2="SO2", NH3="NH3", CH4="CH4",
                     PM25="PM2.5", OC="OC", BC="BC", PM10="PM10")
# Fallback molar masses (g/mol) = FINN_SC config/config.yml (conversion.molar_mass_g_per_mol).
DEFAULT_MOLAR_MASS = {"CO": 28.01, "NO": 30.01, "NO2": 46.01, "SO2": 64.07, "NH3": 17.03, "CH4": 16.04}

# FINN v1.5 GEOS-Chem column order used by FINN_SC (python/finn_sc/download.py).
FINN_V15_COLNAMES = [
    "DAY", "TIME", "GENVEG", "LATI", "LONGI", "AREA", "CO2", "CO", "NO", "NO2",
    "SO2", "NH3", "CH4", "ACET", "ALD2", "ALK4", "BENZ", "C2H2", "C2H4", "C2H6",
    "C3H8", "CH2O", "GLYC", "GLYX", "HAC", "MEK", "MGLY", "PRPE", "TOLU", "XYLE",
    "OC", "BC", "PM25",
]
FINN15_ANNUAL_URLS = ["https://www.acom.ucar.edu/Data/fire/data/finn1/FINNv1.5_{year}.GEOSCHEM.tar.gz",
                      "https://www.acom.ucar.edu/Data/fire/data/finn1/FINNv1.5_{year}.GEOSCHEM.txt.gz"]
# finn2cmaq scripts/get_nrt.py
FINN15_NRT_URL = "https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt/GLOB_GEOSchem_{yj}.txt.gz"
FINN2CMAQ_AREA_MIN = 50.0   # txt2daily drops fires with AREA < 50 m2 ("assumed false detect")


def md5(path, block=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def _py(v):
    """numpy / bytes attribute -> plain JSON-friendly Python."""
    if isinstance(v, bytes):
        return v.decode("latin1").strip()
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, np.ndarray):
        return [_py(x) for x in v.tolist()]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


# ---------------------------------------------------------------------------
# 1. Grid: replica of PseudoNetCDF (GDTYP 7) as called by finn2cmaq
# ---------------------------------------------------------------------------
@dataclass
class Grid:
    GDTYP: int
    P_ALP: float
    P_BET: float
    P_GAM: float
    XCENT: float
    YCENT: float
    XORIG: float
    YORIG: float
    XCELL: float
    YCELL: float
    NCOLS: int
    NROWS: int
    R: float = IOAPI_SPHERE_RADIUS

    @classmethod
    def from_attrs(cls, attrs, R=IOAPI_SPHERE_RADIUS):
        kw = {k: _py(attrs[k]) for k in GRID_KEYS}
        kw["GDTYP"], kw["NCOLS"], kw["NROWS"] = int(kw["GDTYP"]), int(kw["NCOLS"]), int(kw["NROWS"])
        return cls(R=R, **kw)

    def _proj(self):
        import pyproj
        if self.GDTYP != 7:
            raise NotImplementedError("only IOAPI GDTYP 7 (equatorial Mercator) is implemented")
        # PseudoNetCDF asserts these two equalities for GDTYP 7 before building the projection.
        if not (self.P_ALP == self.YCENT and self.P_GAM == self.XCENT):
            raise ValueError("GDTYP 7 requires P_ALP == YCENT and P_GAM == XCENT (PseudoNetCDF rule)")
        # PseudoNetCDF: +proj=merc (+lat_0=YCENT) +lon_0=XCENT +a=+b=R (+lat_ts defaults to 0)
        return pyproj.Proj(f"+proj=merc +lat_ts=0 +lon_0={self.XCENT!r} +x_0=0 +y_0=0 "
                           f"+a={self.R!r} +b={self.R!r} +units=m +no_defs")

    def ll2index(self, lon, lat):
        """lon/lat (deg) -> continuous grid coordinates (0 at the SW corner of cell 0)."""
        p = self._proj()
        x, y = p(np.asarray(lon, dtype="f8"), np.asarray(lat, dtype="f8"))
        return (np.asarray(x) - self.XORIG) / self.XCELL, (np.asarray(y) - self.YORIG) / self.YCELL

    def ll2ij(self, lon, lat):
        """PseudoNetCDF ll2ij(clean='mask'): truncation toward zero, then out-of-domain mask."""
        xg, yg = self.ll2index(lon, lat)
        i = np.asarray(xg).astype("i")
        j = np.asarray(yg).astype("i")
        inside = (i >= 0) & (i < self.NCOLS) & (j >= 0) & (j < self.NROWS)
        return i, j, inside

    def ij2ll(self, i, j):
        """Cell-centre lon/lat (PseudoNetCDF ij2ll uses i + 0.5, j + 0.5)."""
        p = self._proj()
        x = (np.asarray(i, dtype="f8") + 0.5) * self.XCELL + self.XORIG
        y = (np.asarray(j, dtype="f8") + 0.5) * self.YCELL + self.YORIG
        return p(x, y, inverse=True)


def compare_grid(attrs, expected=EXPECTED_GRID, rtol=1e-7):
    """List of (key, found, expected) for every grid attribute that differs."""
    bad = []
    for k, ev in expected.items():
        fv = _py(attrs.get(k)) if k in attrs else None
        if fv is None or not np.isclose(float(fv), float(ev), rtol=rtol, atol=1e-6):
            bad.append((k, fv, ev))
    return bad


# ---------------------------------------------------------------------------
# 2. finn2cmaq time and layer allocation (for diagnostics)
# ---------------------------------------------------------------------------
def tfactor25(hours24):
    """finn2cmaq gettemporal before the time-zone roll: 25 instantaneous hourly factors."""
    t = np.asarray(hours24, dtype="f8")
    t = t / t.sum()
    tt = np.append(np.append(t[-1], t), t[0])
    xc = np.arange(tt.size)
    return np.interp(xc[:-1] + 0.5, xc, tt)


def tz_offset(lon):
    """finn2cmaq: (lon / 15).round(0) (numpy rounds half to even)."""
    return np.round(np.asarray(lon, dtype="f8") / 15.0, 0).astype(int)


def hourly_factors(profile_id, tzoff):
    return np.roll(tfactor25(TPRO[profile_id]), -int(tzoff))


def match_time_profile(vec25, tzoff):
    """Compare a cell's 25 hourly values (shape only) with every finn2cmaq profile."""
    v = np.asarray(vec25, dtype="f8")
    if v.size != 25 or v.sum() <= 0:
        return dict(best=None, max_abs_diff={})
    v = v / v.sum()
    diffs = {}
    for pid in TPRO:
        e = hourly_factors(pid, tzoff)
        diffs[pid] = float(np.abs(v - e / e.sum()).max())
    best = min(diffs, key=diffs.get)
    return dict(best=best, max_abs_diff=diffs, matched=diffs[best] < 1e-4,
                S24=float(hourly_factors(best, tzoff)[:24].sum()))


def match_layers(vecz):
    """Compare a cell's layer distribution (shape only) with the default layerfrac.csv."""
    v = np.asarray(vecz, dtype="f8")
    if v.sum() <= 0:
        return dict(matched=None)
    nz = v.size
    ref = np.zeros(nz)
    n = min(nz, len(DEFAULT_LAYERFRAC))
    ref[:n] = DEFAULT_LAYERFRAC[:n]
    d = float(np.abs(v / v.sum() - ref / ref.sum()).max())
    return dict(nz=nz, max_abs_diff=d, matched=d < 1e-4, default_sum=float(ref.sum()))


# ---------------------------------------------------------------------------
# 3. URL list, download, unzip
# ---------------------------------------------------------------------------
FIRE_FILE_REGEX = r"\.3D\.(\d{4}-\d{2}-\d{2})\.zip$"   # BRAIN fire files of 2019 (FINN v1.5) and 2020 (FINN v2.5)


def parse_brain_urls(path, pattern=FIRE_FILE_REGEX):
    """Fire-emission files of a BRAIN URL list, selected by file name (the MEGAN, BRAVES and IND files do not match)."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            u = line.strip()
            if not u.lower().startswith("http"):
                continue
            q = up.parse_qs(up.urlparse(u).query)
            p = q.get("path", [""])[0]
            fn = q.get("fileName", [os.path.basename(p)])[0]
            m = re.search(pattern, fn)
            if not m:
                continue
            rows.append(dict(date=pd.Timestamp(m.group(1)), fileName=fn, path=p,
                             fileId=q.get("fileId", [""])[0], url=u))
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    dup = df[df.date.duplicated(keep=False)]
    if len(dup):
        raise ValueError(f"duplicated dates in the URL list:\n{dup}")
    return df


def valid_zip(path):
    if not os.path.exists(path) or os.path.getsize(path) < 22:
        return False
    try:
        with zipfile.ZipFile(path) as z:
            return z.testzip() is None
    except zipfile.BadZipFile:
        return False


def download(url, dest, session=None, retries=4, timeout=(30, 600), pause=5.0, check=valid_zip):
    """Stream url -> dest with retries; `check(dest)` must accept the result."""
    import requests
    if check(dest):
        return dest
    s = session or requests.Session()
    s.headers.setdefault("User-Agent", "Mozilla/5.0 (FINN_SC BRAIN comparison notebook)")
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    last = None
    for attempt in range(1, retries + 1):
        tmp = dest + ".part"
        try:
            with s.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            if not check(tmp):
                with open(tmp, "rb") as fh:
                    head = fh.read(160)
                raise IOError(f"downloaded file failed the format check; first bytes: {head!r}")
            os.replace(tmp, dest)
            return dest
        except Exception as exc:  # noqa: BLE001 - report and retry
            last = exc
            if os.path.exists(tmp):
                os.remove(tmp)
            time.sleep(pause * attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}\n  last error: {last}")


def is_gzip(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def extract_nc(zip_path, workdir):
    """Extract the single netCDF member of a BRAIN zip (largest member if several)."""
    os.makedirs(workdir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.infolist() if not m.is_dir()]
        if not members:
            raise IOError(f"empty zip: {zip_path}")
        m = max(members, key=lambda x: x.file_size)
        out = os.path.join(workdir, os.path.basename(m.filename))
        with z.open(m) as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
    return out, [x.filename for x in members]


# ---------------------------------------------------------------------------
# 4. Reading one BRAIN daily file
# ---------------------------------------------------------------------------
def read_header(nc_path):
    import netCDF4
    with netCDF4.Dataset(nc_path) as ds:
        attrs = {k: _py(ds.getncattr(k)) for k in ds.ncattrs()}
        dims = {k: len(v) for k, v in ds.dimensions.items()}
        variables = {}
        for name, v in ds.variables.items():
            variables[name] = dict(dims=list(v.dimensions), shape=list(v.shape), dtype=str(v.dtype),
                                   units=_py(getattr(v, "units", "")),
                                   long_name=_py(getattr(v, "long_name", "")),
                                   var_desc=_py(getattr(v, "var_desc", "")))
        tflag = np.asarray(ds.variables["TFLAG"][:, 0, :]) if "TFLAG" in ds.variables else None
        fmt = ds.data_model
    return dict(attrs=attrs, dims=dims, variables=variables, data_model=fmt,
                tflag=None if tflag is None else tflag.tolist())


def detect_speciation(variables):
    names = set(variables)
    for label, sp in SPECIATION.items():
        if sp["marker"] and sp["marker"] in names:
            return label
    return "finn2cmaq <= 2022-08-04 (BRAIN Table S3)"


def needed_vars(speciation_label):
    sp = SPECIATION[speciation_label]
    return GAS_VARS + [v for v in sp["pm_vars"] if v not in GAS_VARS]


def check_units(variables, names):
    """finn2cmaq writes 'moles/s' for gases and 'g/s' for aerosols."""
    problems = []
    for n in names:
        if n not in variables:
            problems.append((n, "missing"))
            continue
        u = variables[n]["units"].replace(" ", "").lower()
        want = "moles/s" if n in GAS_VARS else "g/s"
        if u != want:
            problems.append((n, variables[n]["units"]))
    return problems


def extract_day(nc_path, date, crop, varnames, expected_grid=EXPECTED_GRID):
    """Daily amounts per cell (moles/day or g/day) from one BRAIN daily file.

    The daily amount is the sum of the 24 hourly rates stamped with the file's own date
    (TFLAG hours 00..23) times 3600 s, summed over all layers. finn2cmaq writes the whole
    FINN daily total of DAY d into the file of date d (25 steps, the 25th is d+1 00Z), so
    the result is aligned with the FINN DAY of the records.
    Returns (cells DataFrame with date,i,j,<vars>; diagnostics dict).
    """
    import netCDF4
    j0, j1, i0, i1 = crop
    date = pd.Timestamp(date)
    d0 = int(date.strftime("%Y%j"))
    d1 = int((date + pd.Timedelta(days=1)).strftime("%Y%j"))
    diag = dict(date=str(date.date()), file=os.path.basename(nc_path))
    with netCDF4.Dataset(nc_path) as ds:
        ds.set_auto_maskandscale(False)
        attrs = {k: ds.getncattr(k) for k in ds.ncattrs()}
        diag["grid_mismatch"] = compare_grid(attrs, expected_grid)
        if diag["grid_mismatch"]:      # e.g. BRAIN 2020-12-06 is a file of the 20 km domain (d01)
            raise ValueError(f"{nc_path}: not on the expected grid {diag['grid_mismatch']}")
        diag["SDATE"], diag["TSTEP"] = int(attrs.get("SDATE", -1)), int(attrs.get("TSTEP", -1))
        tf = np.asarray(ds.variables["TFLAG"][:, 0, :])
        steps = np.where(tf[:, 0] == d0)[0]
        hours_ok = len(steps) == 24 and np.array_equal(tf[steps, 1], np.arange(24) * 10000)
        diag["n_steps"] = int(tf.shape[0])
        diag["tflag_ok"] = bool(hours_ok and diag["SDATE"] == d0 and diag["TSTEP"] == 10000)
        diag["has_next_00z"] = bool(tf.shape[0] >= 25 and tf[24, 0] == d1 and tf[24, 1] == 0)
        if not hours_ok:
            raise ValueError(f"{nc_path}: TFLAG does not hold hours 00-23 of {date.date()}")
        out, diag["missing_vars"], diag["negatives"], diag["nonfinite"] = {}, [], {}, {}
        for name in varnames:
            if name not in ds.variables:
                diag["missing_vars"].append(name)
                continue
            v = ds.variables[name]
            if list(v.dimensions) != ["TSTEP", "LAY", "ROW", "COL"]:
                raise ValueError(f"{name}: unexpected dimensions {v.dimensions}")
            a = np.asarray(v[:, :, j0:j1, i0:i1], dtype="f8")
            bad = ~np.isfinite(a) | (np.abs(a) >= 9.0e36)
            if bad.any():
                diag["nonfinite"][name] = int(bad.sum())
                a[bad] = 0.0
            neg = a < 0
            if neg.any():
                diag["negatives"][name] = [int(neg.sum()), float(a[neg].sum() * 3600.0)]
            day = a[steps].sum(axis=(0, 1)) * 3600.0
            out[name] = day
            if name == "CO":
                diag["nlay"] = int(a.shape[1])
                diag["CO_day_mol"] = float(day.sum())
                diag["CO_all25_mol"] = float(a.sum() * 3600.0)
                if day.max() > 0:
                    jj, ii = np.unravel_index(int(np.argmax(day)), day.shape)
                    diag["maxcell_ij"] = [int(ii + i0), int(jj + j0)]
                    diag["maxcell_hourly25"] = a[:, :, jj, ii].sum(axis=1).tolist()
                    diag["maxcell_layers"] = a[:, :, jj, ii].sum(axis=0).tolist()
    if not out:
        raise ValueError(f"{nc_path}: none of the requested variables is present")
    stack = np.stack([out[k] for k in out])
    nz = np.any(stack != 0, axis=0)
    jj, ii = np.nonzero(nz)
    cells = pd.DataFrame({"date": date, "i": ii + i0, "j": jj + j0})
    for k in out:
        cells[k] = out[k][jj, ii]
    return cells, diag


def brain_to_tonnes(cells, molar_mass, speciation_label):
    """BRAIN daily amounts (moles, g) -> tonnes of the compared species.

    NOx (as NO) = (NO + NO2) moles x M(NO), the same basis as the FINN NOXasNO field.
    PM2.5 = FINN PM25 recovered exactly from PSO4 (finn2cmaq: PSO4 = PM25 x f_SO4 x 1000).
    PM25_species_sum = sum of every primary PM variable written by finn2cmaq.
    """
    mm = dict(DEFAULT_MOLAR_MASS)
    mm.update(molar_mass or {})
    sp = SPECIATION[speciation_label]
    out = cells[["date", "i", "j"]].copy()
    out["CO"] = cells["CO"] * mm["CO"] / 1e6
    out["NOx"] = (cells["NO"] + cells["NO2"]) * mm["NO"] / 1e6
    out["SO2"] = cells["SO2"] * mm["SO2"] / 1e6
    out["NH3"] = cells["NH3"] * mm["NH3"] / 1e6
    out["CH4"] = cells["ECH4"] * mm["CH4"] / 1e6
    out["OC"] = cells["POC"] / 1e6
    out["BC"] = cells["PEC"] / 1e6
    out["PM25"] = cells["PSO4"] / sp["f_so4"] / 1e6
    present = [v for v in sp["pm_vars"] if v in cells]
    out["PM25_species_sum"] = cells[present].sum(axis=1) / 1e6
    if "PMC" in cells:            # finn2cmaq v2: PMC = (PM10 - PM25) x 1000
        out["PM10"] = out["PM25"] + cells["PMC"] / 1e6
    return out


def speciation_checks(cells, speciation_label):
    """Two identities of the finn2cmaq PM speciation, on annual sums."""
    sp = SPECIATION[speciation_label]
    s = cells.sum(numeric_only=True)
    res = dict(speciation=speciation_label)
    res["PSO4_over_PNO3_found"] = float(s["PSO4"] / s["PNO3"]) if s.get("PNO3", 0) > 0 else None
    res["PSO4_over_PNO3_expected"] = sp["f_so4"] / sp["f_no3"]
    pm25_g = s["PSO4"] / sp["f_so4"]
    present = [v for v in sp["pm_vars"] if v in s]
    res["species_sum_over_PM25"] = float(s[present].sum() / pm25_g) if pm25_g > 0 else None
    res["ok_ratio"] = (res["PSO4_over_PNO3_found"] is not None and
                       abs(res["PSO4_over_PNO3_found"] / res["PSO4_over_PNO3_expected"] - 1) < 1e-3)
    return res


# ---------------------------------------------------------------------------
# 5. Region: SC municipalities on the BRAIN grid
# ---------------------------------------------------------------------------
def load_municipalities(shp, code_field="CD_MUN", name_field="NM_MUN"):
    import geopandas as gpd
    g = gpd.read_file(shp, encoding="cp1252")          # as FINN_SC python/analysis/_setup.py
    g = g[[code_field, name_field, "geometry"]].rename(columns={code_field: "CD_MUN", name_field: "NM_MUN"})
    g["CD_MUN"] = g["CD_MUN"].astype(str).str.strip()
    return g


def to_index_space(geoms, grid):
    """Lon/lat geometries -> continuous grid coordinates (cell = unit square)."""
    import shapely

    def f(xy):
        x, y = grid.ll2index(xy[:, 0], xy[:, 1])
        return np.column_stack([x, y])
    return shapely.make_valid(shapely.transform(np.asarray(geoms), f))


def region_crop(geoms_idx, grid, margin=3):
    import shapely
    b = shapely.total_bounds(geoms_idx)
    i0 = max(0, int(np.floor(b[0])) - margin)
    j0 = max(0, int(np.floor(b[1])) - margin)
    i1 = min(grid.NCOLS, int(np.ceil(b[2])) + margin)
    j1 = min(grid.NROWS, int(np.ceil(b[3])) + margin)
    return (j0, j1, i0, i1)


def cell_weights(mun, geoms_idx):
    """Fraction of each cell inside each municipality (planar, in grid coordinates).

    Inside one 4 km cell the Mercator scale factor is constant to better than 0.1 %, so the
    planar fraction equals the fraction of the cell's true area.
    """
    import shapely
    rows = []
    for code, name, g in zip(mun["CD_MUN"], mun["NM_MUN"], geoms_idx):
        if g is None or g.is_empty:
            continue
        shapely.prepare(g)
        minx, miny, maxx, maxy = g.bounds
        ii = np.arange(int(np.floor(minx)), int(np.ceil(maxx)))
        jj = np.arange(int(np.floor(miny)), int(np.ceil(maxy)))
        I, J = np.meshgrid(ii, jj)
        I, J = I.ravel(), J.ravel()
        boxes = shapely.box(I, J, I + 1, J + 1)
        a = shapely.area(shapely.intersection(boxes, g))
        k = a > 1e-12
        rows.append(pd.DataFrame({"i": I[k], "j": J[k], "CD_MUN": code, "NM_MUN": name, "frac": a[k]}))
    w = pd.concat(rows, ignore_index=True)
    fsc = w.groupby(["i", "j"], as_index=False)["frac"].sum().rename(columns={"frac": "fSC_raw"})
    fsc["fSC"] = fsc["fSC_raw"].clip(upper=1.0)
    return w, fsc


# ---------------------------------------------------------------------------
# 6. FINN_SC records on the BRAIN grid
# ---------------------------------------------------------------------------
def load_records(path, year):
    df = pd.read_csv(path, low_memory=False)
    df = df[df["year"] == year].copy()
    df["product"] = "FINN " + df["version"].astype(str) + " " + df["sensor"].astype(str)
    df["date"] = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(df["DAY"].astype(int) - 1, unit="D")
    df["CD_MUN"] = df["CD_MUN"].apply(lambda x: str(int(float(x))) if pd.notna(x) else None)
    return df


def records_to_cells(df, grid, value_cols, keys=("product",)):
    i, j, inside = grid.ll2ij(df["LONGI"].values, df["LATI"].values)
    d = df.assign(i=i, j=j, inside=inside)
    n_out = int((~inside).sum())
    cells = d[inside].groupby(list(keys) + ["date", "i", "j"], as_index=False)[list(value_cols)].sum()
    return cells, n_out


# ---------------------------------------------------------------------------
# 7. FINN v1.5 text files (processing check)
# ---------------------------------------------------------------------------
def _open_text(path):
    """Text stream of a FINN file: tar.gz (largest member) or plain .gz (latin1, as finn2cmaq)."""
    if tarfile.is_tarfile(path):
        tf = tarfile.open(path, "r:*")
        members = [m for m in tf.getmembers() if m.isfile() and not m.name.endswith(".pdf")]
        m = max(members, key=lambda x: x.size)
        return io.TextIOWrapper(tf.extractfile(m), encoding="latin1"), tf
    return io.TextIOWrapper(gzip.open(path, "rb"), encoding="latin1"), None


def _fix_d_exponent(txt):
    return txt.replace("D+", "e+").replace("D-", "e-").replace("d+", "e+").replace("d-", "e-")


def read_finn15(path, lon_rng, lat_rng, names=None, lines_per_chunk=400_000):
    """Rows of a FINN v1.5 file inside a lon/lat box.

    names=None: annual file, columns FINN_V15_COLNAMES (first line is a header and is skipped).
    names='header': NRT daily file, column names taken from its own header (finn2cmaq openfinn).
    """
    stream, owner = _open_text(path)
    try:
        header = stream.readline()
        if names == "header":
            alias = {"LONGITUDE": "LONGI", "LATITUDE": "LATI"}
            cols = [alias.get(c.strip().upper(), c.strip().upper()) for c in header.strip().split(",")]
        else:
            cols = FINN_V15_COLNAMES
        parts = []
        while True:
            lines = list(itertools.islice(stream, lines_per_chunk))
            if not lines:
                break
            txt = _fix_d_exponent("".join(lines))
            ch = pd.read_csv(io.StringIO(txt), header=None, names=cols, index_col=False,
                             skipinitialspace=True)
            lon, lat = ch["LONGI"], ch["LATI"]
            parts.append(ch[(lon >= lon_rng[0]) & (lon <= lon_rng[1]) &
                            (lat >= lat_rng[0]) & (lat <= lat_rng[1])])
    finally:
        stream.close()
        if owner is not None:
            owner.close()
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)
    return out, header.strip()


def finn15_to_tonnes(df, year, molar_mass):
    """FINN v1.5 GEOS-Chem rows (gases mole/day; OC, BC, PM25 kg/day) -> tonnes, BRAIN species."""
    mm = dict(DEFAULT_MOLAR_MASS)
    mm.update(molar_mass or {})
    out = pd.DataFrame({
        "date": pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(df["DAY"].astype(int) - 1, unit="D"),
        "LONGI": df["LONGI"].astype(float), "LATI": df["LATI"].astype(float),
        "AREA": df["AREA"].astype(float)})
    out["CO"] = df["CO"] * mm["CO"] / 1e6
    out["NOx"] = (df["NO"] + df["NO2"]) * mm["NO"] / 1e6
    out["SO2"] = df["SO2"] * mm["SO2"] / 1e6
    out["NH3"] = df["NH3"] * mm["NH3"] / 1e6
    out["CH4"] = df["CH4"] * mm["CH4"] / 1e6
    out["PM25"] = df["PM25"] / 1e3
    out["OC"] = df["OC"] / 1e3
    out["BC"] = df["BC"] / 1e3
    if "PM10" in df:
        out["PM10"] = df["PM10"] / 1e3
    return out


# ---------------------------------------------------------------------------
# 8. Synthetic BRAIN file (numpy replica of finn2cmaq) for the self-test
# ---------------------------------------------------------------------------
def write_synthetic_brain_file(rows, grid, date, out_path, profile_id=210,
                               layerfrac=DEFAULT_LAYERFRAC,
                               speciation_label="finn2cmaq <= 2022-08-04 (BRAIN Table S3)"):
    """Build one CMAQ-ready daily file the way txt2daily.py + daily2hourly3d.py do.

    rows: one FINN day with LONGI, LATI, AREA, CO, NO, NO2, SO2, NH3, CH4 (mole/day) and
    OC, BC, PM25 (kg/day). Returns the daily gridded input (dict of 2D arrays).
    """
    import netCDF4
    sp = SPECIATION[speciation_label]
    i, j, inside = grid.ll2ij(rows["LONGI"].values, rows["LATI"].values)
    keep = inside & (rows["AREA"].values >= FINN2CMAQ_AREA_MIN)
    shape = (grid.NROWS, grid.NCOLS)
    D = {}
    for k in ["CO", "NO", "NO2", "SO2", "NH3", "CH4", "OC", "BC", "PM25"]:
        a = np.zeros(shape)
        np.add.at(a, (j[keep], i[keep]), rows[k].values[keep].astype("f8"))
        D[k] = a
    spc = {"CO": D["CO"], "NO": D["NO"], "NO2": D["NO2"], "SO2": D["SO2"], "NH3": D["NH3"],
           "ECH4": D["CH4"], "POC": D["OC"] * 1000, "PEC": D["BC"] * 1000,
           "PSO4": D["PM25"] * sp["f_so4"] * 1000, "PNO3": D["PM25"] * sp["f_no3"] * 1000}
    if sp["marker"] is None:
        spc["PMOTHR"] = D["PM25"] * 1000 - spc["POC"] - spc["PEC"] - spc["PSO4"] - spc["PNO3"]
    else:   # gc12_to_cb6r3_ae7_v2.txt (finn2cmaq, 2022-09-16)
        pm = D["PM25"] * 1000
        spc["PNCOM"] = spc["POC"] * 0.7
        f91102 = dict(PNH4=0.0087915, PCL=0.0414905, PAL=0.0006075, PCA=0.003858, PFE=0.000434, PMG=0.000314,
                      PMN=0.000016, PK=0.0293975, PSI=0.0018185, PNA=0.0057335, PTI=0.0000515)
        for k, v in f91102.items():
            spc[k] = pm * v
        spc["PMOTHR"] = np.maximum(0, pm - sum(spc[k] for k in ["POC", "PEC", "PSO4", "PNO3", "PNCOM", "PNH4", "PCL",
                                                                 "PAL", "PFE", "PMG", "PMN", "PK", "PSI", "PNA", "PTI"]))
        if "PM10" in rows:
            a = np.zeros(shape)
            np.add.at(a, (j[keep], i[keep]), rows["PM10"].values[keep].astype("f8"))
            spc["PMC"] = (a - D["PM25"]) * 1000
    I, J = np.meshgrid(np.arange(grid.NCOLS), np.arange(grid.NROWS))
    lon, _ = grid.ij2ll(I, J)
    tz = tz_offset(lon)
    tf = np.zeros((25,) + shape)
    for z in np.unique(tz):
        tf[:, tz == z] = hourly_factors(profile_id, z)[:, None]
    lf = np.asarray(layerfrac, "f8")
    nz = lf.size
    date = pd.Timestamp(date)
    d0 = int(date.strftime("%Y%j"))
    d1 = int((date + pd.Timedelta(days=1)).strftime("%Y%j"))
    with netCDF4.Dataset(out_path, "w", format="NETCDF4_CLASSIC") as ds:
        ds.createDimension("TSTEP", None)
        ds.createDimension("DATE-TIME", 2)
        ds.createDimension("LAY", nz)
        ds.createDimension("VAR", len(spc))
        ds.createDimension("ROW", grid.NROWS)
        ds.createDimension("COL", grid.NCOLS)
        for k in GRID_KEYS:
            ds.setncattr(k, getattr(grid, k))
        ds.setncattr("SDATE", np.int32(d0))
        ds.setncattr("STIME", np.int32(0))
        ds.setncattr("TSTEP", np.int32(10000))
        ds.setncattr("NLAYS", np.int32(nz))
        ds.setncattr("NVARS", np.int32(len(spc)))
        ds.setncattr("FILEDESC", "SYNTHETIC test file (numpy replica of finn2cmaq)")
        tfl = ds.createVariable("TFLAG", "i4", ("TSTEP", "VAR", "DATE-TIME"))
        flags = np.array([[d0, h * 10000] for h in range(24)] + [[d1, 0]], dtype="i4")
        tfl[:] = np.repeat(flags[:, None, :], len(spc), axis=1)
        for name, day in spc.items():
            v = ds.createVariable(name, "f4", ("TSTEP", "LAY", "ROW", "COL"), zlib=True, complevel=1)
            v.units = ("moles/s" if name in GAS_VARS else "g/s").ljust(16)
            v.long_name = name.ljust(16)
            for t in range(25):
                v[t] = (day[None, :, :] * tf[t][None, :, :] * lf[:, None, None] / 3600.0).astype("f4")
    return spc


def same_version_check(brain_cells, product_cells, species, interior):
    """Cell-day comparison of BRAIN with one FINN_SC product inside the interior cells (region R1).

    Inside R1 the FINN_SC records are complete (all points of an interior cell lie in the State), so when BRAIN was
    built from the same FINN file every cell-day with fire appears in both and the ratio BRAIN / product is the
    processing factor of finn2cmaq (layer sum x share of the day in the 24 hourly steps).
    """
    keys = ["date", "i", "j"]
    b = brain_cells[brain_cells.set_index(["i", "j"]).index.isin(interior)][keys + species]
    p = product_cells[product_cells.set_index(["i", "j"]).index.isin(interior)][keys + species]
    m = b.merge(p, on=keys, how="outer", suffixes=("_B", "_P")).fillna(0.0)
    both = (m.CO_B > 0) & (m.CO_P > 0)
    out = dict(cell_days_BRAIN=int((m.CO_B > 0).sum()), cell_days_product=int((m.CO_P > 0).sum()),
               cell_days_both=int(both.sum()),
               share_BRAIN_CO_in_common=float(m.CO_B[both].sum() / m.CO_B.sum()) if m.CO_B.sum() else np.nan,
               share_product_CO_in_common=float(m.CO_P[both].sum() / m.CO_P.sum()) if m.CO_P.sum() else np.nan)
    for s in species:
        ok = both & (m[f"{s}_P"] > 0)
        r = m.loc[ok, f"{s}_B"] / m.loc[ok, f"{s}_P"]
        out[f"{s}_ratio_p05"] = float(r.quantile(0.05)) if len(r) else np.nan
        out[f"{s}_ratio_median"] = float(r.median()) if len(r) else np.nan
        out[f"{s}_ratio_p95"] = float(r.quantile(0.95)) if len(r) else np.nan
    return out


# ---------------------------------------------------------------------------
# 9. Statistics
# ---------------------------------------------------------------------------
def spearman(x, y):
    from scipy.stats import spearmanr
    x, y = np.asarray(x, "f8"), np.asarray(y, "f8")
    if len(x) < 3 or np.all(x == x[0]) or np.all(y == y[0]):
        return np.nan
    return float(spearmanr(x, y)[0])


def pearson(x, y):
    x, y = np.asarray(x, "f8"), np.asarray(y, "f8")
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def moving_block_bootstrap(x, y, func, block=7, n_boot=2000, seed=20261101, alpha=0.05):
    """Percentile CI of func(x, y) by the moving-block bootstrap (Kuensch, 1989).

    Pairs (x_t, y_t) are resampled in blocks of `block` consecutive days, which keeps the
    serial dependence of daily fire series inside each block.
    """
    x, y = np.asarray(x, "f8"), np.asarray(y, "f8")
    n = len(x)
    if n < 2 * block:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(n_boot, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_boot, -1)[:, :n]
    stats = np.array([func(x[k], y[k]) for k in idx])
    stats = stats[np.isfinite(stats)]
    if stats.size < 0.9 * n_boot:
        return (np.nan, np.nan)
    return (float(np.quantile(stats, alpha / 2)), float(np.quantile(stats, 1 - alpha / 2)))


def save_json(obj, path):
    def conv(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (pd.Timestamp,)):
            return str(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=conv, ensure_ascii=False)