"""Stage9P: signed historical owner evidence vs a fresh read-only source sample."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_receipts as receipts
import gaiaos_memory_mode as mode
import gaiaos_owner_evidence_replay as replay
import gaiaos_one_click_readiness as oneclick
import gaiaos_one_click_console as console

KEY = "ci-only-test-owner-key"
FP = "sf1_" + "a" * 32
CONTROL = {
    "schema": mode.SCHEMA,
    "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH,
    "bigbang_activation_enabled": False,
    "control_version": 7,
    "writes_performed": [],
}


def owner_receipt():
    questions = [
        {"case": 0, "generator_expected_slot": 0},
        {"case": 1, "generator_expected_slot": 1},
        {"case": 2, "generator_expected_slot": 0},
    ]
    choices = [
        {"case": 0, "resolution": "B"},
        {"case": 1, "resolution": "A"},
        {"case": 2, "resolution": "COLLISION"},
    ]
    raw = receipts.owner_from_adjudication(
        sample_fingerprint=FP, questions=questions, choices=choices
    )
    assert raw is not None
    signed = receipts.seal("owner", raw, owner_key=KEY)
    assert signed is not None
    return signed


def collision_receipt():
    data = {
        "schema": "gaiaos.augury.collision-two-source-shadow.v1",
        "status": "PASS_TWO_SOURCE_READBACK_ONLY",
        "case": 2,
        "sample_fingerprint": FP,
        "sample_fingerprint_bound": True,
        "owner_receipt_verified": True,
        "quote_exact_verified": [True, True],
        "strict_literal_compiled": [True, True],
        "galaxy_readback_verified": [True, True],
        "legacy_exact_parity": True,
        "collision_entailment_independently_proven": False,
        "general_semantic_quality_proven": False,
        "historical_coverage": False,
        "full_readiness_status":
            "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
        "model_called": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
    }
    signed = receipts.seal("collision", data, owner_key=KEY)
    assert signed is not None
    return signed


def preview(_runtime, *, fingerprint_key):
    assert fingerprint_key == KEY
    return {
        "schema": "gaiaos.augury.semantic-owner-oracle-preview.v1",
        "status": "READY_OWNER_ADJUDICATION",
        "sample_fingerprint": FP,
        "sample_fingerprint_bound": True,
        "records": [
            {"slot": 0, "statement": "PRIVATE_A"},
            {"slot": 1, "statement": "PRIVATE_B"},
        ],
        "questions": [
            {"case": i, "question": f"PRIVATE_QUESTION_{i}"}
            for i in range(3)
        ],
        "model_called": False,
        "writes_performed": [],
        "release_activated": False,
    }


class NeverWriteStore:
    def __getattr__(self, name):
        if any(word in name for word in ("write", "insert", "update", "delete")):
            raise AssertionError("REPLAY_MUST_NOT_WRITE")
        raise AttributeError(name)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.write_receipt(replay._OWNER_FILE, owner_receipt())
        self.write_receipt(replay._COLLISION_FILE, collision_receipt())

    def write_receipt(self, name, data):
        (self.directory / name).write_text(
            json.dumps(data), encoding="utf-8"
        )

    def run_replay(self, **kwargs):
        with patch.object(mode, "mode_status", return_value=CONTROL):
            return replay.audit(
                NeverWriteStore(), owner_key=KEY,
                proof_directory=self.directory,
                preview_fn=preview, **kwargs
            )

    def test_two_archived_attestations_rebind_without_model_or_writes(self):
        data = self.run_replay()
        self.assertEqual(data["status"],
                         "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE")
        self.assertTrue(data["source_attestations_verified"])
        self.assertTrue(data["live_sample_matches_archive"])
        self.assertEqual(data["owner_labeled_current_cases"], 3)
        self.assertEqual(data["owner_single_source_cases"], 2)
        self.assertEqual(data["owner_collision_cases"], 1)
        self.assertTrue(data["archived_two_source_literal_readback_attested"])
        self.assertFalse(data["archived_signed_model_receipt_in_repo"])
        self.assertFalse(data["model_comparison_performed"])
        self.assertFalse(data["semantic_entailment_independently_proven"])
        self.assertFalse(data["general_semantic_quality_proven"])
        self.assertFalse(data["historical_retrieval_proven"])
        self.assertFalse(data["release_activated"])
        self.assertFalse(data["new_model_call_performed"])
        self.assertEqual(data["writes_performed"], [])
        self.assertNotIn("PRIVATE_", str(data))
        self.assertNotIn(KEY, str(data))
        self.assertNotIn(FP, str(data))

    def test_wrong_key_invalid_signature_and_no_retroactive_signing(self):
        with patch.object(mode, "mode_status", return_value=CONTROL):
            result = replay.audit(
                NeverWriteStore(), owner_key="new-rotated-key",
                proof_directory=self.directory, preview_fn=preview,
            )
        self.assertEqual(
            result["reason"], "ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED"
        )
        damaged = owner_receipt()
        damaged["case_results"][0]["owner_resolution"] = "A"
        self.write_receipt(replay._OWNER_FILE, damaged)
        self.assertEqual(
            self.run_replay()["reason"],
            "ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED",
        )

    def test_missing_oversized_or_extra_private_fields_never_replay(self):
        self.write_receipt(replay._OWNER_FILE, {"private": "DO_NOT_ECHO"})
        missing = self.run_replay()
        self.assertEqual(
            missing["reason"], "ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED"
        )
        self.assertNotIn("DO_NOT_ECHO", str(missing))
        self.write_receipt(replay._OWNER_FILE, owner_receipt())
        extra = owner_receipt()
        extra["private"] = "DO_NOT_ECHO"
        self.write_receipt(replay._OWNER_FILE, extra)
        self.assertEqual(
            self.run_replay()["reason"],
            "ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED",
        )
        (self.directory / replay._OWNER_FILE).write_text("x" * 12001)
        self.assertEqual(
            self.run_replay()["reason"], "ARCHIVED_RECEIPT_UNAVAILABLE"
        )

    def test_live_fingerprint_drift_holds_and_never_claims_stale_current(self):
        def changed(_runtime, *, fingerprint_key):
            data = preview(_runtime, fingerprint_key=fingerprint_key)
            data["sample_fingerprint"] = "sf1_" + "b" * 32
            return data

        with patch.object(mode, "mode_status", return_value=CONTROL):
            result = replay.audit(
                NeverWriteStore(), owner_key=KEY,
                proof_directory=self.directory, preview_fn=changed,
            )
        self.assertEqual(result["reason"], "ARCHIVED_SAMPLE_NOT_CURRENT")
        self.assertFalse(result["live_sample_matches_archive"])

    def test_pretend_provider_call_and_bad_lock_fail_closed(self):
        def unsafe(_runtime, *, fingerprint_key):
            data = preview(_runtime, fingerprint_key=fingerprint_key)
            data["model_called"] = True
            return data

        with patch.object(mode, "mode_status", return_value=CONTROL):
            result = replay.audit(
                NeverWriteStore(), owner_key=KEY,
                proof_directory=self.directory, preview_fn=unsafe,
            )
        self.assertEqual(result["reason"], "LIVE_SOURCE_SAMPLE_UNAVAILABLE")
        bad = {**CONTROL, "bigbang_activation_enabled": True}
        with patch.object(mode, "mode_status", return_value=bad):
            result = replay.audit(
                NeverWriteStore(), owner_key=KEY,
                proof_directory=self.directory, preview_fn=preview,
            )
        self.assertEqual(result["reason"], "HEATDEATH_RELEASE_LOCK_UNVERIFIED")

    def test_oneclick_strict_redaction_nested_and_no_extra_button(self):
        source = self.run_replay()
        redacted = oneclick._owner_evidence_replay(
            {**source, "PRIVATE_STATEMENT": "DO_NOT_ECHO"}
        )
        self.assertEqual(
            redacted["status"], "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE"
        )
        self.assertNotIn("DO_NOT_ECHO", str(redacted))
        self.assertFalse(redacted["model_comparison_performed"])
        corrupted = oneclick._owner_evidence_replay(
            {**source, "general_semantic_quality_proven": True}
        )
        self.assertEqual(corrupted["reason"], "OWNER_REPLAY_UNVERIFIED")
        page = console.render("ci-stage9p-nonce")
        self.assertIn("owner_evidence_replay", page)
        self.assertIn("Archived owner evidence", page)
        self.assertEqual(page.count('id="run"'), 1)


    def test_actual_served_oneclick_browser_redacts_nested_replay(self):
        import shutil
        import subprocess

        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        from test_gaiaos_one_click_stage9l import (
            BROWSER_HARNESS, OneClickSuiteTests, PAGE,
        )
        from test_gaiaos_console_browser_contract import ConsoleHTMLParser

        self.assertIsNotNone(shutil.which("node"), "Node.js required")
        with TestClient(carrier.app) as client:
            page = client.get(PAGE)
        parser = ConsoleHTMLParser()
        parser.feed(page.text)
        self.assertEqual(set(parser.buttons), {"run", "copy"})
        self.assertEqual(len(parser.scripts), 1)

        fixture = OneClickSuiteTests()
        fixture.setUp()
        report, *_ = fixture.run_fixture()
        status = self.run_replay()
        visible = oneclick._owner_evidence_replay(status)
        report["checks"]["current_literal_readback"]["owner_evidence_replay"] = {
            **visible, "private": "DO_NOT_EXPOSE_NESTED_SOURCE",
        }
        # Exercise actual served JS with a valid nested result followed
        # by an altered verification flag. Never allow the latter to copy.
        before = ' process.stdout.write("STAGE9L_ONE_CLICK_BROWSER_PASS\\n");'
        after = """
 assert.equal(
  copiedJSON.checks.current_literal_readback.owner_evidence_replay.status,
  "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE"
 );
 assert.equal(
  copiedJSON.checks.current_literal_readback.owner_evidence_replay
   .live_sample_matches_archive,true
 );
 response={...fixture,checks:{...fixture.checks,
  current_literal_readback:{...fixture.checks.current_literal_readback,
   owner_evidence_replay:{...fixture.checks.current_literal_readback
    .owner_evidence_replay,model_comparison_performed:true}}}};
 await events.run();
 assert.equal(nodes.copy.disabled,true,"Tampered nested proof must not copy");
 assert.ok(!nodes.report.textContent.includes("DO_NOT_EXPOSE"));
 process.stdout.write("STAGE9P_NESTED_BROWSER_PASS\\n");
""" + before
        self.assertIn(before, BROWSER_HARNESS)
        harness_text = BROWSER_HARNESS.replace(before, after)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "served.js").write_text(
                parser.scripts[0][1], encoding="utf-8"
            )
            (root / "fixture.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            (root / "harness.js").write_text(
                harness_text, encoding="utf-8"
            )
            result = subprocess.run(
                ["node", str(root / "harness.js"),
                 str(root / "served.js"), str(root / "fixture.json")],
                capture_output=True, text=True, timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STAGE9P_NESTED_BROWSER_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
