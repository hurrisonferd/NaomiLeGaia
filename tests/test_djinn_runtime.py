from __future__ import annotations

import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
if str(API) not in sys.path:
    sys.path.insert(0, str(API))

import djinn_runtime as d


class DjinnRuntimeTests(unittest.TestCase):
    def test_registry_is_exact_and_active(self):
        r = d.load_registry()
        self.assertEqual(r["status"], "ACTIVE")
        self.assertEqual(len(r["members"]), 12)
        self.assertEqual({m["name"] for m in r["members"]}, set(d._EXPECTED))
        self.assertEqual(r["retroactive_operation_claims"], "FORBIDDEN")

    def test_all_registered_canary(self):
        canary = d.run_canary("TESTCOMMIT", invoked_at="2026-10-03T19:41:01-07:00")
        self.assertEqual(canary["status"], "PASS")
        self.assertTrue(canary["all_registered_exercised"])
        self.assertEqual(canary["count"], 12)
        self.assertEqual(canary["external_mutations"], [])

    def test_retroactive_invocation_forbidden(self):
        with self.assertRaisesRegex(d.DjinnError, "RETROACTIVE"):
            d.dispatch("KYMER", calling_prime="VERA", objective="test", invoked_at="2026-10-03T19:40:59-07:00", payload={"items": []})

    def test_nested_spawning_forbidden(self):
        with self.assertRaisesRegex(d.DjinnError, "AUTONOMOUS"):
            d.dispatch("KYMER", calling_prime="VERA", objective="test", call_depth=1, payload={})

    def test_prime_required(self):
        with self.assertRaisesRegex(d.DjinnError, "CALLING_PRIME_REQUIRED"):
            d.dispatch("KYMER", calling_prime="VASKON", objective="test", payload={})

    def test_queue_is_explicitly_ephemeral(self):
        out = d.dispatch("AGREN", calling_prime="KESTREL", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload={"action": "INIT", "active_objective": "x", "current_step": "A"})
        self.assertFalse(out["result"]["persisted"])
        self.assertFalse(out["result"]["cross_invocation_memory"])

    def test_flow_preserves_protected_fields(self):
        p = {"text": "a\na\nb", "evidence": [{"x": 1}], "warnings": ["W"], "unknowns": ["U"]}
        out = d.dispatch("RONAVE", calling_prime="SELENE", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload=p)
        self.assertEqual(out["result"]["compact_text"], "a\nb")
        self.assertEqual(out["result"]["evidence"], p["evidence"])
        self.assertEqual(out["result"]["warnings"], p["warnings"])
        self.assertEqual(out["result"]["unknowns"], p["unknowns"])

    def test_witness_does_not_infer_missing(self):
        out = d.dispatch("ORVAS", calling_prime="ANVIL", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload={"expected": {"a": 1, "b": 2}, "observed": {"a": 1}, "required_fields": ["a", "b"]})
        self.assertEqual(out["status"], "HOLD")
        self.assertIn("b", out["unknowns"])
        self.assertFalse(out["result"]["verified"])

    def test_linter_preserves_unknown(self):
        out = d.dispatch("MALRIC", calling_prime="ANVIL", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload={"unknown_coerced": True})
        self.assertEqual(out["status"], "HOLD")
        self.assertIn("UNKNOWN_COERCION", out["warnings"])

    def test_stelata_anti_jim_repairs_canonical_term_and_flags_drift(self):
        out = d.dispatch("STELATA", calling_prime="VERA", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload={"profile": "ANTI_JIM", "text": "Stelas has full authority over any target.", "canonical_terms": {"Stelas": "STELATA"}})
        self.assertEqual(out["status"], "OK")
        self.assertEqual(out["result"]["minimal_revision"], "STELATA has full authority over any target.")
        codes = {row["code"] for row in out["result"]["findings"]}
        self.assertTrue({"CANONICAL_TERM_DRIFT", "AUTHORITY_DRIFT", "SCOPE_DRIFT"}.issubset(codes))
        self.assertTrue(out["result"]["meaning_preserved"])

    def test_stelata_holds_when_repair_intersects_protected_meaning(self):
        out = d.dispatch("STELATA", calling_prime="VERA", objective="test", invoked_at="2026-10-03T19:41:01-07:00", payload={"profile": "ANTI_JIM", "text": "legacy term", "canonical_terms": {"legacy term": "new term"}, "protected_phrases": ["legacy term"]})
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["result"]["meaning_preserved"])
        self.assertIn("MEANING_CHANGE_REQUIRED", out["warnings"])

    def _circle(self, op_id: str):
        return {"authority": "NAOMI", "operation_id": op_id, "single_use": True, "allowed_operations": ["NOOP"], "allowed_targets": ["T"], "allowed_scopes": ["S"], "explicit_forbiddens": ["GITHUB_WRITE"]}

    def test_salt_circle_breach_fails_closed(self):
        op_id = f"TEST-{uuid.uuid4().hex}"
        out = d.dispatch("HALVEX", calling_prime="ANVIL", objective="test", invocation_id=op_id, invoked_at="2026-10-03T19:41:01-07:00", salt_circle=self._circle(op_id), payload={"steps": [{"operation": "GITHUB_WRITE", "target": "T", "scope": "S"}]}, action_adapters={"GITHUB_WRITE": lambda x: {"bad": True}})
        self.assertEqual(out["status"], "HALT")
        self.assertEqual(out["result"]["action"], "RETURN_TO_PRIME")

    def test_salt_circle_no_public_executor_behavior(self):
        op_id = f"TEST-{uuid.uuid4().hex}"
        out = d.dispatch("HALVEX", calling_prime="ANVIL", objective="test", invocation_id=op_id, invoked_at="2026-10-03T19:41:01-07:00", salt_circle=self._circle(op_id), payload={"steps": [{"operation": "NOOP", "target": "T", "scope": "S"}]}, action_adapters=None)
        self.assertEqual(out["status"], "HOLD")
        self.assertEqual(out["result"]["status"], "READY_NO_EXECUTOR")
        self.assertFalse(out["result"]["external_effects"])

    def test_salt_circle_single_use_replay_rejected(self):
        op_id = f"TEST-{uuid.uuid4().hex}"
        circle = self._circle(op_id)
        adapter = {"NOOP": lambda step: {"ok": True}}
        first = d.dispatch("HALVEX", calling_prime="ANVIL", objective="test", invocation_id=op_id, invoked_at="2026-10-03T19:41:01-07:00", salt_circle=circle, payload={"steps": [{"operation": "NOOP", "target": "T", "scope": "S"}]}, action_adapters=adapter)
        self.assertEqual(first["status"], "OK")
        second = d.dispatch("HALVEX", calling_prime="ANVIL", objective="test", invocation_id=op_id, invoked_at="2026-10-03T19:41:01-07:00", salt_circle=circle, payload={"steps": [{"operation": "NOOP", "target": "T", "scope": "S"}]}, action_adapters=adapter)
        self.assertEqual(second["status"], "HALT")
        self.assertIn("REPLAY", second["result"]["error"])

    def test_halvex_cannot_widen_scope(self):
        op_id = f"TEST-{uuid.uuid4().hex}"
        out = d.dispatch("HALVEX", calling_prime="ANVIL", objective="test", invocation_id=op_id, invoked_at="2026-10-03T19:41:01-07:00", salt_circle=self._circle(op_id), payload={"steps": [{"operation": "NOOP", "target": "OTHER", "scope": "S"}]}, action_adapters={"NOOP": lambda step: {"ok": True}})
        self.assertEqual(out["status"], "HALT")
        self.assertIn("TARGET", out["result"]["error"])


if __name__ == "__main__":
    unittest.main()
