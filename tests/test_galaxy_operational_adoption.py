"""Bounded operational GALAXY default-on adoption and safeguard tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import galaxy_frontdoor_context as lane


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
            "relations": [],
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

    def test_source_preserves_all_six_elanes_and_owner_authority(self):
        app = (ROOT / "api" / "gaiaos_app.py").read_text(encoding="utf-8")
        host = (ROOT / "api" / "host_memory_gateway.py").read_text(encoding="utf-8")
        self.assertIn("//PW:PRESERVE//", app)
        self.assertIn("GALAXY_FRONTDOOR_KILL_SWITCH", app)
        self.assertIn("include_memory: bool = True", app.split("def gaia(", 1)[1])
        self.assertIn("def _host_memsav(", host)
        self.assertIn("approved", host)
        profiles = (ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS" / "OPERATOR-PROFILES.v1.json").read_text(encoding="utf-8")
        for member in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
            self.assertIn(member, profiles)

    def test_live_review_is_browser_authenticated_and_read_only(self):
        source = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        route = source.split('def galaxy_operational_review(', 1)[1].split('@app.post("/verify"', 1)[0]
        self.assertIn("_authorize_browser_session", route)
        self.assertIn("_snapshot(memcon_runtime)", route)
        self.assertIn("include_memory=False", route)
        self.assertIn("negative_control_no_fabrication", route)
        self.assertIn("counts_unchanged_no_writes", route)
        for invalid in ("write_record(", "galaxy_production.activate(", "galaxy_calculate_gravity("):
            self.assertNotIn(invalid, route)


if __name__ == "__main__":
    unittest.main(verbosity=2)
