# RetailAlign

面向零售业务决策的语言模型监督微调与强化学习。独立后训练项目，复用 Sierra 的环境、规则、工具、用户模拟与评测；不建设前端或服务平台。

当前阶段：可行性与隔离审计。已固定 τ-bench **v2.0.0**，完成免费环境验证；**尚未运行原始模型基线、生成 SFT 轨迹或训练**。目前不能声称训练有效或领域知识增强。

- [第一阶段分析与教学说明](docs/phase1.md)
- [隔离规则](docs/data_protocol.md) 与 [任务划分](manifests/split_v1.json)
- [最小实验、指标与预算](docs/experiment_plan.md)
- [复现指南](docs/reproduce.md)
- [进度](docs/progress.md)、[环境](reports/environment_local.json)、[支出](logs/budget.csv)
- [固定上游版本及数据哈希](manifests/upstream.json)

原始模型 / SFT / SFT+GRPO 的成绩均为待测。开发任务与冻结评测任务分开；最终测试只在协议和检查点冻结后运行。训练依赖待 GPU 实测后单独锁定，不把框架安装通过表述成训练验证通过。

在 A100 服务器上先下载项目并做只读环境检查（脚本仅使用 Python 标准库）：

```bash
git clone https://github.com/1193600423/RetailAlign.git
cd RetailAlign
python3 scripts/probe_environment.py
```

随后按[复现指南](docs/reproduce.md)下载固定版本的上游环境并安装依赖。`vendor/`、虚拟环境和模型权重不随本仓库上传；当前环境检查不会启动训练或模型 API 调用。
