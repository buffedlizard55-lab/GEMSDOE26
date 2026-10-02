import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine
from gems26 import submission as s


@pytest.fixture
def grid(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'HEIGHT',9);monkeypatch.setattr(s,'WIDTH',11)
    fp=np.zeros((9,11),bool);fp[2:7,2:9]=True
    profile=dict(driver='GTiff',height=9,width=11,count=1,dtype='float32',crs='EPSG:32611',transform=s.GRID_TRANSFORM,nodata=np.nan)
    path=tmp_path/'template.tif'
    with rasterio.open(path,'w',**profile) as d:d.write(np.where(fp,0,np.nan).astype(np.float32),1)
    return fp,path,profile


def test_atomic_writer_range_and_nan_roundtrip(grid,tmp_path):
    fp,template,profile=grid;p=np.zeros(fp.shape);p[4,4]=1
    path,receipt=s.write_submission(p,fp,template,tmp_path,'fixture')
    assert receipt['format_pass'];assert receipt['positive_pixels']==1;assert receipt['inside_min']==0;assert receipt['inside_max']==1
    assert path.name.endswith('-nan.tif');assert not list(tmp_path.glob('*.partial'))
    with rasterio.open(path) as d:a=d.read(1);assert np.isnan(a[~fp]).all();assert d.count==1;assert d.dtypes==('float32',)

@pytest.mark.parametrize('bad',[-.01,1.01,np.nan,np.inf,-3.4028235e38])
def test_writer_rejects_not_clips(grid,tmp_path,bad):
    fp,template,_=grid;p=np.zeros(fp.shape);p[4,4]=bad
    with pytest.raises(ValueError):s.write_submission(p,fp,template,tmp_path,'invalid')
    assert not list(tmp_path.glob('gems26-*'))

@pytest.mark.parametrize('defect',['inside_nan','outside_zero','outside_sentinel','range','nodata_sentinel','wrong_crs','wrong_transform','wrong_dtype','two_bands'])
def test_reader_independently_rejects_bad_tiff(grid,tmp_path,defect):
    fp,template,profile=grid;profile=profile.copy();a=np.where(fp,0,np.nan).astype(np.float32)
    if defect=='inside_nan':a[4,4]=np.nan
    if defect=='outside_zero':a[~fp]=0
    if defect=='outside_sentinel':a[~fp]=-9999
    if defect=='range':a[4,4]=-9999
    if defect=='nodata_sentinel':profile['nodata']=-9999;a[~fp]=-9999
    if defect=='wrong_crs':profile['crs']='EPSG:4326'
    if defect=='wrong_transform':profile['transform']=Affine(100,0,243351,0,-100,4508550)
    if defect=='wrong_dtype':profile['dtype']='float64';a=a.astype('float64')
    if defect=='two_bands':profile['count']=2
    path=tmp_path/f'{defect}.tif'
    with rasterio.open(path,'w',**profile) as d:
        d.write(a,1)
        if profile['count']==2:d.write(a,2)
    assert not s.validate_submission(path,template,fp)['format_pass']

def test_digest_ignores_only_outside_and_checks_expected_digest(grid,tmp_path):
    fp,template,_=grid;a=np.zeros(fp.shape);b=a.copy();b[~fp]=np.nan
    assert s.prediction_digest(a,fp)==s.prediction_digest(b,fp)
    path,_=s.write_submission(a,fp,template,tmp_path,'fixture')
    assert not s.validate_submission(path,template,fp,expected_digest='0'*64)['format_pass']

@pytest.mark.parametrize('value',[1+1e-10,-1e-50])
def test_before_quantization_range_guard(grid,tmp_path,value):
    fp,template,_=grid;a=np.zeros(fp.shape,np.float64);a[4,4]=value
    with pytest.raises(ValueError):s.write_submission(a,fp,template,tmp_path,'overshoot')


def test_uint8_binary_mask_is_not_numpy_fancy_indexing(grid,tmp_path):
    fp,template,_=grid;a=np.zeros(fp.shape);a[4,4]=1
    path,r=s.write_submission(a,fp.astype(np.uint8),template,tmp_path,'binary-mask')
    assert r['format_pass'];assert r['positive_pixels']==1
    for bad in (np.zeros(fp.shape),np.full(fp.shape,np.nan),np.full(fp.shape,.5)):
        with pytest.raises(ValueError):s.prediction_digest(a,bad)

@pytest.mark.parametrize('date',['../../escape','20260230','20261301','2026-10-02'])
def test_date_is_not_a_filesystem_path(grid,tmp_path,date):
    fp,template,_=grid
    with pytest.raises(ValueError):s.write_submission(np.zeros(fp.shape),fp,template,tmp_path,'date',date=date)
