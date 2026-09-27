"""Stage 9AF: REAL signed 9Y disk row -> GALAXY -> gateway -> served /chat.

The imported row comes from Stage 9Y's actual pinned-source, canary-bound
native SQLite fixture, not a hand-written mock record. Stage 9Z's separately
signed rollback must remove it from future reads. All credentials, source
content, databases, mode approval and model responses are synthetic LOCAL
test values. Render, both real SOVMEM databases and owner E-LANES untouched.
"""
from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))

import galaxy_stage9af_signed_local_read_fixture as probe
import galaxy_frontdoor_context as reader
import galaxy_phase3_exit
import galaxy_legacy_gravity as gravity
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode
import gaiaos_chat_auto_memory as automatic
import gaiaos_api as carrier
import gaiaos_app as deployed
from test_galaxy_stage9z_local_rollback import SignedLocalRollbackTests

AUTH = {
    "schema": mode.SCHEMA, "effective_mode": mode.BIGBANG,
    "configured_mode": mode.BIGBANG, "bigbang_activation_enabled": True,
    "reason": "STAGE9AF_SYNTHETIC_MODE_APPROVAL_ONLY",
}
HEATDEATH = {
    "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH, "bigbang_activation_enabled": False,
}
MODEL_KEY = "STAGE9AF-FAKE-MODEL-KEY-NEVER-REAL"
SESSION_KEY = "STAGE9AF-LOCAL-SYNTHETIC-BROWSER-KEY"


class _FakeModel:
    def __init__(self):
        self.calls = []
        self.responses = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="LOCAL FIXTURE CHAT RESPONSE ONLY")


def _candidate(row):
    return {
        "status": "PASS",
        "candidates": [{
            "record_id": row["record_id"],
            "statement": row["statement"],
            "relevance": {"coverage": 1.0, "matched_concepts": ["memory"]},
        }],
        "linked_context_candidates": [],
        "checks": {
            "all_admitted_candidates_meet_primary_rule": True,
            "linked_context_requires_verified_direct_primary_edge": True,
        },
    }


def _module_for(rt):
    # The real browser bridge imports memcon_runtime dynamically.
    # Supply ONLY the signed, native SQLite-backed adapter, never live Turso.
    fake = types.ModuleType("memcon_runtime")
    fake._INITIALIZED = True
    fake.search_records = rt.search_records
    fake.galaxy_record = rt.galaxy_record
    fake.galaxy_governing_state = rt.galaxy_governing_state
    fake._db = rt._db
    return fake


