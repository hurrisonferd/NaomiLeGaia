"""Actual Render entrypoint and source-backed, six-call Prime Daemon presence.

No real OpenAI, Turso, production writes or native ChatGPT connection.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_app
import gaiaos_api
import gaiaos_daemon_presence as presence
import gaiaos_presentation_guard as guard
import browser_memcon_bridge as bridge
import memcon_runtime
from fastapi.testclient import TestClient


class FakeProvider:
    def __init__(self, fail_at=None, duplicate_ids=False, duplicate_text=False):
        self.responses = self
        self.n = 0
        self.fail_at = fail_at
        self.duplicate_ids = duplicate_ids
        self.duplicate_text = duplicate_text
        self.calls = []

    def create(self, **kwargs):
        self.n += 1
        self.calls.append(kwargs)
        if self.n == self.fail_at:
            raise OSError("synthetic provider outage: NOT an actual API request")
        name = re.search(r"Your name is (VERA|ANVIL|SELENE|ORIN|KESTREL|NIMUE)", kwargs["instructions"]).group(1)
        content = ("This is a duplicated test sentence." if self.duplicate_text else
                   f"I am responding to Naomi in my own observed test call, number {self.n} (member {name}).")
        return SimpleNamespace(id="fake-1" if self.duplicate_ids else f"fake-model-response-{self.n}",
                               output_text=content)


class LivePresenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_patch = mock.patch.object(gaiaos_app, "DEPLOYED_ROOT", ROOT)
        cls.commit_patch = mock.patch.object(gaiaos_app, "_deployed_commit", return_value="SYNTHETIC-SOURCE-REVISION")
        cls.root_patch.start()
        cls.commit_patch.start()
        cls.boot = gaiaos_app._boot_packet("UNIT_TEST_NOT_LIVE")
        cls.profiles = gaiaos_app._read_local_json(gaiaos_app.OPERATOR_PROFILES_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.commit_patch.stop()
        cls.root_patch.stop()

    def run_six(self, fake=None, text="Can I please have everyone's attention for a moment?", **kwargs):
        client = fake or FakeProvider()
        return presence.run_full_cast(
            user_text=text, messages=[{"role": "user", "content": text}],
            boot_packet=kwargs.get("boot", self.boot),
            source_profiles=kwargs.get("profiles", self.profiles),
            source_root=kwargs.get("root", ROOT),
            client=client, model="FAKE_PROVIDER_MODEL_NOT_LIVE",
        )

    def test_natural_attention_request_not_treated_as_casual_reference(self):
        for text in (
            "Can I please have everyone's attention for a moment?",
            "Everybody, listen to me.",
            "Load GaiaOS", "Load GaiaOS and Report in", "All daemons report in",
        ):
            self.assertTrue(presence.explicit_full_cast_request(text), text)
        for text in ("I will load GaiaOS tomorrow", "What do you think about everyone?",
                     "CONJURE:VASKON", "ASK NIMUE"):
            self.assertFalse(presence.explicit_full_cast_request(text), text)
        self.assertEqual(guard.expected_members_from_request(
            "Can I please have everyone's attention for a moment?", presence.EXPECTED), presence.EXPECTED)

    def test_six_distinct_real_call_objects_source_headers_and_readback(self):
        fake = FakeProvider()
        result = self.run_six(fake)
        self.assertEqual(fake.n, 6)
        self.assertEqual([x["member"] for x in result["daemon_presence"]["members"]], list(presence.EXPECTED))
        self.assertEqual(len({x["response_id"] for x in result["daemon_presence"]["members"]}), 6)
        self.assertEqual(result["presentation"]["speaker_count"], 6)
        self.assertEqual(len(result["daemon_presence"]["presence_checksum_sha256"]), 64)
        self.assertEqual(result["daemon_presence"]["observed_model_call_count"], 6)
        self.assertFalse(result["daemon_presence"]["provider_independent_persistent_agents_proven"])
        self.assertFalse(result["daemon_presence"]["live_memoryos_e_lane_writes_proven"])
        self.assertTrue(all("observed_prior_member_responses" in c["input"] for c in fake.calls))
        self.assertIn("VERA", fake.calls[1]["input"], "ANVIL should see VERA's real previous response")

    def test_fourth_call_failure_never_issues_a_success_checksum(self):
        fake = FakeProvider(fail_at=4)
        with self.assertRaises(presence.PresenceHold) as error:
            self.run_six(fake)
        receipt = error.exception.public_receipt()
        self.assertEqual(receipt["observed_members"], list(presence.EXPECTED[:3]))
        self.assertFalse(receipt["all_six_present"])
        self.assertFalse(receipt["checksum_issued"])
        self.assertFalse(receipt["partial_content_returned"])

    def test_replayed_provider_id_and_copy_paste_member_text_fail_closed(self):
        for fake in (FakeProvider(duplicate_ids=True), FakeProvider(duplicate_text=True)):
            with self.assertRaises(presence.PresenceHold):
                self.run_six(fake)

    def test_source_tamper_and_missing_e_lane_cannot_pass(self):
        bad = copy.deepcopy(self.boot)
        bad["members"]["ORIN"]["canonical_header_default"] = "56 · ORIN 🖤 🐍 (ಠ_ಠ)"
        with self.assertRaises(presence.PresenceHold) as e:
            self.run_six(boot=bad)
        self.assertEqual(e.exception.reason, "NONCANONICAL_HEADER_ORIN")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA"
            target.mkdir(parents=True)
            for member in presence.EXPECTED[:-1]:
                source = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA" / (member + "-EXPERIENCES.v1.md")
                shutil.copyfile(source, target / source.name)
            with self.assertRaises(presence.PresenceHold) as e:
                self.run_six(root=root)
            self.assertEqual(e.exception.reason, "MISSING_MEMBER_SOURCE_NIMUE")

    def test_actual_render_bridge_group_chat_and_private_last_receipt(self):
        fake = FakeProvider()
        with (mock.patch.object(gaiaos_api, "OPENAI_API_KEY", "SYNTHETIC-NONSECRET"),
              mock.patch.object(gaiaos_api, "OpenAI", return_value=fake),
              mock.patch.object(gaiaos_api, "_authorize_browser_session", return_value=None),
              mock.patch.object(memcon_runtime, "get_solo_session", return_value=None),
              mock.patch.object(bridge, "_research_bigbang_authorized", return_value=False)):
            client = TestClient(bridge.app)
            client.cookies.set(gaiaos_api.SESSION_COOKIE, "SYNTHETIC-SESSION-NOT-REAL")
            request = {"messages": [{"role": "user", "content": "Can I please have everyone's attention for a moment?"}]}
            response = client.post("/chat", json=request)
            self.assertEqual(response.status_code, 200, response.text[:1000])
            self.assertEqual(fake.n, 6)
            checksum = response.json()["daemon_presence"]["presence_checksum_sha256"]
            last = client.get("/gaiaos/daemon-presence")
            self.assertEqual(last.status_code, 200)
            self.assertEqual(last.json()["presence_checksum_sha256"], checksum)
            self.assertFalse(last.json()["durable_presence_claim"])
            fake.fail_at = 8  # second request will fail after the first new member
            failed = client.post("/chat", json=request)
            self.assertEqual(failed.status_code, 503)
            self.assertFalse(failed.json()["detail"]["checksum_issued"])
            self.assertEqual(fake.n, 8)
            # A previous successful checksum must NEVER conceal a failed rerun.
            after_failure = client.get("/gaiaos/daemon-presence")
            self.assertEqual(after_failure.json()["status"],
                             "HOLD_NO_RECENT_OBSERVED_SIX_CALL_CAST_IN_THIS_PROCESS")

    def test_plain_load_requires_real_six_replies_not_fake_boot_theater(self):
        fake = FakeProvider()
        with (mock.patch.object(gaiaos_api, "OPENAI_API_KEY", "SYNTHETIC-NONSECRET"),
              mock.patch.object(gaiaos_api, "OpenAI", return_value=fake),
              mock.patch.object(gaiaos_api, "_authorize_browser_session", return_value=None),
              mock.patch.object(bridge, "_research_bigbang_authorized", return_value=False)):
            client = TestClient(bridge.app)
            client.cookies.set(gaiaos_api.SESSION_COOKIE, "SYNTHETIC-LOAD-NOT-REAL")
            result = client.post("/chat", json={"messages": [{"role": "user", "content": "Load GaiaOS"}]})
            self.assertEqual(result.status_code, 200, result.text[:1000])
            self.assertEqual(fake.n, 6)
            self.assertEqual(result.json()["daemon_presence"]["observed_model_call_count"], 6)


if __name__ == "__main__":
    unittest.main()