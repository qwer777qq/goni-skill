"""Goni Community CLI: profiles, source notes, drafts and manual result records."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

from core import DEFAULT_STATE, InputError, Store, VERSION


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", type=Path, default=DEFAULT_STATE, help="Local data directory")
    p.add_argument("--version", action="version", version=VERSION)
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    a = commands.add_parser("profile")
    for key in ("name", "naver-id", "category"):
        a.add_argument("--" + key, required=True)
    a.add_argument("--aside-account", default="")
    a.add_argument("--aside-profile", default="")
    a = commands.add_parser("list")
    a.add_argument("--profile")
    a.add_argument("--status")
    a = commands.add_parser("add")
    a.add_argument("--profile", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--title", default="")
    a.add_argument("--excerpt", default="")
    a.add_argument("--excerpt-file", type=Path)
    a.add_argument("--actions", default="like,comment")
    a = commands.add_parser("import-csv")
    a.add_argument("--profile", required=True)
    a.add_argument("--file", required=True, type=Path)
    a.add_argument("--actions", default="like,comment")
    for command in ("batch", "prompt"):
        a = commands.add_parser(command)
        a.add_argument("--profile", required=True)
        a.add_argument("--count", type=int, default=5)
    a = commands.add_parser("source")
    a.add_argument("--id", type=int, required=True)
    a.add_argument("--title", default="")
    a.add_argument("--file", required=True, type=Path)
    a = commands.add_parser("draft")
    a.add_argument("--id", type=int, required=True)
    group = a.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--file", type=Path)
    for command in ("review", "events"):
        a = commands.add_parser(command)
        a.add_argument("--id", type=int, required=True)
    a = commands.add_parser("record")
    a.add_argument("--id", type=int, required=True)
    a.add_argument("--status", choices=["done", "skipped", "uncertain"], required=True)
    a.add_argument("--evidence", required=True)
    a = commands.add_parser("reopen")
    a.add_argument("--id", type=int, required=True)
    a.add_argument("--reason", required=True)
    a = commands.add_parser("import-legacy")
    a.add_argument("--file", required=True, type=Path)
    a = commands.add_parser("backup")
    a.add_argument("--output", required=True, type=Path)
    a = commands.add_parser("export")
    a.add_argument("--profile")
    a.add_argument("--output", required=True, type=Path)
    a = commands.add_parser("serve")
    a.add_argument("--port", type=int, default=8877)
    commands.add_parser("demo")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        store = Store(args.state)
        c = args.command
        if c == "status":
            result = dict(store.workspace(), state=str(store.path),
                          browser_connected=False, external_posting=False)
        elif c == "profile":
            result = store.profile(vars(args))
        elif c == "list":
            result = store.workspace(args.profile, args.status)
        elif c == "add":
            data = vars(args).copy()
            if args.excerpt_file:
                data["excerpt"] = args.excerpt_file.read_text(encoding="utf-8-sig")
            result = store.add(data)
        elif c == "import-csv":
            result = store.import_csv(args.profile, args.file, args.actions)
        elif c == "batch":
            result = store.batch(args.profile, args.count)
        elif c == "prompt":
            print(store.prompt(args.profile, args.count))
            return 0
        elif c == "source":
            result = store.source(args.id, args.title, args.file.read_text(encoding="utf-8-sig"))
        elif c == "draft":
            text = args.file.read_text(encoding="utf-8-sig") if args.file else args.text
            result = store.draft(args.id, text)
        elif c == "review":
            result = store.review(args.id)
        elif c == "record":
            result = store.record(args.id, args.status, args.evidence)
        elif c == "reopen":
            result = store.reopen(args.id, args.reason)
        elif c == "events":
            result = store.events(args.id)
        elif c == "import-legacy":
            result = store.import_legacy(args.file)
        elif c == "backup":
            result = store.backup(args.output)
        elif c == "export":
            if args.output.exists():
                raise InputError("내보낼 파일이 이미 있습니다. 새 파일명을 사용해 주세요.")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(store.workspace(args.profile), ensure_ascii=False, indent=2),
                                   encoding="utf-8")
            result = {"exported": str(args.output)}
        elif c == "serve":
            from server import serve
            serve(store, args.port)
            return 0
        elif c == "demo":
            if store.workspace()["profiles"]:
                raise InputError("데모는 비어 있는 별도 --state 폴더에서 실행해 주세요.")
            store.profile({"name": "샘플 · 영화", "naver_id": "goni_demo", "category": "영화·드라마"})
            result = store.add({"profile": "샘플 · 영화",
                                "url": "https://blog.naver.com/goni_sample/100000000001",
                                "title": "샘플: 영화 속 색채와 인물의 변화",
                                "excerpt": "연습용으로 만든 본문입니다. 차가운 파란 조명에서 따뜻한 주황 조명으로 바뀌며 주인공의 심리 변화가 드러난다는 내용입니다.",
                                "actions": ["like", "comment"]})
            comment = next(j for j in result["jobs"] if j["action"] == "comment")
            store.draft(comment["id"], "조명의 색 변화로 인물의 심리를 짚어주신 부분이 흥미롭네요. 파란색과 주황색의 대비를 생각하며 장면을 다시 살펴보고 싶어집니다.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (InputError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
