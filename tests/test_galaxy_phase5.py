"""Offline safety tests for GALAXY Phase 5 provenance-backed synthesis review."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_phase5 as p5


class FakeRuntime:
    def __init__(self):
        a, b = p5.FIXTURE_SOURCE_IDS
        self.records = {
            a: {
                "record_id": a,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Later calibration observation revises the core.",
            },
            b: {
                "record_id": b,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Original calibration core observation.",
            },
            "CROSS": {
                "record_id": "CROSS",
                "scope": "OtherScope",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Other-scope record.",
            },
            "ISOLATED": {
                "record_id": "ISOLATED",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Unrelated isolated record.",
            },
            "SYNTH": {
                "record_id": "SYNTH",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "SYNTHESIS",
                "statement": "Existing synthesis.",
            },
        }
        self.edges = {
            "EDGE-REVISES": {
                "edge_id": "EDGE-REVISES",
                "source_record_id": a,
                "target_record_id": b,
                "relation_type": "REVISES",
                "strength": 0.9,
                "status": "VERIFIED",
                "authority": "NAOMI",
                "created_at": "2026-09-20T00:00:00+00:00",
                "verified_at": "2026-09-20T00:01:00+00:00",
            },
            "EDGE-OLD-SUPERSEDES": {
                "edge_id": "EDGE-OLD-SUPERSEDES",
                "source_record_id": a,
                "target_record_id": b,
                "relation_type": "SUPERSEDES",
                "strength": 1.0,
                "status": "REVOKED",
                "authority": "NAOMI",
                "created_at": "2026-09-23T00:00:00+00:00",
                "verified_at": "2026-09-23T00:01:00+00:00",
            },
        }
        self.writes = 0

    def galaxy_record(self, record_id):
        record = self.records.get(record_id)
        if not record:
            return None
        relations = [
            dict(edge) for edge in self.edges.values()
            if edge["source_record_id"] == record_id
            or edge["target_record_id"] == record_id
        ]
        return {"record": dict(record), "relations": relations}

    def galaxy_governing_state(self, record_id):
        record = self.records[record_id]
        incoming = [
            edge for edge in self.edges.values()
            if edge["target_record_id"] == record_id
            and edge["status"] == "VERIFIED"
            and edge["relation_type"] in {"REVISES", "SUPERSEDES"}
        ]
        supersedes = [e for e in incoming if e["relation_type"] == "SUPERSEDES"]
        revises = [e for e in incoming if e["relation_type"] == "REVISES"]
        if supersedes:
            state = "HISTORICAL_SUPERSEDED"
            eligible = False
        elif revises:
            state = "CURRENT_REVISED_CONTEXT"
            eligible = True
        else:
            state = "CURRENT"
            eligible = True
        return {
            "record_id": record_id,
            "state": state,
            "record_status": record["status"],
            "current_default_eligible": eligible,
            "historical_retrieval_eligible": True,
        }


class Phase5Tests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_fixture_review_passes_read_only(self):
        result = p5.fixture_review(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_PHASE5_FIXTURE_REVIEW", result)
        self.assertTrue(result["checks"]["verified_relation_visible"])
        self.assertFalse(
            result["cluster_review"]["synthesis_candidate"]["synthesis_statement_generated"]
        )
        self.assertEqual(self.runtime.writes, 0)

    def test_duplicate_source_holds(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, a])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("DUPLICATE_SOURCE_RECORD_ID", result["hold_reasons"])

    def test_cross_scope_holds(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, "CROSS"])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "CROSS_SCOPE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE",
            result["hold_reasons"],
        )

    def test_unrelated_cluster_holds_without_verified_relation(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, "ISOLATED"])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("NO_VERIFIED_INTERNAL_RELATION", result["hold_reasons"])

    def test_verified_contradiction_holds(self):
        a, b = p5.FIXTURE_SOURCE_IDS
        self.runtime.edges["EDGE-CONTRADICTS"] = {
            "edge_id": "EDGE-CONTRADICTS",
            "source_record_id": a,
            "target_record_id": b,
            "relation_type": "CONTRADICTS",
            "strength": 0.8,
            "status": "VERIFIED",
            "authority": "NAOMI",
            "created_at": "2026-09-23T00:02:00+00:00",
            "verified_at": "2026-09-23T00:03:00+00:00",
        }
        result = p5.review_cluster(self.runtime, [a, b])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "UNRESOLVED_VERIFIED_CONTRADICTION_IN_CLUSTER",
            result["hold_reasons"],
        )

    def test_recursive_synthesis_holds_initial_slice(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        self.runtime.edges["EDGE-SYNTH"] = {
            "edge_id": "EDGE-SYNTH",
            "source_record_id": "SYNTH",
            "target_record_id": a,
            "relation_type": "DERIVED_FROM",
            "strength": 1.0,
            "status": "VERIFIED",
            "authority": "NAOMI",
            "created_at": "2026-09-23T00:04:00+00:00",
            "verified_at": "2026-09-23T00:05:00+00:00",
        }
        result = p5.review_cluster(self.runtime, ["SYNTH", a])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "RECURSIVE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE",
            result["hold_reasons"],
        )

    def test_carrier_packages_phase5_module(self):
        root = Path(__file__).resolve().parents[1]
        dockerfile = (root / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY api/galaxy_phase5.py ./galaxy_phase5.py", dockerfile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
