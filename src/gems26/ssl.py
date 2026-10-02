"""Small patch-masked convolutional autoencoder, not a ViT MAE/Prithvi replica.

There is no label IO in this module. Missing channels are explicitly encoded and
excluded from target loss. There is no unmasked skip path into the decoder.
"""
from __future__ import annotations

import hashlib

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class MaskedGeoEncoder(nn.Module):
    def __init__(self, channels: int = 19, latent: int = 24):
        super().__init__()
        self.channels = channels
        self.latent = latent
        self.encoder = nn.Sequential(
            nn.Conv2d(channels * 2, 16, 3, padding=1), nn.GELU(),
            nn.Conv2d(16, latent, 3, padding=2, dilation=2), nn.GELU(),
            nn.Conv2d(latent, latent, 3, padding=4, dilation=4), nn.GELU(),
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(latent, 16, 3, padding=1), nn.GELU(),
            nn.Conv2d(16, channels, 1),
        )

    def encode(self, values: torch.Tensor, visible: torch.Tensor) -> torch.Tensor:
        # NaN * 0 is still NaN. Prepared inputs are finite; this does not change
        # the numerical path on the archived executed dataset.
        hidden_safe = torch.where(visible != 0, values, torch.zeros_like(values))
        return self.encoder(torch.cat((hidden_safe, visible), dim=1))

    def forward(self, values: torch.Tensor, visible: torch.Tensor):
        z = self.encode(values, visible)
        return self.decoder(z), z


def state_hash(model: nn.Module) -> str:
    h = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        h.update(name.encode())
        h.update(str(tuple(value.shape)).encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def freeze(model: nn.Module) -> None:
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)


def random_patch_mask(batch: int, h: int, w: int, patch: int, ratio: float, generator=None) -> torch.Tensor:
    if (not all(isinstance(x, (int, np.integer)) for x in (batch, h, w, patch)) or
            min(batch, h, w, patch) <= 0 or h % patch or w % patch or not 0 < ratio < 1):
        raise ValueError("Positive dimensions, dividing patch size and mask fraction in (0,1) required")
    n = (h // patch) * (w // patch)
    count = max(1, int(round(ratio * n)))
    order = torch.rand(batch, n, generator=generator).argsort(dim=1)
    grid = torch.zeros(batch, n, dtype=torch.bool)
    grid.scatter_(1, order[:, :count], True)
    return grid.reshape(batch, 1, h // patch, w // patch).repeat_interleave(patch, -2).repeat_interleave(patch, -1)


def force_unseen_patches(mask: torch.Tensor, unseen: torch.Tensor, patch: int) -> torch.Tensor:
    """Force a whole patch, not an isolated pixel, if any valid target is unseen."""
    if not isinstance(patch, (int, np.integer)) or patch <= 0 or mask.shape != unseen.shape or mask.shape[-2] % patch or mask.shape[-1] % patch:
        raise ValueError("Aligned unseen/mask tensors with dividing positive patch size required")
    u = F.max_pool2d(unseen.float(), kernel_size=patch, stride=patch) > 0
    expanded = u.repeat_interleave(patch, -2).repeat_interleave(patch, -1)
    return mask | expanded


def masked_reconstruction_loss(pred: torch.Tensor, target: torch.Tensor,
                               observed: torch.Tensor, masked: torch.Tensor) -> torch.Tensor:
    if pred.ndim != 4 or pred.shape != target.shape or observed.shape != target.shape:
        raise ValueError("Aligned B,C,H,W prediction/target/observation tensors required")
    if masked.shape not in (pred.shape, (pred.shape[0], 1, *pred.shape[-2:])):
        raise ValueError("Aligned spatial patch mask required")
    if not (((observed == 0) | (observed == 1)).all() and ((masked == 0) | (masked == 1)).all()):
        raise ValueError("Finite binary observation/mask factors required")
    valid = observed * masked
    selected = valid != 0
    if valid.sum().item() == 0:
        # Differentiable zero, even if wholly missing targets/predictions contain NaNs.
        return torch.where(torch.isfinite(pred), pred, torch.zeros_like(pred)).sum() * 0
    if not (torch.isfinite(pred[selected]).all() and torch.isfinite(target[selected]).all()):
        raise ValueError("Observed masked targets and predictions must be finite")
    # Preserve full-array summation order for reproduction, without evaluating
    # the loss on unavailable or visible NaN targets.
    safe_pred = torch.where(selected, pred, torch.zeros_like(pred))
    safe_target = torch.where(selected, target, torch.zeros_like(target))
    loss = F.smooth_l1_loss(safe_pred, safe_target, reduction="none")
    return (loss * valid).sum() / valid.sum()


def complementary_mask(h: int, w: int, phase: int, patch: int = 4,
                       row_origin: int = 0, col_origin: int = 0) -> torch.Tensor:
    """4 phases: each pixel hidden in 3, visible in 1; coordinates align halos."""
    if (phase not in range(4) or not all(isinstance(x, (int, np.integer)) for x in (h, w, patch)) or
            min(h, w, patch) <= 0):
        raise ValueError("Mask phase must be 0..3 and dimensions/patch positive integers")
    yy = np.floor_divide(np.arange(h) + row_origin, patch)[:, None]
    xx = np.floor_divide(np.arange(w) + col_origin, patch)[None, :]
    groups = (yy % 2) * 2 + (xx % 2)
    return torch.from_numpy((groups != phase)[None, None])


def load_frozen(path):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    model = MaskedGeoEncoder(saved["channels"], saved["latent"])
    model.load_state_dict(saved["state_dict"])
    freeze(model)
    if state_hash(model) != saved["state_sha256"]:
        raise ValueError("Checkpoint parameter integrity failed")
    return model, saved
