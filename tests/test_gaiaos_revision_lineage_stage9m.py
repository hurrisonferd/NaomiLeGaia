"""Stage9M: synthetic only, real REVISES leads never auto-promote history."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import gaiaos_revision_lineage_scout as scout
import gaiaos_one_click_readiness as suite
import gaiaos_memory_mode as mode
import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as history
from test_gaiaos_historical_evidence_stage9j import SyntheticMemoryStore
from test_gaiaos_one_click_stage9l import (
    CONTROL, PREFLIGHT, HISTORY, LITERAL, SyntheticStore,
    health as stage9l_health,
)


class RevisionLineageSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticMemoryStore()
        self.addCleanup(self.store.db.close)
        control = patch.object(mode, "mode_status", return_value=CONTROL)
        control.start()
        self.addCleanup(control.stop)

    def seed(self, *, relation="REVISES", status="VERIFIED",
             older="GALAXY v1.2 older memory behavior",
             newer="GALAXY v2.0 revised newer memory behavior",
             newer_state="ACTIVE", older_source="naomi-owner-save",
             edge=True):
        self.store.insert("private-old", older, source=older_source)
        self.store.insert("private-new", newer, status=newer_state)
        self.store.insert("another", "HEATDEATH original legacy safeguards")
        if edge:
            self.store.supersedes(
                "private-old", "private-new", relation=relation,
                status=status,
            )
        self.store.db.commit()

    def assert_protected(self, result):
        self.assertFalse(result["lead_is_a_supersession"])
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["historical_retrieval_proven"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertFalse(result["model_called"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        for private in ("private-old", "private-new", "v1.2", "v2.0",
                        "naomi-owner-save", "older memory behavior"):
            self.assertNotIn(private, json.dumps(result))

    def test_no_verified_real_owner_revises_is_a_complete_zero_not_history(self):
        self.seed(edge=False)
        result = scout.scout(self.store)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["window_complete"])
        self.assertEqual(result["reason"], "NO_VERIFIED_OWNER_REVISES_IN_WINDOW")
        self.assertEqual(result["verified_owner_revises_in_window"], 0)
        self.assert_protected(result)

    def test_real_owner_revises_lead_is_only_manual_review(self):
        self.seed()
        result = scout.scout(self.store)
        self.assertEqual(result["status"], "LEADS_FOUND_OWNER_REVIEW_ONLY")
        self.assertEqual(result["reason"], "REVISES_LEADS_REQUIRE_OWNER_REVIEW")
        self.assertTrue(result["window_complete"])
        self.assertTrue(result["lead_owner_review_required"])
        self.assertEqual(result["approved_owner_revision_pairs_in_window"], 1)
        self.assertEqual(result["distinct_old_marker_leads_in_window"], 1)
        self.assert_protected(result)

    def test_nonverified_or_wrong_relation_cannot_be_revision_lead(self):
        for relation, status in (
            ("REVISES", "REVOKED"), ("SUPERSEDES", "VERIFIED")
        ):
            with self.subTest(relation=relation, status=status):
                self.store.db.execute("DELETE FROM memory_relations")
                self.store.db.execute("DELETE FROM memory_records")
                self.seed(relation=relation, status=status)
                result = scout.scout(self.store)
                self.assertEqual(result["reason"],
                                 "NO_VERIFIED_OWNER_REVISES_IN_WINDOW")
                self.assert_protected(result)

    def test_calibration_sources_never_form_authentic_lead(self):
        self.seed(older_source="synthetic-calibration-fixture")
        result = scout.scout(self.store)
        self.assertEqual(result["reason"], "NO_APPROVED_OWNER_REVISES_PAIR")
        self.assertEqual(result["approved_owner_revision_pairs_in_window"], 0)
        self.assert_protected(result)

    def test_archived_successor_does_not_count_as_active_revision(self):
        self.seed(newer_state="ARCHIVED")
        result = scout.scout(self.store)
        self.assertEqual(result["reason"], "NO_ACTIVE_NEWER_RECORD")
        self.assertEqual(result["distinct_old_marker_leads_in_window"], 0)
        self.assert_protected(result)

    def test_old_marker_must_be_real_and_distinct(self):
        for older, newer in (
            ("GALAXY older behavior", "GALAXY newer behavior"),
            ("GALAXY v1.2 older behavior", "GALAXY v1.2 also new behavior"),
        ):
            with self.subTest(older=older):
                self.store.db.execute("DELETE FROM memory_relations")
                self.store.db.execute("DELETE FROM memory_records")
                self.seed(older=older, newer=newer)
                result = scout.scout(self.store)
                self.assertEqual(result["reason"], "NO_DISTINCT_OLD_VERSION_MARKER")
                self.assert_protected(result)

    def test_101_records_cannot_claim_inventory_absence(self):
        self.seed(edge=False)
        for n in range(101):
            self.store.insert(
                "overflow-"+str(n), "GALAXY owner technical note "+str(n)
            )
        self.store.db.commit()
        result = scout.scout(self.store)
        self.assertEqual(result["reason"], "BOUNDED_WINDOW_INCOMPLETE")
        self.assertFalse(result["window_complete"])
        self.assert_protected(result)

    def test_release_lock_blocks_reads_and_retains_hold(self):
        self.seed()
        with patch.object(mode, "mode_status", return_value={
            **CONTROL, "effective_mode": mode.BIGBANG,
            "bigbang_activation_enabled": True,
        }):
            result = scout.scout(self.store)
        self.assertEqual(result["reason"], "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")
        self.assertFalse(result["window_complete"])
        self.assert_protected(result)


class OneClickIntegrationTests(unittest.TestCase):
    def test_genuine_leads_show_on_same_click_but_never_change_state(self):
        store = SyntheticStore()
        fixture = scout._base("REVISES_LEADS_REQUIRE_OWNER_REVIEW")
        fixture.update({
            "status": "LEADS_FOUND_OWNER_REVIEW_ONLY", "window_complete": True,
            "approved_technical_records_in_window": 3,
            "verified_owner_revises_in_window": 1,
            "approved_owner_revision_pairs_in_window": 1,
            "active_successor_revision_pairs_in_window": 1,
            "distinct_old_marker_leads_in_window": 1,
            "lead_owner_review_required": True,
        })
        with patch.object(mode, "mode_status", return_value=CONTROL), patch.object(
            readiness, "technical_preflight", return_value=PREFLIGHT
        ), patch.object(
            history, "audit", return_value=HISTORY
        ), patch.object(
            readiness, "technical_literal_wiring_probe", return_value=LITERAL
        ), patch.object(scout, "scout", return_value=fixture) as lead, patch(
            "openai.OpenAI"
        ) as sdk:
            result = suite.run(store, carrier_health=stage9l_health)
            sdk.assert_not_called()
            lead.assert_called_once_with(store)
        self.assertEqual(result["status"], "SAFE_CHECKS_COMPLETE_RELEASE_LOCKED")
        self.assertEqual(len(result["checks"]), 6)
        hint = result["checks"]["historical_evidence"]["revision_leads"]
        self.assertEqual(hint["status"], "LEADS_FOUND_OWNER_REVIEW_ONLY")
        self.assertEqual(hint["counts"]["distinct_old_marker_leads_in_window"], 1)
        self.assertFalse(hint["lead_is_a_supersession"])
        self.assertEqual(
            result["next_action"], "OWNER_REVIEW_VERIFIED_REVISES_LEADS_WITHOUT_PROMOTION"
        )
        self.assertFalse(result["historical_retrieval_proven"])
        self.assertFalse(result["release_activated"])
        self.assertEqual(result["writes_performed"], [])

    def test_forged_or_missing_leads_fail_closed_without_leaking(self):
        data = scout._base("REVISES_LEADS_REQUIRE_OWNER_REVIEW")
        data.update({
            "status": "LEADS_FOUND_OWNER_REVIEW_ONLY",
            "window_complete": True,
            "approved_technical_records_in_window": 1,
            "verified_owner_revises_in_window": 1,
            "approved_owner_revision_pairs_in_window": 1,
            "active_successor_revision_pairs_in_window": 1,
            "distinct_old_marker_leads_in_window": 1,
            "lead_owner_review_required": True,
            "model_called": True, "private_statement": "SHOULD_NOT_LEAK",
        })
        cleaned = suite._revision_leads(data)
        self.assertEqual(cleaned["reason"], "REVISION_LEADS_UNVERIFIED")
        self.assertNotIn("SHOULD_NOT_LEAK", str(cleaned))
        data["model_called"] = False
        valid = suite._revision_leads(data)
        self.assertEqual(valid["counts"]["distinct_old_marker_leads_in_window"], 1)
        self.assertNotIn("SHOULD_NOT_LEAK", str(valid))


if __name__ == "__main__":
    unittest.main(verbosity=2)
