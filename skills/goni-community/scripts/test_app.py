import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from core import InputError, Store, canonical
from server import create_server
from start import is_workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state")
        self.store.profile({"name": "film", "naver_id": "my_blog", "category": "영화"})

    def tearDown(self):
        self.temp.cleanup()

    def add(self, profile="film", url="https://m.blog.naver.com/writer/123", actions="comment"):
        return self.store.add({"profile": profile, "url": url, "actions": actions,
                               "title": "제목", "excerpt": "본문에 파란 조명이 등장한다."})["jobs"][0]

    def test_url_canonicalization_and_rejection(self):
        expected = "https://blog.naver.com/writer/123"
        self.assertEqual(canonical("https://m.blog.naver.com/Writer/123?from=feed"), expected)
        self.assertEqual(canonical("https://blog.naver.com/PostView.naver?blogId=writer&logNo=123"), expected)
        for value in ["https://blog.naver.com.evil.test/writer/123", "https://x@y.blog.naver.com/writer/123",
                      "https://blog.naver.com:443/writer/123", "https://m.naver.com/",
                      "https://blog.naver.com/writer/%2f123"]:
            with self.assertRaises(InputError):
                canonical(value)

    def test_account_scoped_dedupe_across_aliases(self):
        first = self.add()
        self.store.profile({"name": "other-alias", "naver_id": "my_blog", "category": "영화"})
        second = self.add(profile="other-alias")
        self.assertEqual(first["id"], second["id"])
        self.store.profile({"name": "second-account", "naver_id": "another_blog", "category": "여행"})
        self.assertNotEqual(first["id"], self.add(profile="second-account")["id"])
        self.assertEqual(len(self.store.workspace("second-account")["jobs"]), 1)

    def test_profile_remap_does_not_change_identity(self):
        self.add()
        with self.assertRaises(InputError):
            self.store.profile({"name": "film", "naver_id": "another_blog", "category": "영화"})

    def test_complete_requires_review_and_evidence(self):
        job = self.add()
        with self.assertRaises(InputError):
            self.store.record(job["id"], "done", "내가 확인")
        self.store.draft(job["id"], "파란 조명으로 분위기를 표현한 부분이 흥미롭네요.")
        self.store.review(job["id"])
        with self.assertRaises(InputError):
            self.store.record(job["id"], "done", "")
        result = self.store.record(job["id"], "done", "사용자가 등록 문구와 표시를 직접 확인")
        self.assertFalse(result["externally_verified"])
        self.assertEqual(self.store.batch("film")["selected_posts"], 0)

    def test_source_and_draft_changes_invalidate_review(self):
        job = self.add()
        self.store.draft(job["id"], "초안")
        self.store.review(job["id"])
        self.store.draft(job["id"], "수정 초안")
        self.assertEqual(self.store.workspace()["jobs"][0]["status"], "draft")
        self.store.review(job["id"])
        self.store.source(job["id"], "새 제목", "새 본문")
        self.assertEqual(self.store.workspace()["jobs"][0]["status"], "draft")

    def test_uncertain_excluded_until_explicit_reopen(self):
        job = self.add()
        self.store.record(job["id"], "uncertain", "등록 여부 불명확")
        self.assertEqual(self.store.batch("film")["jobs"], [])
        with self.assertRaises(InputError):
            self.store.draft(job["id"], "재전송 초안")
        with self.assertRaises(InputError):
            self.store.reopen(job["id"], "")
        self.store.reopen(job["id"], "사용자가 이전 결과를 확인하고 다시 준비 요청")
        self.assertEqual(self.store.batch("film")["selected_posts"], 1)

    def test_batch_counts_posts_not_actions(self):
        for i in range(7):
            self.add(url=f"https://blog.naver.com/writer/{100+i}", actions="like,comment")
        batch = self.store.batch("film", 5)
        self.assertEqual(batch["selected_posts"], 5)
        self.assertEqual(len(batch["jobs"]), 10)

    def test_csv_invalid_row_rolls_back_whole_import(self):
        csv_path = self.root / "input.csv"
        csv_path.write_text("url,title,excerpt\nhttps://blog.naver.com/writer/1,첫 글,내용\ninvalid,둘째,내용",
                            encoding="utf-8")
        with self.assertRaises(InputError):
            self.store.import_csv("film", csv_path)
        self.assertEqual(self.store.workspace()["jobs"], [])

    def test_draft_needs_source(self):
        job = self.store.add({"profile": "film", "url": "https://blog.naver.com/writer/123",
                              "actions": "comment"})["jobs"][0]
        with self.assertRaises(InputError):
            self.store.draft(job["id"], "내용 없는 초안")

    def test_legacy_import_idempotent(self):
        path = self.root / "legacy.sqlite3"
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""CREATE TABLE profiles(name,account,profile_id,naver_id,category);
              CREATE TABLE jobs(id,name,naver_id,url,action,note,status,evidence);
              INSERT INTO profiles VALUES('legacy','u0','sample-profile','legacy_blog','영화');
              INSERT INTO jobs VALUES(1,'legacy','legacy_blog','https://m.blog.naver.com/writer/123',
                'like','내용','done','이전 확인 기록');""")
            db.commit()
        self.assertEqual(self.store.import_legacy(path)["added_jobs"], 1)
        self.assertEqual(self.store.import_legacy(path)["added_jobs"], 0)
        job = self.store.workspace("legacy")["jobs"][0]
        self.assertEqual(job["evidence_type"], "legacy_record")
        self.assertEqual(job["status"], "done")

    def test_backup_is_readable_and_does_not_overwrite(self):
        self.add()
        out = self.root / "backup.sqlite3"
        self.store.backup(out)
        with closing(sqlite3.connect(out)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
        with self.assertRaises(InputError):
            self.store.backup(out)

    def test_local_http_rejects_cross_origin_and_serves_only_allowlisted_assets(self):
        server = create_server(self.store, 0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            def call(method, path, body=None, headers=None):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request(method, path, body=body, headers=headers or {})
                response = connection.getresponse()
                result = response.status, response.read()
                connection.close()
                return result
            self.assertTrue(is_workspace(server.server_port))
            status, health = call("GET", "/api/health")
            self.assertEqual(status, 200)
            self.assertEqual(set(json.loads(health)), {"app", "version", "mode"})
            status, body = call("GET", "/api/workspace")
            self.assertEqual(status, 200)
            csrf = json.loads(body)["csrf"]
            data = json.dumps({"profile": "film", "url": "https://blog.naver.com/writer/111"})
            headers = {"Content-Type": "application/json", "X-Goni-Csrf": csrf,
                       "Origin": "https://unrelated.example"}
            self.assertEqual(call("POST", "/api/add", data, headers)[0], 403)
            headers["Origin"] = f"http://127.0.0.1:{server.server_port}"
            self.assertEqual(call("POST", "/api/add", data, headers)[0], 200)
            self.assertEqual(call("GET", "/../../workspace.sqlite3")[0], 404)
            self.assertEqual(call("GET", "/api/workspace", headers={"Host": "other.example"})[0], 403)
            self.assertEqual(call("GET", "/")[0], 200)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def test_launcher_does_not_accept_unrelated_local_server(self):
        class OtherApp(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"app":"another-app"}')

        server = ThreadingHTTPServer(("127.0.0.1", 0), OtherApp)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            self.assertFalse(is_workspace(server.server_port))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
