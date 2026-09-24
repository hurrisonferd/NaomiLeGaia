"""Stage-1 HEATDEATH baseline: isolated real SQLite parity and independent import."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import legacy_memory_reader as legacy


def isolated(script: str, db: str) -> dict:
    env = dict(os.environ)
    env.pop("TURSO_DATABASE_URL", None)
    env.pop("TURSO_AUTH_TOKEN", None)
    env["MEMCONOS_DB_PATH"] = db
    env["PYTHONPATH"] = str(ROOT / "api")
    child = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=35,
    )
    if child.returncode:
        raise AssertionError(
            f"isolated child failed ({child.returncode}):\n{child.stdout}\n{child.stderr}"
        )
    return json.loads(child.stdout)


class LegacyMemoryBaseline(unittest.TestCase):
    def test_reader_has_no_galaxy_import_and_forwards_native_contract(self):
        calls = []
        class Storage:
            def search_records(self, query, limit, scope):
                calls.append((query, limit, scope))
                return {"records": [], "count": 0, "query_filter_active": bool(query)}
        out = legacy.read(Storage(), "legacy memory", "MemoryOS", 4)
        self.assertEqual(out, {"records": [], "count": 0, "query_filter_active": True})
        self.assertEqual(calls, [("legacy memory", 4, "MemoryOS")])
        self.assertEqual(
            legacy.BASELINE_SOURCE_COMMIT,
            "7e4851c2fef77d78bccf51d493d1c100cc99c52d",
        )
        code = (ROOT / "api" / "legacy_memory_reader.py").read_text(encoding="utf-8")
        self.assertNotIn("import galaxy_", code)

    def test_import_survives_galaxy_package_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            response = isolated(
                """
                import builtins, json
                original = builtins.__import__
                def without_galaxy(name, *args, **kwargs):
                    if name.startswith("galaxy"):
                        raise ImportError("GALAXY module deliberately unavailable")
                    return original(name, *args, **kwargs)
                builtins.__import__ = without_galaxy
                import legacy_memory_reader as legacy
                class Fake:
                    def search_records(self, q, n, s):
                        return {"records":[{"record_id":"LEGACY"}],"count":1}
                print(json.dumps(legacy.read(Fake(), "safe", "MemoryOS", 1)))
                """, str(Path(directory) / "isolated.sqlite"),
            )
            self.assertEqual(response["records"][0]["record_id"], "LEGACY")

    def test_real_legacy_sqlite_queries_approval_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "baseline.sqlite")
            result = isolated(
                """
                import json
                import memcon_runtime as rt
                import legacy_memory_reader as legacy
                rt.initialize()
                def write(rid, scope, statement, notes="", status="ACTIVE"):
                    rt.write_record(
                        authority="NAOMI", approved=True, record_type="BASELINE_TEST",
                        record_id=rid, scope=scope, statement=statement,
                        source="isolated-ci-fixture", notes=notes, status=status,
                    )
                try:
                    rt.write_record(
                        authority="NAOMI", approved=False, record_type="TEST",
                        scope="MemoryOS", statement="disallowed", source="test",
                    )
                    raise AssertionError("unapproved write was permitted")
                except PermissionError:
                    pass
                write("L-01","MemoryOS","legacy memory continuity")
                write("L-02","MemoryOS","legacy archival","memory evidence")
                write("L-03","VERA_E_LANE","legacy memory continuity")
                write("L-04","MemoryOS","planetary atmosphere")
                write("L-05","MemoryOS","legacy historical memory",status="HISTORICAL")
                before = rt._db()
                with before as conn:
                    counts_before = tuple(conn.execute(
                        "SELECT count(*) FROM " + name).fetchone()[0]
                        for name in ("memory_records","memory_relations","memory_gravity",
                                     "memory_importance","runtime_receipts"))
                found = legacy.read_deployed("LEGACY memory","MemoryOS",10)
                empty_scope = legacy.read_deployed("","MemoryOS",20)
                broad = legacy.read_deployed("",None,20)
                no_match = legacy.read_deployed("doesnotmatch","MemoryOS",10)
                notes = legacy.read_deployed("archival evidence","MemoryOS",10)
                with rt._db() as conn:
                    counts_after = tuple(conn.execute(
                        "SELECT count(*) FROM " + name).fetchone()[0]
                        for name in ("memory_records","memory_relations","memory_gravity",
                                     "memory_importance","runtime_receipts"))
                print(json.dumps({
                    "found_ids":sorted(r["record_id"] for r in found["records"]),
                    "count":found["count"],
                    "scope":found["scope_applied"],
                    "terms":found["query_terms_applied"],
                    "query_filter_active":found["query_filter_active"],
                    "empty_scope_count":empty_scope["count"],
                    "broad_count":broad["count"],
                    "not_found_count":no_match["count"],
                    "notes_ids":[r["record_id"] for r in notes["records"]],
                    "counts_unchanged":counts_before==counts_after,
                    "native_envelope":all(key in found for key in (
                        "records","count","runtime","query_terms_applied",
                        "scope_applied","query_filter_active")),
                }))
                """, db,
            )
            self.assertEqual(result["found_ids"], ["L-01", "L-02", "L-05"])
            self.assertEqual(result["count"], 3)
            self.assertEqual(result["scope"], "MemoryOS")
            self.assertEqual(result["terms"], ["legacy", "memory"])
            self.assertTrue(result["query_filter_active"])
            self.assertEqual(result["empty_scope_count"], 4)
            self.assertEqual(result["broad_count"], 5)
            self.assertEqual(result["not_found_count"], 0)
            self.assertEqual(result["notes_ids"], ["L-02"])
            self.assertTrue(result["counts_unchanged"])
            self.assertTrue(result["native_envelope"])
            # The next process is a genuine fresh import over the same local DB.
            after_restart = isolated(
                """
                import json
                import legacy_memory_reader as legacy
                rows = legacy.read_deployed("legacy memory","MemoryOS",10)
                print(json.dumps({
                    "ids":sorted(row["record_id"] for row in rows["records"]),
                    "count":rows["count"],
                }))
                """, db,
            )
            self.assertEqual(after_restart["ids"], ["L-01", "L-02", "L-05"])
            self.assertEqual(after_restart["count"], 3)

    def test_untouched_owner_and_six_elane_authorities(self):
        host = (ROOT / "api" / "host_memory_gateway.py").read_text(encoding="utf-8")
        self.assertIn("def _host_memsav(", host)
        self.assertIn("payload.approved", host)
        self.assertIn("candidate_ids", host)
        for name in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
            path = ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS" / "IDENTITY-DATA" / f"{name}-EXPERIENCES.v1.md"
            self.assertTrue(path.is_file(), f"missing independent {name} E-LANE")
        loader = (ROOT / "GaiaOS" / "LOAD.v1.md").read_text(encoding="utf-8")
        self.assertIn("GAIAOS-INTEGRATION-FIRST-DESIGN-GATE", loader)


if __name__ == "__main__":
    unittest.main(verbosity=2)
