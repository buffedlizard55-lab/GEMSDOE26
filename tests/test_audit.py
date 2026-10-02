import numpy as np
import pytest

import gems26.audit as audit
from gems26.holdout import quadrant_folds


class ConstantNuisanceModel:
    def __init__(self, **kwargs):
        pass

    def fit(self, x, y):
        return self

    def predict_proba(self, x):
        return np.tile(np.array([[0.5, 0.5]]), (len(x), 1))


def test_audit_accepts_explicit_candidate_name_and_audits_labels_first(monkeypatch):
    rng = np.random.default_rng(714)
    fp = np.ones((160, 160), dtype=bool)
    labels = rng.random(fp.shape) < 0.3
    historical = rng.random(fp.shape) < 0.2
    candidate = rng.random(fp.shape) < 0.25
    folds = quadrant_folds(fp)
    n = int(fp.sum())
    monkeypatch.setattr(audit, "HistGradientBoostingClassifier", ConstantNuisanceModel)
    monkeypatch.setattr(audit, "load_nuisances", lambda _fp: (
        np.zeros((n, 6), dtype=np.float32), np.flatnonzero(fp), {"source_integrity_only": True}))
    result = audit.audit_targets(labels, {"h25_reference": historical, "xedge_head": candidate},
                                 fp, folds, primary="xedge_head")
    assert result["complete"]
    assert result["labels_audited_first"]
    assert result["events"][0]["target"] == "labels"
    assert result["reference_target"] == "h25_reference"
    assert result["primary_target"] == "xedge_head"
    assert set(result["results"]) == {"labels", "h25_reference", "xedge_head"}


def test_audit_rejects_prediction_alias_and_nonbinary_grid():
    fp = np.ones((4, 4), dtype=bool)
    folds = np.zeros((4, 4), dtype=np.int8)
    labels = np.zeros((4, 4), dtype=np.uint8)
    valid = np.zeros((4, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="Distinct label"):
        audit.audit_targets(labels, {"labels": valid, "h25_reference": valid, "xedge": valid},
                           fp, folds, reference="h25_reference", primary="xedge")
    with pytest.raises(ValueError, match="binary grid"):
        audit.audit_targets(labels, {"h25_reference": valid, "xedge": np.full((4, 4), 2)},
                           fp, folds, reference="h25_reference", primary="xedge")
