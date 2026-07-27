#!/usr/bin/env python3
"""Read-only capability probe for notebooklm-iteration-loop target projects."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


NODE_TEST_DEPS = ("vitest", "jest", "mocha", "ava")
NODE_COVERAGE_DEPS = ("@vitest/coverage-v8", "@vitest/coverage-istanbul", "nyc", "c8")
NODE_E2E_DEPS = ("@playwright/test", "playwright", "cypress")
E2E_CONFIGS = (
    "playwright.config.ts",
    "playwright.config.js",
    "playwright.config.mjs",
    "cypress.config.ts",
    "cypress.config.js",
)
GLOBAL_QUALITY_COMMANDS = {
    "sonar": ("sonar-scanner", "dotnet-sonarscanner"),
    "coverage": ("coverage", "coverage3", "c8", "nyc", "dotnet-coverage"),
    "e2e": ("playwright", "cypress"),
}


def _which(command: str, search_path: str | None) -> bool:
    return shutil.which(command, path=search_path) is not None


def _available(
    commands: tuple[str, ...], search_path: str | None, project_root: Path
) -> list[str]:
    available = []
    for command in commands:
        executable = shutil.which(command, path=search_path)
        if executable is None:
            continue
        try:
            Path(executable).resolve().relative_to(project_root)
        except ValueError:
            available.append(command)
    return available


def _load_package_json(root: Path) -> dict[str, Any]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_invalid": True}
    return value if isinstance(value, dict) else {"_invalid": True}


def _node_package_manager(root: Path) -> str | None:
    for lockfile, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
        ("package-lock.json", "npm"),
    ):
        if (root / lockfile).is_file():
            return manager
    return None


def _node_capabilities(root: Path, package: dict[str, Any]) -> dict[str, Any]:
    dependencies: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            dependencies.update(value)
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}
    names = set(dependencies)
    test_scripts = sorted(
        name
        for name in scripts
        if name == "test" or name.startswith(("test:", "coverage", "e2e"))
    )
    return {
        "present": bool(package),
        "valid": not package.get("_invalid", False),
        "package_manager": _node_package_manager(root),
        "test_frameworks": sorted(set(NODE_TEST_DEPS) & names),
        "coverage_tools": sorted(set(NODE_COVERAGE_DEPS) & names),
        "e2e_frameworks": sorted(set(NODE_E2E_DEPS) & names),
        "verification_scripts": test_scripts,
    }


def detect(project_root: Path, search_path: str | None = None) -> dict[str, Any]:
    root = project_root.resolve()
    package = _load_package_json(root)
    node = _node_capabilities(root, package)

    python_markers = [
        name
        for name in ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg")
        if (root / name).is_file()
    ]
    python_tests = sorted(
        str(path.relative_to(root))
        for path in (root / "tests").glob("test_*.py")
        if path.is_file()
    ) if (root / "tests").is_dir() else []
    e2e_configs = [name for name in E2E_CONFIGS if (root / name).is_file()]
    sonar_configured = any(
        (root / name).is_file()
        for name in ("sonar-project.properties", "pom.xml", "build.gradle", "build.gradle.kts")
    )
    global_quality = {
        family: _available(commands, search_path, root)
        for family, commands in GLOBAL_QUALITY_COMMANDS.items()
    }
    native_verifiers = []
    if node["verification_scripts"]:
        native_verifiers.append("node")
    if python_markers or python_tests:
        native_verifiers.append("python")
    if (root / "Cargo.toml").is_file():
        native_verifiers.append("rust")
    if (root / "go.mod").is_file():
        native_verifiers.append("go")
    if (root / "pom.xml").is_file() or (root / "build.gradle").is_file() or (
        root / "build.gradle.kts"
    ).is_file():
        native_verifiers.append("jvm")

    blockers = []
    if not _which("codegraph", search_path):
        blockers.append("codegraph_cli_missing")
    if not (root / ".codegraph").is_dir():
        blockers.append("codegraph_index_missing")
    if not native_verifiers:
        blockers.append("project_verifier_not_detected")

    return {
        "schema_version": 1,
        "project_root": str(root),
        "required": {
            "codegraph_cli": _which("codegraph", search_path),
            "codegraph_index": (root / ".codegraph").is_dir(),
            "nlm_cli": _which("nlm", search_path),
            "native_verifiers": native_verifiers,
        },
        "quality": {
            "global_commands": global_quality,
            "sonar_scanner": bool(global_quality["sonar"]),
            "sonar_configured": sonar_configured,
            "coverage_detected": bool(node["coverage_tools"])
            or (root / ".coveragerc").is_file()
            or (root / "coverage.xml").is_file(),
            "e2e_configs": e2e_configs,
        },
        "project": {
            "node": node,
            "python_markers": python_markers,
            "python_tests": python_tests,
            "rust": (root / "Cargo.toml").is_file(),
            "go": (root / "go.mod").is_file(),
        },
        "blockers": blockers,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when a required capability cannot be detected.",
    )
    args = parser.parse_args(argv)

    result = detect(args.project_root, os.environ.get("PATH"))
    output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(output)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output + "\n", encoding="utf-8")
    return 2 if args.strict and result["blockers"] else 0


if __name__ == "__main__":
    sys.exit(main())
