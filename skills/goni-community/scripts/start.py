"""Open or start the local Goni workspace. Never connects to an external site."""
import argparse
import http.client
import json
import threading
import webbrowser

from core import DEFAULT_STATE, Store
from server import create_server


def is_workspace(port):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        body = response.read(4096)
        return response.status == 200 and json.loads(body).get("app") == "goni-community"
    except (OSError, ValueError, AttributeError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535.")
    url = f"http://127.0.0.1:{args.port}/"
    if is_workspace(args.port):
        print(f"Existing workspace: {url}", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        return 0
    try:
        server = create_server(Store(DEFAULT_STATE), args.port)
    except OSError:
        print(f"Port {args.port} is in use. Use --port 8878 or close the other application.")
        return 1
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    print(f"Goni Community: {url}", flush=True)
    print("Local drafts and records only. Stop with Ctrl+C or the app shutdown button.", flush=True)
    try:
        if not args.no_browser:
            webbrowser.open(url)
        while worker.is_alive():
            worker.join(timeout=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
