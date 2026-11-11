#!/usr/bin/env python3
"""tools/extract_mapbiomas_sc.py - Santa Catarina window of a MapBiomas land use and land cover GeoTIFF (Brazil coverage).

Writes the input of tools/study_area_map.py: an .npz with `a` (MapBiomas class id), `inside` (pixel centre inside the
state, IBGE 2024) and `transform` (affine of the window, EPSG:4326), read at 1/FACTOR of the native 30 m resolution
(FACTOR = 4: ~120 m) with nearest-neighbour resampling, which uses the internal overviews of the file.
Source file: brazil_coverage_<year>.tif of MapBiomas Collection 10
(https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection_10/lulc/coverage/brazil_coverage_<year>.tif).
Usage: python tools/extract_mapbiomas_sc.py <brazil_coverage_year.tif> <out.npz> [FACTOR]
Run on 2026-10-06 with the authors' copy of the 2019 file (FACTOR 2 and 4). That copy is incomplete at full resolution
(tiles south of about 25.9 S cannot be read), but its overviews (2x to 512x) are complete; class shares at 60 m and
120 m agree to within 0.02 percentage points.
"""
import sys
from pathlib import Path
import numpy as np, rasterio, geopandas as gpd
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from rasterio.enums import Resampling

ROOT = Path(__file__).resolve().parents[1]
SRC, OUT = sys.argv[1], sys.argv[2]
FACT = int(sys.argv[3]) if len(sys.argv) > 3 else 4
SHP = ROOT / 'data' / 'inputs' / 'SC_Municipios_2024.shp'
try:
    mun = gpd.read_file(SHP, encoding='cp1252')
except UnicodeDecodeError:
    mun = gpd.read_file(SHP, columns=['CD_MUN'])
sc = mun.to_crs(4326).dissolve().geometry.iloc[0]
minx, miny, maxx, maxy = sc.bounds
with rasterio.open(SRC) as r:
    win = from_bounds(minx - 0.05, miny - 0.05, maxx + 0.05, maxy + 0.05, r.transform).round_offsets().round_lengths()
    h, w = int(win.height // FACT), int(win.width // FACT)
    a = r.read(1, window=win, out_shape=(h, w), resampling=Resampling.nearest)
    t = r.window_transform(win) * rasterio.Affine.scale(win.width / w, win.height / h)
inside = geometry_mask([sc], out_shape=a.shape, transform=t, invert=True)
np.savez_compressed(OUT, a=a, inside=inside, transform=np.array(t)[:6])
v, c = np.unique(a[inside], return_counts=True)
print('shape', a.shape, 'resolution (deg)', t.a, dict(zip(v.tolist(), c.tolist())))
