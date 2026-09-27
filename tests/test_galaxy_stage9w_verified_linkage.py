"""Stage 9W: link provenance must survive real operational -> gateway boundaries.

All test records, graph edges and release permissions are synthetic. This suite
never reads/writes production Turso, calls a hosted model, promotes memories
or merges the six independent Prime Daemon E-LANES.
"""
from __future__ import annotations

from copy import deepcopy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import galaxy_frontdoor_context as operational
import galaxy_phase3_exit
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode

from test_bigbang_operational_reader_stage6 import FakeMemory, candidate_pool

QUERY = "gravity contextual influence memory retrieval"
AUTH = {
    "schema": mode.SCHEMA, "effective_mode": mode.BIGBANG,
    "configured_mode": mode.BIGBANG, "bigbang_activation_enabled": True,
    "reason": "TEST_ONLY_NEVER_ACTUAL_RELEASE",
}


class Stage9WVerifiedLinkageTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeMemory()

    def operational(self, pool=None):
        with patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            return_value=deepcopy(pool) if pool is not None else candidate_pool(),
        ):
            return operational.operational(self.rt, QUERY, limit=4)

    def test_positive_exact_live_link_has_explicit_verified_status(self):
        out = self.operational()
        self.assertEqual(out["status"], "PASS_GALAXY_OPERATIONAL_RETRIEVAL", out)
        links = out["verified_linked_context"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["record"]["record_id"], "LINKED")
        self.assertTrue(links[0]["context_only"])
        self.assertEqual(links[0]["verified_direct_primary_edges"], [{
            "edge_id": "EDGE-VERIFIED",
            "source_record_id": "LINKED",
            "target_record_id": "CURRENT",
            "status": "VERIFIED",
        }])
        self.assertTrue(gateway._galaxy_valid(out, 4))
        self.assertEqual(out["writes_performed"], [])
        self.assertFalse(out["e_lanes_modified"])

    def test_untrusted_pool_extra_revoked_unrelated_edges_never_emitted(self):
        pool = deepcopy(candidate_pool())
        edges = pool["linked_context_candidates"][0]["verified_direct_primary_edges"]
        edges.extend((
            {"edge_id": "FORGED-REVOKED", "status": "REVOKED",
             "source_record_id": "LINKED", "target_record_id": "CURRENT",
             "untrusted_notes": "DO NOT FORWARD TO USER"},
            {"edge_id": "UNRELATED", "status": "VERIFIED",
             "source_record_id": "OTHER", "target_record_id": "CURRENT"},
        ))
        out = self.operational(pool)
        self.assertEqual(out["status"], "PASS_GALAXY_OPERATIONAL_RETRIEVAL", out)
        published = out["verified_linked_context"][0]["verified_direct_primary_edges"]
        self.assertEqual(len(published), 1)
        self.assertEqual(published[0]["edge_id"], "EDGE-VERIFIED")
        self.assertEqual(published[0]["status"], "VERIFIED")
        self.assertNotIn("DO NOT FORWARD TO USER", str(out))
        self.assertTrue(gateway._galaxy_valid(out, 4))

    def test_revoked_candidate_or_revoked_live_edge_holds(self):
        pool = deepcopy(candidate_pool())
        pool["linked_context_candidates"][0]["verified_direct_primary_edges"][0][
            "status"
        ] = "REVOKED"
        out = self.operational(pool)
        self.assertEqual(out["status"], "HOLD_LINKED_EDGE_INVALID", out)
        self.assertEqual(out["writes_performed"], [])
        self.rt.link_verified = False
        revoked_live = self.operational()
        self.assertEqual(revoked_live["status"], "HOLD_LINKED_EDGE_CHANGED", revoked_live)
        self.assertEqual(revoked_live["writes_performed"], [])

    def test_gateway_rejects_revoked_missing_unrelated_or_mixed_edges(self):
        valid = self.operational()
        self.assertTrue(gateway._galaxy_valid(valid, 4))
        for edge_changes in (
            {"status": "REVOKED"},
            {"status": None},
            {"target_record_id": "HISTORY"},
            {"target_record_id": "UNKNOWN"},
        ):
            with self.subTest(edge_changes=edge_changes):
                forged = deepcopy(valid)
                forged["verified_linked_context"][0][
                    "verified_direct_primary_edges"
                ][0].update(edge_changes)
                self.assertFalse(gateway._galaxy_valid(forged, 4))
        mixed = deepcopy(valid)
        mixed["verified_linked_context"][0]["verified_direct_primary_edges"].append({
            "edge_id": "FORGED-REVOKED", "source_record_id": "LINKED",
            "target_record_id": "CURRENT", "status": "REVOKED",
        })
        self.assertFalse(gateway._galaxy_valid(mixed, 4))

    def test_duplicate_ids_cannot_cross_current_historical_or_linked(self):
        valid = self.operational()
        duplicated_history = deepcopy(valid)
        duplicated_history["historical_context"][0]["record"]["record_id"] = "CURRENT"
        duplicated_history["historical_context"][0]["governing_state"]["record_id"] = "CURRENT"
        self.assertFalse(gateway._galaxy_valid(duplicated_history, 4))
        duplicated_link = deepcopy(valid)
        duplicated_link["verified_linked_context"][0]["record"]["record_id"] = "CURRENT"
        duplicated_link["verified_linked_context"][0]["governing_state"]["record_id"] = "CURRENT"
        self.assertFalse(gateway._galaxy_valid(duplicated_link, 4))

    def test_bad_gateway_link_falls_back_to_real_verified_legacy_envelope(self):
        out = self.operational()
        out["verified_linked_context"][0]["verified_direct_primary_edges"][0][
            "status"
        ] = "REVOKED"
        with patch.object(gateway.mode, "mode_status", return_value=AUTH), patch.object(
            operational, "operational", return_value=out,
        ):
            result = gateway.read(self.rt, "gravity", scope="MemoryOS", limit=4)
        self.assertEqual(result["status"], "PASS_HEATDEATH_FALLBACK", result)
        self.assertEqual(result["effective_mode"], mode.HEATDEATH)
        self.assertFalse(result["galaxy_applied"])
        self.assertTrue(result["fallback_occurred"])
        self.assertEqual(result["retrieval"]["records"][0]["record_id"], "CURRENT")
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])


if __name__ == "__main__":
    unittest.main()
