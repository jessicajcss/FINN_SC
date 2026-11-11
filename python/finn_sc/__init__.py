"""
finn_sc - Python engine for the FINN Santa Catarina wildfire emissions pipeline.

A faithful port of the R pipeline (see ../../R/).
The processing steps mirror the R scripts one-to-one:

    download        -> 00_download_finn
    convert_units   -> 01_convert_units
    clip_sc         -> 02_clip_region
    aggregate       -> 04_aggregate_region
    plots           -> 05_descriptive_analysis

Data reference (official):
    FINNv1   Wiedinmyer et al., 2011  https://doi.org/10.5194/gmd-4-625-2011
    FINNv2.5 Wiedinmyer et al., 2023  https://doi.org/10.5194/gmd-16-3873-2023
    Archive  NSF NCAR RDA ds312.9      https://rda.ucar.edu/datasets/ds312-9/
"""

# --- Robust PROJ database path (fixes CRS errors on many Windows/conda setups) ---
# On mixed pip/conda installs, a broken base env, or when a stale global PROJ_LIB /
# PROJ_DATA (e.g. from QGIS or OSGeo4W) points somewhere without `proj.db`, pyproj
# cannot find its database, which breaks every CRS operation — such as reading the
# IBGE shapefile (EPSG:4674) with "Invalid projection: EPSG:4674 ... no database
# context" (often preceded by "pyproj unable to set PROJ database path").
#
# When the active PROJ location is missing proj.db, we search, in order:
#   1. pyproj's own bundled copy (pip wheels),
#   2. this interpreter's env (conda <env>/Library/share/proj or <env>/share/proj),
#   3. every SIBLING conda env under the same root (e.g. run on `base` but you also
#      have a working `finn` env — we borrow that env's proj.db).
# and point PROJ at the first location that actually contains proj.db. Setting the
# env vars too fixes the C-level PROJ used by GDAL/pyogrio inside geopandas. This
# runs *before* geopandas is imported below, so the fix applies pipeline-wide.
# No-op on healthy installs; if nothing is found it prints one actionable hint.
import os as _os
import sys as _sys
import glob as _glob
try:
    import pyproj as _pyproj

    def _has_db(_d):
        return bool(_d) and _os.path.exists(_os.path.join(_d, "proj.db"))

    try:
        _cur = _pyproj.datadir.get_data_dir()
    except Exception:
        _cur = None

    if not _has_db(_cur):
        _cands = [
            # 1) pip wheels bundle PROJ data inside the pyproj package:
            _os.path.join(_os.path.dirname(_pyproj.__file__), "proj_dir", "share", "proj"),
        ]
        # 2) this interpreter's own env (conda on Windows uses Library/share/proj):
        _envs = {_sys.prefix}
        _cp = _os.environ.get("CONDA_PREFIX")
        if _cp:
            _envs.add(_cp)
        for _e in _envs:
            _cands += [_os.path.join(_e, "Library", "share", "proj"),
                       _os.path.join(_e, "share", "proj")]
        # 3) sibling conda envs under the same root: rescue a broken env (e.g. base)
        #    by borrowing a working env's proj.db (e.g. envs/finn/.../proj).
        _roots = set()
        for _e in _envs:
            _roots.add(_e)                                   # a root itself
            if _os.path.basename(_os.path.dirname(_e)) == "envs":
                _roots.add(_os.path.dirname(_os.path.dirname(_e)))   # <root>/envs/<name> -> <root>
        for _r in _roots:
            for _pat in ("Library/share/proj", "share/proj"):
                _cands += _glob.glob(_os.path.join(_r, "envs", "*", *_pat.split("/")))

        _fixed = False
        for _d in _cands:
            if _has_db(_d):
                _pyproj.datadir.set_data_dir(_d)
                _os.environ["PROJ_DATA"] = _d
                _os.environ["PROJ_LIB"] = _d
                _fixed = True
                break
        if not _fixed:
            import warnings as _warnings
            _warnings.warn(
                "finn_sc: could not locate a PROJ 'proj.db' for this Python. CRS "
                "operations (reading the shapefile) will fail. Run in a conda env "
                "that has geopandas, e.g. `conda activate finn` (in VS Code, pick "
                "the 'finn' kernel), or `conda install -c conda-forge proj`.")
except Exception:
    pass

from .config import load_config, project_root
from .download import (build_finn_urls, filter_finn_urls, filter_finn_by_date,
                       download_finn_files)
from .convert_units import convert_finn_units
from .clip_sc import clip_to_bbox, clip_to_region, resolve_bbox   # 2026-10-03 review: + clip_to_region
from .aggregate import (aggregate_by_region, aggregate_by_municipality,
                        count_fire_units, drop_exact_duplicates)  # 2026-10-03 review
from .dates import date_bounds, selected_years, filter_rows_by_date

__all__ = [
    "load_config", "project_root",
    "build_finn_urls", "filter_finn_urls", "filter_finn_by_date", "download_finn_files",
    "convert_finn_units", "resolve_bbox", "clip_to_bbox", "clip_to_region",
    "aggregate_by_region", "aggregate_by_municipality",
    "count_fire_units", "drop_exact_duplicates",
    "date_bounds", "selected_years", "filter_rows_by_date",
]
__version__ = "1.0.0"
