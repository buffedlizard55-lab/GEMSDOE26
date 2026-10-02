from types import SimpleNamespace
import numpy as np
import pytest
from gems26.common import decode_runs,tile_origins,padded_tile,verify_grid,GRID_TRANSFORM
from rasterio.crs import CRS


def test_footprint_alternation():
    assert decode_runs(bytes([2,3,1]),6).tolist()==[False,False,True,True,True,False]
    assert decode_runs(bytes([0,6]),6).all()

@pytest.mark.parametrize('payload,total',[(b'\x80',4),(b'\x06',5),(b'',3),(b'\x01',0),(b'\x80'*12,5)])
def test_malformed_footprint(payload,total):
    with pytest.raises(ValueError):decode_runs(payload,total)

def test_tiling_every_footprint_pixel():
    fp=np.zeros((11,13),bool);fp[1:10,2:13]=True
    seen=np.zeros_like(fp,int)
    for r,c in tile_origins(fp,4):seen[r:r+4,c:c+4]+=1
    assert (seen[fp]==1).all()
    with pytest.raises(ValueError):tile_origins(fp,0)

def test_corner_halo_no_wrap():
    a=np.arange(25).reshape(5,5);out=padded_tile(a,0,0,3,2)
    assert out.shape==(7,7);assert (out[:2]==0).all();assert np.array_equal(out[2:7,2:7],a)
    z=padded_tile(a,4,4,3,1);assert z[1,1]==a[4,4];assert (z[2:]==0).all()

def test_grid_reject_wrong_projection():
    d=SimpleNamespace(shape=(3730,3292),crs=CRS.from_epsg(4326),transform=GRID_TRANSFORM)
    with pytest.raises(ValueError):verify_grid(d)


def test_missing_crs_is_clean_validation_error():
    d=SimpleNamespace(shape=(3730,3292),crs=None,transform=GRID_TRANSFORM)
    with pytest.raises(ValueError):verify_grid(d)
