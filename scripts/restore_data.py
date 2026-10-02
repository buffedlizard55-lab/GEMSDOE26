#!/usr/bin/env python3
"""Restore the owner-authorized public mirrors, NOT login-gated DrivenData data.

All inputs are pinned to immutable commits and SHA256. For small binary blobs use
Git's base64 blobs endpoint: the contents/raw route corrupted .bin in the initial
sandbox audit. Bulk bytes use raw media and must match the final assembled hash.
No credentials are read/stored here; gh uses the existing GitHub connection.
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems26.common import RAW, read_json, sha256_file, utcnow, write_json


def gh_download(repo: str, path: str, ref: str, dest: Path, *, small_binary=False) -> None:
    if repo not in {"buffedlizard55-lab/GEMSDOE", "buffedlizard55-lab/GEMSDOE24"}:
        raise ValueError("Unapproved mirror repository")
    if len(ref) != 40 or any(x not in "0123456789abcdef" for x in ref):
        raise ValueError("An immutable commit is required")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        endpoint = f"repos/{repo}/contents/{path}?ref={ref}"
        if small_binary:
            metadata = json.loads(subprocess.check_output(["gh", "api", endpoint]))
            blob = json.loads(subprocess.check_output(["gh", "api", f"repos/{repo}/git/blobs/{metadata['sha']}"]))
            if blob["encoding"] != "base64":
                raise ValueError("Unexpected Git blob encoding")
            payload = base64.b64decode(blob["content"], validate=False)
            if len(payload) != blob["size"]:
                raise ValueError("Git blob size mismatch")
            tmp.write_bytes(payload)
        else:
            with tmp.open("wb") as f:
                subprocess.run(["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"], stdout=f, check=True)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def matches(path: Path, row: dict) -> bool:
    return path.is_file() and path.stat().st_size == row["bytes"] and sha256_file(path) == row["sha256"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    rows = read_json(ROOT / "data/input_manifest.json")["files"]
    if not args.verify_only and shutil.which("gh") is None:
        raise SystemExit("gh is required to restore public GitHub mirrors; no DrivenData login is used")
    failures, receipts = [], []
    for row in rows:
        dest = ROOT / row["path"]
        if not matches(dest, row):
            if args.verify_only:
                failures.append(str(dest.relative_to(ROOT)))
                continue
            if "remote_paths" in row:
                parts_dir = RAW / "parts"
                parts_dir.mkdir(parents=True, exist_ok=True)
                def get(p):
                    part = parts_dir / Path(p).name
                    gh_download(row["repo"], p, row["ref"], part)
                    return part
                with ThreadPoolExecutor(max_workers=3) as ex:
                    parts = list(ex.map(get, row["remote_paths"]))
                tmp = dest.with_suffix(".partial")
                try:
                    with tmp.open("wb") as f:
                        for part in parts:
                            with part.open("rb") as src:
                                shutil.copyfileobj(src, f, length=1 << 20)
                    if not matches(tmp, row):
                        raise ValueError("Assembled feature raster integrity failed")
                    tmp.replace(dest)
                finally:
                    tmp.unlink(missing_ok=True)
                    for part in parts:
                        part.unlink(missing_ok=True)
            else:
                gh_download(row["repo"], row["remote_path"], row["ref"], dest,
                            small_binary=dest.suffix == ".bin")
            if not matches(dest, row):
                dest.unlink(missing_ok=True)
                raise ValueError(f"Downloaded file failed hash pin: {dest.name}")
        receipts.append({**row, "verified": True})
        print("verified", dest.name, row["sha256"][:12], flush=True)
    receipt = {"checked_utc": utcnow(), "integrity_not_organizer_authentication": True,
               "files": receipts, "failures": failures,
               "note": "No raster label values opened. No automatic DrivenData access."}
    write_json(ROOT / "evidence/data_restore.json", receipt)
    if failures:
        raise SystemExit("Missing or corrupt pinned inputs: " + ", ".join(failures))


if __name__ == "__main__":
    main()
