import numpy as np
import pytest
torch=pytest.importorskip('torch')
from gems26.ssl import MaskedGeoEncoder,random_patch_mask,force_unseen_patches,masked_reconstruction_loss,complementary_mask,freeze,state_hash
from gems26.heads import fit_head


def test_75_percent_patch_mask_and_seed():
    a=random_patch_mask(2,16,16,4,.75,torch.Generator().manual_seed(2))
    b=random_patch_mask(2,16,16,4,.75,torch.Generator().manual_seed(2))
    assert torch.equal(a,b);assert torch.equal(a.sum((1,2,3)),torch.tensor([192,192]))
    assert torch.equal(a[:,:,0:4,0:4],a[:,:,0,0,None,None].expand(2,1,4,4))

def test_force_unseen_whole_patch():
    a=torch.zeros((1,1,16,16),dtype=torch.bool);unseen=a.clone();unseen[0,0,7,9]=True
    b=force_unseen_patches(a,unseen,4);assert b.sum()==16;assert b[0,0,4:8,8:12].all()

def test_complementary_hidden_three_times_and_global_halo_alignment():
    masks=[complementary_mask(20,20,i) for i in range(4)]
    assert torch.equal(sum(m.int() for m in masks),torch.full((1,1,20,20),3))
    for i in range(4):
        large=complementary_mask(40,40,i,row_origin=-16,col_origin=-16)
        assert torch.equal(large[:,:,16:36,16:36],masks[i])

def test_loss_excludes_missing_and_visible_targets():
    pred=torch.zeros((1,2,8,8),requires_grad=True);target=torch.ones_like(pred);obs=torch.ones_like(pred)
    obs[:,1]=0;mask=torch.zeros((1,1,8,8));mask[:,:,:4]=1
    loss=masked_reconstruction_loss(pred,target,obs,mask);assert loss.item()==pytest.approx(.5)
    loss.backward();assert pred.grad[:,1].abs().sum()==0;assert pred.grad[:,:,4:].abs().sum()==0
    pred2=torch.zeros_like(pred,requires_grad=True);zero=masked_reconstruction_loss(pred2,target,torch.zeros_like(obs),mask)
    zero.backward();assert zero.item()==0;assert pred2.grad.abs().sum()==0

def test_no_unmasked_skip_and_freeze():
    torch.manual_seed(4);model=MaskedGeoEncoder(channels=3)
    a=torch.zeros((1,3,16,16));b=a.clone();b[:,:,4:8,4:8]=999
    visible=torch.ones_like(a);visible[:,:,4:8,4:8]=0
    assert torch.equal(model(a,visible)[0],model(b,visible)[0])
    before=state_hash(model);freeze(model);assert not any(p.requires_grad for p in model.parameters())
    assert state_hash(model)==before

def test_only_head_optimizes_and_train_only_scaler():
    rng=np.random.default_rng(2);x=rng.normal(size=(100,5)).astype(np.float32);y=np.repeat([0,1],50)
    torch.set_num_threads(2)
    a,m,s,receipt=fit_head(x,y,2,epochs=2);b,m2,s2,r2=fit_head(x,y,2,epochs=2)
    assert state_hash(a)==state_hash(b);assert np.allclose(m,x.mean(axis=0));assert receipt['encoder_trainable_parameters']==0
    assert np.isfinite(receipt['losses']).all();assert np.array_equal(m,m2);assert np.array_equal(s,s2)
    with pytest.raises(ValueError):fit_head(x,np.zeros(100),2)

@pytest.mark.parametrize('args',[(1,16,16,0,.75),(0,16,16,4,.75),(1,0,16,4,.75),(1,16,16,-4,.75),(1,16,16,4,0),(1,16,16,4,1)])
def test_zero_or_invalid_mask_arguments(args):
    with pytest.raises(ValueError):random_patch_mask(*args)


def test_nan_missing_targets_cannot_poison_valid_loss_or_gradients():
    pred=torch.zeros((1,2,8,8),requires_grad=True);target=torch.ones_like(pred);observed=torch.ones_like(pred)
    observed[:,1]=0;target[:,1]=float('nan');masked=torch.ones((1,1,8,8))
    loss=masked_reconstruction_loss(pred,target,observed,masked);assert loss.item()==pytest.approx(.5)
    loss.backward();assert torch.isfinite(pred.grad).all();assert pred.grad[:,1].abs().sum()==0
    observed[:,0]=0;pred2=torch.full_like(pred,float('nan'),requires_grad=True)
    zero=masked_reconstruction_loss(pred2,target,observed,masked);zero.backward()
    assert zero.item()==0;assert torch.isfinite(pred2.grad).all()


def test_nan_hidden_input_never_reaches_encoder():
    model=MaskedGeoEncoder(channels=3);a=torch.zeros((1,3,16,16));b=a.clone();b[:,:,4:8,4:8]=float('nan')
    visible=torch.ones_like(a);visible[:,:,4:8,4:8]=0
    assert torch.equal(model(a,visible)[0],model(b,visible)[0])
    with pytest.raises(ValueError):complementary_mask(16,16,0,patch=0)


def test_float64_head_inputs_work_but_zero_epochs_do_not():
    x=np.arange(40,dtype=np.float64).reshape(8,5);y=np.tile([0,1],4)
    assert fit_head(x,y,2,epochs=1)[3]['epochs']==1
    with pytest.raises(ValueError):fit_head(x,y,2,epochs=0)
