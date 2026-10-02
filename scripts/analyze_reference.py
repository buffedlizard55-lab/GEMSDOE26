#!/usr/bin/env python3
"""Reproduce the historical 1.5-pixel thinning WITHOUT labels and verify identity.

Algorithm provenance: buffedlizard55-lab/GEMSDOE24/src/gems/thinning.py at
07345ea0604953d7efb858d9cfbc21e20c7aca0b. This independent implementation follows
its row-first component seed and FIFO eight-neighbour traversal exactly.
"""
from __future__ import annotations

from collections import deque
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import label
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import RAW, EVIDENCE, footprint, read_json, sha256_file, utcnow, write_json
from gems26.submission import prediction_digest


def historical_dot_thin(mask: np.ndarray, radius: float = 1.5) -> np.ndarray:
    m = np.asarray(mask, bool)
    if m.ndim != 2 or not np.isfinite(radius) or radius <= 0:
        raise ValueError("2D mask and finite positive radius required")
    if radius <= 1 or not m.any():
        return m.copy()
    pad = int(np.ceil(radius)) + 1
    h, w = m.shape
    padded = np.pad(m, pad)
    hp, wp = padded.shape
    flat = bytearray(padded.tobytes())
    visited, blocked, chosen = bytearray(hp * wp), bytearray(hp * wp), bytearray(hp * wp)
    disc = [dy * wp + dx for dy in range(-pad + 1, pad) for dx in range(-pad + 1, pad)
            if dy * dy + dx * dx < radius * radius]
    neighbours = (-wp - 1, -wp, -wp + 1, -1, 1, wp - 1, wp, wp + 1)
    components, _ = label(padded, structure=np.ones((3, 3), int))
    ids = np.flatnonzero(components)
    _, first = np.unique(components.ravel()[ids], return_index=True)
    for seed in ids[np.sort(first)].tolist():
        if visited[seed]:
            continue
        queue = deque([seed])
        visited[seed] = 1
        while queue:
            q = queue.popleft()
            if not blocked[q]:
                chosen[q] = 1
                for d in disc:
                    blocked[q + d] = 1
            for d in neighbours:
                j = q + d
                if flat[j] and not visited[j]:
                    visited[j] = 1
                    queue.append(j)
    return np.frombuffer(chosen, dtype=np.uint8).reshape(hp, wp)[pad:pad + h, pad:pad + w].astype(bool)


def main():
    fp = footprint()
    with rasterio.open(RAW / "h19_parent.tif") as d:
        parent = (d.read(1) > 0) & fp
    with rasterio.open(RAW / "h25_best.tif") as d:
        reference = (d.read(1) > 0) & fp
    recomputed = historical_dot_thin(parent)
    distance = cKDTree(np.argwhere(reference)).query(np.argwhere(parent))[0]
    holdout = read_json(EVIDENCE / "holdout.json")
    confirmation = read_json(EVIDENCE / "holdout_confirmation.json")
    decomposition = {}
    for arm in ("h19_parent", "h25_reference"):
        decomposition[arm] = {
            "dense": confirmation["dense"][arm]["pooled"],
            "sparse_mean_TP_w": float(np.mean([r["TP_w"] for r in confirmation["sparse"][arm]["pooled_per_draw"]])),
            "sparse_mean_FP_w": float(np.mean([r["FP_w"] for r in confirmation["sparse"][arm]["pooled_per_draw"]])),
        }
    report = {"checked_utc": utcnow(), "parent_file_sha256": sha256_file(RAW / "h19_parent.tif"),
              "reference_file_sha256": sha256_file(RAW / "h25_best.tif"),
              "parent_pixels": int(parent.sum()), "reference_pixels": int(reference.sum()),
              "emission_retained_fraction": float(reference.sum() / parent.sum()),
              "reference_adds_no_pixel": not bool((reference & ~parent).any()),
              "exact_recomputed_pixel_identity": bool(np.array_equal(recomputed, reference)),
              "reference_prediction_sha256": prediction_digest(reference, fp),
              "recomputed_prediction_sha256": prediction_digest(recomputed, fp),
              "parent_to_kept_distance_pixels": {"mean": float(distance.mean()), "median": float(np.median(distance)), "maximum": float(distance.max())},
              "algorithm_reads_labels": False,
              "upstream_code_url": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/src/gems/thinning.py",
              "owner_reported_parent_score": .1922, "owner_reported_reference_score": .2477,
              "owner_reported_relative_gain": .2477 / .1922 - 1,
              "score_to_file_mapping_verified_by_platform_receipt": False,
              "local_sparse_ratio": holdout["confirmation_summary"]["sparse"]["h25_reference"]["mean_pooled_dti"] /
                                    holdout["confirmation_summary"]["sparse"]["h19_parent"]["mean_pooled_dti"],
              "metric_warning": "TP sums over truth and FP over predictions; TP+FP is not generally emitted pixel count",
              "paired_local_decomposition": decomposition,
              "local_dense_TP_credit_retained": decomposition["h25_reference"]["dense"]["TP_w"] / decomposition["h19_parent"]["dense"]["TP_w"],
              "local_dense_FP_mass_retained": decomposition["h25_reference"]["dense"]["FP_w"] / decomposition["h19_parent"]["dense"]["FP_w"]}
    write_json(EVIDENCE / "reference_forensics.json", report)
    print(report)
    if not report["exact_recomputed_pixel_identity"]:
        raise SystemExit("Historical thinning identity did not reproduce; do not claim it did")

if __name__ == "__main__":
    main()
