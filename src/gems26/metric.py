"""Exact documented distance-weighted Tversky terms (alpha=.2, beta=.8, R=3 px).

https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric
TP is summed over TRUTH pixels, FP over PREDICTION pixels: TP+FP is generally
NOT the number of emitted pixels. The empty-truth convention here is zero.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

ALPHA, BETA, RADIUS = .2, .8, 3.


def finish(tp: float, fp: float, n_truth: int, n_pred: int, mass: float | None = None) -> dict:
    fn = max(0., n_truth - tp)
    denominator = tp + ALPHA * fp + BETA * fn
    return {"TP_w": float(tp), "FP_w": float(fp), "FN_w": float(fn),
            "n_truth": int(n_truth), "n_emitted": int(n_pred),
            "mass": float(n_pred if mass is None else mass),
            "dti": float(tp / denominator) if denominator > 0 else 0.}


def binary_coordinate_components(pred_coords: np.ndarray, truth_coords: np.ndarray) -> dict:
    p, g = np.asarray(pred_coords), np.asarray(truth_coords)
    if p.ndim != 2 or g.ndim != 2 or p.shape[1] != 2 or g.shape[1] != 2:
        raise ValueError("Coordinates must be N×2 raster row/column positions")
    if not np.isfinite(p).all() or not np.isfinite(g).all():
        raise ValueError("Finite coordinates required")
    if not len(g) or not len(p):
        return finish(0., float(len(p)), len(g), len(p))
    distance_to_p = cKDTree(p).query(g, k=1, workers=1)[0]
    distance_to_g = cKDTree(g).query(p, k=1, workers=1)[0]
    tp = np.maximum(1 - distance_to_p / RADIUS, 0).sum(dtype=np.float64)
    fp = np.minimum(distance_to_g / RADIUS, 1).sum(dtype=np.float64)
    return finish(float(tp), float(fp), len(g), len(p))


def dti(pred: np.ndarray, truth: np.ndarray, valid: np.ndarray | None = None,
        known: np.ndarray | None = None) -> dict:
    p, g = np.asarray(pred), np.asarray(truth)
    if p.ndim != 2 or p.shape != g.shape:
        raise ValueError("Aligned 2D prediction/truth required")
    active = np.ones(p.shape, dtype=bool)
    for m in (valid, known):
        if m is not None and (np.shape(m) != p.shape or not np.isin(m, [0, 1]).all()):
            raise ValueError("Aligned finite binary evaluation masks required")
    if valid is not None:
        active &= np.asarray(valid, bool)
    if known is not None:
        active &= ~np.asarray(known, bool)
    if not np.isfinite(p[active]).all() or ((p[active] < 0) | (p[active] > 1)).any():
        raise ValueError("Evaluated predictions must be finite in [0,1]")
    if not np.isin(g[active], [0, 1]).all():
        raise ValueError("Binary finite truth required in evaluation domain")
    pp = np.where(active, p, 0).astype(np.float64)
    gg = active & (g > 0)
    pc = np.argwhere(pp > 0)
    gc = np.argwhere(gg)
    if np.isin(pp[active], [0, 1]).all():
        return binary_coordinate_components(pc, gc)
    if not len(gc) or not len(pc):
        return finish(0., float(pp.sum()), len(gc), len(pc), float(pp.sum()))
    credit = np.zeros(len(gc), dtype=np.float64)
    h, w = p.shape
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            weight = max(1 - np.hypot(dy, dx) / RADIUS, 0)
            if weight <= 0:
                continue
            rr, cc = gc[:, 0] + dy, gc[:, 1] + dx
            good = (rr >= 0) & (cc >= 0) & (rr < h) & (cc < w)
            credit[good] = np.maximum(credit[good], pp[rr[good], cc[good]] * weight)
    distances = cKDTree(gc).query(pc, k=1, workers=1)[0]
    fp = (pp[pc[:, 0], pc[:, 1]] * np.minimum(distances / RADIUS, 1)).sum()
    return finish(float(credit.sum()), float(fp), len(gc), len(pc), float(pp.sum()))


def pooled(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("At least one component result required")
    return finish(sum(r["TP_w"] for r in rows), sum(r["FP_w"] for r in rows),
                  sum(r["n_truth"] for r in rows), sum(r["n_emitted"] for r in rows),
                  sum(r.get("mass", r["n_emitted"]) for r in rows))
