import numpy as np
import pytest
from scipy.spatial.distance import pdist
from scipy.ndimage import binary_dilation
from gems26.emission import percentile_rank,ridge_nms,poisson_emit


def test_spacing_budget_and_deterministic_ties():
    a=np.ones((23,25));fp=np.ones_like(a,bool)
    p=poisson_emit(a,fp,80);assert p.sum()==80
    assert pdist(np.argwhere(p)).min()>=1.5
    assert np.array_equal(p,poisson_emit(a,fp,80))
    assert not poisson_emit(a,fp,0).any()

@pytest.mark.parametrize('distance',[0,-1,np.nan,np.inf])
def test_bad_spacing(distance):
    with pytest.raises(ValueError):poisson_emit(np.ones((9,9)),np.ones((9,9),bool),5,distance)

def test_empty_flat_ridge_and_rank():
    a=np.zeros((25,25));valid=np.ones_like(a,bool)
    assert not ridge_nms(a,valid).any();assert not poisson_emit(a,valid,9).any()
    assert not percentile_rank(a,np.zeros_like(valid)).any()
    a[5,5]=np.nan
    with pytest.raises(ValueError):percentile_rank(a,valid)

def test_support_halo_preserves_test_boundary_ridge():
    yy,xx=np.mgrid[:90,:90];score=np.exp(-((yy-44)/2)**2).astype(np.float32)
    all_support=np.ones(score.shape,bool);test=np.zeros_like(all_support);test[45:75,15:75]=True
    halo=binary_dilation(test,structure=np.ones((3,3)),iterations=16)
    expected=ridge_nms(score,all_support)&test
    actual=ridge_nms(np.where(halo,score,0),halo)&test
    assert np.array_equal(actual,expected)

def test_rank_monotone_and_ties():
    a=np.array([[5,5,9,1]],float);v=np.ones_like(a,bool)
    r=percentile_rank(a,v);assert r[0,0]==r[0,1];assert r[0,3]<r[0,0]<r[0,2]

@pytest.mark.parametrize('sigma',[np.inf,np.nan,0])
def test_invalid_ridge_sigma(sigma):
    with pytest.raises(ValueError):ridge_nms(np.ones((20,20)),np.ones((20,20),bool),sigma=sigma)
