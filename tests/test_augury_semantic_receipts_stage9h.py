"""Stage 9H: strictly attested, owner-authenticated, model-free comparison."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_receipts as receipts


FP = "sf1_" + "a" * 32
KEY = "ci-private-owner-secret"


def preview():
    return {
        "schema": "gaiaos.augury.semantic-owner-oracle-preview.v1",
        "status": "READY_OWNER_ADJUDICATION",
        "sample_fingerprint": FP,
        "sample_fingerprint_bound": True,
        "records": [
            {"slot": 0, "label": "A", "statement": "PRIVATE SOURCE A"},
            {"slot": 1, "label": "B", "statement": "PRIVATE SOURCE B"},
        ],
        "questions": [
            {"case": 0, "question": "PRIVATE QUESTION 0", "generator_expected_slot": 0},
            {"case": 1, "question": "PRIVATE QUESTION 1", "generator_expected_slot": 1},
            {"case": 2, "question": "PRIVATE QUESTION 2", "generator_expected_slot": 0},
        ],
        "model_called": False, "writes_performed": [],
        "release_activated": False,
    }


CHOICES = [
    {"case": 0, "resolution": "B"},
    {"case": 1, "resolution": "A"},
    {"case": 2, "resolution": "COLLISION"},
]


def owner_receipt():
    result = receipts.owner_from_adjudication(
        sample_fingerprint=FP, questions=preview()["questions"],
        choices=CHOICES,
    )
    assert result is not None
    return result


def model_receipt(*, collision=False):
    positives = [
        (0, "RESOLVED", 1),
        (1, "RESOLVED", 0),
        (2, "COLLISION" if collision else "RESOLVED",
         None if collision else 1),
    ]
    rows = [{
        "case": index, "kind": "current", "resolution": resolution,
        "model_selected_slot": slot,
        "model_candidate_slots": (
            [slot] if resolution == "RESOLVED" else [0, 1]
        ),
        "source_quote_verified": resolution == "RESOLVED",
        "exact_read_ritual_compiled": resolution == "RESOLVED",
        "galaxy_readback_verified": resolution == "RESOLVED",
        "pass": False,
    } for index, resolution, slot in positives]
    rows += [{
        "case": index, "kind": "negative", "resolution": "UNKNOWN",
        "model_selected_slot": None, "model_candidate_slots": [],
        "source_quote_verified": False, "exact_read_ritual_compiled": False,
        "galaxy_readback_verified": False, "pass": True,
    } for index in (3, 4)]
    return {
        "schema": "gaiaos.augury.semantic-read-shadow.v1",
        "status": "HOLD", "sample_fingerprint": FP,
        "sample_fingerprint_bound": True, "case_count": 5,
        "case_results": rows, "model_called": True,
        "legacy_exact_parity": True, "writes_performed": [],
        "release_activated": False,
    }


class StrictReceiptTests(unittest.TestCase):
    def test_owner_choices_attest_b_a_collision_and_expected_slot_membership(self):
        owner = receipts.seal("owner", owner_receipt(), owner_key=KEY)
        self.assertIsNotNone(owner)
        self.assertTrue(receipts.verified("owner", owner, owner_key=KEY))
        self.assertEqual(owner["case_results"][0]["owner_supported_slots"], [1])
        self.assertEqual(owner["case_results"][1]["owner_supported_slots"], [0])
        self.assertEqual(owner["case_results"][2]["owner_supported_slots"], [0, 1])
        self.assertTrue(owner["case_results"][2]["generator_expected_supported"])
        self.assertFalse(
            owner["case_results"][2]["generator_expected_is_unique_owner_answer"]
        )
        for private in ("PRIVATE SOURCE", "PRIVATE QUESTION", KEY):
            self.assertNotIn(private, str(owner))

    def test_signed_model_and_owner_identical_sample_compare_without_effects(self):
        owner = receipts.seal("owner", owner_receipt(), owner_key=KEY)
        model = receipts.seal("model", model_receipt(), owner_key=KEY)
        self.assertIsNotNone(model)
        self.assertTrue(receipts.verified("model", model, owner_key=KEY))
        result = receipts.compare_attested(model, owner, owner_key=KEY)
        self.assertTrue(result["authenticated_redacted_receipts"])
        self.assertTrue(result["sample_match_verified"])
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(
            [x["classification"] for x in result["case_results"]],
            [
                "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED",
                "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED",
                "MODEL_SELECTED_MEMBER_BUT_MISSED_COLLISION",
            ],
        )
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertEqual(result["writes_performed"], [])

    def test_model_collision_matches_owner_collision_but_cannot_release(self):
        model = receipts.seal(
            "model", model_receipt(collision=True), owner_key=KEY,
        )
        owner = receipts.seal("owner", owner_receipt(), owner_key=KEY)
        result = receipts.compare_attested(model, owner, owner_key=KEY)
        self.assertEqual(result["status"], "AGREEMENT_ON_BOUNDED_SAMPLE_ONLY")
        self.assertEqual(
            result["case_results"][2]["classification"],
            "OWNER_MODEL_AGREE_COLLISION_UNVERIFIED",
        )
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertFalse(result["release_activated"])

    def test_missing_modified_extra_private_or_foreign_signatures_hold(self):
        good_owner = receipts.seal("owner", owner_receipt(), owner_key=KEY)
        good_model = receipts.seal("model", model_receipt(), owner_key=KEY)
        bad_owner = dict(good_owner)
        bad_owner.pop("receipt_attestation")
        self.assertEqual(
            receipts.compare_attested(
                good_model, bad_owner, owner_key=KEY
            )["reason"],
            "UNATTESTED_OR_MODIFIED_OWNER_RECEIPT",
        )
        bad_owner = {
            **good_owner,
            "case_results": [dict(row) for row in good_owner["case_results"]],
        }
        bad_owner["case_results"][0]["owner_resolution"] = "A"
        self.assertFalse(receipts.verified("owner", bad_owner, owner_key=KEY))
        bad_owner = {**good_owner, "private_statement": "DO NOT ECHO"}
        self.assertFalse(receipts.verified("owner", bad_owner, owner_key=KEY))
        self.assertNotIn(
            "DO NOT ECHO",
            str(receipts.compare_attested(
                good_model, bad_owner, owner_key=KEY,
            )),
        )
        self.assertFalse(
            receipts.verified("model", good_model, owner_key="other-owner-key")
        )
        changed_model = {**good_model, "sample_fingerprint": "sf1_" + "f" * 32}
        self.assertFalse(receipts.verified("model", changed_model, owner_key=KEY))

    def test_old_unbound_or_fabricated_readback_cannot_be_attested(self):
        old = model_receipt()
        old.pop("sample_fingerprint")
        self.assertIsNone(receipts.seal("model", old, owner_key=KEY))
        fabricated = model_receipt()
        fabricated["case_results"][0]["source_quote_verified"] = False
        self.assertIsNone(receipts.seal("model", fabricated, owner_key=KEY))
        negative = model_receipt()
        negative["case_results"][4]["pass"] = False
        self.assertIsNone(receipts.seal("model", negative, owner_key=KEY))

    def test_owner_choice_shape_fail_closed(self):
        self.assertIsNone(receipts.owner_from_adjudication(
            sample_fingerprint=FP, questions=preview()["questions"],
            choices=[CHOICES[0], CHOICES[0], CHOICES[2]],
        ))
        self.assertIsNone(receipts.owner_from_adjudication(
            sample_fingerprint=FP, questions=preview()["questions"],
            choices=[CHOICES[0], CHOICES[1], {"case": 2, "resolution": "BOTH"}],
        ))


class AuthenticatedReceiptRouteTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        self.carrier = carrier
        self.client = TestClient(carrier.app)
        self.addCleanup(self.client.close)

    def test_finalize_requires_owner_key_and_identical_live_sample(self):
        import augury_semantic_retrieval as shadow
        payload = {
            "expected_sample_fingerprint": FP,
            "choices": CHOICES,
        }
        with patch.object(self.carrier.base, "API_KEY", KEY), patch.object(
            shadow, "owner_oracle_preview", return_value=preview(),
        ) as read, patch("openai.OpenAI") as sdk:
            denied = self.client.post(
                "/gaiaos/memory/augury-semantic-owner-oracle-finalize",
                json=payload,
            )
            self.assertEqual(denied.status_code, 401)
            stale = self.client.post(
                "/gaiaos/memory/augury-semantic-owner-oracle-finalize",
                headers={"Authorization": "Bearer " + KEY},
                json={**payload, "expected_sample_fingerprint": "sf1_" + "f" * 32},
            )
            self.assertEqual(stale.status_code, 409)
            self.assertEqual(stale.json()["reason"], "OWNER_SAMPLE_CHANGED_OR_UNAVAILABLE")
            answer = self.client.post(
                "/gaiaos/memory/augury-semantic-owner-oracle-finalize",
                headers={"Authorization": "Bearer " + KEY},
                json=payload,
            )
            self.assertEqual(answer.status_code, 200, answer.text)
            self.assertEqual(answer.headers["cache-control"], "no-store")
            self.assertTrue(receipts.verified(
                "owner", answer.json(), owner_key=KEY,
            ))
            self.assertNotIn("PRIVATE SOURCE", answer.text)
            self.assertNotIn("PRIVATE QUESTION", answer.text)
            self.assertEqual(read.call_count, 2)
            sdk.assert_not_called()

    def test_compare_route_is_authenticated_no_store_and_model_free(self):
        owner = receipts.seal("owner", owner_receipt(), owner_key=KEY)
        model = receipts.seal("model", model_receipt(), owner_key=KEY)
        endpoint = "/gaiaos/memory/augury-semantic-compare"
        data = {"owner_receipt": owner, "model_receipt": model}
        with patch.object(self.carrier.base, "API_KEY", KEY), patch(
            "openai.OpenAI",
        ) as sdk:
            self.assertEqual(
                self.client.post(endpoint, json=data).status_code, 401,
            )
            result = self.client.post(
                endpoint,
                json=data,
                headers={"Authorization": "Bearer " + KEY},
            )
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.headers["cache-control"], "no-store")
            self.assertEqual(result.json()["status"], "HOLD")
            self.assertTrue(result.json()["authenticated_redacted_receipts"])
            sdk.assert_not_called()
            unsigned = self.client.post(
                endpoint,
                json={**data, "model_receipt": model_receipt()},
                headers={"Authorization": "Bearer " + KEY},
            )
            self.assertEqual(
                unsigned.json()["reason"], "UNATTESTED_OR_MODIFIED_MODEL_RECEIPT",
            )

    def test_served_console_contains_model_free_comparison_controls(self):
        page = self.client.get("/gaiaos/memory/technical-partial-console")
        self.assertEqual(page.status_code, 200)
        for marker in (
            'id="ownerReceiptInput"', 'id="modelReceiptInput"',
            'id="compare"',
            "/gaiaos/memory/augury-semantic-owner-oracle-finalize",
            "/gaiaos/memory/augury-semantic-compare",
        ):
            self.assertIn(marker, page.text)
        self.assertNotIn("PRIVATE SOURCE", page.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
