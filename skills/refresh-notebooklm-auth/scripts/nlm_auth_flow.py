#!/usr/bin/env python3
"""Scripted, non-secret NotebookLM auth plumbing.

The helper keeps the known-good local proxy on both sides of the flow:
Python/CLI requests and Chrome's ``--proxy-server`` flag.  It never reads or
prints cookies, storage, passwords, or tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PROXY_URL = "http://127.0.0.1:51081"
DEFAULT_CDP_PORT = 19222
DEFAULT_PROFILE_NAME = "nlm-chrome-auth"
LOGIN_URL = "https://notebook.google.com/"


def resolve_proxy(value: str | None = None) -> str:
    """Resolve explicit proxy, process override, or the fixed local default."""

    return value or os.environ.get("NLM_PROXY_URL") or DEFAULT_PROXY_URL


def network_env(proxy: str) -> dict[str, str]:
    """Build a process-local environment; never mutate system proxy settings."""

    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        env[key] = proxy
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"
    return env


def chrome_args(proxy: str, profile: Path, cdp_port: int) -> list[str]:
    return [
        f"--proxy-server={proxy}",
        f"--remote-debugging-port={cdp_port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile}",
        LOGIN_URL,
    ]


def chrome_executable() -> str:
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("chrome") or shutil.which("chrome.exe")
    if found:
        return found
    raise FileNotFoundError("Google Chrome executable not found")


def launch(proxy: str, profile: Path, cdp_port: int) -> dict[str, Any]:
    profile.mkdir(parents=True, exist_ok=True)
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
    process = subprocess.Popen(
        [chrome_executable(), *chrome_args(proxy, profile, cdp_port)],
        env=network_env(proxy),
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {
        "started": True,
        "pid": process.pid,
        "proxy": proxy,
        "profile": str(profile),
        "cdp_url": f"http://127.0.0.1:{cdp_port}",
        "url": LOGIN_URL,
    }


def local_json(url: str, timeout: float = 5.0) -> Any:
    # CDP is local; bypass HTTP(S)_PROXY even when the user proxy is required
    # for Google.  This request contains no credentials.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=timeout) as response:
        return json.load(response)


def status(cdp_url: str) -> dict[str, Any]:
    base = cdp_url.rstrip("/")
    version = local_json(f"{base}/json/version")
    tabs = local_json(f"{base}/json/list")
    pages = [
        {"title": tab.get("title", ""), "url": tab.get("url", ""), "type": tab.get("type", "")}
        for tab in tabs
        if tab.get("type") == "page"
    ]
    return {"cdp": True, "browser": version.get("Browser", ""), "pages": pages}


def run_nlm(arguments: list[str], proxy: str, timeout: int) -> tuple[int, str]:
    command = shutil.which("nlm") or shutil.which("nlm.exe")
    if not command:
        raise FileNotFoundError("nlm executable not found")
    result = subprocess.run(
        [command, *arguments],
        env=network_env(proxy),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    # nlm's check/list output is non-secret; do not add arbitrary browser output.
    return result.returncode, (result.stdout + result.stderr).strip()


def verify(proxy: str, timeout: int) -> dict[str, Any]:
    check_code, _ = run_nlm(["login", "--check"], proxy, timeout)
    result: dict[str, Any] = {"proxy": proxy, "login_check_exit": check_code}
    if check_code == 0:
        list_code, list_output = run_nlm(["notebook", "list"], proxy, timeout)
        result["notebook_list_exit"] = list_code
        if list_code == 0:
            try:
                notebooks = json.loads(list_output)
            except json.JSONDecodeError:
                notebooks = None
            result["notebook_count"] = len(notebooks) if isinstance(notebooks, list) else None
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Keep NotebookLM CLI and Chrome proxy wiring consistent.")
    sub = p.add_subparsers(dest="command", required=True)

    launch_p = sub.add_parser("launch", help="launch dedicated Chrome for interactive sign-in")
    launch_p.add_argument("--proxy", default=None)
    launch_p.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    launch_p.add_argument("--profile", type=Path, default=None)

    status_p = sub.add_parser("status", help="show non-secret CDP page metadata")
    status_p.add_argument("--cdp-url", default=f"http://127.0.0.1:{DEFAULT_CDP_PORT}")

    verify_p = sub.add_parser("verify", help="run nlm login check and notebook list")
    verify_p.add_argument("--proxy", default=None)
    verify_p.add_argument("--timeout", type=int, default=30)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "launch":
            proxy = resolve_proxy(args.proxy)
            profile = args.profile or Path(os.environ.get("TEMP", ".")) / DEFAULT_PROFILE_NAME
            result = launch(proxy, profile, args.cdp_port)
        elif args.command == "status":
            result = status(args.cdp_url)
        else:
            result = verify(resolve_proxy(args.proxy), args.timeout)
    except (FileNotFoundError, OSError, urllib.error.URLError, TimeoutError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True))
        return 1
    # ASCII JSON avoids PowerShell 5.1's GBK stdout codec corrupting CLI output.
    print(json.dumps(result, ensure_ascii=True))
    if args.command == "verify":
        return int(result.get("login_check_exit", 1) != 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
