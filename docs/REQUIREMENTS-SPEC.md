# notebooklm-iteration-loop · 需求规范

> Pending 未获用户明确批准前，不改对应代码、不生成执行合同、不上传需求来源。

## 待审批变更 (Pending Changes)

### PENDING-REQ-20260729-01 · CodeGraph 增量认知与版本兼容

- 状态:`PENDING`
- 类型:`MODIFY`
- 原始意图:以 Token 节省为首要目标；在保留 CodeGraph 架构事实校验与 NotebookLM 两份常驻真相源的
  前提下，避免每轮把 CodeGraph 检索当成全仓初始化，并让历史归档可按需读取而非整份重载。
- 关联 Active:`REQ-001`、`REQ-003`、`REQ-004`。
- 目标行为:
  1. 初始化或满足重建条件时建立完整架构基线；常规轮次先复用 `PROJECT-STATE` 的基线，仅验证
     本轮目标 symbol、直接影响与边界变化。
  2. 工作流适配已安装 CodeGraph 的 MCP 面：以 `codegraph_explore` 为主；索引健康以 CLI
     `codegraph status` 判断；仅在 pending、watcher 不可用或索引异常时 `codegraph sync`。
  3. `PROJECT-STATE` 区分稳定架构基线与本轮 delta；模块边界未变时不重绘 Mermaid、不重述全图。
  4. 明确全量重建触发条件，并消除“工作树 dirty 禁止 codegraph”与“开发后必须 impact 校验”的冲突。
  5. 调研并确定本地迭代存档能否改为 append-only JSONL：单条记录可独立解析、按尾部/ID/类型读取，
     避免为获取近期历史而读取整份归档；无须保留人读 Markdown 派生物。
- 范围:`SKILL.md`、`README*`、`references/`、`templates/`、本仓 `docs/` 与相应确定性测试；不改
  NotebookLM 现有来源，不新增第三份常驻真相文档。
- 非目标:不降低代码事实校验、需求审批、质量闸或两份常驻来源约束；不在无 `.codegraph/` 的项目
  自动创建索引；不承诺未经基准测量的 token 降幅；不保留归档的人读 Markdown 副本；不把
  `PROJECT-STATE`、`REQUIREMENTS-SPEC` 或 NotebookLM 常驻来源改成 JSONL。
- 假设与待确认:
  1. CodeGraph 版本及 MCP 工具面随安装版本变化，最终措辞须以深研与本机 `1.4.1` 实测为准。
  2. `PROJECT-STATE` 的稳定段足以承担 agent 长期认知；是否需独立本地 `project_context.md` 留待调研结论。
  3. token 收益须以同类任务的 `token-usage --all` 基线/改后对照确认。
  4. JSONL 仅适于 append-only archive；是否取代 `LOG.md`、逐轮报告、NotebookLM 原文指导，以及
     分片、索引与迁移策略，留待深研结论。
- 确定性验收:
  1. 常规迭代指令不再要求无条件 `codegraph sync`、全量架构勾勒，且无废弃 MCP 工具名。
  2. 模板含“架构基线 / 本轮影响 delta / 全量重建触发条件”；边界未变时允许保留原架构图。
  3. Git 新鲜度规则允许在本轮受控 diff 上做只读影响校验，仍禁止未经用户裁定的远端分叉扫描。
  4. 新增或更新的确定性校验覆盖上述不变量；现有测试与 skill validator 全绿。
  5. 若采纳 JSONL，schema、追加/尾读 API 与迁移/兼容策略须有确定性测试；查询近期记录不得依赖
     全文件反序列化。
- 预期落点:`SKILL.md`、`README.md`、`README.zh-CN.md`、`references/QUALITY-AND-REQUIREMENTS.md`、
  `templates/PROJECT-STATE.md`、`templates/WORKFLOW.md`、`docs/WORKFLOW.md`、`tests/`。
- 深研结论(仍待批准):采纳「稳定架构基线 + 本轮 delta」；不新增第三份状态文档。常规轮先读
  `PROJECT-STATE`、Git 受控 diff 与索引健康，只查目标 symbol/直接依赖；首次、索引缺失/异常、
  重大分支/核心边界/数据模型变更或用户明确要求时才全量重建。以本机命令能力探测为准，最低依赖
  `codegraph status`、`codegraph explore`，不得把版本特定 MCP 名称写成硬前提。
- 归档决策(仍待批准):仅将 `LOG`、已结束 iteration 报告与 NotebookLM guidance 等历史改为
  分片 append-only JSONL；`PROJECT-STATE`、`REQUIREMENTS-SPEC`、合同仍保留当前形态。记录以
  schema/version、id、时间、类型、事实/证据指针、受影响路径/symbol、验证结果、下一步为最小字段；
  提供有界 tail/type 读取，按需添加可重建索引，禁止整档反序列化。无 Markdown 归档副本。
- 拒采项:深研中未被本机/上游证实的固定 token 降幅、500ms watcher、专有 `cgc doctor`、工具 preset、
  PageRank 与固定阈值；收益只以同任务 `token-usage --all` A/B 实测声明。

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
- 版本:`v1.0.0`
- 行为:模糊新需求或修订先进入单一 `REQUIREMENTS-SPEC.md` Pending；用户明确批准后才生效。
- 边界:批准前禁止对应业务代码、执行合同与 NotebookLM 需求来源更新；旧 Active 继续生效。
- 验收:`requirements_gate.py assert-executable` 对 Pending 返回非零；空 Pending 返回 0。
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

## 修订账本 (Revision Ledger)

| 版本 | 日期 | Pending ID | 变更 | 关联/取代 | 批准证据 |
| --- | --- | --- | --- | --- | --- |
| v1.0.0 | 2026-07-27 | INITIAL | 从《AI 时代代码质量与验证重塑》提炼并实施首版治理 | - | 用户要求“作为下一步设计规划并实现” |
