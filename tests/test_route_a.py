"""Route A replication test: raw FINN records -> steps 01, 02 and 06 of the maintained Python pipeline ->
records identical to the archived dataset.

tests/data/raw_2025_subset_v2.5.1_MODIS+VIIRS.csv.gz holds raw FINN v2.5.1 NRT records (native units,
format written by step 00) of 1 January to 28 May 2025 (DAY 1-148, 147 daily files): every record of those
days inside Santa Catarina plus a sample of records elsewhere, so that the clipping step is exercised.
The test runs the pipeline in a temporary copy of the project and compares the result with
data/derived/finn_sc_records_2003_2025.csv.gz (tools/compare_records.py).
"""
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tests" / "data" / "raw_2025_subset_v2.5.1_MODIS+VIIRS.csv.gz"
pytest.importorskip("geopandas")


@pytest.mark.skipif(not (ROOT / "data/inputs/SC_Municipios_2024.shp").is_file(), reason="IBGE shapefile missing")
def test_route_a_reproduces_archived_records(tmp_path):
    proj = tmp_path / "proj"
    for d in ("config", "python", "tools", "data/inputs", "data/derived"):
        shutil.copytree(ROOT / d, proj / d, ignore=shutil.ignore_patterns("__pycache__", "finn_sc_records_rebuilt*"))
    (proj / "data/raw_finn").mkdir(parents=True)
    (proj / "data/interim").mkdir(parents=True)
    (proj / "data/output").mkdir(parents=True)
    with gzip.open(RAW, "rb") as fi, open(proj / "data/raw_finn/2025_finn_v2.5.1_MODIS+VIIRS.csv", "wb") as fo:
        shutil.copyfileobj(fi, fo)
    cfg = (proj / "config/config.yml").read_text(encoding="utf-8")
    cfg = cfg.replace('  years: [2019]', '  years: [2025]').replace('  version: "v1.5"', '  version: "v2.5.1"').replace('  sensor: "MODIS"  ', '  sensor: "MODIS+VIIRS"  ')
    (proj / "config/config.yml").write_text(cfg, encoding="utf-8")
    for step in ("01_convert_units.py", "02_clip_region.py", "06_build_sc_records.py"):
        subprocess.run([sys.executable, str(proj / "python" / step)], cwd=proj, check=True)
    out = subprocess.run([sys.executable, str(proj / "tools/compare_records.py")], cwd=proj, capture_output=True, text=True)
    print(out.stdout)
    assert out.returncode == 0
    assert "rebuilt 2341 | archived (same days) 2341 | matched 2341" in out.stdout
    assert "municipality differences: 0" in out.stdout
