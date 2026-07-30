# 有界多 Agent 编排协议

## 结论

默认启用编排闸，不默认强制并行。主 Agent 生成后端无关任务包；仅独立 DAG 波次满足隔离、
写集与资源无冲突时 fan-out。否则仍派一个有界 Worker 或串行派发。

此协议优先压缩**单 Worker 上下文**与可并行任务墙钟；总 token 未必下降。Anthropic 的公开实测指出，
多 Agent 复杂研究可显著缩短墙钟，但典型总 token 远高于普通对话；故收益只认同任务
`token-usage --all` A/B，不由架构推断。

## 角色

### 主 Agent

- 过 Git、需求、能力、预算与迭代闸；
- 只从 Active REQ 拆任务，取得 CodeGraph 最小 symbol/调用链证据；
- 生成 packet，选择后端，派发、监控、回收；
- 串行集成；复跑联合验证；更新状态、归档、提交与推送。

### Worker

- 只读自己的 packet 与允许文件；
- 开始时核对 `dispatch_id`、`packet_hash`、HEAD、worktree digest、CodeGraph revision；
- 不扩图、不扩写集、不批准需求、不调用 NotebookLM、不 commit/push/stash/checkout；
- 只写结构化 result；失败须留命令、退出码与证据指针。

Reviewer 默认只读；可与实现 Worker 并行，但不改代码。

## 任务包

由 `agent_dispatch.py build` 从 `templates/AGENT-DISPATCH.json` 生成。每包含：

- `dispatch_id`、`packet_hash`、`packet_bytes`；
- `baseline.head/worktree_digest/codegraph_revision`；
- 目标、精确 Active REQ 记录；
- symbol、CodeGraph 查询与有界事实/调用链证据；
- allowed files/write paths、约束、依赖；
- verification 命令与预期退出码；
- difficulty、目标 tier/effort、resolved profile 与 capability revision；
- Worker 禁止事项。

默认每包 `16384` bytes，总包 `49152` bytes，最多三个 Worker。大背景、原始日志、全 Git 历史、
聊天记录不得入包。

## 并行判据

编排默认 `enabled:true`。同一 DAG 波次仅全部成立方可并行：

1. 至少两个任务且无依赖路径；
2. 写路径无相等或目录前缀交叠；
3. `exclusive_resources` 不交叠；
4. 写任务声明 `isolation:"worktree"`；共享工作区写任务自动串行；
5. packet、Worker 与预算均未超限；
6. 基于同一 HEAD、worktree digest、CodeGraph revision。

后端为 `serial`、写隔离不足或发生冲突时，脚本输出 singleton waves 与
`parallel_rejections`，不强行并行。主 Agent 不自动合并冲突。

## 后端

`--backend auto|ridge|native|tmux|serial` 可覆盖模板。`auto` 顺序：

1. Ridge Agent's Commune；
2. tmux；
3. 宿主原生 sub-agent API；
4. serial。

后端只负责发现、spawn、投递、观察和回话；packet/result 语义不随之后端变化。
仅后端不可用、返回结构化 unsupported、或任务接受前 spawn 失败方进下一档。一旦终端/Agent 已接受，
不得向后备后端重派同 packet；任务执行失败亦不得当成后端不可用，须回主 Agent 裁决。

### Ridge

1. 从当前宿主 MCP 工具注册表发现 `ridge_*` 能力；不得按本机配置猜 server 名、端口、Token、路径或 pane；
2. 调 `ridge_list_launch_profiles`，原样保存有 revision 的能力快照；再以 `ridge_get_team_profile` 找目标 pane；
3. 主 Agent 标难度：`light→secondary+low`、`medium→intermediate+medium`、
   `complex→frontier+high`；必要时显式覆写 effort；
4. `agent_dispatch.py` 仅从能力快照解析 profile；无匹配即停，不猜模型名。spawn 前重查 revision，
   再以 `ridge_split_pane` 的 typed `launch_profile/reasoning_effort` 拉起；
5. 共用文件系统时只传 packet 路径；跨边界或包较大时用 `ridge_stash_data`，消息仅传
   `ridge://cache/<id>`；
6. `ridge_delegate_task` 派发，保存 `receiptId`；
7. `ridge_delivery_status`、`ridge_capture_pane`、`ridge_inbox_read` 观察；
8. Worker `ridge_acknowledge_receipt` 仅表示接受/拒绝任务；
9. 完成仍以含实际 profile/model/effort 的 result 经 `validate-result` 为准。

`submit_dispatched`、`terminalAccepted`、`agentAcknowledged` 均非完成证明。Ridge Inbox/Stash 为
内存态；`dispatch-plan.json` 与 result 文件才是本轮持久 SSOT。ACK 超时先查 receipt，勿盲重派。
若宿主未暴露 Ridge Commune 工具，须报告能力缺失并按后端顺序降级；Mycelium 属项目索引/记忆，
不得代替 Agent 会话投递。

