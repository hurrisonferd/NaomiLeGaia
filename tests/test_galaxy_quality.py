"""Phase 3G read-only audit tests. Fake storage prevents writes and external calls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_quality as quality


class FakeMemory:
    GALAXY_PHASE3C_CALIBRATION_QUERIES = (
        "gravity contextual influence memory retrieval", "other",
        "other", "calibration core revision memory context", "other",
        "satellite calibration core memory context",
    )
    GALAXY_QUERY_STOPWORDS = set()
    GALAXY_QUERY_CONCEPT_ALIASES = {"contextual": "context", "memories": "memory"}

    def __init__(self):
        self.writes = 0
        self.records = [
            {
                "record_id": "GENERIC", "scope": "MemoryOS",
                "statement": "GALAXY gravity never grants authority.",
                "notes": "calibration revision context",
                "source": "PROTOCOL", "status": "ACTIVE", "created_at": "t1",
                "coverage": 0.8,
            },
            {
                "record_id": "CORE", "scope": "MemoryOS",
                "statement": "The calibration core reports a violet carrier pulse.",
                "notes": "", "source": "OBSERVED", "status": "ACTIVE",
                "created_at": "t2", "coverage": 0.6,
            },
            {
                "record_id": "REV", "scope": "MemoryOS",
                "statement": "An observation revises the calibration core.",
                "notes": "revision", "source": "OBSERVED", "status": "ACTIVE",
                "created_at": "t3", "coverage": 0.8,
            },
        ]

    @staticmethod
    def _galaxy_query_tokens(s):
        import re
        return re.findall(r"[a-z0-9]+", str(s).lower())

    def _galaxy_query_concept(self, token):
        return self.GALAXY_QUERY_CONCEPT_ALIASES.get(token, token)

    def galaxy_phase3_candidate_pool(self, query, *, scope="MemoryOS", limit=10):
        rows = self.records[:limit]
        return {
            "scope_eligible_population_count": len(self.records),
            "candidate_record_ids": [r["record_id"] for r in rows],
            "candidates": [
                {"record_id": r["record_id"],
                 "relevance": {
                     "coverage": r["coverage"],
                     "matched_terms": []}}
                for r in rows
            ],
            "ambiguous_record_ids": [],
        }

    def _galaxy_phase3c_score_pool(self, pool, relevance_weight, gravity_weight):
        rows = [
            {"record_id": row["record_id"], "gravity_score": 0.0,
             "weighted_rank": i + 1, "weighted_score": row["relevance"]["coverage"] * 0.8}
            for i, row in enumerate(pool["candidates"])
        ]
        return {"weighted_order": rows, "candidate_set_preserved": True,
                "top_relevance_preserved": True,
                "cross_relevance_tier_inversion_count": 0}

    def search_records(self, query, limit=10, scope=None):
        return {"records": [], "count": 0}

    def galaxy_record(self, record_id):
        row = next((r for r in self.records if r["record_id"] == record_id), None)
        if row is None:
            return None
        relations = (
            [{"edge_id": "EDGE-1", "source_record_id": "REV",
              "target_record_id": "CORE", "relation_type": "REVISES",
              "status": "VERIFIED"}]
            if record_id in ("CORE", "REV") else
            [{"edge_id": "EDGE-NO", "source_record_id": "GENERIC",
              "target_record_id": "CORE", "relation_type": "ASSOCIATED_WITH",
              "status": "PROPOSED"}]
        )
        return {"record": row, "relations": relations}

    def galaxy_governing_state(self, record_id):
        return {"current_default_eligible": True, "state": "CURRENT"}


class QualityReviewTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeMemory()

    def test_metadata_match_is_separate_from_statement_and_scope(self):
        result = quality.review(self.runtime, query_index=3)
        self.assertEqual(result["status"], "OBSERVED_READ_ONLY")
        self.assertEqual(result["topic_anchored_candidate_ids"], ["CORE", "REV"])
        self.assertEqual(result["indirect_or_policy_context_ids"], ["GENERIC"])
        generic = result["records"][0]
        origins = {row["query_term"]: row for row in generic["match_origin"]}
        self.assertFalse(origins["calibration"]["statement"])
        self.assertTrue(origins["calibration"]["notes"])
        self.assertTrue(origins["memory"]["scope_virtual_memory"])
        self.assertFalse(origins["core"]["statement"])
        self.assertEqual(generic["verified_relations"], [])
        self.assertEqual(self.runtime.writes, 0)

    def test_core_not_dropped_by_coverage_shortcut(self):
        result = quality.review(self.runtime, query_index=3)
        core = next(x for x in result["records"] if x["record_id"] == "CORE")
        self.assertEqual(core["query_relevance_coverage"], 0.6)
        self.assertTrue(core["statement_anchor_present"])
        self.assertEqual(core["verified_in_pool_relation_count"], 1)
        self.assertEqual(result["checks"]["cross_relevance_tier_inversions"], 0)
        self.assertFalse(result["provisional_containment_experiment"]["promotion_implemented"])

    def test_missing_record_forces_hold_and_no_write(self):
        self.runtime.galaxy_record = lambda rid: None if rid == "CORE" else FakeMemory.galaxy_record(self.runtime, rid)
        result = quality.review(self.runtime, query_index=3)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["missing_record_ids"], ["CORE"])
        self.assertEqual(self.runtime.writes, 0)

    def test_reject_unapproved_queries_and_large_scans(self):
        with self.assertRaises(ValueError):
            quality.review(self.runtime, query_index=2)
        with self.assertRaises(ValueError):
            quality.review(self.runtime, query_index=3, limit=100)
        self.assertEqual(self.runtime.writes, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
