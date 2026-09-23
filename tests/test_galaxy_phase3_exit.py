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
                "statement": "GALAXY gravity remains an estimate of contextual influence.",
                "notes": "memory retrieval authority",
                "source": "TEST",
            },
            {
                "record_id": "CORE",
                "scope": "MemoryOS",
                "statement": "The calibration core revision memory context is observed.",
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "SATELLITE",
                "scope": "MemoryOS",
                "statement": "A satellite calibration core memory context note.",
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "REVISION",
                "scope": "MemoryOS",
                "statement": "A later controlled observation revises the calibration core toward ultraviolet.",
                "notes": "",
                "source": "TEST",
            },
            {
                "record_id": "LINKED",
                "scope": "MemoryOS",
                "statement": "Calibration detail.",
                "notes": "core revision memory context",
                "source": "TEST",
            },
            {
                "record_id": "NOTES_ONLY",
                "scope": "MemoryOS",
                "statement": "Unrelated procedural record.",
                "notes": "gravity contextual influence memory retrieval calibration core revision",
                "source": "TEST",
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
        relations = []
        if record_id == "LINKED":
            relations = [{
                "edge_id": "EDGE-LINKED",
                "source_record_id": "LINKED",
                "target_record_id": "CORE",
                "relation_type": "CONTEXT_FOR",
                "status": "VERIFIED",
            }]
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

    def test_linked_context_is_separate_and_never_weighted_candidate(self):
        query = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[3]
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertIn("CORE", result["candidate_record_ids"])
        self.assertIn("LINKED", result["linked_context_record_ids"])
        self.assertNotIn("LINKED", result["candidate_record_ids"])
        self.assertFalse(result["checks"]["linked_context_admitted_to_weighted_records"])

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
        query = "calibration core revision memory context"
        for index in range(5):
            self.runtime.records.append({
                "record_id": f"OVERFLOW-{index}",
                "scope": "MemoryOS",
                "statement": query,
                "notes": "",
                "source": "TEST",
            })
        result = exit_gate.build_candidate_pool(
            self.runtime, query, scope="MemoryOS", limit=10,
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["primary_overflow_record_ids"])

    def test_review_suite_is_read_only_and_bounded(self):
        result = exit_gate.review_suite(self.runtime)
        self.assertIn(result["status"], ("PASS_READ_ONLY_PREFLIGHT", "HOLD"))
        self.assertEqual(result["query_indexes"], [0, 3, 5])
        self.assertTrue(result["checks"]["zero_memory_writes"])
        self.assertFalse(result["checks"]["pilot_activated"])
        self.assertEqual(self.runtime.writes, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
