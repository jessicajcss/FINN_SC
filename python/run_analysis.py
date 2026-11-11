#!/usr/bin/env python3
"""Run the whole analysis layer (route B) in order and write results/.

    python python/run_analysis.py            # Python steps a01-a09, R kernel density, figures (a10), co-authors' review
                                             # (a11, a12), study-area map (2019 table, then the 2023 figure), report flowchart
    python python/run_analysis.py --no-r     # skip R (the kernel-density figure then uses the archived results/tables/kde_*)

Route B starts from the archived record table data/derived/finn_sc_records_2003_2025.csv.gz.
Route A (raw FINN -> records) is python/00-02 + python/06_build_sc_records.py; see README.md.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "python" / "analysis"
STEPS = ["a01_events_screening.py", "a02_series_trends.py", "a03_municipal_mesoregion.py", "a04_genveg_partition.py",
         "a05_mapbiomas_comparison.py", "a06_climate_drivers.py", "a07_landcover.py", "a08_report_indicators.py",
         "a09_emission_factor_check.py"]


def run(cmd, **env):
    print("\n>>>", " ".join(f"{k}={v}" for k, v in env.items()), " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True, env={**os.environ, **env})


for s in STEPS:
    run([sys.executable, str(A / s)])
if "--no-r" not in sys.argv:
    rs = shutil.which("Rscript")
    if rs is None:
        sys.exit("Rscript not found: install R (>= 4.3) with sf and spatstat, or run with --no-r")
    run([rs, "R/analysis/kde_events.R"])
    run([rs, "R/analysis/kde_sensitivity_annual.R", "all"])          # (about 40 min)
run([sys.executable, str(A / "a10_figures.py")])
run([sys.executable, str(A / "a11_coauthor_review.py")])            # co-authors' review (Figure S3)
run([sys.executable, str(A / "a12_gee_review_outputs.py")])         # Earth Engine results of the co-authors' review
run([sys.executable, str(A / "a13_recurrence_landcover.py")])       # recurrence of events and land cover (report)
run([sys.executable, str(A / "a14_validity_checks.py")])            # land cover at the events, mapped-area scenario, recurrence CIs
run([sys.executable, str(A / "a15_v7_review.py")])               # robustness checks of the English manuscript v7
run([sys.executable, str(A / "a16_v71_review.py")])              # checks asked in the comments on the v7 abstract
run([sys.executable, str(A / "a17_v72_review.py")])              # FINN v1.5 two-day rule, land cover by mesoregion, profiles (v7.2)
run([sys.executable, str(A / "a18_exports.py")])                  # Comex Stat exports 2025 by mesoregion and municipality (v7.2)
run([sys.executable, str(A / "a19_v72_followup.py")])             # FINNv1 two-day rule check, forest class scenario, NOx check (v7.2)
run([sys.executable, str(A / "a20_finn15_correction.py")])         # FINN v1.5 studies with and without the next-day continuations
run([sys.executable, str(ROOT / "tools" / "study_area_map.py")], FIG1_YEAR="2019")   # report figure (2019) and results/tables/landcover2019_mesoregion.csv
run([sys.executable, str(ROOT / "tools" / "study_area_map.py")])      # manuscript Figure 1 (2023) and landcover2023_mesoregion.csv
run([sys.executable, str(ROOT / "tools" / "fig7_flowchart.py")])      # report Figure 7 (repository structure)
run([sys.executable, str(A / "a10_figures.py")], FIG_LANG="en")   # English figures (*_en.png; no log)
run([sys.executable, str(A / "figS3_en.py")])                     # English Figure S3
run([sys.executable, str(A / "figures_est_en.py")])               # ES&T Figure 2 (four panels) and TOC graphic
run([sys.executable, str(A / "figures_est_v72.py")])             # TOC graphic of the ES&T version (v7.2)
# fig_v7_en.py (manuscript v7) is superseded by fig_v71.py, which writes the same English file names
run([sys.executable, str(A / "fig_v71.py")], FIG_LANG="en")          # Figures 8 and 9 of manuscript v7.1 (English)
run([sys.executable, str(A / "fig_v71.py")], FIG_LANG="en", FIG_NOTES="0")   # Figures 8 and 9 without notes (*_nn_en.png)
run([sys.executable, str(A / "fig_v71.py")], FIG_LANG="pt")          # Figures 8 and 9 of manuscript v7.1 (Portuguese)
run([sys.executable, str(A / "fig_v71.py")], FIG_LANG="pt", FIG_NOTES="0")   # Figures 8 and 9 without notes (*_nn_pt.png)
run([sys.executable, str(A / "a10_figures.py")], FIG_LANG="en", FIG_NOTES="0")   # maps without source notes (*_nn_en.png; manuscript v7.2)
run([sys.executable, str(A / "a10_figures.py")], FIG_LANG="pt", FIG_NOTES="0")   # maps without source notes (*_nn.png; manuscript v7.2)
print("\nAll analysis steps finished. Tables: results/tables; figures: results/figures; logs: results/logs.")
