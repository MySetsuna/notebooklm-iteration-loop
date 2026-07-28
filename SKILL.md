---
name: notebooklm-iteration-loop
description: >
  用 CodeGraph 与 NotebookLM 持续迭代项目；维护两份常驻真相源、需求审批、确定性质量闸、
  按需深研与有界 JSONL 历史。当用户要求以 NotebookLM 规划下一步、初始化或整理项目笔记本、
  将质量信号转为需求/债务/重构候选、或需要 CodeGraph 驱动的迭代流程时使用。
---

# CodeGraph + NotebookLM 迭代循环

目标：代码事实可证、规划按需、历史有界读取；不为每轮重新理解全仓。

## 不变量

1. 代码事实问 CodeGraph；NotebookLM 只作规划/根因 maker，冲突时以前者和确定性验证为准。
2. 笔记本常驻且仅两源：获批 `REQUIREMENTS-SPEC` 与 `PROJECT-STATE`。Pending、历史、原始日志不上传。
3. Pending 未获明确批准，禁止对应实现、合同与需求源替换；运行 `requirements_gate.py`。
4. 不自动 `codegraph init`；索引不存在/不可用，记录缺口并由项目所有者决定。
5. 质量结论必须有命令、退出码、计数或证据指针；原始长日志只留本地/CI artifact。
6. 删除 NotebookLM 来源、覆盖用户工作、远端合并/重写历史均须单独授权。
7. Token 收益以同任务 `token-usage --all` 的 A/B 计量，不承诺固定百分比。

## 开工闸

首次扫描或规划前：检查分支、upstream、`git fetch --prune`、ahead/behind、工作区。非 `0/0`、
detached、无 upstream 或用户遗留 dirty 时，先取得“有意分叉/继续当前基线”的裁定；不得擅自
pull/merge/rebase/reset/checkout/stash。**本轮实现已产生的受控 diff 可做只读 impact/测试选择，
不重跑远端裁定。**

然后运行：

```text
python <skill>/scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md
python <skill>/scripts/preflight.py --project-root <repo> --strict
```

质量/需求细则读 [`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md)。

## 普通迭代（最短路径）

1. 读 Active、当前合同、`PROJECT-STATE` 稳定基线和 `archive.py tail` 的少量相关记录；勿整读历史。
2. 先看 `git diff --name-only/stat`，判定 `planning_delta`：仅当需求语义、架构边界、质量回归、
   外部阻塞或里程碑变化时为真。
3. 无代码改动时跳过 CodeGraph。否则先 `codegraph status`；仅 status 显示 pending/异常、后台
   catch-up 不可用或用户要求时 `codegraph sync`。通过当前安装的 `--help`/MCP 工具表确认能力，
   用 `codegraph explore <目标 symbol/问题>` 批量取直接事实；只对 changed symbol/file 查 impact/
   affected tests。不得把版本特定 MCP 名硬写成前提。
4. 按合同实现。先跑受影响测试；合同完成、影响不可判、跨边界或提交前必须跑全部适用确定性闸。
5. 仅在稳定基线变更时更新 `PROJECT-STATE` 的基线/图；本轮证据、影响、质量结果写 delta 尾段。
   稳定前缀不重排、不插日期/UUID，以利缓存复用。
6. `planning_delta=true` 才替换 `PROJECT-STATE` 来源并 `notebook_query`；否则只归档事实，跳过
   NotebookLM 往返。新产品语义仍进 Pending。
7. 用 `archive.py append` 写一条结构化历史；历史报告、guidance、已关闭账本不再生成 Markdown 副本。

## 全量重建触发

仅以下情形：首次基线、索引缺失/损坏/状态异常、重大分支切换、核心模块边界或数据模型变更、
查询事实与代码矛盾、或用户明确要求。重建后才全图、全模块图与完整架构叙述。

## 文档与归档

- `PROJECT-STATE`、Active/Pending、当前合同、`WORKFLOW` 保持 Markdown；它们是当前真相或审批界面。
- 历史仅 `docs/archive/events-YYYY-MM.jsonl`：分片、append-only、tail/type 有界读取；不先造索引。
- Schema、迁移和命令见 [`references/ARCHIVE-JSONL.md`](./references/ARCHIVE-JSONL.md)。

## 按需路线

- 不合规笔记本、来源清理、notes/愿景：读 [`references/INITIALIZATION-AND-NOTES.md`](./references/INITIALIZATION-AND-NOTES.md)。
- 外部生态/疑难根因：读 [`references/DEEP-RESEARCH.md`](./references/DEEP-RESEARCH.md)。
- MCP 安装/认证：读配套 [`skills/install-notebooklm-mcp/SKILL.md`](./skills/install-notebooklm-mcp/SKILL.md)；
  外部 CDP 已登录但 NLM 未刷新时读 `skills/refresh-notebooklm-auth/SKILL.md`。
- 文档库 junction：读配套 [`skills/link-to-doc-library/SKILL.md`](./skills/link-to-doc-library/SKILL.md)。

## 度量与停机

同一任务记录输入/缓存读写/输出/总量、工具调用数、墙钟时间和确定性结果；比较全量基线与增量路径。
出现 Pending、索引矛盾、验证失败、未经授权删除/远端操作或无进展预算耗尽时停止相应动作并归档证据。
