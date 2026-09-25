"""Stage 9I offline dual-source COLLISION proof with no provider or writes."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_collision as collision
import augury_semantic_receipts as receipts
import augury_semantic_retrieval as shadow
import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode
from test_augury_semantic_retrieval_stage9f import FakeStore, cases

KEY = "ci-fake-private-owner-key"
QUOTE_A = "GALAXY separates relevance from gravity"
QUOTE_B = "GALAXY preserves owner authority independently"


class TwoSourceCollisionTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeStore()
        self.prepared = {
            "preview": {
                "status": "HOLD",
                "reason": "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES",
            },
            "cases": [], "partial_cases": cases(),
        }
        self.control = {
            "schema": mode.SCHEMA,
            "effective_mode": mode.HEATDEATH,
            "configured_mode": mode.HEATDEATH,
            "control_version": "ci-only",
            "bigbang_activation_enabled": False,
        }
        self.baseline = {
            "status": "PASS_HEATDEATH",
            "retrieval": {
                "records": [], "count": 0, "scope_applied": "MemoryOS",
                "query_terms_applied": [], "query_filter_active": True,
                "runtime": "ci-only",
            },
        }
        with patch.object(
            readiness, "prepare_technical_cases", return_value=self.prepared,
        ), patch.object(
            mode, "mode_status", return_value=self.control,
        ):
            preview = shadow.owner_oracle_preview(
                self.runtime, fingerprint_key=KEY,
            )
        self.assertEqual(preview["status"], "READY_OWNER_ADJUDICATION")
        self.fp = preview["sample_fingerprint"]
        unsigned = receipts.owner_from_adjudication(
            sample_fingerprint=self.fp,
            questions=preview["questions"],
            choices=[
                {"case": 0, "resolution": "COLLISION"},
                {"case": 1, "resolution": "B"},
                {"case": 2, "resolution": "A"},
            ],
        )
        self.owner = receipts.seal("owner", unsigned, owner_key=KEY)
        self.assertTrue(receipts.verified("owner", self.owner, owner_key=KEY))

    def run_review(
        self, *,
        owner=None, case_index=0,
        quote_a=QUOTE_A, quote_b=QUOTE_B,
        packet_kind="valid", after=None, compile_kind="valid",
    ):
        calls = []

        def operational(runtime, query, limit):
            self.assertIs(runtime, self.runtime)
            self.assertEqual(limit, 4)
            calls.append(query)
            target = ("real-one", "real-two")[len(calls) - 1]
            if packet_kind == "missing_second" and len(calls) == 2:
                target = "real-one"
            return {
                "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                "records": [{"record": {"record_id": target}}],
            }

        compile_results = iter(
            ["ci-strict-concepts-a", "ci-strict-concepts-b"]
            if compile_kind == "valid" else [None],
        )
        with patch.object(
            readiness, "prepare_technical_cases", return_value=self.prepared,
        ), patch.object(
            mode, "mode_status", return_value=self.control,
        ), patch.object(
            gateway, "read", side_effect=[self.baseline, after or self.baseline],
        ) as legacy, patch.object(
            gateway, "_validated_legacy", return_value=True,
        ), patch.object(
            gateway, "_galaxy_valid", return_value=True,
        ), patch.object(
            shadow, "_compile_read_only_query",
            side_effect=lambda *a: next(compile_results),
        ) as compiler, patch(
            "galaxy_frontdoor_context.operational", side_effect=operational,
        ) as reader, patch("openai.OpenAI") as model:
            result = collision.review(
                self.runtime, owner_receipt=owner or self.owner,
                case_index=case_index, quote_a=quote_a,
                quote_b=quote_b, fingerprint_key=KEY,
            )
            model.assert_not_called()
        return result, compiler, reader, legacy

    def test_signed_owner_collision_two_exact_source_readbacks(self):
        result, compiler, reader, legacy = self.run_review()
        self.assertEqual(result["status"], collision.PASS, result)
        self.assertEqual(result["sample_fingerprint"], self.fp)
        self.assertEqual(result["quote_exact_verified"], [True, True])
        self.assertEqual(result["strict_literal_compiled"], [True, True])
        self.assertEqual(result["galaxy_readback_verified"], [True, True])
        self.assertTrue(result["owner_receipt_verified"])
        self.assertTrue(result["legacy_exact_parity"])
        self.assertFalse(result["collision_entailment_independently_proven"])
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertFalse(result["historical_coverage"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["model_called"])
        self.assertEqual(compiler.call_count, 2)
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(legacy.call_count, 2)
        self.assertEqual(compiler.call_args_list[0].args[2], QUOTE_A)
        self.assertEqual(compiler.call_args_list[1].args[2], QUOTE_B)
        signed = receipts.seal("collision", result, owner_key=KEY)
        self.assertTrue(receipts.verified("collision", signed, owner_key=KEY))
        for secret in (
            KEY, "real-one", "real-two", QUOTE_A, QUOTE_B,
        ):
            self.assertNotIn(secret, str(result))
            self.assertNotIn(secret, str(signed))

    def test_modified_attestation_and_unsigned_owner_rejected_before_read(self):
        unsigned = {
            k: v for k, v in self.owner.items()
            if k != "receipt_attestation"
        }
        result, compiler, reader, legacy = self.run_review(owner=unsigned)
        self.assertEqual(result["reason"], "SIGNED_OWNER_COLLISION_REQUIRED")
        self.assertEqual(compiler.call_count, 0)
        self.assertEqual(reader.call_count, 0)
        self.assertEqual(legacy.call_count, 0)

    def test_owner_must_have_selected_collision_on_exact_case(self):
        result, compiler, reader, legacy = self.run_review(case_index=1)
        self.assertEqual(result["reason"], "OWNER_COLLISION_NOT_ADJUDICATED")
        self.assertEqual(reader.call_count, 0)
        self.assertEqual(legacy.call_count, 0)

    def test_fabricated_quote_fails_before_literal_compile(self):
        result, compiler, reader, legacy = self.run_review(
            quote_b="Invented text not present in approved statement",
        )
        self.assertEqual(result["reason"], "QUOTE_NOT_EXACT_APPROVED_SOURCE")
        self.assertEqual(reader.call_count, 0)
        self.assertEqual(legacy.call_count, 0)
        self.assertIsNone(receipts.seal("collision", result, owner_key=KEY))

    def test_source_drift_fails_before_readback(self):
        self.runtime.records[0]["statement"] += " This statement was changed."
        result, compiler, reader, legacy = self.run_review()
        self.assertEqual(
            result["reason"], "SIGNED_OWNER_SAMPLE_CHANGED_OR_UNAVAILABLE",
        )
        self.assertEqual(reader.call_count, 0)

    def test_unchanged_quote_but_strict_compiler_rejects(self):
        result, compiler, reader, legacy = self.run_review(
            compile_kind="reject",
        )
        self.assertEqual(
            result["reason"], "STRICT_TWO_CONCEPT_QUOTE_COMPILATION_HOLD",
        )
        self.assertEqual(compiler.call_count, 1)
        self.assertEqual(reader.call_count, 0)

    def test_one_missing_record_does_not_count_as_both(self):
        result, compiler, reader, legacy = self.run_review(
            packet_kind="missing_second",
        )
        self.assertEqual(
            result["reason"], "EXACT_SOURCE_RECORD_NOT_RETRIEVED",
        )
        self.assertEqual(reader.call_count, 2)
        self.assertIsNone(receipts.seal("collision", result, owner_key=KEY))

    def test_legacy_parity_regression_forces_hold(self):
        changed = {
            **self.baseline,
            "retrieval": {**self.baseline["retrieval"], "count": 1},
        }
        result, compiler, reader, legacy = self.run_review(after=changed)
        self.assertEqual(result["reason"], "LEGACY_PARITY_OR_RELEASE_LOCK_CHANGED")
        self.assertEqual(reader.call_count, 2)
        self.assertFalse(result["release_activated"])

    def test_signature_refuses_bool_as_integer_and_extra_private_text(self):
        result, *_ = self.run_review()
        proof = receipts.seal("collision", result, owner_key=KEY)
        tampered = dict(proof)
        tampered["case"] = True
        self.assertFalse(
            receipts.verified("collision", tampered, owner_key=KEY),
        )
        leaked = {**proof, "private_quote": QUOTE_A}
        self.assertFalse(receipts.verified("collision", leaked, owner_key=KEY))
        proof["receipt_attestation"]["mac"] = "ra1_" + "f" * 64
        self.assertFalse(receipts.verified("collision", proof, owner_key=KEY))


class CollisionRouteTests(unittest.TestCase):
    def test_owner_auth_no_store_no_openai_call_and_no_private_text_return(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        unsigned = {
            "schema": collision.SCHEMA, "status": collision.PASS,
            "case": 0, "sample_fingerprint": "sf1_" + "a" * 32,
            "sample_fingerprint_bound": True, "owner_receipt_verified": True,
            "quote_exact_verified": [True, True],
            "strict_literal_compiled": [True, True],
            "galaxy_readback_verified": [True, True],
            "legacy_exact_parity": True,
            "collision_entailment_independently_proven": False,
            "general_semantic_quality_proven": False,
            "historical_coverage": False,
            "full_readiness_status":
                "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
            "model_called": False, "writes_performed": [],
            "e_lanes_modified": False, "release_activated": False,
        }
        request = {
            "owner_receipt": {"fake": "owner"},
            "case": 0, "quote_a": QUOTE_A, "quote_b": QUOTE_B,
        }
        with patch.object(
            carrier.base, "API_KEY", KEY,
        ), patch.object(
            collision, "review", return_value=unsigned,
        ) as core, patch("openai.OpenAI") as sdk:
            denied = client.post(
                "/gaiaos/memory/augury-collision-two-source-shadow",
                json=request,
            )
            self.assertEqual(denied.status_code, 401)
            allowed = client.post(
                "/gaiaos/memory/augury-collision-two-source-shadow",
                json=request,
                headers={"Authorization": "Bearer " + KEY},
            )
            self.assertEqual(allowed.status_code, 200, allowed.text)
            self.assertEqual(allowed.headers["cache-control"], "no-store")
            self.assertTrue(receipts.verified(
                "collision", allowed.json(), owner_key=KEY,
            ))
            self.assertEqual(
                core.call_args.kwargs["fingerprint_key"], KEY,
            )
            sdk.assert_not_called()
            self.assertNotIn(QUOTE_A, allowed.text)
            self.assertNotIn(QUOTE_B, allowed.text)
            self.assertNotIn(KEY, allowed.text)

    def test_existing_console_exposes_dual_source_panel_and_button(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        with TestClient(carrier.app) as client:
            page = client.get("/gaiaos/memory/technical-partial-console")
        self.assertEqual(page.status_code, 200)
        for marker in (
            'id="collisionPanel"', 'id="collisionCase"',
            'id="collisionQuoteA"', 'id="collisionQuoteB"',
            'id="collisionVerify"',
            "/gaiaos/memory/augury-collision-two-source-shadow",
        ):
            self.assertIn(marker, page.text)
        self.assertNotIn(QUOTE_A, page.text)
        self.assertNotIn(QUOTE_B, page.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
