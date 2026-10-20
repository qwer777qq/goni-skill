"""Inspect a ZIP containing a PyInstaller/Python app and browser extension.

Reads bytes only: never imports, executes, or connects to the inspected app.
Detailed outputs are local research material, not automatically publishable.
Use the Python minor version matching the embedded PYZ bytecode.
"""
from __future__ import annotations

import argparse
import dis
import hashlib
import importlib.util
import io
import json
import marshal
from pathlib import Path
import re
import struct
import sys
import types
import zipfile
import zlib

LIMIT = 128 * 1024 * 1024
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact(text: str) -> str:
    text = re.sub(r"\beyJ[\w-]{15,}\.[\w-]+\.[\w-]+\b", "[REDACTED_JWT]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED_KEY]", text)
    text = re.sub(r"(https?://[^\s?\"'<>]+)\?[^\s\"'<>]+", r"\1?[REDACTED_QUERY]", text)
    return text


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(json.dumps(value, ensure_ascii=False, indent=2)) + "\n", encoding="utf-8")


def inflate(data: bytes, limit: int = LIMIT) -> bytes:
    decoder = zlib.decompressobj()
    result = decoder.decompress(data, limit + 1)
    if len(result) > limit or decoder.unconsumed_tail or not decoder.eof:
        raise ValueError("compressed data exceeds limit or is incomplete")
    return result


def read_carchive(exe: bytes) -> tuple[dict, list[dict], dict[str, bytes]]:
    pos = exe.rfind(COOKIE)
    if pos < 0 or pos + 88 > len(exe):
        raise ValueError("supported PyInstaller cookie not found")
    _, size, toc_pos, toc_len, pyver, pylib = struct.unpack("!8sIIII64s", exe[pos:pos + 88])
    start = pos + 88 - size
    toc_start = start + toc_pos
    toc_end = toc_start + toc_len
    if start < 0 or toc_start < start or toc_end > pos:
        raise ValueError("CArchive bounds invalid")
    rows, selected, cursor = [], {}, toc_start
    while cursor < toc_end:
        if cursor + 18 > toc_end:
            raise ValueError("CArchive TOC truncated")
        length, offset, packed, unpacked, compressed, kind = struct.unpack(
            "!IIIIBc", exe[cursor:cursor + 18])
        if length < 18 or cursor + length > toc_end:
            raise ValueError("CArchive entry invalid")
        name = exe[cursor + 18:cursor + length].split(b"\0", 1)[0].decode("utf-8", "replace")
        if start + offset < start or start + offset + packed > toc_start or unpacked > LIMIT:
            raise ValueError(f"CArchive member outside bounds: {name}")
        row = {"name": name, "type": kind.decode("ascii", "replace"),
               "packed_bytes": packed, "bytes": unpacked, "compressed": bool(compressed)}
        rows.append(row)
        if name == "PYZ.pyz" or (kind == b"s" and not name.startswith("pyi")):
            data = exe[start + offset:start + offset + packed]
            data = inflate(data) if compressed else data
            if len(data) != unpacked:
                raise ValueError(f"CArchive size mismatch: {name}")
            selected[name] = data
            row["sha256"] = sha(data)
        cursor += length
    return {"python_version": pyver, "python_library": pylib.split(b"\0", 1)[0].decode()}, rows, selected


def read_pyz(data: bytes) -> tuple[list[dict], dict[str, types.CodeType]]:
    if data[:4] != b"PYZ\0":
        raise ValueError("not a PYZ archive")
    if data[4:8] != importlib.util.MAGIC_NUMBER:
        raise ValueError(
            f"Python bytecode mismatch: embedded={data[4:8].hex()}, "
            f"local={importlib.util.MAGIC_NUMBER.hex()}; select matching Python")
    toc_pos = struct.unpack("!I", data[8:12])[0]
    if toc_pos < 12 or toc_pos >= len(data):
        raise ValueError("PYZ TOC outside bounds")
    toc = dict(marshal.loads(data[toc_pos:]))
    rows, modules = [], {}
    for name, (kind, pos, length) in toc.items():
        if pos < 12 or pos + length > toc_pos:
            raise ValueError(f"PYZ member outside bounds: {name}")
        rows.append({"module": name, "kind": kind, "packed_bytes": length})
        if name == "src" or name.startswith("src."):
            obj = marshal.loads(inflate(data[pos:pos + length]))
            if not isinstance(obj, types.CodeType):
                raise ValueError(f"not a Python code object: {name}")
            modules[name] = obj
    return rows, modules


def walk_code(code: types.CodeType):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from walk_code(value)


