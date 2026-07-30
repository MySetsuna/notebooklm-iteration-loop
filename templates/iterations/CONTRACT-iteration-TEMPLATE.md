# CONTRACT · iteration-{N}

## 生效需求引用

- `REQ-<...>`:`<目标行为>`
- 任务闸:`python <skill>/scripts/requirements_gate.py assert-task-executable --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md --request-file .iteration/request.txt --intake-file .iteration/intakes/INTAKE-ID.json`

## 本轮目标(常态 4–8 个,含 1 条主线)

1. [主线] <目标描述> — 验收:`<可被编译器/测试/退出码判定的命令及期望结果>`
2. <目标描述> — 验收:`<...>`

## 边界(constraints)

- 允许修改:`<路径/模块>`
- 不做:`<超出本轮范围的事>`
- 不动:`<不应触碰的模块/文件>`
- 预期 codegraph 影响:`<符号/调用路径/爆炸半径>`
- 查询预算:`<目标 symbol、changed files、允许 impact/affected；无代码则 skip>`
- NotebookLM trigger:`<HOT_LOOP_SKIP | 十类 trigger 之一 + 证据>`
- 决策包/状态快照:`<仅冷闸触发时填写；否则 skip>`
- NotebookLM 闸:`python <skill>/scripts/notebook_gate.py assert-allowed ...`
- Context package:`python <skill>/scripts/context_compiler.py --root <repo> --task "..." --output .iteration/context.json`
- 迭代预算:`python <skill>/scripts/iteration_budget.py check --budget .iteration/budget.json --usage .iteration/usage.json`
- 硬闸:`python <skill>/scripts/iteration_gate.py --root <repo> --context .iteration/context.json --budget .iteration/budget.json --usage .iteration/usage.json`
- Reviewer:`<只审合同、diff、失败知识与验证；不改代码>`

## 质量闸

| 闸 | 命令 | 门槛 |
| --- | --- | --- |
| compile/typecheck | `<command>` | exit 0 |
| unit/coverage | `<command>` | `<Active REQ / WORKFLOW 基线>` |
| E2E | `<command>` | `<场景全绿或明确不适用>` |
| Sonar/lint | `<command>` | `<quality gate / new issues=0>` |

先跑受影响测试；合同完成、影响不可判、跨边界或提交前必须补全量适用验证。

Context package 未列出的文件、symbol、测试不得主动探索；预算超限即停并归档。

## 需求—代码—测试追踪

| Active REQ | 代码落点 | 测试/质量证据 |
| --- | --- | --- |
| `REQ-<...>` | `<path/symbol>` | `<test/gate>` |

## 停机条件

- `<触发条件>` → `<动作:回滚 / 停止 / 升级授权>`
- 出现未批准 Pending、越出允许路径、质量闸失败、codegraph 影响超出预期 → 停止并修订合同；保留用户改动，禁用 `git reset --hard`

## 依赖顺序

- `<目标间的强依赖,若有;尽量无强依赖以便并行推进>`
