"""Spatial clip to the study region (Python port of 02_clip_region.R).

Keeps only FINN fire points inside the study bounding box. The box can be given
explicitly, taken as "none" (skip the pre-filter), or derived automatically from
the region shapefile's own extent (config: region.bbox = auto). This is a cheap
pre-filter run before the more expensive point-in-polygon join (see aggregate.py).

2026-10-03 review: a bounding box also keeps points in neighbouring states,
Argentina/Paraguay and the ocean, so bbox-only files must not be used for
totals or point-level statistics. ``clip_to_region`` applies the bbox
pre-filter AND a point-in-polygon test against the study polygons; step 02
now uses it, so every intermediate point file is restricted to the polygons.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

# NOTE: this module needs only pandas. The bounding-box clip is a pure
# coordinate comparison (fast, exact for a lon/lat rectangle); resolve_bbox in
# "auto" mode reads the extent from the caller's already-loaded shapefile (a
# GeoDataFrame) via its own methods. So importing finn_sc never requires the
# spatial stack - geopandas is only needed to READ the shapefile (in the step
# scripts and in aggregate_by_region).


def resolve_bbox(cfg: Dict[str, Any],
                 shp: Optional[gpd.GeoDataFrame] = None) -> Optional[Dict[str, float]]:
    """Return the bbox for the region, or ``None`` when pre-filtering is disabled.

    Modes for ``region['bbox']``:
      * a mapping with lon_min/lon_max/lat_min/lat_max -> used as given (explicit);
      * ``"auto"`` (or missing) -> derived from the shapefile extent (reprojected
        to EPSG:4326) plus ``region['bbox_margin_deg']``; requires ``shp``;
      * ``"none"`` -> returns ``None`` (caller skips the pre-filter).
    """
    b = cfg["region"].get("bbox", "auto")
    if isinstance(b, dict) and {"lon_min", "lon_max", "lat_min", "lat_max"} <= set(b):
        return {k: b[k] for k in ("lon_min", "lon_max", "lat_min", "lat_max")}
    if isinstance(b, str) and b.lower() == "none":
        return None
    # "auto" (or unset): derive from the shapefile extent + margin.
    if shp is None:
        raise ValueError(
            "region['bbox'] is 'auto' but no shapefile was supplied. Pass the "
            "boundaries shapefile, or set an explicit bbox / 'none' in config."
        )
    margin = cfg["region"].get("bbox_margin_deg", 0) or 0
    minx, miny, maxx, maxy = shp.to_crs(4326).total_bounds
    return {"lon_min": minx - margin, "lon_max": maxx + margin,
            "lat_min": miny - margin, "lat_max": maxy + margin}


def clip_to_bbox(df: pd.DataFrame,
                 cfg: Dict[str, Any],
                 shp: Optional[gpd.GeoDataFrame] = None) -> pd.DataFrame:
    """Return the subset of ``df`` whose LONGI/LATI fall inside the region bbox.

    If the resolved bbox is ``None`` (config bbox = "none"), ``df`` is returned
    unchanged. LONGI/LATI are preserved as plain columns.
    """
    bb = resolve_bbox(cfg, shp)
    if bb is None:
        return df.copy()

    # FINN coordinates are native lon/lat (EPSG:4326) and the bbox is an
    # axis-aligned lon/lat rectangle, so a vectorised coordinate comparison is
    # exact and far faster than building a GeoDataFrame and running `within`
    # over the whole (global) cloud. Precise polygon membership is tested later,
    # in step 04 (aggregate_by_region).
    lon = pd.to_numeric(df["LONGI"], errors="coerce")
    lat = pd.to_numeric(df["LATI"], errors="coerce")
    mask = ((lon >= bb["lon_min"]) & (lon <= bb["lon_max"]) &
            (lat >= bb["lat_min"]) & (lat <= bb["lat_max"]))
    return df[mask.fillna(False)].copy()


def clip_to_region(df: pd.DataFrame,
                   cfg: Dict[str, Any],
                   shp: "gpd.GeoDataFrame") -> pd.DataFrame:
    """2026-10-03 review: bbox pre-filter + point-in-polygon clip.

    Returns the rows of ``df`` whose point (LONGI, LATI) lies inside at least
    one polygon of ``shp`` (predicate ``within``, the same test used in
    step 04). Each input row is returned at most once, even if polygons
    overlap. Columns are unchanged (the region attribute is attached in
    step 04).
    """
    if shp is None:
        raise ValueError("clip_to_region needs the boundaries shapefile "
                         "(region.boundaries_shp); points must be restricted to "
                         "the study polygons, not only to the bounding box.")
    import geopandas as gpd

    pre = clip_to_bbox(df, cfg, shp=shp).reset_index(drop=True)
    if pre.empty:
        return pre
    pts = gpd.GeoDataFrame(
        pre[[]].copy(),
        geometry=gpd.points_from_xy(pd.to_numeric(pre["LONGI"], errors="coerce"),
                                    pd.to_numeric(pre["LATI"], errors="coerce")),
        crs=f"EPSG:{cfg['region']['crs_epsg']}",
    )
    if pts.crs != shp.crs:
        pts = pts.to_crs(shp.crs)
    hit = gpd.sjoin(pts, shp[["geometry"]], how="inner", predicate="within")
    inside = pre.index.isin(hit.index.unique())
    return pre[inside].copy()
