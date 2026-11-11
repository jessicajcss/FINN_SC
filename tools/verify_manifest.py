#!/usr/bin/env python3
"""Check a reproduction against the published results (results/MANIFEST.sha256).

Usage (from the project root):
    python tools/verify_manifest.py            # check results/ against the manifest
    python tools/verify_manifest.py --write    # maintainers only: rewrite the manifest from results/

The manifest lists the SHA-256 checksum of every table (results/tables) and log (results/logs) of the
published run. Compressed tables (.csv.gz) are checked on their decompressed content, because the gzip
header stores a time stamp. Figures are not listed: PNG files carry the matplotlib version in their
metadata and differ in bytes between library versions even when the picture is identical.

For each file the script prints one of:
    OK          identical to the published file (byte for byte);
    EQUIVALENT  bytes differ, but every number agrees within a relative tolerance of 1e-9 and every text
                cell is identical (typical of a different library version printing a different last digit);
    DIFFERENT   numbers or text differ beyond that tolerance (the largest differences are shown);
    CHANGED     bytes differ and no reference copy is available to compare numbers (see below);
    MISSING     the file was not produced.
The numeric comparison needs the published copy of the file. In a git clone it is read from the last
commit (git show HEAD:<path>), so run the reproduction in a clone and commit nothing before checking.
Exit status: 0 when every file is OK or EQUIVALENT, 1 otherwise.
"""
import gzip
import hashlib
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "MANIFEST.sha256"
PATTERNS = ["results/tables/*.csv", "results/tables/*.csv.gz", "results/logs/*.txt"]
RTOL = 1e-9


def content(path: Path) -> bytes:
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == ".gz" else data


def sha256(path: Path) -> str:
    return hashlib.sha256(content(path)).hexdigest()


def published_copy(rel: str):
    """Bytes of the committed version of `rel` (decompressed if .gz), or None outside a git clone."""
    try:
        out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return gzip.decompress(out.stdout) if rel.endswith(".gz") else out.stdout


def compare_tables(new: bytes, old: bytes):
    import numpy as np
    import pandas as pd
    a = pd.read_csv(io.BytesIO(new))
    b = pd.read_csv(io.BytesIO(old))
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        return False, f"shape/columns differ: {a.shape} vs {b.shape}"
    worst, notes = 0.0, []
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv, yv = x.to_numpy(float), y.to_numpy(float)
            both_nan = np.isnan(xv) & np.isnan(yv)
            if (np.isnan(xv) != np.isnan(yv)).any():
                return False, f"column {c}: missing values differ"
            rel = np.abs(xv - yv) / np.maximum(np.abs(yv), 1e-300)
            rel[both_nan] = 0.0
            rel[(xv == 0) & (yv == 0)] = 0.0
            m = float(np.nanmax(rel)) if len(rel) else 0.0
            if m > worst:
                worst = m
            if m > RTOL:
                notes.append(f"{c}: max relative difference {m:.2e}")
        elif not x.astype(str).equals(y.astype(str)):
            return False, f"column {c}: text differs"
    if notes:
        return False, "; ".join(notes[:6])
    return True, f"max relative difference {worst:.1e}"


def compare_text(new: bytes, old: bytes):
    import difflib
    d = list(difflib.unified_diff(old.decode("utf-8", "replace").splitlines(),
                                  new.decode("utf-8", "replace").splitlines(), "published", "reproduced", lineterm="", n=0))
    return False, "\n      " + "\n      ".join(d[2:14]) + ("\n      ..." if len(d) > 14 else "")


def write():
    files = sorted({p for pat in PATTERNS for p in ROOT.glob(pat)})
    lines = ["# SHA-256 of the published results (tables and logs). Checked by tools/verify_manifest.py.",
             "# .csv.gz files: checksum of the decompressed content."]
    lines += [f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in files]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {MANIFEST.relative_to(ROOT)} ({len(files)} files)")


def check():
    entries = [l.split(None, 1) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    counts = {"OK": 0, "EQUIVALENT": 0, "DIFFERENT": 0, "CHANGED": 0, "MISSING": 0}
    for digest, rel in entries:
        rel = rel.strip()
        path = ROOT / rel
        if not path.is_file():
            status, note = "MISSING", ""
        elif sha256(path) == digest:
            status, note = "OK", ""
        else:
            old = published_copy(rel)
            if old is None or hashlib.sha256(old).hexdigest() != digest:
                status, note = "CHANGED", "(no published copy to compare numbers; run in a git clone)"
            else:
                ok, note = (compare_tables if ".csv" in rel else compare_text)(content(path), old)
                status = "EQUIVALENT" if ok else "DIFFERENT"
        counts[status] += 1
        if status != "OK":
            print(f"{status:10s} {rel} {note}")
    print(f"{len(entries)} files: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return 0 if counts["OK"] + counts["EQUIVALENT"] == len(entries) else 1


if __name__ == "__main__":
    if "--write" in sys.argv[1:]:
        write()
    else:
        sys.exit(check())
