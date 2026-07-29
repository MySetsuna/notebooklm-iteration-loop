# notebooklm-iteration-loop · 需求规范

> NotebookLM 唯一已批准需求合同；Pending 仅存本地 `PENDING-REQUIREMENTS.md`。

- 需求版本:`v2.0.0`

## 正式需求 (Active Requirements)

### REQ-001 · 质量信号驱动迭代规划

- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:SonarScanner、coverage、E2E、编译器与测试结果须转成有界质量遥测，并可提出需求、
  技术债、架构重构与 Bug 候选。
- 边界:原始长日志不上传 NotebookLM；模型自述不作验证。
- 验收:模板含质量遥测 schema，主 skill 规定退出码、相对基线、证据与 codegraph 影响。
- 追踪:`references/QUALITY-AND-REQUIREMENTS.md`、`templates/PROJECT-STATE.md`、`SKILL.md`。

### REQ-002 · 模糊需求范式化与审批

- 状态:`ACTIVE`
- 版本:`v2.0.0`
- 行为:模糊新需求或修订先进入本地 `PENDING-REQUIREMENTS.md`；用户明确批准后才融入本文件。
- 边界:Pending 完整内容不得进入已批准需求源或 NotebookLM；批准前禁止对应业务代码、执行合同与来源更新。
- 验收:`requirements_gate.py assert-executable` 同时检查 Active/Pending 两文件；Pending 非空返回非零。
- 追踪:`scripts/requirements_gate.py`、`tests/test_requirements_gate.py`、
  `templates/REQUIREMENTS-SPEC.md`。

### REQ-003 · 两份常驻真相源

- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:每个项目笔记本常驻且仅常驻 `REQUIREMENTS-SPEC` 与 `PROJECT-STATE`，均覆盖替换。
- 边界:Pending、迭代报告、原始日志、历史快照不作常驻来源；研究报告与排障日志只可临时存在。
- 验收:主 skill、README 与全部模板不再声明“仅一份 PROJECT-STATE 来源”。
- 追踪:`SKILL.md`、`README.md`、`README.zh-CN.md`、`templates/WORKFLOW.md`。

### REQ-004 · 安全依赖预检与安装阶梯

- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:进入循环前只读探测 codegraph、NotebookLM CLI、项目原生验证及 Sonar/Coverage/E2E 能力。
- 边界:预检不安装、不写配置；新增工具、全局安装、系统服务与 MCP 注册须授权。
- 验收:`preflight.py --strict` 在必需能力齐全时返回 0，缺口时返回 2；测试覆盖只读性与 blocker。
- 追踪:`scripts/preflight.py`、`tests/test_preflight.py`。

### REQ-005 · 增量认知与有界归档

- 状态:`ACTIVE`
- 版本:`v2.0.0`
- 原始 Pending:`PENDING-REQ-20260729-01`
- 行为:常规热循环复用稳定基线，只按任务查询目标 symbol、直接影响与受影响测试；NotebookLM 默认禁用，
  仅 `notebook_gate.py` 命中批准触发条件才进入冷循环。历史以分片 JSONL 追加，按尾部/类型有界读取。
- 重建:首次、索引缺失/异常、核心边界/数据模型/重大分支变化或用户明确要求才全量重建；能力以
  `codegraph status` 与 `codegraph explore` 实测为准，不硬编码版本特定 MCP 工具名。
- 边界:不自动创建 CodeGraph 索引；不降低最终全量验证；不新增第三份状态文档；Active/Pending、当前合同、
  `PROJECT-STATE`、`WORKFLOW` 不转 JSONL；不声明未经 `token-usage --all` A/B 验证的收益。
- 验收:静态规约按场景加载；NotebookLM 无触发时硬拒绝；JSONL 不整档反序列化；受影响测试先行，
  合同完成/不确定时仍全量验证。
- 追踪:`SKILL.md`、`references/`、`scripts/archive.py`、`templates/`、`tests/`。

### REQ-006 · Agent 上下文编排、预算与失败知识

- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 批准依据:`用户明确要求按 Context Compiler、Iteration Budget、Failed Knowledge 方案改动`
- 行为:每轮先生成任务限定 `.iteration/context.json`，列出允许 files/symbols/tests/constraints；Agent 不得主动探索包外内容。
  预算以机器可读 JSON 定义 exploration、CodeGraph queries、files、retries、token 上限，超限即停并归档。
  `PROJECT-STATE` 保存有证据的失败路径；NotebookLM 仅输出 hypothesis/risk/candidate/question，CodeGraph、合同与测试裁决实现。
