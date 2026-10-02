"""Small integrity, grid and artifact helpers; no label reading at import time."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from affine import Affine

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
PREP = ROOT / "data/prepared"
ART = ROOT / "artifacts"
EVIDENCE = ROOT / "evidence"
HEIGHT, WIDTH = 3730, 3292
GRID_TRANSFORM = Affine(100, 0, 243350, 0, -100, 4508550)
CRS = "EPSG:32611"
FOOTPRINT_PIXELS = 5_167_373
SEED = 20261002


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def write_json(path: str | Path, value: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".partial")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(p)


def verify_pinned(path: str | Path) -> dict:
    p = Path(path).resolve()
    manifest = read_json(ROOT / "data/input_manifest.json")
    rows = [r for r in manifest["files"] if (ROOT / r["path"]).resolve() == p]
    if len(rows) != 1:
        raise ValueError(f"No unique input hash pin for {p.name}")
    row = rows[0]
    if not p.is_file() or p.stat().st_size != row["bytes"] or sha256_file(p) != row["sha256"]:
        raise ValueError(f"Input integrity failed: {p.name}; run download_competition_data.sh")
    return row


def decode_runs(payload: bytes, total: int) -> np.ndarray:
    """Decode alternating outside/inside unsigned LEB128, rejecting malformed runs."""
    if total <= 0:
        raise ValueError("Positive raster size required")
    result = np.zeros(total, dtype=bool)
    pos = covered = 0
    inside = False
    while pos < len(payload):
        value = shift = 0
        while True:
            if pos >= len(payload) or shift > 63:
                raise ValueError("Truncated/oversized footprint run")
            b = payload[pos]
            pos += 1
            value |= (b & 127) << shift
            if not b & 128:
                break
            shift += 7
        if covered + value > total:
            raise ValueError("Footprint runs overflow raster")
        if inside:
            result[covered:covered + value] = True
        covered += value
        inside = not inside
    if covered != total:
        raise ValueError(f"Footprint covers {covered}, expected {total}")
    return result


def footprint() -> np.ndarray:
    p = RAW / "footprint.bin"
    verify_pinned(p)
    fp = decode_runs(p.read_bytes(), HEIGHT * WIDTH).reshape(HEIGHT, WIDTH)
    if fp.sum() != FOOTPRINT_PIXELS:
        raise ValueError("Footprint pixel count mismatch")
    return fp


def verify_grid(dataset) -> None:
    if dataset.shape != (HEIGHT, WIDTH) or dataset.crs is None or dataset.crs.to_epsg() != 32611 or dataset.transform != GRID_TRANSFORM:
        raise ValueError("Input does not match the pinned competition grid")


def tile_origins(fp: np.ndarray, size: int) -> list[tuple[int, int]]:
    if size <= 0:
        raise ValueError("Positive tile size required")
    return [(r, c) for r in range(0, fp.shape[0], size)
            for c in range(0, fp.shape[1], size)
            if fp[r:r + size, c:c + size].any()]


def padded_tile(array: np.ndarray, r: int, c: int, size: int, halo: int = 0) -> np.ndarray:
    """Zero-pad outside the GRID, never wrap opposite edges. Leading channels optional."""
    h, w = array.shape[-2:]
    r0, c0 = max(0, r - halo), max(0, c - halo)
    r1, c1 = min(h, r + size + halo), min(w, c + size + halo)
    shape = array.shape[:-2] + (size + 2 * halo, size + 2 * halo)
    out = np.zeros(shape, dtype=array.dtype)
    dr, dc = r0 - (r - halo), c0 - (c - halo)
    out[..., dr:dr + r1 - r0, dc:dc + c1 - c0] = array[..., r0:r1, c0:c1]
    return out
