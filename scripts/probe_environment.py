"""Read-only hardware and package probe; never reads environment secrets."""

import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys

result = {
    "python": sys.version,
    "platform": platform.platform(),
    "machine": platform.machine(),
}
for name in ("torch", "transformers", "peft", "trl", "tau2", "litellm"):
    try:
        result[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        result[name] = None
if shutil.which("nvidia-smi"):
    for key, args in [
        (
            "gpu",
            [
                "--query-gpu=name,memory.total,memory.free,driver_version",
                "--format=csv",
            ],
        ),
        ("gpu_layout", ["-L"]),
    ]:
        p = subprocess.run(["nvidia-smi", *args], capture_output=True, text=True)
        result[key] = {
            "returncode": p.returncode,
            "output": p.stdout.strip(),
            "error": p.stderr.strip(),
        }
else:
    result["gpu"] = "nvidia-smi unavailable; remote RTX3060/A100 unverified"
if platform.system() == "Darwin":
    result["ram_bytes"] = int(
        subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
    )
result["disk_free_bytes"] = shutil.disk_usage(".").free
print(json.dumps(result, ensure_ascii=False, indent=2))
