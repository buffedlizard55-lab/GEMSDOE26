"""Coherent masked-error signal computed without labels, coordinates or catalogues."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter

from .emission import percentile_rank


def coherent_error(errors: np.ndarray, observed: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, dict]:
    if errors.shape != observed.shape or errors.shape[1:] != fp.shape:
        raise ValueError("Error/observation/footprint alignment required")
    aggregate = np.zeros(fp.shape, dtype=np.float32)
    valid_count = np.zeros(fp.shape, dtype=np.float32)
    scales = []
    for band in range(errors.shape[0]):
        valid = fp & (observed[band] > 0)
        values = np.log1p(np.asarray(errors[band], dtype=np.float32))
        if not np.isfinite(values[valid]).all() or (values[valid] < 0).any():
            raise ValueError("Invalid reconstruction errors")
        q90 = max(float(np.quantile(values[valid], .9)), 1e-5)
        aggregate += np.where(valid, np.clip(values / q90, 0, 5), 0)
        valid_count += valid
        scales.append(q90)
    aggregate /= np.maximum(valid_count, 1)
    gy, gx = np.gradient(gaussian_filter(aggregate, 1.))
    jxx = gaussian_filter(gx * gx, 2.)
    jyy = gaussian_filter(gy * gy, 2.)
    jxy = gaussian_filter(gx * gy, 2.)
    coherence = np.clip(np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / np.maximum(jxx + jyy, 1e-7), 0, 1)
    support = binary_erosion(fp & (valid_count > 0), iterations=7, structure=np.ones((3, 3), bool))
    result = percentile_rank(aggregate, fp & (valid_count > 0)) * (.5 + .5 * coherence)
    result[~support] = 0
    return result.astype(np.float32), {
        "label_free": True, "channel_q90_log1p_error_scale": scales,
        "aggregation": "Mean of per-channel log1p masked MSE / unlabeled 90th percentile, capped at 5",
        "coherence": "Doubled-angle structure tensor: sqrt((Jxx-Jyy)^2+4Jxy^2)/(Jxx+Jyy), Gaussian 2px",
        "formula": "percentile_rank(mean_error) * (0.5 + 0.5*coherence)",
        "support": "7-pixel eroded observed footprint, preventing padding silhouette emission",
        "eligible_support_pixels": int(support.sum()),
        "warning": "Orientation coherence is not proof of tectonic origin; contacts and survey stripes also cohere"}
