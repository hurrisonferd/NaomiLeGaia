"""Stage9N: actual SELECT-only endpoint diagnosis and one-click redaction tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient
import gaiaos_app as carrier
import gaiaos_revision_endpoint_audit as endpoint
import gaiaos_revision_lineage_scout as lineage
import gaiaos_one_click_readiness as suite
import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as historical
import gaiaos_memory_mode as mode
from test_gaiaos_historical_evidence_stage9j import SyntheticMemoryStore
from test_gaiaos_one_click_stage9l import (
    CONTROL, PREFLIGHT, HISTORY, LITERAL, SyntheticStore,
    health, BROWSER_HARNESS,
)
from test_gaiaos_console_browser_contract import ConsoleHTMLParser


class ParameterizedSyntheticStore(SyntheticMemoryStore):
    def _fetchall_dicts(self, connection, query, params=()):
        assert query.lstrip().upper().startswith("SELECT"), "AUDIT_MUST_NOT_WRITE"
        self.reads += 1
        return [
            dict(row) for row in connection.execute(query, tuple(params)).fetchall()
        ]


class ExistingEndpointTests(unittest.TestCase):
    def setUp(self):
        self.store = ParameterizedSyntheticStore()
        self.addCleanup(self.store.db.close)
        lock = patch.object(mode, "mode_status", return_value=CONTROL)
        lock.start()
        self.addCleanup(lock.stop)

    def seed(
        self, *, older="GALAXY v1.2 old owner-approved behavior",
        newer="GALAXY v2.0 newer owner-approved behavior",
        older_source="naomi-owner-save",
        older_scope="MemoryOS",
        older_authority="NAOMI", older_missing=False,
        relation_source="new", relation_target="old",
    ):
        if not older_missing:
            self.store.insert(
                "old", older, source=older_source,
                scope=older_scope, authority=older_authority,
            )
        self.store.insert("new", newer)
        self.store.supersedes(
            relation_target, relation_source,
            status="VERIFIED", relation="REVISES",
        )
        self.store.db.commit()

    def approved_count(self):
        window = self.store._fetchall_dicts(
            self.store.db, historical._RECORD_QUERY
        )
        return sum(bool(readiness._technical_topics(row)) for row in window)

    def run_audit(self, *, expected_count=None, expected_edges=1):
        before_changes = self.store.db.total_changes
        result = endpoint.audit(
            self.store, expected_verified_owner_edges=expected_edges,
            expected_approved_records=(
                self.approved_count() if expected_count is None else expected_count
            ),
        )
        self.assertEqual(self.store.db.total_changes, before_changes)
        self.assertFalse(result["model_called"])
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["relation_created"])
        self.assertFalse(result["lead_is_a_supersession"])
        self.assertFalse(result["historical_retrieval_proven"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        serialized = json.dumps(result)
        for private in (
            "naomi-owner-save", "owner-approved behavior",
            "synthetic-calibration-fixture", "v1.2", "v2.0",
            '"record_id"', '"source_record_id"',
        ):
            self.assertNotIn(private, serialized)
        return result

    def test_excluded_calibration_older_endpoint_is_not_promoted(self):
        self.seed(older_source="synthetic-calibration-fixture")
        result = self.run_audit()
        self.assertEqual(result["status"], "CLASSIFIED_EXISTING_REVISION_ONLY")
        self.assertEqual(result["owner_revision_edges_checked"], 1)
        self.assertEqual(result["older_endpoint_reasons"], {
            "EXCLUDED_PROVENANCE": 1,
        })
        self.assertEqual(result["newer_endpoint_reasons"], {
            "ELIGIBLE_REAL_TECHNICAL": 1,
        })
        self.assertTrue(result["endpoint_scan_complete"])
        self.assertTrue(result["lead_owner_review_required"])

    def test_outside_scope_requires_one_private_narrow_lookup(self):
        self.seed(older_scope="FairyOS")
        result = self.run_audit()
        self.assertEqual(result["older_endpoint_reasons"], {"WRONG_SCOPE": 1})
        self.assertEqual(result["newer_endpoint_reasons"], {
            "ELIGIBLE_REAL_TECHNICAL": 1,
        })
        self.assertGreaterEqual(self.store.reads, 4)

    def test_nonowner_authority_is_separate_from_scope(self):
        self.seed(older_authority="OTHER")
        result = self.run_audit()
        self.assertEqual(result["older_endpoint_reasons"], {
            "NON_OWNER_AUTHORITY": 1,
        })

    def test_non_technical_statement_outside_window(self):
        self.seed(older="A genuine but unrelated old note")
        result = self.run_audit()
        self.assertEqual(result["older_endpoint_reasons"], {
            "NON_TECHNICAL_STATEMENT": 1,
        })

    def test_missing_endpoint_does_not_expose_identifier(self):
        self.seed(older_missing=True)
        result = self.run_audit()
        self.assertEqual(result["older_endpoint_reasons"], {
            "MISSING_RECORD": 1,
        })

    def test_self_referencing_edge_cannot_become_history(self):
        self.seed(relation_source="new", relation_target="new")
        result = self.run_audit()
        self.assertEqual(result["older_endpoint_reasons"], {
            "SELF_REFERENTIAL_REVISION": 1,
        })
        self.assertEqual(result["newer_endpoint_reasons"], {
            "SELF_REFERENTIAL_REVISION": 1,
        })
        self.assertFalse(result["lead_is_a_supersession"])

    def test_if_both_approved_parent_scout_disagreement_holds(self):
        self.seed()
        result = self.run_audit()
        self.assertEqual(result["reason"], "PARENT_SCOUT_DISAGREEMENT")
        self.assertFalse(result["endpoint_scan_complete"])

    def test_parent_count_drift_blocks_diagnosis(self):
        self.seed(older_source="synthetic-calibration-fixture")
        result = self.run_audit(expected_count=2)
        self.assertEqual(result["reason"], "PARENT_SAMPLE_CHANGED")
        self.assertFalse(result["window_complete"])

    def test_overfull_window_is_incomplete_not_no_candidates(self):
        self.seed()
        for number in range(99):
            self.store.insert(
                "extra-" + str(number),
                "GALAXY owner technical extra note " + str(number),
            )
        self.store.db.commit()
        result = self.run_audit(expected_count=100)
        self.assertEqual(result["reason"], "BOUNDED_WINDOW_INCOMPLETE")
        self.assertFalse(result["window_complete"])

    def test_too_many_owner_edges_does_not_make_20_extra_lookups(self):
        self.seed(older_missing=True)
        for _ in range(endpoint.MAX_EDGES):
            self.store.supersedes("old", "new", relation="REVISES")
        self.store.db.commit()
        before_reads = self.store.reads
        result = self.run_audit(expected_edges=11)
        self.assertEqual(result["reason"], "TOO_MANY_EDGES_FOR_BOUNDED_DIAGNOSIS")
        self.assertLessEqual(self.store.reads - before_reads, 3)

    def test_changed_release_control_returns_hold_even_if_evidence_exists(self):
        self.seed(older_source="synthetic-calibration-fixture")
        with patch.object(
            mode, "mode_status",
            side_effect=[CONTROL, {**CONTROL, "control_version": 999}],
        ):
            result = self.run_audit()
        self.assertEqual(
            result["reason"], "RELEASE_LOCK_CHANGED_OR_UNVERIFIED"
        )
        self.assertFalse(result["endpoint_scan_complete"])


def classified():
    result = endpoint._base("INELIGIBLE_ENDPOINTS_CLASSIFIED", checked=1)
    result.update({
        "status": "CLASSIFIED_EXISTING_REVISION_ONLY",
        "window_complete": True,
        "endpoint_scan_complete": True,
        "older_endpoint_reasons": {"EXCLUDED_PROVENANCE": 1},
        "newer_endpoint_reasons": {"ELIGIBLE_REAL_TECHNICAL": 1},
        "lead_owner_review_required": True,
        "EXTRA_PRIVATE_SOURCE": "DO_NOT_EXPOSE_ENDPOINT_ID",
    })
    return result


def fake_scout():
    value = lineage._base("NO_APPROVED_OWNER_REVISES_PAIR")
    value.update({
        "window_complete": True,
        "approved_technical_records_in_window": 2,
        "verified_owner_revises_in_window": 1,
        "approved_owner_revision_pairs_in_window": 0,
    })
    return value


class OneClickEndpointIntegrationTests(unittest.TestCase):
    def run_one_click(self, diagnostic=None):
        synthetic = SyntheticStore()
        with patch.object(mode, "mode_status", return_value=CONTROL), patch.object(
            readiness, "technical_preflight", return_value=PREFLIGHT
        ), patch.object(
            historical, "audit", return_value=HISTORY
        ), patch.object(
            lineage, "scout", return_value=fake_scout()
        ), patch.object(
            endpoint, "audit",
            return_value=classified() if diagnostic is None else diagnostic
        ) as audit, patch.object(
            readiness, "technical_literal_wiring_probe", return_value=LITERAL
        ), patch("openai.OpenAI") as sdk:
            result = suite.run(synthetic, carrier_health=health)
            sdk.assert_not_called()
        return result, audit, synthetic

    def test_same_six_checks_include_one_advisory_with_no_writes(self):
        result, audit, store = self.run_one_click()
        audit.assert_called_once_with(
            store, expected_verified_owner_edges=1,
            expected_approved_records=2,
        )
        self.assertEqual(result["status"], "SAFE_CHECKS_COMPLETE_RELEASE_LOCKED")
        self.assertEqual(len(result["checks"]), 6)
        self.assertEqual(
            result["next_action"], "OWNER_REVIEW_INELIGIBLE_REVISION_ENDPOINTS"
        )
        nested = result["checks"]["historical_evidence"]["revision_leads"][
            "endpoint_diagnostic"
        ]
        self.assertEqual(nested["older_endpoint_reasons"], {
            "EXCLUDED_PROVENANCE": 1,
        })
        self.assertFalse(nested["lead_is_a_supersession"])
        self.assertNotIn("DO_NOT_EXPOSE", json.dumps(result))
        self.assertEqual(store.write_calls, 0)
        self.assertFalse(result["release_activated"])

    def test_fake_success_flags_and_forged_counts_fail_closed(self):
        data = classified()
        data["model_called"] = True
        self.assertEqual(
            suite._endpoint_reasons(data)["reason"],
            "ENDPOINT_DIAGNOSTIC_UNVERIFIED",
        )
        data["model_called"] = False
        data["older_endpoint_reasons"] = {"EXCLUDED_PROVENANCE": True}
        self.assertEqual(
            suite._endpoint_reasons(data)["reason"],
            "ENDPOINT_DIAGNOSTIC_UNVERIFIED",
        )
        data["older_endpoint_reasons"] = {"EXCLUDED_PROVENANCE": 1}
        self.assertEqual(
            suite._endpoint_reasons(data)["status"],
            "CLASSIFIED_EXISTING_REVISION_ONLY",
        )
        self.assertNotIn("DO_NOT_EXPOSE", str(suite._endpoint_reasons(data)))

    def test_fail_closed_legacy_scans_not_triggered_by_no_revision(self):
        old = lineage._base("NO_VERIFIED_OWNER_REVISES_IN_WINDOW")
        old.update({"window_complete": True, "approved_technical_records_in_window": 2})
        with patch.object(mode, "mode_status", return_value=CONTROL), patch.object(
            readiness, "technical_preflight", return_value=PREFLIGHT
        ), patch.object(historical, "audit", return_value=HISTORY), patch.object(
            lineage, "scout", return_value=old
        ), patch.object(
            endpoint, "audit",
            side_effect=AssertionError("no new audit without verified revision")
        ), patch.object(
            readiness, "technical_literal_wiring_probe", return_value=LITERAL
        ):
            result = suite.run(SyntheticStore(), carrier_health=health)
        self.assertEqual(len(result["checks"]), 6)
        self.assertEqual(result["next_action"], "RESOLVE_REAL_HISTORICAL_EVIDENCE_GAP")

    def test_actual_served_page_single_click_redacts_nested_diagnosis(self):
        if not shutil.which("node"):
            self.fail("Node.js required for actual served console browser test")
        result, _, _ = self.run_one_click()
        result["raw_secret"] = "DO_NOT_EXPOSE_SERVER_SECRET"
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        page = client.get("/gaiaos/memory/one-click-console")
        parser = ConsoleHTMLParser()
        parser.feed(page.text)
        self.assertEqual(set(parser.buttons), {"run", "copy"})
        self.assertEqual(len(parser.scripts), 1)
        extra = """assert.equal(copiedJSON.checks.historical_evidence.revision_leads
          .endpoint_diagnostic.older_endpoint_reasons.EXCLUDED_PROVENANCE,1);
 assert.equal(copiedJSON.checks.historical_evidence.revision_leads
          .endpoint_diagnostic.lead_is_a_supersession,false);
 assert.match(nodes.summary.textContent,/Older side/);"""
        inject = " assert.equal(copiedJSON.schema,fixture.schema);"
        self.assertIn(inject, BROWSER_HARNESS)
        harness = BROWSER_HARNESS.replace(inject, inject + "\n " + extra)
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            js = root / "served.js"
            fixture = root / "fixture.json"
            test = root / "browser.js"
            js.write_text(parser.scripts[0][1], encoding="utf-8")
            fixture.write_text(json.dumps(result), encoding="utf-8")
            test.write_text(harness, encoding="utf-8")
            proc = subprocess.run(
                ["node", str(test), str(js), str(fixture)],
                text=True, capture_output=True, timeout=15, check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("STAGE9L_ONE_CLICK_BROWSER_PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
