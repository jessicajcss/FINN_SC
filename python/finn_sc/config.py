"""Configuration loading for the FINN Santa Catarina pipeline.

Reads the SAME config/config.yml used by the R scripts, so both routes stay
in sync. Paths in the config are relative to the project root, which is
detected by walking up from this file until config/config.yml is found.

PyYAML is the preferred parser and is listed in requirements.txt. If it is not
installed in the active environment, this module falls back to a small built-in
reader that understands the subset of YAML used by config/config.yml (block
mappings, scalars, quoted strings, ints/floats, booleans, ``~``/null, and flow
lists / flow maps). The fallback means the pipeline still runs in a bare
environment; installing PyYAML (``conda install -c conda-forge pyyaml`` or
``pip install pyyaml``) is still recommended for full YAML support.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

try:                                    # preferred: the real YAML parser
    import yaml                          # type: ignore
    _HAVE_YAML = True
except Exception:                        # ModuleNotFoundError, or a broken install
    yaml = None                          # type: ignore
    _HAVE_YAML = False


# ---------------------------------------------------------------------------
# Minimal YAML fallback (used only when PyYAML is unavailable)
# ---------------------------------------------------------------------------
def _strip_inline_comment(line: str) -> str:
    """Drop a ``#`` comment that is not inside quotes or [ ] / { } brackets."""
    out: List[str] = []
    quote = None
    depth = 0
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch in "[{":
            depth += 1
            out.append(ch)
        elif ch in "]}":
            depth = max(0, depth - 1)
            out.append(ch)
        elif ch == "#" and depth == 0 and (i == 0 or line[i - 1] in " \t"):
            break                        # start of a comment
        else:
            out.append(ch)
    return "".join(out)


def _split_flow(body: str) -> List[str]:
    """Split a flow collection body on top-level commas (respect quotes/brackets)."""
    parts: List[str] = []
    buf: List[str] = []
    quote = None
    depth = 0
    for ch in body:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch in "[{":
            depth += 1
            buf.append(ch)
        elif ch in "]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _parse_scalar(tok: str) -> Any:
    """Parse a single YAML scalar / flow value the config file can contain."""
    s = tok.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if s[0] == "[" and s[-1] == "]":
        return [_parse_scalar(x) for x in _split_flow(s[1:-1])]
    if s[0] == "{" and s[-1] == "}":
        out: Dict[str, Any] = {}
        for item in _split_flow(s[1:-1]):
            if ":" in item:
                k, _, v = item.partition(":")
                out[_parse_scalar(k)] = _parse_scalar(v)
        return out
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s                             # bare string


def _minimal_yaml_load(text: str) -> Dict[str, Any]:
    """Parse the subset of YAML used by config/config.yml into a dict.

    Supports indentation-based block mappings, scalar values, quoted strings,
    numbers, booleans, ``~``/null and flow lists / flow maps. Block sequences
    (``- item`` lines) are intentionally NOT supported — the config file uses
    only flow-style lists — and raise a clear error so the caller can fall back
    to asking the user to install PyYAML.
    """
    rows = []                            # (indent, key, raw_value)
    for raw in text.splitlines():
        line = _strip_inline_comment(raw)
        if line.strip() == "":
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if content.startswith("- "):
            raise ValueError("block sequences are not supported by the fallback parser")
        if ":" not in content:
            raise ValueError(f"cannot parse config line: {raw!r}")
        key, _, val = content.partition(":")
        key = key.strip()
        if len(key) >= 2 and key[0] == key[-1] and key[0] in ("'", '"'):
            key = key[1:-1]              # unquote "NO" / 'NO' -> NO (match PyYAML)
        rows.append((indent, key, val.strip()))

    root: Dict[str, Any] = {}
    stack = [(-1, root)]                  # (indent, container dict)
    for idx, (indent, key, val) in enumerate(rows):
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if val == "":
            # nested mapping if the next row is indented deeper; else explicit null
            if idx + 1 < len(rows) and rows[idx + 1][0] > indent:
                child: Dict[str, Any] = {}
                parent[key] = child
                stack.append((indent, child))
            else:
                parent[key] = None
        else:
            parent[key] = _parse_scalar(val)
    return root


_warned_no_yaml = False


def _load_yaml_text(text: str) -> Dict[str, Any]:
    """Parse YAML text with PyYAML if available, else the built-in fallback."""
    global _warned_no_yaml
    if _HAVE_YAML:
        return yaml.safe_load(text)
    if not _warned_no_yaml:
        print(
            "[finn_sc] PyYAML not found - using the built-in minimal config reader.\n"
            "          For full YAML support install it once:\n"
            "            conda install -c conda-forge pyyaml   (or)   pip install pyyaml",
            file=sys.stderr,
        )
        _warned_no_yaml = True
    try:
        return _minimal_yaml_load(text)
    except Exception as exc:             # pragma: no cover - exotic hand edits
        raise ModuleNotFoundError(
            "PyYAML is not installed and the built-in fallback could not parse "
            f"config/config.yml ({exc}). Install PyYAML to continue:\n"
            "  conda install -c conda-forge pyyaml   (or)   pip install pyyaml\n"
            "Or recreate the environment in one step:\n"
            "  conda env create -f environment.yml   (then: conda activate finn)"
        ) from exc


def project_root(start: Path | None = None) -> Path:
    """Return the project root (the folder that contains config/config.yml)."""
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "config" / "config.yml").is_file():
            return parent
    # Fallback: two levels up from python/finn_sc/
    return Path(__file__).resolve().parents[2]


def load_config(path: str | os.PathLike | None = None) -> Dict[str, Any]:
    """Load config.yml as a dict.

    Parameters
    ----------
    path : optional explicit path to config.yml. If omitted, the file is
        located relative to the detected project root.
    """
    root = project_root()
    cfg_path = Path(path) if path else root / "config" / "config.yml"
    if not cfg_path.is_file():
        raise FileNotFoundError(
            f"config.yml not found at {cfg_path}. Run from the project root."
        )
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = _load_yaml_text(fh.read())
    # Stash the resolved root so callers can build absolute paths.
    cfg["_root"] = str(root)
    return cfg


def resolve(cfg: Dict[str, Any], rel: str) -> Path:
    """Resolve a config-relative path against the project root."""
    return Path(cfg["_root"]) / rel
