"""Stage 5D: HEATDEATH wins at actual authenticated research HTTP/chat routes.

This test suite uses only a temporary isolated SQLite database. It never
executes a production GALAXY operation or modifies a real Naomi memory record.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
_TEMP_DB = tempfile.TemporaryDirectory(prefix="gaiaos-heatdeath-5d-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_TEMP_DB.name) / "stage5d-ci.sqlite")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ["RENDER_GIT_COMMIT"] = "stage5d-ci-source"

import browser_memcon_bridge as bridge
import gaiaos_api as base
import gaiaos_memory_mode as mode
import gaiaos_lazy_diagnostics as lazy
import memcon_runtime as storage


def heatdeath():
    return {
        "schema": mode.SCHEMA,
        "effective_mode": "HEATDEATH",
        "configured_mode": "HEATDEATH",
        "bigbang_activation_enabled": False,
        "reason": "PERSISTED_OWNER_EMERGENCY",
    }


def fake_bigbang(*, permitted):
    return {
        "schema": mode.SCHEMA,
        "effective_mode": "BIGBANG",
        "configured_mode": "BIGBANG",
        "bigbang_activation_enabled": permitted,
        "reason": "TEST_ONLY_INJECTED_FUTURE_AUTHORIZATION",
    }


class HeatdeathResearchRoutePolicy(unittest.TestCase):
    def setUp(self):
        api_key = patch.object(base, "API_KEY", "ci-only-session-key-not-a-real-secret")
        api_key.start()
        self.addCleanup(api_key.stop)
        self.client = TestClient(bridge.app)
        self.addCleanup(self.client.close)
        self.client.cookies.set(base.SESSION_COOKIE, base._session_token())

    def test_status_routes_report_disabled_without_importing_research(self):
        with patch.object(mode, "mode_status", return_value=heatdeath()), patch.object(
            lazy.importlib, "import_module",
            side_effect=AssertionError("research module imported under HEATDEATH")
        ) as loader, patch.object(
            storage, "galaxy_status",
            side_effect=AssertionError("GALAXY runtime called under HEATDEATH"),
        ):
            for path in ("/galaxy/status", "/galaxy/production/status"):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200, response.text)
                    body = response.json()
                    self.assertEqual(body["status"], "GALAXY_DISABLED_BY_HEATDEATH")
                    self.assertEqual(body["effective_mode"], "HEATDEATH")
                    self.assertFalse(body["research_import_attempted"])
                    self.assertEqual(body["writes_performed"], [])
                    self.assertEqual(response.headers["cache-control"], "no-store")
        loader.assert_not_called()

    def test_all_research_http_families_hold_before_any_mutation_or_import(self):
        targets = [
            ("GET", "/galaxy/retrieval/phase3-experiment"),
            ("GET", "/galaxy/pruning/phase7-positive-canary"),
            ("GET", "/galaxy/canary/approve"),
            ("GET", "/galaxy/gravity/calibration/approve"),
            ("GET", "/galaxy/production/review"),
            ("POST", "/galaxy/production/activate"),
            ("POST", "/galaxy/production/rollback-proof"),
            ("POST", "/galaxy/pruning/phase7-tombstone-shadow-controls/manifest"),
            ("GET", "/ritual/status"),
            ("POST", "/ritual/manifest"),
        ]
        with patch.object(mode, "mode_status", return_value=heatdeath()), patch.object(
            lazy.importlib, "import_module",
            side_effect=AssertionError("unexpected research code import"),
        ) as loader, patch.object(
            storage, "write_record", side_effect=AssertionError("unexpected write")
        ):
            for method, path in targets:
                with self.subTest(method=method, path=path):
                    r = self.client.request(method, path)
                    self.assertEqual(r.status_code, 503, r.text)
                    p = r.json()
                    self.assertEqual(p["status"], "HOLD_GALAXY_DISABLED_BY_HEATDEATH")
                    self.assertFalse(p["research_import_attempted"])
                    self.assertEqual(p["writes_performed"], [])
                    self.assertEqual(p["effective_mode"], "HEATDEATH")
        loader.assert_not_called()

    def test_invalid_or_unavailable_mode_fails_to_heatdeath(self):
        controls = (
            RuntimeError("Turso control offline"),
            {"schema": mode.SCHEMA, "effective_mode": "BIGBANG",
             "configured_mode": "BIGBANG", "bigbang_activation_enabled": False},
            {"schema": mode.SCHEMA, "effective_mode": "BIGBANG",
             "configured_mode": "HEATDEATH", "bigbang_activation_enabled": True},
            None,
        )
        for value in controls:
            with self.subTest(value=value):
                patcher = (patch.object(mode, "mode_status", side_effect=value)
                           if isinstance(value, Exception)
                           else patch.object(mode, "mode_status", return_value=value))
                with patcher, patch.object(
                    lazy.importlib, "import_module",
                    side_effect=AssertionError("research import attempted"),
                ):
                    response = self.client.post("/galaxy/production/activate")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json()["status"], "HOLD_GALAXY_DISABLED_BY_HEATDEATH",
                )

    def test_unauthenticated_caller_is_denied_before_disclosure(self):
        with patch.object(mode, "mode_status", return_value=heatdeath()):
            self.client.cookies.clear()
            for path in ("/galaxy/status", "/galaxy/production/activate"):
                with self.subTest(path=path):
                    r = self.client.get(path)
                    self.assertEqual(r.status_code, 401, r.text)
                    self.assertEqual(
                        r.json()["detail"],
                        "Browser session missing; reload the GaiaOS page",
                    )

    def test_synthetic_future_bigbang_can_pass_policy_but_unapproved_cannot(self):
        # This only tests routing through the policy; Stage-2 production mode
        # never issues the authorized BIGBANG state used in this mocked branch.
        with patch.object(mode, "mode_status",
                          return_value=fake_bigbang(permitted=False)):
            denied = self.client.get("/galaxy/status")
        self.assertEqual(denied.json()["status"], "GALAXY_DISABLED_BY_HEATDEATH")
        with patch.object(mode, "mode_status",
                          return_value=fake_bigbang(permitted=True)), patch.object(
            storage, "galaxy_status", return_value={"status": "CI_ONLY_PASS"}
        ):
            allowed = self.client.get("/galaxy/status")
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(allowed.json()["status"], "CI_ONLY_PASS")

    def test_actual_browser_command_handler_blocks_all_existing_research_forms(self):
        commands = [
            "//PW:ORBIT// MEM-TEST",
            "PW:GRAVITY MEM-TEST",
            "GALAXY CANARY START",
            "GALAXY CANARY APPROVE",
            "GALAXY PROPOSE MEM-1 SUPERSEDES MEM-2",
            "GALAXY VERIFY EDGE-1",
        ]
        with patch.object(mode, "mode_status", return_value=heatdeath()), patch.object(
            bridge, "_handle_galaxy_canary_approve",
            side_effect=AssertionError("GALAXY handler called")
        ), patch.object(
            bridge.gaiaos_app, "_deployed_source",
            return_value={"commit": "stage5d-ci"},
        ), patch.object(
            lazy.importlib, "import_module",
            side_effect=AssertionError("research import attempted"),
        ) as loader:
            for cmd in commands:
                with self.subTest(cmd=cmd):
                    response = self.client.post(
                        "/chat", json={"messages": [{"role": "user", "content": cmd}]}
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    data = response.json()
                    self.assertTrue(
                        data["output"].startswith("GALAXY DISABLED BY HEATDEATH"),
                        data,
                    )
                    self.assertIn("HOLD_GALAXY_DISABLED_BY_HEATDEATH", data["output"])
        loader.assert_not_called()

    def test_original_normal_chat_and_legacy_memory_routes_still_work(self):
        with patch.object(mode, "mode_status", return_value=heatdeath()), patch.object(
            bridge, "_original_chat",
            return_value={"output":"legacy hosted chat", "model":"ci",
                          "source":"ci"},
        ) as hosted, patch.object(
            lazy.importlib, "import_module",
            side_effect=AssertionError("optional research imported"),
        ) as loader:
            chat = self.client.post("/chat", json={
                "messages": [{"role": "user", "content": "Tell me about memory"}]
            })
            self.assertEqual(chat.status_code, 200)
            self.assertEqual(chat.json(), {
                "output": "legacy hosted chat", "model": "ci", "source": "ci",
            })
            hosted.assert_called_once()
        loader.assert_not_called()
        self.assertIsNone(bridge._explicit_galaxy_chat_command(
            "Tell me about memory"
        ) or None)

    def test_existing_legacy_review_remains_exception_and_is_not_research_gate(self):
        with patch.object(mode, "mode_status", return_value=heatdeath()), patch.object(
            bridge, "_bootstrap_browser_session_redirect", return_value=None
        ), patch.object(
            lazy.importlib, "import_module",
            side_effect=ImportError("GALAXY deliberately unavailable"),
        ):
            response = self.client.get(
                "/galaxy/integration/frontdoor-readonly-review"
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "HOLD")
        self.assertEqual(response.json()["error_type"], "HTTPException")

    def test_preservation_and_approval_branches_precede_research_block(self):
        source = (ROOT / "api" / "browser_memcon_bridge.py").read_text()
        start = source.index('async def browser_chat(')
        end = source.index('def _ordinary_chat(', start)
        handler = source[start:end]
        self.assertLess(handler.index('_is_preserve_command(last_message)'),
                        handler.index('_explicit_galaxy_chat_command(last_message)'))
        for protected in (
            '_is_command(last_message, "SOLO")',
            '_is_command(last_message, "ENDSOLO")',
            '_is_command(last_message, "MEMSAV")',
            '_is_command(last_message, "CANDIPULL")',
        ):
            self.assertIn(protected, handler)
        self.assertIn("HOLD_GALAXY_DISABLED_BY_HEATDEATH", source)
        self.assertNotIn("\nimport galaxy_phase7\n", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
