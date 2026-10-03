import ast
from pathlib import Path

import numpy as np
import pytest

from gems26.strain import build_srcoh_feature


def synthetic_stack(size=256, crossed=False, polarity=1.0):
    yy, xx = np.mgrid[:size, :size]
    values = np.zeros((19, size, size), dtype=np.float32)
    values[3] = polarity * (xx >= size // 2)
    values[6] = polarity * ((yy >= size // 2) if crossed else (xx >= size // 2))
    values[7] = polarity * (xx >= size // 2)
    observed = np.ones(values.shape, dtype=np.uint8)
    footprint = np.ones((size, size), dtype=np.uint8)
    return values, observed, footprint


def test_srcoh_aligns_three_strain_edges_across_scales_and_is_nonmutating():
    values, observed, footprint = synthetic_stack()
    before = values.copy()
    ranked, support, metadata = build_srcoh_feature(values, observed, footprint)
    assert np.array_equal(values, before)
    assert ranked.dtype == np.float32
    assert np.isfinite(ranked).all()
    assert ranked.min() == 0 and ranked.max() <= 1
    assert support.sum() == (256 - 2 * 48) ** 2
    assert (ranked[~support] == 0).all()
    yy, xx = np.mgrid[:256, :256]
    edge = support & (np.abs(xx - 128) <= 8)
    background = support & (np.abs(xx - 128) >= 32)
    assert ranked[edge].mean() > ranked[background].mean()
    assert metadata["input_bands_zero_based"] == [3, 6, 7]
    assert metadata["support_pixels"] == int(support.sum())


def test_srcoh_penalizes_crossed_channel_normals():
    aligned, observed, footprint = synthetic_stack(crossed=False)
    crossed, _, _ = synthetic_stack(crossed=True)
    aligned_rank, support, _ = build_srcoh_feature(aligned, observed, footprint)
    crossed_rank, crossed_support, _ = build_srcoh_feature(crossed, observed, footprint)
    common = support & crossed_support
    assert common.any()
    assert aligned_rank[common].mean() > crossed_rank[common].mean()


def test_srcoh_zero_gradient_stays_exactly_zero():
    values = np.zeros((19, 192, 192), dtype=np.float32)
    observed = np.ones_like(values, dtype=np.uint8)
    footprint = np.ones((192, 192), dtype=np.uint8)
    ranked, support, metadata = build_srcoh_feature(values, observed, footprint)
    assert support.any()
    assert np.isfinite(ranked).all()
    assert (ranked == 0).all()
    assert metadata["raw_zero_pixels_on_support"] == int(support.sum())


def test_srcoh_ignores_unobserved_values_and_unselected_channels():
    values, observed, footprint = synthetic_stack()
    observed[[3, 6, 7], :, 128] = 0
    values[[3, 6, 7], :, 128] = 9999
    baseline = values.copy()
    ranked_a, support_a, _ = build_srcoh_feature(values, observed, footprint)
    values[[3, 6, 7], :, 128] = -9999
    values[[0, 1, 2, 4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]] = 12345
    ranked_b, support_b, _ = build_srcoh_feature(values, observed, footprint)
    assert np.array_equal(values[[3, 6, 7], :, 128], np.full((3, 256), -9999))
    assert np.array_equal(support_a, support_b)
    assert np.array_equal(ranked_a, ranked_b)
    assert not np.array_equal(values, baseline)


def test_srcoh_is_invariant_to_gradient_polarity():
    positive, observed, footprint = synthetic_stack(polarity=1)
    negative, _, _ = synthetic_stack(polarity=-1)
    a, support, _ = build_srcoh_feature(positive, observed, footprint)
    b, other_support, _ = build_srcoh_feature(negative, observed, footprint)
    assert np.array_equal(support, other_support)
    np.testing.assert_allclose(a, b, rtol=1e-6, atol=1e-7)


def test_srcoh_rejects_malformed_grids_and_masks():
    values, observed, footprint = synthetic_stack()
    with pytest.raises(ValueError, match="19 aligned"):
        build_srcoh_feature(values[:18], observed[:18], footprint)
    with pytest.raises(ValueError, match="binary"):
        build_srcoh_feature(values, observed, np.full_like(footprint, 2))
    bad_mask = observed.copy()
    bad_mask[3, 1, 1] = 2
    with pytest.raises(ValueError, match="binary"):
        build_srcoh_feature(values, bad_mask, footprint)
    bad_values = values.copy()
    bad_values[6, 100, 100] = np.nan
    with pytest.raises(ValueError, match="finite valid observations"):
        build_srcoh_feature(bad_values, observed, footprint)
    with pytest.raises(ValueError, match="no valid pixels"):
        build_srcoh_feature(values, observed, np.zeros_like(footprint))
    tiny = np.ones((19, 96, 96), dtype=np.float32)
    with pytest.raises(ValueError, match="no support"):
        build_srcoh_feature(tiny, np.ones_like(tiny, dtype=np.uint8), np.ones((96, 96), bool))


def test_h27_feature_builder_has_no_label_or_template_file_path():
    tree = ast.parse(Path("scripts/build_h27_srcoh.py").read_text())
    strings = [node.value for node in ast.walk(tree)
               if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    forbidden = ("labels.tif", "sample_submission.tif", "label_values", "template_values")
    assert not any(token in value for token in forbidden for value in strings)
    assert "rasterio" not in {alias.name for node in ast.walk(tree)
                              if isinstance(node, ast.Import) for alias in node.names}
