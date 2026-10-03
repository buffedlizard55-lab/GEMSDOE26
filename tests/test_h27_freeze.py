import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_h27_protocol_and_scientific_sources_match_committed_freeze_manifest():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "knowledge/h27-srcoh-code-freeze.json").read_text())
    assert manifest["schema_version"] == 1
    assert sha256(root / manifest["preregistration_path"]) == manifest["preregistration_sha256"]
    assert sha256(root / "data/input_manifest.json") == manifest["input_manifest_sha256"]
    assert manifest["code_sha256"]
    for relative, expected in manifest["code_sha256"].items():
        assert sha256(root / relative) == expected, relative
