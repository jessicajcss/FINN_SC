"""Download and merge FINN fire-emission files (Python port of 00_download_finn.R).

Builds the FINN download URLs (v1.5 / v2.5 / v2.5.1 monthly / v2.5.1 NRT daily),
downloads them, merges and de-duplicates rows, and writes one combined CSV.

Handles the FINNv1.5 header quirk (the released files use fixed, non
self-describing column names) and, for v2.5+, can prepend the source URL as a
provenance column.
"""
from __future__ import annotations

import calendar
import datetime as _dt
import gzip
import io
import os
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Optional as _Opt

import requests


def _decode_finn_payload(content: bytes) -> _Opt[str]:
    """Return the text of a downloaded FINN file, or None if undecodable.

    Handles both distribution formats transparently:
      * plain gzipped text  (``.txt.gz``)  -> FINN v2.5 / v2.5.1;
      * gzipped tar archive (``.tar.gz``)  -> FINN v1.5 annual files, which
        extract to a folder containing the emissions ``.txt``.
    Returns None for anything that is neither (e.g. an HTML error page).
    """
    # Try tar.gz first (FINNv1.5 annual archives).
    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
            if members:
                biggest = max(members, key=lambda m: m.size)  # the emissions table
                fh = tf.extractfile(biggest)
                if fh is not None:
                    return fh.read().decode("utf-8", errors="replace")
    except (tarfile.TarError, OSError, EOFError):
        pass
    # Fall back to plain gzip text.
    try:
        return gzip.decompress(content).decode("utf-8", errors="replace")
    except (OSError, EOFError):
        return None

# Fixed column order for FINNv1.5 GEOS-CHEM files.
FINN_V15_COLNAMES = [
    "DAY", "TIME", "GENVEG", "LATI", "LONGI", "AREA", "CO2", "CO", "NO", "NO2",
    "SO2", "NH3", "CH4", "ACET", "ALD2", "ALK4", "BENZ", "C2H2", "C2H4", "C2H6",
    "C3H8", "CH2O", "GLYC", "GLYX", "HAC", "MEK", "MGLY", "PRPE", "TOLU", "XYLE",
    "OC", "BC", "PM25",
]

_BASE_V1 = "https://www.acom.ucar.edu/Data/fire/data/finn1"
_BASE_V25 = "https://data-osdf.rda.ucar.edu/ncar/rda/d312009"
_BASE_V25_NRT = "https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt"


