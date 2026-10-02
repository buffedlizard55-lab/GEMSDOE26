#!/usr/bin/env python3
"""Refresh public official metadata, retain timestamps/errors, never scrape DrivenData."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gems26.common import read_json,write_json
from gems26.feed import refresh

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'docs/data/source-feed.json')
    p.add_argument('--strict',action='store_true')
    args=p.parse_args()
    old=read_json(args.output) if args.output.exists() else {}
    result=refresh(old)
    write_json(args.output,result)
    for name,item in result['items'].items():
        print(name,item['status'],item.get('error',''))
    if args.strict and not result['all_refreshes_succeeded']:raise SystemExit(1)
if __name__=='__main__':main()
