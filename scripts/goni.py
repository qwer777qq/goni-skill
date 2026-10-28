"""Repeatable Goni repository, tool, graph, and memory operations."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ACCOUNT = "qwer777qq"
REPOSITORY = "qwer777qq/goni-skill"
KST = timezone(timedelta(hours=9), "KST")
SECRET = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|"
    r"sk-[A-Za-z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY|"
    r"(?:password|api[_ -]?key|token)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def command(args: list[str], project: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=project, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout, check=False,
    )


def plugin_info() -> dict[str, str] | None:
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    candidates = (home / "plugins/cache/scv-codex/scv").glob("*/.codex-plugin/plugin.json")
    found = []
    for manifest in candidates:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            found.append({"version": data["version"], "path": str(manifest.parents[1])})
        except (OSError, ValueError, KeyError):
            continue
    return max(found, key=lambda item: tuple(int(n) for n in re.findall(r"\d+", item["version"]))) if found else None


def scv_plugin_enabled(project: Path) -> bool | None:
    codex = shutil.which("codex")
    if not codex:
        return None
    result = command([codex, "plugin", "list"], project, timeout=45)
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.strip().startswith("scv@scv-codex"):
            return "installed, enabled" in line
    return False


def graphify_install_paths(project: Path) -> list[dict[str, str | int]]:
    primary = shutil.which("graphify")
    paths = [primary] if primary else []
    if os.name == "nt":
        located = command(["where.exe", "graphify"], project)
        if located.returncode == 0:
            paths.extend(located.stdout.splitlines())
    unique = list(dict.fromkeys(str(Path(item).resolve()) for item in paths if item))
    details: list[dict[str, str | int]] = []
    for path in unique:
        result = command([path, "--version"], project, timeout=20)
        match = re.search(r"graphify\s+([\d.]+)", result.stdout)
        details.append({
            "path": path,
            "version": match.group(1) if match else "unknown",
            "exit_code": result.returncode,
        })
    return details


def local_remote(project: Path) -> str | None:
    if not shutil.which("git"):
        return None
    result = command(["git", "remote", "get-url", "origin"], project)
    return result.stdout.strip() if result.returncode == 0 else None


def doctor(project: Path) -> int:
    try:
        version = importlib.metadata.version("graphifyy")
    except importlib.metadata.PackageNotFoundError:
        version = None
    plugin = plugin_info()
    plugin_enabled = scv_plugin_enabled(project)
    graphify_installs = graphify_install_paths(project)
    checks = {
        "project": str(project),
        "scv_plugin": plugin,
        "scv_plugin_enabled": plugin_enabled,
        "scv_project_ready": (project / "scv/SCV.md").is_file(),
        "graphify_package": version,
        "graphify_cli": shutil.which("graphify"),
        "graphify_installs": graphify_installs,
        "git_cli": shutil.which("git"),
        "github_cli": shutil.which("gh"),
        "origin": local_remote(project),
    }
    checks["tools_ready"] = bool(plugin and plugin_enabled and version and graphify_installs and checks["git_cli"] and checks["github_cli"])
    checks["ready"] = bool(checks["tools_ready"] and checks["scv_project_ready"])
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if checks["ready"] else 1


def repo(project: Path, live: bool) -> int:
    result: dict[str, object] = {"account": ACCOUNT, "expected_skill_repo": REPOSITORY, "origin": local_remote(project)}
    if live:
        gh = shutil.which("gh")
        if not gh:
            raise RuntimeError("GitHub CLI is not installed")
        response = command([gh, "repo", "view", REPOSITORY, "--json", "nameWithOwner,url,visibility,defaultBranchRef"], project)
        if response.returncode:
            raise RuntimeError(response.stderr.strip() or "GitHub repository lookup failed")
        result["github"] = json.loads(response.stdout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def resume(project: Path) -> int:
    for name in ("AGENTS.md", "memory/development-workflow.md", "memory/workflow-state.json"):
        path = project / name
        print(f"\n### {name}\n{path.read_text(encoding='utf-8-sig') if path.is_file() else '(not recorded)'}")
    return 0


def checkpoint(project: Path, summary: str, next_action: str) -> int:
    if SECRET.search(summary + "\n" + next_action):
        raise RuntimeError("Possible secret in checkpoint; remove it before recording")
    entry = {"updated_at": datetime.now(KST).isoformat(), "summary": summary, "next_action": next_action}
    memory = project / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    state = memory / "workflow-state.json"
    temporary = state.with_suffix(".tmp")
    temporary.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(state)
    with (memory / "workflow-log.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def graph_path(project: Path, scope: str) -> Path:
    return project / ".workspace-tools/graphs" / scope / "graphify-out/graph.json"


def graph(project: Path, scope: str) -> int:
    executable = shutil.which("graphify")
    if not executable:
        raise RuntimeError("Graphify CLI is not installed")
    target = (project / scope).resolve()
    if not target.is_dir() or not target.is_relative_to(project):
        raise RuntimeError(f"Code scope missing or outside project: {scope}")
    out = graph_path(project, scope).parent.parent
    out.mkdir(parents=True, exist_ok=True)
    result = command([executable, "extract", str(target), "--code-only", "--no-cluster", "--max-workers", "2", "--out", str(out)], project, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Graphify extraction failed")
    path = graph_path(project, scope)
    if not path.is_file():
        raise RuntimeError("Graphify completed without graph.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({"graph": str(path), "nodes": len(data.get("nodes", [])), "edges": len(data.get("links", data.get("edges", [])))}, ensure_ascii=False))
    return 0


def query(project: Path, scope: str, question: str) -> int:
    path = graph_path(project, scope)
    if not path.is_file():
        raise RuntimeError("Build the code graph first")
    executable = shutil.which("graphify")
    if not executable:
        raise RuntimeError("Graphify CLI is not installed")
    result = command([executable, "query", question, "--graph", str(path), "--budget", "1800"], project, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Graphify query failed")
    print(result.stdout.rstrip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("doctor")
    sub.add_parser("resume")
    sub.add_parser("repo").add_argument("--live", action="store_true")
    save = sub.add_parser("checkpoint")
    save.add_argument("--summary", required=True)
    save.add_argument("--next", dest="next_action", required=True)
    for name in ("graph", "query"):
        option = sub.add_parser(name)
        option.add_argument("--scope", choices=("scripts",), default="scripts")
        if name == "query":
            option.add_argument("question")
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error(f"Project directory does not exist: {project}")
    try:
        if args.action == "doctor":
            return doctor(project)
        if args.action == "repo":
            return repo(project, args.live)
        if args.action == "resume":
            return resume(project)
        if args.action == "checkpoint":
            return checkpoint(project, args.summary, args.next_action)
        if args.action == "graph":
            return graph(project, args.scope)
        return query(project, args.scope, args.question)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
