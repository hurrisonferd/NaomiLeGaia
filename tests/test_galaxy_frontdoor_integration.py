"""Source + behavioral tests for the first opt-in GALAXY front-door memory lane."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import galaxy_frontdoor_context as lane


class ControlledMemoryRuntime:
    _INITIALIZED = True

    def __init__(self):
        self.calls = []
        self.record = {
            "record_id": "MEM-INTEGRATION-FIXTURE",
            "authority": "NAOMI",
            "record_type": "TEST",
            "scope": "MemoryOS",
            "statement": "GALAXY calibration evidence",
            "source": "integration-source",
            "status": "ACTIVE",
            "version": "1",
        }

    def search_records(self, query, limit, scope):
        self.calls.append(("search_records", query, limit, scope))
        return {
            "scope_applied": scope,
            "query_filter_active": bool(query.split()),
            "records": [dict(self.record)] if "calibration" in query else [],
        }

    def galaxy_record(self, record_id):
        self.calls.append(("galaxy_record", record_id))
        return {
            "record": dict(self.record),
            "relations": [{"edge_id": "EDGE-1", "relation_type": "REVISES", "status": "VERIFIED"}],
            "lifecycle": {"state": "ACTIVE"},
        }

    def galaxy_governing_state(self, record_id):
        self.calls.append(("galaxy_governing_state", record_id))
        return {"record_id": record_id, "state": "CURRENT_REVISED_CONTEXT", "current_default_eligible": True}

    def write_record(self, *args, **kwargs):
        raise AssertionError("front door may not write")


class GalaxyFrontdoorReadTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ControlledMemoryRuntime()

    def test_opt_in_exact_provenance_and_governance(self):
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "PASS_SHADOW_LEGACY_READ", result)
        self.assertEqual(result["count"], 1)
        evidence = result["records"][0]
        self.assertEqual(evidence["record"]["record_id"], "MEM-INTEGRATION-FIXTURE")
        self.assertEqual(evidence["source_provenance"], "integration-source")
        self.assertEqual(evidence["governing_state"]["state"], "CURRENT_REVISED_CONTEXT")
        self.assertEqual(evidence["lifecycle"]["state"], "ACTIVE")
        self.assertEqual(evidence["relations"][0]["relation_type"], "REVISES")
        self.assertEqual(result["ranking"], "LEGACY_UNWEIGHTED_CONTROL")
        self.assertFalse(result["galaxy_weighting_applied"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertEqual(result["writes_performed"], [])
        self.assertEqual(self.runtime.calls[0], ("search_records", "calibration", 2, "MemoryOS"))

    def test_no_match_is_explicit_not_an_empty_success(self):
        result = lane.preview(self.runtime, "notfound", 2)
        self.assertEqual(result["status"], "HOLD_NO_MATCH")
        self.assertEqual(result["records"], [])

    def test_refuses_empty_query_and_invalid_limits_without_read(self):
        for q, n in (("", 1), (" ", 1), ("test", 0), ("test", 7), ("test", True)):
            result = lane.preview(self.runtime, q, n)
            self.assertTrue(result["status"].startswith("HOLD"))
        self.assertEqual(self.runtime.calls, [])

    def test_runtime_not_initialized_never_touches_database(self):
        self.runtime._INITIALIZED = False
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_RUNTIME_NOT_INITIALIZED")
        self.assertEqual(self.runtime.calls, [])

    def test_scope_mismatch_fails_closed(self):
        base = self.runtime.search_records
        self.runtime.search_records = lambda q,n,s: {**base(q,n,s), "scope_applied": "OtherMember"}
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_SOURCE_FILTER_UNVERIFIED")
        self.assertEqual(result["records"], [])

    def test_unfiltered_broad_search_refused(self):
        base = self.runtime.search_records
        self.runtime.search_records = lambda q,n,s: {**base(q,n,s), "query_filter_active": False}
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_SOURCE_FILTER_UNVERIFIED")

    def test_cross_member_record_refused(self):
        self.runtime.record["scope"] = "SELENE_E_LANE"
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_SOURCE_INVALID")
        self.assertEqual(result["records"], [])

    def test_unverified_governing_state_refused(self):
        self.runtime.galaxy_governing_state = lambda rid: {"record_id": rid, "state": "UNKNOWN"}
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_GOVERNING_STATE_UNVERIFIED")
        self.assertEqual(result["records"], [])

    def test_read_failure_returns_no_partial_memory(self):
        self.runtime.galaxy_record = lambda rid: (_ for _ in ()).throw(RuntimeError("read error"))
        result = lane.preview(self.runtime, "calibration", 2)
        self.assertEqual(result["status"], "HOLD_SOURCE_UNAVAILABLE")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["error_type"], "RuntimeError")

    def test_frontdoor_source_is_heatedeath_default_with_one_gateway(self):
        source = (ROOT / "api" / "gaiaos_app.py").read_text(encoding="utf-8")
        snippet = source.split("def _frontdoor_packet(", 1)[1].split("def _selftest_packet(", 1)[0]
        self.assertIn("include_memory: bool | None = None", snippet)
        self.assertIn("memory_query: str | None = None", snippet)
        self.assertIn("gaiaos_memory_mode.mode_status(", snippet)
        self.assertIn("gaiaos_memory_gateway.read(", snippet)
        self.assertIn('**({"memory_context": memory_context} if should_read_memory else {})', snippet)
        self.assertNotIn("galaxy_frontdoor_context.preview(", snippet)
        self.assertNotIn("write_record(", snippet)
        self.assertNotIn("activate(", snippet)
        self.assertNotIn("delete(", snippet)
        self.assertNotIn("galaxy_production.retrieve(", snippet)
        self.assertIn("    include_memory: bool | None = None", source.split("class GaiaAssistRequest", 1)[1])

    def test_one_tap_browser_review_is_authenticated_get_only(self):
        source = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        start = '@app.get("/galaxy/integration/frontdoor-readonly-review"'
        end = '@app.post("/verify"'
        self.assertIn(start, source)
        segment = source.split(start, 1)[1].split(end, 1)[0]
        self.assertIn("_bootstrap_browser_session_redirect(browser_request)", segment)
        self.assertIn("gaiaos_api._authorize_browser_session(browser_request)", segment)
        self.assertIn("galaxy_phase7_isolated_restore._snapshot(memcon_runtime)", segment)
        self.assertIn("include_memory=True", segment)
        self.assertIn('memory_query="GALAXY-CAL-CORE"', segment)
        self.assertIn("default_frontdoor_memory_absent", segment)
        self.assertIn("runtime_counts_after", segment)
        self.assertNotIn("@app.post(", segment)
        self.assertNotIn("@app.delete(", segment)
        self.assertNotIn("memcon_runtime.write_record(", segment)
        self.assertNotIn("galaxy_production.activate(", segment)

    def test_runtime_module_has_no_effectful_sql_or_hidden_broad_fallback(self):
        source = (ROOT / "api" / "galaxy_frontdoor_context.py").read_text(encoding="utf-8")
        for prohibited in (
            "INSERT INTO", "UPDATE memory_", "DELETE FROM", "runtime._db(",
            "runtime.initialize(", "runtime.write_record(", "galaxy_production.activate(",
        ):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
