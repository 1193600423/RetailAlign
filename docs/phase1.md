# 第一阶段：输入、行为与验证

日期：2026-11-23（Asia/Shanghai）。状态：源码审计与免费工具验证完成；模型可行性仍待基线。时间安排以每周 10–15 小时为假设。

## 版本与证据

选用官方 [v2.0.0 发布](https://github.com/sierra-research/tau2-bench/releases/tag/v2.0.0)，annotated tag object 为 `acd66c4d8681ce27ef0cbb4839d24f87218b9b9c`，实际提交为 `989d3285ae669e49503324bdb9981bf14fccedeb`。包版本是 2.0.0；仓库名 tau2-bench 不代表所有提交都是 2.0，历史 τ² / τ³ 名称也不是实验版本号。

本项目选择英文、文本、Retail。2.0 的公开文本协议名称仍是 **text-v1**，数据 revision 为 `regional-release-data-v16`，与软件版本是不同维度。完整矩阵含六语言三领域，每格 50 任务；我们的英文 Retail 子集不宣称完整公开基准成绩。[固定源码 README](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/README.md)、[协议](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/data/tau2/benchmarks/text.json)。2.0 的 reviewed English Retail 50 条位于 multilingual/en/retail_tasks_en.json，不能用历史 domains/retail/tasks.json 中的同 ID 原文替代最终测试。

[MIT 许可证](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/LICENSE)允许使用、修改与分发，需保留版权和许可文本。当前仓库数据未发现单独的 Retail 许可文件；按该固定仓库许可保存来源，教师模型/基础模型与供应商条款需另查。保留 upstream LICENSE，不将官方资产归为原创。

## 模型到底看到什么

Agent 每一步输入是：规则 system prompt、工具 JSON schema、截至当前的用户消息、自身动作与工具返回。输出是用户可见回复，或一个带参数的工具调用。环境执行动作并产生新 observation，用户模拟器继续对话。这是部分可观测、多轮业务决策问题；当前项目首先学习行为，不能预先宣称新增知识。

用户模拟器单独接收 user_scenario、persona 与模拟规则。它知道用户的目标、已知/未知信息，按角色提供这些信息。评测器独享 evaluation_criteria、参考动作、环境断言和验收答案。Agent 不应看到 user_scenario 全文或这些隐藏字段。官方 LLMAgent 的普通实现满足这个接口边界；**不得使用 llm_agent_gt / 带参考动作的 Agent 作基线或教师输入**。Retail get_environment 不支持 solo_mode。

来源：[普通 Agent](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/src/tau2/agent/llm_agent.py)、[用户模拟](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/src/tau2/user/user_simulator.py)。后续 adapter 必须在实际发送给模型的 payload 上验证边界。

## 小样本任务分析（全部来自 dev，不使用最终测试）

以下是开发者阅读的验收信息，不能直接拼入 Agent prompt。0–4 共享同一用户，0/1 还共享订单，不能算五个独立业务客户。

| dev ID | 用户需求与决策点 | 需要学的参数/动作 | 验证重点 |
|---|---|---|---|
| 0 | 键盘+温控器换货；首选不存在时允许无背光备选 | 姓名邮编认证；查询订单、商品；收集两个 item/new_item 配对，确认后一次 exchange | 正确变体与付款；两件合并；不能把 product_id 当 item_id |
| 1 | 与 0 极近似，但键盘不满足全部条件时只换温控器 | 同样工具链，最终换货清单不同 | 不能照抄近似任务答案；遵守条件偏好 |
| 2 | 查询可用 T 恤选项数量，同时退三件已送达商品 | 查询用户所有订单，定位商品；退货列表和退款方式 | DB 状态+自然语言数量断言；查到信息要向用户说明 |
| 3 | 修改待发货的小码 T 恤，保持其他指定属性 | 区分 pending/delivered；查变体；付款差额；modify_pending_order_items | 只改满足条件的订单，确认所有修改后一次提交 |
| 4 | 所有待发货 T 恤改小码，涉及多个订单 | 跨订单枚举与逐订单合并操作 | 不漏订单、不多改；有官方 open issue，纳入噪声分析，不作为唯一选点依据 |
| 75 | 指定已送达耳机换成另一配置 | 邮箱认证；检查库存、同产品、付款；exchange | 简单单写操作，可用作最小接入 smoke |

主要工具有身份查找、用户/订单/商品查询、计算器、取消、改地址/商品/付款、退货、换货与转人工。写工具关键约束：[业务规则](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/data/tau2/domains/retail/policy.md)。

先认证，即使用户已经报 user_id；每次数据库写入前列出细节并得到明确确认；同一对话只操作一个用户；每步最多一个工具调用，不能同时回复用户；pending 才能取消/修改，delivered 才能退换；换货/修改商品需一次收齐清单，不能跨产品类型。退款和差价支付也有付款来源/余额约束。这些共同构成决策能力，工具 schema 仅约束其中一部分。

## SFT 与 RL 的不同假设

SFT（监督微调）从成功交互中学“在这个上下文下下一步怎么做”：规范 JSON、正确 ID、参数列表配对、查状态、追问缺失信息、合并写操作、明确确认。它可能减少格式/流程错误，但是否改善多约束决策要实测。标签只覆盖 assistant 生成的回复与调用，用户、工具输出、system 和 padding 全部屏蔽；不能把隐藏参考动作作为额外输入。

在线 GRPO（组相对策略优化）让当前策略对同一训练任务采样多条真实多轮交互，比较终局奖励，强化同组中较好的选择。可能优化备选商品选择、操作顺序、漏项与不必要重试；若所有样本都失败或都成功，就缺少有用的组内差异。RL 不保证有效，0.6B 也可能欠缺完成任务的最低能力。

## 奖励可靠性：已发现的限制

官方 ALL 根据 task.reward_basis 将适用分量相乘。DB：重放轨迹，将预测环境与执行参考动作后的环境做完整 DB hash 对比；ENV_ASSERTION：确定性环境检查；ACTION：指定动作和参数检查。COMMUNICATE 在启用时默认语义模型判断；NL_ASSERTION 使用模型评审自然语言断言，空断言直接通过。独立的 tau2 judges 后处理与任务 reward 不同，不要混为一谈。[组合实现](https://github.com/sierra-research/tau2-bench/blob/989d3285ae669e49503324bdb9981bf14fccedeb/src/tau2/evaluator/evaluator.py)。

免费反例审计 scripts/smoke_environment.py 在 dev75 上直接执行参考写操作，**没有身份验证或用户确认**，DB 分量仍得 1。它不是模型 rollout，也不是完整官方评测成绩。它证明仅以终局数据库为奖励会留下流程漏洞。独立环境 hash 验证同时通过。见 reports/environment_smoke.json。

因此：保留官方成功率用于对比，另报告经流程审计的成功率；拟议训练奖励优先终局正确，且认证/授权确认/额外修改必须过门控。确认是否覆盖了具体操作的语义，需要人工抽查和正反例验证，不能用找一个 yes 的正则宣称可靠。新增门控属于自定义训练奖励，单独版本化，不能偷偷改官方分数。拒绝所有请求、转人工不等于成功；只读/本应拒绝类任务必须同时验证回复与无额外状态修改。

## 难度与成本的当前结论

0/1 参考动作各 5 个，2/3/4 参考动作约 11–13 个；75 的参考只有 1 个写操作，**不含一个合规交互所需的认证、查询和确认**。这些不是模型实际轨迹长度。工具输出包含商品大量变体、完整订单资料，token 成本可能明显高于动作数所暗示的成本。下一步实测总上下文、最长工具返回与截断，先从 dev75 开始，再加入多约束任务。现在没有实测成功率、模型时延、显存或单任务费用，不判断正式规模可承受。

本机工具测试通过仅说明复用链路可加载。训练可行性仍取决于远端 GPU 实际显存、原模型小样本成功率、SFT 过拟合结果和同题奖励方差。
