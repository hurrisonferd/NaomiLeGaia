"""Stage 9W: actual GaiaOS served-app integration and full owner-session gate.

Unlike tests importing the underlying gaiaos_api FastAPI application directly,
this module imports the gaiaos_app EXTENSION that the GaiaOS deployment serves.
It never calls real OpenAI or Turso, or changes any memory/E-LANE.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_api as carrier
import gaiaos_app as deployed
import gaiaos_chat_auto_memory as auto_memory
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode

SIGNING_KEY = "STAGE9W-LOCAL-TEST-SESSION-KEY-NO-REAL-CREDENTIAL"
FAKE_MODEL_KEY = "STAGE9W-FAKE-OPENAI-KEY-NO-NETWORK"


class _Model:
    def __init__(self):
        self.calls = []
        self.responses = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="A fixture-only response.")


class GaiaOSDeployedAppTests(unittest.TestCase):
    def setUp(self):
        self.model = _Model()
        self.patches = (
            patch.object(carrier, "API_KEY", SIGNING_KEY),
            patch.object(carrier, "OPENAI_API_KEY", FAKE_MODEL_KEY),
            patch.object(carrier, "OpenAI", return_value=self.model),
            patch.object(carrier, "_load_bundle", return_value={
                "gaiaos": {"source": "STAGE9W-ISOLATED-DEPLOYED-APP"},
            }),
            patch.object(carrier, "_carrier_instructions", return_value="Verified fixture carrier."),
        )
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(deployed.app, base_url="https://testserver")

    def test_served_extension_uses_exactly_one_real_browser_route(self):
        self.assertIs(deployed.app, carrier.app)
        paths = [route for route in deployed.app.routes if isinstance(route, APIRoute)]
        browser = [route for route in paths if route.path == "/chat" and "POST" in route.methods]
        self.assertEqual(len(browser), 1)
        self.assertIs(browser[0].endpoint, carrier.browser_chat)
        self.assertTrue(
            any(route.path == "/gaiaos/assist" and "POST" in route.methods for route in paths)
        )
        mounted = [r for r in deployed.app.routes if isinstance(r, Mount) and r.path == "/mcp"]
        self.assertEqual(len(mounted), 1)
        self.assertFalse(any(isinstance(r, APIRoute) and r.endpoint is carrier.chat for r in paths))

    def test_hosted_home_sets_real_secure_session_cookie_then_chat_stays_legacy(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        cookie = home.cookies.get(carrier.SESSION_COOKIE)
        self.assertTrue(cookie, home.headers)
        self.assertIn("secure", home.headers.get("set-cookie", "").lower())
        self.assertIn("httponly", home.headers.get("set-cookie", "").lower())
        self.client.cookies.set(carrier.SESSION_COOKIE, cookie)
        with patch.object(mode, "mode_status", return_value={
            "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
            "configured_mode": mode.HEATDEATH, "bigbang_activation_enabled": False,
        }), patch.object(gateway, "read", side_effect=AssertionError("legacy must not auto-query")):
            resp = self.client.post(
                "/chat", json={"messages": [{"role": "user", "content": "Legacy chat"}]},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertNotIn("memory_context", resp.json())
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(self.model.calls[0]["instructions"], "Verified fixture carrier.")

    def test_missing_or_invalid_real_browser_session_does_not_scan_or_call_model(self):
        with patch.object(auto_memory, "prepare_for_browser") as prep:
            missing = self.client.post(
                "/chat", json={"messages": [{"role": "user", "content": "secret?"}]},
            )
            self.assertEqual(missing.status_code, 401, missing.text)
            prep.assert_not_called()
            self.assertEqual(self.model.calls, [])
            self.client.cookies.set(carrier.SESSION_COOKIE, "forged.invalid")
            invalid = self.client.post(
                "/chat", json={"messages": [{"role": "user", "content": "secret?"}]},
            )
            self.assertEqual(invalid.status_code, 401, invalid.text)
            prep.assert_not_called()
            self.assertEqual(self.model.calls, [])

    def test_served_browser_explicit_opt_out_blocks_gateway_with_signed_session(self):
        self.client.cookies.set(carrier.SESSION_COOKIE, carrier._session_token())
        with patch.object(auto_memory, "prepare_for_browser") as prep:
            resp = self.client.post("/chat", json={
                "include_memory": False,
                "messages": [{"role": "user", "content": "DO NOT RETRIEVE"}],
            })
        self.assertEqual(resp.status_code, 200, resp.text)
        prep.assert_not_called()
        self.assertEqual(self.model.calls[0]["instructions"], "Verified fixture carrier.")
        self.assertNotIn("memory_context", resp.json())

    def test_served_frontdoor_explicit_legacy_read_and_no_default_implicit_read(self):
        self.client.cookies.set(carrier.SESSION_COOKIE, carrier._session_token())
        fake_control = {
            "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
            "configured_mode": mode.HEATDEATH, "bigbang_activation_enabled": False,
        }
        def config(path):
            if path == deployed.CURRENT_PATH:
                return {"platform_version": "stage9w.test"}
            if path == deployed.VERSION_PATH:
                return {"version": "stage9w.test"}
            raise AssertionError("unexpected source read")

        with patch.object(deployed, "_deployed_commit", return_value="a" * 40), \
             patch.object(deployed, "_deployed_source", return_value="STAGE9W-SOURCE"), \
             patch.object(deployed, "_read_local_json", side_effect=config), \
             patch.object(deployed, "_infer_signals", return_value=[]), \
             patch.object(deployed, "_requested_members_from_text", return_value=[]), \
             patch.object(carrier, "_dispatch_packet", return_value={
                 "selected": [], "unknown_requested_members": [],
             }), \
             patch.object(mode, "mode_status", return_value=fake_control), \
             patch.object(gateway, "read", return_value={
                 "status": "PASS_HEATDEATH", "effective_mode": "HEATDEATH",
                 "galaxy_applied": False, "writes_performed": [],
             }) as read:
            default = self.client.post(
                "/gaiaos/assist", headers={"Authorization": "Bearer " + SIGNING_KEY},
                json={"request": "read gravity context", "include_context": False},
            )
            self.assertEqual(default.status_code, 200, default.text)
            self.assertNotIn("memory_context", default.json())
            read.assert_not_called()
            explicit = self.client.post(
                "/gaiaos/assist", headers={"Authorization": "Bearer " + SIGNING_KEY},
                json={"request": "read gravity context", "include_context": False,
                      "include_memory": True},
            )
            self.assertEqual(explicit.status_code, 200, explicit.text)
            self.assertEqual(explicit.json()["memory_context"]["status"], "PASS_HEATDEATH")
            self.assertFalse(explicit.json()["memory_context"]["galaxy_applied"])
            read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
