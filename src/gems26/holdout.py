"""Spatial splits and exact paired sparse simulation; no hidden-fault labels."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label

from .common import SEED
from .metric import binary_coordinate_components, pooled

NAMES = ["NW", "NE", "SW", "SE"]


def _binary_grid(a: np.ndarray, name: str) -> np.ndarray:
    values = np.asarray(a)
    if values.ndim != 2 or values.dtype.kind not in "biuf" or not np.isin(values, [0, 1]).all():
        raise ValueError("Finite 2D binary grid required: " + name)
    return values.astype(bool, copy=False)


def quadrant_folds(fp: np.ndarray) -> np.ndarray:
    fp = _binary_grid(fp, "footprint")
    if not fp.any():
        raise ValueError("Nonempty 2D footprint required")
    yy, xx = np.nonzero(fp)
    ymid, xmid = int(np.median(yy)), int(np.median(xx))
    gy, gx = np.ogrid[:fp.shape[0], :fp.shape[1]]
    folds = np.full(fp.shape, -1, dtype=np.int8)
    for f in range(4):
        ym = gy < ymid if f < 2 else gy >= ymid
        xm = gx < xmid if f % 2 == 0 else gx >= xmid
        folds[fp & ym & xm] = f
    if any(not (folds == f).any() for f in range(4)):
        raise ValueError("Empty outer quadrant; cannot claim four-region validation")
    return folds


def train_sample(labels: np.ndarray, fp: np.ndarray, folds: np.ndarray,
                 components: np.ndarray, fold: int, seed: int,
                 max_positive: int = 24000, max_negative: int = 120000):
    labels, fp = _binary_grid(labels, "labels"), _binary_grid(fp, "footprint")
    if fold not in range(4) or not isinstance(max_positive, (int, np.integer)) or not isinstance(max_negative, (int, np.integer)) or min(max_positive, max_negative) <= 0:
        raise ValueError("One of four folds and positive integer sampling budgets required")
    if not (labels.shape == fp.shape == folds.shape == components.shape):
        raise ValueError("Aligned label/footprint/fold/component grids required")
    test = folds == fold
    collar_distance = distance_transform_edt(~test)
    touching = np.unique(components[test & labels])
    touching = touching[touching > 0]
    excluded_component = np.isin(components, touching) & labels
    train = fp & ~test & (collar_distance > 15)
    # Whole-component grouping exclusion from the training example pool.
    train &= ~binary_dilation(excluded_component, iterations=4, structure=np.ones((3, 3), bool))
    positive = labels & train
    known_distance = distance_transform_edt(~positive)
    negative = train & ~labels & (known_distance > 4)
    pos = np.flatnonzero(positive)
    neg = np.flatnonzero(negative)
    if not len(pos) or not len(neg):
        raise ValueError("Spatial training fold lacks two classes")
    rng = np.random.default_rng(seed)
    if len(pos) > max_positive:
        pos = rng.choice(pos, max_positive, replace=False)
    if len(neg) > max_negative:
        neg = rng.choice(neg, max_negative, replace=False)
    ids = np.concatenate((pos, neg))
    y = np.concatenate((np.ones(len(pos)), np.zeros(len(neg)))).astype(np.float32)
    if test.ravel()[ids].any() or np.isin(components.ravel()[pos], touching).any():
        raise ValueError("Training overlap/whole-component leakage")
    return ids, y, {
        "fold": NAMES[fold], "training_positive": len(pos), "training_unlabeled_as_negative": len(neg),
        "excluded_whole_components": len(touching), "minimum_train_test_gap_pixels": float(collar_distance.ravel()[ids].min()),
        "train_test_pixel_overlap": 0, "train_positive_test_component_overlap": 0,
        "positive_accuracy_and_unlabeled_negative_assumption": "Not independently identified; no PU calibration claim"}


def paired_evaluation(arms: dict[str, np.ndarray], labels: np.ndarray, fp: np.ndarray,
                      folds: np.ndarray, components: np.ndarray,
                      draws: int = 30, seed_offset: int = 0) -> dict:
    labels, fp = _binary_grid(labels, "labels"), _binary_grid(fp, "footprint")
    if not isinstance(draws, (int, np.integer)) or draws < 1 or not arms:
        raise ValueError("Positive integer number of sparse draws and nonempty binary arms required")
    if not (labels.shape == fp.shape == folds.shape == components.shape) or labels.ndim != 2:
        raise ValueError("Aligned 2D evaluation grids required")
    if not np.isin(labels[fp], [0, 1]).all():
        raise ValueError("Binary known truth required")
    for tag, arm in arms.items():
        if np.shape(arm) != fp.shape or not np.isin(np.asarray(arm)[fp], [0, 1]).all():
            raise ValueError("Paired evaluation requires binary finite arms: " + tag)
    dense = {tag: [] for tag in arms}
    per_draw = {tag: [] for tag in arms}
    fold_means = {tag: [] for tag in arms}
    raw_draws = []
    fold_cached = []
    for f in range(4):
        domain = fp & (folds == f)
        gc = np.argwhere(labels & domain)
        gids = components[gc[:, 0], gc[:, 1]]
        unique = np.unique(gids)
        unique = unique[unique > 0]
        pc = {tag: np.argwhere(np.asarray(a, bool) & domain) for tag, a in arms.items()}
        pg = {tag: components[p[:, 0], p[:, 1]] for tag, p in pc.items()}
        for tag in arms:
            dense[tag].append(binary_coordinate_components(pc[tag], gc))
        fold_cached.append((gc, gids, unique, pc, pg))
    for draw in range(draws):
        row = {"draw": draw + seed_offset, "folds": []}
        for f, (gc, gids, unique, pc, pg) in enumerate(fold_cached):
            rng = np.random.default_rng(SEED + 1000 * f + seed_offset + draw)
            keep = rng.choice(unique, max(1, int(round(.2 * len(unique)))), replace=False)
            g = gc[np.isin(gids, keep)]
            details = {}
            for tag in arms:
                # Non-retained components are known/masked in this explicit sparse PROXY.
                keep_p = (pg[tag] == 0) | np.isin(pg[tag], keep)
                details[tag] = binary_coordinate_components(pc[tag][keep_p], g)
            row["folds"].append({"fold": NAMES[f], "seed": SEED + 1000 * f + seed_offset + draw,
                                  "retained_components": len(keep), "available_components": len(unique),
                                  "truth_pixels": len(g), "arms": details})
        for tag in arms:
            per_draw[tag].append(pooled([r["arms"][tag] for r in row["folds"]]))
        raw_draws.append(row)
    for tag in arms:
        fold_means[tag] = [float(np.mean([r["folds"][f]["arms"][tag]["dti"] for r in raw_draws])) for f in range(4)]
    return {"scope": "Known-catalogue sensitivity simulation, NOT new-fault ground truth",
            "sparse_component_fraction": .2, "draws": draws, "seed_offset": seed_offset,
            "dense": {tag: {"pooled": pooled(rows), "folds": rows,
                              "fold_mean_dti": float(np.mean([r["dti"] for r in rows]))} for tag, rows in dense.items()},
            "sparse": {tag: {"mean_pooled_dti": float(np.mean([r["dti"] for r in rows])),
                               "pooled_dti_std_across_draws": float(np.std([r["dti"] for r in rows])),
                               "fold_mean_dti": fold_means[tag], "pooled_per_draw": rows} for tag, rows in per_draw.items()},
            "raw_draws": raw_draws,
            "dependence_warning": "Draws reuse the same geological catalogue; 30×4 is NOT 120 independent discoveries"}


def promotion_gate(selection: dict, confirmation: dict, primary: str = "ssl_fusion",
                   comparators: tuple[str, ...] = ("h25_reference", "raw_head")) -> dict:
    rules, deltas = {}, {}
    for stage, report in (("selection", selection), ("confirmation", confirmation)):
        for comp in comparators:
            sparse_delta = report["sparse"][primary]["mean_pooled_dti"] - report["sparse"][comp]["mean_pooled_dti"]
            dense_delta = report["dense"][primary]["pooled"]["dti"] - report["dense"][comp]["pooled"]["dti"]
            fold_delta = np.asarray(report["sparse"][primary]["fold_mean_dti"]) - report["sparse"][comp]["fold_mean_dti"]
            key = f"{stage}_vs_{comp}"
            deltas[key] = {"pooled_sparse_delta": float(sparse_delta), "pooled_dense_delta": float(dense_delta),
                           "sparse_fold_delta": fold_delta.tolist(), "fold_wins": int((fold_delta > 0).sum())}
            rules[key + "_sparse_margin_0.005"] = bool(sparse_delta >= .005)
            rules[key + "_dense_noninferiority_0.005"] = bool(dense_delta >= -.005)
            if stage == "confirmation":
                rules[key + "_at_least_3_of_4_fold_wins"] = bool((fold_delta > 0).sum() >= 3)
    return {"holdout_pass": bool(all(rules.values())), "rules": rules, "deltas": deltas,
            "hidden_fault_validation": False, "weekly_slot_spent": False,
            "note": "Historical file is as-emitted and catalogue-masked; matched raw head is the fresh OOF control"}
