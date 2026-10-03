#!/usr/bin/env python3
"""Run the one frozen H27-SRCOH buffered spatial screen; never upload."""
from __future__ import annotations

import gc
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
import torch
from scipy.ndimage import binary_dilation, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import (ART, EVIDENCE, PREP, RAW, SEED, read_json, sha256_file,
                           utcnow, verify_grid, verify_pinned, write_json)
from gems26.emission import BUDGET_FRACTION, percentile_rank, poisson_emit, ridge_nms
from gems26.h27_protocol import verify_h27_freeze
from gems26.heads import FeatureStore, fit_head
from gems26.holdout import NAMES, paired_evaluation, promotion_gate, quadrant_folds, train_sample
from gems26.submission import validate_submission


def _prediction_in_chunks(store, head, mean, scale, ids, score, shape,
                          *, use_srcoh: bool) -> np.ndarray:
    out = np.zeros(shape, dtype=np.float32)
    with torch.no_grad():
        for start in range(0, len(ids), 65536):
            batch_ids = ids[start:start + 65536]
            base = store.get(batch_ids, ssl=False)
            if base.shape[1] != 51:
                raise ValueError("The fixed raw control must contain exactly 51 dimensions")
            extra = (np.asarray(score).ravel()[batch_ids, None].astype(np.float32, copy=False)
                     if use_srcoh else np.zeros((len(batch_ids), 1), dtype=np.float32))
            features = np.concatenate((base, extra), axis=1)
            if features.shape[1] != 52:
                raise ValueError("Matched raw/H27 heads must both contain 52 dimensions")
            normalized = np.clip((features - mean) / scale, -12, 12)
            out.ravel()[batch_ids] = torch.sigmoid(head(torch.from_numpy(normalized))).numpy()
    return out


def _load_emitted_reference(path: Path, fp: np.ndarray, *, name: str,
                            expected_sha256: str | None = None) -> tuple[np.ndarray, dict]:
    if expected_sha256 and sha256_file(path) != expected_sha256:
        raise ValueError(f"Pinned {name} raster checksum mismatch")
    with rasterio.open(path) as source:
        verify_grid(source)
        if source.count != 1 or source.dtypes[0] != "float32":
            raise ValueError(f"{name} must be a single-band float32 grid")
        raw = source.read(1)
    if (not np.isfinite(raw[fp]).all() or not np.isin(raw[fp], [0, 1]).all()
            or not np.isnan(raw[~fp]).all()):
        raise ValueError(f"{name} is not an exact binary, NaN-masked emission raster")
    return (raw == 1) & fp, {"sha256": sha256_file(path), "positive_pixels": int(np.count_nonzero(raw[fp] == 1)),
                            "path": str(path.relative_to(ROOT))}


