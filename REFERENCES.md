# References / Referências

*The reference list is language-neutral (author, title, journal, DOI). Notes are
given in English; see the Portuguese docs for translated descriptions.*

All entries below were verified against their DOI or publisher landing page.
A machine-readable version is in [`references.bib`](references.bib). Where a full
author list could not be confirmed, "et al." is used rather than inventing names.

## FINN model (primary sources)

1. **Wiedinmyer, C., Akagi, S. K., Yokelson, R. J., Emmons, L. K., Al-Saadi, J. A., Orlando, J. J., and Soja, A. J. (2011).** The Fire INventory from NCAR (FINN): a high resolution global model to estimate the emissions from open burning. *Geoscientific Model Development*, 4(3), 625–641. https://doi.org/10.5194/gmd-4-625-2011
   *Defines the FINN v1 method: active-fire detections × assumed burned area × fuel loading × combustion completeness × emission factors. Underpins the v1/v1.5 files this pipeline downloads.*

2. **Wiedinmyer, C., et al. (2023).** The Fire Inventory from NCAR version 2.5: an updated global fire emissions model for climate and chemistry applications. *Geoscientific Model Development*, 16(13), 3873–3891. https://doi.org/10.5194/gmd-16-3873-2023
   *The v2.5 update: MODIS + VIIRS detections, revised land cover, fuels and emission factors, and VOC speciation for MOZART-T1, SAPRC99 and GEOS-Chem. Primary reference for the v2.5 / v2.5.1 files.*

## Emission factors

3. **Akagi, S. K., Yokelson, R. J., et al. (2011).** Emission factors for open and domestic biomass burning for use in atmospheric models. *Atmospheric Chemistry and Physics*, 11(9), 4039–4072. https://doi.org/10.5194/acp-11-4039-2011
   *A key emission-factor compilation used by FINN to convert burned biomass into species-specific emissions.*

4. **Andreae, M. O. (2019).** Emission of trace gases and aerosols from biomass burning – an updated assessment. *Atmospheric Chemistry and Physics*, 19(13), 8523–8546. https://doi.org/10.5194/acp-19-8523-2019
   *Updated emission factors by fire/fuel type; useful for interpreting and sensitivity-testing FINN species ratios.*

## Satellite active-fire products (FINN inputs)

5. **Giglio, L., Schroeder, W., and Justice, C. O. (2016).** The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*, 178, 31–41. https://doi.org/10.1016/j.rse.2016.02.054
   *The MODIS Collection 6 active-fire product that supplies FINN's MODIS detections.*

6. **Schroeder, W., Oliva, P., et al. (2014).** The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96. https://doi.org/10.1016/j.rse.2013.12.008
   *The 375 m VIIRS active-fire product added in FINN v2.5's "MODIS+VIIRS" configuration.*

## Global fire-emission inventory (for comparison)

7. **van der Werf, G. R., et al. (2017).** Global fire emissions estimates during 1997–2016. *Earth System Science Data*, 9(2), 697–720. https://doi.org/10.5194/essd-9-697-2017
   *GFED4s: the most common independent inventory to benchmark FINN totals against.*

## Emission preprocessing for chemistry models

8. **Freitas, S. R., Longo, K. M., et al. (2011).** PREP-CHEM-SRC – 1.0: a preprocessor of trace gas and aerosol emission fields for regional and global atmospheric chemistry models. *Geoscientific Model Development*, 4(2), 419–433. https://doi.org/10.5194/gmd-4-419-2011
   *Widely used in Brazil to prepare fire emissions (including FINN-style inputs) for CCATT-BRAMS/WRF-Chem.*

## Regional context — Southern Brazil and Santa Catarina

9. **Teixeira, N. C., Chaffe, P. L. B., Chagas, V. B. P., Ribeiro, C. B., Rodrigues, R. R., and Hoinaski, L. (2025).** Recent fire occurrence and associated emissions in Southern Brazil. *Air Quality, Atmosphere & Health*, 18(4), 953–970. https://doi.org/10.1007/s11869-024-01681-5
   *Directly relevant regional study of fire emissions in Southern Brazil (which includes Santa Catarina).*

10. **Hoinaski, L., Will, R., and Ribeiro, C. B. (2024).** Brazilian Atmospheric Inventories – BRAIN: a comprehensive database of air quality in Brazil. *Earth System Science Data*, 16(5), 2385–2405. https://doi.org/10.5194/essd-16-2385-2024
    *A national air-quality/emissions database context for placing a state inventory within Brazil.*

## Conceptual emission model

11. **Seiler, W., and Crutzen, P. J. (1980).** Estimates of gross and net fluxes of carbon between the biosphere and the atmosphere from biomass burning. *Climatic Change*, 2(3), 207–247. https://doi.org/10.1007/BF00137988
    *The foundational `E = A × B × CC × EF` biomass-burning framework that FINN operationalises.*

## Chemistry constants (molar masses)

12. **Meija, J., Coplen, T. B., Berglund, M., et al. (2016).** Atomic weights of the elements 2013 (IUPAC Technical Report). *Pure and Applied Chemistry*, 88(3), 265–291. https://doi.org/10.1515/pac-2015-0305
    *Source of the molar masses used in step 01's mole→tonne conversion.*

## Software

13. **Pebesma, E. (2018).** Simple Features for R: Standardized Support for Spatial Vector Data. *The R Journal*, 10(1), 439–446. https://doi.org/10.32614/RJ-2018-009
    *The `sf` package used for all spatial operations in the R route.*

