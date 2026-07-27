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

## 修订账本 (Revision Ledger)

| 版本 | 日期 | Pending ID | 变更 | 关联/取代 | 批准证据 |
| --- | --- | --- | --- | --- | --- |
| v1.0.0 | 2026-07-27 | INITIAL | 从《AI 时代代码质量与验证重塑》提炼并实施首版治理 | - | 用户要求“作为下一步设计规划并实现” |