def main() -> None:
    output_path = EVIDENCE / "h27_srcoh_holdout.json"
    if output_path.exists():
        raise SystemExit("An H27-SRCOH holdout receipt already exists; do not refit or retune")

    feature_path = EVIDENCE / "h27_srcoh_feature.json"
    feature = read_json(feature_path)
    if (feature.get("labels_opened") is not False or
            feature.get("template_opened") is not False or
            feature.get("preregistration_path") != "knowledge/hypothesis-slate-20261002-v2.md"):
        raise ValueError("A completed preregistered label-free H27 feature is required")
    frozen = verify_h27_freeze(
        ROOT,
        required_ancestor=feature.get("code_freeze_commit"),
        expected_manifest_sha256=feature.get("code_freeze_manifest_sha256"),
    )
    if feature.get("source_sha256") != frozen["code_sha256"]:
        raise ValueError("H27 source hashes changed after feature construction")
    if feature.get("preregistration_sha256") != frozen["manifest"]["preregistration_sha256"]:
        raise ValueError("H27 feature protocol hash differs from the committed slate")
    if feature.get("input_manifest_sha256") != frozen["manifest"]["input_manifest_sha256"]:
        raise ValueError("Pinned input manifest changed after feature construction")
    for relative, evidence_key in (
        ("evidence/preparation.json", "preparation_receipt_sha256"),
        ("evidence/pretraining.json", "pretraining_receipt_sha256"),
        ("evidence/representation.json", "representation_receipt_sha256"),
        ("evidence/anomaly.json", "anomaly_receipt_sha256"),
    ):
        if sha256_file(ROOT / relative) != feature.get(evidence_key):
            raise ValueError(f"A label-free prerequisite receipt changed: {relative}")
    if feature.get("completed_utc", "") < read_json(EVIDENCE / "anomaly.json").get("completed_utc", ""):
        raise ValueError("H27 feature must follow completed label-free anomaly generation")

    score_path = ART / "h27_srcoh_score.npy"
    support_path = ART / "h27_srcoh_support.npy"
    if (sha256_file(score_path) != feature.get("score_sha256") or
            sha256_file(support_path) != feature.get("support_sha256")):
        raise ValueError("H27 feature bytes differ from the pre-label receipt")
    score = np.load(score_path, mmap_mode="r")
    support = np.load(support_path)
    footprint = np.load(PREP / "footprint.npy")
    if score.shape != footprint.shape or support.shape != footprint.shape:
        raise ValueError("H27 score/support differ from the fixed feature grid")
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any() or (score[~support] != 0).any():
        raise ValueError("H27 score is not finite, bounded and zero outside its frozen support")
    if sha256_file(PREP / "values.npy") != feature["prepared_values_sha256"]:
        raise ValueError("Prepared feature values changed after H27 construction")
    if sha256_file(PREP / "observed.npy") != feature["prepared_observed_sha256"]:
        raise ValueError("Prepared observation masks changed after H27 construction")
    if sha256_file(PREP / "footprint.npy") != feature["footprint_sha256"]:
        raise ValueError("Prepared footprint changed after H27 construction")

    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)

    # This is the first label-pixel access in the frozen H27 run. All inputs,
    # transforms, receipt hashes, and code/protocol checks above are label-free.
    first_label_access_utc = utcnow()
    labels_path = RAW / "labels.tif"
    label_pin = verify_pinned(labels_path)
    with rasterio.open(labels_path) as source:
        verify_grid(source)
        raw_labels = source.read(1)
    if not np.isin(raw_labels[footprint], [0, 1]).all():
        raise ValueError("Known targets are not finite binary values on the feature footprint")
    labels = (raw_labels == 1) & footprint
    del raw_labels
    folds = quadrant_folds(footprint)
    components, component_count = label(labels, structure=np.ones((3, 3), dtype=np.uint8))

    verify_pinned(RAW / "lidar_scarp_features_u8.tif")
    with rasterio.open(RAW / "lidar_scarp_features_u8.tif") as source:
        verify_grid(source)
        lidar = source.read()
    if lidar.shape[0] != 12:
        raise ValueError("The fixed owner-mirror terrain feature schema is not 12 bands")
    store = FeatureStore(lidar)

    template_path = RAW / "sample_submission.tif"
    template_pin = verify_pinned(template_path)
    h25_path = RAW / "h25_best.tif"
    h25_pin = verify_pinned(h25_path)
    h25_format = validate_submission(h25_path, template_path, footprint)
    if not h25_format["format_pass"]:
        raise ValueError("The pinned historical H25 comparator fails local raster-grid checks")
    with rasterio.open(h25_path) as source:
        verify_grid(source)
        h25_raw = source.read(1)
    if not np.isfinite(h25_raw[footprint]).all() or not np.isin(h25_raw[footprint], [0, 1]).all():
        raise ValueError("Pinned H25 comparator is not binary on the valid footprint")
    h25 = (h25_raw == 1) & footprint
    del h25_raw

    xedge_receipt = read_json(EVIDENCE / "xedge_holdout.json")
    xedge_artifact = xedge_receipt.get("oof_artifact", {})
    if not xedge_artifact.get("format_pass"):
        raise ValueError("A locally validated fixed H26-XEDGE OOF comparator is required")
    xedge_path = (ROOT / xedge_artifact["path"]).resolve()
    try:
        xedge_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("XEDGE comparator path must be inside the frozen project") from exc
    xedge_oof, xedge_pin = _load_emitted_reference(
        xedge_path, footprint, name="H26-XEDGE OOF",
        expected_sha256=xedge_artifact.get("sha256"),
    )
    if xedge_pin["positive_pixels"] != xedge_artifact.get("positive_pixels"):
        raise ValueError("H26-XEDGE OOF emitted-cell count differs from its receipt")

    arms = {
        "h25_reference": h25,
        "xedge_oof": xedge_oof,
        "raw_head": np.zeros(footprint.shape, dtype=bool),
        "srcoh_head": np.zeros(footprint.shape, dtype=bool),
    }
    fold_records = []
    t0 = time.monotonic()
    for fold in range(4):
        print("FITTING FROZEN H27 FOLD", NAMES[fold], flush=True)
        ids, y, split_meta = train_sample(labels, footprint, folds, components,
                                          fold, SEED + fold)
        test = folds == fold
        inference_support = binary_dilation(
            test, iterations=16, structure=np.ones((3, 3), dtype=bool)
        ) & footprint
        inference_ids = np.flatnonzero(inference_support)

        base_x = store.get(ids, ssl=False)
        if base_x.shape[1] != 51:
            raise ValueError("The frozen raw feature stack must contain 51 dimensions")
        raw_x = np.zeros((len(ids), 52), dtype=np.float32)
        raw_x[:, :51] = base_x
        srcoh_x = raw_x.copy()
        srcoh_x[:, 51] = np.asarray(score).ravel()[ids].astype(np.float32, copy=False)
        del base_x

        raw_head, raw_mean, raw_scale, raw_fit = fit_head(
            raw_x, y, SEED + fold, epochs=16
        )
        del raw_x
        srcoh_head, srcoh_mean, srcoh_scale, srcoh_fit = fit_head(
            srcoh_x, y, SEED + fold, epochs=16
        )
        del srcoh_x
        if (raw_fit["dimensions"] != 52 or srcoh_fit["dimensions"] != 52 or
                raw_fit["head_parameters"] != srcoh_fit["head_parameters"] or
                raw_fit["seed"] != srcoh_fit["seed"] or raw_fit["epochs"] != srcoh_fit["epochs"]):
            raise ValueError("H27 and constant-zero raw control are not dimension/seed/epoch matched")

        raw_prediction = _prediction_in_chunks(
            store, raw_head, raw_mean, raw_scale, inference_ids, score,
            footprint.shape, use_srcoh=False,
        )
        srcoh_prediction = _prediction_in_chunks(
            store, srcoh_head, srcoh_mean, srcoh_scale, inference_ids, score,
            footprint.shape, use_srcoh=True,
        )
        ranked = {
            "raw_head": percentile_rank(raw_prediction, inference_support),
            "srcoh_head": percentile_rank(srcoh_prediction, inference_support),
        }
        budget = int(round(BUDGET_FRACTION * int(test.sum())))
        emission = {}
        for tag, field in ranked.items():
            eligible = ridge_nms(field, inference_support) & test
            emitted = poisson_emit(field, eligible, budget, min_distance=1.5)
            arms[tag] |= emitted
            emission[tag] = {
                "fixed_budget": budget,
                "eligible_ridges": int(eligible.sum()),
                "emitted_pixels": int(emitted.sum()),
                "support_pixels_in_inference_halo": int(inference_support.sum()),
            }
        fold_records.append({
            "split": split_meta,
            "heads": {"raw_head": raw_fit, "srcoh_head": srcoh_fit},
            "emission": emission,
        })
        del raw_head, srcoh_head, raw_prediction, srcoh_prediction, ranked
        del ids, y, inference_ids, inference_support
        gc.collect()

    for tag, arm in arms.items():
        np.save(ART / f"h27_srcoh_emitted_{tag}.npy", arm, allow_pickle=False)

    print("EVALUATING PRESPECIFIED DRAW OFFSETS 120..149", flush=True)
    selection = paired_evaluation(arms, labels, footprint, folds, components,
                                  draws=30, seed_offset=120)
    print("EVALUATING PRESPECIFIED REPEAT OFFSETS 150..179", flush=True)
    confirmation = paired_evaluation(arms, labels, footprint, folds, components,
                                     draws=30, seed_offset=150)
    gate = promotion_gate(
        selection, confirmation, primary="srcoh_head",
        comparators=("raw_head", "xedge_oof", "h25_reference"),
    )
    decision = ("ELIGIBLE_FOR_EXTERNAL_CONFIRMATION_ONLY" if gate["holdout_pass"]
                else "BLOCKED_DO_NOT_SUBMIT")
    gate.update({
        "decision": decision,
        "weekly_slot_spent": False,
        "external_confirmation_required_even_if_screen_passes": True,
        "warning": "Reused public catalogue and spatial quadrants are a sensitivity screen, not independent hidden-fault truth or an official score.",
    })

    write_json(EVIDENCE / "h27_srcoh_selection.json", selection)
    write_json(EVIDENCE / "h27_srcoh_confirmation.json", confirmation)
    output_receipt = {
        "run": "H27-SRCOH-v1",
        "preregistration_path": feature["preregistration_path"],
        "preregistration_sha256": feature["preregistration_sha256"],
        "slate_commit": feature["slate_commit"],
        "code_freeze_commit": feature["code_freeze_commit"],
        "code_freeze_manifest_sha256": feature["code_freeze_manifest_sha256"],
        "feature_receipt_sha256": sha256_file(feature_path),
        "input_manifest_sha256": feature["input_manifest_sha256"],
        "label_file_pin": label_pin,
        "sample_template_pin": template_pin,
        "first_label_pixel_access_utc": first_label_access_utc,
        "completed_utc": utcnow(),
        "label_free_feature_preceded_label_access": feature["completed_utc"] <= first_label_access_utc,
        "labels_opened_only_after_pretraining_inference_anomaly_and_srcoh": True,
        "encoder_and_decoder_fine_tuned": False,
        "encoder_used_in_final_head": False,
        "raw_control_constant_zero_52nd_feature": True,
        "candidate_and_control_dimensions": 52,
        "folds": fold_records,
        "known_positive_pixels": int(labels.sum()),
        "connected_label_components": int(component_count),
        "srcoh_support_pixels": int(support.sum()),
        "emission_fraction": BUDGET_FRACTION,
        "minimum_spacing_pixels": 1.5,
        "selection_seed_offsets": [120, 149],
        "confirmation_seed_offsets": [150, 179],
        "selection_summary": {key: selection[key] for key in ("dense", "sparse")},
        "confirmation_summary": {key: confirmation[key] for key in ("dense", "sparse")},
        "comparators": {
            "h25_reference": {**h25_format, "as_emitted": True,
                               "catalogue_masking_leakage_retained": True,
                               "input_pin": h25_pin, "positive_pixels": int(h25.sum())},
            "xedge_oof": {**xedge_artifact, "as_emitted": True,
                          "receipt_sha256": sha256_file(EVIDENCE / "xedge_holdout.json"),
                          "positive_pixels": xedge_pin["positive_pixels"]},
            "raw_head": {"same_run": True, "constant_zero_52nd_feature": True},
        },
        "emitted_arm_sha256": {
            tag: sha256_file(ART / f"h27_srcoh_emitted_{tag}.npy") for tag in arms
        },
        "gate": gate,
        "decision": decision,
        "hidden_fault_validation": False,
        "weekly_slot_spent": False,
        "upload_performed": False,
        "leaderboard_accessed": False,
        "scope": "Four spatial quadrants and two fixed seed-offset catalogue-thinning groups; reused labels are not independent unknown-fault validation.",
        "limitations": [
            "The three strain-channel names and units are owner-mirror descriptions, not organizer-authenticated source metadata.",
            "The screen tests correlation with the known public catalogue, not discovery of hidden faults, vents, heat, fluid, permeability or a geothermal resource.",
            "The historical H25 comparator retains its previously documented all-catalogue-mask leakage; the H26-XEDGE comparator is its fixed OOF as-emitted raster.",
            "Two seed-offset groups reuse the same components and quadrants; their draws are not independent geological discoveries.",
            "No DrivenData site access, leaderboard read, TIF publication or upload was performed by this screen.",
        ],
    }
    write_json(output_path, output_receipt)
    print("H27-SRCOH SCREEN DECISION", decision, flush=True)
    for tag in arms:
        print(tag, "dense", confirmation["dense"][tag]["pooled"]["dti"],
              "sparse", confirmation["sparse"][tag]["mean_pooled_dti"], flush=True)
    print("weekly slot spent: false; hidden-fault validation: false", flush=True)


if __name__ == "__main__":
    main()
