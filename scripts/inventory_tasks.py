"""Report train/dev reference metadata, never model performance or test contents."""

import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
split = json.loads((root / "manifests/split_v1.json").read_text())
tasks = json.loads(
    (root / "vendor/tau2-bench/data/tau2/domains/retail/tasks.json").read_text()
)
out = {}
for name in ("train", "dev"):
    selected = [t for t in tasks if t["id"] in split[name]]
    coverage = Counter()
    counts = []
    for task in selected:
        actions = task["evaluation_criteria"].get("actions") or []
        counts.append(len(actions))
        coverage.update(a["name"] for a in actions)
    out[name] = {
        "independent_task_ids": len(selected),
        "entity_or_similarity_groups": sum(
            bool(set(g) & set(split[name])) for g in split["groups"]
        ),
        "reference_action_counts": counts,
        "reference_tool_coverage": dict(coverage),
        "rollout_count": 0,
        "derived_scenarios": 0,
        "warning": "Reference-action counts are not observed model trajectory lengths; no trajectory token/duplicate statistics yet.",
    }
(root / "reports/task_inventory.json").write_text(json.dumps(out, indent=2) + "\n")
print("Wrote train/dev inventory; model trajectories: 0")
