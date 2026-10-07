"""Read-only canary for the OCA/MemoryOS host reader."""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import sqlite3
import tempfile
from pathlib import Path

CHATOS = Path(__file__).resolve().parents[1]
REPO = CHATOS.parents[2]
API = REPO / "api"
MEMCON = API / "memcon_runtime.py"
GATEWAY = API / "host_memory_gateway.py"
ADAPTERS = CHATOS / "Protocols" / "GAIAOS-OCA-ADAPTERS.v1.json"

for path in (MEMCON, GATEWAY, ADAPTERS):
    assert path.is_file(), path

mem_source = MEMCON.read_text(encoding="utf-8")
gateway_source = GATEWAY.read_text(encoding="utf-8")
adapters = json.loads(ADAPTERS.read_text(encoding="utf-8"))

mem_tree = ast.parse(mem_source)
gateway_tree = ast.parse(gateway_source)


def fn_source(tree: ast.AST, source: str, name: str) -> str:
    node = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )
    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


read_fn = fn_source(mem_tree, mem_source, "read_record_read_only")
read_node = next(
    n for n in ast.walk(mem_tree)
    if isinstance(n, ast.FunctionDef) and n.name == "read_record_read_only"
)
read_calls = {
    n.func.id
    for n in ast.walk(read_node)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
}
assert "initialize" not in read_calls
assert "_db_read_only" in read_calls
for token in ("INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE", "write_record(", "promote_candidate("):
    assert token not in read_fn, token

host_fn = fn_source(gateway_tree, gateway_source, "_host_memory_read")
assert "read_record_read_only(" in host_fn
for token in ("_host_candipull(", "_host_memsav(", "write_record(", "promote_candidate("):
    assert token not in host_fn, token

assert "def gaia_host_memory_read(" in gateway_source
assert '@app.get("/host/memory/read"' in gateway_source
assert '"durable_write": "NOT_PERFORMED"' in gateway_source
assert '"elane_write": "NOT_PERFORMED"' in gateway_source

adapter = adapters["adapters"]["MEMORYOS_CONTINUITY"]
assert adapter["host_read_surface"]["preferred_tool_when_connected"] == "gaia_host_memory_read"
assert adapter["host_read_surface"]["schema_initialization_allowed"] is False
assert adapter["host_read_surface"]["mutation_allowed"] is False
assert "HOST_GATEWAY_EXACT_RECORD_READ" in adapter["accepted_read_operations"]

# Dynamic local proof: the reader can SELECT an existing record without touching
# the database mtime, and refuses to create a missing database.
with tempfile.TemporaryDirectory() as td:
    db = Path(td) / "memory.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """CREATE TABLE memory_records (
            record_id TEXT PRIMARY KEY,
            authority TEXT NOT NULL,
            record_type TEXT NOT NULL,
            scope TEXT NOT NULL,
            statement TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            supersedes TEXT,
            notes TEXT NOT NULL DEFAULT ''
        )"""
    )
    conn.execute(
        "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "MEM-CANARY", "NAOMI", "TEST", "GaiaOS:Canary", "read-only",
            "canary", "ACTIVE", "1", "2026-10-06T00:00:00Z",
            "2026-10-06T00:00:00Z", None, "",
        ),
    )
    conn.commit()
    conn.close()
    before = db.stat().st_mtime_ns

    old_db = os.environ.get("MEMCONOS_DB_PATH")
    old_url = os.environ.get("TURSO_DATABASE_URL")
    old_token = os.environ.get("TURSO_AUTH_TOKEN")
    os.environ["MEMCONOS_DB_PATH"] = str(db)
    os.environ.pop("TURSO_DATABASE_URL", None)
    os.environ.pop("TURSO_AUTH_TOKEN", None)
    try:
        spec = importlib.util.spec_from_file_location("memcon_read_canary", MEMCON)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = module.read_record_read_only("MEM-CANARY")
        assert row and row["statement"] == "read-only"
        assert db.stat().st_mtime_ns == before

        missing = Path(td) / "does-not-exist.db"
        module.DB_PATH = missing
        assert module.read_record_read_only("MEM-MISSING") is None
        assert not missing.exists()
    finally:
        if old_db is None:
            os.environ.pop("MEMCONOS_DB_PATH", None)
        else:
            os.environ["MEMCONOS_DB_PATH"] = old_db
        if old_url is None:
            os.environ.pop("TURSO_DATABASE_URL", None)
        else:
            os.environ["TURSO_DATABASE_URL"] = old_url
        if old_token is None:
            os.environ.pop("TURSO_AUTH_TOKEN", None)
        else:
            os.environ["TURSO_AUTH_TOKEN"] = old_token

print("OCA_MEMORYOS_HOST_READER_CANARY PASS")
