import ast
from pathlib import Path

import numpy as np
import pytest

from gems26.dilcond import build_dilcond_score


def coincidence_stack(size=256, both_positive=True, anti_correlated=False):
    yy, xx = np.mgrid[:size, :size]
    x = np.zeros((19, size, size), dtype=np.float32)
    blob = (((yy - size // 2) ** 2 + (xx - size // 2) ** 2) < (size // 6) ** 2).astype(np.float32)
    x[7] = blob  # geod_dilaterate: positive dilatation in the blob
    if anti_correlated:
        x[16] = 1.0 - blob  # cond_surf anomaly is ELSEWHERE, not coincident
    elif both_positive:
        x[16] = blob  # cond_surf: elevated conductivity in the SAME blob
    observed = np.ones_like(x, dtype=np.uint8)
    footprint = np.ones((size, size), dtype=np.uint8)
    return x, observed, footprint


def test_dilcond_finds_coincident_positive_anomaly_and_never_mutates_inputs():
    values, observed, footprint = coincidence_stack()
    original = values.copy()
    ranked, support, metadata = build_dilcond_score(values, observed, footprint)
    assert np.array_equal(values, original)
    assert ranked.dtype == np.float32
    assert np.isfinite(ranked).all()
    assert ranked.min() == 0 and ranked.max() <= 1
    assert (ranked[~support] == 0).all()
    size = 256
    yy, xx = np.mgrid[:size, :size]
    center = support & (((yy - size // 2) ** 2 + (xx - size // 2) ** 2) < (size // 10) ** 2)
    background = support & (((yy - size // 2) ** 2 + (xx - size // 2) ** 2) > (size // 3) ** 2)
    assert center.any() and background.any()
    assert ranked[center].mean() > ranked[background].mean()
    assert metadata["input_bands_zero_based"] == {"geod_dilaterate": 7, "cond_surf": 16}
    assert metadata["support_pixels"] == int(support.sum())


def test_dilcond_requires_sign_aware_coincidence_not_just_either_anomaly():
    coincident, observed, footprint = coincidence_stack(both_positive=True)
    disjoint, _, _ = coincidence_stack(both_positive=True, anti_correlated=True)
    coincident_rank, support, _ = build_dilcond_score(coincident, observed, footprint)
    disjoint_rank, disjoint_support, _ = build_dilcond_score(disjoint, observed, footprint)
    common = support & disjoint_support
    assert common.any()
    assert coincident_rank[common].mean() > disjoint_rank[common].mean()


def test_dilcond_negative_dilatation_does_not_score_even_with_elevated_conductivity():
    size = 256
    yy, xx = np.mgrid[:size, :size]
    x = np.zeros((19, size, size), dtype=np.float32)
    blob = (((yy - size // 2) ** 2 + (xx - size // 2) ** 2) < (size // 6) ** 2).astype(np.float32)
    x[7] = -blob  # compressional (negative) dilatation, not extensional
    x[16] = blob  # elevated conductivity
    observed = np.ones_like(x, dtype=np.uint8)
    footprint = np.ones((size, size), dtype=np.uint8)
    ranked, support, _ = build_dilcond_score(x, observed, footprint)
    center = support & (((yy - size // 2) ** 2 + (xx - size // 2) ** 2) < (size // 10) ** 2)
    assert center.any()
    assert (ranked[center] == 0).all()


def test_dilcond_zero_signal_stays_zero_not_an_average_rank_tie():
    values = np.zeros((19, 192, 192), dtype=np.float32)
    observed = np.ones_like(values, dtype=np.uint8)
    footprint = np.ones((192, 192), dtype=np.uint8)
    ranked, support, _ = build_dilcond_score(values, observed, footprint)
    assert support.any()
    assert np.isfinite(ranked).all()
    assert (ranked[support] == 0).all()


def test_dilcond_rejects_partial_or_malformed_inputs():
    values, observed, footprint = coincidence_stack()
    with pytest.raises(ValueError, match="19 aligned"):
        build_dilcond_score(values[:18], observed[:18], footprint)
    with pytest.raises(ValueError, match="binary"):
        build_dilcond_score(values, observed, np.full_like(footprint, 2))
    bad = values.copy()
    bad[7, 100, 100] = np.nan
    with pytest.raises(ValueError, match="finite valid observations"):
        build_dilcond_score(bad, observed, footprint)
    no_support = np.zeros_like(footprint)
    with pytest.raises(ValueError, match="no valid pixels"):
        build_dilcond_score(values, observed, no_support)


def test_dilcond_builder_has_no_label_or_template_path_access():
    tree = ast.parse(Path("scripts/build_dilcond.py").read_text())
    strings = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    forbidden = ("labels.tif", "sample_submission.tif", "label_values", "template_values")
    assert not any(token in value for token in forbidden for value in strings)
