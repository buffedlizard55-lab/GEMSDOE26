#!/usr/bin/env python3
"""Static local-link, receipts, payload and GeoTIFF checks. No external crawling."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import argparse,base64,sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gems26.common import HEIGHT,WIDTH,FOOTPRINT_PIXELS,decode_runs,read_json,sha256_file,write_json,utcnow
from gems26.submission import validate_submission,prediction_digest

class Document(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set();self.duplicates=[];self.has_main=False;self.has_lang=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.has_lang=a.get('lang')=='en'
        if tag=='main':self.has_main=True
        if 'id' in a:
            if a['id'] in self.ids:self.duplicates.append(a['id'])
            self.ids.add(a['id'])
        for key in ('href','src','data-map','data-file'):
            if key in a:self.links.append(a[key])

def verify(root:Path=ROOT):
    root=root.resolve();pages=[root/'index.html',*(root/'docs').glob('*.html')]
    errors=[];references=0;docs={}
    for p in pages:
        d=Document();d.feed(p.read_text());docs[p.resolve()]=d
        if not d.has_main or not d.has_lang or d.duplicates:errors.append(f'{p.name}: missing main/lang or duplicate ids {d.duplicates}')
    for p,d in docs.items():
        for url in d.links:
            parsed=urlparse(url)
            if parsed.scheme or parsed.netloc:continue  # external references are for manual review, never crawler targets
            target=(p.parent/unquote(parsed.path)).resolve() if parsed.path else p
            references+=1
            if not target.is_relative_to(root) or not target.is_file():errors.append(f'{p.relative_to(root)}: missing/escaping local reference {url}')
            elif parsed.fragment and target.suffix=='.html' and parsed.fragment not in docs.get(target,Document()).ids:errors.append(f'{p.name}: missing fragment {url}')
    h=read_json(root/'evidence/holdout.json');model=read_json(root/'docs/data/browser-model.json')
    fp=decode_runs(base64.b64decode(model['footprint_runs_base64'],validate=True),HEIGHT*WIDTH).reshape(HEIGHT,WIDTH)
    if int(fp.sum())!=FOOTPRINT_PIXELS:errors.append('Incorrect browser footprint')
    manifest=read_json(root/'data/input_manifest.json')
    pin=next(r for r in manifest['files'] if r['path']=='data/raw/footprint.bin')
    import hashlib
    if hashlib.sha256(base64.b64decode(model['footprint_runs_base64'])).hexdigest()!=pin['sha256']:errors.append('Footprint payload not input-pinned')
    positives=np.frombuffer(base64.b64decode(model['positive_indices_base64'],validate=True),dtype='<u4')
    if len(positives)!=model['positive_pixels'] or len(np.unique(positives))!=len(positives) or (positives>=fp.size).any() or not fp.ravel()[positives].all():errors.append('Malformed prediction payload')
    else:
        prediction=np.zeros(fp.shape,bool);prediction.ravel()[positives]=True
        if prediction_digest(prediction,fp)!=model['prediction_sha256']:errors.append('Payload fingerprint mismatch')
    checks=[]
    template=root/h['artifacts'][2]['path']
    for row in h['artifacts']:
        path=root/row['path']
        if not path.is_file() or sha256_file(path)!=row['sha256']:errors.append('Published SHA mismatch '+row['path']);continue
        receipt=validate_submission(path,template,fp,expected_digest=row['prediction_sha256']);checks.append(receipt)
        if not receipt['format_pass']:errors.append('Invalid publication '+row['path'])
    if h['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or model['release_decision']!=h['gate']['decision']:errors.append('Failed research gate relabelled')
    if sha256_file(root/'knowledge/preregistration.md')!=h['preregistration_sha256']:errors.append('Frozen preregistration changed')
    catalog=read_json(root/'sources/catalog.json')['sources'];ids={r['id'] for r in catalog}
    if len(ids)!=len(catalog):errors.append('Duplicate source ids')
    for claim in read_json(root/'sources/claims.json')['claims']:
        if not set(claim['sources']).issubset(ids):errors.append('Missing claim source '+claim['id'])
    for p in (root/'index.html',root/'docs/index.html',root/'docs/executive-summary.html'):
        text=p.read_text()
        if Path(h['artifacts'][0]['path']).name not in text or 'download' not in text or 'Do not submit' not in text:errors.append('Missing first-screen artifact/warning '+p.name)
    return {'checked_utc':utcnow(),'status':'PASS' if not errors else 'FAIL','local_html_pages':len(pages),'local_references_checked':references,'external_links_not_crawled':True,'errors':errors,'geotiffs':checks,'scientific_release':h['gate']['decision']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=ROOT/'evidence/site_checks.json')
    args=p.parse_args();r=verify(args.root);write_json(args.output,r);print(json.dumps({k:v for k,v in r.items() if k!='geotiffs'},indent=2))
    if r['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
