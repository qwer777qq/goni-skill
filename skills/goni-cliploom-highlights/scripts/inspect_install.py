#!/usr/bin/env python3
"""Read-only Cliploom source/tool check; does not read .env or user data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def run(args, cwd=None):
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=20)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def safe_file(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Asset path is outside the app folder")
    return target


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(repo):
    app = repo / "shorts-saas"
    issues = []
    required = ["AGENTS.md", "README.md", "shorts-saas/package.json",
                "shorts-saas/src/server.mjs", "shorts-saas/src/media.mjs",
                "shorts-saas/scripts/media.py", "shorts-saas/requirements.txt",
                "shorts-saas/docs/API.md", "shorts-saas/public/editor-fonts.json",
                "shorts-saas/assets/render-fonts/manifest.json"]
    missing = [name for name in required if not (repo / name).is_file()]
    issues.extend("Missing: " + name for name in missing)
    count = 0
    if not missing:
        try:
            catalog = json.loads((app / "public/editor-fonts.json").read_text(encoding="utf-8"))
            manifest = json.loads((app / "assets/render-fonts/manifest.json").read_text(encoding="utf-8"))
            entries = {item["id"]: item for item in manifest["fonts"]}
            ids = [item["id"] for item in catalog["fonts"]]
            if len(set(ids)) != len(ids) or set(ids) != set(entries):
                issues.append("Catalog/manifest font IDs differ or contain duplicates")
            if catalog["defaultId"] not in ids:
                issues.append("Default font is absent")
            for item in catalog["fonts"]:
                entry = entries.get(item["id"])
                if not entry:
                    continue
                render = safe_file(app, item["renderFile"])
                web = safe_file(app / "public", item["file"].lstrip("/"))
                if item["renderFile"] != entry["renderFile"]:
                    issues.append("Render path mismatch: " + item["id"])
                elif not render.is_file() or sha256(render) != entry["renderSha256"]:
                    issues.append("Missing or altered render font: " + item["id"])
                elif not web.is_file() or sha256(web) != item["sourceSha256"]:
                    issues.append("Missing or altered web font: " + item["id"])
                else:
                    count += 1
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append("Font validation failed: " + type(exc).__name__)
    node = shutil.which("node")
    version = run([node, "--version"]) if node else None
    parsed = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", version or "")
    node_ok = bool(parsed and tuple(map(int, parsed.groups())) >= (24, 15, 0))
    if not node_ok:
        issues.append("Node >=24.15 is required")
    git = shutil.which("git")
    commit = run([git, "rev-parse", "HEAD"], cwd=repo) if git and repo.is_dir() else None
    configured_python = os.environ.get("PYTHON_EXECUTABLE")
    local_python = app / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    python = configured_python or (str(local_python) if local_python.is_file() else sys.executable)
    probe = "import importlib.metadata as m,json; names=['faster-whisper','av','Pillow','yt-dlp']; result={};\nfor n in names:\n try: result[n]=m.version(n)\n except m.PackageNotFoundError: result[n]=None\nprint(json.dumps(result))"
    packages = run([python, "-c", probe])
    try:
        packages = json.loads(packages) if packages else None
    except ValueError:
        packages = None
    return {
        "repo": str(repo), "commit": commit, "source_and_node_ok": not issues,
        "issues": issues, "verified_font_pairs": count,
        "node": {"path": node, "version": version, "compatible": node_ok},
        "tool_candidates": {
            "python": str(python).replace("\\", "/"),
            "ffmpeg": (os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg") or "").replace("\\", "/"),
            "yt_dlp": (os.environ.get("YTDLP_PATH") or shutil.which("yt-dlp") or "").replace("\\", "/"),
        },
        "python_packages": packages,
        "runtime_status": "NOT_VERIFIED: run app doctor/readiness and a real media job",
        "notes": ["No .env, database, credentials, or media were read.",
                  "Candidate tools/package versions are not proof of app configuration.",
                  "The script neither downloads models nor starts servers."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Repository root, not shorts-saas")
    args = parser.parse_args()
    report = inspect(args.repo.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["source_and_node_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
