"""Offline safety tests for Phase 3F using a deterministic fake MemoryOS runtime."""
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_production as gp


class FakeRuntime:
    BOOT_ID = "TEST-BOOT-1"
    SCHEMA_VERSION = "test.memoryos.v1"
    GALAXY_PHASE3C_CALIBRATION_QUERIES = (
        "gravity contextual influence memory retrieval",
        "history current context revision memory",
        "authority permission memory retrieval",
        "calibration core revision memory context",
        "provenance contradiction memory context",
        "satellite calibration core memory context",
    )

    def __init__(self):
        self.break_guard = False
        self.fail_record = False
        self.writes = 0

    @staticmethod
    def _galaxy_query_tokens(query):
        return query.lower().split()

    def _ids(self, query):
        index = self.GALAXY_PHASE3C_CALIBRATION_QUERIES.index(query)
        return [f"MEM-FAKE-{index}-A", f"MEM-FAKE-{index}-B", f"MEM-FAKE-{index}-C"]

    def search_records(self, query, limit=10, scope=None):
        try:
            ids = self._ids(query)
        except ValueError:
            ids = ["MEM-LEGACY-OTHER"]
        return {
            "records": [{"record_id": value, "scope": scope, "statement": value}
                        for value in ids[:limit]],
            "count": min(len(ids), limit),
            "runtime": self.SCHEMA_VERSION,
            "query_terms_applied": query.lower().split(),
            "scope_applied": scope,
            "query_filter_active": bool(query.strip()),
        }

    def galaxy_phase3_candidate_pool(self, query, *, scope="MemoryOS", limit=10):
        ids = self._ids(query)
        coverages = (1.0, 0.6, 0.6)
        return {
            "candidate_record_ids": ids,
            "candidate_count": len(ids),
            "candidates": [
                {"record_id": key, "relevance": {"coverage": rel}}
                for key, rel in zip(ids, coverages)
            ],
        }

    def _galaxy_phase3c_score_pool(self, pool, relevance_weight, gravity_weight):
        rows = []
        for index, item in enumerate(pool["candidates"]):
            gravity = (0.0, 0.0, 1.0)[index]
            relevance = item["relevance"]["coverage"]
            rows.append({
                "record_id": item["record_id"],
                "control_rank": index + 1,
                "query_relevance_coverage": relevance,
                "gravity_score": gravity,
                "weighted_score": round(relevance_weight * relevance + gravity_weight * gravity, 6),
            })
        rows.sort(key=lambda item: (-item["weighted_score"], item["control_rank"]))
        for index, item in enumerate(rows):
            item["weighted_rank"] = index + 1
        return {
            "weighted_order": rows,
            "candidate_set_preserved": True,
            "top_relevance_preserved": True,
            "cross_relevance_tier_inversion_count": int(self.break_guard),
            "rerank_observed": [r["record_id"] for r in rows] != pool["candidate_record_ids"],
        }

    def get_record(self, record_id):
        if self.fail_record:
            return None
        return {"record_id": record_id, "scope": "MemoryOS", "statement": record_id}


class Phase3FTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("GALAXY_PRODUCTION_PILOT_KILL_SWITCH", None)
        self.runtime = FakeRuntime()
        with gp._LOCK:
            gp._disable_locked("TEST_RESET")
            gp._STATE["last_test"] = None
            gp._STATE["last_rollback"] = None

    def tearDown(self):
        os.environ.pop("GALAXY_PRODUCTION_PILOT_KILL_SWITCH", None)
        gp.rollback(self.runtime, reason="UNIT_TEST_CLEANUP")

    def retrieve(self, query, scope="MemoryOS", limit=10):
        return {"retrieval": gp.retrieve(self.runtime, query, scope, limit),
                "context_authority": "NONE",
                "retrieval_is_not_identity_adoption": True}

    def test_default_off_and_legacy_unchanged(self):
        q = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[0]
        result = self.retrieve(q)
        self.assertEqual(result["retrieval"]["records"][0]["record_id"], "MEM-FAKE-0-A")
        self.assertFalse(result["retrieval"]["galaxy_production"]["weighted_applied"])
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")

    def test_cannot_activate_without_fresh_switch_test(self):
        result = gp.activate(self.runtime, authority="NAOMI", approved=True)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")

    def test_switch_test_exercises_integrated_path_and_restores(self):
        result = gp.switch_test(self.runtime, self.retrieve)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(len(result["during_weighted"]), 3)
        self.assertTrue(result["unweighted_control_restored_exactly"])
        self.assertEqual(result["mode_after"], "OFF")
        self.assertEqual(self.runtime.writes, 0)

    def test_activation_scoped_and_live_active_rollback(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        q = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[0]
        on = self.retrieve(q)["retrieval"]
        self.assertTrue(on["galaxy_production"]["weighted_applied"])
        self.assertEqual([r["record_id"] for r in on["records"]],
                         ["MEM-FAKE-0-A", "MEM-FAKE-0-C", "MEM-FAKE-0-B"])
        for outside_query, outside_scope, outside_limit in (
            (self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[1], "MemoryOS", 10),
            (q, "OtherScope", 10),
            (q, "MemoryOS", 11),
        ):
            outside = self.retrieve(outside_query, outside_scope, outside_limit)
            self.assertFalse(outside["retrieval"]["galaxy_production"]["weighted_applied"])
        rollback = gp.live_rollback_proof(self.runtime, self.retrieve)
        self.assertEqual(rollback["status"], "PASS", rollback)
        self.assertTrue(rollback["exact_legacy_restoration"])
        self.assertEqual(rollback["mode_after"], "OFF")
        self.assertEqual(self.runtime.writes, 0)

    def test_bad_relevance_guard_auto_fails_closed(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        self.runtime.break_guard = True
        q = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[0]
        result = self.retrieve(q)["retrieval"]
        self.assertFalse(result["galaxy_production"]["weighted_applied"])
        self.assertEqual(result["galaxy_production"]["reason"], "AUTO_FAIL_CLOSED")
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")

    def test_missing_record_auto_fails_closed(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        self.runtime.fail_record = True
        q = self.runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[3]
        result = self.retrieve(q)["retrieval"]
        self.assertFalse(result["galaxy_production"]["weighted_applied"])
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")

    def test_kill_switch_and_lease_expiry_fail_closed(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        os.environ["GALAXY_PRODUCTION_PILOT_KILL_SWITCH"] = "1"
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")
        os.environ.pop("GALAXY_PRODUCTION_PILOT_KILL_SWITCH")
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        with gp._LOCK:
            gp._STATE["expires_at_monotonic"] = time.monotonic() - 1
        self.assertEqual(gp.status(self.runtime)["mode"], "OFF")

    def test_reactivation_requires_fresh_test_after_rollback(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "PILOT_ACTIVE")
        self.assertEqual(gp.rollback(self.runtime)["status"], "ROLLED_BACK")
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "HOLD")

    def test_denied_authority_and_test_expiration(self):
        self.assertEqual(gp.switch_test(self.runtime, self.retrieve)["status"], "PASS")
        self.assertEqual(gp.activate(self.runtime, authority="OTHER", approved=True)["status"], "HOLD")
        with gp._LOCK:
            gp._STATE["last_test"]["completed_monotonic"] = time.monotonic() - gp.TEST_VALID_SECONDS - 1
        self.assertEqual(gp.activate(self.runtime, authority="NAOMI", approved=True)["status"], "HOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
