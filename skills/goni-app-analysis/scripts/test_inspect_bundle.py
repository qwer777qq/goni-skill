"""Synthetic archive tests; no third-party application or live website required."""
import importlib.util
import marshal
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

from inspect_bundle import COOKIE, inflate, inspect, read_carchive, read_pyz


def pyz_bytes(code):
    payload = zlib.compress(marshal.dumps(code))
    toc = marshal.dumps([("src.sample", (0, 12, len(payload)))])
    return b"PYZ\0" + importlib.util.MAGIC_NUMBER + struct.pack("!I", 12 + len(payload)) + payload + toc


def exe_bytes(pyz):
    name = b"PYZ.pyz\0"
    entry = struct.pack("!IIIIBc", 18 + len(name), 0, len(pyz), len(pyz), 0, b"z") + name
    cookie = struct.pack("!8sIIII64s", COOKIE, len(pyz) + len(entry) + 88,
                         len(pyz), len(entry), 313, b"python313.dll")
    return b"MZ synthetic fixture" + pyz + entry + cookie


class AnalysisTests(unittest.TestCase):
    def test_end_to_end_does_not_execute_payload_or_extract_member_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "SHOULD_NOT_EXIST.txt"
            code = compile(f"open({str(marker)!r}, 'w').write('executed')\ndef f(x):\n return x + 1\n",
                           "src/sample.py", "exec")
            bundle = root / "sample.zip"
            with zipfile.ZipFile(bundle, "w") as z:
                z.writestr("app.exe", exe_bytes(pyz_bytes(code)))
                z.writestr("../outside.txt", "must stay inside archive")
            result = inspect(bundle, root / "analysis")
            self.assertTrue(result["complete_for_selected_modules"])
            self.assertEqual(result["application_modules"], 1)
            self.assertEqual(result["code_objects"], 2)
            self.assertFalse(marker.exists())
            self.assertFalse((root / "outside.txt").exists())
            with self.assertRaisesRegex(ValueError, "already exists"):
                inspect(bundle, root / "analysis")

    def test_python_version_mismatch_stops(self):
        data = bytearray(pyz_bytes(compile("pass", "src/x.py", "exec")))
        data[4:8] = b"\0\0\0\0"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            read_pyz(bytes(data))

    def test_truncated_cookie_stops(self):
        with self.assertRaises(ValueError):
            read_carchive(b"MZ" + COOKIE)

    def test_bad_archive_bounds_stop(self):
        data = bytearray(exe_bytes(pyz_bytes(compile("pass", "src/x.py", "exec"))))
        struct.pack_into("!I", data, len(data) - 88 + 12, 0xFFFFFFF0)
        with self.assertRaisesRegex(ValueError, "bounds"):
            read_carchive(bytes(data))

    def test_decompression_limit_and_truncation(self):
        compressed = zlib.compress(b"x" * 1024)
        with self.assertRaises(ValueError):
            inflate(compressed, limit=16)
        with self.assertRaises(ValueError):
            inflate(compressed[:-2])


if __name__ == "__main__":
    unittest.main()
