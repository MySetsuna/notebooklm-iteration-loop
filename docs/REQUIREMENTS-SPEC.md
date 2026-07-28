# notebooklm-iteration-loop · 需求规范

> Pending 未获用户明确批准前，不改对应代码、不生成执行合同、不上传需求来源。

## 待审批变更 (Pending Changes)

_无_

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

### REQ-005 · 增量认知与有界归档

- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 原始 Pending:`PENDING-REQ-20260729-01`
- 行为:常规轮复用 `PROJECT-STATE` 稳定基线，只按 Git 受控 diff 查询目标 symbol、直接影响与受影响测试；
  `planning_delta` 为假时不得重建全图、替换状态来源或查询 NotebookLM。历史以分片 JSONL 追加，按尾部/
  类型有界读取。
- 重建:首次、索引缺失/异常、核心边界/数据模型/重大分支变化或用户明确要求才全量重建；能力以
  `codegraph status` 与 `codegraph explore` 实测为准，不硬编码版本特定 MCP 工具名。
- 边界:不自动创建 CodeGraph 索引；不降低最终全量验证；不新增第三份状态文档；Active/Pending、当前合同、
  `PROJECT-STATE`、`WORKFLOW` 不转 JSONL；不声明未经 `token-usage --all` A/B 验证的收益。
- 验收:静态规约按场景加载；状态基线未变时仅更新 delta 尾段；JSONL 不整档反序列化；受影响测试先行、
  合同完成/不确定时仍全量验证。
- 追踪:`SKILL.md`、`references/`、`scripts/archive.py`、`templates/`、`tests/`。

## 修订账本 (Revision Ledger)

关闭 Pending、历史修订与批准证据见 `docs/archive/events-2026-07.jsonl`；本文件只保留当前 Active/Pending。
