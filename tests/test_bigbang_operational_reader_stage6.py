"""Stage 6 source-only, release-locked GALAXY operational reader tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import galaxy_frontdoor_context as lane
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode


class FakeMemory:
    _INITIALIZED = True

    def __init__(self):
        self.records = {
            "CURRENT": {
                "record_id": "CURRENT", "scope": "MemoryOS",
                "status": "ACTIVE", "statement": "gravity contextual influence memory retrieval",
                "authority": "NAOMI", "source": "proof:current",
            },
            "HISTORY": {
                "record_id": "HISTORY", "scope": "MemoryOS",
                "status": "ACTIVE", "statement": "history context revision memory",
                "authority": "NAOMI", "source": "proof:history",
            },
            "LINKED": {
                "record_id": "LINKED", "scope": "MemoryOS",
                "status": "ACTIVE", "statement": "linked context memory",
                "authority": "NAOMI", "source": "proof:linked",
            },
        }
        self.reads = []

    def search_records(self, query, limit, scope):
        words = [word.lower() for word in query.split()]
        records = [
            dict(record) for record in self.records.values()
            if (scope is None or record["scope"] == scope)
            and all(word in record["statement"].lower() for word in words)
        ][:max(1, min(int(limit), 100))]
        self.reads.append(("search_records", query, limit, scope))
        return {
            "records": records, "count": len(records),
            "runtime": "isolated-stage6-fake-runtime",
            "query_terms_applied": words, "scope_applied": scope,
            "query_filter_active": bool(words),
        }

    def galaxy_record(self, record_id):
        self.reads.append(("galaxy_record", record_id))
        if record_id not in self.records:
            return None
        return {
            "record": dict(self.records[record_id]),
            "gravity": {
                "gravity_score": 0.75 if record_id == "CURRENT" else 0.4,
            },
            "lifecycle": {"state": "ACTIVE"},
            "relations": [{
                "edge_id": "EDGE-VERIFIED",
                "source_record_id": "LINKED",
                "target_record_id": "CURRENT",
                "status": "VERIFIED" if getattr(self, "link_verified", True)
                          else "REVOKED",
            }] if record_id == "LINKED" else [],
            "importance": {"gate_units": 4750},
        }

    def galaxy_governing_state(self, record_id):
        self.reads.append(("galaxy_governing_state", record_id))
        return {
            "record_id": record_id,
            "state": "HISTORICAL_SUPERSEDED" if record_id == "HISTORY" else "CURRENT",
            "current_default_eligible": record_id != "HISTORY",
        }

    def write_record(self, *args, **kwargs):
        raise AssertionError("GALAXY retrieval must never write")
    def galaxy_calculate_gravity(self, *args, **kwargs):
        raise AssertionError("GALAXY retrieval must never write")


def candidate_pool(*args, **kwargs):
    return {
        "status": "PASS",
        "candidates": [
            {"record_id": "CURRENT", "statement": "gravity contextual influence memory retrieval",
             "relevance": {"coverage": 1.0, "matched_concepts": ["gravity", "memory"]}},
            {"record_id": "HISTORY", "statement": "history context revision memory",
             "relevance": {"coverage": 0.67, "matched_concepts": ["memory", "context"]}},
        ],
        "linked_context_candidates": [
            {"record_id": "LINKED", "verified_direct_primary_edges": [
                {"edge_id": "EDGE-VERIFIED", "source_record_id": "LINKED",
                 "target_record_id": "CURRENT"}]},
        ],
        "checks": {
            "all_admitted_candidates_meet_primary_rule": True,
            "linked_context_requires_verified_direct_primary_edge": True,
        },
    }


class GALAXYOperationalTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeMemory()
        self.patch = patch("galaxy_phase3_exit.build_candidate_pool", side_effect=candidate_pool)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_current_evidence_ranked_history_kept_and_links_separate(self):
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval", limit=4)
        self.assertEqual(out["status"], "PASS_GALAXY_OPERATIONAL_RETRIEVAL", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["records"][0]["record"]["record_id"], "CURRENT")
        self.assertEqual(out["records"][0]["source_provenance"], "proof:current")
        self.assertEqual(out["records"][0]["importance"]["gate_units"], 4750)
        self.assertEqual(out["records"][0]["ranking"]["relevance_weight"], 0.8)
        self.assertEqual(out["records"][0]["ranking"]["gravity_weight"], 0.2)
        self.assertEqual(out["historical_context"][0]["record"]["record_id"], "HISTORY")
        self.assertEqual(out["verified_linked_context"][0]["record"]["record_id"], "LINKED")
        self.assertTrue(out["verified_linked_context"][0]["context_only"])
        self.assertFalse(out["automatic_capture"])
        self.assertFalse(out["automatic_promotion"])
        self.assertFalse(out["e_lanes_modified"])
        self.assertFalse(out["physical_delete"])
        self.assertEqual(out["writes_performed"], [])

    def test_uninitialized_hold_before_data_access(self):
        self.rt._INITIALIZED = False
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_RUNTIME_NOT_INITIALIZED")
        self.assertEqual(self.rt.reads, [])

    def test_phase3_candidate_hold_does_not_fabricate(self):
        with patch("galaxy_phase3_exit.build_candidate_pool", return_value={
            "status": "HOLD", "reason": "NO_PRIMARY_CANDIDATE"
        }):
            out = lane.operational(self.rt, "unrelated information")
        self.assertEqual(out["status"], "HOLD_NO_CONFIDENT_GALAXY_MATCH")
        self.assertEqual(out["records"], [])
        self.assertTrue(out["no_broad_fallback"])

    def test_changed_source_statement_fails_closed(self):
        self.rt.records["CURRENT"]["statement"] = "changed after candidate admission"
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_STATEMENT_CHANGED")
        self.assertEqual(out["records"], [])

    def test_wrong_record_scope_fails_closed(self):
        self.rt.records["CURRENT"]["scope"] = "VERA_E_LANE"
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_SCOPE_OR_ID_CHANGED")
        self.assertEqual(out["records"], [])

    def test_read_failure_fails_closed(self):
        self.rt.galaxy_record = lambda rid: (_ for _ in ()).throw(RuntimeError("source offline"))
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_GALAXY_UNAVAILABLE")
        self.assertEqual(out["records"], [])
        self.assertEqual(out["error_type"], "RuntimeError")


    def test_legacy_gateway_is_unmodified_until_explicit_mock_bigbang(self):
        query = "gravity contextual influence memory retrieval"
        legacy_native = self.rt.search_records(query, 4, "MemoryOS")
        self.rt.reads.clear()
        emergency = gateway.read(self.rt, query, "MemoryOS", 4)
        self.assertEqual(emergency["status"], "PASS_HEATDEATH")
        self.assertEqual(emergency["retrieval"], legacy_native)
        self.assertIsNone(emergency["galaxy_context"])
        self.assertFalse(emergency["galaxy_applied"])
        self.assertFalse(emergency["fallback_occurred"])
        authorized_test_only = {
            "schema": mode.SCHEMA, "effective_mode": "BIGBANG",
            "configured_mode": "BIGBANG", "bigbang_activation_enabled": True,
            "reason": "TEST_ONLY_MOCKED_RELEASE_GATE",
        }
        with patch.object(mode, "mode_status", return_value=authorized_test_only):
            bigbang = gateway.read(self.rt, query, "MemoryOS", 4)
        self.assertEqual(bigbang["status"], "PASS_BIGBANG", bigbang)
        self.assertTrue(bigbang["galaxy_applied"])
        self.assertEqual(bigbang["retrieval"], legacy_native)
        self.assertEqual(bigbang["galaxy_context"]["records"][0]["record"]["record_id"],
                         "CURRENT")
        self.assertEqual(bigbang["galaxy_context"]["verified_linked_context"][0]
                         ["record"]["record_id"], "LINKED")
        self.assertEqual(bigbang["writes_performed"], [])
        self.assertFalse(bigbang["e_lanes_modified"])

    def test_live_edge_revoked_between_admission_and_read_holds(self):
        self.rt.link_verified = False
        out = lane.operational(self.rt, "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_LINKED_EDGE_CHANGED", out)
        self.assertEqual(out["records"], [])

    def test_linked_edge_must_target_current_primary_not_historical(self):
        unsafe = candidate_pool()
        unsafe["linked_context_candidates"][0]["verified_direct_primary_edges"] = [{
            "edge_id": "EDGE-FALSE",
            "source_record_id": "LINKED",
            "target_record_id": "HISTORY",
        }]
        with patch("galaxy_phase3_exit.build_candidate_pool",
                   return_value=unsafe):
            out = lane.operational(self.rt,
                                   "gravity contextual influence memory retrieval")
        self.assertEqual(out["status"], "HOLD_LINKED_EDGE_INVALID")
        self.assertEqual(out["records"], [])

    def test_new_galaxy_reader_cannot_override_owner_and_elanes(self):
        src = (ROOT / "api" / "galaxy_frontdoor_context.py").read_text()
        gateway_source = (ROOT / "api" / "gaiaos_memory_gateway.py").read_text()
        mode_source = (ROOT / "api" / "gaiaos_memory_mode.py").read_text()
        self.assertIn("def preview(", src)
        self.assertIn("def operational(", src)
        self.assertIn("BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED", mode_source)
        self.assertIn("importlib.import_module(\"galaxy_frontdoor_context\")",
                      gateway_source)
        self.assertNotIn("runtime.write_record(", src)
        self.assertNotIn("runtime.galaxy_calculate_gravity(", src)
        self.assertNotIn("runtime.initialize(", src)
        profiles = (ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS"
                    / "OPERATOR-PROFILES.v1.json").read_text()
        for name in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
            self.assertIn(name, profiles)
            self.assertTrue((
                ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS"
                / "IDENTITY-DATA" / (name+"-EXPERIENCES.v1.md")
            ).is_file())

    def test_gateway_rejects_unverified_live_edge_without_memory_fabrication(self):
        self.rt.link_verified = False
        condition = {
            "schema": mode.SCHEMA, "effective_mode": "BIGBANG",
            "configured_mode": "BIGBANG", "bigbang_activation_enabled": True,
        }
        with patch.object(mode, "mode_status", return_value=condition):
            out = gateway.read(self.rt, "gravity contextual influence memory retrieval",
                               "MemoryOS", 4)
        self.assertEqual(out["status"], "PASS_HEATDEATH_FALLBACK", out)
        self.assertTrue(out["fallback_occurred"])
        self.assertFalse(out["galaxy_applied"])
        self.assertEqual(out["retrieval"]["records"][0]["record_id"], "CURRENT")
        self.assertIsNone(out["galaxy_context"])
        self.assertTrue(out["manual_emergency_latch_required"])




if __name__ == "__main__":
    unittest.main(verbosity=2)
