"""Install Goni Community and skills for both Codex and Claude Code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

FILES = [
    "SKILL.md", "agents/openai.yaml", "references/quickstart.md",
    "scripts/core.py", "scripts/server.py", "scripts/cli.py", "scripts/install.py",
    "scripts/test_app.py", "scripts/start.py", "INSTALL.cmd", "START.cmd",
    "assets/index.html", "assets/style.css", "assets/app.js",
]


def install(home):
    source = Path(__file__).resolve().parent.parent
    home = Path(home).expanduser().resolve()
    app = home / ".goni-community" / "app"
    destinations = [app, home / ".codex" / "skills" / "goni-community",
                    home / ".claude" / "skills" / "goni-community"]
    for relative in FILES:
        if not (source / relative).is_file():
            raise ValueError(f"Package file missing: {relative}")
    for destination in destinations:
        for relative in FILES:
            origin, target = source / relative, destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if origin.resolve() != target.resolve():
                shutil.copy2(origin, target)
    binary = home / ".goni-community" / "bin"
    binary.mkdir(parents=True, exist_ok=True)
    # Absolute quoted paths; no credentials or browser commands in launchers.
    if sys.platform == "win32":
        launcher = binary / "goni-community.cmd"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" -X utf8 "{app / "scripts" / "cli.py"}" %*\r\n',
                            encoding="utf-8")
    else:
        import shlex
        launcher = binary / "goni-community"
        launcher.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} -X utf8 '
                            f'{shlex.quote(str(app / "scripts" / "cli.py"))} "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    hashes = {f: hashlib.sha256((app / f).read_bytes()).hexdigest() for f in FILES}
    (home / ".goni-community" / "installed-files.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8")
    return {"app": str(app), "launcher": str(launcher), "start": str(app / "START.cmd"),
            "skills": [str(x) for x in destinations[1:]],
            "state": str(home / ".goni-community"),
            "path_modified": False, "external_posting": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()
    print(json.dumps(install(args.home), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
