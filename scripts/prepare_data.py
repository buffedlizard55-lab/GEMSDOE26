#!/usr/bin/env python3
"""Prepare the COMPLETE unlabeled stack, band by band. Never open labels/template."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import PREP, RAW, footprint, utcnow, verify_grid, verify_pinned, write_json, sha256_file


def main() -> None:
    source = RAW / "training_features.tif"
    pin = verify_pinned(source)
    fp = footprint()
    PREP.mkdir(parents=True, exist_ok=True)
    with rasterio.open(source) as ds:
        verify_grid(ds)
        if ds.count != 19:
            raise ValueError("All 19 channels required, refusing a partial stack")
        shape = (ds.count, ds.height, ds.width)
        values = np.lib.format.open_memmap(PREP / "values.npy", mode="w+", dtype=np.float16, shape=shape)
        observed = np.lib.format.open_memmap(PREP / "observed.npy", mode="w+", dtype=np.uint8, shape=shape)
        any_observed = np.zeros(fp.shape, dtype=bool)
        rows = []
        for i in range(ds.count):
            raw = ds.read(i + 1)
            valid = fp & np.isfinite(raw) & (raw > -1e30)
            if ds.nodata is not None and np.isfinite(ds.nodata):
                valid &= raw != ds.nodata
            vector = raw[valid].astype(np.float64)
            if not vector.size:
                raise ValueError(f"Band {i+1} has no valid observations")
            q02, med, q98 = np.quantile(vector, [0.02, 0.5, 0.98])
            # Robust scale, constant channels remain available with zero variation.
            scale = max(float((q98 - q02) / 4.0), 1e-6)
            normalized = np.zeros(fp.shape, dtype=np.float32)
            normalized[valid] = np.clip((raw[valid].astype(np.float64) - med) / scale, -8, 8)
            values[i] = normalized.astype(np.float16)
            observed[i] = valid
            any_observed |= valid
            row = {"band": i + 1, "description_from_owner_mirror_not_certified": ds.descriptions[i],
                   "valid_pixels": int(valid.sum()), "median": float(med), "scale": scale,
                   "q02": float(q02), "q98": float(q98), "clipped_pixels": int((np.abs(normalized[valid]) >= 8).sum())}
            rows.append(row)
            print("prepared", i + 1, row["valid_pixels"], flush=True)
        values.flush()
        observed.flush()
    np.save(PREP / "footprint.npy", fp)
    write_json(ROOT / "evidence/preparation.json", {
        "completed_utc": utcnow(), "feature_pin": pin, "shape": list(shape),
        "footprint_pixels": int(fp.sum()), "any_observed_pixels": int((fp & any_observed).sum()),
        "inside_pixels_without_any_observation": int((fp & ~any_observed).sum()),
        "all_channels_retained": True, "labels_opened": False,
        "band_scale_fit": "Full unlabeled footprint: median, scale=(q98-q02)/4, clip [-8,8]",
        "semantic_warning": "Mirror descriptions are not organizer metadata; tc, earthquake and conductive-base depth meanings require source resolution.",
        "bands": rows, "values_sha256": sha256_file(PREP / "values.npy"),
        "observed_sha256": sha256_file(PREP / "observed.npy"),
        "missing_targets_excluded": True})


if __name__ == "__main__":
    main()
