"""Validate an official custom-run plan; this script can ONLY execute --dry-run."""

import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
split = json.loads((root / "manifests/split_v1.json").read_text())
ids = ["75", "0", "1", "2", "3", "4"]
assert set(ids) <= set(split["dev"])
assert not set(ids) & set(split["final_test"])
cmd = [
    str(root / "vendor/tau2-bench/.venv/bin/tau2"),
    "run",
    "--benchmark",
    "none",
    "--domain",
    "retail",
    "--language",
    "en",
    "--agent",
    "llm_agent",
    "--agent-llm",
    "openai/retailalign-0.6b",
    "--agent-llm-args",
    json.dumps(
        {
            "api_base": "http://127.0.0.1:8000/v1",
            "api_key": "local-unused",
            "temperature": 0.0,
            "max_tokens": 512,
        }
    ),
    "--user-llm",
    "gpt-4.1-2025-04-14",
    "--user-llm-args",
    '{"temperature":0.0,"max_tokens":512}',
    "--task-split-name",
    "base",
    "--task-ids",
    *ids,
    "--num-trials",
    "1",
    "--seed",
    "300",
    "--max-steps",
    "80",
    "--max-errors",
    "3",
    "--timeout",
    "180",
    "--max-concurrency",
    "1",
    "--save-to",
    "retailalign-base-dev-pilot-v1",
    "--dry-run",
]
result = subprocess.run(
    cmd, cwd=root / "vendor/tau2-bench", capture_output=True, text=True
)
(root / "logs/baseline_dry_run.log").write_text(result.stdout + result.stderr)
(root / "configs/baseline_plan.json").write_text(
    json.dumps(
        {
            "status": "dry_run_only_inference_server_not_validated",
            "argv": cmd[1:],
            "model": "Qwen/Qwen3-0.6B",
            "model_revision": None,
            "prerequisites": [
                "pin model revision",
                "GPU probe",
                "tool parsing roundtrip",
                "context length measurement",
                "provider prices and paid approval",
                "semantic audit before training data generation",
            ],
            "returncode": result.returncode,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print("Official CLI dry-run returncode:", result.returncode)
raise SystemExit(result.returncode)
