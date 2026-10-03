#!/usr/bin/env python3
"""Six exhaustive tile passes of the unlabeled raster. No label or template IO."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import ART, EVIDENCE, PREP, SEED, padded_tile, read_json, sha256_file, tile_origins, utcnow, write_json
from gems26.ssl import MaskedGeoEncoder, force_unseen_patches, masked_reconstruction_loss, random_patch_mask, state_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--tile", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--preregistration", default="knowledge/preregistration.md",
                        help="Committed protocol whose bytes are pinned in the label-free receipt")
    args = parser.parse_args()
    if args.epochs < 1 or args.tile % 4 or args.batch_size < 1 or args.threads < 1:
        raise ValueError("Positive epochs/batch/threads and 4-divisible tile size required")
    preregistration_path = (ROOT / args.preregistration).resolve()
    try:
        preregistration_relative = preregistration_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("Preregistration must be inside the project root") from exc
    if not preregistration_path.is_file():
        raise FileNotFoundError(f"Preregistration not found: {preregistration_relative}")
    torch.set_num_threads(args.threads)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    generator = torch.Generator().manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    prep = read_json(EVIDENCE / "preparation.json")
    values = np.load(PREP / "values.npy", mmap_mode="r")
    observed = np.load(PREP / "observed.npy", mmap_mode="r")
    fp = np.load(PREP / "footprint.npy")
    if values.shape != observed.shape or values.shape[0] != 19 or values.shape[1:] != fp.shape:
        raise ValueError("Prepared arrays are inconsistent or partial")
    if sha256_file(PREP / "values.npy") != prep["values_sha256"] or sha256_file(PREP / "observed.npy") != prep["observed_sha256"]:
        raise ValueError("Prepared feature integrity failed")
    tiles = tile_origins(fp, args.tile)
    model = MaskedGeoEncoder(19, 24)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    seen = np.zeros(fp.shape, dtype=bool)
    target_seen = np.zeros(fp.shape, dtype=bool)
    band_targets = np.zeros(19, dtype=np.int64)
    records = []
    start = utcnow()
    t0 = time.monotonic()
    for epoch in range(args.epochs):
        model.train()
        order = rng.permutation(len(tiles))
        loss_sum = steps = 0
        epoch_seen = np.zeros(fp.shape, bool)
        for offset in range(0, len(tiles), args.batch_size):
            coords = [tiles[i] for i in order[offset:offset + args.batch_size]]
            x = torch.from_numpy(np.stack([padded_tile(values, r, c, args.tile) for r, c in coords]).astype(np.float32))
            obs = torch.from_numpy(np.stack([padded_tile(observed, r, c, args.tile) for r, c in coords]).astype(np.float32))
            mask = random_patch_mask(len(coords), args.tile, args.tile, 4, .75, generator)
            if epoch == args.epochs - 1:
                unseen = torch.from_numpy(np.stack([padded_tile(fp & ~target_seen, r, c, args.tile) for r, c in coords])[:, None])
                mask = force_unseen_patches(mask, unseen, 4)
            pred, _z = model(x, obs * (~mask))
            loss = masked_reconstruction_loss(pred, x, obs, mask)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite reconstruction training loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            loss_sum += loss.item()
            steps += 1
            m = mask[:, 0].numpy()
            for j, (r, c) in enumerate(coords):
                h = min(args.tile, fp.shape[0] - r)
                w = min(args.tile, fp.shape[1] - c)
                epoch_seen[r:r + h, c:c + w] |= fp[r:r + h, c:c + w]
                target_seen[r:r + h, c:c + w] |= m[j, :h, :w] & fp[r:r + h, c:c + w]
            band_targets += (obs.numpy() * mask.numpy()).sum(axis=(0, 2, 3)).astype(np.int64)
            if steps % 100 == 0:
                print(f"epoch {epoch+1} step {steps} loss {loss_sum/steps:.5f}", flush=True)
        seen |= epoch_seen
        if not np.array_equal(epoch_seen, fp):
            raise ValueError("An epoch did not visit the complete footprint")
        record = {"epoch": epoch + 1, "mean_masked_huber_loss": loss_sum / steps,
                  "visited_pixels": int(epoch_seen.sum()), "tiles": len(tiles), "steps": steps,
                  "elapsed_seconds": round(time.monotonic() - t0, 2)}
        records.append(record)
        print(record, flush=True)
    if not np.array_equal(seen, fp) or not np.array_equal(target_seen, fp) or (band_targets <= 0).any():
        raise ValueError("Incomplete visit/masking/channel coverage; refusing to permit label fitting")
    ART.mkdir(parents=True, exist_ok=True)
    checkpoint = ART / "encoder.pt"
    parameter_hash = state_hash(model)
    torch.save({"state_dict": model.state_dict(), "channels": 19, "latent": 24,
                "state_sha256": parameter_hash, "seed": SEED, "epochs": args.epochs}, checkpoint)
    np.save(ART / "ssl_visited.npy", seen)
    np.save(ART / "ssl_masked.npy", target_seen)
    receipt = {"started_utc": start, "completed_utc": utcnow(), "labels_opened": False,
               "input_feature_sha256": prep["feature_pin"]["sha256"],
               "all_channels": 19, "training_geography": "Entire unlabeled footprint; transductive",
               "architecture": "Small convolutional masked autoencoder, no unmasked decoder skip",
               "mask_patch_pixels": 4, "mask_ratio": .75, "args": vars(args),
               "loss": "Masked valid-only SmoothL1 (Huber)", "epochs": records,
               "footprint_pixels_visited": int(seen.sum()), "footprint_pixels_masked": int(target_seen.sum()),
               "band_valid_target_exposures": band_targets.tolist(),
               "pixels_with_no_observed_channel": prep["inside_pixels_without_any_observation"],
               "missingness_caveat": "These pixels are visited/masked but cannot provide any reconstruction target.",
               "coverage_pass": True, "encoder_state_sha256": parameter_hash,
               "checkpoint_sha256": sha256_file(checkpoint),
               "torch_version": torch.__version__, "device": "cpu",
               "elapsed_seconds": round(time.monotonic() - t0, 2),
               "preregistration_path": preregistration_relative,
               "preregistration_sha256": sha256_file(preregistration_path)}
    write_json(EVIDENCE / "pretraining.json", receipt)
    print("PRETRAINING COMPLETE — labels still unopened", flush=True)


if __name__ == "__main__":
    main()
