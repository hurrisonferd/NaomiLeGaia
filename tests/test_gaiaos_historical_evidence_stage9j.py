"""Stage 9J: isolated SQLite-only technical-history gap diagnosis."""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import gaiaos_historical_evidence_audit as audit
import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_mode as mode


CONTROL = {
    "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH, "control_version": "ci-only",
    "bigbang_activation_enabled": False,
}


class SyntheticMemoryStore:
    """Mirrors read-only Turso SQL contract, never connects to production."""
    _INITIALIZED = True

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE memory_records (
                record_id TEXT, authority TEXT, scope TEXT, statement TEXT,
                source TEXT, status TEXT, created_at TEXT
            );
            CREATE TABLE memory_relations (
                source_record_id TEXT, target_record_id TEXT,
                authority TEXT, status TEXT, relation_type TEXT,
                verified_at TEXT
            );
        """)
        self.reads = 0
        self.writes = 0
        self.governing_broken = False
        self.governing_nonhistorical = False

    def storage_status(self):
        # Fixture metadata only. This does NOT contact a remote database.
        return {"backend": "turso_libsql", "remote_configured": True}

    def _db(self):
        return self.db

    def _fetchall_dicts(self, connection, query):
        assert query.lstrip().upper().startswith("SELECT"), "AUDIT_MUST_NOT_WRITE"
        self.reads += 1
        return [dict(row) for row in connection.execute(query).fetchall()]

    def insert(
        self, record_id, statement, *, source="naomi-owner-save",
        status="ACTIVE", authority="NAOMI", scope="MemoryOS",
    ):
        self.db.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?)",
            (record_id, authority, scope, statement, source, status, record_id),
        )

    def supersedes(
        self, old, successor, *, status="VERIFIED", relation="SUPERSEDES",
        authority="NAOMI", verified_at="2026-09-25",
    ):
        self.db.execute(
            "INSERT INTO memory_relations VALUES (?,?,?,?,?,?)",
            (successor, old, authority, status, relation, verified_at),
        )

    def galaxy_governing_state(self, record_id):
        if self.governing_broken:
            raise RuntimeError("private backend detail must never leak")
        row = self.db.execute(
            "SELECT status FROM memory_records WHERE record_id=?", (record_id,),
        ).fetchone()
        incoming = self.db.execute(
            "SELECT source_record_id FROM memory_relations "
            "WHERE target_record_id=? AND status='VERIFIED' "
            "AND relation_type='SUPERSEDES'", (record_id,),
        ).fetchall()
        if incoming and not self.governing_nonhistorical:
            state = (
                "HISTORICAL_SUPERSEDED" if row["status"] == "ACTIVE"
                else "NONACTIVE_HISTORICAL"
            )
            current = False
        else:
            state = "CURRENT"
            current = row["status"] == "ACTIVE"
        return {
            "record_id": record_id, "state": state,
            "current_default_eligible": current,
            "historical_retrieval_eligible": True,
        }


class HistoricalEvidenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.runtime = SyntheticMemoryStore()
        self.addCleanup(self.runtime.db.close)
        control = patch.object(mode, "mode_status", return_value=CONTROL)
        control.start()
        self.addCleanup(control.stop)

    def seed(self, *, old_statement="HEATDEATH v1.2 historical rollback guard",
             new_statement="HEATDEATH v2.0 replaces old rollback guard",
             successor_status="ACTIVE", old_status="ACTIVE",
             current_count=2, supersede=True, edge_status="VERIFIED",
             edge_relation="SUPERSEDES"):
        self.runtime.insert("hist-old", old_statement, status=old_status)
        self.runtime.insert(
            "hist-new", new_statement, status=successor_status,
        )
        if current_count >= 1:
            self.runtime.insert(
                "curr-a", "Power Word preserve safeguards memory continuity",
            )
        if current_count >= 2:
            self.runtime.insert(
                "curr-b", "six independent E-LANES retain owner provenance",
            )
        if supersede:
            self.runtime.supersedes(
                "hist-old", "hist-new",
                status=edge_status, relation=edge_relation,
            )
        self.runtime.db.commit()

    def assert_private_safe(self, result):
        text = str(result)
        for secret in (
            "hist-old", "hist-new", "curr-a", "curr-b",
            "v1.2", "v2.0", "naomi-owner-save",
            "historical rollback guard", "private backend detail",
        ):
            self.assertNotIn(secret, text)
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["historical_retrieval_tested"])
        self.assertFalse(result["historical_retrieval_proven"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["model_called"])

    def test_absent_verified_owner_edge_is_specific_nonleaking_hold(self):
        self.seed(supersede=False)
        result = audit.audit(self.runtime)
        self.assertEqual(
            result["reason"], "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW"
        )
        self.assertTrue(result["bounded_window_complete"])
        self.assertEqual(result["approved_technical_records_in_window"], 4)
        self.assertEqual(result["verified_owner_supersedes_in_window"], 0)
        self.assert_private_safe(result)

    def test_revoked_and_revises_never_count_as_verified_supersedes(self):
        for status, relation in (
            ("REVOKED", "SUPERSEDES"), ("VERIFIED", "REVISES"),
        ):
            with self.subTest(status=status, relation=relation):
                self.runtime.db.execute("DELETE FROM memory_records")
                self.runtime.db.execute("DELETE FROM memory_relations")
                self.seed(edge_status=status, edge_relation=relation)
                result = audit.audit(self.runtime)
                self.assertEqual(
                    result["reason"], "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW"
                )
                self.assert_private_safe(result)

    def test_verified_edge_to_unapproved_fixture_is_not_history(self):
        self.runtime.insert(
            "hist-old", "GALAXY v1.2 historical owner topic",
            source="synthetic-calibration-fixture",
        )
        self.runtime.insert(
            "hist-new", "GALAXY v2.0 owner successor",
        )
        self.runtime.insert("curr-a", "Power Word preserve protects continuity")
        self.runtime.insert("curr-b", "six E-LANES protect owner provenance")
        self.runtime.supersedes("hist-old", "hist-new")
        result = audit.audit(self.runtime)
        self.assertEqual(
            result["reason"], "NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR"
        )
        self.assertEqual(result["verified_owner_supersedes_in_window"], 1)
        self.assert_private_safe(result)

    def test_inactive_successor_cannot_qualify(self):
        self.seed(successor_status="ARCHIVED")
        result = audit.audit(self.runtime)
        self.assertEqual(result["reason"], "NO_ACTIVE_APPROVED_SUCCESSOR")
        self.assertEqual(result["approved_technical_pairs_in_window"], 1)
        self.assert_private_safe(result)

    def test_absent_or_shared_old_marker_cannot_qualify(self):
        for old_statement, new_statement in (
            ("HEATDEATH historical rollback guard",
             "HEATDEATH current rollback guard"),
            ("HEATDEATH v1.2 historical rollback guard",
             "HEATDEATH v1.2 and v2.0 current guard"),
        ):
            with self.subTest(old=old_statement):
                self.runtime.db.execute("DELETE FROM memory_records")
                self.runtime.db.execute("DELETE FROM memory_relations")
                self.seed(
                    old_statement=old_statement,
                    new_statement=new_statement,
                )
                result = audit.audit(self.runtime)
                self.assertEqual(result["reason"], "NO_DISTINCT_HISTORICAL_MARKER")
                self.assert_private_safe(result)

    def test_missing_governance_is_a_separate_fail_closed_reason(self):
        self.seed()
        self.runtime.governing_nonhistorical = True
        result = audit.audit(self.runtime)
        self.assertEqual(
            result["reason"], "HISTORICAL_GOVERNING_STATE_UNVERIFIED"
        )
        self.assertEqual(result["distinct_old_marker_pairs_in_window"], 1)
        self.assertEqual(result["governed_historical_pairs_in_window"], 0)
        self.assert_private_safe(result)

        self.runtime.governing_broken = True
        result = audit.audit(self.runtime)
        self.assertEqual(
            result["reason"], "HISTORICAL_GOVERNING_STATE_READ_FAILED"
        )
        self.assert_private_safe(result)

    def test_read_only_realistic_candidate_is_prepared_but_not_tested(self):
        self.seed()
        with patch.object(
            readiness, "review",
            side_effect=AssertionError("Stage9J cannot execute GALAXY"),
        ):
            result = audit.audit(self.runtime)
        self.assertEqual(result["status"], "CANDIDATE_PRESENT_UNTESTED", result)
        self.assertEqual(
            result["reason"], "HISTORICAL_CANDIDATE_PREPARED_UNTESTED"
        )
        self.assertEqual(result["approved_technical_pairs_in_window"], 1)
        self.assertEqual(result["governed_historical_pairs_in_window"], 1)
        self.assertTrue(result["historical_case_prepared"])
        self.assertGreater(self.runtime.reads, 0)
        self.assertEqual(self.runtime.writes, 0)
        self.assert_private_safe(result)

    def test_archived_real_superseded_record_remains_eligible_for_audit(self):
        self.seed(old_status="ARCHIVED")
        result = audit.audit(self.runtime)
        self.assertEqual(result["status"], "CANDIDATE_PRESENT_UNTESTED")
        self.assert_private_safe(result)

    def test_even_valid_history_holds_without_two_current_cases(self):
        self.seed(current_count=0)
        result = audit.audit(self.runtime)
        self.assertEqual(
            result["reason"], "STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED"
        )
        self.assertFalse(result["historical_case_prepared"])
        self.assert_private_safe(result)

    def test_101st_row_fails_closed_instead_of_reporting_absence(self):
        self.seed(supersede=False)
        for index in range(101):
            self.runtime.insert(
                f"overflow-{index:03d}",
                "GALAXY owner context for overflow item",
                source="naomi-owner-save",
            )
        result = audit.audit(self.runtime)
        self.assertEqual(result["reason"], "BOUNDED_WINDOW_INCOMPLETE")
        self.assertFalse(result["bounded_window_complete"])
        self.assert_private_safe(result)

    def test_broken_or_unconfirmed_backend_and_emergency_control_hold(self):
        self.runtime._INITIALIZED = False
        result = audit.audit(self.runtime)
        self.assertEqual(result["reason"], "RUNTIME_NOT_INITIALIZED")
        self.runtime._INITIALIZED = True
        with patch.object(
            self.runtime, "storage_status",
            return_value={"backend": "sqlite", "remote_configured": False},
        ):
            result = audit.audit(self.runtime)
        self.assertEqual(result["reason"], "REMOTE_STORAGE_NOT_CONFIRMED")
        with patch.object(
            mode, "mode_status",
            return_value={**CONTROL, "effective_mode": mode.BIGBANG,
                          "bigbang_activation_enabled": True},
        ):
            result = audit.audit(self.runtime)
        self.assertEqual(result["reason"], "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")
        self.assert_private_safe(result)

    def test_owner_http_route_denies_missing_bearer_and_returns_no_store(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier

        with TestClient(carrier.app) as client, patch.object(
            carrier.base, "API_KEY", "ci-only-owner-secret",
        ), patch.object(
            audit, "audit",
            return_value={"schema": audit.SCHEMA, "status": "HOLD",
                          "reason": "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
                          "writes_performed": [], "release_activated": False},
        ) as core, patch("openai.OpenAI") as sdk:
            path = "/gaiaos/memory/historical-evidence-audit"
            self.assertEqual(client.post(path).status_code, 401)
            good = client.post(
                path,
                headers={"Authorization": "Bearer ci-only-owner-secret"},
            )
            self.assertEqual(good.status_code, 200, good.text)
            self.assertIn("no-store", good.headers["cache-control"])
            self.assertEqual(good.json()["schema"], audit.SCHEMA)
            core.assert_called_once()
            sdk.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