class SignedImportToChatTests(unittest.TestCase):
    def setUp(self):
        fx = SignedLocalRollbackTests(
            "test_signed_exact_rollback_removes_only_new_rows_and_retains_receipts"
        )
        fx.setUp()
        self.fx = fx
        self.addCleanup(fx.doCleanups)
        self.receipt = fx.first["receipt"]
        self.rid = self.receipt["items"][0]["record_id"]
        self.row = fx.fx.conn.execute(
            "SELECT record_id,statement,status,source FROM memory_records"
        ).fetchone()
        self.rt = self.load()
        self.assertIsNotNone(self.rt)
        self.assertEqual(self.rt.proof()["held_signed_record_count"], 1)

    def load(self, **overrides):
        kwargs = {
            "fixture_connection": self.fx.fx.conn,
            "fixture_root": self.fx.fx.root,
            "config": self.fx.original["config"],
            "original_manifest": self.fx.original["approval"],
            "original_signature": self.fx.original["signature_hex"],
            "original_key": self.fx.original["approval_key"],
            "original_receipt": self.receipt,
            "confirm_synthetic_local_only": True,
        }
        kwargs.update(overrides)
        return probe.open_signed_local_archive_runtime(**kwargs)

    def test_true_stage9y_signed_disk_row_and_canary_loaded_not_recreated(self):
        report = self.rt.proof()
        self.assertEqual(report["status"], "PASS_SIGNED_LOCAL_FIXTURE_ONLY")
        self.assertTrue(report["original_signed_ledger_verified_at_creation"])
        self.assertFalse(report["live_turso_connected"])
        self.assertFalse(report["real_sovmem_main_connected"])
        self.assertFalse(report["bigbang_activated"])
        self.assertFalse(report["e_lanes_modified"])
        self.assertTrue(report["fixture_runtime_deliberately_forges_governing_state"])
        raw = self.rt.galaxy_record(self.rid)["record"]
        self.assertEqual(raw["statement"], self.row[1])
        self.assertEqual(raw["status"], "STAGED_HISTORICAL_HOLD")
        self.assertEqual(raw["source"], self.row[3])
        self.assertTrue(raw["source"].startswith("galaxy-archive-v1:"))
        self.assertEqual(
            self.rt.galaxy_governing_state(self.rid)["state"], "CURRENT"
        )
        self.assertEqual(self.fx.state(), (1, 1, 1, 0))
        self.assertNotIn(self.row[1], json.dumps(report))
        self.assertNotIn(self.row[3], json.dumps(report))

    def test_true_imported_primary_cannot_gain_current_status_or_gravity(self):
        before = self.fx.fx.stage_file.read_bytes()
        with patch.object(
            galaxy_phase3_exit, "build_candidate_pool",
            return_value=_candidate({"record_id": self.rid, "statement": self.row[1]}),
        ), patch.object(
            gravity, "resolve_for_retrieval",
            side_effect=AssertionError("MUST NOT SCORE HELD HISTORY"),
        ):
            denied = reader.operational(self.rt, self.row[1], limit=4)
        self.assertEqual(denied["status"], "HOLD_UNRELEASED_STAGED_ARCHIVE")
        self.assertEqual(denied["records"], [])
        self.assertEqual(denied["writes_performed"], [])
        self.assertEqual(self.fx.fx.stage_file.read_bytes(), before)

    def test_real_imported_held_row_blocked_on_legacy_heatdeath_and_bigbang(self):
        for control in (HEATDEATH, AUTH):
            with self.subTest(mode=control["effective_mode"]), patch.object(
                mode, "mode_status", return_value=control,
            ):
                result = gateway.read(
                    self.rt, self.row[1], scope="MemoryOS", limit=4,
                )
            self.assertEqual(
                result["status"], "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY"
            )
            self.assertIsNone(result["retrieval"])
            self.assertIsNone(result["galaxy_context"])
            self.assertNotIn(self.row[1], json.dumps(result))
            self.assertNotIn(self.row[3], json.dumps(result))

    def test_clean_legacy_malicious_candidate_pool_still_cannot_surface_import(self):
        runtime = self.load(include_synthetic_current=True)
        self.assertIsNotNone(runtime)
        clean_query = probe.SAFE_ROW["statement"]
        bad_pool = _candidate({
            "record_id": self.rid, "statement": self.row[1],
        })
        with patch.object(
            mode, "mode_status", return_value=AUTH,
        ), patch.object(
            galaxy_phase3_exit, "build_candidate_pool", return_value=bad_pool,
        ), patch.object(
            gravity, "resolve_for_retrieval",
            side_effect=AssertionError("UNRELEASED HISTORY MUST NOT BE SCORED"),
        ):
            result = gateway.read(
                runtime, clean_query, scope="MemoryOS", limit=4,
            )
        self.assertEqual(result["status"], "PASS_HEATDEATH_FALLBACK")
        self.assertEqual(result["effective_mode"], "HEATDEATH")
        self.assertFalse(result["galaxy_applied"])
        self.assertTrue(result["fallback_occurred"])
        self.assertEqual(
            result["retrieval"]["records"][0]["record_id"], probe.SAFE_ID,
        )
        self.assertNotIn(self.row[1], json.dumps(result))
        self.assertNotIn(self.row[3], json.dumps(result))

    def test_signed_held_record_forged_verified_graph_cannot_be_linked_context(self):
        runtime = self.load(include_synthetic_current=True)
        pool = _candidate(probe.SAFE_ROW)
        pool["linked_context_candidates"] = [{
            "record_id": self.rid,
            "verified_direct_primary_edges": [{
                "edge_id": probe.EDGE_ID,
                "source_record_id": self.rid,
                "target_record_id": probe.SAFE_ID,
                "status": "VERIFIED",
            }],
        }]
        with patch.object(
            galaxy_phase3_exit, "build_candidate_pool", return_value=pool,
        ), patch.object(
            gravity, "resolve_for_retrieval", return_value={
                "score": .5, "basis": "SYNTHETIC_TEST",
                "score_version": "SYNTHETIC_TEST",
                "backfill_required": False,
            },
        ):
            out = reader.operational(runtime, probe.SAFE_ROW["statement"])
        self.assertEqual(out["status"], "HOLD_UNRELEASED_LINKED_ARCHIVE")
        self.assertEqual(out["records"], [])
        self.assertEqual(out["writes_performed"], [])

    def _browser(self, rt, user_query, *, control=AUTH, pool=None):
        model = _FakeModel()
        mods = {"memcon_runtime": _module_for(rt)}
        patches = [
            patch.object(carrier, "API_KEY", SESSION_KEY),
            patch.object(carrier, "OPENAI_API_KEY", MODEL_KEY),
            patch.object(carrier, "OpenAI", return_value=model),
            patch.object(carrier, "_load_bundle", return_value={
                "gaiaos": {"source": "STAGE9AF-ISOLATED-SERVED-APP"},
            }),
            patch.object(carrier, "_carrier_instructions",
                         return_value="Trusted carrier. No memory injected."),
            patch.object(mode, "mode_status", return_value=control),
            patch.dict(sys.modules, mods),
        ]
        if pool is not None:
            patches.append(patch.object(
                galaxy_phase3_exit, "build_candidate_pool",
                return_value=pool,
            ))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        client = TestClient(deployed.app, base_url="https://testserver")
        self.assertIs(deployed.app, carrier.app)
        client.cookies.set(carrier.SESSION_COOKIE, carrier._session_token())
        result = client.post("/chat", json={
            "messages": [{"role": "user", "content": user_query}],
        })
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(model.calls[0]["instructions"],
                         "Trusted carrier. No memory injected.")
        self.assertNotIn("memory_context", result.json())
        self.assertNotIn(self.row[1], result.text)
        self.assertNotIn(self.row[3], result.text)
        self.assertNotIn(self.row[1], model.calls[0]["instructions"])
        self.assertNotIn(self.row[3], model.calls[0]["instructions"])

    def test_real_served_chat_actual_signed_archive_does_not_leak(self):
        self._browser(self.rt, self.row[1])

    def test_real_served_chat_clean_legacy_and_adversarial_galaxy_pool(self):
        self._browser(
            self.load(include_synthetic_current=True),
            probe.SAFE_ROW["statement"],
            pool=_candidate({"record_id": self.rid, "statement": self.row[1]}),
        )

    def test_after_signed_rollback_old_runtime_can_no_longer_read_imported_row(self):
        self.assertEqual(
            self.fx.rollback()["status"], "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN",
        )
        self.assertEqual(self.fx.state(), (0, 1, 1, 1))
        self.assertIsNone(self.load())
        self.assertEqual(self.rt.search_records("", 4, "MemoryOS")["records"], [])
        self.assertIsNone(self.rt.galaxy_record(self.rid))
        self.assertEqual(self.rt.proof()["held_signed_record_count"], 1)
        self.fx.protected()
        self._browser(self.rt, self.row[1])
        # The test adapter retains the creation-time proof marker, NOT a
        # snapshot of old private statements or an ability to re-read them.

    def test_tampering_after_initial_signed_proof_never_becomes_chat_current(self):
        self.fx.fx.conn.execute(
            "UPDATE memory_records SET status='ACTIVE' WHERE record_id=?",
            (self.rid,),
        )
        self.fx.fx.conn.commit()
        self.assertIsNone(self.load())
        actual = self.rt.galaxy_record(self.rid)["record"]
        self.assertEqual(actual["status"], "ACTIVE")
        self.assertTrue(actual["source"].startswith("galaxy-archive-v1:"))
        with patch.object(mode, "mode_status", return_value=HEATDEATH):
            result = gateway.read(
                self.rt, self.row[1], scope="MemoryOS", limit=4,
            )
        self.assertEqual(result["status"], "HOLD_UNRELEASED_ARCHIVE_IN_LEGACY")
        self.assertNotIn(self.row[1], json.dumps(result))

    def test_invalid_signature_source_schema_and_explicit_flag_refused(self):
        cases = [
            {"confirm_synthetic_local_only": False},
            {"original_signature": "0" * 64},
            {"original_key": b"wrong-fixture-key" * 3},
            {"original_receipt": {
                **self.receipt, "source_sha256": "0" * 64,
            }},
        ]
        for change in cases:
            with self.subTest(change=list(change)):
                self.assertIsNone(self.load(**change))
        original = self.fx.fx.conn.execute(
            "SELECT nonce_sha256 FROM galaxy_stage9v_canaries"
        ).fetchone()[0]
        self.fx.fx.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256='BAD-CANARY'"
        )
        self.fx.fx.conn.commit()
        self.assertIsNone(self.load())
        self.fx.fx.conn.execute(
            "UPDATE galaxy_stage9v_canaries SET nonce_sha256=?", (original,),
        )
        self.fx.fx.conn.commit()
        self.assertIsNotNone(self.load())
        self.fx.fx.conn.execute(
            "CREATE VIEW UNAPPROVED_TRIGGER_SURFACE AS SELECT 1 AS x"
        )
        self.fx.fx.conn.commit()
        self.assertIsNone(self.load())


if __name__ == "__main__":
    unittest.main()
