# 质量遥测与需求治理

主 `SKILL.md` 触发以下情形时读本文件：

- 用户给出模糊需求，或修订既有需求；
- 合同要引入 SonarScanner、coverage、E2E 或其他质量闸；
- 验证结果要用于推演需求、技术债、重构或 Bug；
- 需检索、补装或降级质量工具链。

## 1. 两份常驻真相源

NotebookLM 中每个项目常驻且仅常驻两份来源：

| 来源 | 内容 | 更新时机 |
| --- | --- | --- |
| `REQUIREMENTS-SPEC` | 已批准的当前需求；单文件、覆盖替换 | 用户明确批准 Pending 后 |
| `PROJECT-STATE` | 代码事实、架构、质量遥测、验证与差距 | 每轮验证及 codegraph 刷新后 |

Pending 只存在于本地 `docs/REQUIREMENTS-SPEC.md`，不上传；NotebookLM 继续读取上一版已批准需求。
迭代报告、原始日志、历史 RFC、指导原文不作常驻来源。

## 2. 需求范式与审批闸

### 2.1 模糊需求先范式化

把用户原话写入 Pending，并补齐：

- ID、类型：`NEW | MODIFY | REMOVE | FIX`；
- 原始意图；
- 目标行为与用户可观察结果；
- 范围、非目标、不可动边界；
- 关联的 Active `REQ-*`；
- 假设与待确认点；
- 确定性验收信号；
- 需求—代码—测试预期落点。

不得把模型推测伪装成用户要求；每项假设须显式列出。

### 2.2 Pending 状态机

```text
draft/pending ──用户修改──> pending
draft/pending ──用户批准──> active + revision ledger
draft/pending ──用户拒绝──> 从 Pending 移除；历史只留 git
active ──新修订──> 新 Pending（原 Active 继续生效）
新 Pending 获批 ──> 替换/补充 Active；旧条款记 superseded
```

硬闸：

1. 存在 Pending 时，禁止为该 Pending 修改业务代码、生成执行合同、同步需求来源。
2. “批准”“Approved”等明确同意只批准当前展示过的具体 Pending；模糊肯定不算。
3. 批准后先把 Pending 融入 Active、更新 Revision Ledger，再上传新来源；确认入库后方删旧来源。
4. 多个 Pending 可并存，但须分别列关联项；冲突时停下请用户裁定。
5. 运行 `python <skill>/scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md`
   作机器闸；退出码非 0 则不得开发。

## 3. 本机全局质量工具链

先通过主 `SKILL.md` 的「Git 新鲜度硬闸」；未通过时禁止 preflight 后续扫描与质量规划。

先运行只读预检：

```text
python <skill>/scripts/preflight.py --project-root <repo> --strict
```

`--strict` 仅报告能力，不安装、不改配置。质量 CLI 统一装到当前用户/本机全局，跨项目复用；
项目仅保留配置与调用命令，不因本 skill 改 manifest/lockfile。

| 能力 | 探测命令 | 首选全局安装 |
| --- | --- | --- |
| Sonar | `sonar-scanner` / `dotnet-sonarscanner` | 官方 SonarScanner CLI 解压并把 `bin` 加入 PATH；.NET 项目可用 `dotnet tool install --global dotnet-sonarscanner` |
| Python coverage | `coverage` / `coverage3` | `pipx install coverage`；无 pipx 时 `python -m pip install --user coverage` |
| Node coverage | `c8` / `nyc` | 按项目现有命令择一：`npm install -g c8` 或 `npm install -g nyc` |
| .NET coverage | `dotnet-coverage` | `dotnet tool install --global dotnet-coverage` |
| Web E2E | `playwright` / `cypress` | 按项目配置择一：`npm install -g playwright` 或 `npm install -g cypress`；需要时再装用户级浏览器资产 |

执行阶梯：

