---
name: link-to-doc-library
description: >
  通过 Windows NTFS Junction 把一个文件夹连入指定的「文档库」(本地汇总目录,供 Obsidian 等
  工具一起索引)。当用户说「把 xx 连入工作文档库」「连进文档库」「link xxx to doc library」,
  或 notebooklm-iteration-loop 在初始化/脚手架后要求确保项目 docs 已联入 vault 时使用。
---

# Link Folder to Doc Library

把一个项目子目录通过 Windows 目录联接(Junction)映射进统一的本地汇总目录,方便
Obsidian / 全文搜索 / 笔记工具**跨项目一起浏览**。

文件实际仍存放在源位置,对源的读写穿透生效;删除 junction **不影响**源。

## 角色边界(与 notebooklm-iteration-loop 的分工)

| 谁 | 做什么 |
| --- | --- |
| **人 + Obsidian vault** | 关联浏览、复盘、第二脑外壳 |
| **agent 查项目现状** | 只读仓库内 `docs/PROJECT-STATE.md`、`docs/LOG.md`、codegraph — **不经本 skill、不查 vault** |
| **本 skill** | 只做 junction 创建/校验(人轨基础设施),**不**当 agent 记忆总线,不写 vault 镜像 |

双写、每轮同步 vault、Obsidian MCP 当现状源 — **一律不做**。

## 文档库注册表

| 库名(用户口语) | 路径 |
| --- | --- |
| 工作文档库 / work / 默认 | `C:\work-specs` |

> 用户提到上表未列出的库名时,**先 ask** 该库本地路径(一句话)。可临时用,不必强制写回本表;
> 用户说「以后都用」再登记。

## 被 notebooklm-iteration-loop 调用时(标准入参)

nlm skill 在**脚手架落 `docs/` 之后**或**初始化终态**或**九步开工前发现未联入**时触发本 skill。
默认参数(调用方未另指定则用此):

| 参数 | 默认 |
| --- | --- |
| 源文件夹 | `<目标项目根>/docs`(绝对路径) |
| 文档库 | 工作文档库 `C:\work-specs` |
| junction 名 | **仓库根目录名**(见下节命名规则,勿用字面 `docs`) |

**幂等**:目标库下已有同名 junction 且 Target 相同 → **noop**,简短报告「已联入」即止,不重复创建、不问用户。

非 Windows 或无法建 junction → **跳过并记一句**,不阻断 nlm 主环。

## 执行步骤

### 1. 解析参数

- **源文件夹**(必填):本地目录绝对路径。例:`C:\workcode\xxx\.kiro\specs`、`C:\code\foo\docs`。
- **文档库**(可选):口语库名。缺省 → 工作文档库。

若只说「连进去」且无 nlm 默认上下文可推断路径 → 问一句源路径。

### 2. 解析目标库路径

查注册表。命中 → 用注册路径;未命中 → 问用户。

库目录不存在则创建(非破坏性,无需确认):

```powershell
New-Item -ItemType Directory -Path '<lib>' -Force | Out-Null
```

### 3. 校验源路径

```powershell
Test-Path -LiteralPath '<source>'
```

不存在 → 报错并停止(nlm 调用方应先确保 `docs/` 已建)。

### 4. 计算 junction 名

按优先级:

1. **`docs` 模式**(nlm 标准):源路径匹配 `\\docs$` 或 `/docs$` → 取**父目录**名。
   - 例:`C:\code\myapp\docs` → `myapp`
2. **`.kiro/specs` 模式**:源匹配 `\.kiro\specs$` 或含 `\.kiro\specs\` → 取 `.kiro` 前一段路径的最末目录名。
   - 例:`C:\workcode\wxmini\.kiro\specs` → `wxmini`
3. **退路**:源路径自身最末目录名。
   - 例:`D:\notes\foo` → `foo`

结果在用户语境里不直观时可反问。**禁止**把项目 docs 联成库内字面名 `docs`(多项目会撞名)。

### 5. 检查冲突

```powershell
$target = Join-Path '<lib>' '<name>'
$exists = Test-Path -LiteralPath $target
if ($exists) {
    $item = Get-Item -LiteralPath $target -Force
    if ($item.LinkType -eq 'Junction') {
        # 已是 junction:比较 Target;同一目标 → noop;不同目标 → 询问
    } else {
        # 普通目录或文件:报错停止,不要覆盖
    }
}
```

冲突时问用户:覆盖(仅可先删 **junction** 再重建)/ 改名 / 取消。**禁止**静默覆盖普通目录或文件。

### 6. 创建 junction

```powershell
New-Item -ItemType Junction -Path '<lib>\<name>' -Target '<source>' | Out-Null
```

### 7. 验证 + 报告

```powershell
Get-ChildItem -LiteralPath '<lib>' -Force |
    Where-Object { $_.Name -eq '<name>' } |
    Select-Object Name, LinkType, @{Name='Target',Expression={$_.Target}} |
    Format-Table -AutoSize
```

简短回报:

- 新建 / 已存在 junction 的路径与目标
- 库目录路径(首次创建时尤其要说)
- 提醒:Obsidian 须把该库当 vault 打开才能看到;agent 查现状仍读仓库 `docs/`,不读 vault

## 安全约束

- **只创建**:可建 junction 与库目录;普通文件、普通目录、源目录**绝不删或覆盖**。
- **冲突先问**:路径占用一律询问(幂等同目标除外)。
- **仅 Windows**:依赖 NTFS junction;跨盘符可用,跨主机/网络盘未保证。
- **不修改源**:全程不动源目录内容。

## 示例

> 用户:"把 C:\workcode\foo\.kiro\specs 连入工作文档库"

→ 源 = 该路径,库 = `C:\work-specs`,名 = `foo` → 创建/noop → 报告。

> nlm skill 初始化后自动触发

→ 源 = `<repo>\docs`,库 = 默认,名 = 仓库根目录名 → 幂等联入 → 一句报告,继续主环。

> 用户:"把 D:\stuff 连入笔记库"

→ "笔记库" 未登记 → ask 路径 → 再继续。
