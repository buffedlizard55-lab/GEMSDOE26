#!/usr/bin/env python3
"""Stage a small explicit public allowlist; never serve .git, raw inputs or caches."""
from pathlib import Path
import argparse,shutil
ROOT=Path(__file__).resolve().parents[1]


def stage(output: Path) -> Path:
    destination=output.resolve()
    cache=(ROOT/'.cache').resolve()
    if not destination.is_relative_to(cache) or destination==cache:
        raise ValueError('Public staging destination must be a child of repository .cache, never the repository root')
    if destination.exists():shutil.rmtree(destination)
    destination.mkdir(parents=True)
    files=['index.html','.nojekyll','README.md','AI_DISCLOSURE.md','data/input_manifest.json']
    for folder in ('docs','sources','knowledge','evidence','src','scripts','tests'):
        files.extend(str(p.relative_to(ROOT)) for p in (ROOT/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.partial'))
    for name in sorted(set(files)):
        source=ROOT/name
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):raise ValueError('Do not expose symbolic-link targets')
        if not source.is_file():raise ValueError('Missing public file '+name)
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    if (destination/'.git').exists() or (destination/'data/raw').exists():raise ValueError('Private/bulk paths in public staging')
    return destination


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.cache/pages-site')
    args=p.parse_args();out=stage(args.output)
    print('Public site staged at',out,'—',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'bytes')
if __name__=='__main__':main()
