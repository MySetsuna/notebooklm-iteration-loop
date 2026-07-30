---
name: install-notebooklm-mcp
description: >
  在一台设备上安装并认证 notebooklm-mcp（NotebookLM MCP 服务器），接入 Codex / Claude Code
  等宿主。当用户说「装 notebooklm mcp / 接入 NotebookLM / 在这台电脑上配置 notebooklm-mcp /
  把 NotebookLM 接进 Codex / notebooklm 认证失败要重新登录」时使用；notebooklm-iteration-loop
  发现 MCP 未装、未连或 cookie 失效时也必须触发本 skill。当前系统固定可通代理为
  `http://127.0.0.1:51081`；如用户明确给出新代理才覆盖。认证使用「外部 CDP」法
  在不改系统代理的前提下完成 Google 登录抓取 cookie。cookie 约 2–4 周过期，过期后同样用本 skill
  重新认证。
---

# 安装 & 认证 notebooklm-mcp

> 本 skill 由 [notebooklm-iteration-loop](https://github.com/MySetsuna/notebooklm-iteration-loop)
> 仓库 `skills/install-notebooklm-mcp/` 管理；与主 skill、`link-to-doc-library` 同仓。

把 [`notebooklm-mcp-cli`](https://github.com/jacob-bd/notebooklm-mcp-cli) 装到本机并接入宿主
（下文以 **Codex** 注册为例；Claude Code / 其他宿主见步骤 4 备注）。它靠**浏览器 cookie**
认证（无需 API key），因此最难的一步是「让浏览器能访问 Google 并完成登录」。在被墙/需代理的
网络下，直接 `nlm login` 会失败——本 skill 用工具内置的**外部 CDP 通道**：我们自己启动一个
带代理的 Chrome，用户在里面登录，再让 `nlm` 连上去抽 cookie，全程**不改系统代理、不动用户
日常浏览器**。

> 关键事实（决定为什么要这么绕，均来自源码 `notebooklm_tools/utils/cdp.py`、`cli/main.py`）：
> - `nlm login` 默认（builtin）会自己启动 Chrome，且强制加 `--disable-extensions` + 隔离 `--user-data-dir`，**并不加 `--proxy-server`** → 只会走「系统代理」。所以代理扩展没用，除非改系统代理。
> - 但只要给 `nlm login` 传一个**非默认**的 `--cdp-url`（≠ `http://127.0.0.1:18800`），它就切换到**外部 CDP 模式**（`extract_cookies_via_existing_cdp`）：不自己开浏览器，而是连到我们已经启动好的、带代理的 Chrome 去抽 cookie。这就是我们要用的路子。
> - 工具连本地 CDP（`127.0.0.1:<port>`）时会主动绕过代理，所以即使设了 `HTTP_PROXY` 也不会把 CDP 请求错误地发去代理。

整个流程分 5 步。默认始终携带 `http://127.0.0.1:51081`；仅用户明确要求直连或更换代理时才改变。

---

## 前置条件

- **Python 3.8+** 和 **`uv`**（推荐；没有则用 `pip`/`pipx`）。
- 一个 **Chromium 内核浏览器**（Chrome / Edge / Brave / Chromium 皆可）。
- 一个能访问 **NotebookLM** 的 **Google 账号**。
- 本机已安装目标宿主 CLI（**Codex** 和/或 **Claude Code** 等）；步骤 4 按实际宿主注册。

下面命令以 **Windows / PowerShell** 为主（本 skill 在 Windows 上验证过）。macOS/Linux 的差异见文末「跨平台适配」。路径里用 `~` 或 `$env:USERPROFILE` 动态解析，**不要硬编码具体用户名**。

## 被 notebooklm-iteration-loop 调用时

主 skill 在以下情况**必须先读本文件全文并执行**，完成后再回主环：

| 时机 | 动作 |
| --- | --- |
| 无 `notebooklm-mcp` 工具 / `nlm` 不在可执行路径 | 完整走步骤 1–5 |
| `nlm login --check` 失败或 MCP 报未认证 | 重跑步骤 3B + 步骤 5；无需重装 |
| 用户只说「装/认证 NotebookLM」 | 只跑本 skill，不进迭代九步 |

**阻断主环**：未装妥或未认证成功时，**不要**假装能 `notebook_query` / `source_add`。

---

## 步骤 1：安装 CLI

```powershell
uv tool install notebooklm-mcp-cli
```

会生成两个可执行文件：`nlm`（管理/认证）和 `notebooklm-mcp`（MCP 服务器）。默认装到 `~\.local\bin\`，**该目录通常不在 PATH**。记下完整路径备用：

```powershell
$BIN = "$env:USERPROFILE\.local\bin"
"$BIN\nlm.exe", "$BIN\notebooklm-mcp.exe" | ForEach-Object { if (Test-Path $_) { "OK  $_" } else { "缺失 $_" } }
```

（可选）`uv tool update-shell` 可把该目录加进用户 PATH，但**后面注册 MCP 时一律用完整路径**，不依赖 PATH，更稳。

---

## 步骤 2：验证固定代理（关键前置）

先验证固定代理能否访问 Google；不要因直连失败而切掉代理。

```powershell
`$PROXY = "http://127.0.0.1:51081"`
curl.exe -s -o NUL -w "via proxy -> %{http_code}`n" -x $PROXY --max-time 15 https://www.google.com/generate_204
```

- 返回 `204`/`200`/`3xx` → **走步骤 3B（代理认证）**。
- 超时 / `000` / 连接失败 → 停止并诊断代理；不得静默改走无代理认证。

---

## 步骤 3A：直连认证（仅用户明确要求）

直接用内置流程，它会弹出浏览器让用户登录 Google：

```powershell
& "$env:USERPROFILE\.local\bin\nlm.exe" login
```

引导用户在弹出的浏览器窗口完成 Google 登录。登录后工具自动抽取 cookie。然后 **跳到步骤 4**。

> 若这一步卡在「Waiting for sign-in…」超时，多半其实是需要代理——转步骤 3B。

---

## 步骤 3B：代理认证（外部 CDP 法，不改系统代理）

### 3B-1　确定代理地址/端口

本机已验证固定代理为 `http://127.0.0.1:51081`，默认不得改写。仅用户明确给出新值时设置
`$PROXY`，并先验证其连通性：

```powershell
Write-Output "=== 代理环境变量 ==="
"HTTP_PROXY=$env:HTTP_PROXY  HTTPS_PROXY=$env:HTTPS_PROXY  ALL_PROXY=$env:ALL_PROXY"

Write-Output "=== Windows 系统代理 ==="
$r = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($r.ProxyEnable)  ProxyServer=$($r.ProxyServer)  PAC=$($r.AutoConfigURL)"

Write-Output "=== 常见本地代理端口是否在监听 ==="
foreach ($p in 7890,7897,7891,1080,1081,10808,10809,2080,8080,8888,20171,2334) {
  if (Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue) { "port $p : LISTENING" }
}

Write-Output "=== 疑似代理进程 ==="
Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.ProcessName -match 'clash|mihomo|verge|v2ray|xray|sing-?box|surge|nekoray|trojan|hysteria|shadow|ss-|winxray|qv2ray' } |
  Select-Object ProcessName, Id | Format-Table -AutoSize
```

判读：
- 固定代理 `http://127.0.0.1:51081` → 直接使用；环境变量不得覆盖它。
- 只看到监听端口：`1080` 多为 **SOCKS5**，`108x`/`789x`/`108xx` 多为 **HTTP**。Clash/Verge 常见 HTTP `7890`/`7897`，v2rayN 常见 `10809`(HTTP)/`10808`(SOCKS)。
- 只有用户明确要求更换代理时才询问新地址；默认固定值不可被环境变量静默覆盖。

得到明确代理后，**先验证它真能到 Google 再往下走**：

```powershell
$PROXY = "http://127.0.0.1:51081"
curl.exe -s -o NUL -w "via proxy -> %{http_code}`n" -x $PROXY --max-time 15 https://www.google.com/generate_204
```

期望 `204`。若失败，停止认证并报告代理不可达；不得静默回退直连。

### 3B-2　用代理 + 调试端口启动一个独立 Chrome

选一个调试端口，**避开 `9222`（chrome-devtools MCP 常用）和 `18800`（nlm 内置哨兵值，用了会退回非外部模式）**。默认用 `19222`，被占就换。

```powershell
python <iteration-loop>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py launch `
  --proxy http://127.0.0.1:51081 --cdp-port 19222
python <iteration-loop>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py status `
  --cdp-url http://127.0.0.1:19222
```

确认这个浏览器**通过代理真的打开了 Google**（而不是错误页）：

```powershell
Start-Sleep 3
(curl.exe -s --noproxy '*' --max-time 8 "http://127.0.0.1:$PORT/json" | ConvertFrom-Json) |
  Where-Object { $_.type -eq 'page' } | Select-Object title, url | Format-List
```

看到 `accounts.google.com`（Google 登录页）、`notebook.google.com` 或 `Gemini Notebook` 就对了。若是 Chrome 错误页 → 代理不通，回 3B-1。

### 3B-3　让用户登录，再抽 cookie

引导用户：**在这个新弹出的窗口里**完成 Google 登录（账号、密码、二次验证都由用户本人操作；Codex 不碰凭据），一直登到能看到 NotebookLM 首页/笔记本列表。

**等用户确认「登录好了」之后**再抽取（这样没有倒计时压力）：

```powershell
& "$env:APPDATA\uv\tools\notebooklm-mcp-cli\Scripts\python.exe" `
  "<iteration-loop>\skills\refresh-notebooklm-auth\scripts\save_external_cdp_auth.py" `
  --cdp-url "http://127.0.0.1:19222"
```

成功会打印 `✓ Successfully authenticated!` + 账号 + cookie 数。cookie 落盘在 `~\.notebooklm-mcp-cli\profiles\default`。

### 3B-4　关掉临时 Chrome

认证已落盘，临时浏览器不再需要，按端口精准关闭其整棵进程树（不影响日常 Chrome）：

```powershell
$c = Get-NetTCPConnection -State Listen -LocalPort $PORT -ErrorAction SilentlyContinue
if ($c) { taskkill /PID (($c | Select-Object -First 1).OwningProcess) /T /F }
```

---

## 步骤 4：注册到各宿主 MCP

用 **user（全局）作用域** + **完整路径** 注册。**若走了步骤 3B（需代理），务必把代理用 `-e` 固化进 MCP 配置**——因为 `HTTP_PROXY` 往往只是当前会话变量（User/Machine 级常为空），宿主重启后拉起 MCP 子进程时不一定继承得到，而这个 MCP **每次调 NotebookLM API 都要走代理**。

用户用到的宿主**都注册**（Codex / Claude Code / Grok），不要只装一个假定全家可用。

```powershell
$NLM = "$env:USERPROFILE\.local\bin\notebooklm-mcp.exe"
$PROXY = "http://127.0.0.1:51081"
$GROK = "$env:USERPROFILE\.grok\bin\grok.exe"
```

**Codex（需代理）：**
```powershell
codex mcp remove notebooklm-mcp -s user 2>$null
codex mcp add notebooklm-mcp -s user `
  -e HTTP_PROXY=$PROXY -e HTTPS_PROXY=$PROXY -e NO_PROXY=localhost,127.0.0.1 `
  -- "$NLM"
```

**Grok Build（需代理）：**
```powershell
& $GROK mcp remove notebooklm-mcp -s user 2>$null
& $GROK mcp add notebooklm-mcp -s user `
  -e "HTTP_PROXY=$PROXY" -e "HTTPS_PROXY=$PROXY" -e "NO_PROXY=localhost,127.0.0.1" `
  -- $NLM
# 验证：& $GROK mcp doctor notebooklm-mcp   期望 handshake OK + tools discovered
```

**Claude Code（需代理；PowerShell 下 `--` 易被吃，优先 cmd）：**
```powershell
cmd /c "claude mcp add notebooklm-mcp -s user -e HTTP_PROXY=$PROXY -e HTTPS_PROXY=$PROXY -e NO_PROXY=localhost,127.0.0.1 -- $NLM"
# 验证：claude mcp list  应见 notebooklm-mcp √ Connected
```

**直连（步骤 3A，无需代理）**：同上各命令，去掉全部 `-e HTTP_PROXY/...` 即可。

> 作用域：NotebookLM 是通用工具，用 `user` 作用域让所有项目可用，勿把含代理的 MCP 配置提交进仓库。

---

## 步骤 5：验证 & 冒烟测试

```powershell
Codex mcp list | Select-String notebooklm                                  # Codex 宿主：期望 ✔ Connected
& "$env:USERPROFILE\.local\bin\nlm.exe" login --check                       # 期望 ✓ Authentication valid + Notebooks found: N
& "$env:USERPROFILE\.local\bin\nlm.exe" notebook list | Select-Object -First 20   # 真实列出笔记本 = 端到端打通
```

⚠️ MCP 配置写入后，**当前会话里工具通常不会立刻出现**。提示用户 **重启宿主**（或该宿主的
`/mcp` 刷新）后再用。`nlm login --check` 与 `nlm notebook list` 不依赖会话内 MCP，可先验证 cookie。

---

## 重新认证（cookie 过期，约 2–4 周）

现象：`nlm login --check` 报失效，或 MCP 调用返回未认证。**直接重跑步骤 3B + 步骤 5 即可**，无需重装、无需重新注册 MCP。使用固定代理 Chrome → 登录 → `save_external_cdp_auth.py`，避免 `nlm login --cdp-url` 的 300 秒假等待。

---

## 故障排查

| 现象 | 处理 |
|---|---|
| `nlm login` 卡「Waiting for sign-in」超时 | 使用固定代理 `nlm_auth_flow.py launch` + 外部 CDP 提取 |
| `Cannot connect to CDP endpoint` | 临时 Chrome 没起来或端口不对；确认 `/json/version` 能返回 JSON，`--remote-allow-origins=*` 是否带上 |
| CDP 里 Chrome 停在错误页 | 代理不通 → 回 3B-1 重新确认 `http://127.0.0.1:51081` 并 `curl -x` 验证到 Google |
| `--remote-debugging-port` 不生效/端口无监听 | 没用独立 `--user-data-dir`，被并进已开的 Chrome；换个新目录重启 |
| 注册用了 `18800` 端口做 cdp-url | 那是内置哨兵值，会退回非外部模式；换 `19222` 等 |
| MCP 连上但调用报错/连不上 Google | 代理没进 MCP 配置 → 按步骤 4「需要代理」版本重注册（`-e HTTP_PROXY/HTTPS_PROXY`） |
| `notebooklm-mcp` 找不到命令 | 用完整路径 `~\.local\bin\notebooklm-mcp.exe`（该目录默认不在 PATH） |
| 诊断 | `nlm doctor` |

---

## 跨平台适配（macOS / Linux）

概念完全一致，只是命令不同：

- **安装**：`uv tool install notebooklm-mcp-cli` 相同；二进制在 `~/.local/bin/`（无 `.exe` 后缀）。
- **直连测试**：`curl -s -o /dev/null -w '%{http_code}\n' --noproxy '*' --max-time 10 https://www.google.com/generate_204`
- **查系统代理**：macOS `scutil --proxy`（或 `networksetup -getwebproxy "Wi-Fi"`）；Linux 看 `$HTTP_PROXY` / `env | grep -i proxy` / `gsettings get org.gnome.system.proxy mode`。
- **查监听端口**：`lsof -iTCP -sTCP:LISTEN -P -n | grep -E ':(7890|7897|1080|1081|10808|10809)'`
- **Chrome 路径**：macOS `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`；Linux `google-chrome` / `chromium`。
- **后台启动 Chrome**：在命令末尾加 `&`，参数（`--proxy-server` / `--remote-debugging-port` / `--remote-allow-origins=*` / `--user-data-dir` / 起始 URL）完全相同；隔离 profile 用 `"$TMPDIR/nlm-chrome-auth"` 或 `/tmp/nlm-chrome-auth`。
- **验证 CDP**：`curl -s --noproxy '*' http://127.0.0.1:$PORT/json/version`
- **按端口关临时 Chrome**：`lsof -ti tcp:$PORT | xargs kill`
- **注册 MCP**：`Codex mcp add notebooklm-mcp -s user -e HTTP_PROXY=$PROXY -e HTTPS_PROXY=$PROXY -e NO_PROXY=localhost,127.0.0.1 -- "$HOME/.local/bin/notebooklm-mcp"`
- **验证**：`~/.local/bin/nlm login --check` 与 `nlm notebook list` 相同。
