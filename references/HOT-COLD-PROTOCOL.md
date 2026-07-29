# 热循环与 NotebookLM 冷循环

## 权威与职责

事实与规范分轴，勿混成单一顺序：

- 事实：运行/测试/构建 → 当前代码、Git、配置 → CodeGraph → 有证据的 `PROJECT-STATE`。
- 规范：用户明确批准 → `REQUIREMENTS-SPEC` → 当前执行合同。
- NotebookLM、旧聊天、旧计划、模型记忆皆低权威，不得覆盖上述两轴。

Codex 执行、修改、验证与回流；CodeGraph 只查定义、引用、调用链、依赖、边界、影响；
NotebookLM 只比较方案、查矛盾、审架构、列风险/假设、排序根因假设、作里程碑复盘。

## 热循环

每轮内部判断：任务是否批准、状态是否匹配当前仓库、最小 symbol/files/tests/modify 为何、
能否局部完成、最小验证集合为何、是否真命中冷闸。

查询阶梯：

1. 当前 symbol；
2. 当前文件；
3. 直接调用链与依赖；
4. 当前模块；
5. 必要相邻模块；
6. 最后才全仓。

故障先提取稳定错误签名、首个失败位置、最近相关 diff；建立一个主假设，设计最小可证伪实验。
实验后保留或否定；勿每轮重述架构或让 NotebookLM“确认一下”。

## 冷闸触发

`notebook_gate.py --trigger` 仅接受：

- `requirements_conflict`
- `cross_architecture_boundaries`
- `multiple_viable_solutions`
- `two_failed_local_repairs`
- `conflicting_root_cause_evidence`
- `state_behavior_mismatch`
- `new_requirement_or_debt_candidate`
- `milestone_review`
- `high_risk_low_reversibility`
- `user_requested`

无触发即留热循环。`two_failed_local_repairs` 须有两次不同且确定失败的 experiment，并记录结构化 result/evidence；
多方案须至少两候选；冲突根因须至少两假设。

## 调用前

确认：

- `PROJECT-STATE` 快照 HEAD 等于当前 HEAD；
- 需求 version/hash 等于当前已批准文件；
- 当前 diff、验证与失败已摘要；
- Pending 仅以 ID/主题/状态/冻结范围索引出现；
- 决策包有界且无原始日志、全 Git 历史、无关代码或长聊天。

决策包 JSON 必含：

```json
{
  "question": "...",
  "target": "...",
  "approved_constraints": [],
  "verified_facts": [{"fact": "...", "evidence": "..."}],
  "failure_signals": [],
  "attempts": [{
    "experiment": "...",
    "result": {"status": "failed", "summary": "..."},
    "evidence": {"command": "...", "exit_code": 1, "pointer": "..."}
  }],
  "candidate_solutions": [],
  "hypotheses": [],
  "prohibitions": [],
  "questions": []
}
```

新决策覆盖旧包；默认上限 32768 bytes。

## NotebookLM 输出合同

输出 JSON：

```json
{
  "status": "PROCEED|NEEDS_DECISION|NEEDS_MORE_EVIDENCE|REQUIREMENTS_CONFLICT",
  "confirmed_facts": [],
  "contradictions": [],
  "unverified_hypotheses": [],
  "candidates": [{
    "core": "...",
    "constraints": [],
    "risks": [],
    "reversibility": "...",
    "scope": [],
    "validation": []
  }],
  "recommendation": "...",
  "next_step": {"type": "implementation|experiment|decision", "value": "..."},
  "stop_conditions": []
}
```

候选最多三项；不得声明最终根因。根因只可写假设、支持/反对证据与可证伪实验。

## 回流

Codex 将输出标为建议；逐项核对代码/CodeGraph 与获批需求，拒绝越界建议，化为一个最小步骤或实验，
运行确定性验证。仅验证成功后更新状态。需求变化另进 Pending 并获明确批准；不得原样复制 NotebookLM 输出。

根因确认须同时满足：解释关键现象；隔离或修改后失败消失；相关回归通过；无更简单同证解释。