def build_finn_urls(include_monthly: bool = True,
                    include_daily: bool = True) -> List[Dict]:
    """Return the full catalogue of FINN file descriptors.

    Each item is a dict with keys: url, version, sensor, granularity, year
    (and month/day for monthly/daily files).
    """
    urls: List[Dict] = []

    # FINNv1.5 GEOS-CHEM, MODIS (2002-2020)
    # Every FINN v1.5 year, 2002 included, is a .tar.gz archive; the earlier ".txt.gz" address of 2002 returned 404
    # (corrected 11 Nov 2026). The FINN page (https://www.acom.ucar.edu/Data/fire/) asks users to submit their name
    # and contact information before downloading the FINN v1.5 files.
    for year in range(2002, 2021):
        suffix = ".tar.gz"
        urls.append(dict(url=f"{_BASE_V1}/FINNv1.5_{year}.GEOSCHEM{suffix}",
                         version="v1.5", sensor="MODIS",
                         granularity="yearly", year=year))

    # FINNv2.5 GEOS-CHEM, MODIS (2003-2021)
    for year in range(2003, 2022):
        suffix = "c20221105" if year == 2021 else "c20211213"
        urls.append(dict(
            url=f"{_BASE_V25}/{year}_eachfire_modis/FINNv2.5_mod_GEOSCHEM_{year}_{suffix}.txt.gz",
            version="v2.5", sensor="MODIS", granularity="yearly", year=year))

    # FINNv2.5 GEOS-CHEM, MODIS+VIIRS (2012-2021)
    for year in range(2012, 2022):
        suffix = "c20220714" if year == 2021 else "c20211213"
        urls.append(dict(
            url=f"{_BASE_V25}/{year}_eachfire_modisviirs/FINNv2.5_modvrs_GEOSCHEM_{year}_{suffix}.txt.gz",
            version="v2.5", sensor="MODIS+VIIRS", granularity="yearly", year=year))

    # FINNv2.5.1 monthly (2022-2023)
    if include_monthly:
        for i in range(1, 13):
            urls.append(dict(
                url=f"{_BASE_V25}/2022_eachfire_modis/FINNv2.5.1_mod_GEOSCHEM_2022{i:02d}_c20240525.txt.gz",
                version="v2.5.1", sensor="MODIS", granularity="monthly", year=2022, month=i))
            urls.append(dict(
                url=f"{_BASE_V25}/2023_eachfire_modis/FINNv2.5.1_mod_GEOSCHEM_2023{i:02d}_c20240621.txt.gz",
                version="v2.5.1", sensor="MODIS", granularity="monthly", year=2023, month=i))
            urls.append(dict(
                url=f"{_BASE_V25}/2022_eachfire_modisviirs/FINNv2.5.1_modvrs_GEOSCHEM_2022{i:02d}_c20240506.txt.gz",
                version="v2.5.1", sensor="MODIS+VIIRS", granularity="monthly", year=2022, month=i))
            urls.append(dict(
                url=f"{_BASE_V25}/2023_eachfire_modisviirs/FINNv2.5.1_modvrs_GEOSCHEM_2023{i:02d}_c20240521.txt.gz",
                version="v2.5.1", sensor="MODIS+VIIRS", granularity="monthly", year=2023, month=i))

    # FINNv2.5.1 near-real-time (NRT) daily (2024-present).
    # File name is always FINNv2.5.1_modvrs_nrt_GEOSCHEM_<YYYYMMDD>.txt.gz, but
    # UCAR moves files between two locations over time:
    #   * the CURRENT year's files sit directly in .../finn_emis_txt/
    #   * PAST years are archived into a per-year folder .../FINN2nrt_<year>/
    # (verified against the live directory index: FINN2nrt_2024/, FINN2nrt_2025/
    #  as folders, with the current year's days in the root). Because the split
    #  shifts at each year rollover, every NRT date carries BOTH candidate URLs
    #  and the downloader uses whichever responds. NRT is a *rolling* product:
    #  very old dates may 404 once superseded by the finalized release - those
    #  are skipped cleanly rather than crashing the run.
    if include_daily:
        current_year = _dt.date.today().year
        for year in range(2024, current_year + 1):
            n_days = 366 if calendar.isleap(year) else 365
            for day in range(1, n_days + 1):
                date = (_dt.date(year, 1, 1) + _dt.timedelta(days=day - 1))
                ymd = date.strftime("%Y%m%d")
                root = f"{_BASE_V25_NRT}/FINNv2.5.1_modvrs_nrt_GEOSCHEM_{ymd}.txt.gz"
                folder = f"{_BASE_V25_NRT}/FINN2nrt_{year}/FINNv2.5.1_modvrs_nrt_GEOSCHEM_{ymd}.txt.gz"
                # Order by the most likely spot for this year, but keep both.
                candidates = [root, folder] if year == current_year else [folder, root]
                urls.append(dict(url=candidates[0], url_candidates=candidates,
                                 version="v2.5.1", sensor="MODIS+VIIRS",
                                 granularity="daily", year=year,
                                 month=date.month, day=date.day))
    return urls


def filter_finn_urls(urls: List[Dict],
                     version: Optional[str | List[str]] = None,
                     sensor: Optional[str | List[str]] = None,
                     year: Optional[int | List[int]] = None) -> List[Dict]:
    """Filter the URL catalogue by version / sensor / year (scalars or lists)."""
    def _as_set(v):
        if v is None:
            return None
        return set(v) if isinstance(v, (list, tuple, set)) else {v}

    vset, sset, yset = _as_set(version), _as_set(sensor), _as_set(year)
    out = []
    for u in urls:
        if vset is not None and u["version"] not in vset:
            continue
        if sset is not None and u["sensor"] not in sset:
            continue
        if yset is not None and u["year"] not in yset:
            continue
        out.append(u)
    return out


