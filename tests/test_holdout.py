import numpy as np
import pytest
from scipy.ndimage import label
from gems26.holdout import quadrant_folds,train_sample,promotion_gate


def test_whole_component_and_buffer_exclusion():
    fp=np.ones((140,140),bool);folds=quadrant_folds(fp);fault=np.zeros_like(fp)
    fault[25,10:135]=True;fault[100,10:40]=True;fault[110,90:125]=True
    components,_=label(fault,structure=np.ones((3,3)))
    ids,y,receipt=train_sample(fault,fp,folds,components,0,123,max_positive=100,max_negative=200)
    assert not ((folds.ravel()[ids])==0).any();assert receipt['minimum_train_test_gap_pixels']>15
    touching=np.unique(components[(folds==0)&fault]);assert not np.isin(components.ravel()[ids[y==1]],touching).any()
    assert receipt['train_positive_test_component_overlap']==0

def fake(primary_sparse=.11,raw=.1,h25=.1,primary_dense=.2):
    tags={'ssl_fusion':primary_sparse,'raw_head':raw,'h25_reference':h25}
    return {'sparse':{k:{'mean_pooled_dti':v,'fold_mean_dti':[v]*4} for k,v in tags.items()},'dense':{k:{'pooled':{'dti':primary_dense if k=='ssl_fusion' else .2}} for k in tags}}

def test_gate_requires_both_stages_comparators_folds_and_dense():
    a=fake();assert promotion_gate(a,a)['holdout_pass']
    b=fake(primary_sparse=.09);assert not promotion_gate(a,b)['holdout_pass']
    b=fake(primary_dense=.19);assert not promotion_gate(a,b)['holdout_pass']
    b=fake();b['sparse']['ssl_fusion']['fold_mean_dti']=[.2,.2,.09,.09]
    assert not promotion_gate(a,b)['holdout_pass']
    assert not promotion_gate(a,b)['weekly_slot_spent'];assert not promotion_gate(a,b)['hidden_fault_validation']

def test_degenerate_quadrants_refused():
    with pytest.raises(ValueError):quadrant_folds(np.zeros((5,5),bool))
    with pytest.raises(ValueError):quadrant_folds(np.ones((1,5),bool))
