"""Offline tests for GALAXY Phase 7A pruning research."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import memcon_runtime as runtime
import galaxy_phase7 as p7
import galaxy_phase7_tombstone as p7d
import galaxy_phase7_tombstone_shadow as p7e
import galaxy_phase7_isolated_restore as p7f


class Phase7PruningResearchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.originals = (runtime.DB_PATH, runtime.STORAGE_BACKEND, runtime._INITIALIZED)
        runtime.DB_PATH = Path(self.temporary.name) / "phase7.sqlite3"
        runtime.STORAGE_BACKEND = "local_sqlite"
        runtime._INITIALIZED = False
        runtime.initialize()

        for record_id, statement in (
            ("MEM-P7-OLD", "Superseded historical calibration observation."),
            ("MEM-P7-NEW", "Current replacement calibration observation."),
            ("MEM-P7-CURRENT", "Current independent observation."),
        ):
            runtime.write_record(
                authority="NAOMI",
                record_type="OBSERVATION",
                scope="MemoryOS",
                statement=statement,
                source="GALAXY_PHASE7_TEST",
                approved=True,
                record_id=record_id,
            )

    def tearDown(self):
        runtime.DB_PATH, runtime.STORAGE_BACKEND, runtime._INITIALIZED = self.originals
        self.temporary.cleanup()

    def _set_lifecycle(self, record_id, state):
        with runtime._db() as conn:
            conn.execute(
                """INSERT INTO memory_lifecycle
                   (record_id,state,changed_at,reason,authority,receipt_id)
                   VALUES (?,?,?,?,?,?)""",
                (record_id, state, runtime._now(), "phase7 test fixture", "NAOMI", None),
            )

    def _verify_supersedes(self, source_id, target_id):
        proposal = runtime.galaxy_propose_relation(
            source_record_id=source_id,
            target_record_id=target_id,
            relation_type="SUPERSEDES",
            strength=1.0,
            evidence={"purpose": "phase7 test"},
            classifier="GALAXY_PHASE7_TEST",
        )
        edge_id = proposal["relation"]["edge_id"]
        runtime.galaxy_verify_relation(edge_id, authority="NAOMI", approved=True)
        return edge_id

    def _counts(self):
        with runtime._db() as conn:
            tables = (
                "memory_records", "memory_relations", "memory_gravity",
                "memory_importance", "memory_lifecycle",
                "memory_lifecycle_events", "memory_syntheses",
                "runtime_receipts",
            )
            return {
                table: runtime._fetchone_dict(
                    conn, f"SELECT COUNT(*) AS n FROM {table}"
                )["n"]
                for table in tables
            }

    def test_missing_record_holds_without_effect(self):
        before = self._counts()
        result = p7.review(runtime, "MEM-MISSING")
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["research_hold_reasons"], ["RECORD_NOT_FOUND"])
        self.assertFalse(result["destructive_eligibility"])
        self.assertEqual(result["writes_performed"], [])
        self.assertEqual(self._counts(), before)

    def test_compressed_current_record_is_not_research_candidate(self):
        self._set_lifecycle("MEM-P7-CURRENT", "COMPRESSED")
        before = self._counts()
        record_before = runtime.get_record("MEM-P7-CURRENT")
        result = p7.review(runtime, "MEM-P7-CURRENT")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("CURRENT_DEFAULT_ELIGIBLE", result["research_hold_reasons"])
        self.assertFalse(result["research_candidate"])
        self.assertFalse(result["physical_delete"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertEqual(runtime.get_record("MEM-P7-CURRENT"), record_before)
        self.assertEqual(self._counts(), before)

    def test_superseded_compressed_record_can_only_be_research_candidate(self):
        self._verify_supersedes("MEM-P7-NEW", "MEM-P7-OLD")
        self._set_lifecycle("MEM-P7-OLD", "COMPRESSED")
        before = self._counts()
        old_before = runtime.get_record("MEM-P7-OLD")

        result = p7.review(runtime, "MEM-P7-OLD")

        self.assertEqual(result["status"], "PASS_READ_ONLY_RESEARCH_CANDIDATE", result)
        self.assertTrue(result["research_candidate"])
        self.assertEqual(result["proposed_research_label"], "PRUNABLE_RESEARCH_ONLY")
        self.assertFalse(result["governing_state"]["current_default_eligible"])
        self.assertEqual(len(result["incoming_verified_supersedes"]), 1)
        self.assertFalse(result["destructive_eligibility"])
        self.assertTrue(all(value is False for value in result["destructive_gates"].values()))
        self.assertEqual(result["writes_performed"], [])
        self.assertEqual(runtime.get_record("MEM-P7-OLD"), old_before)
        self.assertEqual(runtime.galaxy_record("MEM-P7-OLD")["lifecycle"]["state"], "COMPRESSED")
        self.assertEqual(self._counts(), before)

    def test_outgoing_governing_record_is_held(self):
        self._verify_supersedes("MEM-P7-NEW", "MEM-P7-OLD")
        self._set_lifecycle("MEM-P7-NEW", "COMPRESSED")
        result = p7.review(runtime, "MEM-P7-NEW")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("GOVERNS_OTHER_RECORDS", result["research_hold_reasons"])
        self.assertFalse(result["destructive_eligibility"])

    def test_synthesis_source_dependency_holds_candidate(self):
        self._verify_supersedes("MEM-P7-NEW", "MEM-P7-OLD")
        self._set_lifecycle("MEM-P7-OLD", "COMPRESSED")
        runtime.write_record(
            authority="NAOMI",
            record_type="SYNTHESIS",
            scope="GALAXY_SYNTHESIS_SHADOW",
            statement="Test synthesis.",
            source="GALAXY_PHASE7_TEST",
            status="SYNTHESIS_VERIFIED_SHADOW",
            approved=True,
            record_id="MEM-P7-SYNTH",
        )
        with runtime._db() as conn:
            conn.execute(
                """INSERT INTO memory_syntheses
                   (synthesis_record_id,source_record_ids_json,method,confidence,created_at,authority)
                   VALUES (?,?,?,?,?,?)""",
                (
                    "MEM-P7-SYNTH",
                    json.dumps(["MEM-P7-OLD"]),
                    "PHASE7_TEST",
                    1.0,
                    runtime._now(),
                    "NAOMI",
                ),
            )
        result = p7.review(runtime, "MEM-P7-OLD")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("SYNTHESIS_PROVENANCE_DEPENDENCY", result["research_hold_reasons"])
        self.assertFalse(result["research_candidate"])

    def test_zero_write_readback_wrapper_proves_candidate_path_unchanged(self):
        self._verify_supersedes("MEM-P7-NEW", "MEM-P7-OLD")
        self._set_lifecycle("MEM-P7-OLD", "COMPRESSED")
        before = self._counts()
        result = p7.review_with_readback(runtime, "MEM-P7-OLD")
        self.assertEqual(result["status"], "PASS_READ_ONLY_RESEARCH_CANDIDATE", result)
        self.assertEqual(result["readback_status"], "PASS_ZERO_WRITE_READBACK", result)
        self.assertTrue(result["zero_write_readback"])
        self.assertTrue(all(result["readback_checks"].values()))
        self.assertEqual(result["database_counts_before"], result["database_counts_after"])
        self.assertEqual(self._counts(), before)

    def test_zero_write_readback_wrapper_proves_hold_path_unchanged(self):
        self._set_lifecycle("MEM-P7-CURRENT", "COMPRESSED")
        before = self._counts()
        result = p7.review_with_readback(runtime, "MEM-P7-CURRENT")
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["readback_status"], "PASS_ZERO_WRITE_READBACK", result)
        self.assertTrue(result["zero_write_readback"])
        self.assertEqual(self._counts(), before)

    def test_carrier_exposes_only_authenticated_get_fixture_surface(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        docker = (ROOT / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('galaxy_phase7 = deferred("galaxy_phase7")', bridge)
        self.assertIn("from gaiaos_lazy_diagnostics import deferred", bridge)
        self.assertNotIn("\\nimport galaxy_phase7\\n", bridge)
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-fixture-review"',
            bridge,
        )
        segment = bridge.split(
            '@app.get("/galaxy/pruning/phase7-fixture-review"', 1
        )[1].split(
            '@app.get("/galaxy/pruning/phase7-positive-canary"', 1
        )[0]
        self.assertIn("gaiaos_api._authorize_browser_session(browser_request)", segment)
        self.assertIn("galaxy_phase7.review_with_readback(", segment)
        self.assertNotIn("@app.post(", segment)
        self.assertNotIn("galaxy_phase7.execute", bridge)
        self.assertNotIn("galaxy_phase7.prune", bridge)
        self.assertNotIn("galaxy_phase7.delete", bridge)
        self.assertIn("COPY api/galaxy_phase7.py ./galaxy_phase7.py", docker)

    def test_positive_path_canary_uses_shared_locks_without_database_access(self):
        before = self._counts()
        result = p7.positive_path_canary()
        self.assertEqual(result["status"], "PASS_SYNTHETIC_POSITIVE_CANARY", result)
        self.assertTrue(result["synthetic_only"])
        self.assertFalse(result["production_database_access"])
        self.assertTrue(result["research_candidate"])
        self.assertEqual(result["proposed_research_label"], "PRUNABLE_RESEARCH_ONLY")
        self.assertEqual(result["research_hold_reasons"], [])
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["destructive_eligibility"])
        self.assertTrue(all(value is False for value in result["destructive_gates"].values()))
        self.assertEqual(result["writes_performed"], [])
        self.assertEqual(self._counts(), before)

    def test_carrier_exposes_authenticated_get_only_positive_canary(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-positive-canary"',
            bridge,
        )
        segment = bridge.split(
            '@app.get("/galaxy/pruning/phase7-positive-canary"', 1
        )[1].split(
            '@app.get("/galaxy/pruning/phase7-tombstone-contract-canary"', 1
        )[0]
        self.assertIn("gaiaos_api._authorize_browser_session(browser_request)", segment)
        self.assertIn("galaxy_phase7.positive_path_canary()", segment)
        self.assertNotIn("@app.post(", segment)

    def test_real_review_uses_shared_research_hold_evaluator(self):
        self._set_lifecycle("MEM-P7-CURRENT", "COMPRESSED")
        original = p7._research_hold_reasons
        calls = []
        def sentinel(**kwargs):
            calls.append(kwargs)
            return ["SHARED_LOCK_SENTINEL"]
        p7._research_hold_reasons = sentinel
        try:
            result = p7.review(runtime, "MEM-P7-CURRENT")
        finally:
            p7._research_hold_reasons = original
        self.assertEqual(result["research_hold_reasons"], ["SHARED_LOCK_SENTINEL"])
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(len(calls), 1)

    def test_phase7d_tombstone_contract_round_trip_is_exact_and_nondestructive(self):
        before = self._counts()
        result = p7d.synthetic_tombstone_contract_canary()
        self.assertEqual(result["status"], "PASS_SYNTHETIC_TOMBSTONE_CONTRACT_CANARY", result)
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["physical_delete"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertFalse(result["destructive_eligibility"])
        self.assertFalse(result["destructive_gates"]["tombstone_protocol_implemented"])
        self.assertFalse(result["destructive_gates"]["destructive_restore_proven"])
        self.assertEqual(self._counts(), before)

    def test_phase7d_corrupted_manifest_fails_closed(self):
        result = p7d.synthetic_tombstone_contract_canary()
        manifest = result["manifest"]
        manifest["evidence_bundle"]["record"]["statement"] = "CORRUPTED"
        restoration = p7d.restore_in_memory(manifest)
        self.assertEqual(restoration["status"], "HOLD_RESTORE_REFUSED")
        self.assertFalse(restoration["restored"])
        self.assertFalse(restoration["validation"]["checks"]["evidence_hash_matches"])
        self.assertIsNone(restoration["restored_bundle"])

    def test_phase7d_module_has_no_database_or_destructive_surface(self):
        source = (ROOT / "api" / "galaxy_phase7_tombstone.py").read_text(encoding="utf-8")
        for forbidden in (
            "memcon_runtime", "sqlite3", "DELETE FROM", "UPDATE memory_",
            "INSERT INTO memory_", "def delete", "def prune", "def execute",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(p7d.TOMBSTONE_PROTOCOL_IMPLEMENTED)
        self.assertFalse(p7d.DESTRUCTIVE_RESTORE_PROVEN)
        self.assertFalse(p7d.PHYSICAL_PRUNING_ENABLED)
        self.assertFalse(p7d.PRODUCTION_ATTENUATION_ENABLED)

    def test_phase7e_shadow_write_preserves_all_protected_tables(self):
        before = self._counts()
        ready = p7e.inspect(runtime)
        self.assertEqual(ready["status"], "PASS_READY_FOR_EXPLICIT_SHADOW_WRITE", ready)
        result = p7e.execute(
            runtime,
            authority="NAOMI",
            approved=True,
            confirmation=p7e.CONFIRMATION,
        )
        self.assertEqual(result["status"], "PASS_READBACK", result)
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["protected_counts_before"], result["protected_counts_after"])
        after = self._counts()
        for table in (
            "memory_records", "memory_relations", "memory_gravity",
            "memory_importance", "memory_lifecycle", "memory_lifecycle_events",
            "memory_syntheses",
        ):
            self.assertEqual(after[table], before[table], table)
        self.assertEqual(after["runtime_receipts"], before["runtime_receipts"] + 1)
        self.assertFalse(result["memoryos_mutation"])
        self.assertFalse(result["physical_delete"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertFalse(result["destructive_eligibility"])
        with runtime._db() as conn:
            shadow_count = runtime._fetchone_dict(
                conn, "SELECT COUNT(*) AS n FROM galaxy_tombstones_shadow"
            )["n"]
            receipt_count = runtime._fetchone_dict(
                conn,
                """SELECT COUNT(*) AS n FROM runtime_receipts
                   WHERE operation='GALAXY_PHASE7E_SHADOW_TOMBSTONE_WRITE'"""
            )["n"]
        self.assertEqual(shadow_count, 1)
        self.assertEqual(receipt_count, 1)

    def test_phase7e_duplicate_write_fails_closed(self):
        p7e.execute(
            runtime,
            authority="NAOMI",
            approved=True,
            confirmation=p7e.CONFIRMATION,
        )
        with self.assertRaises(ValueError):
            p7e.execute(
                runtime,
                authority="NAOMI",
                approved=True,
                confirmation=p7e.CONFIRMATION,
            )

    def test_phase7e_corrupted_shadow_manifest_holds_readback(self):
        p7e.execute(
            runtime,
            authority="NAOMI",
            approved=True,
            confirmation=p7e.CONFIRMATION,
        )
        with runtime._db() as conn:
            conn.execute(
                """UPDATE galaxy_tombstones_shadow
                   SET manifest_json=? WHERE tombstone_id=?""",
                ('{"corrupt":true}', p7e.TOMBSTONE_ID),
            )
        result = p7e.inspect(runtime)
        self.assertEqual(result["status"], "HOLD_SHADOW_READBACK")
        self.assertFalse(result["checks"]["manifest_valid"])

    def test_phase7e_requires_explicit_naomi_confirmation(self):
        with self.assertRaises(PermissionError):
            p7e.execute(
                runtime,
                authority="NAOMI",
                approved=False,
                confirmation=p7e.CONFIRMATION,
            )
        with self.assertRaises(PermissionError):
            p7e.execute(
                runtime,
                authority="NAOMI",
                approved=True,
                confirmation="WRONG_CONFIRMATION",
            )

    def test_phase7e_browser_controls_are_get_review_plus_explicit_post(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-tombstone-shadow-review"',
            bridge,
        )
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-tombstone-shadow-controls"',
            bridge,
        )
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-tombstone-shadow-controls/confirm"',
            bridge,
        )
        self.assertIn(
            '@app.post("/galaxy/pruning/phase7-tombstone-shadow-controls/manifest"',
            bridge,
        )
        self.assertIn("Explicit Naomi authorization required", bridge)
        self.assertNotIn(
            '@app.delete("/galaxy/pruning/phase7',
            bridge,
        )

    def test_phase7e_shadow_module_has_no_delete_or_memoryos_update_sql(self):
        source = (ROOT / "api" / "galaxy_phase7_tombstone_shadow.py").read_text(encoding="utf-8")
        self.assertNotIn("DELETE FROM", source)
        self.assertNotIn("UPDATE memory_", source)
        self.assertNotIn("INSERT INTO memory_records", source)
        self.assertNotIn("INSERT INTO memory_relations", source)
        self.assertNotIn("INSERT INTO memory_lifecycle", source)
        self.assertNotIn("INSERT INTO memory_syntheses", source)
        self.assertIn("INSERT INTO galaxy_tombstones_shadow", source)
        self.assertIn("INSERT INTO runtime_receipts", source)

    def test_phase7f_requires_existing_valid_shadow_before_isolated_restore(self):
        before = p7f._snapshot(runtime)
        result = p7f.review(runtime)
        self.assertEqual(result["status"], "HOLD_SHADOW_SOURCE_INVALID", result)
        self.assertFalse(result["restored"])
        self.assertFalse(result["isolated_store_created"])
        self.assertEqual(result["production_writes_performed"], [])
        self.assertTrue(result["runtime_counts_unchanged"])
        self.assertEqual(p7f._snapshot(runtime), before)

    def test_phase7f_reconstructs_exact_synthetic_bundle_in_unattached_ram(self):
        p7e.execute(
            runtime, authority="NAOMI", approved=True, confirmation=p7e.CONFIRMATION,
        )
        before = p7f._snapshot(runtime)
        result = p7f.review(runtime)
        self.assertEqual(result["status"], "PASS_ISOLATED_RESTORE", result)
        self.assertTrue(result["restored"])
        self.assertTrue(result["isolated_store_created"])
        self.assertTrue(result["isolated_store_discarded"])
        self.assertEqual(result["isolated_manifest_count"], 1)
        self.assertEqual(
            result["restored_evidence_bundle"],
            p7d.synthetic_tombstone_contract_canary()["manifest"]["evidence_bundle"],
        )
        self.assertEqual(result["restored_evidence_sha256"], p7e._expected_manifest()["evidence_sha256"])
        self.assertEqual(result["source_receipt_id"], p7e.inspect(runtime)["receipt"]["receipt_id"])
        self.assertTrue(all(result["source_checks"].values()))
        self.assertTrue(all(result["restore_checks"].values()))
        self.assertTrue(result["runtime_counts_unchanged"])
        self.assertTrue(result["same_shadow_source_after"])
        self.assertEqual(result["production_writes_performed"], [])
        self.assertFalse(result["production_memoryos_restore"])
        self.assertFalse(result["memoryos_mutation"])
        self.assertFalse(result["physical_delete"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertFalse(result["destructive_eligibility"])
        self.assertFalse(result["destructive_restore_proven"])
        self.assertEqual(p7f._snapshot(runtime), before)

    def test_phase7f_refuses_corrupted_shadow_without_isolated_restore(self):
        p7e.execute(
            runtime, authority="NAOMI", approved=True, confirmation=p7e.CONFIRMATION,
        )
        with runtime._db() as conn:
            conn.execute(
                "UPDATE galaxy_tombstones_shadow SET manifest_json=? WHERE tombstone_id=?",
                ('{"tampered":true}', p7e.TOMBSTONE_ID),
            )
        before = p7f._snapshot(runtime)
        result = p7f.review(runtime)
        self.assertEqual(result["status"], "HOLD_SHADOW_SOURCE_INVALID", result)
        self.assertFalse(result["restored"])
        self.assertFalse(result["isolated_store_created"])
        self.assertFalse(result["source_checks"]["manifest_valid"])
        self.assertEqual(p7f._snapshot(runtime), before)

    def test_phase7f_refuses_failed_receipt_without_production_write(self):
        receipt = p7e.execute(
            runtime, authority="NAOMI", approved=True, confirmation=p7e.CONFIRMATION,
        )["receipt"]["receipt_id"]
        with runtime._db() as conn:
            conn.execute(
                "UPDATE runtime_receipts SET result='FAILED' WHERE receipt_id=?",
                (receipt,),
            )
        before = p7f._snapshot(runtime)
        result = p7f.review(runtime)
        self.assertEqual(result["status"], "HOLD_SHADOW_SOURCE_INVALID", result)
        self.assertFalse(result["restored"])
        self.assertFalse(result["isolated_store_created"])
        self.assertFalse(result["source_checks"]["original_receipt_success"])
        self.assertEqual(p7f._snapshot(runtime), before)

    def test_phase7f_refuses_manifest_digest_mismatch(self):
        p7e.execute(
            runtime, authority="NAOMI", approved=True, confirmation=p7e.CONFIRMATION,
        )
        source = p7e.inspect(runtime)
        source["row"]["evidence_sha256"] = "BAD-DIGEST"
        result = p7f.restore_from_readback(source)
        self.assertEqual(result["status"], "HOLD_SHADOW_SOURCE_INVALID")
        self.assertFalse(result["source_checks"]["row_digest_exact"])
        self.assertFalse(result["isolated_store_created"])

    def test_phase7f_refuses_changed_source_between_readbacks(self):
        p7e.execute(
            runtime, authority="NAOMI", approved=True, confirmation=p7e.CONFIRMATION,
        )
        original = p7f.shadow.inspect
        calls = []
        def changed_second_inspection(config):
            result = original(config)
            calls.append(True)
            if len(calls) == 2:
                result["row"]["receipt_id"] = "CHANGED-RECEIPT"
            return result
        p7f.shadow.inspect = changed_second_inspection
        try:
            result = p7f.review(runtime)
        finally:
            p7f.shadow.inspect = original
        self.assertEqual(result["status"], "HOLD_RUNTIME_READBACK", result)
        self.assertFalse(result["restored"])
        self.assertTrue(result["runtime_counts_unchanged"])
        self.assertFalse(result["same_shadow_source_after"])
        self.assertEqual(len(calls), 2)

    def test_phase7f_exposes_exact_authenticated_get_only_route(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        docker = (ROOT / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('galaxy_phase7_isolated_restore = deferred("galaxy_phase7_isolated_restore")', bridge)
        self.assertIn("from gaiaos_lazy_diagnostics import deferred", bridge)
        self.assertNotIn("\\nimport galaxy_phase7_isolated_restore\\n", bridge)
        start = '@app.get("/galaxy/pruning/phase7-isolated-restore-review"'
        end = '@app.get("/galaxy/pruning/phase7-tombstone-shadow-controls"'
        self.assertIn(start, bridge)
        segment = bridge.split(start, 1)[1].split(end, 1)[0]
        self.assertIn("gaiaos_api._authorize_browser_session(browser_request)", segment)
        self.assertIn("galaxy_phase7_isolated_restore.review(memcon_runtime)", segment)
        self.assertNotIn("@app.post(", segment)
        self.assertNotIn("@app.delete(", segment)
        self.assertIn(
            "COPY api/galaxy_phase7_isolated_restore.py ./galaxy_phase7_isolated_restore.py",
            docker,
        )

    def test_phase7f_source_has_no_production_mutation_sql_or_delete_route(self):
        source = (ROOT / "api" / "galaxy_phase7_isolated_restore.py").read_text(encoding="utf-8")
        for forbidden in (
            "DELETE FROM", "UPDATE memory_", "INSERT INTO memory_",
            "INSERT INTO galaxy_tombstones_shadow", "INSERT INTO runtime_receipts",
            "def delete", "def prune", "def execute",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('sqlite3.connect(":memory:")', source)
        self.assertIn('conn.execute("PRAGMA database_list")', source)
        self.assertFalse(hasattr(p7f, "delete"))
        self.assertFalse(hasattr(p7f, "prune"))
        self.assertFalse(hasattr(p7f, "execute"))

    def test_phase7_module_contains_no_destructive_sql_or_mutation_entrypoint(self):
        source = (ROOT / "api" / "galaxy_phase7.py").read_text(encoding="utf-8")
        for forbidden in ("DELETE FROM", "UPDATE memory_", "INSERT INTO memory_"):
            self.assertNotIn(forbidden, source)
        self.assertFalse(hasattr(p7, "execute"))
        self.assertFalse(hasattr(p7, "delete"))
        self.assertFalse(hasattr(p7, "prune"))
        self.assertFalse(p7.PHYSICAL_PRUNING_ENABLED)
        self.assertFalse(p7.PRODUCTION_ATTENUATION_ENABLED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
