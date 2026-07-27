# CONTRACT · iteration-1

## Active 需求

- REQ-001～REQ-004；Pending 闸须返回 0。

## 目标

1. [主线] 建立单一需求规范、Pending 审批状态机与机器闸。
2. 建立只读依赖/质量能力 preflight 与安全安装阶梯。
3. 建立 Sonar/Coverage/E2E→质量遥测→规划候选的治理 schema。
4. 把单一来源不变量迁移为两份单一职责真相源。
5. 加厚模板、中英文说明、测试与 CodeGraph 证据。

## 边界

- 允许:`SKILL.md`、`README*`、`references/`、`scripts/`、`tests/`、`templates/`、`docs/`。
- 禁止:静默安装工具；上传原始长日志；自动提交/合并；删除 NotebookLM 来源；覆盖既有用户改动。

## 质量闸

- `python -m unittest discover -s tests -v` → exit 0。
- `python scripts/preflight.py --project-root . --strict` → blockers=[]、exit 0。
- `python .../quick_validate.py .` → valid、exit 0。
- `codegraph index` → Python 文件进入索引。

## 停机条件

- 发现 Pending、外部删除未获授权、测试失败、用户改动冲突 → 停止对应动作并保留工作区。
