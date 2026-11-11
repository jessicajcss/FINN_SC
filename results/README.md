# `results/`: outputs of the analysis layer

Written by `python python/run_analysis.py`, which runs the Python steps a01 to a14, `R/analysis/kde_events.R`,
`tools/study_area_map.py` and `tools/fig7_flowchart.py`:

* `tables/`: CSV tables (56 files; the `.csv.gz` files are compressed);
* `figures/`: PNG figures (26 files);
* `logs/`: plain-text logs with every number quoted in the manuscript and in the report (17 files);
* `MANIFEST.sha256`: SHA-256 checksums of the tables and logs of the published run;
* `brain_2019/`: comparison with BRAIN, 2019 (outputs of `notebooks/BRAIN_FINN_comparison_SC_2019.ipynb`, outside
  the manifest; see `brain_2019/README.md`).

The copies committed here are the outputs of the published run. After you run the analysis
yourself, check your copy with:

```bash
python -m pytest -q tests                 # 76 tests, including every published value
python tools/verify_manifest.py           # byte-for-byte (or numerical) comparison with the published run
```

Which file supports which published number, and which file is which figure of the manuscript:
[`../docs/results_map.md`](../docs/results_map.md) ([Português](../docs/results_map.pt-BR.md)).
