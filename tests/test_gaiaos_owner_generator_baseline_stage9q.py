"""Stage9Q: bounded owner-generator labels after signed Stage9P replay."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import gaiaos_owner_generator_baseline as baseline
import gaiaos_owner_evidence_replay as replay
import gaiaos_one_click_readiness as oneclick
import gaiaos_memory_mode as mode

import test_gaiaos_owner_evidence_replay_stage9p as prior


class OwnerGeneratorBaselineTests(unittest.TestCase):
    def test_signed_owner_labels_vs_generator_targets_not_model_accuracy(self):
        owner = prior.owner_receipt()
        self.assertTrue(
            __import__("augury_semantic_receipts").verified(
                "owner", owner, owner_key=prior.KEY
            )
        )
        result = baseline.classify_verified_owner_receipt(owner)
        self.assertEqual(result["status"], baseline.STATUS)
        self.assertEqual(result["owner_labeled_current_cases"], 3)
        self.assertEqual(result["owner_collision_cases"], 1)
        self.assertEqual(result["owner_unknown_cases"], 0)
        self.assertEqual(result["generator_unique_owner_support"], 0)
        self.assertEqual(result["generator_nonunique_owner_support"], 1)
        self.assertEqual(result["generator_not_owner_supported"], 2)
        self.assertEqual(result["negative_controls_owner_adjudicated"], 0)
        for key in (
            "model_receipt_compared", "independent_entailment_proven",
            "general_semantic_quality_proven", "historical_retrieval_proven",
            "model_called", "e_lanes_modified", "release_activated",
        ):
            self.assertIs(result[key], False)
        self.assertEqual(result["writes_performed"], [])
        self.assertNotIn(prior.KEY, str(result))
        self.assertNotIn(prior.FP, str(result))

    def test_collision_support_is_never_unique_correctness(self):
        item = prior.owner_receipt()
        result = baseline.classify_verified_owner_receipt(item)
        self.assertEqual(result["generator_nonunique_owner_support"], 1)
        self.assertEqual(result["generator_unique_owner_support"], 0)
        self.assertFalse(result["independent_entailment_proven"])

    def test_unknown_is_not_mistaken_for_generator_mismatch(self):
        owner = prior.owner_receipt()
        item = owner["case_results"][1]
        item.update({
            "owner_resolution": "UNKNOWN", "owner_slot": None,
            "owner_supported_slots": [],
            "generator_expected_supported": False,
            "generator_expected_is_unique_owner_answer": False,
        })
        result = baseline.classify_verified_owner_receipt(owner)
        self.assertEqual(result["status"], baseline.STATUS)
        self.assertEqual(result["owner_unknown_cases"], 1)
        self.assertEqual(result["generator_not_owner_supported"], 1)

    def test_malformed_owner_shapes_hold_without_echoing_input(self):
        owner = prior.owner_receipt()
        variations = []
        malformed = copy.deepcopy(owner)
        malformed["case_results"][0]["owner_supported_slots"] = [0]
        variations.append(malformed)
        malformed = copy.deepcopy(owner)
        malformed["case_results"][1]["generator_expected_supported"] = True
        variations.append(malformed)
        malformed = copy.deepcopy(owner)
        malformed["case_results"].reverse()
        variations.append(malformed)
        malformed = copy.deepcopy(owner)
        malformed["case_results"][2]["generator_expected_is_unique_owner_answer"] = True
        variations.append(malformed)
        malformed = copy.deepcopy(owner)
        malformed["model_called"] = True
        variations.append(malformed)
        malformed = copy.deepcopy(owner)
        malformed["case_results"][0]["generator_expected_slot"] = True
        variations.append(malformed)
        for item in variations:
            with self.subTest(item=item["case_results"]):
                result = baseline.classify_verified_owner_receipt(item)
                self.assertEqual(result["status"], "HOLD")
                self.assertNotIn("owner_labeled_current_cases", result)
                self.assertNotIn(prior.FP, str(result))
                self.assertEqual(result["writes_performed"], [])

    def test_replay_inherits_hmac_fingerprint_and_heatdeath_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / replay._OWNER_FILE).write_text(
                json.dumps(prior.owner_receipt()), encoding="utf-8"
            )
            (folder / replay._COLLISION_FILE).write_text(
                json.dumps(prior.collision_receipt()), encoding="utf-8"
            )
            with patch.object(mode, "mode_status", return_value=prior.CONTROL):
                good = replay.audit(
                    prior.NeverWriteStore(), owner_key=prior.KEY,
                    proof_directory=folder, preview_fn=prior.preview,
                )
            self.assertEqual(
                good["owner_generator_baseline"]["status"], baseline.STATUS
            )
            self.assertEqual(good["status"],
                             "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE")
            self.assertNotIn(prior.KEY, str(good))
            self.assertNotIn(prior.FP, str(good))
            with patch.object(mode, "mode_status", return_value=prior.CONTROL):
                wrong = replay.audit(
                    prior.NeverWriteStore(), owner_key="rotated-key",
                    proof_directory=folder, preview_fn=prior.preview,
                )
            self.assertEqual(wrong["status"], "HOLD")
            self.assertNotIn("owner_generator_baseline", wrong)
            def drift(_runtime, *, fingerprint_key):
                output = prior.preview(_runtime, fingerprint_key=fingerprint_key)
                output["sample_fingerprint"] = "sf1_" + "b" * 32
                return output
            with patch.object(mode, "mode_status", return_value=prior.CONTROL):
                changed = replay.audit(
                    prior.NeverWriteStore(), owner_key=prior.KEY,
                    proof_directory=folder, preview_fn=drift,
                )
            self.assertEqual(changed["reason"], "ARCHIVED_SAMPLE_NOT_CURRENT")
            self.assertNotIn("owner_generator_baseline", changed)
            unsafe = {**prior.CONTROL, "bigbang_activation_enabled": True}
            with patch.object(mode, "mode_status", return_value=unsafe):
                locked = replay.audit(
                    prior.NeverWriteStore(), owner_key=prior.KEY,
                    proof_directory=folder, preview_fn=prior.preview,
                )
            self.assertEqual(
                locked["reason"], "HEATDEATH_RELEASE_LOCK_UNVERIFIED"
            )
            self.assertNotIn("owner_generator_baseline", locked)

    def test_server_allowlist_drops_private_fields_and_holds_bad_counts(self):
        raw = baseline.classify_verified_owner_receipt(prior.owner_receipt())
        clean = oneclick._owner_generator_baseline({
            **raw, "PRIVATE_SENTENCE": "DO_NOT_EXPOSE"
        })
        self.assertEqual(clean["status"], baseline.STATUS)
        self.assertNotIn("DO_NOT_EXPOSE", str(clean))
        self.assertNotIn(prior.FP, str(clean))
        bad = oneclick._owner_generator_baseline({
            **raw, "generator_unique_owner_support": 3
        })
        self.assertEqual(bad["status"], "HOLD")
        bad = oneclick._owner_generator_baseline({
            **raw, "model_called": True
        })
        self.assertEqual(bad["status"], "HOLD")

    def test_existing_oneclick_nested_shape_preserves_six_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / replay._OWNER_FILE).write_text(
                json.dumps(prior.owner_receipt()), encoding="utf-8"
            )
            (folder / replay._COLLISION_FILE).write_text(
                json.dumps(prior.collision_receipt()), encoding="utf-8"
            )
            with patch.object(mode, "mode_status", return_value=prior.CONTROL):
                source = replay.audit(
                    prior.NeverWriteStore(), owner_key=prior.KEY,
                    proof_directory=folder, preview_fn=prior.preview,
                )
        result = oneclick._owner_evidence_replay(source)
        self.assertEqual(
            result["owner_generator_baseline"]["status"], baseline.STATUS
        )
        self.assertFalse(result["model_comparison_performed"])
        self.assertNotIn("PRIVATE_", str(result))
        bad = copy.deepcopy(source)
        bad["owner_generator_baseline"]["model_called"] = True
        nested = oneclick._owner_evidence_replay(bad)
        self.assertEqual(nested["status"],
                         "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE")
        self.assertEqual(nested["owner_generator_baseline"]["status"], "HOLD")
        self.assertFalse(nested["semantic_entailment_independently_proven"])

    def test_actual_served_oneclick_browser_good_and_tampered_nested_payload(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        from test_gaiaos_one_click_stage9l import (
            BROWSER_HARNESS, OneClickSuiteTests, PAGE,
        )
        from test_gaiaos_console_browser_contract import ConsoleHTMLParser
        self.assertIsNotNone(shutil.which("node"), "Node is required by CI")
        with TestClient(carrier.app) as client:
            page = client.get(PAGE)
        self.assertEqual(page.status_code, 200)
        parser = ConsoleHTMLParser()
        parser.feed(page.text)
        self.assertEqual(set(parser.buttons), {"run", "copy"})
        self.assertEqual(len(parser.scripts), 1)

        fixture = OneClickSuiteTests()
        fixture.setUp()
        report, *_ = fixture.run_fixture()
        owner = prior.owner_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / replay._OWNER_FILE).write_text(
                json.dumps(owner), encoding="utf-8"
            )
            (folder / replay._COLLISION_FILE).write_text(
                json.dumps(prior.collision_receipt()), encoding="utf-8"
            )
            with patch.object(mode, "mode_status", return_value=prior.CONTROL):
                replayed = replay.audit(
                    prior.NeverWriteStore(), owner_key=prior.KEY,
                    proof_directory=folder, preview_fn=prior.preview,
                )
        visible = oneclick._owner_evidence_replay(replayed)
        report["checks"]["current_literal_readback"]["owner_evidence_replay"] = {
            **visible, "PRIVATE_PAYLOAD": "DO_NOT_EXPOSE"
        }
        before = ' process.stdout.write("STAGE9L_ONE_CLICK_BROWSER_PASS\\n");'
        after = """
 assert.equal(
  copiedJSON.checks.current_literal_readback.owner_evidence_replay
   .owner_generator_baseline.status,
  "BOUNDED_OWNER_GENERATOR_BASELINE_ONLY"
 );
 const b=copiedJSON.checks.current_literal_readback
  .owner_evidence_replay.owner_generator_baseline;
 assert.equal(b.generator_unique_owner_support,0);
 assert.equal(b.generator_nonunique_owner_support,1);
 assert.equal(b.generator_not_owner_supported,2);
 assert.equal(b.negative_controls_owner_adjudicated,0);
 assert.equal(b.model_receipt_compared,false);
 response={...fixture,checks:{...fixture.checks,
  current_literal_readback:{...fixture.checks.current_literal_readback,
   owner_evidence_replay:{...fixture.checks.current_literal_readback
    .owner_evidence_replay,
    owner_generator_baseline:{...b,generator_unique_owner_support:3}}}}};
 await events.run();
 assert.equal(nodes.copy.disabled,true,"Contradictory nested counts must not copy");
 assert.ok(!nodes.report.textContent.includes("DO_NOT_EXPOSE"));
 process.stdout.write("STAGE9Q_NESTED_BROWSER_PASS\\n");
""" + before
        self.assertIn(before, BROWSER_HARNESS)
        harness = BROWSER_HARNESS.replace(before, after)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "served.js").write_text(
                parser.scripts[0][1], encoding="utf-8"
            )
            (folder / "fixture.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            (folder / "harness.js").write_text(harness, encoding="utf-8")
            finished = subprocess.run(
                ["node", str(folder / "harness.js"),
                 str(folder / "served.js"), str(folder / "fixture.json")],
                capture_output=True, text=True, timeout=20,
            )
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertIn("STAGE9Q_NESTED_BROWSER_PASS", finished.stdout)


if __name__ == "__main__":
    unittest.main()
