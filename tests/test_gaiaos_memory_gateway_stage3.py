"""Stage 3 gateway contract: legacy first, BIGBANG gated, explicit failure fallback."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode


class FakeRuntime:
    _INITIALIZED = True

    def __init__(self):
        self.calls = []
        self.records = [{
            "record_id": "LEGACY-1",
            "scope": "MemoryOS",
            "statement": "gravity memory calibration",
            "status": "ACTIVE",
            "source": "verified-existing-memory",
        }]

    def search_records(self, query, limit, scope):
        self.calls.append((query, limit, scope))
        candidates = [row for row in self.records
                      if scope is None or row["scope"] == scope]
        words = [w.lower() for w in query.split()]
        candidates = [row for row in candidates
                      if all(word in row["statement"] or word in row["scope"].lower()
                             for word in words)]
        candidates = candidates[:max(1, min(int(limit), 100))]
        return {
            "records": [dict(row) for row in candidates],
            "count": len(candidates),
            "runtime": "fake.legacy.v1",
            "query_terms_applied": words,
            "scope_applied": scope,
            "query_filter_active": bool(words),
        }

    def _db(self):
        raise RuntimeError("control table inaccessible in this fake")


def bigbang_control():
    return {
        "schema": mode.SCHEMA,
        "effective_mode": mode.BIGBANG,
        "configured_mode": mode.BIGBANG,
        "bigbang_activation_enabled": True,
        "reason": "TEST_ONLY_RELEASE_GATE_INJECTION",
    }


def galaxy_pass(query, limit, *, bad_provenance=False, dirty=False):
    record = {
        "record_id": "LEGACY-1",
        "scope": "MemoryOS",
        "statement": "gravity memory calibration",
        "status": "ACTIVE",
        "source": "verified-existing-memory",
    }
    return {
        "schema": gateway.GALAXY_SCHEMA,
        "scope": "MemoryOS",
        "execution": "READ_ONLY",
        "candidate_set_preserved": True,
        "provenance_preserved": True,
        "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
        "ranking": gateway.GALAXY_RANKING,
        "galaxy_weighting_applied": True,
        "memory_context_authority": "NONE",
        "automatic_capture": False,
        "automatic_promotion": False,
        "physical_delete": False,
        "e_lanes_modified": False,
        "writes_performed": ["memory_records"] if dirty else [],
        "records": [{
            "record": record,
            "source_provenance": "invented" if bad_provenance else record["source"],
            "governing_state": {
                "record_id": "LEGACY-1",
                "state": "CURRENT",
                "current_default_eligible": True,
            },
            "not_identity_authority": True,
            "ranking": {"score": 0.84},
        }],
        "count": 1,
        "historical_context": [],
        "verified_linked_context": [],
    }


def isolated(script, db):
    env = dict(os.environ)
    env.pop("TURSO_DATABASE_URL", None)
    env.pop("TURSO_AUTH_TOKEN", None)
    env["MEMCONOS_DB_PATH"] = db
    env["PYTHONPATH"] = str(ROOT / "api")
    p = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        text=True, capture_output=True, cwd=ROOT, env=env, timeout=35,
    )
    if p.returncode:
        raise AssertionError(f"subprocess failed: {p.stderr}\n{p.stdout}")
    return json.loads(p.stdout)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeRuntime()

    def test_heatdeath_returns_exact_native_legacy_without_galaxy(self):
        # Missing durable mode control selects emergency, never BIGBANG.
        original = self.rt.search_records("gravity", 4, "MemoryOS")
        self.rt.calls.clear()
        with patch.object(gateway.importlib, "import_module",
                          side_effect=AssertionError("GALAXY import attempted")):
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "PASS_HEATDEATH")
        self.assertEqual(out["effective_mode"], mode.HEATDEATH)
        self.assertEqual(out["retrieval"], original)
        self.assertIsNone(out["galaxy_context"])
        self.assertFalse(out["galaxy_applied"])
        self.assertFalse(out["fallback_occurred"])
        self.assertEqual(self.rt.calls, [("gravity", 4, "MemoryOS")])

    def test_uninitialized_refuses_control_lookup_or_schema_creation(self):
        self.rt._INITIALIZED = False
        with patch.object(gateway.mode, "mode_status",
                          side_effect=AssertionError("mode touched")):
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "HOLD_RUNTIME_NOT_INITIALIZED")
        self.assertIsNone(out["retrieval"])
        self.assertEqual(self.rt.calls, [])

    def test_invalid_modes_do_not_activate_galaxy(self):
        for fake in (
            {"schema": mode.SCHEMA, "effective_mode": "BIGBANG",
             "configured_mode": "BIGBANG", "bigbang_activation_enabled": False},
            {"schema": mode.SCHEMA, "effective_mode": "JIMBANG",
             "configured_mode": "BIGBANG", "bigbang_activation_enabled": True},
            {"schema": "unknown", "effective_mode": "BIGBANG",
             "configured_mode": "BIGBANG", "bigbang_activation_enabled": True},
            None,
        ):
            with self.subTest(fake=fake), patch.object(
                gateway.mode, "mode_status", return_value=fake
            ), patch.object(
                gateway.importlib, "import_module",
                side_effect=AssertionError("GALAXY must remain OFF"),
            ):
                out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
                self.assertEqual(out["status"], "PASS_HEATDEATH")
                self.assertEqual(out["effective_mode"], mode.HEATDEATH)

    def test_test_only_bigbang_path_keeps_native_legacy_separate(self):
        fake_galaxy = types.SimpleNamespace(
            operational=lambda rt, q, lim: galaxy_pass(q, lim),
        )
        with patch.object(gateway.mode, "mode_status",
                          return_value=bigbang_control()), patch.object(
            gateway.importlib, "import_module", return_value=fake_galaxy
        ) as imported:
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "PASS_BIGBANG")
        self.assertEqual(out["effective_mode"], mode.BIGBANG)
        self.assertTrue(out["galaxy_applied"])
        self.assertEqual(out["galaxy_context"]["records"][0]["record"]["record_id"],
                         "LEGACY-1")
        self.assertEqual(out["retrieval"], self.rt.search_records(
            "gravity", 4, "MemoryOS"
        ))
        self.assertEqual(out["writes_performed"], [])
        imported.assert_called_once_with("galaxy_frontdoor_context")

    def test_bigbang_fails_to_heatdeath_on_galaxy_import_failure(self):
        with patch.object(gateway.mode, "mode_status",
                          return_value=bigbang_control()), patch.object(
            gateway.importlib, "import_module",
            side_effect=ModuleNotFoundError("missing GALAXY"),
        ):
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "PASS_HEATDEATH_FALLBACK")
        self.assertEqual(out["effective_mode"], mode.HEATDEATH)
        self.assertTrue(out["fallback_occurred"])
        self.assertTrue(out["manual_emergency_latch_required"])
        self.assertEqual(out["galaxy_error_type"], "ModuleNotFoundError")
        self.assertEqual(len(self.rt.calls), 1)
        self.assertEqual(out["retrieval"]["records"][0]["record_id"], "LEGACY-1")

    def test_galaxy_contract_failure_and_source_spoofing_fall_back(self):
        for bad in (galaxy_pass("gravity", 4, bad_provenance=True),
                    galaxy_pass("gravity", 4, dirty=True),
                    {"status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL"}):
            with self.subTest(bad=bad), patch.object(
                gateway.mode, "mode_status", return_value=bigbang_control()
            ), patch.object(gateway.importlib, "import_module",
                            return_value=types.SimpleNamespace(
                                operational=lambda *_: bad)):
                out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
            self.assertEqual(out["status"], "PASS_HEATDEATH_FALLBACK")
            self.assertEqual(out["galaxy_error_type"], "ValueError")
            self.assertEqual(out["writes_performed"], [])

    def test_galaxy_invalid_history_and_linked_context_fall_back(self):
        wrong_history = galaxy_pass("gravity", 4)
        wrong_history["historical_context"] = [{
            "record": {"record_id": "HIST", "scope": "VERA_E_LANE", "source": "s"},
            "source_provenance": "s",
            "governing_state": {"record_id": "HIST", "current_default_eligible": False},
        }]
        bad_link = galaxy_pass("gravity", 4)
        bad_link["verified_linked_context"] = [{
            "record": {"record_id": "LINK", "scope": "MemoryOS", "source": "s"},
            "source_provenance": "s", "context_only": True,
            "governing_state": {"record_id": "LINK"},
            "verified_direct_primary_edges": [{
                "edge_id": "UNRELATED", "source_record_id": "LINK",
                "target_record_id": "NON_PRIMARY",
            }],
        }]
        for malformed in (wrong_history, bad_link):
            with self.subTest(case=malformed), patch.object(
                gateway.mode, "mode_status", return_value=bigbang_control()
            ), patch.object(gateway.importlib, "import_module",
                            return_value=types.SimpleNamespace(
                                operational=lambda *_: malformed)):
                out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
            self.assertEqual(out["status"], "PASS_HEATDEATH_FALLBACK")
            self.assertFalse(out["galaxy_applied"])

    def test_galaxy_no_match_is_explicit_hold_not_fabricated(self):
        def no_match(*_):
            return {
                "schema": gateway.GALAXY_SCHEMA,
                "scope": "MemoryOS",
                "execution": "READ_ONLY",
                "memory_context_authority": "NONE",
                "status": "HOLD_NO_CONFIDENT_GALAXY_MATCH",
                "records": [],
                "writes_performed": [],
            }
        with patch.object(gateway.mode, "mode_status",
                          return_value=bigbang_control()), patch.object(
            gateway.importlib, "import_module",
            return_value=types.SimpleNamespace(operational=no_match),
        ):
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "HOLD_BIGBANG_NO_CONFIDENT_MATCH")
        self.assertEqual(out["effective_mode"], mode.BIGBANG)
        self.assertFalse(out["galaxy_applied"])
        self.assertFalse(out["fallback_occurred"])
        self.assertEqual(out["retrieval"]["count"], 1)

    def test_nonmemory_scope_and_empty_query_never_enter_galaxy(self):
        with patch.object(gateway.mode, "mode_status",
                          return_value=bigbang_control()), patch.object(
            gateway.importlib, "import_module",
            side_effect=AssertionError("GALAXY should not be touched"),
        ):
            scoped = gateway.read(self.rt, "gravity", "ANVIL_E_LANE", 4)
            empty = gateway.read(self.rt, "", "MemoryOS", 4)
        self.assertEqual(scoped["status"], "PASS_BIGBANG_LEGACY_SCOPE_ONLY")
        self.assertEqual(empty["status"], "PASS_BIGBANG_LEGACY_SCOPE_ONLY")
        self.assertFalse(scoped["galaxy_applied"])

    def test_legacy_failure_is_hold_not_invented_fallback(self):
        def offline(*_):
            raise RuntimeError("durable memory database unavailable")
        self.rt.search_records = offline
        with patch.object(gateway.mode, "mode_status",
                          return_value=bigbang_control()):
            out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "HOLD_LEGACY_UNAVAILABLE")
        self.assertIsNone(out["retrieval"])
        self.assertFalse(out["fallback_occurred"])

    def test_malformed_legacy_envelope_holds(self):
        self.rt.search_records = lambda *_: {
            "records": [{"record_id": "FAKE"}], "count": 99
        }
        out = gateway.read(self.rt, "gravity", "MemoryOS", 4)
        self.assertEqual(out["status"], "HOLD_LEGACY_CONTRACT_INVALID")
        self.assertIsNone(out["retrieval"])

    def test_real_sqlite_legacy_reads_leave_protected_tables_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            db = str(Path(d) / "live-fixture.sqlite")
            out = isolated(
                """
                import json
                import memcon_runtime as rt
                import gaiaos_memory_gateway as gateway
                rt.initialize()
                rt.write_record(
                    authority="NAOMI", approved=True, record_type="FIXTURE",
                    scope="MemoryOS", statement="gravity memory reference",
                    source="real-sqlite-test", record_id="GATE-1",
                )
                rt.write_record(
                    authority="NAOMI", approved=True, record_type="FIXTURE",
                    scope="ANVIL_E_LANE", statement="gravity memory reference",
                    source="real-sqlite-test", record_id="GATE-2",
                )
                names = (
                    "memory_records", "memory_relations", "memory_gravity",
                    "memory_importance", "memory_lifecycle",
                    "memory_lifecycle_events", "memory_syntheses",
                    "runtime_receipts", "memory_candidates",
                )
                def counts():
                    with rt._db() as conn:
                        return [conn.execute("SELECT count(*) FROM " + name
                                ).fetchone()[0] for name in names]
                before = counts()
                got = gateway.read(rt, "gravity memory", "MemoryOS", 5)
                after = counts()
                print(json.dumps({
                    "status": got["status"],
                    "mode": got["effective_mode"],
                    "record_ids": [r["record_id"] for r in got["retrieval"]["records"]],
                    "scope": got["retrieval"]["scope_applied"],
                    "counts_unchanged": before == after,
                    "galaxy_context": got["galaxy_context"],
                }))
                """, db,
            )
            self.assertEqual(out["status"], "PASS_HEATDEATH")
            self.assertEqual(out["mode"], "HEATDEATH")
            self.assertEqual(out["record_ids"], ["GATE-1"])
            self.assertEqual(out["scope"], "MemoryOS")
            self.assertTrue(out["counts_unchanged"])
            self.assertIsNone(out["galaxy_context"])

    def test_galaxy_broken_import_does_not_prevent_gateway_import(self):
        with tempfile.TemporaryDirectory() as d:
            result = isolated(
                """
                import builtins, json
                old = builtins.__import__
                def sabotaged(name, *args, **kwargs):
                    if name.startswith("galaxy"):
                        raise ImportError("test GALAXY code is broken")
                    return old(name, *args, **kwargs)
                builtins.__import__ = sabotaged
                import gaiaos_memory_gateway as gateway
                class Runtime:
                    _INITIALIZED = True
                    def _db(self):
                        raise RuntimeError("control offline")
                    def search_records(self, q, limit, scope):
                        return {
                            "records": [], "count": 0, "runtime": "test",
                            "query_terms_applied": q.split(),
                            "scope_applied": scope,
                            "query_filter_active": bool(q.strip()),
                        }
                got = gateway.read(Runtime(), "nothing", "MemoryOS", 3)
                print(json.dumps({"status":got["status"],"mode":got["effective_mode"]}))
                """, str(Path(d) / "independent.sqlite"),
            )
            self.assertEqual(result, {"status": "PASS_HEATDEATH",
                                      "mode": "HEATDEATH"})

    def test_source_has_no_application_routes_or_write_effect(self):
        source = (ROOT / "api" / "gaiaos_memory_gateway.py").read_text()
        self.assertNotIn("\nimport galaxy_frontdoor_context", source)
        self.assertNotIn("\nfrom galaxy_frontdoor_context", source)
        for forbidden in ("write_record(", "engage_heatdeath(",
                          "galaxy_production.activate(", "INSERT INTO ",
                          "DELETE FROM ", "UPDATE memory_"):
            self.assertNotIn(forbidden, source)
        mode_source = (ROOT / "api" / "gaiaos_memory_mode.py").read_text()
        self.assertIn("BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED", mode_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
