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
    h=read_json(root/'evidence/holdout.json');xedge=read_json(root/'evidence/xedge_holdout.json')
    dilcond=read_json(root/'evidence/dilcond_holdout.json')
    srcoh=read_json(root/'evidence/h27_srcoh_holdout.json')
    srcoh_feature=read_json(root/'evidence/h27_srcoh_feature.json')
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
    archived=dilcond['oof_artifact'];archived_path=root/archived['path']
    previous=xedge['oof_artifact'];previous_path=root/previous['path']
    current=read_json(root/'docs/data/current.json')
    latest_status=current.get('latest_candidate',{})
    latest_tiff=current.get('latest_available_research_tiff',{})
    provenance=current.get('provenance_boundary',{})
    if (current.get('scientific_decision')!='BLOCKED_DO_NOT_SUBMIT' or
            latest_status.get('run')!=srcoh.get('run') or latest_status.get('decision')!='BLOCKED_DO_NOT_SUBMIT' or
            latest_status.get('tiff_emitted') is not False or latest_status.get('path') is not None or
            latest_status.get('gate_rules_total')!=15 or latest_status.get('gate_rules_passed')!=0 or
            latest_status.get('weekly_slot_spent') is not False or latest_status.get('upload_performed') is not False or
            latest_status.get('leaderboard_accessed') is not False or current.get('no_competition_upload') is not True or
            provenance.get('experiment_commit_ancestry_reauthenticated') is not False or
            provenance.get('pinned_source_hashes_match') is not True):
        errors.append('Current site status must identify blocked H27-SRCOH with no TIFF and its provenance boundary')
    if (latest_tiff.get('run')!=dilcond.get('run') or latest_tiff.get('path')!=archived['path'] or
            latest_tiff.get('sha256')!=archived['sha256'] or latest_tiff.get('decision')!='BLOCKED_DO_NOT_SUBMIT'):
        errors.append('Current available research TIFF is not synchronized with the earlier DILCOND receipt')
    if not archived_path.is_file() or sha256_file(archived_path)!=archived['sha256']:
        errors.append('H27-DILCOND archived OOF artifact SHA mismatch '+archived['path'])
    else:
        archived_receipt=validate_submission(archived_path,template,fp,expected_digest=archived['prediction_sha256'])
        checks.append(archived_receipt)
        if not archived_receipt['format_pass'] or not dilcond['gate']['rules']['exact_oof_tiff_format_pass']:
            errors.append('H27-DILCOND OOF artifact fails strict format checks')
    if not previous_path.is_file() or sha256_file(previous_path)!=previous['sha256']:
        errors.append('XEDGE OOF artifact SHA mismatch '+previous['path'])
    else:
        previous_receipt=validate_submission(previous_path,template,fp,expected_digest=previous['prediction_sha256'])
        checks.append(previous_receipt)
        if not previous_receipt['format_pass'] or not xedge['gate']['rules']['exact_oof_tiff_format_pass']:
            errors.append('XEDGE OOF artifact fails strict format checks')
    if (h['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or
            xedge['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or xedge['gate']['holdout_pass'] or
            xedge['gate']['weekly_slot_spent'] or not xedge['label_free_feature_preceded_label_access'] or
            dilcond['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or dilcond['gate']['holdout_pass'] or
            dilcond['gate']['weekly_slot_spent'] or not dilcond['label_free_feature_preceded_label_access'] or
            srcoh['decision']!='BLOCKED_DO_NOT_SUBMIT' or srcoh['gate']['decision']!='BLOCKED_DO_NOT_SUBMIT' or
            srcoh['gate']['holdout_pass'] or any(srcoh['gate']['rules'].values()) or len(srcoh['gate']['rules'])!=15 or
            srcoh['weekly_slot_spent'] or srcoh['upload_performed'] or srcoh['leaderboard_accessed'] or
            not srcoh['label_free_feature_preceded_label_access'] or srcoh_feature['labels_opened'] or
            srcoh_feature['template_opened'] or model['release_decision']!=h['gate']['decision']):
        errors.append('A blocked research gate, label-free ordering, or no-upload status was relabelled')
    if any('srcoh' in x.name.casefold() and x.suffix.casefold()=='.tif' for x in (root/'docs/downloads').glob('*')):
        errors.append('An H27-SRCOH TIFF must not be published')
    if sha256_file(root/'knowledge/preregistration.md')!=h['preregistration_sha256']:errors.append('Frozen preregistration changed')
    catalog=read_json(root/'sources/catalog.json')['sources'];ids={r['id'] for r in catalog}
    if len(ids)!=len(catalog):errors.append('Duplicate source ids')
    for claim in read_json(root/'sources/claims.json')['claims']:
        if not set(claim['sources']).issubset(ids):errors.append('Missing claim source '+claim['id'])
    for p in (root/'index.html',root/'docs/index.html',root/'docs/executive-summary.html'):
        text=p.read_text()
        if (Path(archived['path']).name not in text or 'H27-SRCOH' not in text or 'no tiff' not in text.casefold() or
                'download' not in text.casefold() or 'Do not submit' not in text or 'BLOCKED_DO_NOT_SUBMIT' not in text):
            errors.append('Missing latest H27-SRCOH failure + no-TIFF status or earlier DILCOND research download '+p.name)
    return {'checked_utc':utcnow(),'status':'PASS' if not errors else 'FAIL','local_html_pages':len(pages),
            'local_references_checked':references,'external_links_not_crawled':True,'errors':errors,'geotiffs':checks,
            'scientific_release':srcoh['decision'],'latest_available_research_tiff':dilcond['run'],
            'h27_srcoh_tiff_emitted':False,'provenance_boundary_preserved':not provenance.get('experiment_commit_ancestry_reauthenticated',True),
            'format_is_not_scientific_release':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=ROOT/'evidence/site_checks.json')
    args=p.parse_args();r=verify(args.root);write_json(args.output,r);print(json.dumps({k:v for k,v in r.items() if k!='geotiffs'},indent=2))
    if r['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
