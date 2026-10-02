import ast
from pathlib import Path

import numpy as np
import pytest

from gems26.xedge import build_xedge_score


def step_stack(size=256, crossed=False):
    yy, xx = np.mgrid[:size, :size]
    x = np.zeros((19, size, size), dtype=np.float32)
    x[1] = (xx >= size // 2).astype(np.float32)
    x[12] = ((yy >= size // 2) if crossed else (xx >= size // 2)).astype(np.float32)
    observed = np.ones_like(x, dtype=np.uint8)
    footprint = np.ones((size, size), dtype=np.uint8)
    return x, observed, footprint


def test_xedge_finds_aligned_cross_scale_step_and_never_mutates_inputs():
    values, observed, footprint = step_stack()
    original = values.copy()
    ranked, support, metadata = build_xedge_score(values, observed, footprint)
    assert np.array_equal(values, original)
    assert ranked.dtype == np.float32
    assert np.isfinite(ranked).all()
    assert ranked.min() == 0 and ranked.max() <= 1
    assert support.sum() == (256 - 2 * 48) ** 2
    assert (ranked[~support] == 0).all()
    yy, xx = np.mgrid[:256, :256]
    edge = support & (np.abs(xx - 128) <= 4)
    background = support & (np.abs(xx - 128) >= 24)
    assert ranked[edge].mean() > ranked[background].mean()
    assert metadata["input_bands_zero_based"] == {"magnetic_rtp": 1, "isostatic_gravity": 12}
    assert metadata["support_pixels"] == int(support.sum())


def test_xedge_requires_cross_modal_orientation_agreement():
    aligned, observed, footprint = step_stack(crossed=False)
    crossed, _, _ = step_stack(crossed=True)
    aligned_rank, support, _ = build_xedge_score(aligned, observed, footprint)
    crossed_rank, crossed_support, _ = build_xedge_score(crossed, observed, footprint)
    common = support & crossed_support
    assert common.any()
    assert aligned_rank[common].mean() > crossed_rank[common].mean()


def test_xedge_zero_signal_stays_zero_not_an_average_rank_tie():
    values = np.zeros((19, 192, 192), dtype=np.float32)
    observed = np.ones_like(values, dtype=np.uint8)
    footprint = np.ones((192, 192), dtype=np.uint8)
    ranked, support, _ = build_xedge_score(values, observed, footprint)
    assert support.any()
    assert np.isfinite(ranked).all()
    assert (ranked[support] == 0).all()


def test_xedge_rejects_partial_or_malformed_inputs():
    values, observed, footprint = step_stack()
    with pytest.raises(ValueError, match="19 aligned"):
        build_xedge_score(values[:18], observed[:18], footprint)
    with pytest.raises(ValueError, match="binary"):
        build_xedge_score(values, observed, np.full_like(footprint, 2))
    bad = values.copy()
    bad[1, 100, 100] = np.nan
    with pytest.raises(ValueError, match="finite valid observations"):
        build_xedge_score(bad, observed, footprint)
    no_support = np.zeros_like(footprint)
    with pytest.raises(ValueError, match="no valid pixels"):
        build_xedge_score(values, observed, no_support)


def test_xedge_builder_has_no_label_or_template_path_access():
    tree = ast.parse(Path("scripts/build_xedge.py").read_text())
    strings = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    forbidden = ("labels.tif", "sample_submission.tif", "label_values", "template_values")
    assert not any(token in value for token in forbidden for value in strings)
