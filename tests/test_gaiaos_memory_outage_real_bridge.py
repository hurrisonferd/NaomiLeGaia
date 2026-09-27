"""Actual Render GaiaOS carrier boot/recovery, with Turso forcibly unavailable.

Every case starts an ISOLATED FRESH PROCESS and imports the actual
browser_memcon_bridge entrypoint. The offline remote case supplies only
SYNTHETIC provider-shaped variables and monkeypatches _db BEFORE the import:
a real Turso connection is impossible, and no original database is touched.

A SOLO session cannot be declared absent during an outage, so ordinary
/chat HOLDS rather than pretending the browser has exited SOLO. The distinct
explicit /chat/recovery path can serve generic non-SOLO hosted chat with
signed browser session + positive, no-memory acknowledgment, without any DB.
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

OUTAGE_SCRIPT = r"""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import memcon_runtime as store
assert store._INITIALIZED is False
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
calls = {"db": 0}
def unavailable():
    calls["db"] += 1
    raise OSError("PRIVATE-SYNTHETIC-CONNECTION-STRING-NEVER-REVEAL")
store._db = unavailable

# The ACTUAL Docker entrypoint must import without accessing the backend.
import browser_memcon_bridge as bridge
import memcon_entrypoint as entry
import gaiaos_api as base
from fastapi.testclient import TestClient
assert store._INITIALIZED is False
assert calls["db"] == 0
client = TestClient(bridge.app, base_url="https://testserver")

live = client.get("/health")
assert live.status_code == 200, live.text
assert live.json()["status"] == "ok"
assert calls["db"] == 0

unauthorized = client.get("/memconos/health")
assert unauthorized.status_code == 401, unauthorized.text
assert calls["db"] == 0
down = client.get(
    "/memconos/health",
    headers={"Authorization": "Bearer " + os.environ["GAIAOS_API_KEY"]},
)
assert down.status_code == 503, down.text
assert down.json()["detail"]["status"] == "HOLD_STORAGE_UNAVAILABLE"
assert down.json()["detail"]["backend"] == os.environ["CI_BACKEND_EXPECTED"]
assert down.json()["detail"]["durability_verified"] is False
assert "PRIVATE-SYNTHETIC" not in down.text
assert store._INITIALIZED is False

client.cookies.set(base.SESSION_COOKIE, base._session_token())
page = client.get("/chat/recovery")
assert page.status_code == 200, page.text
assert "new, generic chat" in page.text
assert "recovery_acknowledged:true" in page.text
assert page.headers["cache-control"] == "no-store"
assert calls["db"] == 1
normal = client.post("/chat", json={
    "messages": [{"role": "user", "content": "General, non-Daemon question"}],
    "include_memory": False,
})
assert normal.status_code == 503, normal.text
assert normal.json()["detail"]["status"] == "HOLD_SOLO_STATE_UNVERIFIED"
assert normal.json()["detail"]["solo_identity_restored"] is False
assert normal.json()["detail"]["recovery_endpoint"] == "/chat/recovery"
assert "PRIVATE-SYNTHETIC" not in normal.text
before = calls["db"]

missing = client.post("/chat/recovery", json={
    "messages": [{"role": "user", "content": "General offline question"}],
    "include_memory": False,
})
assert missing.status_code == 409, missing.text
assert missing.json()["detail"]["status"] == (
    "HOLD_EXPLICIT_NO_MEMORY_RECOVERY_ACK_REQUIRED"
)
wrong_memory = client.post("/chat/recovery", json={
    "messages": [{"role": "user", "content": "General offline question"}],
    "include_memory": True, "recovery_acknowledged": True,
})
assert wrong_memory.status_code == 409, wrong_memory.text
wrong_truthy = client.post("/chat/recovery", json={
    "messages": [{"role": "user", "content": "General offline question"}],
    "include_memory": False, "recovery_acknowledged": 1,
})
assert wrong_truthy.status_code == 409, wrong_truthy.text
past_solo = client.post("/chat/recovery", json={
    "messages": [
        {"role": "assistant", "content": "Previous SOLO conversation"},
        {"role": "user", "content": "New generic offline question"},
    ],
    "include_memory": False, "recovery_acknowledged": True,
})
assert past_solo.status_code == 409, past_solo.text
assert past_solo.json()["detail"]["status"] == (
    "HOLD_START_FRESH_GENERIC_MESSAGE_ONLY"
)
assert calls["db"] == before

