# 《AI 时代代码质量与验证重塑》提炼与对抗评审

## 用户意图精华

1. 最大化 SonarScanner、coverage、E2E：不仅判质量，还用于推演需求、债务、重构与 Bug。
2. 为 skill 建立依赖检索与安装能力。
3. 用工具与流程防止 LLM 理解偏差、愿景偏离。
4. 模糊需求先转成易理解范式，经用户审批才落地。
5. RFC 不增生：只保留一份需求文档，在其中维护 Pending、Active 与修订关联。

## Reframe 表

| 原建议 | 更高价值可测切片 | 验收 | 结论 |
| --- | --- | --- | --- |
| 自动全局安装、自愈 | 只读 preflight + 项目级恢复 + 授权阶梯 | strict exit code、只读测试 | reframed 采纳 |
| `.codegraph` 缺失即自动初始化 | 遵仓库规约先询问，再初始化 | 用户批准记录 + status | reframed 采纳 |
| 原始 Sonar/Coverage 日志上传 | 有界摘要 + evidence pointer + codegraph impact | PROJECT-STATE schema | reframed 采纳 |
| `git reset --hard` 纠偏 | 停止越界、保留用户改动、修订状态与合同 | SKILL 禁令 | 原建议 non-goal；替代采纳 |
| 多份 RFC 永久来源 | 单一 REQUIREMENTS-SPEC 内 Pending/Active/Ledger | gate tests | 用户修订后采纳 |
| 笔记本只有 PROJECT-STATE | 两份单一职责真相源 | invariant scan | reframed 采纳 |
| coverage/E2E 自动推新需求 | 只产 Pending 候选，用户审批后生效 | requirement gate | reframed 采纳 |

## 采纳边界

质量工具是 checker 与规划输入，不是模型裁判。CodeGraph 仍是代码事实源；NotebookLM 仍是 maker。
任何产品语义变化不能因工具告警自动变成 Active 需求。

## 基于两份新真相源的下一轮建议

NotebookLM 排序为：CLI 黑盒集成测试、质量遥测解析器、preflight 插件化、changed-code/Sonar
new-code 策略、需求关系校验。

### NotebookLM 原文

> 优先级 1：CLI 黑盒集成测试与协同验证。新增集成测试，模拟 preflight、requirements gate 与
> telemetry 链路；真实临时目录中组合运行，覆盖至少三种失败场景。
>
> 优先级 2：质量遥测降维解析器。新增 `telemetry_parser.py`，读取 coverage/Sonar JSON，
> 提取复杂度、未覆盖行并关联 codegraph；以有界结构写入状态文档。
>
> 优先级 3：Preflight 可扩展性重构。把硬编码探测改为 manifest 驱动，使新增工具无需修改 Python。
>
> 优先级 4：Changed-code 质量策略。区分 overall 与 changed-code coverage，并接入 Sonar
> New Code；建议 changed-code 失败返回非零。
>
> 优先级 5：需求原子替换与 Pending 校验。检查 `supersedes` 指向真实 Active REQ，并生成
> Revision Ledger 更新预览。

## 第二次对抗评审

| NotebookLM 建议 | 代码事实/问题 | Reframe | 结论 |
| --- | --- | --- | --- |
| 增强 `scripts/quick_validate.py` | 本仓无此文件；validator 属外部 skill-creator | 集成测试以 subprocess 调本仓两只 CLI，再单独调用外部 validator | reframed 采纳 |
| 测“Pipe 通信” | 两 CLI 无 pipe 协议 | 测真实临时目录、stdout JSON 与 exit 0/2/3 | reframed 采纳 |
| YAML manifest | 本仓坚持标准库；引入 YAML 解析依赖无必要 | 改 JSON manifest；只允许声明 command/file/package，不执行任意 shell | reframed 采纳 |
| 1MB→2KB、复杂度排行榜 | 阈值与字段均无 Active REQ 支撑 | 限记录数/字段/schema；解析与 codegraph 关联分层，emit fragment 不覆写状态 | reframed 采纳 |
| changed-code coverage 固定 80% | 虚假统一阈值，违反项目自定基线 | evaluator 要求显式 policy；缺阈值即不可判，不暗设数字 | non-goal+替代 |
| 自动更新 Revision Ledger | 容易越过用户审批、破坏原子性 | 校验 Pending→Active 关联并生成 preview，不自动批准/改写 | reframed 采纳 |

CodeGraph 影响：`detect` 影响 7 symbols，`inspect_document` 影响 8 symbols；下一轮须同步加厚其 CLI
与测试调用方，不能只改核心函数。
