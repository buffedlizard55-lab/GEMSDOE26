#!/usr/bin/env python3
"""Validate a GeoTIFF, never repair it by silently clipping predictions."""
import argparse,json,sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import RAW, footprint
from gems26.submission import validate_submission

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path)
    args=p.parse_args()
    receipt=validate_submission(args.path, RAW/'sample_submission.tif', footprint())
    print(json.dumps(receipt,indent=2,allow_nan=False))
    if not receipt['format_pass']:raise SystemExit(1)
if __name__=='__main__':main()
