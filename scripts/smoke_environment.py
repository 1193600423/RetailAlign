"""Free developer audit, deliberately uses a dev reference action, never training data."""

import json
from pathlib import Path
from tau2.data_model.message import AssistantMessage, ToolCall
from tau2.data_model.tasks import Task
from tau2.domains.retail.environment import get_environment
from tau2.evaluator.evaluator_env import EnvironmentEvaluator

root = Path(__file__).resolve().parents[1]
split = json.loads((root / "manifests/split_v1.json").read_text())
assert "75" in split["dev"], (
    "Reviewed task must stay in dev; review split change before running."
)
raw = json.loads(
    (root / "vendor/tau2-bench/data/tau2/domains/retail/tasks.json").read_text()
)
task = Task.model_validate(next(t for t in raw if t["id"] == "75"))
action = task.evaluation_criteria.actions[0]
first, second = get_environment(), get_environment()
before = second.get_db_hash()
assert first.get_db_hash() == before
call = ToolCall(id="audit-75", name=action.name, arguments=action.arguments)
response = first.get_response(call)
assert not response.error, response.content
assert first.get_db_hash() != before
assert second.get_db_hash() == before
trajectory = [AssistantMessage(role="assistant", tool_calls=[call]), response]
reward = EnvironmentEvaluator.calculate_reward(get_environment, task, trajectory)
assert reward.db_check.db_match
result = {
    "kind": "developer_oracle_audit_not_model_rollout",
    "task_id": "75",
    "independent_environment_state": True,
    "tool_execution": "passed",
    "db_component_reward_without_auth_or_confirmation": reward.reward,
    "conclusion": "DB component alone does not enforce authentication or explicit user confirmation.",
    "paid_calls": 0,
}
(root / "reports/environment_smoke.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps(result, indent=2))
