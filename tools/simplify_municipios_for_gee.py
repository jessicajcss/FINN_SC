"""tools/simplify_municipios_for_gee.py - simplified copy of the IBGE 2024 municipal mesh for Earth Engine requests.

The full mesh (data/inputs/SC_Municipios_2024.shp, 2.5 million vertices, about 70 MB as GeoJSON) exceeds the 10 MB
limit of an Earth Engine request, so the notebooks in gee/ send this copy instead:
  * shapely.coverage_simplify with a tolerance of 0.0005 degrees (about 55 m, a tenth of an MCD64A1 pixel); the
    coverage method simplifies the shared edges once, so neighbouring municipalities keep a common border (no gaps or
    overlaps) and the dissolved State keeps its 79 parts;
  * coordinates rounded to 1e-5 degrees (about 1 m);
  * columns CD_MUN, NM_MUN and mesorregiao (data/external/sc_municipios_2024_atributos.csv); EPSG:4326.
Area change per municipality: at most 0.07 % (median 0.006 %); about 3.3 MB as GeoJSON.

Usage (from the repository root): python tools/simplify_municipios_for_gee.py
Output: gee/SC_municipios_2024_simplified.gpkg
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[1]
TOL = 0.0005
GRID = 1e-5
OUT = ROOT / "gee" / "SC_municipios_2024_simplified.gpkg"

mun = gpd.read_file(ROOT / "data" / "inputs" / "SC_Municipios_2024.shp", encoding="cp1252").to_crs(4326)
mun["CD_MUN"] = mun["CD_MUN"].astype("int64")
att = pd.read_csv(ROOT / "data" / "external" / "sc_municipios_2024_atributos.csv")
geom = shapely.set_precision(shapely.coverage_simplify(mun.geometry.values, TOL), GRID)
s = gpd.GeoDataFrame(mun[["CD_MUN", "NM_MUN"]].copy(), geometry=geom, crs=4326)
s = s.merge(att[["CD_MUN", "mesorregiao"]], on="CD_MUN", how="left")
assert len(s) == 295 and s.CD_MUN.is_unique and s.mesorregiao.notna().all()
assert shapely.is_valid(s.geometry.values).all()
d_area = (s.to_crs(5880).area / mun.to_crs(5880).area - 1).abs() * 100
print(f"area change per municipality: max {d_area.max():.3f} %, median {d_area.median():.4f} %")
s[["CD_MUN", "NM_MUN", "mesorregiao", "geometry"]].to_file(OUT, layer="SC_municipios_2024_simplified", driver="GPKG")
print("saved", OUT)
