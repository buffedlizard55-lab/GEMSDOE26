"""Label-free, preregistered cross-scale magnetic/gravity edge agreement."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter

from .emission import percentile_rank

# Zero-based positions in the owner-mirror band order documented in the
# preparation receipt. These aliases are not organizer-authenticated metadata.
MAG_RTP_BAND = 1
GRAV_ISOSTATIC_BAND = 12
SCALES_PIXELS = (3.0, 6.0, 12.0)  # 100 m cells: sigma = 300, 600, 1,200 m
EDGE_HALO_PIXELS = 4 * int(SCALES_PIXELS[-1])


def _binary_grid(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not array.size or array.dtype.kind not in "biuf":
        raise ValueError(f"Nonempty two-dimensional {name} required")
    if array.dtype != np.dtype(bool) and not np.isin(array, [0, 1]).all():
        raise ValueError(f"Finite binary {name} required")
    return array.astype(bool, copy=False)


def build_xedge_score(values: np.ndarray, observed: np.ndarray, footprint: np.ndarray
                      ) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return a ranked XEDGE feature, its valid support, and fixed metadata.

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
    for band, label in ((MAG_RTP_BAND, "RTP magnetic"),
                        (GRAV_ISOSTATIC_BAND, "isostatic gravity")):
        valid = fp & obs[band]
        if not valid.any() or not np.isfinite(x[band][valid]).all():
            raise ValueError(f"{label} band has no finite valid observations")

    input_valid = fp & obs[MAG_RTP_BAND] & obs[GRAV_ISOSTATIC_BAND]
    support = binary_erosion(input_valid, structure=np.ones((3, 3), dtype=bool),
                             iterations=EDGE_HALO_PIXELS, border_value=0)
    if not support.any():
        raise ValueError("XEDGE has no support after fixed 4-sigma footprint/nodata erosion")

    magnetic = np.array(x[MAG_RTP_BAND], dtype=np.float32, copy=True)
    gravity = np.array(x[GRAV_ISOSTATIC_BAND], dtype=np.float32, copy=True)
    magnetic[~(fp & obs[MAG_RTP_BAND])] = 0
    gravity[~(fp & obs[GRAV_ISOSTATIC_BAND])] = 0
    if not np.isfinite(magnetic).all() or not np.isfinite(gravity).all():
        raise ValueError("Prepared edge inputs contain nonfinite values")

    log_joint = np.zeros(fp.shape, dtype=np.float32)
    m_cos2 = np.zeros(fp.shape, dtype=np.float32)
    m_sin2 = np.zeros(fp.shape, dtype=np.float32)
    g_cos2 = np.zeros(fp.shape, dtype=np.float32)
    g_sin2 = np.zeros(fp.shape, dtype=np.float32)
    for sigma in SCALES_PIXELS:
        m_smooth = gaussian_filter(magnetic, sigma=sigma, mode="nearest", truncate=4.0)
        m_y, m_x = np.gradient(m_smooth)
        del m_smooth
        g_smooth = gaussian_filter(gravity, sigma=sigma, mode="nearest", truncate=4.0)
        g_y, g_x = np.gradient(g_smooth)
        del g_smooth

        m_norm = np.hypot(m_x, m_y)
        g_norm = np.hypot(g_x, g_y)
        m_rank = percentile_rank(m_norm, support)
        g_rank = percentile_rank(g_norm, support)
        alignment = np.abs(m_x * g_x + m_y * g_y) / (m_norm * g_norm + 1e-6)
        np.clip(alignment, 0, 1, out=alignment)
        joint = np.sqrt(m_rank * g_rank) * alignment
        log_joint[support] += np.log(joint[support] + 1e-6)

        m_den = np.maximum(m_norm, 1e-12)
        g_den = np.maximum(g_norm, 1e-12)
        m_ux, m_uy = m_x / m_den, m_y / m_den
        g_ux, g_uy = g_x / g_den, g_y / g_den
        m_cos2 += m_ux * m_ux - m_uy * m_uy
        m_sin2 += 2 * m_ux * m_uy
        g_cos2 += g_ux * g_ux - g_uy * g_uy
        g_sin2 += 2 * g_ux * g_uy
        del m_x, m_y, g_x, g_y, m_norm, g_norm, m_rank, g_rank
        del alignment, joint, m_den, g_den, m_ux, m_uy, g_ux, g_uy

    n_scales = float(len(SCALES_PIXELS))
    m_persistence = np.hypot(m_cos2 / n_scales, m_sin2 / n_scales)
    g_persistence = np.hypot(g_cos2 / n_scales, g_sin2 / n_scales)
    raw = np.exp(log_joint / n_scales) * np.sqrt(m_persistence * g_persistence)
    raw[~support] = 0
    if not np.isfinite(raw[support]).all() or (raw[support] < 0).any() or (raw[support] > 1.00001).any():
        raise ValueError("XEDGE transform produced invalid scores")
    ranked = percentile_rank(raw, support)
    # Tied zero-valued regions are not evidence and must not become a .5
    # pseudo-signal (or arbitrary top-K emissions) through average-rank ties.
    ranked[(~support) | (raw <= 0)] = 0
    metadata = {
        "method": "XEDGE-v1: signed cross-modal edge-normal agreement with cross-scale line persistence",
        "input_bands_zero_based": {"magnetic_rtp": MAG_RTP_BAND,
                                    "isostatic_gravity": GRAV_ISOSTATIC_BAND},
        "input_band_names_from_owner_mirror_not_organizer_authentication": ["rtp", "iso_grav_anom"],
        "scales_sigma_pixels": list(SCALES_PIXELS),
        "scales_sigma_m_at_100m_grid": [s * 100 for s in SCALES_PIXELS],
        "gaussian_truncate_sigma": 4.0,
        "edge_halo_pixels": EDGE_HALO_PIXELS,
        "support_definition": "joint observed mask and footprint eroded by 48 px with 3x3 all-true structure",
        "cross_modal_alignment": "abs(dot(g_mag,g_grav))/(norm(g_mag)*norm(g_grav)+1e-6)",
        "scale_agreement": "geometric mean of per-scale sqrt(percentile_rank(|g_mag|)*percentile_rank(|g_grav|))*alignment",
        "orientation_persistence": "resultant length of mean doubled-angle unit gradient vectors, separately per field",
        "final_score": "exp(mean(log(per_scale_joint+1e-6)))*sqrt(R_mag*R_gravity), then percentile-ranked on support",
        "support_pixels": int(support.sum()),
        "ranked_min": float(ranked[support].min()),
        "ranked_max": float(ranked[support].max()),
        "label_free_inputs_only": True,
        "caveat": "Potential-field edges also mark contacts, intrusions, interpolation boundaries and survey artefacts; not a fault probability.",
    }
    return ranked.astype(np.float32), support, metadata
