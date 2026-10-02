#!/usr/bin/env python3
"""Independent Rasterio validation of the JavaScript-generated full-grid TIFF."""
import argparse,sys,base64
from pathlib import Path
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from gems26.common import HEIGHT,WIDTH,read_json,decode_runs,write_json,utcnow
from gems26.submission import validate_submission

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--output',type=Path,default=ROOT/'evidence/browser_export_checks.json');a=p.parse_args()
    model=read_json(ROOT/'docs/data/browser-model.json');h=read_json(ROOT/'evidence/holdout.json')
    fp=decode_runs(base64.b64decode(model['footprint_runs_base64']),HEIGHT*WIDTH).reshape(HEIGHT,WIDTH)
    receipt=validate_submission(a.path,ROOT/h['artifacts'][2]['path'],fp,expected_digest=model['prediction_sha256'])
    with rasterio.open(a.path) as d,rasterio.open(ROOT/h['artifacts'][0]['path']) as original:
        actual,expected=d.read(1),original.read(1)
    receipt.update(checked_utc=utcnow(),inside_cell_identity=bool(np.array_equal(actual[fp],expected[fp])),nan_footprint_identity=bool(np.array_equal(np.isnan(actual),np.isnan(expected))),scope='JavaScript copy of same frozen prediction cells; not a new detector')
    write_json(a.output,receipt);print(receipt)
    if not (receipt['format_pass'] and receipt['inside_cell_identity'] and receipt['nan_footprint_identity']):raise SystemExit(1)
if __name__=='__main__':main()
