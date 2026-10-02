import numpy as np
import pytest
from gems26.metric import dti,pooled,binary_coordinate_components


def brute(p,g,valid=None):
    mask=np.ones(p.shape,bool) if valid is None else valid
    pc=np.argwhere(mask&(p>0));gc=np.argwhere(mask&(g>0))
    t=0.;f=0.
    for x in gc:
        t+=max([max(1-np.linalg.norm(x-z)/3,0)*p[tuple(z)] for z in pc] or [0])
    for z in pc:
        k=max([max(1-np.linalg.norm(z-x)/3,0) for x in gc] or [0])
        f+=p[tuple(z)]*(1-k)
    den=.2*(t+f)+.8*len(gc)
    return t,f,t/den if den else 0

@pytest.mark.parametrize('soft',[False,True])
def test_bruteforce_probability_kernel(soft):
    rng=np.random.default_rng(25);p=rng.uniform(size=(8,9));g=rng.uniform(size=p.shape)>.75
    if not soft:p=p>.6
    valid=rng.uniform(size=p.shape)>.2
    a=dti(p,g,valid);t,f,s=brute(p,g,valid)
    assert a['TP_w']==pytest.approx(t);assert a['FP_w']==pytest.approx(f);assert a['dti']==pytest.approx(s)

@pytest.mark.parametrize('offset,credit',[(0,1),(1,2/3),(2,1/3),(3,0),(4,0)])
def test_triangular_three_pixel_support(offset,credit):
    p=np.zeros((9,9));g=np.zeros_like(p);p[4,4+offset]=1;g[4,4]=1
    a=dti(p,g);assert a['TP_w']==pytest.approx(credit);assert a['FP_w']==pytest.approx(1-credit)

def test_empty_and_perfect():
    z=np.zeros((7,8));assert dti(z,z)['dti']==0
    g=z.copy();g[3,3]=1;assert dti(g,g)['dti']==1;assert dti(z,g)['dti']==0
    assert dti(g,z)['FP_w']==1

def test_known_mask_and_outside_nan():
    p=np.zeros((5,5));g=p.copy();g[2,2]=1;p[2,2]=1
    known=g.astype(bool);assert dti(p,g,known=known)['n_truth']==0
    valid=np.ones_like(known);valid[0,0]=False;p[0,0]=np.nan
    assert dti(p,g,valid)['dti']==1

@pytest.mark.parametrize('value',[-.1,1.001,np.inf,np.nan])
def test_invalid_inside_prediction(value):
    a=np.zeros((4,4));a[1,1]=value
    with pytest.raises(ValueError):dti(a,np.zeros_like(a))

def test_tp_plus_fp_not_emitted_count():
    p=np.zeros((7,7));g=np.zeros_like(p);p[3,3]=1;g[2:5,3]=1
    a=dti(p,g);assert a['TP_w']>a['n_emitted'];assert a['TP_w']+a['FP_w']!=a['n_emitted']

def test_uniform_probability_downscale_cannot_help():
    p=np.zeros((9,9));g=np.zeros_like(p);p[4,4]=1;p[0,0]=1;g[4,5]=1
    assert dti(.5*p,g)['dti']<dti(p,g)['dti']

def test_pooled_is_not_fold_mean():
    a=np.zeros((8,8));a[3,3]=1
    b=np.zeros_like(a);b[2:5,2:5]=1
    results=[dti(a,a),dti(np.zeros_like(b),b)]
    result=pooled(results)
    assert result['n_truth']==10;assert result['dti']!=np.mean([r['dti'] for r in results])
