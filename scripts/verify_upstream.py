"""Fail closed on upstream commit or distributed-input drift."""

import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
up = root / "vendor/tau2-bench"
manifest = json.loads((root / "manifests/upstream.json").read_text())
head = subprocess.check_output(
    ["git", "-C", str(up), "rev-parse", "HEAD"], text=True
).strip()
assert head == manifest["commit"], head
subprocess.run(
    [
        "git",
        "-C",
        str(up),
        "diff",
        "--exit-code",
        "HEAD",
        "--",
        "src",
        "data",
        "pyproject.toml",
        "uv.lock",
        "LICENSE",
    ],
    check=True,
    capture_output=True,
)
expected = dict(manifest["data_sha256"])
expected["uv.lock"] = manifest["uv_lock_sha256"]
for relative, digest in expected.items():
    assert hashlib.sha256((up / relative).read_bytes()).hexdigest() == digest, relative
print(f"PASS: commit and {len(expected)} distributed input/lock hashes")
