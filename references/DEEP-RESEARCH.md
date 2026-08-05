# NotebookLM 深度调研

仅在外部生态、架构选型或根因无法由代码/现有两源确定，且结论会复用时使用：

```text
nlm research start "<question>" -n <notebook_id> -m deep
nlm research status
```

## 首选入口：ChatGPT Deep Research 桥接 MCP

已安装的 `chatgpt-nlm-research` 是本机可选的深度调研入口，负责：

1. `research_start` 用 `provider="chatgpt"` 在已登录 ChatGPT Web 页面点击 Deep Research、输入并发送，返回可持久追踪的浏览器 task ID；
2. `research_status` 按同一 task ID 读取 Chrome CDP 页面 DOM；连续两次得到相同且非流式报告后，才写入本地 gitignored 数据目录；
3. `research_import` 只通过现有 `notebooklm-mcp` 的 `source_add(source_type="file", wait=true)` 导入该报告。

宿主服务器名为 `chatgpt-nlm-research`，最小调用序列：

```json
{"query":"<question>","notebook_id":"<notebook-id>","provider":"chatgpt"}
{"task_id":"<returned-task-id>","wait_seconds":30}
{"task_id":"<same-task-id>"}
```

若 Chrome CDP 同时有多个 ChatGPT 页面，先从 `/json/list` 取目标 `id`，将其作为 `browser_target_id` 传入；勿凭猜测切换页面或重提任务。

三行依次对应 `research_start`、`research_status`、`research_import`；不得用标题或新生成的伪 ID 替代返回的 task ID。

调用时必须提供目标 `notebook_id`。报告正文与任务元数据只留本地；原始日志、密钥、浏览器凭据不得上传。

ChatGPT Web 配额或限流时，改用 `provider="auto"`，桥接器仅在明确识别 quota/rate-limit 页面信号时切换 NotebookLM Deep Research；
也可直接用 `provider="notebooklm"`。NotebookLM 回退结果只导入 `result_type=5` 的深度调研报告，不导入其余网页来源。

ChatGPT 报告在 NotebookLM 中仅作临时第三来源。决策完成后压缩为经代码/测试核验的 note 或 JSONL 事实，删除临时报告来源，恢复两份常驻来源。

完成后仅导入调研报告为临时第三来源，绝不导入数十网页参考。以两常驻源和报告发起一次有格式、
有证据上限的决策问题；建议必须经代码事实与确定性验收对抗核验。相关实现完成后，将结论压成 note/
JSONL 事实，删除临时报告来源，恢复两常驻源。
