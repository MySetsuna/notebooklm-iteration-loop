---
name: notebooklm-iteration-loop
description: >
  用 CodeGraph、Codex 与 NotebookLM 低消耗迭代项目；维护获批需求、项目状态快照、需求审批、
  确定性质量闸、局部代码查询与按条件触发的 NotebookLM 冷循环。当用户要求初始化或运行迭代、
  规划下一步、整理项目笔记本、分析复杂根因/架构决策，或限制扫描与模型消耗时使用。
---

# CodeGraph + Codex + NotebookLM 低消耗迭代

目标：确定性事实、局部查询、最小修改、验证闭环；NotebookLM 仅作低频战略层。

## 不变量

1. 事实轴：运行/测试/构建 → 当前代码与 Git → CodeGraph → `PROJECT-STATE`；低位不得改写高位。
2. 规范轴：用户明确批准 → `REQUIREMENTS-SPEC` → 当前合同；现有代码与测试不得把偏离变成需求。
3. NotebookLM 不裁决代码事实、根因、需求批准或质量；其输出只作待验证建议。
4. NotebookLM 常驻仅两源：已批准 `REQUIREMENTS-SPEC` 与运行时 `PROJECT-STATE` 快照。
5. Pending 仅存本地 `PENDING-REQUIREMENTS.md`；不上传、不实施、不进入已批准需求源。
6. Agent 只读 `.iteration/context.json` 允许集合；每轮受 budget/usage 与 `iteration_gate.py` 约束。
7. 不自动初始化 CodeGraph；不上传原始日志；不承诺未经 `token-usage --all` A/B 验证的节省。
8. 删除来源、覆盖用户工作、远端合并/重写历史须单独授权。

## 开工闸

先检查分支、upstream、ahead/behind、dirty。非 `0/0`、detached、无 upstream 或遗留 dirty 时，
先取得继续当前基线的裁定；禁擅自 pull/merge/rebase/reset/checkout/stash。

```text
python <skill>/scripts/requirements_gate.py assert-executable \
  --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md
python <skill>/scripts/preflight.py --project-root <repo> --strict
```

需求审批与质量细则见 [`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md)。

## 默认热循环

1. 首轮运行 `iteration_budget.py init` 与 `iteration_budget.py init-usage` 建立 `.iteration/budget.json`
   和 `.iteration/usage.json`；每轮按实际工具调用更新 usage。
2. 以 `requirements_store.py read --id REQ-*` 取当前合同引用条目；勿整读需求或历史。
3. 生成 `.iteration/context.json`，显式列 requirement/symbol/file/test/modify/constraint；随即过
   `iteration_gate.py`。上下文细则见 [`references/CONTEXT-CONTROL.md`](./references/CONTEXT-CONTROL.md)。
4. 看受控 diff；CodeGraph 依次查目标 symbol → 文件 → 直接调用/依赖 → 当前模块。仅必要时扩相邻模块；
   全仓分析只用于首次、索引异常、重大分支/边界/数据模型变化、事实矛盾或用户明确要求。
5. 一轮只做一项已批准目标；禁顺带重构、优化、升级、扩范围或改无关文件。
6. 跑目标测试、相关回归及适用 typecheck/lint/build/runtime；不得凭阅读宣布成功。
7. 只更新新增事实与状态变化；历史用 `archive.py append`，原始日志留本地/CI。
8. 再跑 requirements/iteration gate；Reviewer 只读复核合同、diff、失败知识与验证。

默认：局部查询、局部修改、局部验证、**不调用 NotebookLM**。

## NotebookLM 冷闸

仅 [`references/HOT-COLD-PROTOCOL.md`](./references/HOT-COLD-PROTOCOL.md) 所列十类触发可进入冷循环。
调用前生成决策 JSON 与状态快照：

```text
python <skill>/scripts/state_snapshot.py build --root <repo> \
  --state docs/PROJECT-STATE.md --requirements docs/REQUIREMENTS-SPEC.md \
  --pending docs/PENDING-REQUIREMENTS.md --decision .iteration/decision.json
python <skill>/scripts/notebook_gate.py assert-allowed --root <repo> \
  --snapshot .iteration/PROJECT-STATE.snapshot.md --requirements docs/REQUIREMENTS-SPEC.md \
  --pending docs/PENDING-REQUIREMENTS.md \
  --decision .iteration/decision.json --trigger <trigger>
```

闸通过后，才以快照替换 NotebookLM 的 `PROJECT-STATE` 来源并查询。收到结果后先运行
`notebook_gate.py validate-output`，再以代码、CodeGraph、获批需求和测试验证；禁止直接实施或写入需求。

## 文档

- `REQUIREMENTS-SPEC.md`：仅 Active；批准后覆盖 NotebookLM 来源。
- `PENDING-REQUIREMENTS.md`：本地审批界面；不上传。
- `PROJECT-STATE.md`：稳定 tracked 正文；`state_snapshot.py` 在 `.iteration/` 生成动态尾段。
- `docs/archive/events-YYYY-MM.jsonl`：分片、append-only、有界 tail；不上传。
- 当前合同与 `WORKFLOW` 保持 Markdown；运行 context/decision/snapshot 不作第三常驻来源。

出现 Pending、状态快照失配、触发证据不足、索引矛盾、验证失败、越界写或预算耗尽，即停止相应动作。
