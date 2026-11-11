#!/usr/bin/env python3
"""Municipal land-cover fractions from MapBiomas (Google Earth Engine), year 2023.

Recipe used to build data/external/mapbiomas_lulc2023_SC_municipal_fractions.csv. Transcribed from the authors'
NotebookB_drivers.ipynb (cells 10 and 24): asset projects/mapbiomas-public/assets/brazil/lulc/v1, image of
year 2023, band 'classification'; for each class group a binary mask (remap) is averaged over each
municipality polygon (geobr, year 2022) with ee.Reducer.mean() at 100 m (tileScale 4):
    forest       = [1, 3, 4, 5, 6, 49]     grassland   = [12]          pasture = [15]
    agriculture  = [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62]   silviculture = [9]
OPEN ITEMS (authors): (1) the MapBiomas collection behind the 'lulc/v1' asset at the time of the run must be
recorded. The Earth Engine catalog page of the asset ("MapBiomas Land Use and Land Cover - Brazil V1.0") lists the
image properties `year`, `version` and `collection_id`; the script now prints the collections available for
YEAR_LULC and the `collection_id` of the image it uses, and COLLECTION_ID pins one collection; (2) the archived CSV holds 277 of the 295 municipalities (those with FINN records in 2025); running
this script writes all 295 municipalities, which is what the land-cover analysis should use.
Not executed in the 2026-10-03 revision (requires Earth Engine). Requirements: earthengine-api, geemap, geobr, pandas.
Reference: Souza Junior et al. (2020) Remote Sensing 12, 2735.
"""
import ee
import geemap
import geobr

PROJECT = "your-ee-project-id"            # <-- your Earth Engine Cloud project
YEAR_LULC = 2023
COLLECTION_ID = None                      # e.g. 10 to pin a MapBiomas collection; None = first image of the year (as in NotebookB)
OUT = "mapbiomas_lulc2023_SC_municipal_fractions_all295.csv"
GROUPS = {"forest": [1, 3, 4, 5, 6, 49], "grassland": [12], "pasture": [15],
          "agriculture": [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62], "silviculture": [9]}

ee.Initialize(project=PROJECT)
sc_muni = geobr.read_municipality(code_muni="SC", year=2022).to_crs(4326)
muni_ee = geemap.geopandas_to_ee(sc_muni[["code_muni", "name_muni", "geometry"]])
col = ee.ImageCollection("projects/mapbiomas-public/assets/brazil/lulc/v1").filter(ee.Filter.eq("year", YEAR_LULC))
print("collection_id of the images of", YEAR_LULC, ":", col.aggregate_array("collection_id").getInfo())
if COLLECTION_ID is not None:
    col = col.filter(ee.Filter.eq("collection_id", COLLECTION_ID))
img = col.first()
print("image used: collection_id =", img.get("collection_id").getInfo(), "| version =", img.get("version").getInfo())
lulc = img.select("classification")
frac = sc_muni[["code_muni", "name_muni"]].copy()
for name, codes in GROUPS.items():
    mask = lulc.remap(codes, [1] * len(codes), 0).rename("m")
    fc = mask.reduceRegions(collection=muni_ee, reducer=ee.Reducer.mean(), scale=100, tileScale=4)
    d = geemap.ee_to_df(fc)
    col = "mean" if "mean" in d.columns else [c for c in d.columns if c not in ("code_muni", "name_muni")][0]
    frac = frac.merge(d[["code_muni", col]].rename(columns={col: name}), on="code_muni", how="left")
frac.rename(columns={"name_muni": "municipality"}).to_csv(OUT, index=False)
print("saved", OUT, len(frac), "municipalities")
