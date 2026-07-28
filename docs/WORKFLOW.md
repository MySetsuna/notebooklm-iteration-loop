# notebooklm-iteration-loop · 本仓适配

## 确定性验证

- 需求闸:`python scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md`
- 单元测试:`python -m unittest discover -s tests -v`
- preflight:`python scripts/preflight.py --project-root . --strict`
- skill 结构:`python <CODEX_HOME>/skills/.system/skill-creator/scripts/quick_validate.py .`
- codegraph:`codegraph status`；本仓当前未初始化，禁止 agent 自动 `init`
- coverage/E2E/Sonar:本仓仅含 skill 文档与两只标准库脚本，当前未配置；由单元测试与 skill validator
  作等价 checker，缺口保留于状态文档。

## CodeGraph

- 根:`<repo>`
- Markdown 不入 AST；Python 脚本与测试可索引。
- 首次:项目所有者决定是否 `codegraph init -i`；日常先 `status`，仅 pending/异常时 `sync`，查询用
  `codegraph explore`。

## NotebookLM

- notebook_id:`2bf9b409-7b68-4e9c-8bb4-66036003e2c3`
- 标题:`基于NotebookLM与codegraph的迭代开发工作流`
- 目标常驻来源:`REQUIREMENTS-SPEC`、`PROJECT-STATE`
- 删除既有来源前须用户明确同意。

## 历史

- `docs/archive/events-YYYY-MM.jsonl`：append-only；用 `scripts/archive.py tail` 有界读取。
- 当前合同留 `docs/iterations/`；结束合同、进度、guidance 不留 Markdown 副本。

## 人轨

- `docs/` 经 junction 联入 `C:\work-specs\notebooklm-iteration-loop`。
- agent 只读仓库 `docs/` 与 codegraph，不把 vault 当真相源。
