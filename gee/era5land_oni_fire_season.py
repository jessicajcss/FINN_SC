#!/usr/bin/env python3
"""ERA5-Land fire-season climate of Santa Catarina and fire-season ONI (Google Earth Engine + NOAA CPC).

Recipe used to build data/external/era5land_oni_SC_fire_season_2012_2025.csv (columns year, precip_mm_fs,
Tc_fs, VPD_kPa_fs, soil_moist_fs, ONI_fs). Transcribed from the authors' NotebookB_drivers.ipynb (cells 4, 10,
12, 14 and 18; manuscript_draft/notebooks), keeping its choices so that the archived values can be regenerated:
  * ECMWF/ERA5_LAND/MONTHLY_AGGR, bands total_precipitation_sum, temperature_2m, dewpoint_temperature_2m,
    volumetric_soil_water_layer_1; mean over the SC state polygon (geobr, year 2022) at 11132 m;
  * precipitation (mm) = total_precipitation_sum x 1000; T and Td in deg C; VPD (kPa) from the Tetens
    equation, es - ea with e = 0.6108 exp(17.27 T / (T + 237.3)), clipped at 0;
  * fire season = July-November: precipitation summed, T, VPD and soil water averaged;
  * ONI: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt, mean of the JAS, ASO and SON anomalies.
Not executed in the 2026-10-03 revision (requires an Earth Engine account and internet access); the archived
CSV is the output of the authors' run. Requirements: earthengine-api, geemap, geobr, pandas, numpy.
References: Muñoz-Sabater et al. (2021) ESSD 13, 4349-4383; NOAA CPC Oceanic Niño Index.
"""
import io
import urllib.request

import ee
import geemap
import geobr
import numpy as np
import pandas as pd

PROJECT = "your-ee-project-id"            # <-- your Earth Engine Cloud project
FIRE_MONTHS = [7, 8, 9, 10, 11]
OUT = "era5land_oni_SC_fire_season.csv"

ee.Initialize(project=PROJECT)
sc_state = geobr.read_state(code_state="SC", year=2022).to_crs(4326)
GEOM = geemap.geopandas_to_ee(sc_state).geometry()

BANDS = ["total_precipitation_sum", "temperature_2m", "dewpoint_temperature_2m", "volumetric_soil_water_layer_1"]
ic = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").select(BANDS).filterDate("2003-01-01", "2026-01-01")


def _reduce(img):
    d = img.reduceRegion(ee.Reducer.mean(), GEOM, 11132, maxPixels=1e10)
    return ee.Feature(None, d).set("date", img.date().format("YYYY-MM-dd"))


clim = geemap.ee_to_df(ee.FeatureCollection(ic.map(_reduce)))
clim["date"] = pd.to_datetime(clim["date"])
clim["precip_mm"] = clim["total_precipitation_sum"] * 1000.0
clim["Tc"] = clim["temperature_2m"] - 273.15
clim["Tdc"] = clim["dewpoint_temperature_2m"] - 273.15
es = 0.6108 * np.exp(17.27 * clim["Tc"] / (clim["Tc"] + 237.3))
ea = 0.6108 * np.exp(17.27 * clim["Tdc"] / (clim["Tdc"] + 237.3))
clim["VPD_kPa"] = (es - ea).clip(lower=0)
clim["soil_moist"] = clim["volumetric_soil_water_layer_1"]
clim["year"], clim["month"] = clim["date"].dt.year, clim["date"].dt.month
fs = (clim[clim.month.isin(FIRE_MONTHS)].groupby("year")
      .agg(precip_mm_fs=("precip_mm", "sum"), Tc_fs=("Tc", "mean"), VPD_kPa_fs=("VPD_kPa", "mean"),
           soil_moist_fs=("soil_moist", "mean")).reset_index())

txt = urllib.request.urlopen("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", timeout=60).read().decode()
oni = pd.read_csv(io.StringIO(txt), sep=r"\s+")
oni.columns = [c.strip() for c in oni.columns]
order = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
oni["sidx"] = oni["SEAS"].map({s: i for i, s in enumerate(order)})
oni_fs = (oni[oni.sidx.between(7, 9)].groupby("YR")["ANOM"].mean().reset_index()
          .rename(columns={"YR": "year", "ANOM": "ONI_fs"}))
fs.merge(oni_fs, on="year", how="left").to_csv(OUT, index=False)
print("saved", OUT)
