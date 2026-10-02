"""Label-free, preregistered dilatation/conductivity co-anomaly coincidence (H27-DILCOND-v1).

Unlike XEDGE (unsigned gradient-orientation agreement between two potential-field
bands), this is a *sign-aware coincidence* test between a geodetic strain-rate
component and a subsurface electrical property: is this location both anomalously
extensional AND anomalously conductive, relative to its own regional background?
No gradient, edge, or curvature operator is used; no magnetic or gravity band is read.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter

from .emission import percentile_rank

# Zero-based positions in the owner-mirror band order documented in the
# preparation receipt (confirmed via embedded GDAL tags: data_category
# geodetic_strain / subsurface respectively; see sources/band_tags_official.csv).
DILATERATE_BAND = 7   # one-based band 8: geod_dilaterate
CONDUCTIVITY_BAND = 16  # one-based band 17: cond_surf
SCALES_PIXELS = (3.0, 6.0, 12.0)  # 100 m cells: sigma = 300, 600, 1,200 m
BACKGROUND_FACTOR = 4.0  # regional background sigma = 4 * local sigma
EDGE_HALO_PIXELS = 4 * int(SCALES_PIXELS[-1])


def _binary_grid(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not array.size or array.dtype.kind not in "biuf":
        raise ValueError(f"Nonempty two-dimensional {name} required")
    if array.dtype != np.dtype(bool) and not np.isin(array, [0, 1]).all():
        raise ValueError(f"Finite binary {name} required")
    if name == "footprint" and not array.any():
        raise ValueError("Footprint has no valid pixels")
    return array.astype(bool, copy=False)


def build_dilcond_score(values: np.ndarray, observed: np.ndarray, footprint: np.ndarray
                        ) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return a ranked DILCOND feature, its valid support, and fixed metadata.

    The only inputs are unlabeled normalized channels, observation masks and
    the geometric footprint. No labels, template values, coordinates, external
    layers or trainable parameters are accepted by this API.
    """
    x = np.asanyarray(values)
    obs = np.asanyarray(observed)
    fp = _binary_grid(footprint, "footprint")
    if x.ndim != 3 or x.shape[0] != 19 or x.shape[1:] != fp.shape:
        raise ValueError("All 19 aligned prepared feature bands are required")
    if obs.shape != x.shape or obs.dtype.kind not in "biuf":
        raise ValueError("Aligned feature observation masks are required")
    if obs.dtype != np.dtype(bool) and not np.isin(obs, [0, 1]).all():
        raise ValueError("Observation masks must be binary")
    obs = obs.astype(bool, copy=False)
    for band, label in ((DILATERATE_BAND, "geodetic dilatation rate"),
                        (CONDUCTIVITY_BAND, "subsurface conductivity")):
        valid = fp & obs[band]
        if not valid.any() or not np.isfinite(x[band][valid]).all():
            raise ValueError(f"{label} band has no finite valid observations")

    input_valid = fp & obs[DILATERATE_BAND] & obs[CONDUCTIVITY_BAND]
    support = binary_erosion(input_valid, structure=np.ones((3, 3), dtype=bool),
                             iterations=EDGE_HALO_PIXELS, border_value=0)
    if not support.any():
        raise ValueError("DILCOND has no support after fixed 4-sigma footprint/nodata erosion")

    dilate = np.array(x[DILATERATE_BAND], dtype=np.float32, copy=True)
    cond = np.array(x[CONDUCTIVITY_BAND], dtype=np.float32, copy=True)
    dilate[~(fp & obs[DILATERATE_BAND])] = 0
    cond[~(fp & obs[CONDUCTIVITY_BAND])] = 0
    if not np.isfinite(dilate).all() or not np.isfinite(cond).all():
        raise ValueError("Prepared coincidence inputs contain nonfinite values")

    # Geometric mean of per-scale joint coincidence, computed by direct
    # multiplication (NOT log-sum-exp with an additive epsilon): any scale
    # with a non-anomalous (zero) joint must force the combined score to
    # exactly zero, with no additive constant that could otherwise leave a
    # shared, non-zero tied rank for every pixel that is inactive at every
    # scale (that previously produced a large mid-percentile tied block for
    # the non-anomalous majority of the raster instead of the documented
    # zero floor; fixed before any result was interpreted for promotion).
    product = np.ones(fp.shape, dtype=np.float64)
    for sigma in SCALES_PIXELS:
        bg_sigma = BACKGROUND_FACTOR * sigma
        d_local = gaussian_filter(dilate, sigma=sigma, mode="nearest", truncate=4.0)
        d_bg = gaussian_filter(dilate, sigma=bg_sigma, mode="nearest", truncate=4.0)
        d_resid = np.clip(d_local - d_bg, 0, None)  # positive (extensional) only
        del d_local, d_bg

        c_local = gaussian_filter(cond, sigma=sigma, mode="nearest", truncate=4.0)
        c_bg = gaussian_filter(cond, sigma=bg_sigma, mode="nearest", truncate=4.0)
        c_resid = np.clip(c_local - c_bg, 0, None)  # positive (elevated) only
        del c_local, c_bg

        d_rank = percentile_rank(d_resid, support)
        c_rank = percentile_rank(c_resid, support)
        joint = np.sqrt(d_rank.astype(np.float64) * c_rank.astype(np.float64))
        # Zero out non-anomalous (zero-residual) pixels: a pixel that is
        # anomalous in neither field at this scale contributes an exact zero.
        joint[(d_resid <= 0) | (c_resid <= 0)] = 0
        product[support] *= joint[support]
        del d_resid, c_resid, d_rank, c_rank, joint

    n_scales = float(len(SCALES_PIXELS))
    raw = np.power(product, 1.0 / n_scales).astype(np.float32)
    raw[~support] = 0
    if not np.isfinite(raw[support]).all() or (raw[support] < 0).any() or (raw[support] > 1.00001).any():
        raise ValueError("DILCOND transform produced invalid scores")
    ranked = percentile_rank(raw, support)
    ranked[(~support) | (raw <= 0)] = 0
    metadata = {
        "method": "DILCOND-v1: sign-aware positive dilatation x positive conductivity local-anomaly coincidence",
        "input_bands_zero_based": {"geod_dilaterate": DILATERATE_BAND, "cond_surf": CONDUCTIVITY_BAND},
        "input_band_names_from_owner_mirror": ["geod_dilaterate", "cond_surf"],
        "input_band_data_category_from_embedded_gdal_tags": ["geodetic_strain", "subsurface"],
        "scales_sigma_pixels": list(SCALES_PIXELS),
        "scales_sigma_m_at_100m_grid": [s * 100 for s in SCALES_PIXELS],
        "background_sigma_factor": BACKGROUND_FACTOR,
        "gaussian_truncate_sigma": 4.0,
        "edge_halo_pixels": EDGE_HALO_PIXELS,
        "support_definition": "joint observed mask and footprint eroded by 48 px with 3x3 all-true structure",
        "residual_definition": "clip(gaussian(sigma) - gaussian(4*sigma), 0, None); positive-only, asymmetric by design",
        "joint_score": "sqrt(percentile_rank(dilation_residual+) * percentile_rank(conductivity_residual+)), zeroed where either residual is non-positive",
        "final_score": "geometric_mean(per_scale_joint) via direct product (exact zero if any scale is non-anomalous), then percentile-ranked on support",
        "support_pixels": int(support.sum()),
        "ranked_min": float(ranked[support].min()),
        "ranked_max": float(ranked[support].max()),
        "label_free_inputs_only": True,
        "caveat": "Elevated conductivity plus positive dilatation can equally reflect playa evaporite, irrigated soil moisture, perched groundwater or geodetic processing noise, not only a fluid-charged fault.",
    }
    return ranked.astype(np.float32), support, metadata
