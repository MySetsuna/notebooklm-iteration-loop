# JSONL 历史归档

历史只存 `docs/archive/events-YYYY-MM.jsonl`；一行一个独立 JSON 对象。Git 保留被迁移 Markdown 的
历史，工作树不保留人读副本。

最小 schema：

```json
{"schema_version":1,"id":"unique-id","at":"YYYY-MM-DD","type":"iteration|guidance|ledger|telemetry","facts":["bounded fact"],"evidence":["command/sha/path"],"paths":["relative/path"],"symbols":["symbol"],"next":["next action"]}
```

- `facts` 是已验证事实，不写原始模型长文或终端全文。
- `evidence` 只存命令、退出码、hash、artifact/CI 指针。
- `id` 由调用方稳定指定；不需要人读标题。
- 任意 ID 查找只在规模证明必要时增加**可重建** sidecar；当前禁止 SQLite/二进制索引。

使用本 skill 的标准库工具：

```text
python <skill>/scripts/archive.py append --root docs/archive --record <record.json>
python <skill>/scripts/archive.py tail --root docs/archive --limit 5 --type iteration --max-bytes 65536
python <skill>/scripts/archive.py migrate-markdown --root docs/archive --source <old.md> --id <id> --at YYYY-MM-DD --type guidance
```

`tail` 从文件尾部按字节上限读取；结果不足时宁缺勿整档扫描。迁移只做一次，迁完删除旧 Markdown，
并在 JSONL 留原路径与 SHA-256 证据。
