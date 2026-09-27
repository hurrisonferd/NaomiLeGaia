"""Stage 9AE: Stage 9Y HOLD must never become current/linked/legacy/chat.

Tests actual Stage 9W operational -> gateway -> browser instruction boundaries.
ALL data and permissions are synthetic; BIGBANG is mocked only in tests.
Neither SOVMEM database, original GaiaOS production, Render nor E-LANES
are accessed. A test-only forged CURRENT state cannot graduate an archive.
"""
from __future__ import annotations

from copy import deepcopy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))
import galaxy_frontdoor_context as reader
import galaxy_phase3_exit
import galaxy_archive_staging as imported
import gaiaos_memory_gateway as gateway
import gaiaos_chat_memory as evidence
import gaiaos_memory_mode as mode
import gaiaos_chat_auto_memory as automatic
import galaxy_legacy_gravity as gravity
from test_bigbang_operational_reader_stage6 import FakeMemory, candidate_pool
from test_galaxy_stage9w_browser_chat_wiring import (
    Stage9WBrowserRouting, AUTH, HEATDEATH, prepared,
)

QUERY = "gravity contextual influence memory retrieval"
ARCHIVE_SOURCE = "galaxy-archive-v1:" + "a" * 64


class HeldHistoryReadBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeMemory()

    def operational(self, pool=None):
        with patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            return_value=deepcopy(pool if pool is not None else candidate_pool()),
        ):
            return reader.operational(self.rt, QUERY, limit=4)

    def test_held_primary_cannot_be_current_even_if_governing_claims_current(self):
        self.rt.records["CURRENT"]["status"] = imported.STAGED_STATUS
        result = self.operational()
        self.assertEqual(result["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["galaxy_weighting_applied"])
        self.assertFalse(result["e_lanes_modified"])

    def test_ungraduated_archive_source_cannot_be_activated_by_forged_status(self):
        self.rt.records["CURRENT"]["status"] = "ACTIVE"
        self.rt.records["CURRENT"]["source"] = ARCHIVE_SOURCE
        with patch.object(
            gravity, "resolve_for_retrieval",
            side_effect=AssertionError("archive gravity MUST NOT RESOLVE"),
        ):
            out = self.operational()
        self.assertEqual(out["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(out["records"], [])

    def test_held_candidate_in_historical_context_is_denied_not_promoted(self):
        self.rt.records["HISTORY"]["status"] = imported.STAGED_STATUS
        result = self.operational()
        self.assertEqual(result["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["writes_performed"], [])

    def test_held_or_forged_active_archive_link_cannot_be_verified_context(self):
        for change in (
            {"status": imported.STAGED_STATUS},
            {"source": ARCHIVE_SOURCE, "status": "ACTIVE"},
        ):
            with self.subTest(change=change):
                self.rt.records["LINKED"].update(change)
                result = self.operational()
                self.assertEqual(result["status"], "HOLD_UNRELEASED_LINKED_ARCHIVE")
                self.assertEqual(result["records"], [])
                self.assertEqual(result["writes_performed"], [])
                self.rt.records["LINKED"] = {
                    **self.rt.records["LINKED"],
                    "status": "ACTIVE", "source": "proof:linked",
                }

    def test_gateway_independently_rejects_all_three_forged_archive_lanes(self):
        valid = self.operational()
        self.assertTrue(gateway._galaxy_valid(valid, 4))
        for lane in ("records", "historical_context", "verified_linked_context"):
            for change in (
                {"status": imported.STAGED_STATUS},
                {"source": ARCHIVE_SOURCE, "status": "ACTIVE"},
            ):
                with self.subTest(lane=lane,change=change):
                    forged = deepcopy(valid)
                    forged[lane][0]["record"].update(change)
                    forged[lane][0]["source_provenance"] = forged[lane][0]["record"]["source"]
                    self.assertFalse(gateway._galaxy_valid(forged, 4))

    def test_forged_operational_packet_triggers_bounded_legacy_fallback(self):
        valid = self.operational()
        forged = deepcopy(valid)
        forged["records"][0]["record"]["status"] = imported.STAGED_STATUS
        with patch.object(gateway.mode, "mode_status", return_value=AUTH), patch.object(
            reader, "operational", return_value=forged,
        ):
            result = gateway.read(self.rt, "gravity", scope="MemoryOS", limit=4)
        self.assertEqual(result["status"], "PASS_HEATDEATH_FALLBACK", result)
        self.assertFalse(result["galaxy_applied"])
        self.assertIsNone(result["galaxy_context"])
        self.assertTrue(result["fallback_occurred"])
        self.assertTrue(all(
            r.get("status") != imported.STAGED_STATUS
            for r in result["retrieval"]["records"]
        ))

    def test_misconfigured_legacy_never_echoes_staged_archives_even_in_heatdeath(self):
        for control in (HEATDEATH, AUTH):
            for change in (
                {"status": imported.STAGED_STATUS},
                {"source": ARCHIVE_SOURCE, "status": "ACTIVE"},
            ):
                with self.subTest(control=control["effective_mode"],change=change):
                    self.rt.records["CURRENT"].update(change)
                    with patch.object(gateway.mode, "mode_status", return_value=control):
                        result = gateway.read(
                            self.rt, QUERY, scope="MemoryOS", limit=4,
                        )
                    self.assertEqual(result["status"], "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY")
                    self.assertIsNone(result["retrieval"])
                    self.assertIsNone(result["galaxy_context"])
                    self.assertFalse(result["fallback_occurred"])
                    self.assertNotIn(
                        self.rt.records["CURRENT"]["statement"], json.dumps(result),
                    )
                    self.rt.records["CURRENT"].update({
                        "status": "ACTIVE", "source": "proof:current",
                    })

    def test_clean_legacy_and_source_galaxy_paths_unchanged(self):
        with patch.object(gateway.mode, "mode_status", return_value=HEATDEATH):
            legacy = gateway.read(self.rt, QUERY, scope="MemoryOS", limit=4)
        self.assertEqual(legacy["status"], "PASS_HEATDEATH")
        self.assertEqual(legacy["retrieval"]["records"][0]["record_id"], "CURRENT")
        self.assertFalse(legacy["galaxy_applied"])
        operational = self.operational()
        self.assertEqual(operational["status"], "PASS_GALAXY_OPERATIONAL_RETRIEVAL")
        self.assertTrue(gateway._galaxy_valid(operational, 4))


class HeldHistoryModelBoundaryTests(unittest.TestCase):
    def test_final_model_instruction_guard_refuses_held_current_or_linked(self):
        for key in ("current_records", "verified_linked_context"):
            packet = prepared()
            if key == "verified_linked_context":
                packet[key] = [{
                    "record_id": "MEM-STAGE9AE-HELD-LINK",
                    "statement": "STAGE9AE-UNTRUSTED-HISTORICAL-TEXT",
                    "statement_truncated": False,
                    "source": "proof:old",
                    "source_truncated": False,
                    "governing_state": "CURRENT",
                    "current_default_eligible": True,
                    "context_only": True,
                    "status": "ACTIVE",
                }]
            for change in (
                {"status": imported.STAGED_STATUS},
                {"source": ARCHIVE_SOURCE, "status": "ACTIVE"},
            ):
                with self.subTest(key=key,change=change):
                    forged = deepcopy(packet)
                    forged[key][0].update(change)
                    self.assertFalse(evidence.validate_prepared(forged))
                    with self.assertRaises(ValueError):
                        evidence.instructions(forged)

    def test_actual_browser_route_never_injects_forged_held_archive(self):
        harness = Stage9WBrowserRouting(
            "test_actual_chat_route_gates_implicit_retrieval_in_heatdeath"
        )
        harness.setUp()
        try:
            for change in (
                {"status": imported.STAGED_STATUS},
                {"source": ARCHIVE_SOURCE, "status": "ACTIVE"},
            ):
                with self.subTest(change=change):
                    packet = prepared()
                    packet["current_records"][0].update(change)
                    with patch.object(automatic, "prepare_for_browser",
                                      return_value=packet), patch.object(
                        mode, "mode_status", return_value=AUTH,
                    ):
                        resp = harness.post()
                    self.assertEqual(resp.status_code, 200, resp.text)
                    self.assertEqual(
                        harness.model.calls[-1]["instructions"],
                        "Trusted carrier.",
                    )
                    self.assertEqual(
                        resp.json()["memory_context"]["status"],
                        "HOLD_NOT_APPLIED_UNVERIFIED_OR_HEATDEATH",
                    )
                    self.assertNotIn(ARCHIVE_SOURCE, resp.text)
                    self.assertNotIn(
                        "Verified fixture historical memory",
                        harness.model.calls[-1]["instructions"],
                    )
        finally:
            harness.doCleanups()


if __name__ == "__main__":
    unittest.main()