### 难度与提级

难度由主 Agent 据已批准范围裁定；用户可覆盖。默认：

| 难度 | tier | effort | 适用 |
| --- | --- | --- | --- |
| light | secondary | low | 局部文档、独立小测、机械变换 |
| medium | intermediate | medium | 单模块功能、证据明确的修复 |
| complex | frontier | high | 跨边界、多假设冲突、高风险修改 |

两轮局部失败、跨架构边界、证据冲突、高风险或用户指定方可提级。提级须新开 Worker，并携原 packet、
checkpoint 与失败证据；旧 Worker 停写。禁静默原地切模。`xhigh` 仅显式请求且能力快照支持时可用。

### tmux / native

tmux 映射为开 pane/session、发送 packet 路径、回收 result；native 才映射宿主
`spawn_agent/send_message/wait_agent` 等内部 sub-agent API。
若后端无 ACK，须如实标记；不得伪造强回执。

## 状态机与回收

```text
validated → dispatched → terminal_accepted → agent_accepted
→ result_reported → leader_validated
```

不可由前态推导后态。Worker result 须匹配 packet，并含：

- `status: completed|failed|blocked`；
- changed paths；
- 每条验证命令、实际退出码、本地证据文件路径与 sha256；
- `input/cache_read/cache_write/output/total`；
- spawn 回执中的实际 profile/model/effort 与 capability revision；
- 可选 transport receipt；
- `result_hash`。

`validate-result` 拒绝陈旧 baseline、错 packet/result hash、越界写、残缺计量或伪完成。
`validate-batch` 拒绝缺失、重复或未知任务，并仅输出 `ready_for_lead_validation`；主 Agent 仍须自行跑联合质量闸。
Worker 将命令输出存本地证据文件并算 sha256；再写不含 `result_hash` 的 JSON，运行
`finalize-result`。勿由模型手算 canonical hash，亦勿以任意文本冒充执行证据。

## 最短命令

```text
python <skill>/scripts/agent_dispatch.py build --root <repo> \
  --manifest .iteration/dispatch.json --requirements docs/REQUIREMENTS-SPEC.md \
  --pending docs/PENDING-REQUIREMENTS.md \
  --capabilities .iteration/ridge-launch-profiles.json \
  --output-dir .iteration/agents

python <skill>/scripts/agent_dispatch.py finalize-result \
  --result .iteration/agents/result-worker-1.json

python <skill>/scripts/agent_dispatch.py validate-result --root <repo> \
  --plan .iteration/agents/dispatch-plan.json --result .iteration/agents/result-worker-1.json

python <skill>/scripts/agent_dispatch.py validate-batch --root <repo> \
  --plan .iteration/agents/dispatch-plan.json \
  --result .iteration/agents/result-worker-1.json --result .iteration/agents/result-worker-2.json
```

## A/B

同一 HEAD、REQ、模型、工具、权限、预算、验证命令；single 与 bounded-multi 冷/暖缓存分列。
墙钟从制包前计至主 Agent 联合验证结束。比较：

- 正确率与越界数；
- input、cache read/write、output、total；
- 主从全部 session；
- packet bytes 与重复上下文；
- 墙钟中位数、p95；
- 写冲突、重试与伪完成拒绝数。

仅 multi 的配对 `total` 置信上界低于 single，方可称总 token 节省；否则只称上下文分片或墙钟收益。

前向矩阵：

| 场景 | 必须行为 |
| --- | --- |
| 单一局部修复 | bounded single；正确率相同，墙钟/total 中位数不高于 single `1.25×` |
| 两个独立均衡任务 | 两 Worker；墙钟中位数不高于 `0.75×`，total 不高于 `1.35×` |
| 大共享背景 | 不复制无关背景；每包过字节闸；重复输入目标不高于 `15%` |
| 显式依赖链 | 上游经主 Agent 验证后才启下游 |
| 写集/独占资源交叠 | 自动串行；不得出现实际并发冲突 |
| 陈旧 HEAD/worktree | 派发或回收 fail closed |
| 伪投递/ACK/完成 | 无匹配 result 与验证证据，一律不认完成 |
| 越界/超预算 | 即停，不扩包、不持久化无证据失败知识 |

阈值须按项目与实测校准；安全负例任一误接受即协议失败。

研究依据：

- Anthropic, *How we built our multi-agent research system*:
  https://www.anthropic.com/engineering/multi-agent-research-system
- MCP Tasks SEP-1686:
  https://modelcontextprotocol.io/seps/1686-tasks
- Ridge Agent's Commune 本机协议:
  `C:/code/wind/static/docs/mcp-integration.md`
