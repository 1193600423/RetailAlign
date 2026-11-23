# 第一阶段复现

需要 git、uv、Python3.12；此阶段不需要 GPU 或 API 密钥。所有命令在 RetailAlign 根目录运行。不要把 .env 或 SSH 私钥复制入项目。

```bash
mkdir -p vendor
# vendor 目录未存在时执行：
git clone --depth 1 --branch v2.0.0 https://github.com/sierra-research/tau2-bench.git vendor/tau2-bench
git -C vendor/tau2-bench rev-parse HEAD
# 必须等于 989d3285ae669e49503324bdb9981bf14fccedeb
uv sync --project vendor/tau2-bench --frozen --no-default-groups --extra dev --python 3.12
vendor/tau2-bench/.venv/bin/python scripts/probe_environment.py
python3 scripts/verify_upstream.py
python3 scripts/audit_data.py
python3 scripts/inventory_tasks.py
vendor/tau2-bench/.venv/bin/python scripts/smoke_environment.py
vendor/tau2-bench/.venv/bin/python scripts/baseline_plan.py
```

Windows venv 可执行目录是 Scripts，远端 Linux 为 bin；A100 先仅执行 probe_environment.py，用实际 nvidia-smi 结果确认设备/MIG切片/空闲显存。Mac 上本次使用 3.12.13。uv 版本、安装包精确版本与依赖树分别见 reports/uv_version.txt、reports/environment_packages.txt 和上游固定 uv.lock（哈希记录在 manifests/upstream.json）。训练库不在当前环境里；不要把此依赖锁当作已验证训练栈。

上游免费检查（项目根目录执行）：

```bash
uv run --project vendor/tau2-bench --frozen tau2 check-data
# 上游 pytest 使用其根目录 conftest/config，先进入目录：
cd vendor/tau2-bench
uv run --frozen pytest tests/test_domains/test_retail/test_tools_retail.py -q
```

预期：check-data 只验证目录存在；工具测试19通过；smoke 验证独立 DB 并复现缺少认证/确认仍有 DB奖励的反例；baseline_plan 仅校验自定义运行配置并写日志，**不会调用模型**，不会验证 endpoint、语言绑定的最终prompt或实际任务成功。

split audit 会重新写 manifests/split_v1.json 和 reports/split_audit.json；结果若变化，停止下游工作、检查上游哈希与脚本变化，不接受自动覆盖后的不一致。耗时约数分钟（文本两两比对），不调用模型。当前基线脚本检查 dev allowlist，不支持执行正式调用。原模型、SFT、GRPO 入口将按最小实验逐阶段实现；目前不提供空壳训练脚本或伪日志。

原始日志位于 logs/；reports/environment_smoke.json 标记 developer_oracle_audit，不能作模型成功轨迹。当前最终测试任务全文与答案未输出到报告；manifests 中仅有 ID、分组、哈希。源仓库是公开可读资产，运行/数据生成入口还需在后续阶段强化 split 校验。
