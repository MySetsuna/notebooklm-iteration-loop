# notebooklm-iteration-loop · 需求规范

> NotebookLM 唯一已批准需求合同；Pending 仅存本地 `PENDING-REQUIREMENTS.md`。

- 需求版本:`v2.3.0`

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

- 批准依据:`用户要求深入调研并落地；后续批准 typed profile 路由，并明确默认降级序为 Ridge MCP、tmux、宿主 native sub-agent、serial`
- 状态:`ACTIVE`
- 版本:`v1.3.0`
- 行为:默认启用主控—执行 Agent 编排闸。主 Agent仅派发获批需求，并为每个 Worker 标注 `light|medium|complex` 难度；确定性映射为 `secondary+low|intermediate+medium|frontier+high`。Ridge 后端须先读取当前宿主 `ridge_list_launch_profiles` 能力快照，再解析实际 `launch_profile`，生成 typed spawn 参数；Skill、模板与脚本不得固化本机模型名、端口、Token、路径、pane ID 或启动命令。存在至少两个无依赖且安全隔离的任务包时并行；否则退化为有界单 Agent 或串行波次。
- 后端:`auto|ridge|tmux|native|serial` 可覆盖；`auto` 严格按 Ridge Agent's Commune、tmux、宿主 native sub-agent、serial 降级。仅能力缺失、结构化 unsupported 或任务接受前 spawn 失败可进入下一档；终端或 Agent 一经接受，不得跨后端重派同 packet。任务执行失败不等同后端不可用。投递、终端接受、Agent 确认、结果上报、主 Agent 验证分层记录。
- 边界:主 Agent保留难度裁定、审批、冲突裁决、最终验证、状态、提交与推送权；用户可覆盖难度，但 Worker 不自提级、不扩范围、不批准需求、不调用 NotebookLM。写任务仅在独立 worktree 且写集/资源无冲突时并行。两轮局部失败、跨架构边界、证据冲突、高风险或用户指定方可由主 Agent 新开更高 profile Worker；禁止静默原地切模。未以同任务 `token-usage --all` A/B 验证前，不宣称节省总 token。
- 验收:脚本拒绝 Pending/未知需求、陈旧 baseline、非法难度、缺失/陈旧能力快照、无匹配 tier/effort 的 profile、超限或 hash 不符任务包、并行冲突、残缺结果与伪完成。plan 固定 Ridge→tmux→native→serial 顺序及接受前降级规则；packet 绑定难度、目标 tier/effort、resolved profile 与 capability revision；结果回收须含实际 profile/model/effort、changed paths、验证退出码、证据 sha256、token 分项及 packet/result hash；实际执行配置与 packet 不符即拒绝。Ridge 回执不得解释为已执行。
- 追踪:`SKILL.md`、`references/MULTI-AGENT-PROTOCOL.md`、`scripts/agent_dispatch.py`、`templates/AGENT-DISPATCH.json`、`templates/AGENT-RESULT.json`、`tests/test_agent_dispatch.py`。

### REQ-010 · 可选 Kiro 事后补记

- 批准依据:`用户要求增加可选子 Skill；需求与已落地实现按 Kiro 格式补记，但不得作为设计或规划依据`
- 状态:`ACTIVE`
- 版本:`v1.1.0`
- 行为:仅用户明确说 `执行Kiro补记` 或调用 `$record-kiro-spec` 时，将已批准需求、已验证代码实现及
  成功验证证据补记至 `.kiro/specs/<name>/requirements.md|design.md|tasks.md`。
- 边界:该三文件仅供记录与他人工作流对齐，不构成需求合同、设计输入、任务授权、代码事实源或
  NotebookLM 常驻来源；Pending、提案、未实现任务、推测及失败验证不得写入。
- 验收:子 Skill 禁止隐式调用；先有界抽样目标仓既有 spec，沿用项目本地标题、追踪与元数据惯例；
  无先例才用官方三件套保底。脚本仅更新自身标记区块并保留既有 Kiro 内容，拒绝非法 slug、
  未绑定需求、无证据实现、非零验证及越界目标；任务均为 `[x]` 事后完成项。`spec.json` 仅仓内已有
  先例且目标缺失时生成，既有文件不改。
- 追踪:`skills/record-kiro-spec/`、`tests/test_record_kiro_spec.py`、`SKILL.md`。

### REQ-011 · 请求绑定审批入口闸

- 批准依据:`用户确认审批步骤被跳过后明确要求“那现在开始修复吧”；继而要求修复完提交推送并同步`
- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:每项用户任务在任何开工动作前，须生成绑定当前请求 hash 的 intake。完全落在 Active 条款内方可
  分类 `active`；新增、修订、删除、Fix 或含未决范围/验收/假设者必须写 Pending、展示完整规范稿并停机；
  用户明确批准该已展示草稿后，方以 `approved` intake 提升并实施。
- 边界:空 Pending 不构成批准证据；旧 intake、模糊肯定、未展示草稿、模型自判或 NotebookLM 建议不得
  替代用户批准。脚本无法读取宿主聊天，故须由主 Agent 保存当前请求原文；宿主级强制执行不作虚假承诺。
- 验收:`requirements_gate.py assert-task-executable` 缺 request/intake 即拒绝；intake 绑定请求、
  Active、Pending 三 hash。`pending` 永不可执行；`approved` 须绑定此前 pending intake、草稿 hash、
  Pending ID、Active 结果及批准原话；陈旧/伪完整 manifest、未清 Pending、文档漂移均拒绝。
- 追踪:`SKILL.md`、`references/QUALITY-AND-REQUIREMENTS.md`、`scripts/requirements_intake.py`、
  `scripts/requirements_gate.py`、`templates/REQUIREMENTS-INTAKE.json`、`tests/test_requirements_intake.py`。

### REQ-012 · 统一使用 chatgpt-nlm-research 发起深度调研

- Approval evidence:`批准 PENDING-REQ-20260822-01，按此草案推进`
- Status:`ACTIVE`
- Version:`v1.0.0`
- Behavior:`迭代工作流进入深度调研时，以已安装的 chatgpt-nlm-research 为唯一调研发起端：调用 research_start(provider=chatgpt)，轮询同一浏览器任务的 research_status，并用 research_import 将已持久化报告导入目标 NotebookLM 笔记本。`
- Boundary:`工作流不得启动或回退到 NotebookLM Deep Research；桥接或登录会话不可用时须失败并给出可诊断阻断信息。NotebookLM MCP 仍可用于报告导入后的来源存储与查询；保留既有热/冷触发门、状态快照、审批和安全约束；不新增 API key、cookie、浏览器存储或凭据。`
- Acceptance:`受控文件检索除迁移说明/历史记录外，不再存在会启动或回退 NotebookLM Deep Research 的工作流指令、脚本或测试；相关回归测试、仓库原生测试/静态检查及 git diff --check 通过；提交后当前分支工作树干净且远端包含该实现。`
- Traceability:`SKILL.md、README/工作流说明、references、templates、scripts 与 tests 中的深度调研路径；以 chatgpt-nlm-research 的 research_start/research_status/research_import 调用及阻断测试验证。
## 修订账本 (Revision Ledger)

关闭 Pending、历史修订与批准证据见 `docs/archive/events-2026-07.jsonl`；本文件只保留当前 Active。
