from pathlib import Path
import json
from gems26.common import ROOT,sha256_file


def load(name):return json.loads((ROOT/name).read_text())

def test_frozen_failed_gate_and_timestamps():
    h=load('evidence/holdout.json');p=load('evidence/pretraining.json');r=load('evidence/representation.json');a=load('evidence/anomaly.json')
    assert p['completed_utc']<h['started_label_access_utc'];assert r['completed_utc']<h['started_label_access_utc'];assert a['completed_utc']<h['started_label_access_utc']
    assert h['label_access_after_ssl_and_anomaly'];assert h['encoder_state_before']==h['encoder_state_after']
    assert h['gate']['decision']=='BLOCKED_DO_NOT_SUBMIT';assert not h['gate']['holdout_pass'];assert not h['gate']['weekly_slot_spent']
    assert sha256_file(ROOT/'knowledge/preregistration.md')==h['preregistration_sha256']
    assert p['coverage_pass'] and r['coverage_pass'];assert p['all_channels']==19
    assert not p['labels_opened'];assert not r['labels_opened']

def test_historical_identity_and_non_discovery():
    f=load('evidence/reference_forensics.json')
    assert f['exact_recomputed_pixel_identity'];assert f['reference_adds_no_pixel'];assert f['reference_pixels']==60069
    assert not f['algorithm_reads_labels'];assert not f['score_to_file_mapping_verified_by_platform_receipt']

def test_score_history_scope():
    s=load('sources/reported_scores.json');r=load('evidence/sibling_site_review.json')
    assert not s['platform_receipts_accessed'];assert len(r['rows'])==24;assert r['reviewed_sibling_count']==24
    assert sum(x['score'] is not None for x in s['rows'])==32
    assert max(x['score'] for x in s['rows'] if x['score'] is not None)==.2477
    for row in r['rows']:assert len(row['source_commit'])==40;assert len(row['source_sha256'])==64

def test_claims_have_clear_status_and_sources():
    sources=load('sources/catalog.json')['sources'];claims=load('sources/claims.json')['claims'];ids={r['id'] for r in sources}
    assert len(ids)==len(sources)
    for c in claims:
        assert c['status'];assert c['claim'];assert set(c['sources'])<=ids
        if c.get('evidence'):assert (ROOT/c['evidence'].split('#')[0]).is_file()
        if c.get('implementation'):assert (ROOT/c['implementation']).is_file()
