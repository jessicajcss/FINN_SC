# =============================================================================
# Makefile - FINN Santa Catarina wildfire emissions pipeline
# -----------------------------------------------------------------------------
# Drives both the R and the Python routes. Parameters (years, version, sensor,
# paths) live in config/config.yml, NOT here. Run from the project root.
#
# Common usage:
#   make install        # install both R and Python dependencies
#   make all-r          # run the full pipeline via R
#   make all-py         # run the full pipeline via Python
#   make help           # list every target
#
# Override the interpreters if needed:
#   make all-py PYTHON=python3.11
#   make all-r  RSCRIPT=/usr/local/bin/Rscript
# (Windows without `make`: use run_all.bat instead.)
# =============================================================================

RSCRIPT ?= Rscript
PYTHON  ?= python3

.PHONY: help install install-r install-py \
        r-download r-convert r-clip r-stack r-aggregate r-describe all-r \
        py-download py-convert py-clip py-stack py-aggregate py-describe all-py \
        records analysis analysis-py kde test reproduce \
        clean clean-outputs

# ---- Help --------------------------------------------------------------------
help:
	@echo "FINN Santa Catarina pipeline - make targets"
	@echo ""
	@echo "  Setup:"
	@echo "    install         install R and Python dependencies"
	@echo "    install-r       Rscript install_r_packages.R"
	@echo "    install-py      pip install -r requirements.txt"
	@echo ""
	@echo "  Full pipeline:"
	@echo "    all-r           R route: download -> convert -> clip -> aggregate -> describe"
	@echo "    all-py          Python route: same steps"
	@echo ""
	@echo "  Individual steps (R):  r-download r-convert r-clip r-stack r-aggregate r-describe"
	@echo "  Individual steps (Py): py-download py-convert py-clip py-stack py-aggregate py-describe"
	@echo ""
	@echo "  Paper / report results (route B: from the archived SC records):"
	@echo "    analysis        python/run_analysis.py: tables, statistics, kernel density (R) and figures -> results/"
	@echo "    analysis-py     same, without the R kernel density"
	@echo "    kde             Rscript R/analysis/kde_events.R only"
	@echo "    test            pytest: unit tests, golden values of the manuscript/report, route-A replication test"
	@echo "    reproduce       analysis + test"
	@echo "    records         route A: build data/derived/finn_sc_records_rebuilt.csv.gz from steps 00-02"
	@echo ""
	@echo "  Cleanup:"
	@echo "    clean-outputs   remove generated raw/interim/output files (keeps inputs)"
	@echo "    clean           alias for clean-outputs"
	@echo ""
	@echo "  Edit config/config.yml to choose years / version / sensor / region."

# ---- Setup -------------------------------------------------------------------
install: install-r install-py
install-r:
	$(RSCRIPT) install_r_packages.R
install-py:
	$(PYTHON) -m pip install -r requirements.txt

# ---- R route -----------------------------------------------------------------
r-download:
	$(RSCRIPT) R/00_download_finn.R
r-convert:
	$(RSCRIPT) R/01_convert_units.R
r-clip:
	$(RSCRIPT) R/02_clip_region.R
r-stack:
	$(RSCRIPT) R/03_stack_years.R
r-aggregate:
	$(RSCRIPT) R/04_aggregate_region.R
r-describe:
	$(RSCRIPT) R/05_descriptive_analysis.R
all-r: r-download r-convert r-clip r-aggregate r-describe
	@echo "R pipeline complete. See data/output/."

# ---- Python route ------------------------------------------------------------
py-download:
	$(PYTHON) python/00_download_finn.py
py-convert:
	$(PYTHON) python/01_convert_units.py
py-clip:
	$(PYTHON) python/02_clip_region.py
py-stack:
	$(PYTHON) python/03_stack_years.py
py-aggregate:
	$(PYTHON) python/04_aggregate_region.py
py-describe:
	$(PYTHON) python/05_descriptive_analysis.py
all-py: py-download py-convert py-clip py-aggregate py-describe
	@echo "Python pipeline complete. See data/output/."

# ---- Analysis layer ---------------------------------------------------
records:
	$(PYTHON) python/06_build_sc_records.py
analysis:
	$(PYTHON) python/run_analysis.py
analysis-py:
	$(PYTHON) python/run_analysis.py --no-r
kde:
	$(RSCRIPT) R/analysis/kde_events.R
test:
	$(PYTHON) -m pytest -q tests
reproduce: analysis test
	@echo "Results reproduced in results/ and checked against the published values (tests/)."

# ---- Cleanup -----------------------------------------------------------------
# Removes generated data products but keeps folders and inputs.
clean-outputs:
	@rm -f data/raw_finn/*.csv data/interim/*.csv 2>/dev/null || true
	@find data/output -type f ! -name '.gitkeep' -delete 2>/dev/null || true
	@echo "Removed generated raw/interim/output files (inputs kept)."
clean: clean-outputs
