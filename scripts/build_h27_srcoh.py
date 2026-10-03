#!/usr/bin/env python3
"""Build the preregistered H27-SRCOH feature before any target access."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import (ART, EVIDENCE, PREP, footprint as pinned_footprint,
                           read_json, sha256_file, utcnow, write_json)
from gems26.h27_protocol import verify_h27_freeze
from gems26.strain import build_srcoh_feature


def require_label_free_prerequisites(freeze: dict) -> tuple[dict, dict, dict, dict]:
    prep_path = EVIDENCE / "preparation.json"
    pre_path = EVIDENCE / "pretraining.json"
    rep_path = EVIDENCE / "representation.json"
    anomaly_path = EVIDENCE / "anomaly.json"
    prep, pre, rep, anomaly = (read_json(path) for path in
                                (prep_path, pre_path, rep_path, anomaly_path))
    for name, receipt in (("preparation", prep), ("pretraining", pre),
                          ("representation", rep), ("anomaly", anomaly)):
        if receipt.get("labels_opened") is not False:
            raise ValueError(f"The {name} receipt is not label-free")
    if not prep.get("all_channels_retained"):
        raise ValueError("The complete prepared 19-channel stack is required")
    if not pre.get("coverage_pass") or pre.get("all_channels") != 19:
        raise ValueError("Complete whole-footprint, all-channel masked pretraining is required")
    if pre.get("preregistration_path") != "knowledge/hypothesis-slate-20261002-v2.md":
        raise ValueError("Pretraining must pin the committed H27 slate")
    if pre.get("preregistration_sha256") != freeze["manifest"]["preregistration_sha256"]:
        raise ValueError("Pretraining protocol hash differs from the H27 slate")
    if pre.get("input_feature_sha256") != prep.get("feature_pin", {}).get("sha256"):
        raise ValueError("Pretraining feature input differs from the prepared stack")
    if (not rep.get("coverage_pass") or
            rep.get("visited_pixels") != prep.get("footprint_pixels") or
            rep.get("masked_evaluations_per_pixel") != 3 or
            rep.get("encoder_state_sha256") != pre.get("encoder_state_sha256")):
        raise ValueError("Complete frozen full-footprint inference is required")
    if rep.get("checkpoint_sha256") != pre.get("checkpoint_sha256"):
        raise ValueError("Representation checkpoint differs from pretraining")
    if not anomaly.get("label_free") or anomaly.get("source_errors_sha256") != rep.get("errors_sha256"):
        raise ValueError("A completed label-free anomaly receipt is required")

    expected_order = [prep.get("completed_utc"), pre.get("completed_utc"),
                      rep.get("completed_utc"), anomaly.get("completed_utc")]
    if not all(isinstance(value, str) for value in expected_order) or expected_order != sorted(expected_order):
        raise ValueError("Preparation, pretraining, inference, and anomaly stages are not ordered")

    files = {
        PREP / "values.npy": prep.get("values_sha256"),
        PREP / "observed.npy": prep.get("observed_sha256"),
        ART / "encoder.pt": pre.get("checkpoint_sha256"),
        ART / "latent.npy": rep.get("latent_sha256"),
        ART / "errors.npy": rep.get("errors_sha256"),
        ART / "anomaly.npy": anomaly.get("anomaly_sha256"),
    }
    for path, expected in files.items():
        if not path.is_file() or not expected or sha256_file(path) != expected:
            raise ValueError(f"Label-free prerequisite bytes differ from their receipt: {path.name}")
    if rep["checkpoint_sha256"] != pre["checkpoint_sha256"]:
        raise ValueError("Frozen representation checkpoint mismatch")
    return prep, pre, rep, anomaly


def main() -> None:
    output_receipt = EVIDENCE / "h27_srcoh_feature.json"
    if output_receipt.exists():
        raise SystemExit("An H27-SRCOH feature receipt already exists; preserve it")
    frozen = verify_h27_freeze(ROOT)
    preregistration = frozen["manifest"]["preregistration_path"]
    if preregistration != "knowledge/hypothesis-slate-20261002-v2.md":
        raise ValueError("The freeze manifest points to an unexpected preregistration")
    prep, pre, rep, anomaly = require_label_free_prerequisites(frozen)

    values_path = PREP / "values.npy"
    observed_path = PREP / "observed.npy"
    footprint_path = PREP / "footprint.npy"
    values = np.load(values_path, mmap_mode="r")
    observed = np.load(observed_path, mmap_mode="r")
    footprint = np.load(footprint_path)
    if values.shape != (19, *footprint.shape) or observed.shape != values.shape:
        raise ValueError("Prepared full-raster arrays do not align")
    if not np.array_equal(footprint, pinned_footprint()):
        raise ValueError("Prepared footprint differs from the pinned RLE geometry")
    if int(footprint.sum()) != prep.get("footprint_pixels"):
        raise ValueError("Prepared footprint differs from its frozen receipt")

    started = utcnow()
    t0 = time.monotonic()
    score, support, transform = build_srcoh_feature(values, observed, footprint)
    ART.mkdir(parents=True, exist_ok=True)
    score_path, support_path = ART / "h27_srcoh_score.npy", ART / "h27_srcoh_support.npy"
    np.save(score_path, score, allow_pickle=False)
    np.save(support_path, support, allow_pickle=False)

    source_hashes = {relative: sha256_file(ROOT / relative)
                     for relative in frozen["code_sha256"]}
    receipt = {
        "method": "H27-SRCOH-v1",
        "started_utc": started,
        "completed_utc": utcnow(),
        "labels_opened": False,
        "template_opened": False,
        "preregistration_path": preregistration,
        "preregistration_sha256": frozen["manifest"]["preregistration_sha256"],
        "slate_commit": frozen["manifest"]["slate_commit"],
        "code_freeze_commit": frozen["commit"],
        "code_freeze_branch": frozen["branch"],
        "code_freeze_manifest_sha256": frozen["manifest_sha256"],
        "source_sha256": source_hashes,
        "preparation_receipt_sha256": sha256_file(EVIDENCE / "preparation.json"),
        "pretraining_receipt_sha256": sha256_file(EVIDENCE / "pretraining.json"),
        "representation_receipt_sha256": sha256_file(EVIDENCE / "representation.json"),
        "anomaly_receipt_sha256": sha256_file(EVIDENCE / "anomaly.json"),
        "pretraining_encoder_state_sha256": pre["encoder_state_sha256"],
        "input_feature_stack_sha256": prep["feature_pin"]["sha256"],
        "input_manifest_sha256": sha256_file(ROOT / "data/input_manifest.json"),
        "prepared_values_sha256": sha256_file(values_path),
        "prepared_observed_sha256": sha256_file(observed_path),
        "footprint_sha256": sha256_file(footprint_path),
        "representation_latent_sha256": rep["latent_sha256"],
        "masked_errors_sha256": rep["errors_sha256"],
        "anomaly_sha256": anomaly["anomaly_sha256"],
        "transform": transform,
        "score_sha256": sha256_file(score_path),
        "support_sha256": sha256_file(support_path),
        "elapsed_seconds": round(time.monotonic() - t0, 3),
        "screen_only": True,
        "warning": "Label-free owner-mirror strain-channel transform; channel semantics and units are unverified; not a fault probability.",
    }
    write_json(output_receipt, receipt)
    print("H27-SRCOH FEATURE COMPLETE — labels and template values unopened", flush=True)
    print({key: receipt[key] for key in
           ("completed_utc", "score_sha256", "support_sha256", "elapsed_seconds")}, flush=True)


if __name__ == "__main__":
    main()
