#!/usr/bin/env python3
"""Build the frozen full-raster XEDGE feature without reading labels/template."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import (ART, EVIDENCE, PREP, RAW, footprint as pinned_footprint,
                           read_json, sha256_file, utcnow, verify_pinned, write_json)
from gems26.xedge import build_xedge_score

SLATE_COMMIT = "876c0b2d71116edbf8c888f38366762aea1eb195"
PROTOCOL_FREEZE_COMMIT = "fce3f74ad58a7f37ac5cffca6bc0c1a770bb9eda"
PREREG_PATH = ROOT / "knowledge/hypothesis-slate-20261002.md"


def require_preregistered_commit() -> None:
    for commit in (SLATE_COMMIT, PROTOCOL_FREEZE_COMMIT):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                                cwd=ROOT, check=False)
        if result.returncode != 0:
            raise ValueError("The ranked slate and final XEDGE v1 protocol must be committed before feature construction")


def main() -> None:
    if (EVIDENCE / "xedge_feature.json").exists():
        raise SystemExit("An XEDGE feature receipt already exists. Preserve its hashes/timestamps; do not overwrite it.")
    started = utcnow()
    t0 = time.monotonic()
    require_preregistered_commit()
    prep = read_json(EVIDENCE / "preparation.json")
    pre = read_json(EVIDENCE / "pretraining.json")
    rep = read_json(EVIDENCE / "representation.json")
    ano = read_json(EVIDENCE / "anomaly.json")
    if (not prep.get("labels_opened") is False or not pre.get("coverage_pass") or
            pre.get("labels_opened") is not False or not rep.get("coverage_pass") or
            rep.get("labels_opened") is not False or ano.get("labels_opened") is not False):
        raise ValueError("Complete label-free preparation, pretraining, inference and anomaly receipts are required")
    if not (prep["completed_utc"] <= pre["started_utc"] <= pre["completed_utc"] <=
            rep["completed_utc"] <= ano["completed_utc"] <= started):
        raise ValueError("Label-free stages are not ordered before XEDGE construction")
    if prep["shape"][0] != 19 or not prep.get("all_channels_retained"):
        raise ValueError("All 19 feature channels must have been prepared")
    if prep["feature_pin"].get("sha256") != verify_pinned(RAW / "training_features.tif").get("sha256"):
        raise ValueError("Prepared stack differs from the pinned feature raster")
    if sha256_file(PREP / "values.npy") != prep["values_sha256"] or sha256_file(PREP / "observed.npy") != prep["observed_sha256"]:
        raise ValueError("Prepared arrays differ from their archived receipt")
    if sha256_file(ART / "encoder.pt") != pre["checkpoint_sha256"]:
        raise ValueError("Full-raster encoder checkpoint differs from its receipt")
    if sha256_file(ART / "latent.npy") != rep["latent_sha256"] or sha256_file(ART / "errors.npy") != rep["errors_sha256"]:
        raise ValueError("Frozen representation arrays differ from their receipts")
    if sha256_file(ART / "anomaly.npy") != ano["anomaly_sha256"]:
        raise ValueError("Label-free anomaly array differs from its receipt")
    expected_descriptions = ((2, "rtp -"), (13, "iso_grav_anom -"))
    for one_based_band, prefix in expected_descriptions:
        actual = prep["bands"][one_based_band - 1]["description_from_owner_mirror_not_certified"]
        if not actual.startswith(prefix):
            raise ValueError(f"Expected band {one_based_band} alias {prefix!r}; refusing silent substitution")

    # From this point to receipt writing, only the precomputed unlabeled stack,
    # masks and the geometric footprint are read. No label/template path exists.
    values = np.load(PREP / "values.npy", mmap_mode="r")
    observed = np.load(PREP / "observed.npy", mmap_mode="r")
    footprint = np.load(PREP / "footprint.npy")
    if not np.array_equal(footprint, pinned_footprint()):
        raise ValueError("Prepared footprint differs from pinned run-length geometry")
    score, support, details = build_xedge_score(values, observed, footprint)
    ART.mkdir(parents=True, exist_ok=True)
    np.save(ART / "xedge_score.npy", score)
    np.save(ART / "xedge_support.npy", support)
    receipt = {
        "method": "H26-XEDGE-v1",
        "started_utc": started,
        "completed_utc": utcnow(),
        "labels_opened": False,
        "template_opened": False,
        "preregistration_path": str(PREREG_PATH.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG_PATH),
        "preregistration_commit": SLATE_COMMIT,
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "preparation_completed_utc": prep["completed_utc"],
        "pretraining_completed_utc": pre["completed_utc"],
        "representation_completed_utc": rep["completed_utc"],
        "anomaly_completed_utc": ano["completed_utc"],
        "pretraining_encoder_state_sha256": pre["encoder_state_sha256"],
        "feature_stack_sha256": prep["feature_pin"]["sha256"],
        "prepared_values_sha256": prep["values_sha256"],
        "prepared_observed_sha256": prep["observed_sha256"],
        "transform": details,
        "score_sha256": sha256_file(ART / "xedge_score.npy"),
        "support_sha256": sha256_file(ART / "xedge_support.npy"),
        "elapsed_seconds": round(time.monotonic() - t0, 3),
        "screen_only": True,
        "warning": "Label-free geophysical edge score; not a probability or confirmed fault/vent map.",
    }
    write_json(EVIDENCE / "xedge_feature.json", receipt)
    print("XEDGE FEATURE COMPLETE — no label/template values read", flush=True)
    print({k: receipt[k] for k in ("completed_utc", "score_sha256", "support_sha256", "elapsed_seconds")}, flush=True)


if __name__ == "__main__":
    main()
