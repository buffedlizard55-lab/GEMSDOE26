#!/usr/bin/env python3
"""Infer complete frozen embeddings and complementary MASKED errors, before labels."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import ART, EVIDENCE, PREP, padded_tile, read_json, sha256_file, tile_origins, utcnow, write_json
from gems26.ssl import complementary_mask, load_frozen, state_hash

GROUPS = {"magnetic": [0, 1, 2, 8, 13], "gravity": [4, 10, 12, 17],
          "terrain": [11, 18], "strain": [3, 6, 7], "conductive": [14, 16],
          "other_unresolved": [5, 9, 15]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tile", type=int, default=192)
    parser.add_argument("--halo", type=int, default=16)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.tile < 4 or args.tile % 4 or args.halo < 8 or args.halo % 4 or args.threads < 1:
        raise ValueError("4-divisible tiles/halo, halo >= 8 and positive threads required")
    torch.set_num_threads(args.threads)
    receipt = read_json(EVIDENCE / "pretraining.json")
    if not receipt["coverage_pass"] or receipt["labels_opened"]:
        raise ValueError("Label-free full-raster pretraining receipt required")
    if sha256_file(ART / "encoder.pt") != receipt["checkpoint_sha256"]:
        raise ValueError("Checkpoint file checksum mismatch")
    model, saved = load_frozen(ART / "encoder.pt")
    if state_hash(model) != receipt["encoder_state_sha256"]:
        raise ValueError("Pretraining receipt parameter mismatch")
    values = np.load(PREP / "values.npy", mmap_mode="r")
    obs = np.load(PREP / "observed.npy", mmap_mode="r")
    fp = np.load(PREP / "footprint.npy")
    latent = np.lib.format.open_memmap(ART / "latent.npy", mode="w+", dtype=np.float16, shape=(24,) + fp.shape)
    errors = np.lib.format.open_memmap(ART / "errors.npy", mode="w+", dtype=np.float16, shape=(19,) + fp.shape)
    latent[:] = 0
    errors[:] = 0
    done = np.zeros(fp.shape, bool)
    masked_counts = np.zeros(fp.shape, np.uint8)
    tiles = tile_origins(fp, args.tile)
    t0 = time.monotonic()
    with torch.no_grad():
        for i, (r, c) in enumerate(tiles):
            tile_size = args.tile + 2 * args.halo
            x = torch.from_numpy(padded_tile(values, r, c, args.tile, args.halo)[None].astype(np.float32))
            o = torch.from_numpy(padded_tile(obs, r, c, args.tile, args.halo)[None].astype(np.float32))
            z = model.encode(x, o)
            accum = torch.zeros_like(x)
            counts = torch.zeros(1, 1, tile_size, tile_size)
            for phase in range(4):
                m = complementary_mask(tile_size, tile_size, phase, 4, r - args.halo, c - args.halo)
                recon, _ = model(x, o * (~m))
                accum += (recon - x).square() * m
                counts += m
            if not torch.all(counts == 3):
                raise ValueError("Every inference pixel must be hidden in exactly 3 masks")
            e = accum / counts * o
            h = min(args.tile, fp.shape[0] - r)
            w = min(args.tile, fp.shape[1] - c)
            crop = (slice(args.halo, args.halo + h), slice(args.halo, args.halo + w))
            latent[:, r:r + h, c:c + w] = z[0].numpy()[(slice(None),) + crop].astype(np.float16)
            errors[:, r:r + h, c:c + w] = np.clip(e[0].numpy()[(slice(None),) + crop], 0, 60000).astype(np.float16)
            done[r:r + h, c:c + w] |= fp[r:r + h, c:c + w]
            masked_counts[r:r + h, c:c + w] = counts[0, 0].numpy()[crop].astype(np.uint8)
            if (i + 1) % 20 == 0:
                print(f"inferred {i+1}/{len(tiles)} tiles {time.monotonic()-t0:.1f}s", flush=True)
    latent.flush()
    errors.flush()
    if not np.array_equal(done, fp) or (masked_counts[fp] != 3).any():
        raise ValueError("Representation inference coverage is incomplete")
    if state_hash(model) != saved["state_sha256"]:
        raise ValueError("Frozen representation weights changed during inference")
    rows = []
    for i in range(19):
        valid = fp & (obs[i] > 0)
        e = errors[i][valid].astype(np.float32)
        if not np.isfinite(e).all():
            raise ValueError("Nonfinite masked error")
        rows.append({"band": i + 1, "masked_mse_mean": float(e.mean()),
                     "masked_mse_median": float(np.median(e)), "valid_pixels": int(valid.sum())})
    write_json(EVIDENCE / "representation.json", {
        "completed_utc": utcnow(), "labels_opened": False, "coverage_pass": True,
        "encoder_state_sha256": state_hash(model), "checkpoint_sha256": receipt["checkpoint_sha256"],
        "visited_pixels": int(done.sum()), "masked_evaluations_per_pixel": 3,
        "inference_args": vars(args), "tiles": len(tiles), "groups_zero_based": GROUPS,
        "latent_sha256": sha256_file(ART / "latent.npy"), "errors_sha256": sha256_file(ART / "errors.npy"),
        "mask_scheme": "4 complementary phases, 75% hidden, global patch coordinates and >=16 pixel halo",
        "error_meaning": "Label-free anomaly diagnostic, NOT probability or evidence of a fault",
        "elapsed_seconds": round(time.monotonic() - t0, 2), "bands": rows})
    print("MASKED INFERENCE COMPLETE — labels still unopened", flush=True)


if __name__ == "__main__":
    main()
