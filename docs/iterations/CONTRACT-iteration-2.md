# CONTRACT · iteration-2

## Active 需求引用

- REQ-001：质量遥测有界化并驱动规划候选。
- REQ-002：Pending 审批与修订关系确定性校验。
- REQ-004：只读、可扩展、安全的依赖预检。
- 开工闸:`python scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md`。

## 本轮目标（约 2 工程师工作日）

1. [主线] 新增标准库质量遥测 normalizer：至少支持 coverage.py JSON、LCOV 与 Sonar issues JSON
   的有界统一 schema；只 emit JSON/Markdown fragment，不覆写 `PROJECT-STATE`。
2. 新增显式质量 policy evaluator：区分 overall/changed-code、Sonar new issues；无项目阈值则
   返回 `not_evaluable`，禁止内置 80% 等虚假统一值。
3. 将 preflight 探测扩展为安全 JSON manifest：声明 command/file/package 能力，禁止执行 manifest
   中任意 shell；保留现有 built-in detectors。
4. 加厚 requirements gate：校验 Pending 关联的 Active REQ 存在、ID 唯一、必填字段完整；
   只生成审批 preview，不自动批准或改写 Ledger。
5. 建立 subprocess CLI 黑盒套件：真实临时目录覆盖正常、缺依赖、Pending、坏结构、坏 manifest、
   遥测截断与 policy 不可判等路径。
6. 同步 reference/templates/README 与 CodeGraph 事实，跑全闸。

## 允许/禁止

- 允许:`scripts/`、`tests/`、`references/`、`templates/`、`SKILL.md`、`README*`、`docs/`。
- 禁止:新增第三方 Python 依赖；执行 manifest shell；写回原始质量报告；自动批准需求；
  内置 coverage 数字门槛；改动/删除 NotebookLM 旧来源。

## 质量闸

| 闸 | 门槛 |
| --- | --- |
| unittest | 新旧测试全绿、exit 0 |
| CLI integration | exit 0/2/3 与 JSON schema 符合 fixture |
| requirements gate | Pending/坏关联/坏结构均阻断 |
| telemetry | 输入有界处理、输出字段/条数上限确定；不含原始长日志 |
| preflight | 现有行为兼容；坏 manifest fail closed；全程只读 |
| skill validator | valid、exit 0 |
| CodeGraph | 新脚本/测试均入索引，impact 与文档一致 |

## 停机条件

- 需新增依赖、无法安全解析格式、policy 必须猜阈值、需求 preview 会写 Active、测试需联网 →
  停止该目标；其余独立目标继续。
