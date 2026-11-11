"""Shared set-up for the analysis scripts (python/analysis/aNN_*.py).

All inputs are read from the paths in config/config.yml (section `analysis`), and all
outputs go to results/ (tables/, figures/, logs/). Nothing is downloaded here: the
analysis starts from the archived Santa Catarina record table produced by the pipeline
(data/derived/finn_sc_records_2003_2025.csv.gz) and from the external tables in data/external/.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # python/ -> import finn_sc

import pandas as pd                            # noqa: E402
from finn_sc.config import load_config         # noqa: E402

CFG = load_config()
ROOT = Path(CFG["_root"])
A = CFG["analysis"]
RES = ROOT / A["results_dir"]
TAB = RES / "tables"
FIG = RES / "figures"
LOGD = RES / "logs"
for _d in (TAB, FIG, LOGD):
    _d.mkdir(parents=True, exist_ok=True)


def path(key: str) -> Path:
    """Absolute path of an input listed in config.analysis.inputs."""
    return ROOT / A["inputs"][key]


class Log:
    """Print and keep every line, then write results/logs/<name>.txt."""

    def __init__(self, name: str):
        self.name, self.lines = name, []

    def __call__(self, *a):
        s = " ".join(str(x) for x in a)
        print(s)
        self.lines.append(s)

    def save(self):
        (LOGD / f"{self.name}.txt").write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def load_records(product: str | None = None) -> pd.DataFrame:
    """Archived SC records (FINN v2.5 / v2.5.1; MODIS and MODIS+VIIRS).

    product: None (all), 'MV' (MODIS+VIIRS only) or 'MODIS'."""
    rec = pd.read_csv(path("records"))
    rec = rec[rec.version.isin(["v2.5", "v2.5.1"])]
    if product == "MV":
        rec = rec[rec.sensor == "MODIS+VIIRS"]
    elif product == "MODIS":
        rec = rec[rec.sensor == "MODIS"]
    return rec.reset_index(drop=True)


def municipalities() -> pd.DataFrame:
    """IBGE 2024 municipal attributes (CD_MUN, NM_MUN, AREA_KM2) + mesoregion."""
    return pd.read_csv(path("municipalities"))


def mesoregion_of() -> dict:
    m = municipalities()
    return dict(zip(m.NM_MUN, m.mesorregiao))


def read_shapefile():
    """IBGE 2024 municipal mesh (needed only for maps, KDE and spatial weights)."""
    import geopandas as gpd
    p = path("municipalities_shp")
    if not p.is_file():
        raise FileNotFoundError(f"{p} not found. Download the IBGE 2024 SC municipal mesh (data/inputs/README.md).")
    g = gpd.read_file(p, encoding="cp1252") if p.suffix == ".shp" else gpd.read_file(p)
    return g


def screened_events() -> pd.DataFrame:
    """Events table written by a01 (all products), with the persistent-anomaly flag."""
    return pd.read_csv(TAB / "events.csv.gz")
