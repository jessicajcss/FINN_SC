# Reproducibility tests

> 🌐 **English** · [Português (pt-BR)](reproducibility.pt-BR.md)

## Published run

The tables (`results/tables/`) and run logs (`results/logs/`) kept in the repository are the published run. The
SHA-256 sum of each is in `results/MANIFEST.sha256`. The exact Python library versions of that run are in
`requirements-lock.txt`. Figures are not in the manifest, because a PNG file stores the matplotlib version and its
bytes change between versions even when the picture is identical.

## How to check a reproduction

```bash
python python/run_analysis.py --no-r     # recomputes tables, logs and figures
python -m pytest -q tests                # 76 tests: units, statistics, published values, route A
python tools/verify_manifest.py          # compares tables and logs with the published run
```

`verify_manifest.py` labels each file OK (byte-identical), EQUIVALENT (numbers equal within a relative tolerance of
10⁻⁹), DIFFERENT (larger difference) or CHANGED (bytes differ and no published copy is available to compare the
numbers, e.g. outside a git clone).

## Independent test of 1 November 2026

Environment different from the published run: Linux, Python 3.10.12, pandas 2.3.3, numpy 2.2.6, scipy 1.15.3,
geopandas 1.1.4, matplotlib 3.10.9, shapely 2.1.2, pyproj 3.7.1, spreg 1.9.0, esda 2.7.0 and libpysal 4.13.0.

* Recomputed on this machine: `a01` to `a09` and `a11` to `a14`, from a clean copy of the repository. `a10`
  (figures) exceeded the 3-minute limit per command of the test session and was not recomputed. R was not used
  (`--no-r`).
* Result: 59 of the 73 manifest files were byte-identical. In the other 14, only the last digits of floating-point
  values changed. The largest relative differences were in the spatial-error-model outputs: 8 × 10⁻⁵ in
  `landcover_sem.csv` (Moran's I of the residuals) and 3 × 10⁻⁵ in `recurrence_sem.csv`. In the other tables the
  differences stayed below 2 × 10⁻⁶. In the `a13` log, the last printed digit of one p-value changed (5.53 × 10⁻⁷¹
  and 5.52 × 10⁻⁷¹). No rounded value quoted in the article or in the report changed.
* The 76 tests passed on the recomputed results.
* The test revealed an environment dependence in `a14`: in 5,030 events (6.0%) the largest FINN area belongs to two
  or more vegetation types, and the choice of the dominant type in these ties depended on the sorting algorithm of
  the installed pandas. `a14` now assigns ties to the lowest type code, the rule of `a08`, and logs the number of
  ties and the result with the opposite rule. The table `finn_genveg_vs_mapbiomas.csv`, the `a14` log, the test
  `test_round15.py` and the manifest were updated.
