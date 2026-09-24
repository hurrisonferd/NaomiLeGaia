"""Stage-2 persistent HEATDEATH precedence and zero-GALAXY dependencies."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import gaiaos_memory_mode as mode


class SQLiteStore:
    def __init__(self, path: str):
        self.path = path
    def _db(self):
        return sqlite3.connect(self.path, timeout=5)


class DownStore:
    def _db(self):
        raise RuntimeError("remote control database offline")


class ModeControlTests(unittest.TestCase):
    def test_missing_table_does_not_migrate_on_read_and_fails_heatdeath(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "shared.sqlite")
            state = mode.mode_status(SQLiteStore(db), environ={})
            self.assertEqual(state["effective_mode"], "HEATDEATH")
            self.assertEqual(state["reason"], "NO_PERSISTED_CONTROL")
            with sqlite3.connect(db) as conn:
                count = conn.execute(
                    "SELECT count(*) FROM sqlite_master WHERE name=?",
                    (mode.TABLE,),
                ).fetchone()[0]
            self.assertEqual(count, 0)

    def test_owner_approval_required_and_unauthorized_call_does_not_create_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "no-writes.sqlite"))
            for authority, approved in (
                ("NAOMI", False), ("OTHER", True), ("OTHER", False),
            ):
                result = mode.engage_heatdeath(
                    store, authority=authority, approved=approved,
                    reason="emergency",
                )
                self.assertEqual(result["status"], "HOLD")
                self.assertEqual(result["writes_performed"], [])
            with store._db() as conn:
                count = conn.execute(
                    "SELECT count(*) FROM sqlite_master WHERE name=?",
                    (mode.TABLE,),
                ).fetchone()[0]
            self.assertEqual(count, 0)

    def test_persists_and_versions_heatdeath_without_touching_memory_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "persistent.sqlite")
            store = SQLiteStore(path)
            before = mode.mode_status(store, environ={})
            self.assertEqual(before["effective_mode"], "HEATDEATH")
            one = mode.engage_heatdeath(
                store, authority="NAOMI", approved=True,
                reason="owner approved emergency",
            )
            self.assertEqual(one["status"], "PASS_HEATDEATH_CONTROL_PERSISTED")
            self.assertEqual(one["control_version"], 1)
            self.assertTrue(one["readback_verified"])
            other_instance = SQLiteStore(path)
            readback = mode.mode_status(other_instance, environ={})
            self.assertEqual(readback["configured_mode"], "HEATDEATH")
            self.assertEqual(readback["control_version"], 1)
            two = mode.engage_heatdeath(
                other_instance, authority="NAOMI", approved=True,
                reason="reaffirm emergency",
            )
            self.assertEqual(two["control_version"], 2)
            with sqlite3.connect(path) as conn:
                tables = [row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()]
            self.assertEqual(tables, [mode.TABLE])

            # Fresh process, same durable SQLite file: no process-local flag.
            child = textwrap.dedent("""
                import json, sqlite3, sys
                import gaiaos_memory_mode as mode
                class Runtime:
                    def _db(self):
                        return sqlite3.connect(sys.argv[1])
                print(json.dumps(mode.mode_status(Runtime(), environ={})))
            """)
            proc = subprocess.run(
                [sys.executable, "-c", child, path], cwd=ROOT, text=True,
                capture_output=True, timeout=20,
                env={**os.environ, "PYTHONPATH": str(ROOT / "api")},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            restarted = json.loads(proc.stdout)
            self.assertEqual(restarted["effective_mode"], "HEATDEATH")
            self.assertEqual(restarted["control_version"], 2)

    def test_environment_override_is_emergency_first_and_storage_independent(self):
        for key in mode.OVERRIDES:
            out = mode.mode_status(DownStore(), environ={key: "1"})
            self.assertEqual(out["reason"], "EMERGENCY_ENV_OVERRIDE")
            self.assertEqual(out["override"], key)
            self.assertEqual(out["effective_mode"], "HEATDEATH")
        invalid = mode.mode_status(DownStore(), environ={
            "GAIAOS_FORCE_HEATDEATH": "surprise"
        })
        self.assertEqual(invalid["reason"], "INVALID_EMERGENCY_OVERRIDE")
        self.assertEqual(invalid["effective_mode"], "HEATDEATH")

    def test_shared_control_outage_fails_closed_without_claiming_a_read(self):
        out = mode.mode_status(DownStore(), environ={})
        self.assertEqual(out["effective_mode"], "HEATDEATH")
        self.assertEqual(out["reason"], "HOLD_SHARED_CONTROL_UNAVAILABLE")
        self.assertEqual(out["error_type"], "RuntimeError")
        self.assertEqual(out["writes_performed"], [])

    def test_bigbang_row_cannot_reactivate_before_release_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "manual-row.sqlite"))
            approved = mode.engage_heatdeath(
                store, authority="NAOMI", approved=True, reason="test",
            )
            self.assertEqual(approved["status"], "PASS_HEATDEATH_CONTROL_PERSISTED")
            # Simulate a future BIGBANG row: this stage must fail closed.
            with store._db() as conn:
                conn.execute(
                    "UPDATE gaiaos_memory_mode_control "
                    "SET selected_mode='BIGBANG' WHERE control_id=1"
                )
            decision = mode.mode_status(store, environ={})
            self.assertEqual(decision["configured_mode"], "BIGBANG")
            self.assertEqual(decision["effective_mode"], "HEATDEATH")
            self.assertEqual(decision["reason"], "BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED")

    def test_galaxy_import_failure_does_not_affect_mode_control(self):
        child = textwrap.dedent("""
            import builtins, json
            imp = builtins.__import__
            def blocked(name, *args, **kwargs):
                if name.startswith('galaxy'):
                    raise ImportError('simulated GALAXY startup failure')
                return imp(name, *args, **kwargs)
            builtins.__import__ = blocked
            import gaiaos_memory_mode as mode
            class FailedDB:
                def _db(self):
                    raise RuntimeError('down')
            print(json.dumps(mode.mode_status(FailedDB(), environ={})))
        """)
        proc = subprocess.run(
            [sys.executable, "-c", child], cwd=ROOT, text=True,
            capture_output=True, timeout=20,
            env={**os.environ, "PYTHONPATH": str(ROOT / "api")},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            json.loads(proc.stdout)["effective_mode"], "HEATDEATH",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
