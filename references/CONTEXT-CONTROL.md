# Agent 控制层

## Context Compiler

先以显式任务、symbol、file、test、constraint、failed knowledge 生成 `.iteration/context.json`：

```text
python <skill>/scripts/context_compiler.py --root <repo> --task "fix auth timeout" \
  --symbol AuthService.login --file auth/service.py --test tests/test_auth_timeout.py --modify auth/service.py \
  --constraint "OAuth contract unchanged" --budget .iteration/budget.json
```

输出固定为任务包：`task`、`symbols`、`files`、`tests`、`constraints`、`failed_knowledge`、
`codegraph.queries`、`read_policy.allowed_files` 与 `write_policy.allowed_paths`。入口与写集均须显式提供；
不从 Git diff 或全仓自动推断。路径必须位于项目根，超出 `files_read` 上限即失败。

Agent 只可按 `read_policy` 取上下文。CodeGraph 仅查 `codegraph.queries`，不能把探索结果扩成全仓扫描。
上下文包为运行时缓存，不上传 NotebookLM，不作第三份常驻真相源。

编译后必须过硬闸：

```text
python <skill>/scripts/iteration_gate.py --root <repo> \
  --context .iteration/context.json --budget .iteration/budget.json --usage .iteration/usage.json
```

硬闸会检查显式入口、禁止全图、允许写集、禁止背景复述与预算；返回 `2` 即停止。

## Iteration Budget

复制 `templates/ITERATION-BUDGET.json` 至 `.iteration/budget.json`，每轮维护 usage JSON：

```text
python <skill>/scripts/iteration_budget.py check \
  --budget .iteration/budget.json --usage .iteration/usage.json
```

超限返回 `2`，且必须停止相应动作并归档；不把预算失败改写为“无进展”。预算是上限，不是承诺的 token 节省。

## Failed Knowledge / Reviewer

`PROJECT-STATE` 的 `Known failed approaches` 只收录有命令、退出码、回归或 evidence pointer 的失败。
Reviewer 只读审合同、context、diff、失败知识和验证结果；不改代码、不替 Executor 自行扩大读取面。