class FakeProvider:
    def __init__(self):
        self.calls = []
        self.responses = SimpleNamespace(create=self.create)
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Generic CI response without memory.")

provider = FakeProvider()
with patch.object(base, "OpenAI", return_value=provider), \
     patch.object(base, "_load_bundle", return_value={
         "gaiaos": {"source": "CI-SYNTHETIC-SOURCE-NOT-A-DEPLOY"},
     }), \
     patch.object(base, "_carrier_instructions",
                  return_value="CI generic source-verified instructions"):
    generic = client.post("/chat/recovery", json={
        "messages": [{"role": "user", "content": "General offline question"}],
        "include_memory": False, "recovery_acknowledged": True,
    })

assert generic.status_code == 200, generic.text
assert generic.json()["output"] == "Generic CI response without memory."
assert "memory_context" not in generic.json()
receipt = generic.json()["recovery_receipt"]
assert receipt["status"] == "PASS_EXPLICIT_PLAIN_CHAT_NO_MEMORY"
assert receipt["solo_state_checked"] is False
assert receipt["solo_session_restored"] is False
assert receipt["memconos_backend_access_attempted"] is False
assert receipt["bigbang_activated"] is False
assert receipt["e_lanes_modified"] is False
assert receipt["memory_writes_performed"] == []
assert len(provider.calls) == 1
assert provider.calls[0]["instructions"] == (
    "CI generic source-verified instructions"
)
assert calls["db"] == before
assert store._INITIALIZED is False
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
print(json.dumps({
    "status": "PASS_ISOLATED_REAL_BRIDGE_OUTAGE",
    "backend": os.environ["CI_BACKEND_EXPECTED"],
    "boot_attempted_db_calls": 0,
    "memcon_health": down.json()["detail"]["status"],
    "normal_chat": normal.json()["detail"]["status"],
    "explicit_recovery": receipt["status"],
    "recovery_backend_queries": calls["db"] - before,
    "solo_restored": receipt["solo_session_restored"],
    "actual_render_entrypoint": bridge.app is entry.app,
}))
"""

HEALTHY_SCRIPT = r"""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import memcon_runtime as store
assert store.STORAGE_BACKEND == "local_sqlite"
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
import browser_memcon_bridge as bridge
import memcon_entrypoint as entry
import gaiaos_api as base
from fastapi.testclient import TestClient
assert store._INITIALIZED is False
# Import and even independent carrier liveness must not create a database.
client = TestClient(bridge.app, base_url="https://testserver")
assert client.get("/health").status_code == 200
home = client.get("/")
assert home.status_code == 200, home.text
assert "/chat/recovery" in home.text
assert "SOLO state cannot be checked" in home.text
assert store._INITIALIZED is False
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()
auth = {"Authorization": "Bearer " + os.environ["GAIAOS_API_KEY"]}
memhealth = client.get("/memconos/health", headers=auth)
assert memhealth.status_code == 200, memhealth.text
health = memhealth.json()
assert health["status"] == "ok"
assert health["backend"] == "local_sqlite"
assert health["remote_configured"] is False
assert health["storage_reachable"] is True
assert health["durability_verified"] is False
assert health["durable_backend"] is False
assert health["restart_canary_verified"] is False
assert health["writes_performed"] == []
assert "database" not in health and "local_path" not in health
assert os.environ["MEMCONOS_DB_PATH"] not in memhealth.text
assert Path(os.environ["MEMCONOS_DB_PATH"]).exists()

class FakeProvider:
    def __init__(self):
        self.calls = []
        self.responses = SimpleNamespace(create=self.create)
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Original generic carrier answer.")

