"""Label-free ridge NMS and score-ordered Poisson-disk emission.

The historical reference uses a different deterministic BFS thinning operator.
Both the matched raw and SSL heads use this SAME fixed new operator.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter
from scipy.stats import rankdata

BUDGET_FRACTION = 60069 / 5167373


def percentile_rank(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    a, v = np.asarray(values), np.asarray(valid, bool)
    if a.shape != v.shape or not np.isfinite(a[v]).all():
        raise ValueError("Aligned finite rank scores required")
    out = np.zeros(a.shape, dtype=np.float32)
    n = int(v.sum())
    if n:
        out[v] = rankdata(a[v], method="average").astype(np.float32) / n
    return out


def ridge_nms(score: np.ndarray, support: np.ndarray, sigma: float = 1.) -> np.ndarray:
    a, v = np.asarray(score, dtype=np.float32), np.asarray(support, bool)
    if a.shape != v.shape or a.ndim != 2 or min(a.shape) < 3 or not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("Aligned >=3-pixel 2D arrays and positive sigma required")
    v = v & np.isfinite(a)
    supported = binary_erosion(v, structure=np.ones((3, 3), bool), iterations=int(np.ceil(4 * sigma)) + 3)
    smooth = gaussian_filter(np.where(v, a, 0), sigma)
    gy, gx = np.gradient(smooth)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    hxy = (hxy + hyx) * .5
    lam = (hxx + hyy) * .5 - np.sqrt(((hxx - hyy) * .5) ** 2 + hxy ** 2)
    vx, vy = hxy, lam - hxx
    degenerate = np.abs(vx) + np.abs(vy) < 1e-12
    angle = np.mod(np.arctan2(np.where(degenerate, 0, vy), np.where(degenerate, 1, vx)), np.pi)
    direction = np.round(angle / (np.pi / 4)).astype(np.int8) % 4
    pad = np.pad(smooth, 1, mode="edge")
    h, w = a.shape
    keep = np.zeros(a.shape, dtype=bool)
    for q, (dy, dx) in enumerate(((0, 1), (1, 1), (1, 0), (1, -1))):
        plus = pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        minus = pad[1 - dy:1 - dy + h, 1 - dx:1 - dx + w]
        keep |= (direction == q) & (smooth >= plus) & (smooth >= minus) & ((smooth > plus) | (smooth > minus))
    return keep & supported & (lam < -1e-7) & (a > 0)


def poisson_emit(score: np.ndarray, eligible: np.ndarray, count: int,
                 min_distance: float = 1.5) -> np.ndarray:
    a, valid = np.asarray(score), np.asarray(eligible, bool)
    if a.ndim != 2 or a.shape != valid.shape or count < 0 or not np.isfinite(min_distance) or min_distance <= 0:
        raise ValueError("Aligned 2D grids, nonnegative budget and positive finite separation required")
    out = np.zeros(a.shape, bool)
    if count == 0:
        return out
    ids = np.flatnonzero(valid & np.isfinite(a) & (a > 0))
    if not len(ids):
        return out
    # Multiplicative hash breaks exact ties without a north/row-first geometric priority.
    tie = (ids.astype(np.uint64) * np.uint64(11400714819323198485))
    order = np.lexsort((tie, -a.ravel()[ids]))
    h, w = a.shape
    blocked = np.zeros(a.shape, bool)
    r = int(np.ceil(min_distance))
    offsets = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
               if dy * dy + dx * dx < min_distance * min_distance]
    kept = 0
    for index in ids[order]:
        y, x = divmod(int(index), w)
        if blocked[y, x]:
            continue
        out[y, x] = True
        kept += 1
        for dy, dx in offsets:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
        if kept >= count:
            break
    return out
