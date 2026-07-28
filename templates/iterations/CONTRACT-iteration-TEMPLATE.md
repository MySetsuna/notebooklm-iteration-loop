# CONTRACT · iteration-{N}

## 生效需求引用

- `REQ-<...>`:`<目标行为>`
- 需求闸:`python <skill>/scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md`

## 本轮目标(常态 4–8 个,含 1 条主线)

1. [主线] <目标描述> — 验收:`<可被编译器/测试/退出码判定的命令及期望结果>`
2. <目标描述> — 验收:`<...>`

## 边界(constraints)

- 允许修改:`<路径/模块>`
- 不做:`<超出本轮范围的事>`
- 不动:`<不应触碰的模块/文件>`
- 预期 codegraph 影响:`<符号/调用路径/爆炸半径>`
- planning_delta:`true/false + 需求/边界/质量/外部阻塞/里程碑依据`
- 查询预算:`<目标 symbol、changed files、允许 impact/affected；无代码则 skip>`
- NotebookLM 往返:`<仅 planning_delta=true / skip>`

## 质量闸

| 闸 | 命令 | 门槛 |
| --- | --- | --- |
| compile/typecheck | `<command>` | exit 0 |
| unit/coverage | `<command>` | `<Active REQ / WORKFLOW 基线>` |
| E2E | `<command>` | `<场景全绿或明确不适用>` |
| Sonar/lint | `<command>` | `<quality gate / new issues=0>` |

先跑受影响测试；合同完成、影响不可判、跨边界或提交前必须补全量适用验证。

## 需求—代码—测试追踪

| Active REQ | 代码落点 | 测试/质量证据 |
| --- | --- | --- |
| `REQ-<...>` | `<path/symbol>` | `<test/gate>` |

## 停机条件

- `<触发条件>` → `<动作:回滚 / 停止 / 升级授权>`
- 出现未批准 Pending、越出允许路径、质量闸失败、codegraph 影响超出预期 → 停止并修订合同；保留用户改动，禁用 `git reset --hard`

## 依赖顺序

- `<目标间的强依赖,若有;尽量无强依赖以便并行推进>`