provider = FakeProvider()
client.cookies.set(base.SESSION_COOKIE, base._session_token())
with patch.object(base, "OpenAI", return_value=provider), \
     patch.object(base, "_load_bundle", return_value={
         "gaiaos": {"source": "CI-SYNTHETIC-ORIGINAL-CARRIER"},
     }), \
     patch.object(base, "_carrier_instructions",
                  return_value="Original CI source instructions"):
    plain = client.post("/chat", json={
        "messages": [{"role":"user","content":"General engineering question"}],
        "include_memory": False,
    })
assert plain.status_code == 200, plain.text
assert len(provider.calls) == 1
assert provider.calls[0]["instructions"] == "Original CI source instructions"
assert "memory_context" not in plain.json()
assert store._INITIALIZED is True
print(json.dumps({
    "status": "PASS_HEALTHY_REAL_RENDER_DEFERRED_INIT",
    "boot_created_database": False,
    "memory_health_readable": health["storage_reachable"],
    "durability_verified": health["durability_verified"],
    "ordinary_chat": plain.status_code,
    "actual_render_entrypoint": bridge.app is entry.app,
}))
"""


class RealRenderBootIsolationTests(unittest.TestCase):
    def run_isolated(self, code: str, *, remote: bool) -> dict:
        with tempfile.TemporaryDirectory(prefix="gaia-real-boot-no-secrets-") as tmp:
            db = Path(tmp) / "synthetic-only.sqlite"
            env = dict(os.environ)
            for key in (
                "TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN",
                "MEMCONOS_DB_PATH", "GAIAOS_FORCE_HEATDEATH",
                "GALAXY_PRODUCTION_PILOT_KILL_SWITCH",
                "GALAXY_FRONTDOOR_KILL_SWITCH",
            ):
                env.pop(key, None)
            env.update({
                "PYTHONPATH": str(ROOT / "api"),
                "GAIAOS_API_KEY": CI_KEY,
                "OPENAI_API_KEY": "CI-ONLY-FAKE-MODEL-KEY",
                "RENDER_GIT_COMMIT": "CI-NOT-A-REAL-DEPLOY",
                "MEMCONOS_DB_PATH": str(db),
                "CI_BACKEND_EXPECTED":
                    "turso_libsql" if remote else "local_sqlite",
            })
            if remote:
                # This is not a real database/token. _db is replaced before
                # importing the actual app; no network request can happen.
                env["TURSO_DATABASE_URL"] = (
                    "libsql://ci-disposable-never-connect.invalid"
                )
                env["TURSO_AUTH_TOKEN"] = "CI-FAKE-NOT-OWNER-TOKEN"
            completed = subprocess.run(
                [sys.executable, "-c", textwrap.dedent(code)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=40, check=False,
            )
            self.assertEqual(
                completed.returncode, 0,
                "Isolated carrier test failed:\n" +
                completed.stderr[-7000:] + completed.stdout[-1000:],
            )
            return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_actual_render_import_and_explicit_recovery_with_local_storage_down(self):
        result = self.run_isolated(OUTAGE_SCRIPT, remote=False)
        self.assertEqual(result["status"], "PASS_ISOLATED_REAL_BRIDGE_OUTAGE")
        self.assertEqual(result["backend"], "local_sqlite")
        self.assertEqual(result["recovery_backend_queries"], 0)
        self.assertFalse(result["solo_restored"])

    def test_actual_render_import_and_explicit_recovery_with_fake_remote_outage(self):
        result = self.run_isolated(OUTAGE_SCRIPT, remote=True)
        self.assertEqual(result["status"], "PASS_ISOLATED_REAL_BRIDGE_OUTAGE")
        self.assertEqual(result["backend"], "turso_libsql")
        self.assertEqual(result["boot_attempted_db_calls"], 0)
        self.assertEqual(result["recovery_backend_queries"], 0)

    def test_healthy_local_backend_only_initializes_on_authenticated_memory_request(self):
        result = self.run_isolated(HEALTHY_SCRIPT, remote=False)
        self.assertEqual(
            result["status"], "PASS_HEALTHY_REAL_RENDER_DEFERRED_INIT",
        )
        self.assertFalse(result["boot_created_database"])
        self.assertFalse(result["durability_verified"])
        self.assertEqual(result["ordinary_chat"], 200)


if __name__ == "__main__":
    unittest.main()