14. **Harris, C. R., et al. (2020).** Array programming with NumPy. *Nature*, 585(7825), 357–362. https://doi.org/10.1038/s41586-020-2649-2
15. **McKinney, W. (2010).** Data Structures for Statistical Computing in Python. *Proceedings of the 9th Python in Science Conference*, 56–61. https://doi.org/10.25080/Majora-92bf1922-00a
16. **Hunter, J. D. (2007).** Matplotlib: A 2D Graphics Environment. *Computing in Science & Engineering*, 9(3), 90–95. https://doi.org/10.1109/MCSE.2007.55
    *NumPy/pandas/Matplotlib underpin the Python route's tables and figures. GeoPandas (built on shapely/GEOS + pyproj/PROJ) is the Python spatial stack — software, https://geopandas.org/.*

## Analysis layer

*Verified in the review rounds of the manuscript (DOI resolved on CrossRef/DataCite or document read; see
`wildfire/REVISAO_auditoria_citacoes.md`).*

17. **Wiedinmyer, C., and Emmons, L. (2022).** Fire Inventory from NCAR version 2 Fire Emission [dataset]. NSF National Center for Atmospheric Research, Boulder. https://doi.org/10.5065/XNPA-AF09
    *The FINN v2.5 data set (RDA ds312.9); its June 2024 README is in `docs/`.*
18. **Giglio, L., Schroeder, W., Hall, J. V., and Justice, C. O. (2021).** MODIS Collection 6 and Collection 6.1 Active Fire Product User's Guide, version 1.0. https://modis-land.gsfc.nasa.gov/pdf/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf
    *Static-source criterion (≥ 16 detection days in a calendar year; Sect. 5.5, Table 10) used for the persistent-anomaly screening.*
19. **Mann, H. B. (1945).** Nonparametric tests against trend. *Econometrica*, 13(3), 245–259. https://doi.org/10.2307/1907187
20. **Sen, P. K. (1968).** Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63(324), 1379–1389. https://doi.org/10.1080/01621459.1968.10480934
21. **Holm, S. (1979).** A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70. https://www.jstor.org/stable/4615733
22. **Diggle, P. (1985).** A kernel method for smoothing point process data. *Applied Statistics*, 34(2), 138–147. https://doi.org/10.2307/2347366
23. **Jones, M. C. (1993).** Simple boundary correction for kernel density estimation. *Statistics and Computing*, 3(3), 135–146. https://doi.org/10.1007/BF00147776
24. **Loader, C. (1999).** *Local Regression and Likelihood*. Springer, New York. https://doi.org/10.1007/b98858
25. **Cronie, O., and van Lieshout, M. N. M. (2018).** A non-model-based approach to bandwidth selection for kernel estimators of spatial intensity functions. *Biometrika*, 105(2), 455–462. https://doi.org/10.1093/biomet/asy001
26. **Baddeley, A., Rubak, E., and Turner, R. (2015).** *Spatial Point Patterns: Methodology and Applications with R*. Chapman and Hall/CRC, Boca Raton. https://doi.org/10.1201/b19708
27. **Anselin, L. (1988).** *Spatial Econometrics: Methods and Models*. Kluwer, Dordrecht. https://doi.org/10.1007/978-94-015-7799-1
28. **Rey, S. J., and Anselin, L. (2007).** PySAL: a Python library of spatial analytical methods. *The Review of Regional Studies*, 37(1), 5–27. https://doi.org/10.52324/001c.8285
29. **Muñoz-Sabater, J., et al. (2021).** ERA5-Land: a state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data*, 13(9), 4349–4383. https://doi.org/10.5194/essd-13-4349-2021
30. **Svoboda, M., Hayes, M., and Wood, D. (2012).** *Standardized Precipitation Index User Guide* (WMO-No. 1090). World Meteorological Organization, Geneva. ISBN 978-92-63-11091-6
31. **Alencar, A. A. C., et al. (2022).** Long-term Landsat-based monthly burned area dataset for the Brazilian biomes using deep learning. *Remote Sensing*, 14(11), 2510. https://doi.org/10.3390/rs14112510
32. **MapBiomas (2025).** Algorithm Theoretical Basis Document (ATBD): MapBiomas Fire Collection 4, version 1. https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2025/06/ATBD-MapBiomas-Fogo-Colecao-4.pdf
33. **Souza Jr., C. M., et al. (2020).** Reconstructing three decades of land use and land cover changes in Brazilian biomes with Landsat archive and Earth Engine. *Remote Sensing*, 12(17), 2735. https://doi.org/10.3390/rs12172735
34. **NOAA Climate Prediction Center.** Oceanic Niño Index (ONI). https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt (access date to be recorded by the authors).
35. **IBGE (2025).** *Malha Municipal Digital e Áreas Territoriais 2024: notas metodológicas 01/2025*. Instituto Brasileiro de Geografia e Estatística, Rio de Janeiro.

## Data sources (provenance, not peer-reviewed)

- **FINN data archive (NSF NCAR RDA ds312.9).** https://rda.ucar.edu/datasets/ds312-9/ — and the FINN home page https://www2.acom.ucar.edu/modeling/finn-fire-inventory-ncar
- **NASA FIRMS** (MODIS & VIIRS active fire, FINN's satellite input). https://firms.modaps.eosdis.nasa.gov/
- **IBGE Malha Municipal** (Santa Catarina municipality boundaries). https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html
- **INPE Programa Queimadas / BDQueimadas** (Brazilian fire monitoring, for regional cross-checking). https://terrabrasilis.dpi.inpe.br/queimadas/portal/

---

### How to cite the official FINN data

When you publish results, cite the FINN model papers (refs 1 and/or 2 above,
matching the version you used) and acknowledge the data archive (NSF NCAR RDA
ds312.9). See the FINN home page for the project's current citation guidance.
