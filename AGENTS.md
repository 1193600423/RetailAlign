# RetailAlign 开发约定

本项目为独立的领域 SFT + 真正在线 GRPO 实验。先读 README、docs/progress.md、docs/data_protocol.md 与预算。每次只推进可验证的小实验。

- 不生成虚假结果；区分源码审计、配置校验、工具测试和实际模型实验。
- 不进行付费调用或启动计费 GPU，除非本次具体配置、预计费用、停止条件及余额已获用户确认。不得读取/打印密钥。
- final_test 和 legacy_holdout 不用于训练或调试；生成前读取 split 状态并检查 allowlist，当前 generation_blocked。
- dev0/1/2/3/4/75 已被阅读，不得改作最终测试或训练。
- 不给 Agent 参考动作/隐藏目标；oracle 审计不作训练轨迹。
- 不改上游源码或数据；如确需修改，记录 diff/hash，并标为自定义协议。
- 尚无训练结果，不能声称领域知识增强或 RL 有效。每次实验保存配置、版本、真实日志与费用。
- 不建设前端、完整平台、多 Agent、长期记忆或检索；不集成其他项目。
