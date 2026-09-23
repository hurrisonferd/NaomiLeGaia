"""Offline tests for the finite GALAXY Phase-3 Exit Integration gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_phase3_exit as exit_gate


class FakeRuntime:
    GALAXY_PHASE3C_CALIBRATION_QUERIES = (
        "gravity contextual influence memory retrieval",
        "history current context revision memory",
        "authority permission memory retrieval",
        "calibration core revision memory context",
        "provenance contradiction memory context",
        "satellite calibration core memory context",
    )
    GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS = {
        "planetary", "trajectory", "trajectories", "advertising",
    }
    GALAXY_QUERY_CONCEPT_ALIASES = {
        "contextual": "context",
        "retrieval": "memory",
        "memories": "memory",
    }

    def __init__(self):
        self.writes = 0
        self.records = [
            {
                "record_id": "GRAVITY",
                "scope": "MemoryOS",
                "statement": (
                    "GALAXY gravity must remain an estimate of contextual influence, "
                    "never truth, authority, or permission."
                ),
                "notes": "memory retrieval authority",
                "source": "TEST",
            },
            {
                "record_id": "SATELLITE",
                "scope": "MemoryOS",
                "statement": (
                    "GALAXY-CAL-SATELLITE: A satellite note provides limited "
                    "context for the calibration core."
                ),
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "REVISION",
                "scope": "MemoryOS",
                "statement": (
                    "GALAXY-CAL-REVISION: A later controlled observation revises "
                    "the calibration core toward ultraviolet."
                ),
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "REINFORCER",
                "scope": "MemoryOS",
                "statement": (
                    "GALAXY-CAL-REINFORCER: An independent observation reinforces "
                    "the calibration core."
                ),
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "CORE",
                "scope": "MemoryOS",
                "statement": (
                    "GALAXY-CAL-CORE: The calibration core reports a violet "
                    "carrier pulse."
                ),
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "NOTES_ONLY",
                "scope": "MemoryOS",
                "statement": "Unrelated procedural record.",
                "notes": (
                    "gravity contextual influence memory retrieval calibration "
                    "core revision satellite"
                ),
                "source": "TEST",
            },
        ]
        self.edges = [
            {
                "edge_id": "EDGE-REV-CORE",
                "source_record_id": "REVISION",
                "target_record_id": "CORE",
                "relation_type": "REVISES",
                "status": "VERIFIED",
            },
            {
                "edge_id": "EDGE-SAT-CORE",
                "source_record_id": "SATELLITE",
                "target_record_id": "CORE",
                "relation_type": "CONTEXT_FOR",
                "status": "VERIFIED",
            },
            {
                "edge_id": "EDGE-REV-REINFORCER",
                "source_record_id": "REVISION",
                "target_record_id": "REINFORCER",
                "relation_type": "CONTRADICTS",
                "status": "VERIFIED",
            },
        ]

    @staticmethod
    def _galaxy_query_tokens(text):
        import re
        stop = {
            "a", "an", "and", "are", "as", "at", "be", "can", "could", "does",
            "do", "ever", "for", "from", "how", "i", "in", "is", "it", "like",
            "much", "of", "on", "or", "should", "that", "the", "this", "to",
            "what", "when", "where", "which", "who", "why", "with", "would",
            "act", "become",
        }
        return [
            token for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
            if token not in stop
        ]

    def _galaxy_query_concept(self, token):
        return self.GALAXY_QUERY_CONCEPT_ALIASES.get(token, token)

    def search_records(self, query, limit=100, scope=None):
        rows = [r for r in self.records if scope is None or r["scope"] == scope]
        return {"records": rows[:limit], "count": min(len(rows), limit)}

    def galaxy_record(self, record_id):
        row = next((r for r in self.records if r["record_id"] == record_id), None)
        if row is None:
            return None
        relations = [
            edge for edge in self.edges
            if edge["source_record_id"] == record_id
            or edge["target_record_id"] == record_id
        ]
        return {"record": row, "relations": relations}


class CarrierPackagingTests(unittest.TestCase):
    def test_render_image_packages_phase3_exit_module(self):
        root = Path(__file__).resolve().parents[1]
        dockerfile = (root / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY api/galaxy_phase3_exit.py ./galaxy_phase3_exit.py",
            dockerfile,
        )


class Phase3ExitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_statement_only_primary_excludes_notes_noise(self):
        result = exit_gate.build_candidate_pool(
            self.runtime,
            self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[0],
            scope="MemoryOS",
            limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["candidate_record_ids"], ["GRAVITY"])
        self.assertNotIn("NOTES_ONLY", result["candidate_record_ids"])
        self.assertTrue(result["checks"]["notes_or_scope_cannot_create_primary"])
        self.assertEqual(self.runtime.writes, 0)

    def test_memory_scope_term_is_not_counted_as_content_evidence(self):
        query = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[3]
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        revision = next(
            row for row in result["primary_evidence"]
            if row["record_id"] == "REVISION"
        )
        self.assertIn("memory", revision["query_concepts_raw"])
        self.assertNotIn("memory", revision["query_concepts"])
        self.assertEqual(
            revision["scope_domain_query_concepts_excluded"], ["memory"]
        )

    def test_revision_query_has_anchored_primary_and_separate_context_lane(self):
        query = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[3]
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["candidate_record_ids"], ["REVISION"])
        self.assertEqual(result["required_primary_concepts"], ["revision"])
        self.assertIn("CORE", result["linked_context_record_ids"])
        self.assertIn("REINFORCER", result["linked_context_record_ids"])
        self.assertNotIn("CORE", result["candidate_record_ids"])
        self.assertFalse(result["checks"]["linked_context_admitted_to_primary_lane"])
        self.assertTrue(
            result["checks"]["linked_context_ranked_only_within_context_lane"]
        )

    def test_satellite_query_keeps_core_as_verified_context_not_primary(self):
        query = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[5]
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["candidate_record_ids"], ["SATELLITE"])
        self.assertEqual(result["required_primary_concepts"], ["satellite"])
        self.assertEqual(result["linked_context_record_ids"], ["CORE"])
        self.assertEqual(
            result["constellation_record_ids"], ["SATELLITE", "CORE"]
        )

    def test_phase3j_bridge_recovers_hard_revision_paraphrase(self):
        result = exit_gate.build_candidate_pool(
            self.runtime,
            "subsequent finding updates the violet calibration result",
            scope="MemoryOS",
            limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["candidate_record_ids"], ["REVISION"])
        self.assertEqual(self.runtime.writes, 0)

    def test_external_domain_fails_closed(self):
        result = exit_gate.build_candidate_pool(
            self.runtime, "planetary gravity trajectories",
            scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["candidate_record_ids"], [])

    def test_primary_overflow_holds(self):
        query = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[3]
        for index in range(5):
            self.runtime.records.append({
                "record_id": f"OVERFLOW-{index}",
                "scope": "MemoryOS",
                "statement": "calibration core revision context",
                "notes": "",
                "source": "TEST",
            })
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["primary_overflow_record_ids"])

    def test_review_suite_is_read_only_bounded_and_ready(self):
        result = exit_gate.review_suite(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_PREFLIGHT", result)
        self.assertEqual(result["query_indexes"], [0, 3, 5])
        self.assertTrue(result["checks"]["zero_memory_writes"])
        self.assertFalse(result["checks"]["pilot_activated"])
        self.assertEqual(self.runtime.writes, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
