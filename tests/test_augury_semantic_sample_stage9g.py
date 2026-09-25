"""Stage 9G pure tests: private sample HMAC and category-aware comparison."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_sample as sample


RECORDS = [
    {
        "record_id": "MEM-OWNER-SYNTHETIC-A",
        "statement": "GALAXY relevance is independent of authority.",
        "source": "ci-only-owner-technical",
    },
    {
        "record_id": "MEM-OWNER-SYNTHETIC-B",
        "statement": "GALAXY authority and gravity are independently checked.",
        "source": "ci-only-owner-technical",
    },
]
CASES = [
    {"kind": "current", "query": "Why is relevance independent of authority?",
     "record_id": "MEM-OWNER-SYNTHETIC-A"},
    {"kind": "current", "query": "How is gravity checked?",
     "record_id": "MEM-OWNER-SYNTHETIC-B"},
    {"kind": "current", "query": "How does GALAXY treat gravity?",
     "record_id": "MEM-OWNER-SYNTHETIC-A"},
    {"kind": "negative", "query": "quantum marmalade platypus orchestra"},
    {"kind": "negative", "query": "pineapple telescope opera confetti"},
]


def bound_fingerprint():
    return sample.fingerprint(
        owner_key="ci-strong-private-owner-secret",
        records=RECORDS,
        cases=CASES,
    )


def receipts(*, collision_model=False):
    fp = bound_fingerprint()
    positives = [
        (0, 1, "RESOLVED", [1]),
        (1, 0, "RESOLVED", [0]),
        (2, None if collision_model else 1,
         "COLLISION" if collision_model else "RESOLVED",
         [0, 1] if collision_model else [1]),
    ]
    model = {
        "schema": "gaiaos.augury.semantic-read-shadow.v1",
        "sample_fingerprint": fp, "sample_fingerprint_bound": True,
        "model_called": True, "legacy_exact_parity": True,
        "release_activated": False, "writes_performed": [],
        "case_results": [
            {
                "case": index, "kind": "current", "resolution": resolution,
                "model_selected_slot": slot,
                "model_candidate_slots": candidates,
                "source_quote_verified": resolution == "RESOLVED",
                "exact_read_ritual_compiled": resolution == "RESOLVED",
                "galaxy_readback_verified": resolution == "RESOLVED",
            }
            for index, slot, resolution, candidates in positives
        ] + [
            {"case": index, "kind": "negative", "resolution": "UNKNOWN",
             "model_selected_slot": None, "model_candidate_slots": [],
             "pass": True}
            for index in (3, 4)
        ],
    }
    owner = {
        "schema": "gaiaos.augury.semantic-owner-oracle-redacted.v1",
        "sample_fingerprint": fp, "sample_fingerprint_bound": True,
        "model_called": False, "release_activated": False,
        "writes_performed": [],
        "case_results": [
            {"case": 0, "owner_resolution": "B",
             "owner_supported_slots": [1]},
            {"case": 1, "owner_resolution": "A",
             "owner_supported_slots": [0]},
            {"case": 2, "owner_resolution": "COLLISION",
             "owner_supported_slots": [0, 1]},
        ],
    }
    return model, owner


class SampleFingerprintTests(unittest.TestCase):
    def test_identity_binds_same_ordered_records_and_all_five_cases(self):
        first = bound_fingerprint()
        second = bound_fingerprint()
        self.assertEqual(first, second)
        self.assertRegex(first, r"^sf1_[0-9a-f]{32}$")
        for secret in (
            RECORDS[0]["record_id"], RECORDS[0]["statement"],
            "ci-strong-private-owner-secret",
        ):
            self.assertNotIn(secret, first)

    def test_source_query_order_record_order_and_owner_key_drift_change_identity(self):
        original = bound_fingerprint()
        records = [dict(row) for row in RECORDS]
        records[0]["statement"] += " New clause."
        self.assertNotEqual(original, sample.fingerprint(
            owner_key="ci-strong-private-owner-secret",
            records=records, cases=CASES,
        ))
        records = [dict(row) for row in RECORDS]
        records[0]["source"] = "different-origin"
        self.assertNotEqual(original, sample.fingerprint(
            owner_key="ci-strong-private-owner-secret",
            records=records, cases=CASES,
        ))
        cases = [dict(row) for row in CASES]
        cases[2]["query"] += " Exactly?"
        self.assertNotEqual(original, sample.fingerprint(
            owner_key="ci-strong-private-owner-secret",
            records=RECORDS, cases=cases,
        ))
        self.assertNotEqual(original, sample.fingerprint(
            owner_key="ci-strong-private-owner-secret",
            records=list(reversed(RECORDS)), cases=CASES,
        ))
        self.assertNotEqual(original, sample.fingerprint(
            owner_key="rotated-ci-private-owner-secret",
            records=RECORDS, cases=CASES,
        ))

    def test_fail_closed_unbound_or_wrong_shaped_material(self):
        self.assertIsNone(sample.fingerprint(
            owner_key=None, records=RECORDS, cases=CASES,
        ))
        self.assertIsNone(sample.fingerprint(
            owner_key="ci-private", records=RECORDS[:1], cases=CASES,
        ))
        wrong = [dict(row) for row in CASES]
        wrong[3]["record_id"] = RECORDS[0]["record_id"]
        self.assertIsNone(sample.fingerprint(
            owner_key="ci-private", records=RECORDS, cases=wrong,
        ))


class RedactedOracleComparisonTests(unittest.TestCase):
    def test_first_two_agree_third_single_answer_misses_collision(self):
        model, owner = receipts()
        result = sample.compare_redacted(model, owner)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["sample_match_verified"])
        self.assertEqual(
            [x["classification"] for x in result["case_results"]],
            [
                "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED",
                "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED",
                "MODEL_SELECTED_MEMBER_BUT_MISSED_COLLISION",
            ],
        )
        self.assertFalse(result["categorical_agreement_proven"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertFalse(result["release_activated"])

    def test_collision_matches_collision_without_claiming_entailment(self):
        model, owner = receipts(collision_model=True)
        result = sample.compare_redacted(model, owner)
        self.assertEqual(result["status"], "AGREEMENT_ON_BOUNDED_SAMPLE_ONLY")
        self.assertTrue(result["categorical_agreement_proven"])
        self.assertEqual(
            result["case_results"][2]["classification"],
            "OWNER_MODEL_AGREE_COLLISION_UNVERIFIED",
        )
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertIn("HOLD", result["full_readiness_status"])
        self.assertEqual(result["writes_performed"], [])

    def test_old_unbound_receipts_and_changed_samples_cannot_be_compared(self):
        model, owner = receipts()
        model.pop("sample_fingerprint")
        self.assertEqual(
            sample.compare_redacted(model, owner)["reason"],
            "UNBOUND_OR_DIFFERENT_SAMPLE",
        )
        model, owner = receipts()
        owner["sample_fingerprint"] = "sf1_" + "f" * 32
        self.assertEqual(
            sample.compare_redacted(model, owner)["reason"],
            "UNBOUND_OR_DIFFERENT_SAMPLE",
        )

    def test_invalid_support_set_negative_or_source_readback_fails_closed(self):
        model, owner = receipts()
        owner["case_results"][2]["owner_supported_slots"] = []
        self.assertEqual(
            sample.compare_redacted(model, owner)["reason"],
            "OWNER_SUPPORT_SET_INVALID",
        )
        model, owner = receipts()
        model["case_results"][4]["pass"] = False
        self.assertEqual(
            sample.compare_redacted(model, owner)["reason"],
            "NEGATIVE_CONTROLS_UNVERIFIED",
        )
        model, owner = receipts()
        model["case_results"][0]["source_quote_verified"] = False
        self.assertEqual(
            sample.compare_redacted(model, owner)["reason"],
            "MODEL_SOURCE_READBACK_UNVERIFIED",
        )

    def test_comparison_never_echoes_source_or_key_and_never_calls_model(self):
        model, owner = receipts()
        result = sample.compare_redacted(model, owner)
        payload = str(result)
        for secret in (
            "ci-strong-private-owner-secret",
            RECORDS[0]["record_id"],
            RECORDS[0]["statement"],
            CASES[0]["query"],
        ):
            self.assertNotIn(secret, payload)
        self.assertFalse(result["model_called"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