- 边界:不自动初始化 CodeGraph；不把上下文包升级为第三份常驻 NotebookLM 来源；不承诺固定 token 节省；不凭模型自述写失败知识。
- 验收:`context_compiler.py` 只接受显式入口且拒绝越界路径；`iteration_gate.py` 拒绝全图、无入口、越界写与背景复述；预算超限返回 2。
- 追踪:`SKILL.md`、`scripts/context_compiler.py`、`scripts/iteration_budget.py`、`scripts/iteration_gate.py`、`templates/`、`tests/`。

### REQ-007 · 需求条目有界读写

- 批准依据:`用户明确采用所示方案，并要求写入亦由脚本实现后推进`
- 状态:`ACTIVE`
- 版本:`v2.0.0`
- 行为:`REQUIREMENTS-SPEC.md` 仅承载 Active；`PENDING-REQUIREMENTS.md` 仅承载本地 Pending。每轮以显式 ID
  选取少量条目；脚本内部解析整文件，仅把选段送入 Agent 上下文。
- 边界:不得按“最新若干行”推断当前有效需求；Pending 不上传；Active 写入与删除须有明确批准/决定证据。
- 验收:`requirements_store.py` 拒绝缺失 ID、字节超限、缺字段、空值及占位条目；Pending 写入不改变 Active 文件。
- 追踪:`scripts/requirements_store.py`、`scripts/context_compiler.py`、`scripts/iteration_gate.py`、`tests/`。

### REQ-008 · 低消耗热/冷迭代协议

- 批准依据:`用户明确回复“按修正版批准并推进”`
- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:事实权威与规范权威分轴；Codex 默认执行局部查询、最小修改和确定性验证的热循环。
  仅需求冲突、跨架构边界、多方案、两轮失败、证据冲突、状态失配、新候选、里程碑、高风险或用户明确要求
  可触发 NotebookLM 冷循环。调用前生成含当前 HEAD、需求版本/hash、diff、Pending 索引及有界决策包的
  `PROJECT-STATE` 运行快照。
- 边界:NotebookLM 不裁决代码事实、根因、需求批准或质量；输出不得直接实施，须回到代码、CodeGraph、
  已批准需求与测试验证。动态元数据只置运行快照尾部，不扰 tracked 稳定前缀。
- 验收:`state_snapshot.py` 拒绝 HEAD/version/需求 hash/Pending hash/current diff 失配，并绑定决策 hash；
  `notebook_gate.py` 无触发即拒绝，两轮失败须有两个不同失败实验及命令/退出码/证据指针，决策包超限、
  残缺或快照不含同一决策即拒绝；模板含规定输出合同与停止条件。
- 追踪:`SKILL.md`、`references/HOT-COLD-PROTOCOL.md`、`scripts/state_snapshot.py`、
  `scripts/notebook_gate.py`、`templates/PROJECT-STATE.md`、`tests/`。

### REQ-009 · 有界多 Agent 编排

- 批准依据:`用户要求深入调研并落地；主 Agent 审批派发，携带需求与调用链，Agent's Commune/tmux/宿主 Agent 可配置且默认触发`
- 状态:`ACTIVE`
- 版本:`v1.1.0`
- 行为:默认启用主控—执行 Agent 编排闸。主 Agent 仅派发获批需求，并为每个执行 Agent 生成有界任务包，包含目标、精确 Active REQ、CodeGraph symbol/调用链证据、允许读写路径、约束、验证命令及 HEAD/worktree/CodeGraph 基线。存在至少两个无依赖且安全隔离的任务包时并行；否则退化为一个有界执行 Agent或串行波次。
- 后端:`auto|ridge|native|tmux|serial` 可由参数或用户要求覆盖；`auto` 按 Ridge Agent's Commune、宿主 native、tmux、serial 探测。投递、终端接受、Agent 确认、结果上报、主 Agent 验证分层记录。
- 边界:主 Agent 保留审批、冲突裁决、最终验证、状态更新、提交与推送权；Worker 不扩范围、不互相覆盖、不批准需求、不调用 NotebookLM。写任务仅在独立 worktree 且写集/独占资源无冲突时并行。未以同任务 `token-usage --all` A/B 验证前，不宣称节省总 token。
- 验收:确定性脚本拒绝 Pending/未知需求、陈旧 HEAD/worktree、超限或 hash 不符任务包、并行写集/控制路径/独占资源交叠、残缺结果与伪完成；生成包有字节上限和稳定 hash；结果回收须含 changed paths、验证命令/退出码、本地证据文件 sha256、主从 token 分项及 packet/result hash。Ridge 回执不得被解释为已执行。
- 追踪:`SKILL.md`、`references/MULTI-AGENT-PROTOCOL.md`、`scripts/agent_dispatch.py`、`templates/AGENT-DISPATCH.json`、`templates/AGENT-RESULT.json`、`tests/test_agent_dispatch.py`。
## 修订账本 (Revision Ledger)

关闭 Pending、历史修订与批准证据见 `docs/archive/events-2026-07.jsonl`；本文件只保留当前 Active。
