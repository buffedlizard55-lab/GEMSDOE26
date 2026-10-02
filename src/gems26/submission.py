"""Fail-closed exact-template GeoTIFF export and independent roundtrip validation."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio

from .common import CRS, GRID_TRANSFORM, HEIGHT, WIDTH, sha256_file


def valid_footprint(fp: np.ndarray) -> np.ndarray:
    mask = np.asarray(fp)
    if mask.ndim != 2 or not mask.size or mask.dtype.kind not in "biuf":
        raise ValueError("Nonempty 2D binary footprint required")
    if mask.dtype != np.dtype(bool) and not np.isin(mask, [0, 1]).all():
        raise ValueError("Finite binary footprint required")
    mask = mask.astype(bool, copy=False)
    if not mask.any():
        raise ValueError("Footprint has no valid pixels")
    return mask


def valid_prediction(pred: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mask = valid_footprint(fp)
    original = np.asarray(pred)
    if original.shape != mask.shape or original.dtype.kind not in "biuf":
        raise ValueError("Aligned real-valued prediction grid required")
    inside = original[mask]
    # Validate BEFORE float32 quantization: a tiny illegal overshoot must not
    # silently round to 1, and a tiny negative must not round to -0.
    if not np.isfinite(inside).all() or ((inside < 0) | (inside > 1)).any():
        raise ValueError("Invalid finite in-footprint [0,1] predictions")
    return original.astype(np.float32, copy=False), mask


def prediction_digest(pred: np.ndarray, fp: np.ndarray) -> str:
    a, fp = valid_prediction(pred, fp)
    canonical = np.where(fp, a, 0).astype("<f4")
    h = hashlib.sha256()
    h.update(np.asarray(a.shape, dtype="<u4").tobytes())
    h.update(np.packbits(fp.ravel(), bitorder="little").tobytes())
    h.update(canonical.tobytes())
    return h.hexdigest()


def validate_submission(path: str | Path, template: str | Path, fp: np.ndarray,
                        *, expected_digest: str | None = None) -> dict:
    fp = valid_footprint(fp)
    with rasterio.open(template) as t:
        if (t.count != 1 or t.shape != (HEIGHT, WIDTH) or t.crs is None or
                t.crs.to_epsg() != 32611 or t.transform != GRID_TRANSFORM):
            raise ValueError("Template itself is not the pinned competition grid")
        template_fp = np.isfinite(t.read(1))
        if template_fp.shape != fp.shape or not np.array_equal(template_fp, fp):
            raise ValueError("Footprint differs from supplied template")
        grid = (t.shape, t.crs, t.transform)
    checks = {}
    with rasterio.open(path) as d:
        checks["single_band"] = d.count == 1
        checks["float32"] = d.dtypes == ("float32",)
        checks["shape_matches_template"] = d.shape == grid[0]
        checks["crs_matches_template"] = d.crs == grid[1]
        checks["transform_matches_template"] = d.transform == grid[2]
        checks["nodata_is_nan"] = d.nodata is not None and bool(np.isnan(d.nodata))
        if d.count != 1 or d.shape != fp.shape:
            return {"format_pass": False, "checks": checks, "path": str(path), "sha256": sha256_file(path)}
        a = d.read(1)
        inside = a[fp]
        outside = a[~fp]
        checks["all_inside_finite"] = bool(np.isfinite(inside).all())
        checks["inside_range_0_1"] = bool(((inside >= 0) & (inside <= 1)).all())
        checks["outside_all_nan"] = bool(np.isnan(outside).all())
        # Do not trust a nodata mask that could hide negative/out-of-range in-footprint values.
        compressed = d.read(1, masked=True).compressed()
        checks["masked_read_range_0_1"] = bool(np.isfinite(compressed).all() and
                                               ((compressed >= 0) & (compressed <= 1)).all())
        checks["masked_read_has_all_footprint_values"] = compressed.size == int(fp.sum())
    digest = prediction_digest(a, fp) if checks["all_inside_finite"] and checks["inside_range_0_1"] else None
    if expected_digest is not None:
        checks["prediction_digest_matches"] = digest == expected_digest
    return {"format_pass": bool(all(checks.values())), "checks": checks,
            "path": str(path), "sha256": sha256_file(path), "prediction_sha256": digest,
            "bytes": Path(path).stat().st_size, "inside_pixels": int(fp.sum()),
            "outside_pixels": int((~fp).sum()), "inside_finite": int(np.isfinite(inside).sum()),
            "inside_min": float(inside.min()) if np.isfinite(inside).all() else None,
            "inside_max": float(inside.max()) if np.isfinite(inside).all() else None,
            "positive_pixels": int((inside > 0).sum()), "mass": float(inside.astype(np.float64).sum()) if np.isfinite(inside).all() else None,
            "scientific_release": "Separate from format; consult holdout and audit receipts"}


def write_submission(pred: np.ndarray, fp: np.ndarray, template: str | Path,
                     directory: str | Path, method: str, date: str = "20261002") -> tuple[Path, dict]:
    a, fp = valid_prediction(pred, fp)
    if a.shape != (HEIGHT, WIDTH):
        raise ValueError("Wrong competition shape")
    digest = prediction_digest(a, fp)  # rejects invalid inputs; does NOT silently clip
    if not isinstance(method, str) or not method or len(method) > 80 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in method):
        raise ValueError("Use a safe method slug")
    if not isinstance(date, str) or not re.fullmatch(r"\d{8}", date):
        raise ValueError("Use a YYYYMMDD date, never a path")
    datetime.strptime(date, "%Y%m%d")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"gems26-{method}-{date}-{digest[:12]}-nan.tif"
    tmp = path.with_suffix(".partial")
    try:
        profile = dict(driver="GTiff", height=HEIGHT, width=WIDTH, count=1, dtype="float32",
                       crs=CRS, transform=GRID_TRANSFORM, nodata=np.nan,
                       compress="deflate", predictor=3, tiled=True, blockxsize=256, blockysize=256)
        with rasterio.open(tmp, "w", **profile) as dst:
            dst.write(np.where(fp, a, np.nan).astype(np.float32), 1)
            dst.update_tags(AREA_OR_POINT="Area", METHOD=method, PREDICTION_SHA256=digest,
                            STATUS="Unscored; scientific release gate is recorded separately")
        receipt = validate_submission(tmp, template, fp, expected_digest=digest)
        if not receipt["format_pass"]:
            raise ValueError("Export roundtrip failed: " + str(receipt["checks"]))
        tmp.replace(path)
        receipt["path"] = str(path)
        return path, receipt
    finally:
        tmp.unlink(missing_ok=True)
