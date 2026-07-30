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
10. `.kiro/specs/` 仅作事后对齐记录，不作需求、设计、规划或实现权威。
11. 每项用户任务须先绑定请求 intake；空 Pending 文件不再足以证明任务已获批准。
12. 文档统一 UTF-8 无 BOM；Windows PowerShell 5.1 读取须显式用
    `Get-Content -Encoding UTF8`，不得以默认 ANSI 解码所得文本回写。

## 请求入口闸

此闸先于 Git 开工闸、CodeGraph 探索、上下文编译、派发及代码修改。

1. 把当前用户请求原文存入本地 `.iteration/request.txt`（不提交、不上传），复制
   `templates/REQUIREMENTS-INTAKE.json` 为 `.iteration/intake-decision.json`。
2. 仅可分类：
   - `active`：任务完全落在现有 Active `REQ-*`；列出全部 ID。
   - `pending`：新增/修订/删除/Fix 需求，或目标、范围、非目标、验收、假设任一未定。
   - `approved`：当前消息明确批准此前展示的具体 Pending；须绑定此前 intake。
3. `pending` 时，先以 `requirements_store.py write` 写完整 Pending，再生成 intake：

```text
python <skill>/scripts/requirements_intake.py build \
  --request-file .iteration/request.txt \
  --decision .iteration/intake-decision.json \
  --intake-file .iteration/intakes/INTAKE-ID.json
```

向用户原样展示 Pending ID、规范稿与 `draft_sha256`，随即结束本轮；仅可请其批准、修改或拒绝。
禁止开工、制合同、派 Agent、调 NotebookLM、写 Kiro 记录或改业务代码。
`pending` build 以退出码 `3` 表示“已记录但未批准”，属预期停机，不得重试绕过。

4. 用户批准时，以 `requirements_store.py write --evidence "<批准原话>"` 原子提升并移除 Pending；
   `approved` intake 以 `--previous-intake <此前 intake>` 绑定已展示草稿。模糊肯定、未展示草稿、
   缺旧 intake 或无批准原话均不得提升。
5. `active` 或 `approved` 生成 intake 后，必须运行：

```text
python <skill>/scripts/requirements_gate.py assert-task-executable \
  --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md \
  --request-file .iteration/request.txt --intake-file .iteration/intakes/INTAKE-ID.json
```

缺 intake、请求/hash 失配、文档变化、Pending 未清或批准链不完整皆停止。脚本不能读取宿主聊天；
故主 Agent 不执行此入口闸即属流程失败，不得用旧 intake 或空 Pending 代替。

## 开工闸

先检查分支、upstream、ahead/behind、dirty。非 `0/0`、detached、无 upstream 或遗留 dirty 时，
先取得继续当前基线的裁定；禁擅自 pull/merge/rebase/reset/checkout/stash。

```text
python <skill>/scripts/preflight.py --project-root <repo> --strict
```

需求审批与质量细则见 [`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md)。

## 默认热循环

1. 入口 intake 已通过 `assert-task-executable`；首轮运行 `iteration_budget.py init` 与
   `iteration_budget.py init-usage` 建立 `.iteration/budget.json` 和 `.iteration/usage.json`；
   每轮按实际工具调用更新 usage。
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
10. 用户明确说 `执行Kiro补记` 或调用 `$record-kiro-spec` 时，方读取并执行
    [`skills/record-kiro-spec/SKILL.md`](./skills/record-kiro-spec/SKILL.md)；否则跳过。

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
需要登录、刷新凭据或执行 NotebookLM CLI 前，先使用
[`skills/refresh-notebooklm-auth/SKILL.md`](./skills/refresh-notebooklm-auth/SKILL.md)。
本机固定可通代理为 `http://127.0.0.1:51081`：CLI 环境变量与 Chrome
`--proxy-server` 必须同时传入；不得只给其中一端，也不得改系统代理。

```text
python <skill>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py launch \
  --proxy http://127.0.0.1:51081 --cdp-port 19222
python <skill>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py status \
  --cdp-url http://127.0.0.1:19222
```

NotebookLM 当前有效站点可能为 `https://notebook.google.com/`；不得因域名与
`notebooklm.google.com` 不同而判定未登录。认证提取只输出成功/失败及非敏感元数据，
不得读取、打印、提交 Cookie、Token 或本地凭据。

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
- `.kiro/specs/`：可选事后对齐副本；不上传 NotebookLM，不反向驱动主流程。

出现 Pending、状态快照失配、触发证据不足、索引矛盾、验证失败、越界写或预算耗尽，即停止相应动作。
