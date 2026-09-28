"""Actual Render-entrypoint tests with fake remote outage and disposable local DB.

No real Turso, provider call, production mutation, or generic recovery.
Each test launches a genuinely fresh subprocess and imports the actual bridge.
"""
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
CI_KEY = "CI-ONLY-NOT-OWNER-KEY-1234567890"

SCRIPT = r"""
import json
import os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import memcon_runtime as store

mode = os.environ["CI_TEST_BACKEND"]
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
assert store._INITIALIZED is False
calls = {"db": 0}
if mode == "remote_outage":
    assert store.STORAGE_BACKEND == "turso_libsql"
    def unavailable():
        calls["db"] += 1
        raise OSError("PRIVATE-SYNTHETIC-CONNECTION-STRING-NEVER-REVEAL")
    store._db = unavailable
else:
    assert mode == "healthy_local"
    assert store.STORAGE_BACKEND == "local_sqlite"

# Exactly the production entrypoint, not a special test FastAPI app.
import browser_memcon_bridge as bridge
import memcon_entrypoint as entry
import gaiaos_api as base
import gaiaos_app as source
# In Docker, copied GaiaOS/ sits alongside gaiaos_app.py under /app.
# In the GitHub checkout, the source directory is at the repository root.
# Exercise the identical canonical source without creating a fake app.
source.DEPLOYED_ROOT = Path.cwd().resolve()

assert bridge.app is entry.app
assert store._INITIALIZED is False
assert calls["db"] == 0
client = TestClient(bridge.app, base_url="https://testserver")
health = client.get("/health")
assert health.status_code == 200, health.text
assert health.json()["status"] == "ok"
assert calls["db"] == 0
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()

auth_error = client.get("/memconos/health")
assert auth_error.status_code == 401, auth_error.text
assert calls["db"] == 0
authorized = client.get("/memconos/health", headers={
    "Authorization": "Bearer " + os.environ["GAIAOS_API_KEY"]
})
client.cookies.set(base.SESSION_COOKIE, base._session_token())

if mode == "remote_outage":
    assert authorized.status_code == 503, authorized.text
    failure = authorized.json()["detail"]
    assert failure["status"] == "HOLD_STORAGE_UNAVAILABLE"
    assert failure["backend"] == "turso_libsql"
    assert failure["durability_verified"] is False
    assert failure["storage_reachable"] is False
    effects = failure["side_effects"]
    assert effects["schema_initialization_called"] is True
    assert effects["schema_ddl_possible"] is True
    assert effects["backend_connection_side_effects_possible"] is True
    assert effects["fresh_select_attempted"] is False
    assert effects["memory_promotion_requested"] is False
    assert effects["audit_receipt_insert_requested"] is False
    assert effects["backend_write_effects_exhaustively_measured"] is False
    assert "writes_performed" not in failure
    assert "PRIVATE-SYNTHETIC" not in authorized.text
    assert store._INITIALIZED is False
    assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
    before_boot = calls["db"]
    boot = client.post("/chat", json={
        "messages": [{"role": "user", "content": "Load GaiaOS"}],
        "include_memory": False,
    })
    assert boot.status_code == 200, boot.text
    assert "GAIAOS = ACTIVE / VERIFIED" in boot.json()["output"]
    assert calls["db"] == before_boot
    normal = client.post("/chat", json={
        "messages": [{"role": "user", "content": "ANVIL, report in"}],
        "include_memory": False,
    })
    assert normal.status_code == 503, normal.text
    hold = normal.json()["detail"]
    assert hold["status"] == "HOLD_SOLO_STATE_UNVERIFIED"
    assert hold["solo_identity_restored"] is False
    assert hold["generic_recovery_started"] is False
    assert "PRIVATE-SYNTHETIC" not in normal.text
    result = {
        "status": "PASS_MINIMAL_STARTUP_IDENTITY_BOUNDARY",
        "backend": store.STORAGE_BACKEND,
        "boot_db_reads": before_boot,
        "normal_member_operation": hold["status"],
        "generic_recovery_included": False,
        "schema_effects_reported": True,
    }
else:
    assert authorized.status_code == 200, authorized.text
    status = authorized.json()
    assert status["backend"] == "local_sqlite"
    assert status["remote_configured"] is False
    assert status["storage_reachable"] is True
    assert status["durability_verified"] is False
    assert status["durable_backend"] is False
    assert status["restart_canary_verified"] is False
    effects = status["side_effects"]
    assert effects["schema_initialization_called"] is True
    assert effects["schema_ddl_possible"] is True
    assert effects["backend_connection_side_effects_possible"] is True
    assert effects["fresh_select_attempted"] is True
    assert effects["memory_promotion_requested"] is False
    assert effects["audit_receipt_insert_requested"] is False
    assert effects["backend_write_effects_exhaustively_measured"] is False
    assert "writes_performed" not in status
    assert "database" not in status and "local_path" not in status
    assert Path(os.environ["MEMCONOS_DB_PATH"]).exists()
    # The already-initialized process must report that its next health
    # check skips schema DDL, while connection side effects remain possible.
    second = client.get("/memconos/health", headers={
        "Authorization": "Bearer " + os.environ["GAIAOS_API_KEY"]
    })
    assert second.status_code == 200, second.text
    effects_second = second.json()["side_effects"]
    assert effects_second["schema_ddl_possible"] is False
    assert effects_second["fresh_select_attempted"] is True
    assert effects_second["backend_connection_side_effects_possible"] is True
    # A later outage must not inherit the earlier successful health claim.
    with patch.object(
        store, "_db",
        side_effect=OSError("PRIVATE-SYNTHETIC-LATER-OUTAGE")
    ):
        later = client.get("/memconos/health", headers={
            "Authorization": "Bearer " + os.environ["GAIAOS_API_KEY"]
        })
    assert later.status_code == 503, later.text
    later_detail = later.json()["detail"]
    assert later_detail["status"] == "HOLD_STORAGE_UNAVAILABLE"
    assert later_detail["side_effects"]["schema_ddl_possible"] is False
    assert later_detail["side_effects"]["fresh_select_attempted"] is False
    assert later_detail["side_effects"]["backend_write_effects_exhaustively_measured"] is False
    assert "PRIVATE-SYNTHETIC-LATER-OUTAGE" not in later.text
    session = "CI-ISOLATED-ANVIL-SOLO"
    with store._db() as conn:
        conn.execute(
            "INSERT INTO solo_sessions(session_id,daemon,source,created_at,active) "
            "VALUES (?,?,?,?,1)",
            (session, "ANVIL", "CI-SYNTHETIC", "2026-09-28T00:00:00Z")
        )
    with patch.object(bridge, "_browser_session_id", return_value=session), \
         patch.object(bridge.solo_chat_runtime, "respond", return_value={
             "output": "58 · ANVIL 💗 ⌚ (¬‿¬): CI synthetic member response",
             "model": "CI_SYNTHETIC_NOT_A_PROVIDER_CALL",
         }) as member_response:
        normal = client.post("/chat", json={
            "messages": [{"role": "user", "content": "ANVIL, report in"}],
            "include_memory": False,
        })
    assert normal.status_code == 200, normal.text
    assert member_response.call_count == 1
    assert member_response.call_args.args[1]["daemon"] == "ANVIL"
    assert "ANVIL" in normal.json()["output"]
    result = {
        "status": "PASS_HEALTHY_LOCAL_MEMBER_ROUTING",
        "backend": store.STORAGE_BACKEND,
        "healthy_member": "ANVIL",
        "provider_calls": 0,
        "durability_verified": False,
        "schema_effects_reported": True,
        "later_outage_fails_closed": True,
    }

# Deliberately NOT importing /chat/recovery from the experimental PR chain.
assert client.get("/chat/recovery").status_code == 404
print(json.dumps(result))
"""

