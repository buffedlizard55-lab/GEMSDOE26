"""Frozen, label-free H27-SRCOH multiscale strain-edge coherence feature."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter

from .emission import percentile_rank

# Zero-based positions and aliases from the owner mirror's band descriptions.
# Neither names nor physical units are organizer-authenticated.
STRAIN_BANDS = (3, 6, 7)
STRAIN_NAMES = ("geod_2ndinv", "geod_shearrate", "geod_dilaterate")
SCALES_PIXELS = (3.0, 6.0, 12.0)
EDGE_HALO_PIXELS = 4 * int(SCALES_PIXELS[-1])
LOG_EPSILON = 1e-6
ZERO_GRADIENT_EPSILON = 1e-12


def _binary_grid(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not array.size or array.dtype.kind not in "biuf":
        raise ValueError(f"Nonempty two-dimensional {name} required")
    if array.dtype != np.dtype(bool) and not np.isin(array, [0, 1]).all():
        raise ValueError(f"Finite binary {name} required")
    if name == "footprint" and not array.any():
        raise ValueError("Footprint has no valid pixels")
    return array.astype(bool, copy=False)


def build_srcoh_feature(values: np.ndarray, observed: np.ndarray,
                        footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Build the fixed H27-SRCOH-v1 scalar feature and its label-free support.

    Inputs are only the prepared 19-band unlabeled feature stack, its explicit
    observation masks, and the geometric footprint. This API accepts no labels,
    template values, coordinates, external rasters, or fitted parameters.
    """
    x = np.asanyarray(values)
    obs = np.asanyarray(observed)
    fp = _binary_grid(footprint, "footprint")
    if (x.ndim != 3 or x.shape[0] != 19 or x.shape[1:] != fp.shape
            or x.dtype.kind not in "biuf"):
        raise ValueError("All 19 aligned prepared real-valued feature bands are required")
    if obs.shape != x.shape or obs.dtype.kind not in "biuf":
        raise ValueError("Aligned feature observation masks are required")

    for band, name in zip(STRAIN_BANDS, STRAIN_NAMES, strict=True):
        if obs.dtype != np.dtype(bool) and not np.isin(obs[band], [0, 1]).all():
            raise ValueError(f"{name} observation mask must be binary")
        valid = fp & (obs[band] != 0)
        if not valid.any() or not np.isfinite(x[band][valid]).all():
            raise ValueError(f"{name} band has no finite valid observations")

    joint_observed = fp.copy()
    for band in STRAIN_BANDS:
        joint_observed &= obs[band] != 0
    support = binary_erosion(
        joint_observed,
        structure=np.ones((3, 3), dtype=bool),
        iterations=EDGE_HALO_PIXELS,
        border_value=0,
    )
    if not support.any():
        raise ValueError("H27-SRCOH has no support after fixed 48-pixel erosion")

    orientation_cos = [np.zeros(fp.shape, dtype=np.float32) for _ in STRAIN_BANDS]
    orientation_sin = [np.zeros(fp.shape, dtype=np.float32) for _ in STRAIN_BANDS]
    log_scale_product = np.zeros(fp.shape, dtype=np.float32)

    for sigma in SCALES_PIXELS:
        ranks: list[np.ndarray] = []
        magnitudes: list[np.ndarray] = []
        unit_rows: list[np.ndarray] = []
        unit_cols: list[np.ndarray] = []

        for channel_index, band in enumerate(STRAIN_BANDS):
            valid = fp & (obs[band] != 0)
            channel = np.array(x[band], dtype=np.float32, copy=True)
            if not np.isfinite(channel[valid]).all():
                raise ValueError(f"{STRAIN_NAMES[channel_index]} values are not finite in float32")
            # The observed mask and support erosion ensure zero-filled values
            # cannot enter any retained Gaussian-derivative kernel.
            channel[~valid] = 0
            row_gradient = gaussian_filter(
                channel, sigma=sigma, order=(1, 0), mode="nearest", truncate=4.0
            )
            col_gradient = gaussian_filter(
                channel, sigma=sigma, order=(0, 1), mode="nearest", truncate=4.0
            )
            magnitude = np.hypot(row_gradient, col_gradient)
            rank = percentile_rank(magnitude, support)

            nonzero = magnitude > ZERO_GRADIENT_EPSILON
            unit_row = np.divide(
                row_gradient, magnitude, out=np.zeros_like(row_gradient), where=nonzero
            )
            unit_col = np.divide(
                col_gradient, magnitude, out=np.zeros_like(col_gradient), where=nonzero
            )
            unit_row[~support] = 0
            unit_col[~support] = 0

            # Doubled-angle vectors make opposite gradient polarity equivalent.
            cos2 = np.square(unit_row)
            cos2 -= np.square(unit_col)
            sin2 = unit_row * unit_col
            sin2 *= 2
            orientation_cos[channel_index] += cos2
            orientation_sin[channel_index] += sin2

            ranks.append(rank)
            magnitudes.append(magnitude)
            unit_rows.append(unit_row)
            unit_cols.append(unit_col)
            del channel, row_gradient, col_gradient, cos2, sin2, nonzero

        scale_log = np.zeros(fp.shape, dtype=np.float32)
        for rank in ranks:
            scale_log[support] += np.log(rank[support] + LOG_EPSILON)

        for i, j in ((0, 1), (0, 2), (1, 2)):
            alignment = unit_rows[i] * unit_rows[j]
            alignment += unit_cols[i] * unit_cols[j]
            norm_product = magnitudes[i] * magnitudes[j]
            alignment *= norm_product
            np.abs(alignment, out=alignment)
            norm_product += LOG_EPSILON
            alignment /= norm_product
            np.clip(alignment, 0, 1, out=alignment)
            scale_log[support] += np.log(alignment[support] + LOG_EPSILON)
            del alignment, norm_product

        scale_score = np.exp(scale_log / 6.0)
        log_scale_product[support] += np.log(scale_score[support] + LOG_EPSILON)
        del ranks, magnitudes, unit_rows, unit_cols, scale_log, scale_score

    persistence = []
    for cosine_sum, sine_sum in zip(orientation_cos, orientation_sin, strict=True):
        r = np.hypot(cosine_sum / len(SCALES_PIXELS),
                     sine_sum / len(SCALES_PIXELS)).astype(np.float32, copy=False)
        r[~support] = 0
        persistence.append(r)

    scale_geometric_mean = np.exp(log_scale_product / len(SCALES_PIXELS))
    persistence_product = persistence[0] * persistence[1]
    persistence_product *= persistence[2]
    raw = scale_geometric_mean * np.cbrt(persistence_product)
    raw[~support] = 0
    if (not np.isfinite(raw[support]).all() or (raw[support] < 0).any()
            or (raw[support] > 1.00001).any()):
        raise ValueError("H27-SRCOH transform produced invalid raw scores")

    ranked = percentile_rank(raw, support)
    ranked[(~support) | (raw == 0)] = 0
    if not np.isfinite(ranked).all() or (ranked < 0).any() or (ranked > 1).any():
        raise ValueError("H27-SRCOH percentile ranking produced invalid values")

    metadata = {
        "method": "H27-SRCOH-v1: multiscale cross-channel strain-edge coherence",
        "input_bands_zero_based": list(STRAIN_BANDS),
        "input_band_names_from_owner_mirror_not_organizer_authentication": list(STRAIN_NAMES),
        "scales_sigma_pixels": list(SCALES_PIXELS),
        "scales_sigma_m_at_100m_grid": [int(s * 100) for s in SCALES_PIXELS],
        "gaussian_filter": "scipy.ndimage.gaussian_filter derivatives, mode=nearest, truncate=4.0",
        "support_definition": "joint observed masks and footprint eroded 48 px with a 3x3 all-true structure, border_value=0",
        "magnitude_rank": "average-tie rank divided by support count",
        "pairwise_alignment": "abs(g_i dot g_j)/(norm(g_i)*norm(g_j)+1e-6), clipped [0,1]; zero when either norm <=1e-12",
        "scale_combination": "exp(mean(log(term+1e-6))) over three magnitude ranks and three pairwise alignments",
        "orientation_persistence": "resultant length of mean doubled-angle unit row/column gradients over fixed scales; zero gradients contribute (0,0)",
        "raw_score": "exp(mean(log(scale_score+1e-6))) times cube_root(R0*R1*R2); no floor on persistence product",
        "output_rank": "average-tie percentile rank on support; exact-zero raw values and outside-support pixels forced to zero",
        "support_pixels": int(support.sum()),
        "raw_zero_pixels_on_support": int(np.count_nonzero(support & (raw == 0))),
        "ranked_min_on_support": float(ranked[support].min()),
        "ranked_max_on_support": float(ranked[support].max()),
        "label_free_inputs_only": True,
        "warning": "Owner-mirror channel names/units are unverified; this feature is not a fault probability or geothermal-resource confirmation.",
    }
    return ranked.astype(np.float32, copy=False), support, metadata
