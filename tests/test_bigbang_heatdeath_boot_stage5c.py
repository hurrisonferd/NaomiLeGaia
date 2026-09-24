"""Stage 5C: normal HEATDEATH carrier works when ALL GALAXY imports fail."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def isolated(script: str, db: str) -> dict:
    env = dict(os.environ)
    env.pop("TURSO_DATABASE_URL", None)
    env.pop("TURSO_AUTH_TOKEN", None)
    env["MEMCONOS_DB_PATH"] = db
    env["RENDER_GIT_COMMIT"] = "stage5c-isolated-test"
    env["GAIAOS_FORCE_HEATDEATH"] = "1"
    env["PYTHONPATH"] = str(ROOT / "api")
    proc = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=45,
    )
    if proc.returncode:
        raise AssertionError(
            f"independent HEATDEATH test failed ({proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return json.loads(proc.stdout)


class BootSafeLegacyCarrier(unittest.TestCase):
    def test_lazy_research_proxy_import_never_loads_galaxy(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = isolated(
                """
                import builtins, json, sys
                original = builtins.__import__
                def blocked(name, *args, **kwargs):
                    if name.startswith("galaxy") or name == "augury_ritual":
                        raise ImportError("simulated corrupt GALAXY module")
                    return original(name, *args, **kwargs)
                builtins.__import__ = blocked
                import gaiaos_optional_research
                # importlib.import_module bypasses a patched builtins.__import__
                # in modern Python; sabotage BOTH paths, including the path
                # actually used by LazyResearchModule.
                original_lazy_import = gaiaos_optional_research.import_module
                def blocked_lazy_import(name, *args, **kwargs):
                    if name.startswith("galaxy") or name == "augury_ritual":
                        raise ImportError("simulated broken optional module")
                    return original_lazy_import(name, *args, **kwargs)
                gaiaos_optional_research.import_module = blocked_lazy_import
                holder = gaiaos_optional_research.LazyResearchModule("galaxy_phase4")
                assert "galaxy_phase4" not in sys.modules
                failed = False
                try:
                    holder.FIXTURE_CORE_ID
                except ImportError:
                    failed = True
                print(json.dumps({"import_deferred": True,
                                  "invocation_fails_cleanly": failed,
                                  "no_galaxy_loaded": not any(
                                      x.startswith("galaxy") for x in sys.modules)}))
                """,
                str(Path(tmp) / "isolated.sqlite"),
            )
        self.assertTrue(all(result.values()), result)

    def test_full_normal_legacy_app_boots_with_corrupted_galaxy_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = isolated(
                """
                import builtins, json, sys
                from pathlib import Path
                from unittest.mock import patch
                original = builtins.__import__
                banned = []
                def blocked(name, *args, **kwargs):
                    if name.startswith("galaxy") or name == "augury_ritual":
                        banned.append(name)
                        raise ImportError("simulated unusable research subsystem")
                    return original(name, *args, **kwargs)
                builtins.__import__ = blocked
                import browser_memcon_bridge as browser
                import gaiaos_app as carrier
                import gaiaos_api as api
                import memcon_entrypoint as entry
                import memcon_runtime as storage
                from fastapi.testclient import TestClient

                # A realistic isolated record is only a CI fixture and is never
                # inserted into Naomi's configured production memory store.
                storage.write_record(
                    authority="NAOMI", approved=True, record_type="FIXTURE",
                    scope="MemoryOS", statement="legacy durable continuity",
                    source="isolated-test-record", record_id="CI-HEATDEATH-1",
                )
                app = browser.app
                client = TestClient(app)
                client.cookies.set(api.SESSION_COOKIE, "ci-only-session")
                root = Path.cwd()
                def baseline():
                    with storage._db() as conn:
                        return tuple(conn.execute("SELECT count(*) FROM "+t
                            ).fetchone()[0] for t in (
                            "memory_records","memory_relations","memory_gravity",
                            "memory_importance","runtime_receipts"))
                before = baseline()
                with patch.object(carrier, "DEPLOYED_ROOT", root), patch.object(
                    api, "_authorize_browser_session"
                ), patch.object(
                    api, "_authorize"
                ), patch.object(
                    browser, "_original_chat",
                    return_value={"output":"original legacy chat","model":"ci","source":"ci"}
                ), patch.object(
                    carrier.base, "_dispatch_packet",
                    return_value={"selected":[],"unknown_requested_members":[]}
                ), patch.object(
                    carrier, "_infer_signals", return_value=[]
                ), patch.object(
                    carrier, "_requested_members_from_text", return_value=[]
                ), patch.object(
                    carrier, "_compact_selected", return_value=[]
                ):
                    chat = client.post("/chat", json={"messages":[{
                        "role":"user","content":"is our legacy path available?"
                    }]})
                    status = client.get("/galaxy/status")
                    blocked_research = client.post(
                        "/galaxy/production/activate",
                        json={"authority":"NAOMI","approved":True},
                    )
                    blocked_text = client.post("/chat", json={"messages":[{
                        "role":"user","content":"GALAXY PROPOSE illegal-before-BIGBANG"
                    }]})
                    memory = client.get("/memoryos/retrieve", params={
                        "q":"legacy durable","scope":"MemoryOS","limit":5
                    })
                    assist = client.post("/gaiaos/assist", json={
                        "request":"legacy durable", "include_context":False,
                        "include_memory":True,"memory_query":"legacy durable"
                    })
                    mcp_memory = entry.memory_retrieve(
                        "legacy durable", "MemoryOS", 5
                    )
                    mcp_frontdoor = carrier.gaia(
                        "legacy durable", include_context=False
                    )
                after = baseline()
                result = {
                    "booted": app is not None,
                    "chat_status": chat.status_code,
                    "chat_original": chat.json() == {
                        "output":"original legacy chat","model":"ci","source":"ci"
                    },
                    "research_status_off": status.json().get("effective_mode") == "HEATDEATH",
                    "research_write_blocked": blocked_research.status_code == 503,
                    "research_text_blocked": (
                        blocked_text.json().get("output","").startswith(
                            "GALAXY DISABLED BY HEATDEATH")
                    ),
                    "memory_status": memory.status_code,
                    "native_ids": [
                        r["record_id"] for r in (
                            memory.json().get("retrieval") or {}).get("records", [])
                    ],
                    "assist_status": assist.status_code,
                    "assist_legacy": (assist.json().get("memory_context") or {}).get(
                        "effective_mode") == "HEATDEATH",
                    "mcp_native_ids": [
                        r["record_id"] for r in (
                            mcp_memory.get("retrieval") or {}).get("records", [])
                    ],
                    "mcp_frontdoor_unmodified": "memory_context" not in mcp_frontdoor,
                    "zero_galaxy_import_attempts": len(banned) == 0,
                    "no_galaxy_modules_loaded": not any(
                        n.startswith("galaxy") or n == "augury_ritual"
                        for n in sys.modules
                    ),
                    "protected_table_counts_unchanged": before == after,
                }
                print(json.dumps(result))
                client.close()
                """,
                str(Path(tmp) / "known-good.sqlite"),
            )
        self.assertTrue(result["booted"])
        self.assertEqual(result["chat_status"], 200, result)
        self.assertTrue(result["chat_original"], result)
        self.assertTrue(result["research_status_off"], result)
        self.assertTrue(result["research_write_blocked"], result)
        self.assertTrue(result["research_text_blocked"], result)
        self.assertEqual(result["memory_status"], 200, result)
        self.assertEqual(result["native_ids"], ["CI-HEATDEATH-1"], result)
        self.assertEqual(result["assist_status"], 200, result)
        self.assertTrue(result["assist_legacy"], result)
        self.assertEqual(result["mcp_native_ids"], ["CI-HEATDEATH-1"], result)
        self.assertTrue(result["mcp_frontdoor_unmodified"], result)
        self.assertTrue(result["zero_galaxy_import_attempts"], result)
        self.assertTrue(result["no_galaxy_modules_loaded"], result)
        self.assertTrue(result["protected_table_counts_unchanged"], result)

    def test_required_docker_imports_and_recovery_separation(self):
        main = (ROOT / "api" / "Dockerfile").read_text()
        recovery = (ROOT / "api" / "Dockerfile.legacy-recovery").read_text()
        self.assertIn("COPY api/gaiaos_optional_research.py", main)
        self.assertIn("COPY api/gaiaos_chat_memory.py", main)
        self.assertNotIn("COPY api/gaiaos_optional_research.py", recovery)
        self.assertNotIn("COPY api/browser_memcon_bridge.py", recovery)

    def test_guard_does_not_promote_or_rewrite_any_candidate(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text()
        start = bridge.index("def _research_mode_authorized(")
        end = bridge.index('@app.post("/chat",', start)
        gate = bridge[start:end]
        self.assertIn("GAIAOS", bridge)
        self.assertIn("HOLD_GALAXY_DISABLED_BY_HEATDEATH", gate)
        for forbidden in (
            "write_record(", "promote_candidate(", "INSERT INTO ",
            "DELETE FROM ", "galaxy_production.activate(",
        ):
            self.assertNotIn(forbidden, gate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
