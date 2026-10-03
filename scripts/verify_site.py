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
    h=read_json(root/'evidence/holdout.json');xedge=read_json(root/'evidence/xedge_holdout.json');h27=read_json(root/'evidence/h27_srcoh_holdout.json')
    model=read_json(root/'docs/data/browser-model.json')
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
    archived=xedge['oof_artifact'];archived_path=root/archived['path']
    current=read_json(root/'docs/data/current.json')
    latest=current.get('latest_candidate',{})
    available=current.get('available_research_tiff',{})
    if (current.get('scientific_decision')!='BLOCKED_DO_NOT_SUBMIT' or
            latest.get('run')!='H27-SRCOH-v1' or latest.get('decision')!='BLOCKED_DO_NOT_SUBMIT' or
            latest.get('candidate_tiff_created') is not False or latest.get('path') is not None or
            latest.get('sha256') is not None or available.get('path')!=archived['path'] or
            available.get('sha256')!=archived['sha256'] or available.get('decision')!='BLOCKED_DO_NOT_SUBMIT'):
        errors.append('Current site status must show failed H27 with no TIFF and archived XEDGE as research-only')
    if (h27.get('decision')!='BLOCKED_DO_NOT_SUBMIT' or h27.get('gate',{}).get('holdout_pass') is not False or
            h27.get('weekly_slot_spent') is not False or h27.get('upload_performed') is not False or
            h27.get('leaderboard_accessed') is not False or latest.get('weekly_slot_spent') is not False or
            current.get('no_competition_upload') is not True):
        errors.append('H27 failed/no-upload/zero-slot status is not preserved')
    if not archived_path.is_file() or sha256_file(archived_path)!=archived['sha256']:
        errors.append('Archived XEDGE OOF artifact SHA mismatch '+archived['path'])
    else:
        latest_receipt=validate_submission(archived_path,template,fp,expected_digest=archived['prediction_sha256'])
        checks.append(latest_receipt)
        if not latest_receipt['format_pass'] or not xedge['gate']['rules']['exact_oof_tiff_format_pass']:
            errors.append('Archived XEDGE OOF artifact fails strict format checks')
    if (h['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or
            xedge['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or xedge['gate']['holdout_pass'] or
            xedge['gate']['weekly_slot_spent'] or not xedge['label_free_feature_preceded_label_access'] or
            h27['decision']!='BLOCKED_DO_NOT_SUBMIT' or h27['gate']['holdout_pass'] or
            h27['weekly_slot_spent'] or h27['upload_performed'] or h27['leaderboard_accessed'] or
            not h27['label_free_feature_preceded_label_access'] or
            model['release_decision']!=h['gate']['decision']):
        errors.append('Failed research gate, no-upload status or label-free ordering relabelled')
    if sha256_file(root/'knowledge/preregistration.md')!=h['preregistration_sha256']:errors.append('Frozen preregistration changed')
    catalog=read_json(root/'sources/catalog.json')['sources'];ids={r['id'] for r in catalog}
    if len(ids)!=len(catalog):errors.append('Duplicate source ids')
    for claim in read_json(root/'sources/claims.json')['claims']:
        if not set(claim['sources']).issubset(ids):errors.append('Missing claim source '+claim['id'])
    for p in (root/'index.html',root/'docs/index.html',root/'docs/executive-summary.html'):
        text=p.read_text()
        if Path(archived['path']).name not in text or 'download' not in text or 'Do not submit' not in text or 'BLOCKED_DO_NOT_SUBMIT' not in text or 'H27' not in text:
            errors.append('Missing latest H27 no-TIFF decision or archived XEDGE warning '+p.name)
    return {'checked_utc':utcnow(),'status':'PASS' if not errors else 'FAIL','local_html_pages':len(pages),'local_references_checked':references,'external_links_not_crawled':True,'errors':errors,'geotiffs':checks,'scientific_release':h27['decision'],'format_is_not_scientific_release':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=ROOT/'evidence/site_checks.json')
    args=p.parse_args();r=verify(args.root);write_json(args.output,r);print(json.dumps({k:v for k,v in r.items() if k!='geotiffs'},indent=2))
    if r['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
