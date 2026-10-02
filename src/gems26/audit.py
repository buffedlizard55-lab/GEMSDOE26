"""Association diagnostics, not causal identification or geological validation."""
from __future__ import annotations

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

from .common import RAW, SEED, utcnow, verify_grid, verify_pinned


def load_nuisances(fp: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    arrays, pins = [], []
    for name in ("tiger_road_distance_m.tif", "blm_closed_claim_distance_m.tif", "acquisition_block_id_100m.tif"):
        path = RAW / name
        pins.append(verify_pinned(path))
        with rasterio.open(path) as d:
            verify_grid(d)
            arrays.append(d.read(1))
    road, claim, blocks = arrays
    if (not np.isfinite(road[fp]).all() or not np.isfinite(claim[fp]).all() or
            (road[fp] < 0).any() or (claim[fp] < 0).any() or not np.isin(blocks[fp], [1, 2, 3, 4]).all()):
        raise ValueError("Incomplete/invalid requested nuisance families")
    ids = np.flatnonzero(fp)
    fields = [np.log1p(np.minimum(road.ravel()[ids], 100000)),
              np.log1p(np.minimum(claim.ravel()[ids], 100000))]
    fields.extend((blocks.ravel()[ids] == i).astype(np.float32) for i in range(1, 5))
    x = np.column_stack(fields).astype(np.float32)
    return x, ids, {"sources": pins, "features": ["log1p_road_m", "log1p_closed_claim_m"] + [f"derived_block_{i}" for i in range(1, 5)],
                    "acquisition_geometry": "Derived from official figure, NOT official-coordinate polygons",
                    "source_integrity_only": True}


def _balanced(ids: np.ndarray, target: np.ndarray, rng, cap: int) -> np.ndarray:
    pos = ids[target[ids]]
    neg = ids[~target[ids]]
    n = min(len(pos), len(neg), cap)
    if n < 50:
        raise ValueError("Insufficient positives/negatives for nuisance diagnostic")
    return np.concatenate((rng.choice(pos, n, replace=False), rng.choice(neg, n, replace=False)))


def audit_targets(labels: np.ndarray, predictions: dict[str, np.ndarray], fp: np.ndarray,
                  folds: np.ndarray) -> dict:
    x, ids, meta = load_nuisances(fp)
    fold_fp = folds.ravel()[ids]
    # Python dict preserves this mandatory audit order.
    targets = {"labels": labels, **predictions}
    results, events = {}, []
    with threadpool_limits(limits=2):
        for number, (tag, arr) in enumerate(targets.items()):
            events.append({"target": tag, "started_utc": utcnow()})
            y = np.asarray(arr, bool).ravel()[ids]
            aucs = []
            for fold in range(4):
                rng = np.random.default_rng(SEED + 20000 + 100 * number + fold)
                train = _balanced(np.flatnonzero(fold_fp != fold), y, rng, 20000)
                test = _balanced(np.flatnonzero(fold_fp == fold), y, rng, 5000)
                clf = HistGradientBoostingClassifier(max_iter=60, max_leaf_nodes=7, learning_rate=.08,
                                                    l2_regularization=10, early_stopping=False, random_state=SEED + fold)
                clf.fit(x[train], y[train])
                aucs.append(float(roc_auc_score(y[test], clf.predict_proba(x[test])[:, 1])))
            results[tag] = {"mean_fold_auc": float(np.mean(aucs)), "fold_auc": aucs,
                            "meaning": "Ability of road/closed-claim/derived-block features to identify this raster; NOT fault accuracy"}
            events[-1]["completed_utc"] = utcnow()
    reference = results["h25_reference"]["mean_fold_auc"]
    primary = results["ssl_fusion"]["mean_fold_auc"]
    relative = abs(primary - .5) <= abs(reference - .5) + .01
    return {"complete": True, "labels_audited_first": events[0]["target"] == "labels", "events": events,
            "source_metadata": meta, "results": results, "relative_association_not_worse_by_over_0.01": bool(relative),
            "primary_minus_reference_auc": primary - reference,
            "caveat": "Different target-specific case-control samples; four regions, no causal inference or formal significance. Mirrors are not a fresh official-source download."}


def error_diagnostics(anomaly: np.ndarray, errors: np.ndarray, observed: np.ndarray,
                      fp: np.ndarray, labels: np.ndarray) -> dict:
    rng = np.random.default_rng(SEED + 90000)
    pos = np.flatnonzero(fp & labels)
    neg = np.flatnonzero(fp & ~labels)
    pos = rng.choice(pos, min(40000, len(pos)), replace=False)
    neg = rng.choice(neg, min(40000, len(neg)), replace=False)
    ids = np.concatenate((pos, neg))
    y = np.concatenate((np.ones(len(pos)), np.zeros(len(neg))))
    auc = float(roc_auc_score(y, anomaly.ravel()[ids]))
    with rasterio.open(RAW / "acquisition_block_id_100m.tif") as d:
        blocks = d.read(1)
    # Aggregate error already has explicit exclusion of all-unobserved pixels.
    any_observed = np.zeros(fp.shape, bool)
    mse = np.zeros(fp.shape, np.float32)
    for band in range(errors.shape[0]):
        any_observed |= observed[band] > 0
        mse += np.asarray(errors[band], np.float32)
    mse /= errors.shape[0]
    block_rows = []
    for block in range(1, 5):
        mask = fp & any_observed & (blocks == block)
        block_rows.append({"derived_block": block, "pixels": int(mask.sum()),
                           "mean_masked_mse": float(mse[mask].mean()),
                           "mean_anomaly": float(anomaly[mask].mean())})
    phase_rows = []
    yy, xx = np.ogrid[:fp.shape[0], :fp.shape[1]]
    for dy in range(4):
        for dx in range(4):
            m = fp & any_observed & (yy % 4 == dy) & (xx % 4 == dx)
            phase_rows.append({"row_mod4": dy, "col_mod4": dx, "pixels": int(m.sum()),
                               "mean_masked_mse": float(mse[m].mean())})
    means = [r["mean_masked_mse"] for r in phase_rows]
    return {"known_catalogue_anomaly_auc_diagnostic": auc,
            "fault_specificity_not_established": True,
            "missing_feature_pixels_inside_footprint": int((fp & ~any_observed).sum()),
            "block_error_means": block_rows, "patch_phase_error_means": phase_rows,
            "patch_phase_max_min_ratio": max(means) / max(min(means), 1e-12),
            "warning": "AUC uses known faults after freezing the anomaly. Error varies with geology, coverage and processing. No hidden fault labels or geothermal vent confirmations."}
