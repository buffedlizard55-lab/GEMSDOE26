#!/usr/bin/env python3
"""One frozen XEDGE screen on buffered spatial folds; never uploads to DrivenData."""
from __future__ import annotations

import gc
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
import torch
from scipy.ndimage import binary_dilation, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.audit import audit_targets
from gems26.common import (ART, EVIDENCE, PREP, RAW, SEED, read_json, sha256_file,
                           utcnow, verify_grid, verify_pinned, write_json)
from gems26.emission import BUDGET_FRACTION, percentile_rank, poisson_emit, ridge_nms
from gems26.heads import FeatureStore, fit_head
from gems26.holdout import NAMES, paired_evaluation, promotion_gate, quadrant_folds, train_sample
from gems26.submission import validate_submission, write_submission

SLATE_COMMIT = "876c0b2d71116edbf8c888f38366762aea1eb195"
PROTOCOL_FREEZE_COMMIT = "fce3f74ad58a7f37ac5cffca6bc0c1a770bb9eda"


def require_preregistered_commit() -> None:
    for commit in (SLATE_COMMIT, PROTOCOL_FREEZE_COMMIT):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                                cwd=ROOT, check=False)
        if result.returncode != 0:
            raise ValueError("Ranked slate and final XEDGE protocol must be committed before label evaluation")


def predict_in_chunks(store, head, mean, scale, ids, edge_score, shape, *, add_xedge: bool) -> np.ndarray:
    out = np.zeros(shape, dtype=np.float32)
    with torch.no_grad():
        for start in range(0, len(ids), 65536):
            batch_ids = ids[start:start + 65536]
            features = store.get(batch_ids, ssl=False)
            if add_xedge:
                extra = edge_score.ravel()[batch_ids, None].astype(np.float32, copy=False)
                features = np.concatenate((features, extra), axis=1)
            if features.shape[1] != (52 if add_xedge else 51):
                raise ValueError("Unexpected frozen raw/XEDGE feature dimensionality")
            normalized = np.clip((features - mean) / scale, -12, 12)
            out.ravel()[batch_ids] = torch.sigmoid(head(torch.from_numpy(normalized))).numpy()
    return out


