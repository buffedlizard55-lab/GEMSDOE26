#!/usr/bin/env python3
"""Finish the independent anomaly branch before any label access."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import ART, PREP, EVIDENCE, read_json, sha256_file, utcnow, write_json
from gems26.anomaly import coherent_error


def main():
    rep = read_json(EVIDENCE / "representation.json")
    if not rep["coverage_pass"] or rep["labels_opened"]:
        raise ValueError("Complete label-free representation required")
    if sha256_file(ART / "errors.npy") != rep["errors_sha256"]:
        raise ValueError("Masked error integrity mismatch")
    fp = np.load(PREP / "footprint.npy")
    result, meta = coherent_error(np.load(ART / "errors.npy", mmap_mode="r"),
                                 np.load(PREP / "observed.npy", mmap_mode="r"), fp)
    np.save(ART / "anomaly.npy", result)
    write_json(EVIDENCE / "anomaly.json", {**meta, "completed_utc": utcnow(), "labels_opened": False,
                                          "anomaly_sha256": sha256_file(ART / "anomaly.npy"),
                                          "source_errors_sha256": rep["errors_sha256"]})
    print("LABEL-FREE ANOMALY COMPLETE", flush=True)

if __name__ == "__main__":
    main()
