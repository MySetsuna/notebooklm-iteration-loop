---
name: notebooklm-iteration-loop
description: >
  用 CodeGraph、Codex 与 NotebookLM 低消耗迭代项目；维护获批需求、项目状态快照、需求审批、
  确定性质量闸、局部代码查询、默认有界多 Agent 编排与按条件触发的 NotebookLM 冷循环。
  当用户要求初始化或运行迭代、并行派发 Agent、规划下一步、整理项目笔记本、
  分析复杂根因/架构决策，或限制扫描与模型消耗时使用。
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
7. 主 Agent 保留需求审批、冲突裁决、联合验证、状态、提交与推送权；Worker 不调用 NotebookLM。
8. 不自动初始化 CodeGraph；不上传原始日志；不承诺未经 `token-usage --all` A/B 验证的节省。
9. 删除来源、覆盖用户工作、远端合并/重写历史须单独授权。

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
5. 默认运行多 Agent 编排闸；按 [`references/MULTI-AGENT-PROTOCOL.md`](./references/MULTI-AGENT-PROTOCOL.md)
   制有界 packet。仅安全独立波次并行；否则派一个有界 Worker 或串行。用户可关闭或指定后端。
6. 一轮只做一项已批准目标；禁顺带重构、优化、升级、扩范围或改无关文件。
7. 主 Agent 回收结构化 result 后重跑目标测试、相关回归及适用 typecheck/lint/build/runtime；
   不得凭 Worker 自述或传输回执宣布成功。
8. 只更新新增事实与状态变化；历史用 `archive.py append`，原始日志留本地/CI。
9. 再跑 requirements/iteration gate；Reviewer 只读复核合同、diff、失败知识与验证。

默认：局部查询、局部修改、局部验证、**不调用 NotebookLM**。

## 多 Agent 编排

```text
python <skill>/scripts/agent_dispatch.py build --root <repo> \
  --manifest .iteration/dispatch.json \
  --capabilities .iteration/ridge-launch-profiles.json \
  --output-dir .iteration/agents
```

默认 `enabled:true`、后端 `auto`；顺序 Ridge Agent's Commune → tmux → 宿主 native sub-agent → serial。
仅能力缺失、明确 unsupported、或任务接受前 spawn 失败方降级；一经接受不得重派，防重复执行。
主 Agent 为每包标 `light|medium|complex`；脚本映射 `secondary+low|intermediate+medium|frontier+high`。
需更深推理时显式覆写 effort；不得由 Worker 自提级。Ridge 先调 `ridge_list_launch_profiles`，
把原样能力快照交 `--capabilities`；脚本选择 profile，spawn 前复核 revision。
写 Worker 仅在独立 worktree 且写集/独占资源无冲突时并行；共享工作区自动串行。
大包传文件路径或 Ridge stash URI，消息勿复制全文。投递、终端接受、Agent ACK、执行结果、主 Agent 验证
五层分列；只有匹配 baseline/packet/result hash 且验证证据齐全的 result 可进入主 Agent 联合验证。
Ridge 连接、模型与启动参数须从当前宿主 MCP schema、能力清单及 launcher help 动态发现；禁记录或猜测
本机端口、Token、路径、pane ID、模型名、命令。若无 Ridge 工具，报告缺失；不得以 Mycelium 代投。

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