def main() -> None:
    if (EVIDENCE / "xedge_holdout.json").exists():
        raise SystemExit("An XEDGE holdout receipt already exists. Preserve it; do not refit or retune these folds.")
    require_preregistered_commit()
    feature_receipt = read_json(EVIDENCE / "xedge_feature.json")
    prereg_path = ROOT / "knowledge/hypothesis-slate-20261002.md"
    if (feature_receipt.get("labels_opened") is not False or
            feature_receipt.get("template_opened") is not False or
            feature_receipt.get("preregistration_commit") != SLATE_COMMIT or
            feature_receipt.get("protocol_freeze_commit") != PROTOCOL_FREEZE_COMMIT or
            feature_receipt.get("preregistration_sha256") != sha256_file(prereg_path) or
            feature_receipt.get("completed_utc", "") < feature_receipt.get("anomaly_completed_utc", "")):
        raise ValueError("A completed, preregistered label-free XEDGE feature receipt is required")
    score_path, support_path = ART / "xedge_score.npy", ART / "xedge_support.npy"
    if (sha256_file(score_path) != feature_receipt["score_sha256"] or
            sha256_file(support_path) != feature_receipt["support_sha256"]):
        raise ValueError("XEDGE feature bytes differ from the label-free receipt")
    score = np.load(score_path, mmap_mode="r")
    edge_support = np.load(support_path)
    fp = np.load(PREP / "footprint.npy")
    if score.shape != fp.shape or edge_support.shape != fp.shape:
        raise ValueError("XEDGE and competition grids are not aligned")

    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    first_label_access = utcnow()
    verify_pinned(RAW / "labels.tif")
    with rasterio.open(RAW / "labels.tif") as source:
        verify_grid(source)
        raw_labels = source.read(1)
    if not np.isin(raw_labels[fp], [0, 1]).all():
        raise ValueError("Labels are not finite binary values on the valid footprint")
    labels = (raw_labels == 1) & fp
    del raw_labels
    folds = quadrant_folds(fp)
    components, component_count = label(labels, structure=np.ones((3, 3), dtype=np.uint8))

    verify_pinned(RAW / "lidar_scarp_features_u8.tif")
    with rasterio.open(RAW / "lidar_scarp_features_u8.tif") as source:
        verify_grid(source)
        lidar = source.read()
    if lidar.shape[0] != 12:
        raise ValueError("The fixed owner-mirror terrain feature schema is not 12 bands")
    store = FeatureStore(lidar)

    template_path = RAW / "sample_submission.tif"
    verify_pinned(template_path)
    historical_path = RAW / "h25_best.tif"
    verify_pinned(historical_path)
    historical_format = validate_submission(historical_path, template_path, fp)
    if not historical_format["format_pass"]:
        raise ValueError("Pinned H25 historical comparator fails strict format checks")
    with rasterio.open(historical_path) as source:
        h25 = (source.read(1) > 0) & fp

    arms = {name: np.zeros(fp.shape, dtype=bool)
            for name in ("raw_head", "xedge_head", "edge_only")}
    fold_records = []
    t0 = time.monotonic()
    for fold in range(4):
        print("FITTING BUFFERED XEDGE FOLD", NAMES[fold], flush=True)
        ids, y, split_meta = train_sample(labels, fp, folds, components, fold, SEED + fold)
        test = folds == fold
        inference_support = binary_dilation(test, iterations=16, structure=np.ones((3, 3), bool)) & fp
        inference_ids = np.flatnonzero(inference_support)
        record = {"split": split_meta, "heads": {}, "emission": {}}
        scores = {}

        raw_x = store.get(ids, ssl=False)
        raw_head, raw_mean, raw_scale, raw_fit = fit_head(raw_x, y, SEED + fold, epochs=16)
        del raw_x
        xedge_x = np.concatenate((store.get(ids, ssl=False),
                                  np.asarray(score).ravel()[ids, None].astype(np.float32)), axis=1)
        xedge_head, xedge_mean, xedge_scale, xedge_fit = fit_head(xedge_x, y, SEED + fold, epochs=16)
        del xedge_x
        scores["raw_head"] = predict_in_chunks(store, raw_head, raw_mean, raw_scale,
                                               inference_ids, score, fp.shape, add_xedge=False)
        scores["xedge_head"] = predict_in_chunks(store, xedge_head, xedge_mean, xedge_scale,
                                                 inference_ids, score, fp.shape, add_xedge=True)
        record["heads"] = {"raw_head": raw_fit, "xedge_head": xedge_fit}

        ranked = {tag: percentile_rank(field, inference_support) for tag, field in scores.items()}
        ranked["edge_only"] = percentile_rank(np.asarray(score), inference_support & edge_support)
        rank_support = {"raw_head": inference_support,
                        "xedge_head": inference_support,
                        "edge_only": inference_support & edge_support}
        budget = int(round(BUDGET_FRACTION * test.sum()))
        for tag, field in ranked.items():
            valid = rank_support[tag]
            eligible = ridge_nms(field, valid) & test
            emitted = poisson_emit(field, eligible, budget, min_distance=1.5)
            arms[tag] |= emitted
            record["emission"][tag] = {
                "fixed_budget": budget,
                "eligible_ridges": int(eligible.sum()),
                "emitted_pixels": int(emitted.sum()),
                "support_pixels_in_inference_halo": int(valid.sum()),
            }
        fold_records.append(record)
        del raw_head, xedge_head, scores, ranked, ids, y, inference_ids, inference_support
        gc.collect()

    # Exact historical H25 is an as-emitted, catalogue-leaky local comparator.
    all_arms = {"h25_reference": h25, **arms}
    for tag, field in all_arms.items():
        np.save(ART / f"xedge-emitted-{tag}.npy", field)
    print("EVALUATING FIXED SCREEN DRAWS 60..89", flush=True)
    selection = paired_evaluation(all_arms, labels, fp, folds, components,
                                  draws=30, seed_offset=60)
    print("EVALUATING FIXED SCREEN DRAWS 90..119", flush=True)
    confirmation = paired_evaluation(all_arms, labels, fp, folds, components,
                                     draws=30, seed_offset=90)
    comparison_gate = promotion_gate(selection, confirmation, primary="xedge_head",
                                     comparators=("h25_reference", "raw_head"))

    print("AUDITING LABEL ACCESSIBILITY FIRST, THEN XEDGE FIELDS", flush=True)
    nuisance = audit_targets(labels,
                             {"h25_reference": h25, "xedge_head": arms["xedge_head"],
                              "edge_only": arms["edge_only"]},
                             fp, folds, reference="h25_reference", primary="xedge_head")
    nuisance_pass = bool(nuisance.get("complete") and nuisance.get("labels_audited_first") and
                         nuisance.get("relative_association_not_worse_by_over_0.01"))

    # The OOF mosaic is for research/diagnostics; it is not a full-data final fit.
    note = ("GEMS26 XEDGE-v1 OOF | 300/600/1200m RTP+gravity edge persistence; "
            "four buffered folds; research-only OOF, not full-fit; unscored")
    output, format_receipt = write_submission(arms["xedge_head"], fp, template_path,
                                              ROOT / "docs/downloads", "xedge-oof-v1",
                                              date="20261002")
    format_receipt["path"] = str(output.relative_to(ROOT))
    format_receipt["method"] = "four-fold out-of-fold diagnostic; never an upload recommendation"
    format_receipt["short_comment"] = note
    write_json(ROOT / "docs/downloads" / f"checks-{output.stem}.json", format_receipt)
    (ROOT / "docs/downloads" / f"note-{output.stem}.txt").write_text(note + "\n")

    rules = dict(comparison_gate["rules"])
    rules["labels_audited_first"] = bool(nuisance.get("labels_audited_first"))
    rules["nuisance_complete_and_relative_association_pass"] = nuisance_pass
    rules["exact_oof_tiff_format_pass"] = bool(format_receipt.get("format_pass"))
    screen_pass = bool(comparison_gate["holdout_pass"] and all(rules.values()))
    decision = "ELIGIBLE_FOR_EXTERNAL_CONFIRMATION_ONLY" if screen_pass else "BLOCKED_DO_NOT_SUBMIT"
    gate = {
        **comparison_gate,
        "rules": rules,
        "holdout_pass": screen_pass,
        "decision": decision,
        "weekly_slot_spent": False,
        "external_confirmation_required_even_if_screen_passes": True,
        "warning": "This is a reused known-catalogue screen, not independent hidden-fault validation or an official leaderboard score.",
    }

    archive = read_json(EVIDENCE / "holdout.json")
    archived_raw_dense = archive["confirmation_summary"]["dense"]["raw_head"]["pooled"]["dti"]
    new_raw_dense = confirmation["dense"]["raw_head"]["pooled"]["dti"]
    raw_dense_delta = float(new_raw_dense - archived_raw_dense)
    summary = {
        "run": "H26-XEDGE-v1",
        "preregistration_slate_commit": SLATE_COMMIT,
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "protocol_sha256": feature_receipt["preregistration_sha256"],
        "feature_receipt_sha256": sha256_file(EVIDENCE / "xedge_feature.json"),
        "started_label_pixel_access_utc": first_label_access,
        "completed_utc": utcnow(),
        "label_free_feature_preceded_label_access": feature_receipt["completed_utc"] <= first_label_access,
        "labels_opened_only_after_label_free_pretraining_inference_anomaly_and_xedge": True,
        "encoder_and_decoder_fine_tuned": False,
        "folds": fold_records,
        "known_positive_pixels": int(labels.sum()),
        "connected_label_components": int(component_count),
        "edge_support_pixels": int(edge_support.sum()),
        "edge_support_fraction_of_footprint": float(edge_support.sum() / fp.sum()),
        "emission_fraction": BUDGET_FRACTION,
        "minimum_spacing_pixels": 1.5,
        "selection_seed_offsets": [60, 89],
        "confirmation_seed_offsets": [90, 119],
        "selection_summary": {k: selection[k] for k in ("dense", "sparse")},
        "confirmation_summary": {k: confirmation[k] for k in ("dense", "sparse")},
        "nuisance_audit": nuisance,
        "historical_reference_format": historical_format,
        "matched_raw_head_dense_delta_from_archived_h26_control": raw_dense_delta,
        "matched_raw_head_dense_reproduces_archived_metric_within_1e-10": abs(raw_dense_delta) <= 1e-10,
        "oof_artifact": format_receipt,
        "submission_note": note,
        "gate": gate,
        "scope": "Four buffered quadrant OOF arms scored against the already-used public catalogue and new component-thinning seeds. Not independent unknown-fault evidence.",
        "limitations": [
            "The source band names are owner-mirror metadata, not organizer-authenticated band provenance.",
            "Potential-field edges also mark lithologic contacts, intrusions, interpolation boundaries and survey seams.",
            "The edge feature is transductive over the full unlabeled feature raster.",
            "The same spatial quadrants/catalogue have appeared in earlier reviewed work; new draw seeds do not create independent labels.",
            "H25 is compared as emitted, with its inherited all-catalogue mask leakage explicitly retained.",
            "OOF TIFF is not the full-data final model and must not be submitted.",
            "No DrivenData site access, leaderboard read or upload was performed.",
        ],
    }
    write_json(EVIDENCE / "xedge_selection.json", selection)
    write_json(EVIDENCE / "xedge_confirmation.json", confirmation)
    write_json(EVIDENCE / "xedge_holdout.json", summary)
    print("XEDGE SCREEN DECISION", decision, flush=True)
    for tag in all_arms:
        print(tag, "dense", confirmation["dense"][tag]["pooled"]["dti"],
              "sparse", confirmation["sparse"][tag]["mean_pooled_dti"], flush=True)
    if not summary["matched_raw_head_dense_reproduces_archived_metric_within_1e-10"]:
        raise SystemExit("Raw-head implementation did not reproduce the archived dense control; investigate before interpretation")


if __name__ == "__main__":
    main()
