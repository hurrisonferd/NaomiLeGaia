"""Stage 5C: prove full normal HEATDEATH chat can BOOT with GALAXY broken."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_lazy_diagnostics as lazy


class HeatdeathBootIsolationTests(unittest.TestCase):
    def test_lazy_allowlist_rejects_unregistered_module(self):
        with self.assertRaises(ValueError):
            lazy.deferred("os")
        with self.assertRaises(ValueError):
            lazy.deferred("gaiaos_api")
        self.assertEqual(lazy.deferred("galaxy_phase5").module_name, "galaxy_phase5")
        self.assertEqual(lazy.deferred("augury_ritual").module_name, "augury_ritual")

    def test_unavailable_diagnostic_holds_only_on_explicit_attribute_use(self):
        import fastapi
        optional = lazy.deferred("galaxy_phase4")
        with patch.object(
            lazy.importlib, "import_module",
            side_effect=ImportError("forced broken GALAXY"),
        ) as loader:
            self.assertEqual(optional.module_name, "galaxy_phase4")
            loader.assert_not_called()
            with self.assertRaises(fastapi.HTTPException) as ctx:
                optional.review_pair
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(
            ctx.exception.detail["status"],
            "HOLD_OPTIONAL_DIAGNOSTIC_UNAVAILABLE",
        )
        self.assertNotIn("forced broken", str(ctx.exception.detail))

    def test_optional_modules_stay_unimported_when_proxy_created(self):
        with patch.object(
            lazy.importlib, "import_module",
            side_effect=AssertionError("eager optional module import"),
        ) as loader:
            modules = (
                "galaxy_production", "galaxy_quality",
                "galaxy_phase3_exit", "galaxy_phase4",
                "galaxy_phase5", "galaxy_phase5_controls",
                "galaxy_phase6", "galaxy_phase6_controls",
                "galaxy_phase7", "galaxy_phase7_tombstone",
                "galaxy_phase7_tombstone_shadow",
                "galaxy_phase7_isolated_restore", "augury_ritual",
            )
            for name in modules:
                self.assertEqual(lazy.deferred(name).module_name, name)
            loader.assert_not_called()

    def test_normal_carrier_boots_serves_legacy_chat_and_source_boot_with_broken_galaxy(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "isolated.sqlite")
            script = textwrap.dedent(r"""
                import asyncio, builtins, json, sys
                from pathlib import Path
                real_import = builtins.__import__
                attempted = []
                def sabotage(name, *args, **kwargs):
                    if name.startswith("galaxy_") or name == "augury_ritual":
                        attempted.append(name)
                        raise ImportError("research subsystem deliberately broken")
                    return real_import(name, *args, **kwargs)
                builtins.__import__ = sabotage

                import browser_memcon_bridge as bridge
                import gaiaos_memory_gateway as gateway
                assert bridge.app is not None
                assert not attempted, f"Optional modules eagerly imported: {attempted}"
                assert not any(k.startswith("galaxy_") for k in sys.modules)
                assert "augury_ritual" not in sys.modules

                # The regular HEATDEATH chat retains its original hosted-call
                # envelope. The test deliberately stubs the OpenAI network call.
                bridge.gaiaos_api._authorize_browser_session = lambda _: None
                bridge._original_chat = lambda payload, request: {
                    "output": "legacy hosted chat still answers",
                    "model": "ci-only",
                    "source": "baseline",
                }
                class Request:
                    cookies = {bridge.gaiaos_api.SESSION_COOKIE: "ci-cookie"}
                    async def json(self):
                        return {"messages": [{
                            "role": "user", "content": "ordinary legacy question"
                        }]}
                reply = asyncio.run(bridge.browser_chat(Request()))
                assert reply["output"] == "legacy hosted chat still answers", reply
                assert "memory_gateway_receipt" not in reply

                # Original, current-source bootstrap still loads all six
                # canonical identities without importing GALAXY.
                bridge.gaiaos_app.DEPLOYED_ROOT = Path.cwd()
                boot = bridge.gaiaos_app._boot_packet("CI_BROKEN_GALAXY")
                assert boot["status"] == "ACTIVE", boot
                assert len(boot["roster"]) == 6, boot

                # Create an isolated approved fixture only in temporary CI SQLite.
                runtime = bridge.memcon_runtime
                record = runtime.write_record(
                    authority="NAOMI", approved=True, record_type="CI_FIXTURE",
                    scope="MemoryOS", record_id="CI-HEATDEATH-1",
                    statement="legacy memory with broken galaxy",
                    source="ci:real-sqlite",
                )
                assert record["record"]["record_id"] == "CI-HEATDEATH-1"
                gateway_read = gateway.read(
                    runtime, "legacy memory", "MemoryOS", 4
                )
                assert gateway_read["status"] == "PASS_HEATDEATH", gateway_read
                assert [row["record_id"] for row in gateway_read["retrieval"]["records"]] == ["CI-HEATDEATH-1"]
                assert gateway_read["galaxy_context"] is None
                assert not any(k.startswith("galaxy_") for k in sys.modules)
                print(json.dumps({
                    "status": "PASS_HEATDEATH_FULL_NORMAL_CARRIER_START",
                    "ordinary_chat": reply["output"],
                    "boot_roster": len(boot["roster"]),
                    "memory_record": gateway_read["retrieval"]["records"][0]["record_id"],
                    "optional_import_attempts": attempted,
                }))
            """)
            env = dict(os.environ)
            env.pop("TURSO_DATABASE_URL", None)
            env.pop("TURSO_AUTH_TOKEN", None)
            env["MEMCONOS_DB_PATH"] = database
            env["PYTHONPATH"] = str(ROOT / "api")
            env["RENDER_GIT_COMMIT"] = "CI-only-source"
            env["GAIAOS_FORCE_HEATDEATH"] = "1"
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=ROOT, env=env, text=True,
                capture_output=True, timeout=50,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + "\n" + proc.stdout)
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"], "PASS_HEATDEATH_FULL_NORMAL_CARRIER_START")
            self.assertEqual(data["boot_roster"], 6)
            self.assertEqual(data["memory_record"], "CI-HEATDEATH-1")
            self.assertEqual(data["optional_import_attempts"], [])

    def test_browser_bridge_source_uses_deferred_galaxy_and_augury_imports(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text()
        docker = (ROOT / "api" / "Dockerfile").read_text()
        for module in ("galaxy_production", "galaxy_quality",
                       "galaxy_phase3_exit", "galaxy_phase4",
                       "galaxy_phase5", "galaxy_phase5_controls",
                       "galaxy_phase6", "galaxy_phase6_controls",
                       "galaxy_phase7", "galaxy_phase7_tombstone",
                       "galaxy_phase7_tombstone_shadow",
                       "galaxy_phase7_isolated_restore", "augury_ritual"):
            self.assertNotIn("\nimport " + module + "\n", bridge)
            self.assertIn(module + ' = deferred("' + module + '")', bridge)
        self.assertIn(
            "COPY api/gaiaos_lazy_diagnostics.py", docker
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
