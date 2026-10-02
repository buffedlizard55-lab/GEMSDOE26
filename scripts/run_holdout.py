#!/usr/bin/env python3
"""One frozen confirmatory run; outputs are research-only unless EVERY release gate passes."""
from __future__ import annotations

import argparse
import base64
import gc
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
import torch
from scipy.ndimage import binary_dilation, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import ART, EVIDENCE, PREP, RAW, SEED, read_json, sha256_file, utcnow, verify_grid, verify_pinned, write_json
from gems26.emission import BUDGET_FRACTION, percentile_rank, poisson_emit, ridge_nms
from gems26.heads import FeatureStore, fit_head, predict_head
from gems26.holdout import NAMES, paired_evaluation, promotion_gate, quadrant_folds, train_sample
from gems26.ssl import load_frozen, state_hash
from gems26.submission import prediction_digest, validate_submission, write_submission
from gems26.audit import audit_targets, error_diagnostics


def prerequisites() -> tuple[dict, dict, dict]:
    pre = read_json(EVIDENCE / "pretraining.json")
    rep = read_json(EVIDENCE / "representation.json")
    ano = read_json(EVIDENCE / "anomaly.json")
    if not pre["coverage_pass"] or not rep["coverage_pass"] or any(r["labels_opened"] for r in (pre, rep, ano)):
        raise ValueError("Complete label-free pretraining/inference/anomaly must precede labels")
    if pre["args"]["epochs"] != 6 or pre["args"]["tile"] != 64 or pre["mask_ratio"] != .75:
        raise ValueError("Non-preregistered pretraining cannot receive a confirmatory release")
    if pre["preregistration_sha256"] != sha256_file(ROOT / "knowledge/preregistration.md"):
        raise ValueError("Preregistered protocol changed since training")
    for path, expected in ((ART / "encoder.pt", pre["checkpoint_sha256"]),
                           (ART / "latent.npy", rep["latent_sha256"]),
                           (ART / "errors.npy", rep["errors_sha256"]),
                           (ART / "anomaly.npy", ano["anomaly_sha256"])):
        if sha256_file(path) != expected:
            raise ValueError(f"Stage integrity failed: {path.name}")
    if not (pre["completed_utc"] <= rep["completed_utc"] <= ano["completed_utc"]):
        raise ValueError("Stage order is inconsistent")
    return pre, rep, ano


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--resume-receipts", action="store_true", help="Verify existing completed result without refitting/tuning")
    args = parser.parse_args()
    if args.threads < 1:
        raise ValueError("Positive threads required")
    if (EVIDENCE / "holdout.json").exists():
        if not args.resume_receipts:
            raise SystemExit("This frozen run already exists. Do not retune outer folds; inspect receipts. Use --resume-receipts to verify files only.")
        saved = read_json(EVIDENCE / "holdout.json")
        for row in saved["artifacts"]:
            if sha256_file(ROOT / row["path"]) != row["sha256"]:
                raise ValueError("Saved artifact changed")
        prerequisites()
        print("Existing frozen run verified; no refit", flush=True)
        return
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    pre, rep, ano = prerequisites()
    frozen, checkpoint = load_frozen(ART / "encoder.pt")
    before_hash = state_hash(frozen)
    if any(p.requires_grad for p in frozen.parameters()):
        raise ValueError("Encoder must be frozen")
    fp = np.load(PREP / "footprint.npy")
    if not np.array_equal(np.load(ART / "ssl_visited.npy"), fp) or not np.array_equal(np.load(ART / "ssl_masked.npy"), fp):
        raise ValueError("Recorded exposure arrays do not cover the entire footprint")
    # THIS IS THE FIRST RASTER LABEL ACCESS. All representation stages are complete.
    first_label_access = utcnow()
    verify_pinned(RAW / "labels.tif")
    with rasterio.open(RAW / "labels.tif") as d:
        verify_grid(d)
        raw_labels = d.read(1)
    if not np.isin(raw_labels[fp], [0, 1]).all():
        raise ValueError("Labels invalid inside footprint")
    labels = (raw_labels == 1) & fp
    del raw_labels
    folds = quadrant_folds(fp)
    components, n_components = label(labels, structure=np.ones((3, 3), int))
    with rasterio.open(RAW / "lidar_scarp_features_u8.tif") as d:
        verify_grid(d)
        lidar = d.read()
    if lidar.shape[0] != 12:
        raise ValueError("Unexpected terrain descriptor schema")
    store = FeatureStore(lidar)
    anomaly = np.load(ART / "anomaly.npy", mmap_mode="r")
    arms = {tag: np.zeros(fp.shape, bool) for tag in ("raw_head", "ssl_head", "ssl_fusion", "anomaly_only")}
    historical = {}
    for tag, filename in (("h25_reference", "h25_best.tif"), ("h19_parent", "h19_parent.tif")):
        verify_pinned(RAW / filename)
        receipt = validate_submission(RAW / filename, RAW / "sample_submission.tif", fp)
        if not receipt["format_pass"]:
            raise ValueError("Pinned historical comparator is invalid")
        with rasterio.open(RAW / filename) as d:
            historical[tag] = (d.read(1) > 0) & fp
    t0 = time.monotonic()
    fold_records = []
    for fold in range(4):
        print("FITTING OUTER FOLD", NAMES[fold], flush=True)
        ids, y, split_meta = train_sample(labels, fp, folds, components, fold, SEED + fold)
        test = folds == fold
        support = binary_dilation(test, iterations=16, structure=np.ones((3, 3), bool)) & fp
        inference_ids = np.flatnonzero(support)
        record = {"split": split_meta, "heads": {}, "emission": {}}
        scores = {}
        for tag, use_ssl in (("raw_head", False), ("ssl_head", True)):
            x = store.get(ids, use_ssl)
            head, mean, scale, fit = fit_head(x, y, SEED + fold, epochs=16)
            del x
            scores[tag] = predict_head(store, head, mean, scale, inference_ids, use_ssl, fp.shape)
            record["heads"][tag] = fit
            torch.save({"head_state": head.state_dict(), "mean": torch.from_numpy(mean),
                        "scale": torch.from_numpy(scale), "ssl": use_ssl, "seed": SEED + fold}, ART / f"head-{fold}-{tag}.pt")
            del head
        raw_rank = percentile_rank(scores["raw_head"], support)
        ssl_rank = percentile_rank(scores["ssl_head"], support)
        error_rank = percentile_rank(anomaly, support)
        scores = {"raw_head": raw_rank, "ssl_head": ssl_rank,
                  "ssl_fusion": .9 * ssl_rank + .1 * error_rank, "anomaly_only": error_rank}
        budget = int(round(BUDGET_FRACTION * test.sum()))
        for tag, score in scores.items():
            eligible = ridge_nms(score, support) & test
            emitted = poisson_emit(score, eligible, budget, 1.5)
            arms[tag] |= emitted
            record["emission"][tag] = {"budget": budget, "eligible_ridges": int(eligible.sum()), "emitted_pixels": int(emitted.sum())}
        fold_records.append(record)
        write_json(ART / "fold_progress.json", {"completed_outer_folds": fold_records})
        del scores, raw_rank, ssl_rank, error_rank, ids, y, support, inference_ids
        gc.collect()
        if state_hash(frozen) != before_hash:
            raise ValueError("Frozen encoder changed during supervised fitting")
    all_arms = {**arms, **historical}
    for tag, a in all_arms.items():
        np.save(ART / f"emitted-{tag}.npy", a)
    print("EVALUATING SELECTION DRAWS 0..29", flush=True)
    selection = paired_evaluation(all_arms, labels, fp, folds, components, draws=30, seed_offset=0)
    print("EVALUATING CONFIRMATION DRAWS 30..59", flush=True)
    confirmation = paired_evaluation(all_arms, labels, fp, folds, components, draws=30, seed_offset=30)
    gate = promotion_gate(selection, confirmation)
    write_json(EVIDENCE / "holdout_selection.json", selection)
    write_json(EVIDENCE / "holdout_confirmation.json", confirmation)
    print("AUDITING LABELS FIRST, THEN EXACT EMITTED PREDICTIONS", flush=True)
    try:
        nuisance = audit_targets(labels, {"h25_reference": historical["h25_reference"],
                                         "ssl_fusion": arms["ssl_fusion"], "anomaly_only": arms["anomaly_only"]}, fp, folds)
    except (ValueError, FileNotFoundError) as e:
        nuisance = {"complete": False, "error": str(e), "relative_association_not_worse_by_over_0.01": False}
    write_json(EVIDENCE / "accessibility_audit.json", nuisance)
    error_receipt = error_diagnostics(anomaly, np.load(ART / "errors.npy", mmap_mode="r"),
                                      np.load(PREP / "observed.npy", mmap_mode="r"), fp, labels)
    write_json(EVIDENCE / "error_diagnostics.json", error_receipt)
    downloads = ROOT / "docs/downloads"
    artifact_rows = []
    primary_file = None
    for tag in ("ssl_fusion", "anomaly_only"):
        path, fmt = write_submission(arms[tag], fp, RAW / "sample_submission.tif", downloads,
                                     "ssl-v1" if tag == "ssl_fusion" else "label-free-error-v1")
        fmt["path"] = str(path.relative_to(ROOT))
        write_json(downloads / f"checks-{path.stem}.json", fmt)
        artifact_rows.append({"method": tag, **fmt})
        if tag == "ssl_fusion":
            primary_file = path
    reference_path = downloads / "gems26-reference-h25-1-989f59505db1-nan.tif"
    shutil.copyfile(RAW / "h25_best.tif", reference_path)
    reference_fmt = validate_submission(reference_path, RAW / "sample_submission.tif", fp)
    reference_fmt["path"] = str(reference_path.relative_to(ROOT))
    reference_fmt["method"] = "historical_reference_identical_bytes_do_not_resubmit"
    artifact_rows.append(reference_fmt)
    gate["rules"]["exact_file_format_pass"] = all(r["format_pass"] for r in artifact_rows)
    gate["rules"]["nuisance_inputs_complete"] = bool(nuisance.get("complete"))
    gate["rules"]["labels_audited_first"] = bool(nuisance.get("labels_audited_first"))
    gate["rules"]["relative_accessibility_not_worse_by_over_0.01"] = bool(nuisance.get("relative_association_not_worse_by_over_0.01"))
    gate["rules"]["encoder_unchanged"] = state_hash(frozen) == before_hash
    gate["release_pass"] = bool(all(gate["rules"].values()))
    gate["decision"] = "LOCAL_PROXY_PASS_NO_LIVE_SCORE" if gate["release_pass"] else "BLOCKED_DO_NOT_SUBMIT"
    # Browser export rebuilds exactly these predictions, NOT a new trained candidate.
    browser_model = {"width": fp.shape[1], "height": fp.shape[0], "footprint_pixels": int(fp.sum()),
                     "footprint_runs_base64": base64.b64encode((RAW / "footprint.bin").read_bytes()).decode(),
                     "positive_indices_base64": base64.b64encode(np.flatnonzero(arms["ssl_fusion"]).astype("<u4").tobytes()).decode(),
                     "positive_pixels": int(arms["ssl_fusion"].sum()),
                     "prediction_sha256": prediction_digest(arms["ssl_fusion"], fp),
                     "method": "ssl-v1", "release_decision": gate["decision"]}
    write_json(ROOT / "docs/data/browser-model.json", browser_model)
    note = f"GEMS26 SSL-v1 | full-raster masked pretrain; frozen head; 90/10 error fusion; {int(arms['ssl_fusion'].sum())} dots | unscored | {gate['decision']}"
    (downloads / f"note-{primary_file.stem}.txt").write_text(note + "\n")
    with rasterio.open(RAW / "sample_submission.tif") as d:
        sample = d.read(1)
    input_irregularities = {"template_positive_pixels": int((sample[fp] > 0).sum()),
                            "template_predictions_equal_known_labels": bool(np.array_equal(sample[fp] > 0, labels[fp])),
                            "warning": "Mirror example is not an all-zero sample; organizer provenance is unverified. No sample VALUES used in SSL."}
    summary = {"run": "H26-SSL-v1", "started_label_access_utc": first_label_access,
               "completed_utc": utcnow(), "elapsed_supervised_validation_seconds": round(time.monotonic() - t0, 2),
               "representation_completed_utc": rep["completed_utc"], "anomaly_completed_utc": ano["completed_utc"],
               "label_access_after_ssl_and_anomaly": first_label_access >= ano["completed_utc"],
               "encoder_state_before": before_hash, "encoder_state_after": state_hash(frozen),
               "labels_positive_pixels": int(labels.sum()), "label_components": int(n_components),
               "folds": fold_records, "emission_fraction": BUDGET_FRACTION,
               "primary_mixture": "0.9 percentile-rank frozen SSL head + 0.1 percentile-rank label-free coherent masked error",
               "selection_summary": {k: selection[k] for k in ("dense", "sparse")},
               "confirmation_summary": {k: confirmation[k] for k in ("dense", "sparse")},
               "gate": gate, "artifacts": artifact_rows, "submission_note": note,
               "input_irregularities": input_irregularities,
               "limits": ["Transductive full-raster SSL", "Known-fault spatial proxy only", "Component-thinned sensitivity is not independent new-fault truth",
                          "Historical H25 used an all-catalogue exclusion mask; no leakage-free fresh H25 detector available",
                          "No live competition score, no uploaded file, no calibrated geothermal discovery claim"],
               "preregistration_sha256": pre["preregistration_sha256"]}
    write_json(EVIDENCE / "holdout.json", summary)
    print("FINAL RELEASE DECISION", gate["decision"], flush=True)
    for tag in all_arms:
        print(tag, "dense", confirmation["dense"][tag]["pooled"]["dti"],
              "sparse", confirmation["sparse"][tag]["mean_pooled_dti"], flush=True)


if __name__ == "__main__":
    main()
