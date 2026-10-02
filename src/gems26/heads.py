"""Only the final neural heads are trained; all encoder features are detached caches."""
from __future__ import annotations

import numpy as np
import torch
from torch import nn

from .common import ART, PREP


class FeatureStore:
    def __init__(self, lidar):
        self.values = np.load(PREP / "values.npy", mmap_mode="r").reshape(19, -1)
        self.observed = np.load(PREP / "observed.npy", mmap_mode="r").reshape(19, -1)
        self.latent = np.load(ART / "latent.npy", mmap_mode="r").reshape(24, -1)
        self.errors = np.load(ART / "errors.npy", mmap_mode="r").reshape(19, -1)
        self.lidar = np.asarray(lidar).reshape(12, -1)
        if not (self.values.shape[1] == self.observed.shape[1] == self.latent.shape[1]
                == self.errors.shape[1] == self.lidar.shape[1]):
            raise ValueError("Feature grids differ")

    def get(self, ids: np.ndarray, ssl: bool) -> np.ndarray:
        q = self.lidar[:, ids].T.astype(np.float32)
        has_lidar = q[:, 11] > 0
        base = np.maximum(q - 1, 0) / 254.
        strike = base[:, 10] * np.pi
        # Same cyclic strike features in control and challenger; zero when unavailable.
        terrain = np.column_stack((base[:, :10], np.cos(2 * strike) * has_lidar,
                                   np.sin(2 * strike) * has_lidar, base[:, 11]))
        rows = [self.values[:, ids].T.astype(np.float32), self.observed[:, ids].T.astype(np.float32), terrain]
        if ssl:
            rows.extend((self.latent[:, ids].T.astype(np.float32), np.log1p(self.errors[:, ids].T.astype(np.float32))))
        result = np.concatenate(rows, axis=1)
        if not np.isfinite(result).all():
            raise ValueError("Nonfinite final-head features")
        return result


class FaultHead(nn.Module):
    def __init__(self, dimensions: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(dimensions, 64), nn.GELU(),
                                 nn.Linear(64, 32), nn.GELU(), nn.Linear(32, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)


def fit_head(x: np.ndarray, y: np.ndarray, seed: int, epochs: int = 16) -> tuple[FaultHead, np.ndarray, np.ndarray, dict]:
    if x.ndim != 2 or y.shape != (len(x),) or not np.isin(y, [0, 1]).all() or len(np.unique(y)) != 2:
        raise ValueError("Finite matrix and two-class binary targets required")
    if not isinstance(epochs, (int, np.integer)) or epochs <= 0:
        raise ValueError("Positive integer final-head epochs required")
    if not np.isfinite(x).all() or x.dtype.kind not in "biuf":
        raise ValueError("Head input must be finite and real-valued")
    x = np.asarray(x, dtype=np.float32)
    if not np.isfinite(x).all():
        raise ValueError("Head input is not representable as float32")
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    mean = x.mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = np.maximum(x.std(axis=0, dtype=np.float64), .05).astype(np.float32)
    features = torch.from_numpy(np.clip((x - mean) / scale, -12, 12))
    targets = torch.from_numpy(y.astype(np.float32))
    head = FaultHead(x.shape[1])
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-3)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float((y == 0).sum() / (y == 1).sum())))
    losses = []
    for epoch in range(epochs):
        head.train()
        order = rng.permutation(len(x))
        total = batches = 0
        for start in range(0, len(order), 2048):
            ids = order[start:start + 2048]
            loss = criterion(head(features[ids]), targets[ids])
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite head loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += loss.item()
            batches += 1
        losses.append(total / batches)
    head.eval()
    return head, mean, scale, {"seed": seed, "epochs": epochs, "samples": len(y),
                               "positive_samples": int(y.sum()), "dimensions": x.shape[1],
                               "head_parameters": sum(p.numel() for p in head.parameters()),
                               "losses": losses, "encoder_trainable_parameters": 0,
                               "calibration": "Case-control training; outputs are ranking scores, not calibrated probabilities"}


def predict_head(store: FeatureStore, head: FaultHead, mean, scale, ids, ssl: bool,
                 shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, np.float32)
    with torch.no_grad():
        for start in range(0, len(ids), 65536):
            selected = ids[start:start + 65536]
            x = np.clip((store.get(selected, ssl) - mean) / scale, -12, 12)
            out.ravel()[selected] = torch.sigmoid(head(torch.from_numpy(x))).numpy()
    return out
