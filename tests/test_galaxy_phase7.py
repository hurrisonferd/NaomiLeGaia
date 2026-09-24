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
        self.assertIn("import galaxy_phase7", bridge)
        self.assertIn(
            '@app.get("/galaxy/pruning/phase7-fixture-review"',
            bridge,
        )
        segment = bridge.split(
            '@app.get("/galaxy/pruning/phase7-fixture-review"', 1
        )[1].split(
            '@app.get("/galaxy/lifecycle/phase6-fixture-review"', 1
        )[0]
        self.assertIn("gaiaos_api._authorize_browser_session(browser_request)", segment)
        self.assertIn("galaxy_phase7.review_with_readback(", segment)
        self.assertNotIn("@app.post(", segment)
        self.assertNotIn("galaxy_phase7.execute", bridge)
        self.assertNotIn("galaxy_phase7.prune", bridge)
        self.assertNotIn("galaxy_phase7.delete", bridge)
        self.assertIn("COPY api/galaxy_phase7.py ./galaxy_phase7.py", docker)

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