def strings(value, depth=0):
    if depth > 30:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, (tuple, list, frozenset)):
        for item in value:
            yield from strings(item, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(key, depth + 1)
            yield from strings(item, depth + 1)


def describe_module(name: str, code: types.CodeType, out: Path) -> dict:
    rows, constants, imports = [], [], set()
    all_text = []
    for item in walk_code(code):
        instructions = list(dis.get_instructions(item))
        for ins in instructions:
            if ins.opname == "IMPORT_NAME" and isinstance(ins.argval, str):
                imports.add(ins.argval)
        rows.append({
            "qualname": item.co_qualname, "first_line": item.co_firstlineno,
            "positional_args": list(item.co_varnames[:item.co_argcount]),
            "keyword_only_args": list(item.co_varnames[
                item.co_argcount:item.co_argcount + item.co_kwonlyargcount]),
            "flags": item.co_flags, "names": list(item.co_names),
            "instruction_count": len(instructions),
        })
        for index, value in enumerate(item.co_consts):
            for text in strings(value):
                constants.append({"scope": item.co_qualname, "index": index, "text": text})
                all_text.append(text)
    buffer = io.StringIO()
    # dis recursively formats code objects; it does not evaluate their instructions.
    dis.dis(code, file=buffer, show_caches=False)
    (out / f"{name}.dis.txt").write_text(redact(buffer.getvalue()), encoding="utf-8")
    write_json(out / f"{name}.code.json", rows)
    write_json(out / f"{name}.constants.json", constants)
    sql = [t for t in all_text if re.search(
        r"\b(?:CREATE\s+(?:TABLE|INDEX)|ALTER\s+TABLE|SELECT\s+.+\s+FROM|INSERT\s+INTO)\b", t, re.I | re.S)]
    write_json(out / f"{name}.sql.json", sql)
    table_names = sorted({m.group(1) for t in all_text for m in re.finditer(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?(\w+)", t, re.I)})
    return {"module": name, "source_file": code.co_filename,
            "code_objects": len(rows), "imports": sorted(imports),
            "string_constants": len(constants), "sql_constants": len(sql),
            "tables": table_names,
            "symbols": [r["qualname"] for r in rows if r["qualname"] != "<module>"]}


def web_summary(name: str, data: bytes) -> dict:
    text = data.decode("utf-8-sig")
    patterns = {
        "functions": r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(",
        "bridge_paths": r"""[\"'](/api/[A-Za-z_/-]+)[\"']""",
        "message_types": r"""(?:case\s+|type\s*:\s*)[\"']([A-Z][A-Z_]+)[\"']""",
        "css_selectors": r"([^{}]+)\{",
    }
    row = {"path": name, "bytes": len(data), "sha256": sha(data)}
    for key, pattern in patterns.items():
        if key == "css_selectors" and not name.endswith(".css"):
            continue
        row[key] = [{"value": m.group(1).strip(),
                     "line": text.count("\n", 0, m.start()) + 1}
                    for m in re.finditer(pattern, text)]
    row["discovery"] = "regex hints; not an exhaustive JavaScript parser or call graph"
    return row


def inspect(zip_path: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("output directory already exists; choose a new directory")
    if zip_path.stat().st_size > LIMIT:
        raise ValueError("input exceeds 128 MiB")
    raw = zip_path.read_bytes()
    output.mkdir(parents=True)
    desktop = output / "desktop"
    desktop.mkdir()
    inventory, web, module_rows, errors = [], [], [], []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) > 10000 or sum(m.file_size for m in members) > 4 * LIMIT:
            raise ValueError("ZIP inventory exceeds analysis bounds")
        for member in members:
            if member.is_dir():
                continue
            if member.file_size > LIMIT:
                raise ValueError("ZIP member exceeds 128 MiB")
            # Member names are used as labels only, never as destination paths.
            data = archive.read(member)
            name = member.filename
            inventory.append({"path": name, "bytes": len(data), "sha256": sha(data)})
            if "/extension/" in name and name.endswith((".js", ".css", ".html", ".json")):
                web.append(web_summary(name, data))
                if name.endswith("/manifest.json"):
                    manifest = json.loads(data)
                    write_json(output / "extension-manifest.json", manifest)
            if name.lower().endswith(".exe"):
                try:
                    metadata, carchive, selected = read_carchive(data)
                    write_json(output / "carchive.json", {"metadata": metadata, "entries": carchive})
                    pyz_rows, modules = read_pyz(selected["PYZ.pyz"])
                    write_json(output / "pyz-inventory.json", pyz_rows)
                    for script_name, script in selected.items():
                        if script_name != "PYZ.pyz":
                            obj = marshal.loads(script)
                            if isinstance(obj, types.CodeType):
                                modules[script_name] = obj
                    for mod_name, code in sorted(modules.items()):
                        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", mod_name):
                            raise ValueError("unsafe module name")
                        module_rows.append(describe_module(mod_name, code, desktop))
                except (ValueError, KeyError, TypeError, EOFError, struct.error) as exc:
                    errors.append({"path": name, "error": str(exc)})
    write_json(output / "archive.json", inventory)
    write_json(output / "web-inventory.json", web)
    write_json(output / "modules.json", module_rows)
    summary = {
        "input_sha256": sha(raw), "input_bytes": len(raw), "regular_files": len(inventory),
        "web_files": len(web), "python": sys.version.split()[0],
        "application_modules": len(module_rows),
        "code_objects": sum(m["code_objects"] for m in module_rows),
        "tables": sorted({t for m in module_rows for t in m["tables"]}),
        "errors": errors, "complete_for_selected_modules": not errors and bool(module_rows),
        "limitations": [
            "No inspected application code executed; no network or browser calls.",
            "Bytecode disassembly is not original Python source recovery.",
            "Application modules selected: src.* and non-PyInstaller launcher scripts.",
            "Third-party PYZ modules inventoried, not individually disassembled.",
            "JS regex inventory is a discovery aid; use a static parser for coverage.",
            "Redaction is best effort; review detailed outputs before sharing.",
            "Server source, live behavior, licensing and performance not verified.",
        ],
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = inspect(args.zip, args.output)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"Analysis stopped: {exc}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["complete_for_selected_modules"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
