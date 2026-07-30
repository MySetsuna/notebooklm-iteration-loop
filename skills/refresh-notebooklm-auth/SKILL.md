---
name: refresh-notebooklm-auth
description: Refresh or repair local NotebookLM (`nlm`) authentication with a fixed local proxy and external Chrome CDP, especially when Google requires `http://127.0.0.1:51081`, browser login has succeeded but `nlm login --cdp-url` waits or times out, or NotebookLM resolves to `notebook.google.com`. Use for requests such as "刷新 NLM 登录", "NLM 已登录但 CLI 仍失效", "重取 NotebookLM Cookie", or "NotebookLM MCP cookie 过期".
---

# Refresh NotebookLM authentication

Use an isolated, externally managed Chrome profile; never print, paste, log, or upload Cookie values.

The default proxy is `http://127.0.0.1:51081`. Override only with an explicit
`--proxy` or `NLM_PROXY_URL`; pass the resolved value to both CLI environment
variables and Chrome `--proxy-server`. Do not change the system proxy.

## 1. Preflight

1. Run `nlm login --check` with `HTTP_PROXY`, `HTTPS_PROXY`, and
   `NO_PROXY=127.0.0.1,localhost`. Stop if valid unless the user explicitly requests a refresh.
2. Confirm local CDP health without secrets:

```powershell
Invoke-RestMethod 'http://127.0.0.1:19222/json/version' | Select-Object Browser
```

3. If direct Google access fails, use the fixed proxy or the user's explicit override.
   Do not change the system proxy or silently fall back to an unproxied login.

## 2. Launch and sign in

Use the bundled `nlm_auth_flow.py launch` helper so the proxy and CDP flags stay
consistent. It uses a dedicated Chrome data directory and reports only PID,
profile path, proxy, CDP URL, and page metadata. If visible-browser launch is
blocked by the execution environment, give the generated command to the user;
do not mislabel that as a Google or Ridge failure.

```powershell
python <this skill>/scripts/nlm_auth_flow.py launch \
  --proxy http://127.0.0.1:51081 --cdp-port 19222
```

Ask the user to finish Google sign-in in that Chrome window. Confirm only the URL/title via `/json/list`; do not inspect or report cookie content.

## 3. Extract and save without the false wait

`notebooklm-mcp-cli` 0.8.9 treats only `notebooklm.google.com` as logged in, while the live site may resolve to `notebook.google.com`. Therefore `nlm login --cdp-url ...` can wait 300 seconds after a successful sign-in. Use the bundled extractor; it uses NLM's own CDP and `AuthManager.save_profile` APIs with `wait_for_login=False`.

```powershell
$py="$env:APPDATA\uv\tools\notebooklm-mcp-cli\Scripts\python.exe"
$script='<this skill directory>\scripts\save_external_cdp_auth.py'
& $py $script --cdp-url 'http://127.0.0.1:19222'
```

Default behavior refuses to overwrite a different saved Google account. Use `--force` only after the user confirms account replacement.

## 4. Verify and diagnose

Set only process-local proxy variables using the helper, then run:

```powershell
python <this skill>/scripts/nlm_auth_flow.py verify \
  --proxy http://127.0.0.1:51081
```

Report only success/failure, notebook count, and non-sensitive diagnostics. If check fails after successful extraction, retain the profile and diagnose proxy/network separately; do not expose credentials or repeat login blindly.

## Boundaries

- Cookie files are credentials: never read them into chat, source control, NotebookLM sources, logs, or command output.
- Keep `--user-data-dir` dedicated; never scrape the user's normal Chrome profile.
- Do not use the direct extractor until the user has completed interactive sign-in.
- Confirm only CDP browser/title/URL metadata; never inspect cookies or storage.
- Re-test this workaround after upgrading `notebooklm-mcp-cli`; remove it when its logged-in host recognition includes `notebook.google.com`.
