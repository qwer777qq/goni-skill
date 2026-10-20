"""Local profile mapping and deduplicated queue. Never stores credentials."""
import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode


def canonical(url):
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or p.username or p.password or p.port:
        raise ValueError("Use an HTTPS Naver URL without credentials or port")
    if host not in {"m.naver.com", "blog.naver.com", "m.blog.naver.com", "clip.naver.com", "m.clip.naver.com"}:
        raise ValueError("Unsupported Naver content host")
    q = parse_qs(p.query)
    if host in {"blog.naver.com", "m.blog.naver.com"}:
        if q.get("blogId") and q.get("logNo"):
            return f"https://blog.naver.com/{q['blogId'][0]}/{q['logNo'][0]}"
        host = "blog.naver.com"
    q = {k: v for k, v in q.items() if not k.lower().startswith("utm_") and k not in {"trackingCode", "from"}}
    return f"https://{host}{p.path.rstrip('/') or '/'}" + ("?" + urlencode(sorted(q.items()), doseq=True) if q else "")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", type=Path, default=Path.home() / ".goni-naver-community")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("profile")
    for key in ("name", "account", "profile-id", "naver-id", "category"):
        a.add_argument("--" + key, required=True)
    sub.add_parser("profiles")
    a = sub.add_parser("add")
    for key in ("name", "url"):
        a.add_argument("--" + key, required=True)
    a.add_argument("--action", choices=["like", "comment", "neighbor"], required=True)
    a.add_argument("--note", default="")
    a = sub.add_parser("next")
    a.add_argument("--name", required=True)
    a = sub.add_parser("record")
    a.add_argument("--id", type=int, required=True)
    a.add_argument("--status", choices=["done", "skipped", "uncertain"], required=True)
    a.add_argument("--evidence", required=True)
    a = sub.add_parser("repl-command")
    a.add_argument("--name", required=True)
    a.add_argument("--aside", required=True)
    args = p.parse_args()
    args.state.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.state / "state.sqlite3") as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS profiles(
          name TEXT PRIMARY KEY, account TEXT, profile_id TEXT, naver_id TEXT, category TEXT);
        CREATE TABLE IF NOT EXISTS jobs(
          id INTEGER PRIMARY KEY, name TEXT REFERENCES profiles(name), naver_id TEXT,
          url TEXT, action TEXT, note TEXT, status TEXT DEFAULT 'pending', evidence TEXT DEFAULT '',
          UNIQUE(naver_id,url,action));
        """)
        if args.cmd == "profile":
            old = db.execute("SELECT * FROM profiles WHERE name=?", (args.name,)).fetchone()
            values = (args.name, args.account, args.profile_id, args.naver_id, args.category)
            if old and tuple(old) != values:
                raise ValueError("Existing mapping differs; use a new alias to preserve history")
            db.execute("INSERT OR IGNORE INTO profiles VALUES(?,?,?,?,?)", values)
            result = {"saved": args.name, "site_login_verified": False}
        elif args.cmd == "profiles":
            result = [dict(r) for r in db.execute("SELECT * FROM profiles")]
        elif args.cmd == "record":
            if not args.evidence.strip():
                raise ValueError("Evidence is required")
            cur = db.execute("UPDATE jobs SET status=?,evidence=? WHERE id=?", (args.status, args.evidence, args.id))
            if cur.rowcount != 1:
                raise ValueError("Unknown job")
            result = {"id": args.id, "status": args.status}
        else:
            profile = db.execute("SELECT * FROM profiles WHERE name=?", (args.name,)).fetchone()
            if not profile:
                raise ValueError("Map the profile first")
            if args.cmd == "repl-command":
                result = {"executable": args.aside, "args": ["--account", profile["account"], "--profile", profile["profile_id"], "repl"]}
            elif args.cmd == "next":
                row = db.execute("SELECT * FROM jobs WHERE name=? AND status='pending' ORDER BY id LIMIT 1", (args.name,)).fetchone()
                result = dict(row) if row else None
            else:
                url = canonical(args.url)
                cur = db.execute("INSERT OR IGNORE INTO jobs(name,naver_id,url,action,note) VALUES(?,?,?,?,?)",
                                 (args.name, profile["naver_id"], url, args.action, args.note))
                row = db.execute("SELECT * FROM jobs WHERE naver_id=? AND url=? AND action=?",
                                 (profile["naver_id"], url, args.action)).fetchone()
                result = {"added": cur.rowcount == 1, "job": dict(row)}
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
