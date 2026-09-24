"""Stage 5A: actual front-door and MemoryOS route wiring, preserving HEATDEATH."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
# This suite must not open the actual configured production store.
_DB = tempfile.TemporaryDirectory(prefix="gaiaos-stage5a-")
os.environ["MEMCONOS_DB_PATH"] = str(Path(_DB.name) / "stage5a.sqlite")
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ["RENDER_GIT_COMMIT"] = "stage5a-fixture-commit"

import gaiaos_app as carrier
import gaiaos_memory_mode as mode
import gaiaos_memory_gateway as gateway
import memcon_entrypoint as entry
import memcon_runtime as store


NATIVE = {
    "records": [{
        "record_id": "MEM-LEGACY-CI", "scope": "MemoryOS",
        "statement": "legacy stage five route",
        "source": "ci-known-record", "status": "ACTIVE",
    }],
    "count": 1,
    "runtime": "memconos.runtime.v2",
    "query_terms_applied": ["legacy"],
    "scope_applied": "MemoryOS",
    "query_filter_active": True,
}
GATEWAY = {
    "schema": gateway.SCHEMA,
    "status": "PASS_HEATDEATH",
    "effective_mode": mode.HEATDEATH,
    "configured_mode": None,
    "control_reason": "NO_PERSISTED_CONTROL",
    "retrieval": NATIVE,
    "galaxy_context": None,
    "galaxy_applied": False,
    "fallback_occurred": False,
    "writes_performed": [],
    "e_lanes_modified": False,
    "memory_context_authority": "NONE",
}


class Stage5ARoutes(unittest.TestCase):
    def setUp(self):
        patches = [
            patch.object(carrier, "_deployed_commit", return_value="ci-source"),
            patch.object(carrier, "_deployed_source",
                         return_value={"source_commit": "ci-source"}),
            patch.object(carrier, "_read_local_json",
                         return_value={"version": "ci", "platform_version": "ci"}),
            patch.object(carrier, "_infer_signals", return_value=[]),
            patch.object(carrier, "_requested_members_from_text", return_value=[]),
            patch.object(carrier.base, "_dispatch_packet", return_value={
                "selected": [], "unknown_requested_members": [],
            }),
            patch.object(carrier, "_compact_selected", return_value=[]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_default_frontdoor_keeps_legacy_no_memory_context(self):
        with patch.object(mode, "mode_status", return_value={
            "effective_mode": mode.HEATDEATH,
            "bigbang_activation_enabled": False,
        }), patch.object(gateway, "read",
                        side_effect=AssertionError("Unexpected memory read")):
            result = carrier._frontdoor_packet("legacy stage five",
                                               include_context=False)
        self.assertNotIn("memory_context", result)
        self.assertEqual(result["schema"], "gaiaos.frontdoor.packet.v1")
        self.assertEqual(result["route"]["mode"], "CONTEXT_ONLY")

    def test_explicit_legacy_read_uses_gateway_no_galaxy_preview(self):
        with patch.object(gateway, "read",
                          return_value=GATEWAY) as reader:
            result = carrier._frontdoor_packet(
                "tell me about legacy", include_context=False,
                include_memory=True, memory_query="legacy", context_limit=3,
            )
        self.assertEqual(result["memory_context"], GATEWAY)
        reader.assert_called_once_with(store, "legacy", "MemoryOS", 3)
        self.assertEqual(result["memory_context"]["retrieval"], NATIVE)

    def test_future_approved_bigbang_auto_routes_but_explicit_false_opts_out(self):
        approved = {
            "effective_mode": mode.BIGBANG,
            "configured_mode": mode.BIGBANG,
            "bigbang_activation_enabled": True,
        }
        with patch.object(mode, "mode_status", return_value=approved), patch.object(
            gateway, "read", return_value=GATEWAY
        ) as reader:
            automatic = carrier._frontdoor_packet(
                "meaningful recall", include_context=False
            )
            disabled = carrier._frontdoor_packet(
                "meaningful recall", include_context=False, include_memory=False
            )
        self.assertIn("memory_context", automatic)
        self.assertNotIn("memory_context", disabled)
        reader.assert_called_once_with(store, "meaningful recall", "MemoryOS", 6)

    def test_bigbang_unverified_never_autoloads_memory(self):
        blocked = {
            "effective_mode": mode.BIGBANG,
            "configured_mode": mode.BIGBANG,
            "bigbang_activation_enabled": False,
        }
        with patch.object(mode, "mode_status", return_value=blocked), patch.object(
            gateway, "read", side_effect=AssertionError("premature BIGBANG")
        ):
            result = carrier._frontdoor_packet("memory",
                                               include_context=False)
        self.assertNotIn("memory_context", result)

    def test_mcp_gaia_repaired_optional_parameters_are_defined(self):
        with patch.object(carrier, "_frontdoor_packet",
                          return_value={"source": "ci"}) as front:
            result = carrier.gaia(
                "status", include_context=False,
                include_memory=True, memory_query="legacy",
            )
        self.assertEqual(result["source"], "ci")
        front.assert_called_once_with("status", None, 3, False, 6, 1,
                                      True, "legacy")

    def test_http_assist_uses_same_gateway_args_and_auth(self):
        payload = carrier.GaiaAssistRequest(
            request="remember", include_context=False,
            include_memory=True, memory_query="legacy", context_limit=4,
        )
        with patch.object(carrier.base, "_authorize") as authorized, patch.object(
            carrier, "_frontdoor_packet", return_value={"schema": "ci"}
        ) as front:
            result = carrier.gaia_assist_http(payload, authorization="Bearer ci")
        self.assertEqual(result, {"schema": "ci"})
        authorized.assert_called_once_with("Bearer ci")
        front.assert_called_once_with(
            "remember", [], 3, False, 4, 1, True, "legacy"
        )

    def test_real_dynamic_memoryos_runtime_keeps_legacy_retrieval_envelope(self):
        with patch.object(carrier, "DEPLOYED_ROOT", ROOT):
            runtime = entry._memory_runtime()
        with patch.object(gateway, "read", return_value=GATEWAY) as reader:
            result = runtime.retrieve("legacy", "MemoryOS", 5)
        self.assertEqual(result["schema"], "gaiaos.memoryos.runtime.v1")
        self.assertEqual(result["retrieval"], NATIVE)
        self.assertEqual(result["status"], "OBSERVED")
        self.assertEqual(result["memory_gateway"]["effective_mode"], "HEATDEATH")
        self.assertNotIn("retrieval", result["memory_gateway"])
        self.assertEqual(result["context_authority"], "NONE")
        reader.assert_called_once_with(store, "legacy", "MemoryOS", 5)

    def test_dynamic_memoryos_holds_when_legacy_unavailable(self):
        with patch.object(carrier, "DEPLOYED_ROOT", ROOT):
            runtime = entry._memory_runtime()
        missing = dict(GATEWAY, status="HOLD_LEGACY_UNAVAILABLE", retrieval=None)
        with patch.object(gateway, "read", return_value=missing):
            result = runtime.retrieve("legacy", "MemoryOS", 5)
        self.assertEqual(result["status"], "HOLD")
        self.assertIsNone(result["retrieval"])
        self.assertFalse(result["memory_gateway"]["galaxy_applied"])

    def test_memoryos_http_and_mcp_routes_invoke_updated_runtime(self):
        with patch.object(carrier, "DEPLOYED_ROOT", ROOT):
            runtime = entry._memory_runtime()
        with patch.object(entry, "_memory_runtime", return_value=runtime), patch.object(
            carrier.base, "_authorize"
        ), patch.object(gateway, "read", return_value=GATEWAY):
            http = entry.memory_retrieve_http(
                q="legacy", scope="MemoryOS", limit=5, authorization="Bearer ci"
            )
            mcp = entry.memory_retrieve("legacy", "MemoryOS", 5)
        self.assertEqual(http["retrieval"], NATIVE)
        self.assertEqual(mcp["retrieval"], NATIVE)
        self.assertEqual(http["memory_gateway"]["effective_mode"], "HEATDEATH")

    def test_preservation_approval_and_separate_member_lanes_remain_untouched(self):
        with patch.object(carrier, "DEPLOYED_ROOT", ROOT):
            runtime = entry._memory_runtime()
        import inspect
        source = inspect.getsource(runtime.promote_candidate)
        self.assertIn("approved", source)
        self.assertIn("NAOMI", source)
        for name in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
            lane = ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS" / "IDENTITY-DATA" / f"{name}-EXPERIENCES.v1.md"
            self.assertTrue(lane.is_file())
        docker = (ROOT / "api" / "Dockerfile").read_text()
        for path in ("api/gaiaos_memory_gateway.py",
                     "api/gaiaos_memory_mode.py",
                     "api/legacy_memory_reader.py"):
            self.assertIn("COPY "+path, docker)


if __name__ == "__main__":
    unittest.main(verbosity=2)
