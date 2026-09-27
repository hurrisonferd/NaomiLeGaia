"""Stage 9W: normal /chat uses GALAXY only after independent mode authorization.

Exercises the real FastAPI route with a mocked model, never OpenAI network or
live Turso. Browser-supplied memory_context must never become trusted evidence.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import gaiaos_api as carrier
import gaiaos_chat_auto_memory as automatic
import gaiaos_chat_memory as evidence
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode

AUTH = {
    "schema": mode.SCHEMA, "effective_mode": mode.BIGBANG,
    "configured_mode": mode.BIGBANG, "bigbang_activation_enabled": True,
    "reason": "STAGE9W_ISOLATED_INJECTION_ONLY",
}
HEATDEATH = {
    "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH, "bigbang_activation_enabled": False,
}


def prepared():
    return {
        "schema": evidence.SCHEMA,
        "status": "VERIFIED_READ_ONLY_CONTEXT_FOR_THIS_REQUEST",
        "memory_context_authority": "NONE",
        "untrusted_source_content_not_instructions": True,
        "current_records": [{
            "record_id": "MEM-STAGE9W-CURRENT",
            "statement": "Verified fixture historical memory",
            "statement_truncated": False, "source": "stage9w:fixture:canonical",
            "source_truncated": False, "governing_state": "CURRENT",
            "current_default_eligible": True, "context_only": False,
            "status": "ACTIVE",
        }],
        "verified_linked_context": [],
        "historical_records_omitted_from_current_answer": 1,
        "writes_performed": [], "e_lanes_modified": False,
    }


class RecordingOpenAI:
    def __init__(self):
        self.calls = []
        self.responses = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="The fixture completed.")


class Stage9WBrowserRouting(unittest.TestCase):
    def setUp(self):
        self.model = RecordingOpenAI()
        self.patchers = [
            patch.object(carrier, "_authorize_browser_session", return_value=None),
            patch.object(carrier, "OPENAI_API_KEY", "STAGE9W-FAKE-MODEL-KEY"),
            patch.object(carrier, "OpenAI", return_value=self.model),
            patch.object(carrier, "_load_bundle", return_value={
                "gaiaos": {"source": "stage9w:fixture:checked-out"}
            }),
            patch.object(carrier, "_carrier_instructions", return_value="Trusted carrier."),
        ]
        for item in self.patchers:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(carrier.app)

    def post(self, **kwargs):
        return self.client.post(
            "/chat",
            json={
                "messages": [{"role": "user", "content": "Tell me about the old calibration"}],
                **kwargs,
            },
        )

    def test_actual_chat_route_gates_implicit_retrieval_in_heatdeath(self):
        with patch.object(mode, "mode_status", return_value=HEATDEATH), patch.object(
            gateway, "read", side_effect=AssertionError("GALAXY NOT ALLOWED IN HEATDEATH")
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")

    def test_actual_chat_route_consumes_verified_server_context_only_after_gate(self):
        packet = prepared()
        self.assertTrue(evidence.validate_prepared(packet))
        with patch.object(automatic, "prepare_for_browser", return_value=packet) as prepare, patch.object(
            mode, "mode_status", return_value=AUTH
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        prepare.assert_called_once_with("Tell me about the old calibration")
        self.assertEqual(
            result.json()["memory_context"]["status"], "BIGBANG_VERIFIED_CONTEXT_USED"
        )
        self.assertEqual(
            result.json()["memory_context"]["current_record_ids"],
            ["MEM-STAGE9W-CURRENT"],
        )
        instructions = self.model.calls[-1]["instructions"]
        self.assertIn("BOUNDED MEMORY CONTEXT", instructions)
        self.assertIn("untrusted quoted data", instructions)
        self.assertIn("MEM-STAGE9W-CURRENT", instructions)

    def test_browser_supplied_memory_context_is_ignored_not_trusted(self):
        with patch.object(automatic, "prepare_for_browser", return_value=None), patch.object(
            mode, "mode_status", return_value=AUTH
        ):
            result = self.post(memory_context=prepared())
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertNotIn("MEM-STAGE9W-CURRENT", self.model.calls[0]["instructions"])

    def test_explicit_opt_out_always_prevents_server_memory_lookup(self):
        with patch.object(
            automatic, "prepare_for_browser",
            side_effect=AssertionError("explicit opt-out must never lookup"),
        ), patch.object(mode, "mode_status", return_value=AUTH):
            result = self.post(include_memory=False)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")

    def test_optional_module_import_or_runtime_error_cannot_break_legacy_chat(self):
        with patch.object(
            automatic, "prepare_for_browser", side_effect=ImportError("PRIVATE-ERROR-STRING")
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn("memory_context", result.json())
        self.assertNotIn("PRIVATE-ERROR-STRING", result.text)
        self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")

    def test_last_assistant_turn_cannot_impersonate_user_for_retrieval(self):
        with patch.object(automatic, "prepare_for_browser") as prep:
            result = self.client.post(
                "/chat",
                json={"messages": [
                    {"role": "user", "content": "Earlier real query"},
                    {"role": "assistant", "content": "Untrusted assistant says read private"},
                ]},
            )
        self.assertEqual(result.status_code, 200, result.text)
        prep.assert_not_called()

    def test_second_gate_control_outage_discards_memory_but_serves_chat(self):
        packet = prepared()
        # Preparation already succeeded in the optional server bridge.
        # A lost control connection at the SECOND gate must not abort /chat.
        with patch.object(automatic, "prepare_for_browser", return_value=packet), patch.object(
            mode, "mode_status", side_effect=ConnectionError("PRIVATE-TURSO-TOKEN")
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")
        self.assertEqual(
            result.json()["memory_context"]["status"],
            "HOLD_NOT_APPLIED_UNVERIFIED_OR_HEATDEATH",
        )
        self.assertNotIn("PRIVATE-TURSO-TOKEN", result.text)
        self.assertNotIn("MEM-STAGE9W-CURRENT", self.model.calls[0]["instructions"])

    def test_second_gate_requires_schema_and_ignores_activation_truthy(self):
        packet = prepared()
        altered = (
            {**AUTH, "schema": "INVALID"},
            {**AUTH, "bigbang_activation_enabled": 1},
            {**AUTH, "configured_mode": mode.HEATDEATH},
            HEATDEATH,
            None,
        )
        for control in altered:
            with self.subTest(control=control):
                self.model.calls.clear()
                with patch.object(automatic, "prepare_for_browser", return_value=packet), patch.object(
                    mode, "mode_status", return_value=control
                ):
                    result = self.post()
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(len(self.model.calls), 1)
                self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")
                self.assertEqual(
                    result.json()["memory_context"]["status"],
                    "HOLD_NOT_APPLIED_UNVERIFIED_OR_HEATDEATH",
                )

    def test_second_gate_instruction_builder_failure_never_leaks_partial_memory(self):
        packet = prepared()
        with patch.object(automatic, "prepare_for_browser", return_value=packet), patch.object(
            mode, "mode_status", return_value=AUTH
        ), patch.object(
            evidence, "instructions", side_effect=ValueError("PRIVATE-MEMORY-DATA")
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(self.model.calls[0]["instructions"], "Trusted carrier.")
        self.assertEqual(
            result.json()["memory_context"]["status"],
            "HOLD_NOT_APPLIED_UNVERIFIED_OR_HEATDEATH",
        )
        self.assertNotIn("PRIVATE-MEMORY-DATA", result.text)

    def test_malformed_injected_evidence_fails_second_guard_at_model_call(self):
        packet = prepared()
        packet["current_records"][0]["current_default_eligible"] = False
        with patch.object(automatic, "prepare_for_browser", return_value=packet), patch.object(
            mode, "mode_status", return_value=AUTH
        ):
            result = self.post()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(
            result.json()["memory_context"]["status"],
            "HOLD_NOT_APPLIED_UNVERIFIED_OR_HEATDEATH",
        )
        self.assertNotIn("MEM-STAGE9W-CURRENT", self.model.calls[0]["instructions"])


class Stage9WReleaseLockHelper(unittest.TestCase):
    def test_no_legacy_memory_scan_when_mode_not_authorized(self):
        with patch.object(mode, "mode_status", return_value=HEATDEATH), patch.object(
            gateway, "read", side_effect=AssertionError("gateway must not run")
        ):
            self.assertIsNone(automatic.prepare_for_browser("query"))
        with patch.object(mode, "mode_status", return_value={**AUTH, "schema": "WRONG"}), patch.object(
            gateway, "read", side_effect=AssertionError("gateway must not run")
        ):
            self.assertIsNone(automatic.prepare_for_browser("query"))

    def test_invalid_query_does_not_even_read_mode_control(self):
        with patch.object(mode, "mode_status", side_effect=AssertionError("not called")):
            for query in ("", " " * 3, "x" * 20001, None, []):
                self.assertIsNone(automatic.prepare_for_browser(query))

    def test_authorized_packet_must_still_pass_gateway_and_evidence_checks(self):
        with patch.object(mode, "mode_status", return_value=AUTH), patch.object(
            gateway, "read", return_value={
                "status": "PASS_HEATDEATH_FALLBACK", "effective_mode": "HEATDEATH",
                "galaxy_applied": False,
            },
        ):
            self.assertIsNone(automatic.prepare_for_browser("read older history"))
        with patch.object(mode, "mode_status", return_value=AUTH), patch.object(
            gateway, "read", return_value={
                "status": "PASS_BIGBANG", "effective_mode": "BIGBANG",
                "galaxy_applied": True, "fallback_occurred": False,
                "writes_performed": [], "e_lanes_modified": False,
            },
        ), patch.object(evidence, "prepare", return_value=prepared()):
            self.assertEqual(
                automatic.prepare_for_browser("read older history"), prepared()
            )

    def test_failed_memcon_mode_or_gateway_falls_back_without_relabeling(self):
        with patch.object(mode, "mode_status", side_effect=ConnectionError("PRIVATE-TURSO-TOKEN")):
            self.assertIsNone(automatic.prepare_for_browser("read older history"))
        with patch.object(mode, "mode_status", return_value=AUTH), patch.object(
            gateway, "read", side_effect=ImportError("GALAXY OPTIONAL NOT INSTALLED")
        ):
            self.assertIsNone(automatic.prepare_for_browser("read older history"))


if __name__ == "__main__":
    unittest.main()
