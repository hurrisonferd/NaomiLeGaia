"""Offline Stage 9F: source-grounded AUGURY shadow, no API charges or writes."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import augury_semantic_retrieval as shadow
import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode
import memcon_runtime


class FakeStore:
    _INITIALIZED = True
    GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS = set()

    def __init__(self):
        self.records = [
            {
                "record_id": "real-one", "scope": "MemoryOS",
                "authority": "NAOMI", "status": "ACTIVE",
                "source": "owner-review", "statement":
                "GALAXY separates relevance from gravity in read-only retrieval.",
            },
            {
                "record_id": "real-two", "scope": "MemoryOS",
                "authority": "NAOMI", "status": "ACTIVE",
                "source": "owner-review", "statement":
                "GALAXY preserves owner authority independently of relevance weighting.",
            },
        ]
        self._galaxy_query_tokens = memcon_runtime._galaxy_query_tokens
        self._galaxy_query_concept = memcon_runtime._galaxy_query_concept

    def get_record(self, rid):
        row = next((row for row in self.records if row["record_id"] == rid), None)
        return dict(row) if row else None

    def galaxy_governing_state(self, rid):
        return {"record_id": rid, "current_default_eligible": True}

    def search_records(self, query, limit, scope):
        if (query, limit, scope) != ("", 100, "MemoryOS"):
            raise AssertionError("The semantic shadow broadened retrieval")
        return {"records": [dict(r) for r in self.records], "scope_applied": scope}


def cases():
    return [
        {"kind": "current", "query": "Why is relevance not gravity?",
         "record_id": "real-one"},
        {"kind": "current", "query": "What happens to owner authority?",
         "record_id": "real-two"},
        {"kind": "current", "query": "Explain the separation of relevance",
         "record_id": "real-one"},
        {"kind": "negative", "query": "quantum marmalade platypus orchestra"},
        {"kind": "negative", "query": "pineapple telescope opera confetti"},
    ]


def decisions():
    return {"cases": [
        {"case": 0, "resolution": "RESOLVED", "slot": 0,
         "support_quote": "relevance from gravity"},
        {"case": 1, "resolution": "RESOLVED", "slot": 1,
         "support_quote": "owner authority independently"},
        {"case": 2, "resolution": "RESOLVED", "slot": 0,
         "support_quote": "GALAXY separates relevance"},
        {"case": 3, "resolution": "UNKNOWN", "slot": None,
         "support_quote": None},
        {"case": 4, "resolution": "UNKNOWN", "slot": None,
         "support_quote": None},
    ]}


class SemanticShadowTests(unittest.TestCase):
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
            "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
            "configured_mode": mode.HEATDEATH,
            "control_version": "ci-only", "bigbang_activation_enabled": False,
        }
        self.baseline = {
            "status": "PASS_HEATDEATH", "retrieval": {
                "records": [], "count": 0, "scope_applied": "MemoryOS",
                "query_terms_applied": [], "query_filter_active": True,
                "runtime": "ci-only",
            },
        }

    def run_review(self, model_result=None, *, packet_kind="valid"):
        chosen = decisions() if model_result is None else model_result
        slot_ids = ("real-one", "real-two")
        responses = iter(
            slot_ids[item["slot"]]
            for item in chosen.get("cases", [])[:3]
            if item.get("resolution") == "RESOLVED"
            and item.get("slot") in (0, 1)
        )

        def operational(runtime, query, limit):
            self.assertIs(runtime, self.runtime)
            self.assertEqual(limit, 4)
            if packet_kind == "missing":
                return {"status": "HOLD_NO_CONFIDENT_GALAXY_MATCH",
                        "records": []}
            return {
                "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                "records": [{"record": {"record_id": next(responses)}}],
            }

        with patch.object(readiness, "prepare_technical_cases",
                          return_value=self.prepared), patch.object(
            mode, "mode_status", return_value=self.control
        ), patch.object(
            gateway, "read", return_value=self.baseline
        ), patch.object(
            gateway, "_validated_legacy", return_value=True
        ), patch.object(
            gateway, "_galaxy_valid", return_value=packet_kind != "missing"
        ), patch("galaxy_frontdoor_context.operational",
                 side_effect=operational) as actual:
            def interpret(payload):
                self.assertEqual(payload["operation"], "AUGURY_RETRIEVAL_SHADOW")
                self.assertEqual(payload["scope"], "MemoryOS")
                self.assertEqual(len(payload["questions"]), 5)
                self.assertEqual(len(payload["records"]), 2)
                self.assertEqual(
                    [x["slot"] for x in payload["records"]], [0, 1]
                )
                for record in payload["records"]:
                    self.assertEqual(set(record), {"slot", "statement"})
                    self.assertNotIn("record_id", record)
                    self.assertNotIn("source", record)
                return chosen
            result = shadow.review(self.runtime, interpret)
        return result, actual

    def test_bounded_semantic_shadow_compiles_exact_read_ritual_without_release(self):
        result, calls = self.run_review()
        self.assertEqual(result["status"], "PASS_SHADOW_SAMPLE_ONLY", result)
        self.assertEqual(calls.call_count, 3)
        self.assertTrue(result["model_called"])
        self.assertTrue(result["legacy_exact_parity"])
        self.assertTrue(result["source_grounded_semantic_mechanics_passed"])
        self.assertTrue(result["expected_target_oracle_passed"])
        self.assertEqual(result["expected_target_oracle_state"], "MATCHED")
        self.assertEqual(result["case_count"], 5)
        self.assertTrue(all(r["pass"] for r in result["case_results"]))
        self.assertFalse(result["general_semantic_quality_proven"])
        self.assertFalse(result["historical_coverage"])
        self.assertFalse(result["release_activated"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        for secret in ("real-one", "real-two", "relevance from gravity",
                       "owner authority independently", "owner-review"):
            self.assertNotIn(secret, str(result))

    def test_source_grounded_oracle_mismatch_is_specific_hold(self):
        opposite = {"cases": [
            {"case": 0, "resolution": "RESOLVED", "slot": 1,
             "support_quote": "owner authority independently"},
            {"case": 1, "resolution": "RESOLVED", "slot": 0,
             "support_quote": "relevance from gravity"},
            {"case": 2, "resolution": "RESOLVED", "slot": 1,
             "support_quote": "owner authority independently"},
            {"case": 3, "resolution": "UNKNOWN", "slot": None,
             "support_quote": None},
            {"case": 4, "resolution": "UNKNOWN", "slot": None,
             "support_quote": None},
        ]}
        result, calls = self.run_review(opposite)
        self.assertEqual(result["status"], "HOLD", result)
        self.assertEqual(
            result["reason"],
            "SOURCE_GROUNDED_MECHANICS_PASS_EXPECTED_TARGET_ORACLE_MISMATCH",
        )
        self.assertEqual(calls.call_count, 3)
        self.assertTrue(result["source_grounded_semantic_mechanics_passed"])
        self.assertFalse(result["expected_target_oracle_passed"])
        self.assertEqual(
            result["expected_target_oracle_state"], "MISMATCH_UNRESOLVED"
        )
        self.assertTrue(result["legacy_exact_parity"])
        self.assertTrue(all(
            row["source_quote_verified"]
            and row["exact_read_ritual_compiled"]
            and row["galaxy_readback_verified"]
            and not row["expected_target_supported"]
            and not row["pass"]
            for row in result["case_results"][:3]
        ))
        self.assertTrue(all(row["pass"] for row in result["case_results"][3:]))
        self.assertFalse(result["release_activated"])
        self.assertEqual(result["writes_performed"], [])

    def test_fabricated_quote_cannot_be_read_back(self):
        bad = decisions()
        bad["cases"][0]["support_quote"] = "unrelated invented statement quote"
        result, calls = self.run_review(bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["case_results"][0]["pass"])
        self.assertFalse(result["case_results"][0]["source_quote_verified"])
        self.assertEqual(calls.call_count, 2)

    def test_negative_control_must_remain_unknown(self):
        bad = decisions()
        bad["cases"][3] = {
            "case": 3, "resolution": "RESOLVED", "slot": 0,
            "support_quote": "relevance from gravity",
        }
        result, calls = self.run_review(bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["case_results"][3]["pass"])
        self.assertEqual(calls.call_count, 3)

    def test_collision_is_not_an_implicit_choice(self):
        bad = decisions()
        bad["cases"][0] = {
            "case": 0, "resolution": "COLLISION",
            "slot": None, "support_quote": None,
        }
        result, calls = self.run_review(bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["case_results"][0]["pass"])
        self.assertEqual(calls.call_count, 2)

    def test_missing_actual_galaxy_readback_is_not_success(self):
        result, calls = self.run_review(packet_kind="missing")
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(calls.call_count, 3)
        self.assertTrue(result["legacy_exact_parity"])
        self.assertFalse(any(
            x["galaxy_readback_verified"]
            for x in result["case_results"][:3]
        ))

    def test_bogus_model_shape_fails_closed(self):
        bad = decisions()
        bad["cases"][0]["execute_this_command"] = "MEMSAV all"
        result, calls = self.run_review(bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "SEMANTIC_UNIT_INVALID_OR_INCOMPLETE")
        self.assertFalse(result["release_activated"])
        self.assertEqual(calls.call_count, 0)
        self.assertNotIn("MEMSAV all", str(result))

    def test_unapproved_or_missing_source_never_reaches_model(self):
        self.runtime.records[0]["source"] = "calibration-fixture"
        with patch.object(readiness, "prepare_technical_cases",
                          return_value=self.prepared), patch.object(
            mode, "mode_status", return_value=self.control
        ):
            output = shadow.review(
                self.runtime,
                lambda _: self.fail("Unapproved source reached model"),
            )
        self.assertEqual(output["status"], "HOLD")
        self.assertEqual(output["reason"], "TECHNICAL_SOURCE_PROVENANCE_UNVERIFIED")
        self.assertFalse(output["model_called"])

    def test_exact_quote_compilation_reuses_existing_threshold(self):
        from galaxy_phase3_exit import _statement_evidence
        statement = self.runtime.records[0]["statement"]
        query = shadow._compile_read_only_query(
            self.runtime, statement, "relevance from gravity",
            self.runtime.records,
        )
        self.assertIsNotNone(query)
        evidence = _statement_evidence(
            self.runtime, statement, query, scope="MemoryOS"
        )
        self.assertGreaterEqual(evidence["matched_statement_concept_count"], 2)
        self.assertGreaterEqual(evidence["statement_concept_coverage"], 2/3)
        self.assertIsNone(shadow._compile_read_only_query(
            self.runtime, statement, "fabricated outside exact record",
            self.runtime.records,
        ))

    def test_internal_semantic_unit_preserves_typed_non_effectful_boundary(self):
        unit = shadow._semantic_unit(
            0, "How does GALAXY work?", decisions()["cases"][0]
        )
        required = {
            "schema", "semantic_id", "resolution", "raw_surface", "provenance",
            "semantic_class", "speech_act", "ritual_candidates",
            "ritual_selection_state", "unknowns", "collisions", "loss_report"
        }
        self.assertTrue(required.issubset(unit))
        self.assertEqual(unit["speech_act"], "QUESTION")
        self.assertEqual(unit["ritual_selection_state"], "CANDIDATE")
        self.assertEqual(unit["ritual_candidates"][0]["effect_class"], "READ_ONLY")
        self.assertIsNone(unit["authority_request"])


class ShadowRouteTests(unittest.TestCase):
    def test_owner_consent_guards_api_and_one_no_store_model_call(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        from unittest.mock import Mock
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        fake_response = SimpleNamespace(status="completed", output_text='{"cases":[]}')
        with patch.object(carrier.base, "API_KEY", "ci-owner-key"), patch.object(
            carrier.base, "OPENAI_API_KEY", "ci-provider-key"
        ), patch.object(
            carrier.base, "OPENAI_MODEL", "ci-model-only"
        ), patch.object(
            shadow, "review", side_effect=lambda runtime, interpret: {
                "schema": shadow.SCHEMA,
                "status": "HOLD",
                "probe_result": interpret({
                    "operation": "AUGURY_RETRIEVAL_SHADOW",
                    "scope": "MemoryOS",
                    "records": [{"slot": 0, "statement": "ci fixture A"},
                                {"slot": 1, "statement": "ci fixture B"}],
                    "questions": [{"case": i, "question": "ci question"}
                                  for i in range(5)],
                }),
                "writes_performed": [],
            }
        ) as reviewed, patch("openai.OpenAI") as sdk:
            sdk.return_value.responses.create.return_value = fake_response
            page = client.get("/gaiaos/memory/technical-partial-console")
            self.assertEqual(page.status_code, 200)
            self.assertIn('id="semanticconsent"', page.text)
            self.assertIn("store=false", page.text)
            self.assertIn("/gaiaos/memory/augury-semantic-shadow", page.text)
            self.assertNotIn("ci-provider-key", page.text)
            denied = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
            )
            self.assertEqual(denied.status_code, 401)
            missing_consent = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": False},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
            self.assertEqual(missing_consent.status_code, 400)
            self.assertEqual(sdk.call_count, 0)
            approved = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
            self.assertEqual(approved.status_code, 200, approved.text)
            self.assertEqual(approved.json()["status"], "HOLD")
            reviewed.assert_called_once()
            sdk.assert_called_once()
            call = sdk.return_value.responses.create
            call.assert_called_once()
            kwargs = call.call_args.kwargs
            self.assertIs(kwargs["store"], False)
            self.assertEqual(kwargs["model"], "ci-model-only")
            self.assertEqual(kwargs["text"]["format"]["type"], "json_schema")
            self.assertTrue(kwargs["text"]["format"]["strict"])
            self.assertNotIn("ci-owner-key", kwargs["input"])
            self.assertNotIn("ci-provider-key", kwargs["input"])


    def test_outer_whitespace_is_normalized_before_sdk_use(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        normalized_key = carrier.base._normalized_env_value("  ci-provider-key  ")
        normalized_model = carrier.base._normalized_env_value("  ci-model-only  ")
        fake_response = SimpleNamespace(status="completed", output_text='{"cases":[]}')
        with patch.object(carrier.base, "API_KEY", "ci-owner-key"), patch.object(
            carrier.base, "OPENAI_API_KEY", normalized_key
        ), patch.object(
            carrier.base, "OPENAI_MODEL", normalized_model
        ), patch.object(
            shadow, "review", side_effect=lambda runtime, interpret: {
                "schema": shadow.SCHEMA,
                "status": "HOLD",
                "probe_result": interpret({
                    "operation": "AUGURY_RETRIEVAL_SHADOW",
                    "scope": "MemoryOS",
                    "records": [{"slot": 0, "statement": "ci fixture A"},
                                {"slot": 1, "statement": "ci fixture B"}],
                    "questions": [{"case": i, "question": "ci question"} for i in range(5)],
                }),
                "writes_performed": [],
            }
        ), patch("openai.OpenAI") as sdk:
            sdk.return_value.responses.create.return_value = fake_response
            response = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(sdk.call_args.kwargs["api_key"], "ci-provider-key")
        self.assertEqual(
            sdk.return_value.responses.create.call_args.kwargs["model"],
            "ci-model-only",
        )

    def test_blank_model_name_blocks_before_review_or_sdk(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        with patch.object(carrier.base, "API_KEY", "ci-owner-key"), patch.object(
            carrier.base, "OPENAI_API_KEY", "ci-provider-key"
        ), patch.object(
            carrier.base, "OPENAI_MODEL", "   "
        ), patch.object(shadow, "review") as reviewed, patch("openai.OpenAI") as sdk:
            response = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "SHADOW_MODEL_NAME_NOT_CONFIGURED")
        reviewed.assert_not_called()
        sdk.assert_not_called()

    def test_whitespace_provider_key_blocks_before_review_or_sdk(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        with patch.object(carrier.base, "API_KEY", "ci-owner-key"), patch.object(
            carrier.base, "OPENAI_API_KEY", "   "
        ), patch.object(
            carrier.base, "OPENAI_MODEL", "ci-model"
        ), patch.object(shadow, "review") as reviewed, patch("openai.OpenAI") as sdk:
            response = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "SHADOW_MODEL_NOT_CONFIGURED")
        reviewed.assert_not_called()
        sdk.assert_not_called()

    def test_missing_provider_key_blocks_before_review_or_sdk(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        with patch.object(carrier.base, "API_KEY", "ci-owner-key"), patch.object(
            carrier.base, "OPENAI_API_KEY", ""
        ), patch.object(shadow, "review") as reviewed, patch("openai.OpenAI") as sdk:
            response = client.post(
                "/gaiaos/memory/augury-semantic-shadow",
                json={"explicit_semantic_shadow_consent": True},
                headers={"Authorization": "Bearer ci-owner-key"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "SHADOW_MODEL_NOT_CONFIGURED")
        reviewed.assert_not_called()
        sdk.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
