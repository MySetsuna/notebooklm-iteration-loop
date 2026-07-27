# notebooklm-iteration-loop · 本仓适配

## 确定性验证

- 需求闸:`python scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md`
- 单元测试:`python -m unittest discover -s tests -v`
- preflight:`python scripts/preflight.py --project-root . --strict`
- skill 结构:`python <CODEX_HOME>/skills/.system/skill-creator/scripts/quick_validate.py .`
- codegraph:`codegraph index` 后 `codegraph_status`
- coverage/E2E/Sonar:本仓仅含 skill 文档与两只标准库脚本，当前未配置；由单元测试与 skill validator
  作等价 checker，缺口保留于状态文档。

## CodeGraph

- 根:`<repo>`
- Markdown 不入 AST；Python 脚本与测试可索引。
- 首次:`codegraph init -i`；改动后:`codegraph sync`，索引可疑时:`codegraph index`。

## NotebookLM

- notebook_id:`2bf9b409-7b68-4e9c-8bb4-66036003e2c3`
- 标题:`基于NotebookLM与codegraph的迭代开发工作流`
- 目标常驻来源:`REQUIREMENTS-SPEC`、`PROJECT-STATE`
- 删除既有来源前须用户明确同意。

## 人轨

- `docs/` 经 junction 联入 `C:\work-specs\notebooklm-iteration-loop`。
- agent 只读仓库 `docs/` 与 codegraph，不把 vault 当真相源。
