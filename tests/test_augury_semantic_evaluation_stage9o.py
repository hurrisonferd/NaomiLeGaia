"""Stage9O: no new model calls; only existing HMAC-attested owner labels."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_receipts as receipts
import augury_semantic_evaluation as evaluation

FP = "sf1_" + "a" * 32
KEY = "synthetic-owner-ci-key-not-a-production-credential"
QUESTIONS = [
    {"case": 0, "generator_expected_slot": 0},
    {"case": 1, "generator_expected_slot": 1},
    {"case": 2, "generator_expected_slot": 0},
]
CHOICES = [
    {"case": 0, "resolution": "B"},
    {"case": 1, "resolution": "A"},
    {"case": 2, "resolution": "COLLISION"},
]


def owner():
    raw = receipts.owner_from_adjudication(
        sample_fingerprint=FP, questions=QUESTIONS, choices=CHOICES,
    )
    assert raw is not None
    signed = receipts.seal("owner", raw, owner_key=KEY)
    assert signed is not None
    return signed


def model(*, collision=False):
    rows = []
    for index, slot in ((0, 1), (1, 0), (2, 0)):
        resolution = "COLLISION" if collision and index == 2 else "RESOLVED"
        chosen = None if resolution == "COLLISION" else slot
        rows.append({
            "case": index, "kind": "current",
            "resolution": resolution,
            "model_selected_slot": chosen,
            "model_candidate_slots": [0, 1] if chosen is None else [chosen],
            "source_quote_verified": chosen is not None,
            "exact_read_ritual_compiled": chosen is not None,
            "galaxy_readback_verified": chosen is not None,
            "pass": False,
        })
    for index in (3, 4):
        rows.append({
            "case": index, "kind": "negative",
            "resolution": "UNKNOWN", "model_selected_slot": None,
            "model_candidate_slots": [],
            "source_quote_verified": False,
            "exact_read_ritual_compiled": False,
            "galaxy_readback_verified": False, "pass": True,
        })
    raw = {
        "schema": "gaiaos.augury.semantic-read-shadow.v1",
        "status": "HOLD", "sample_fingerprint": FP,
        "sample_fingerprint_bound": True, "case_count": 5,
        "case_results": rows, "model_called": True,
        "legacy_exact_parity": True,
        "historical_coverage": False,
        "general_semantic_quality_proven": False,
        "writes_performed": [], "release_activated": False,
    }
    signed = receipts.seal("model", raw, owner_key=KEY)
    assert signed is not None
    return signed


class Stage9OAuditTests(unittest.TestCase):
    def test_existing_owner_compare_returns_bounded_aggregate_no_extra_action(self):
        report = receipts.compare_attested(model(), owner(), owner_key=KEY)
        self.assertTrue(report["authenticated_redacted_receipts"])
        self.assertEqual(report["status"], "HOLD")
        audit = report["owner_labeled_audit"]
        self.assertEqual(audit["schema"], evaluation.SCHEMA)
        self.assertEqual(audit["status"], "BOUNDED_OWNER_LABELS_CLASSIFIED")
        self.assertEqual(audit["owner_labeled_current_cases"], 3)
        self.assertEqual(audit["attested_negative_controls"], 2)
        self.assertEqual(audit["owner_single_source_cases"], 2)
        self.assertEqual(audit["owner_collision_cases"], 1)
        self.assertEqual(audit["owner_unknown_cases"], 0)
        self.assertEqual(audit["owner_model_categorical_agreements"], 2)
        self.assertEqual(audit["owner_model_categorical_disagreements"], 1)
        self.assertEqual(audit["single_source_grounded_agreements"], 2)
        self.assertEqual(audit["model_missed_owner_collision"], 1)
        self.assertEqual(audit["collision_claim_agreements_unverified"], 0)
        self.assertEqual(audit["owner_generator_supported_cases"], 1)
        self.assertEqual(audit["owner_generator_unique_correct_cases"], 0)
        self.assertEqual(audit["new_owner_cases_added"], 0)
        self.assertFalse(audit["independent_semantic_entailment_proven"])
        self.assertFalse(audit["general_semantic_quality_proven"])
        self.assertFalse(audit["historical_retrieval_proven"])
        self.assertFalse(audit["release_activated"])
        self.assertEqual(audit["writes_performed"], [])
        self.assertFalse(audit["model_called_now"])

    def test_colliding_prediction_agrees_categorically_but_cannot_prove_meaning(self):
        report = receipts.compare_attested(
            model(collision=True), owner(), owner_key=KEY,
        )
        self.assertEqual(report["status"], "AGREEMENT_ON_BOUNDED_SAMPLE_ONLY")
        audit = report["owner_labeled_audit"]
        self.assertEqual(audit["owner_model_categorical_agreements"], 3)
        self.assertEqual(audit["owner_model_categorical_disagreements"], 0)
        self.assertEqual(audit["collision_claim_agreements_unverified"], 1)
        self.assertFalse(audit["independent_semantic_entailment_proven"])
        self.assertFalse(audit["general_semantic_quality_proven"])

    def test_tampered_key_unsigned_and_foreign_sample_never_get_audit(self):
        baseline = model()
        trusted = owner()
        no_signature = copy.deepcopy(trusted)
        del no_signature["receipt_attestation"]
        changed = copy.deepcopy(trusted)
        changed["case_results"][0]["owner_resolution"] = "A"
        foreign = copy.deepcopy(trusted)
        foreign["sample_fingerprint"] = "sf1_" + "f" * 32
        for candidate in (no_signature, changed, foreign):
            result = receipts.compare_attested(
                baseline, candidate, owner_key=KEY,
            )
            self.assertEqual(result["status"], "HOLD")
            self.assertNotIn("owner_labeled_audit", result)
        wrong_key = receipts.compare_attested(
            baseline, trusted, owner_key="wrong-key",
        )
        self.assertNotIn("owner_labeled_audit", wrong_key)

    def test_read_only_output_never_copies_private_or_secret_fields(self):
        signed_owner = owner()
        signed_model = model()
        signed_owner["private_statement"] = "DO NOT LEAK"
        report = receipts.compare_attested(
            signed_model, signed_owner, owner_key=KEY,
        )
        self.assertNotIn("owner_labeled_audit", report)
        self.assertNotIn("DO NOT LEAK", str(report))
        self.assertNotIn(KEY, str(report))
        good = receipts.compare_attested(
            signed_model, owner(), owner_key=KEY,
        )
        self.assertNotIn(KEY, str(good))
        self.assertNotIn("receipt_attestation", good["owner_labeled_audit"])
        self.assertNotIn("sample_fingerprint", good["owner_labeled_audit"])

    def test_direct_malformed_comparison_holds_without_echo(self):
        fake = {"schema": "junk", "case_results": ["PRIVATE"]}
        report = evaluation.audit(fake, model(), owner())
        self.assertEqual(report["status"], "HOLD_UNVERIFIED_RECEIPT_PAIR")
        self.assertNotIn("PRIVATE", str(report))
        self.assertFalse(report["release_activated"])


if __name__ == "__main__":
    unittest.main()