class MinimalStartupBoundary(unittest.TestCase):
    def run_in_fresh_process(self, mode: str):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "PYTHONPATH": str(ROOT / "api"),
                "MEMCONOS_DB_PATH": str(Path(temp) / "disposable.sqlite"),
                "GAIAOS_API_KEY": CI_KEY,
                "OPENAI_API_KEY": "CI-FAKE-NOT-A-PROVIDER-KEY",
                "RENDER_GIT_COMMIT": "CI-NOT-A-DEPLOYED-REVISION",
                "CI_TEST_BACKEND": mode,
            })
            if mode == "remote_outage":
                env["TURSO_DATABASE_URL"] = "libsql://ci-never-connect.invalid"
                env["TURSO_AUTH_TOKEN"] = "CI-FAKE-NOT-OWNER-TOKEN"
            else:
                env.pop("TURSO_DATABASE_URL", None)
                env.pop("TURSO_AUTH_TOKEN", None)
            result = subprocess.run(
                [sys.executable, "-c", textwrap.dedent(SCRIPT)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=40, check=False,
            )
            self.assertEqual(
                result.returncode, 0,
                "Fresh process failed:\n" + result.stderr[-7000:],
            )
            return json.loads(result.stdout.strip().splitlines()[-1])

    def test_fake_remote_outage(self):
        result = self.run_in_fresh_process("remote_outage")
        self.assertEqual(result["status"], "PASS_MINIMAL_STARTUP_IDENTITY_BOUNDARY")
        self.assertEqual(result["boot_db_reads"], 1)
        self.assertTrue(result["schema_effects_reported"])

    def test_healthy_local_member_routing(self):
        result = self.run_in_fresh_process("healthy_local")
        self.assertEqual(result["status"], "PASS_HEALTHY_LOCAL_MEMBER_ROUTING")
        self.assertEqual(result["healthy_member"], "ANVIL")
        self.assertEqual(result["provider_calls"], 0)
        self.assertTrue(result["schema_effects_reported"])
        self.assertTrue(result["later_outage_fails_closed"])

if __name__ == "__main__":
    unittest.main()
