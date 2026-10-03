"""Integrity gates shared by the label-free H27 builder and frozen screen."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_h27_freeze(root: Path, *, required_ancestor: str | None = None,
                      expected_manifest_sha256: str | None = None) -> dict:
    """Verify pinned slate/code bytes and that the protocol is committed first."""
    root = Path(root).resolve()
    manifest_path = root / "knowledge/h27-srcoh-code-freeze.json"
    preregistration_path = root / "knowledge/hypothesis-slate-20261002-v2.md"
    if not manifest_path.is_file() or not preregistration_path.is_file():
        raise ValueError("Committed H27 protocol and code-freeze manifest are required")
    manifest_sha256 = _sha256(manifest_path)
    if expected_manifest_sha256 and manifest_sha256 != expected_manifest_sha256:
        raise ValueError("H27 code-freeze manifest differs from the feature receipt")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported H27 code-freeze manifest")
    if _sha256(preregistration_path) != manifest.get("preregistration_sha256"):
        raise ValueError("H27 preregistration bytes differ from the committed freeze")
    input_manifest_path = root / "data/input_manifest.json"
    if _sha256(input_manifest_path) != manifest.get("input_manifest_sha256"):
        raise ValueError("Pinned raw-input manifest differs from the committed H27 freeze")
    code_hashes = manifest.get("code_sha256")
    if not isinstance(code_hashes, dict) or not code_hashes:
        raise ValueError("H27 frozen scientific source hashes are missing")
    for relative, expected in code_hashes.items():
        path = root / relative
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"H27 frozen scientific source changed: {relative}")

    source_repo = Path(os.environ.get("GEMS26_SOURCE_REPO", root)).resolve()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True,
            stderr=subprocess.STDOUT,
        ).strip()
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=source_repo, text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("A Git checkout is required to prove the H27 protocol was committed") from exc
    if not branch.startswith("arena/"):
        raise ValueError("H27 screen must run on the Arena session branch")

    slate_commit = manifest.get("slate_commit")
    if not isinstance(slate_commit, str) or len(slate_commit) != 40:
        raise ValueError("Full preregistration commit SHA is required")
    for ancestor in (slate_commit, required_ancestor):
        if not ancestor:
            continue
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
            cwd=source_repo, check=False, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise ValueError(f"Required preregistration/code-freeze commit is not an ancestor: {ancestor}")
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=source_repo, text=True,
    )
    if status.strip():
        raise ValueError("Tracked project files must be clean before H27 feature/evaluation stages")
    return {
        "manifest": manifest,
        "manifest_sha256": manifest_sha256,
        "code_sha256": code_hashes,
        "source_repo": str(source_repo),
        "commit": commit,
        "branch": branch,
    }
