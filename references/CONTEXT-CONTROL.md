# Agent 控制层

## Context Compiler

先以显式任务、symbol、file、test、constraint、failed knowledge 生成 `.iteration/context.json`：

```text
python <skill>/scripts/context_compiler.py --root <repo> --task "fix auth timeout" \
  --requirement REQ-012 \
  --symbol AuthService.login --file auth/service.py --test tests/test_auth_timeout.py --modify auth/service.py \
  --constraint "OAuth contract unchanged" --budget .iteration/budget.json
```

输出固定为任务包：`task`、`symbols`、`files`、`tests`、`constraints`、`failed_knowledge`、
`requirements`、`codegraph.queries`、`read_policy.allowed_files` 与 `write_policy.allowed_paths`。
`--requirement` 可重复；编译器内部读取 Markdown 真相源，仅把指定 ID 条目物化进任务包，并以
`--requirements-max-bytes` 硬限输出。入口与写集均须显式提供；
不从 Git diff 或全仓自动推断。路径必须位于项目根，超出 `files_read` 上限即失败。

需求条目独立读写：

```text
python <skill>/scripts/requirements_store.py read --file docs/REQUIREMENTS-SPEC.md --id REQ-012 --max-bytes 16384
python <skill>/scripts/requirements_store.py write --file docs/REQUIREMENTS-SPEC.md \
  --pending-file docs/PENDING-REQUIREMENTS.md --operation <operation.json> \
  --evidence "<Active 写入或删除的用户批准/拒绝证据>"
```

操作文件 schema 为
`{"schema_version":1,"upsert":[{"id":"...","section":"pending|active","markdown":"### ..."}],"remove":[]}`。
Pending 与 Active 分文件；写入只改列明 ID。Pending 新增不触碰 Active 文件；批准迁移先写 Active
再删 Pending，故中断时 Pending 仍阻断，fail closed。Active 写入与任何删除必须附证据。
`markdown` 须含 `REQUIREMENTS-SPEC` 模板所列完整字段；缺字段、空值、`<...>`/`TODO`/`TBD`
占位值、非法 Pending 类型及非 ACTIVE 条目拒绝。
批准后的修订证据仍按 `ARCHIVE-JSONL.md` 追加 ledger 事件。

Agent 只可按 `read_policy` 取上下文。CodeGraph 仅查 `codegraph.queries`，不能把探索结果扩成全仓扫描。
上下文包为运行时缓存，不上传 NotebookLM，不作第三份常驻真相源。

`codegraph.queries` 只含显式 symbol 与 `--codegraph-query`；files/tests 不自动转成图查询。
编译器与 `iteration_gate.py` 均拒绝超过 `max.codegraph_queries` 的计划。

编译后必须过硬闸：

```text
python <skill>/scripts/iteration_gate.py --root <repo> \
  --context .iteration/context.json --budget .iteration/budget.json --usage .iteration/usage.json
```

硬闸会检查显式入口、禁止全图、允许写集、禁止背景复述与预算；返回 `2` 即停止。

## Iteration Budget

由脚本初始化预算与计量文件；已有文件默认拒绝覆盖。每轮按实际工具调用更新 usage JSON：

```text
python <skill>/scripts/iteration_budget.py init --output .iteration/budget.json
python <skill>/scripts/iteration_budget.py init-usage --output .iteration/usage.json
python <skill>/scripts/iteration_budget.py check \
  --budget .iteration/budget.json --usage .iteration/usage.json
```

超限返回 `2`，且必须停止相应动作并归档；不把预算失败改写为“无进展”。预算是上限，不是承诺的 token 节省。

## Failed Knowledge / Reviewer

`PROJECT-STATE` 的 `Known failed approaches` 只收录有命令、退出码、回归或 evidence pointer 的失败。
Reviewer 只读审合同、context、diff、失败知识和验证结果；不改代码、不替 Executor 自行扩大读取面。

## 冷循环运行包

决策包、PROJECT-STATE 快照与 NotebookLM 输出合同见
[`HOT-COLD-PROTOCOL.md`](./HOT-COLD-PROTOCOL.md)。三者皆存 `.iteration/`；快照只用于替换同名
NotebookLM 来源，不构成第三常驻来源。
