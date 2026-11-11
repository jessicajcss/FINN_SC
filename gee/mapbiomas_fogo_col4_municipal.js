/**
 * gee/mapbiomas_fogo_col4_municipal.js  (Google Earth Engine Code Editor; formerly 15_gee_mapbiomas_fire_corrected.js)
 * Output used by the analysis: data/external/raw/mapbiomas_fogo_col4_SC_municipal_km2_gee_export.csv
 * (export run by the authors on 2026-10-02; cleaned copy with IBGE names: data/external/mapbiomas_fogo_col4_SC_municipal_km2_2012_2024.csv).
 *
 * Corrected extraction of MapBiomas Fogo annual burned area per SC municipality.
 * Replaces the rgee extraction behind repo/data/mapbiomas_fire_*_km2.csv, which is not
 * physically plausible (e.g., 79% of Bom Jardim da Serra burned in 2020; state totals equal
 * to 76% of the whole Mata Atlantica mean; 11-15x the Monitor do Fogo totals for SC).
 * Two estimator rules:
 *   (1) binarise the burned layer (value > 0 -> 1) BEFORE summing; summing raw pixel values
 *       of a band that stores class codes or fire frequency inflates the "pixel count";
 *   (2) convert to area with ee.Image.pixelArea() (true m2 of each pixel), never with a fixed
 *       900 m2: in EPSG:4326 a 30-m (equatorial scale) pixel covers ~784-809 m2 in SC.
 * Edit ASSET and MUNIS before running. Band names are matched by year (not hard-coded).
 */
var ASSET = 'projects/mapbiomas-public/assets/brazil/fire/collection4/mapbiomas_fire_collection4_annual_burned_v1';
var MUNIS = ee.FeatureCollection('users/<your_user>/SC_Municipios_2024');   // IBGE 2024 mesh uploaded as an asset
var YEARS = ee.List.sequence(2012, 2024);

var img = ee.Image(ASSET);
print('bands (check names and value ranges first):', img.bandNames());
print('example histogram 2024 (values must be 1 or class codes?):',
      img.select(img.bandNames().filter(ee.Filter.stringContains('item', '2024')).get(0))
         .reduceRegion({reducer: ee.Reducer.frequencyHistogram(), geometry: MUNIS.geometry().bounds(), scale: 300, maxPixels: 1e10}));

var perYear = YEARS.map(function (y) {
  y = ee.Number(y).int();
  var band = img.bandNames().filter(ee.Filter.stringContains('item', y.format('%d'))).get(0);
  var burned = img.select([band]).gt(0).unmask(0);                      // rule (1)
  var areaKm2 = burned.multiply(ee.Image.pixelArea()).divide(1e6)        // rule (2)
                      .rename('burned_km2');
  var fc = areaKm2.reduceRegions({collection: MUNIS, reducer: ee.Reducer.sum(), scale: 30, tileScale: 4});
  return fc.map(function (f) {
    return ee.Feature(null, {CD_MUN: f.get('CD_MUN'), NM_MUN: f.get('NM_MUN'), year: y, burned_km2: f.get('sum')});
  });
});
var out = ee.FeatureCollection(perYear).flatten();
Export.table.toDrive({collection: out, description: 'mapbiomas_fire_col4_SC_municipal_km2_corrected', fileFormat: 'CSV'});
// Plausibility checks after export: no municipality-year above ~40% of the municipal area;
// state totals compared with the MapBiomas platform statistics for SC and with the Monitor do Fogo.
