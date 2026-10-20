"""Loopback-only UI for Goni local records. No proxy or external requests."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, urlsplit

from core import InputError

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def create_server(store, port=0):
    csrf = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def allowed_host(self):
            return self.headers.get("Host") in {
                f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def send(self, status, data, content_type="application/json; charset=utf-8"):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; script-src 'self'; style-src 'self'; "
                             "img-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
                             "base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.allowed_host():
                return self.send(403, {"error": "허용되지 않은 호스트입니다."})
            url = urlsplit(self.path)
            q = parse_qs(url.query)
            try:
                assets = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/style.css": ("style.css", "text/css; charset=utf-8")}
                if url.path in assets:
                    file, mime = assets[url.path]
                    return self.send(200, (ASSETS / file).read_bytes(), mime)
                if url.path == "/api/workspace":
                    return self.send(200, dict(store.workspace(q.get("profile", [None])[0]), csrf=csrf))
                if url.path == "/api/prompt":
                    return self.send(200, {"prompt": store.prompt(q.get("profile", [""])[0],
                                                                  int(q.get("count", ["5"])[0]))})
                if url.path == "/api/events":
                    return self.send(200, store.events(int(q.get("id", ["0"])[0])))
                return self.send(404, {"error": "없는 경로입니다."})
            except (InputError, ValueError) as exc:
                return self.send(400, {"error": str(exc)})
            except Exception:
                return self.send(500, {"error": "로컬 자료를 읽지 못했습니다."})

        def do_POST(self):
            if not self.allowed_host():
                return self.send(403, {"error": "허용되지 않은 호스트입니다."})
            origins = {f"http://127.0.0.1:{self.server.server_port}",
                       f"http://localhost:{self.server.server_port}"}
            if (self.headers.get("Origin") not in origins or
                    not hmac.compare_digest(self.headers.get("X-Goni-Csrf", ""), csrf)):
                return self.send(403, {"error": "앱 화면을 새로고침한 뒤 다시 저장해 주세요."})
            if self.headers.get_content_type() != "application/json":
                return self.send(415, {"error": "JSON 요청만 지원합니다."})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 1 or size > 131072:
                    return self.send(413, {"error": "요청 크기를 확인해 주세요."})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise InputError("입력은 JSON 객체여야 합니다.")
                route = urlsplit(self.path).path
                if route == "/api/profile":
                    result = store.profile(data)
                elif route == "/api/add":
                    result = store.add(data)
                elif route == "/api/source":
                    result = store.source(int(data["id"]), data.get("title"), data.get("excerpt"))
                elif route == "/api/draft":
                    result = store.draft(int(data["id"]), data.get("text"))
                elif route == "/api/review":
                    result = store.review(int(data["id"]))
                elif route == "/api/record":
                    result = store.record(int(data["id"]), data.get("status"), data.get("evidence"))
                elif route == "/api/reopen":
                    result = store.reopen(int(data["id"]), data.get("reason"))
                elif route == "/api/shutdown":
                    self.send(200, {"stopped": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                else:
                    return self.send(404, {"error": "없는 명령입니다."})
                return self.send(200, result)
            except (InputError, ValueError, KeyError, TypeError) as exc:
                return self.send(400, {"error": str(exc)})
            except Exception:
                return self.send(500, {"error": "저장하지 못했습니다. 입력과 로컬 상태를 확인해 주세요."})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(store, port):
    server = create_server(store, port)
    print(f"Goni Community: http://127.0.0.1:{server.server_port}", flush=True)
    print("Local drafts and user-reported records. No external posting.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
