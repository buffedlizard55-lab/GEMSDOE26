#!/usr/bin/env python3
"""Cold fixed-parameter replication in ignored storage; never overwrite archived results.

Restores pinned inputs automatically into the shared ignored raw cache. Copies
source + immutable preregistration to an isolated .cache child, runs every stage
in order, compares against the archived failure, and saves a small comparison.
This is replication, NOT another hypothesis search or new confirmation dataset.
"""
from __future__ import annotations
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from gems26.common import read_json,write_json,sha256_file,utcnow


def compare(run_root:Path,source_hashes:dict)->dict:
    archived=read_json(ROOT/'evidence/holdout.json');actual=read_json(run_root/'evidence/holdout.json')
    state_equal=archived['encoder_state_before']==actual['encoder_state_before']==actual['encoder_state_after']
    artifact_equal=all(a['prediction_sha256']==b['prediction_sha256'] and a['sha256']==b['sha256'] for a,b in zip(archived['artifacts'],actual['artifacts'],strict=True))
    differences={}
    for arm in archived['confirmation_summary']['dense']:
        differences[arm]={
            'dense_dti_delta':actual['confirmation_summary']['dense'][arm]['pooled']['dti']-archived['confirmation_summary']['dense'][arm]['pooled']['dti'],
            'sparse_mean_dti_delta':actual['confirmation_summary']['sparse'][arm]['mean_pooled_dti']-archived['confirmation_summary']['sparse'][arm]['mean_pooled_dti']}
    metrics_equal=all(abs(v)<1e-12 for row in differences.values() for v in row.values())
    report={'checked_utc':utcnow(),'isolated_run':str(run_root.relative_to(ROOT)),'scope':'Same frozen protocol/data/seed, no retuning; not independent scientific confirmation',
            'source_sha256':source_hashes,'encoder_state_identical':state_equal,'all_artifacts_prediction_and_file_identity':artifact_equal,
            'all_confirmation_metrics_identical_1e-12':metrics_equal,'confirmation_differences':differences,
            'label_access_after_ssl_and_anomaly':actual['label_access_after_ssl_and_anomaly'],
            'scientific_decision':actual['gate']['decision'],'archived_result_untouched':True,
            'replication_pass':bool(state_equal and artifact_equal and metrics_equal and actual['label_access_after_ssl_and_anomaly'] and actual['gate']['decision']==archived['gate']['decision'])}
    write_json(ROOT/'evidence/reproduction.json',report)
    print(report)
    if not report['replication_pass']:raise SystemExit('Replication differed. Preserve differences; do NOT retune to force agreement. Floating-point/platform drift may require investigation.')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.cache/reproduction');args=p.parse_args()
    run_root=args.output.resolve();cache=(ROOT/'.cache').resolve()
    if not run_root.is_relative_to(cache) or run_root==cache:raise SystemExit('Use a child of repository .cache; never the repository or .git root')
    scientific_scripts = ['restore_data.py','prepare_data.py','pretrain.py','infer_representation.py','build_anomaly.py','run_holdout.py']
    paths=[*sorted((ROOT/'src').rglob('*.py')),*(ROOT/'scripts'/name for name in scientific_scripts),ROOT/'data/input_manifest.json',ROOT/'knowledge/preregistration.md']
    hashes={str(f.relative_to(ROOT)):sha256_file(f) for f in paths}
    if run_root.exists():
        if not (run_root/'evidence/holdout.json').exists():raise SystemExit('Partial reproduction exists. Keep it for diagnosis; choose a fresh .cache child, do not alter protocol.')
        old=read_json(run_root/'source-copy.json')
        if old!=hashes:raise SystemExit('Copied source changed; use a fresh .cache child for an honest replication')
        compare(run_root,hashes);return
    run_root.mkdir(parents=True)
    for f in paths:
        dest=run_root/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
    (ROOT/'data/raw').mkdir(parents=True,exist_ok=True)
    (run_root/'data/raw').symlink_to(ROOT/'data/raw',target_is_directory=True)
    write_json(run_root/'source-copy.json',hashes)
    env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2','PYTHON':sys.executable}
    stages=[('restore_data.py',[]),('prepare_data.py',[]),('pretrain.py',['--epochs','6','--tile','64','--batch-size','8','--threads','2']),
            ('infer_representation.py',[]),('build_anomaly.py',[]),('run_holdout.py',[])]
    for name,flags in stages:
        print('\nREPLICATION STAGE:',name,flush=True)
        subprocess.run([sys.executable,str(run_root/'scripts'/name),*flags],cwd=run_root,env=env,check=True)
    compare(run_root,hashes)
if __name__=='__main__':main()