1. 复用已可发现的全局 CLI；按项目语言/现有配置只补适用项，不一次装遍所有生态。
2. 用户已明确要求全局多项目工具链时，直接作用户级全局安装；否则先列清单取得一次授权。
3. 安装后用新进程执行 `<command> --version`（Sonar 可用 `-v`），再重跑 preflight。
4. 全局 CLI 无法满足项目插件/import 解析时，记录限制并请用户裁定；禁止静默退回项目级安装。
5. 管理员权限、系统 PATH、系统服务、容器、付费 Sonar 服务仍须明确授权；密钥不得落盘。
6. NotebookLM MCP 缺失或认证坏掉，转配套 `install-notebooklm-mcp`。
7. `.codegraph/` 缺失或 `codegraph status` 非 ready 时依仓库 `AGENTS.md`：要求询问则先问，再运行
   `codegraph init -i`；不得把目录存在误判为可用索引。

降级规则：

- Sonar 未配置：可用项目 linter/编译器替代静态闸，但须在状态文档标明缺口；
- coverage 未配置：测试可继续，迭代不得宣称“覆盖闸已通过”；
- E2E 不适用：写明理由与等价终态测试；
- 项目原生测试命令、codegraph、NotebookLM 任一必需能力缺失：阻断循环，不伪造通过。

## 4. 质量遥测：只传摘要，不传原始长日志

原始日志留本地临时目录或 CI artifacts。`PROJECT-STATE.md` 仅写有界摘要：

```markdown
## 质量遥测

### 验证能力
| 能力 | 命令 | 状态 | 基线/门槛 |

### 本轮结果
| 闸 | 退出码 | 结果 | 相对基线 | 证据 |

### 待处理信号
| ID | 类别 | 严重度 | 文件/符号 | codegraph 影响 | 证据 | 处置 |
```

规则：

- Sonar：记录 quality gate、新增 issue 数、严重度、规则与符号；优先“新增问题为 0”，不让旧债掩盖回归。
- Coverage：记录 line/branch 及 changed-code 差值、未覆盖分支；阈值来自 Active 需求或 `WORKFLOW.md`，不临时拍脑袋。
- E2E：记录场景、首次失败步骤、错误类别、重跑结果；区分产品回归、需求缺口、环境故障、疑似 flaky。
- Codegraph：为高价值信号附 `context/impact/trace` 事实；索引不支持该语言时明确写“不可判”，不得猜。
- 所有结论带命令、退出码、证据路径或 CI URL；禁止模型自评分。

## 5. 从遥测到下一步

遥测只能提出候选，不得越过审批闸直接改愿景：

| 信号 | 候选 | 必须补的 checker |
| --- | --- | --- |
| E2E 断言失败 | Bug 或需求歧义 | 复现、契约引用、失败步骤 |
| 未覆盖关键分支 | 测试缺口或需求缺口 | 分支可达性、Active REQ |
| Sonar 新安全/可靠性问题 | Bug/债务 | 规则原文、受影响符号 |
| 重复/复杂度集中 | 重构候选 | codegraph impact、E2E 防护 |
| 跨层/循环依赖 | 架构偏离 | 修改前后依赖事实 |

优先级不用虚构精确分数；按以下元组排序：

`阻断状态 → 安全/正确性严重度 → Active 需求关联 → changed-code → blast radius → 修复可逆性`

NotebookLM 可推演四类输出：需求 Pending、技术债合同、重构合同、Bug 合同。每条仍须过引用核查、
codegraph 事实核查与用户审批规则。

## 6. 防偏离闭环

合同须引用 Active `REQ-*`，并写：

- 允许修改路径与禁止路径；
- 预期 codegraph 影响面；
- 测试/coverage/E2E/Sonar 闸；
- 停机条件；
- 需求—代码—测试追踪表。

实现后以 `git diff --name-only`、codegraph impact/trace、质量闸共同核对。偏离时保留用户改动，
不得 `git reset --hard`；停止越界工作，把事实写回状态文档，修订合同后再执行。
