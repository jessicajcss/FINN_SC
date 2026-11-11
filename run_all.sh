#!/usr/bin/env bash
# =============================================================================
# run_all.sh - run the full FINN Santa Catarina pipeline (Linux / macOS / WSL)
# -----------------------------------------------------------------------------
# Usage:
#   ./run_all.sh r        # run via the R route
#   ./run_all.sh python   # run via the Python route   (aliases: py, python3)
#   ./run_all.sh r --stack   # also run the optional step 03 (stack years)
#   ./run_all.sh analysis    # reproduce every table, statistic and figure of the manuscript
#                            #         and of the inventory report from the archived records, then test
#
# Parameters (years / version / sensor / paths) come from config/config.yml.
# Override interpreters with env vars, e.g.  PYTHON=python3.11 ./run_all.sh py
# =============================================================================
set -euo pipefail

ROUTE="${1:-}"
STACK="${2:-}"
RSCRIPT="${RSCRIPT:-Rscript}"
PYTHON="${PYTHON:-python3}"

# Always run from the project root (the directory of this script).
cd "$(dirname "$0")"

run_step() { echo ""; echo ">>> $*"; "$@"; }

case "$ROUTE" in
  r|R)
    echo "=== FINN SC pipeline - R route ==="
    run_step "$RSCRIPT" R/00_download_finn.R
    run_step "$RSCRIPT" R/01_convert_units.R
    run_step "$RSCRIPT" R/02_clip_region.R
    [ "$STACK" = "--stack" ] && run_step "$RSCRIPT" R/03_stack_years.R
    run_step "$RSCRIPT" R/04_aggregate_region.R
    run_step "$RSCRIPT" R/05_descriptive_analysis.R
    ;;
  py|python|python3)
    echo "=== FINN SC pipeline - Python route ==="
    run_step "$PYTHON" python/00_download_finn.py
    run_step "$PYTHON" python/01_convert_units.py
    run_step "$PYTHON" python/02_clip_region.py
    [ "$STACK" = "--stack" ] && run_step "$PYTHON" python/03_stack_years.py
    run_step "$PYTHON" python/04_aggregate_region.py
    run_step "$PYTHON" python/05_descriptive_analysis.py
    ;;
  analysis)
    echo "=== FINN SC analysis layer (route B) ==="
    run_step "$PYTHON" python/run_analysis.py
    run_step "$PYTHON" -m pytest -q tests
    ;;
  *)
    echo "Usage: $0 {r|python|analysis} [--stack]"
    echo "  r        run the R route"
    echo "  python   run the Python route (aliases: py, python3)"
    echo "  analysis reproduce the manuscript/report results from the archived records and run the tests"
    echo "  --stack  also run the optional stack-years step (03)"
    exit 1
    ;;
esac

echo ""
echo "=== Pipeline complete. Outputs are in data/output/. ==="