def filter_finn_by_date(url_list: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """Keep only URL descriptors whose period overlaps [start_date, end_date].

    daily   -> the exact date is within the range;
    monthly -> the (year, month) overlaps the range;
    yearly  -> the year is within the range (a whole-year file is the only
               option for 2002-2021).
    """
    s = _dt.date.fromisoformat(str(start_date))
    e = _dt.date.fromisoformat(str(end_date))
    out = []
    for u in url_list:
        g = u.get("granularity", "yearly")
        if g == "daily":
            if s <= _dt.date(u["year"], u["month"], u["day"]) <= e:
                out.append(u)
        elif g == "monthly":
            m_start = _dt.date(u["year"], u["month"], 1)
            nxt = _dt.date(u["year"] + (u["month"] // 12), (u["month"] % 12) + 1, 1)
            m_end = nxt - _dt.timedelta(days=1)
            if m_start <= e and m_end >= s:
                out.append(u)
        else:  # yearly
            if s.year <= u["year"] <= e.year:
                out.append(u)
    return out


def download_finn_files(url_list: List[Dict],
                        dest_folder: str | os.PathLike = "data/raw_finn",
                        combined_filename: str = "combined_finn.csv",
                        include_source_url: bool = True,
                        min_file_size_kb: float = 0.5,
                        timeout_seconds: int = 600) -> Path:
    """Download, merge and de-duplicate a list of FINN files.

    Returns the path to the combined CSV.
    """
    dest = Path(dest_folder)
    dest.mkdir(parents=True, exist_ok=True)
    combined_path = dest / combined_filename

    seen = set()
    header_line: Optional[str] = None
    n_rows = 0

    with open(combined_path, "w", encoding="utf-8", newline="") as out:
        for u in url_list:
            # Each descriptor may offer several candidate URLs for the same file
            # (e.g. NRT root vs FINN2nrt_<year>/ folder); use whichever responds.
            candidates = u.get("url_candidates") or [u["url"]]
            fname = candidates[0].rsplit("/", 1)[-1]
            print(f"Processing: {fname}")
            resp, src_url = None, None
            for cand in candidates:
                try:
                    r = requests.get(cand, timeout=timeout_seconds)
                except requests.RequestException as exc:
                    print(f"  FAILED: {cand} - {exc}")
                    continue
                if r.status_code == 200 and len(r.content) / 1024 >= min_file_size_kb:
                    resp, src_url = r, cand
                    break
            if resp is None:
                print(f"  skipped (not available / too small): {fname}")
                continue
            text = _decode_finn_payload(resp.content)
            if text is None:
                print(f"  skipped (not a gzip/tar.gz file): {fname}")
                continue

            lines = [ln for ln in text.splitlines() if ln != ""]
            if not lines:
                print(f"  empty file: {fname}")
                continue

            is_v15 = u.get("version") == "v1.5"
            data_lines = lines[1:]

            if header_line is None:
                if is_v15:
                    header_line = ",".join(FINN_V15_COLNAMES)
                elif include_source_url:
                    # Comma (not tab) so the combined file is a clean CSV.
                    header_line = "source_url," + lines[0]
                else:
                    header_line = lines[0]
                out.write(header_line + "\n")

            # De-duplicate on the DATA line only (not the source_url prefix) so a
            # file that briefly exists in two locations isn't counted twice.
            for ln in data_lines:
                if ln in seen:
                    continue
                seen.add(ln)
                row = ln if is_v15 else (f"{src_url},{ln}" if include_source_url else ln)
                out.write(row + "\n")
                n_rows += 1
            print(f"  added: {fname}")

    if n_rows == 0:
        print("WARNING: no data rows were downloaded (all files 404'd, were "
              "empty, or none matched the selection). The combined CSV has a "
              "header only; downstream steps will skip it with a clear message.")
    print(f"Deduplicated and saved ({n_rows} rows): {combined_path}")
    return combined_path
