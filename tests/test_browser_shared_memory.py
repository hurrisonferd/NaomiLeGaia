"""Shared signed-browser MemoryOS bridge in isolated SQLite; no remote writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r'''
import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import shared_memory_browser_bridge as bridge
import browser_memcon_bridge as legacy
import gaiaos_api as base
import gaiaos_app as source
import memcon_runtime as store

source.DEPLOYED_ROOT = Path.cwd()
client = TestClient(bridge.app, base_url="https://testserver")

def command(name, data):
    return client.post("/chat", json={"messages":[{"role":"user","content":name+" "+json.dumps(data)}]})

def body(response):
    assert response.status_code == 200, response.text
    return json.loads(response.json()["output"].split("\n",1)[1])

def circle(operation, scope, operation_id):
    return {
        "authority":"NAOMI",
        "operation_id":operation_id,
        "single_use":True,
        "allowed_operations":[operation],
        "allowed_targets":["MEMORYOS_SHARED_BROWSER"],
        "allowed_scopes":[scope],
        "explicit_forbiddens":["GITHUB_WRITE","ELANE_WRITE","DEPLOY","RESTART","CROSS_MEMBER_MERGE"],
    }

scope = "GaiaOS:DjinnOS"
observation = {
    "owner":"NAOMI",
    "scope":scope,
    "statement":"CI shared GaiaOS DjinnOS continuity marker",
    "source":"CI-isolated",
    "why_material":"CI shared browser boundary proof",
    "record_type":"INTERACTION",
    "salt_circle":circle("SHARED_CANDIPULL",scope,"CI-SHARED-CANDIDATE-1"),
}

# Signed browser session is mandatory.
assert command("SHARED-CANDIPULL", observation).status_code == 401
client.cookies.set(base.SESSION_COOKIE, "invalid")
assert command("SHARED-CANDIPULL", observation).status_code == 401
client.cookies.set(base.SESSION_COOKIE, base._session_token())

# Owner/scope/type are narrow and fail closed.
assert command("SHARED-CANDIPULL", {**observation,"owner":"VERA"}).status_code == 403
assert command("SHARED-CANDIPULL", {**observation,"scope":"ChatOS"}).status_code == 422
assert command("SHARED-CANDIPULL", {**observation,"scope":"Solo:VERA"}).status_code == 422
assert command("SHARED-CANDIPULL", {**observation,"record_type":"TEST"}).status_code == 422

# Wrong SALT_CIRCLE scope or target is forbidden.
bad_scope_circle = circle("SHARED_CANDIPULL", "GaiaOS:Continuity", "CI-BAD-SCOPE")
assert command("SHARED-CANDIPULL", {**observation,"salt_circle":bad_scope_circle}).status_code == 403
bad_target = circle("SHARED_CANDIPULL", scope, "CI-BAD-TARGET")
bad_target["allowed_targets"] = ["SOMETHING_ELSE"]
assert command("SHARED-CANDIPULL", {**observation,"salt_circle":bad_target}).status_code == 403

# Create a real non-durable shared candidate.
created = body(command("SHARED-CANDIPULL", observation))["created"][0]
assert created["owner"] == "NAOMI"
assert created["scope"] == scope
assert created["status"] == "CANDIDATE"
cid = created["candidate_id"]

# SALT_CIRCLE is single-use.
assert command("SHARED-CANDIPULL", observation).status_code == 403

# Promotion requires exact owner/session/scope plus a fresh explicit approval circle.
approval = {
    "candidate_id":cid,
    "approved":True,
    "authority":"NAOMI",
    "scope":scope,
    "salt_circle":circle("SHARED_MEMSAV",scope,"CI-SHARED-SAVE-1"),
}
assert command("SHARED-MEMSAV", {**approval,"approved":False}).status_code == 403
assert command("SHARED-MEMSAV", {**approval,"authority":"VERA"}).status_code == 403
assert command("SHARED-MEMSAV", {**approval,"scope":"GaiaOS:Continuity"}).status_code == 403
with patch.object(legacy, "_browser_session_id", return_value="FOREIGN-SESSION"):
    assert command("SHARED-MEMSAV", approval).status_code == 403

promoted_body = body(command("SHARED-MEMSAV", approval))
assert promoted_body["status"] == "VERIFIED", promoted_body
promoted = promoted_body["results"][0]
assert promoted["status"] == "VERIFIED", promoted
assert promoted["write_receipt"]["result"] == "SUCCESS", promoted
assert promoted["write_receipt"]["receipt_id"].startswith("MEMREC-")
assert promoted["elane_plan"]["targets"] == []
assert promoted["elane_plan"]["github_write_required"] is False
assert promoted_body["elane_writes"] == "FORBIDDEN_AND_NOT_PERFORMED"
assert promoted_body["continuity_readback_routes"] == [
    "/memoryos/continuity?record_id="+promoted["record_id"]
]
record = store.get_record(promoted["record_id"])
assert record["statement"] == created["statement"]
assert record["scope"] == scope
assert json.loads(record["notes"])["memory_owner"] == "NAOMI"

# Re-promotion cannot silently happen.
replay_approval = {**approval,"salt_circle":circle("SHARED_MEMSAV",scope,"CI-SHARED-SAVE-2")}
assert command("SHARED-MEMSAV", replay_approval).status_code == 409

# A second GaiaOS:* shared scope works without opening ChatOS or Solo:*.
scope2 = "GaiaOS:Continuity"
observation2 = {
    **observation,
    "scope":scope2,
    "statement":"CI shared GaiaOS continuity baseline marker",
    "salt_circle":circle("SHARED_CANDIPULL",scope2,"CI-SHARED-CANDIDATE-2"),
}
created2 = body(command("SHARED-CANDIPULL", observation2))["created"][0]
assert created2["owner"] == "NAOMI" and created2["scope"] == scope2
approval2 = {
    "candidate_id":created2["candidate_id"],
    "approved":True,
    "authority":"NAOMI",
    "scope":scope2,
    "salt_circle":circle("SHARED_MEMSAV",scope2,"CI-SHARED-SAVE-3"),
}
promoted2 = body(command("SHARED-MEMSAV", approval2))["results"][0]
assert promoted2["status"] == "VERIFIED"
assert store.get_record(promoted2["record_id"])["scope"] == scope2

# Existing ordinary browser CANDIPULL behavior still delegates to the original bridge.
ordinary = client.post("/chat",json={"messages":[{"role":"user","content":"CI ordinary Naomi observation"},{"role":"user","content":"CANDIPULL"}]})
ordinary_candidates = body(ordinary)["candidates"]
ordinary_candidate = next(c for c in ordinary_candidates if c["statement"] == "CI ordinary Naomi observation")
assert ordinary_candidate["owner"] == "NAOMI"
assert ordinary_candidate["scope"] == "ChatOS"

print("PASS: shared browser auth, GaiaOS scopes, SALT_CIRCLE, receipts/readback, no E-LANE writes, ordinary route preserved")
'''


class BrowserSharedMemoryBoundary(unittest.TestCase):
    def test_real_gateway_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "PYTHONPATH":str(ROOT/"api")+os.pathsep+env.get("PYTHONPATH",""),
                "MEMCONOS_DB_PATH":str(Path(temp)/"isolated.sqlite"),
                "GAIAOS_API_KEY":"CI-ONLY-NOT-OWNER-KEY-1234567890",
                "OPENAI_API_KEY":"CI-FAKE-NOT-A-PROVIDER-KEY",
                "RENDER_GIT_COMMIT":"CI-SOURCE",
            })
            env.pop("TURSO_DATABASE_URL",None)
            env.pop("TURSO_AUTH_TOKEN",None)
            result = subprocess.run(
                [sys.executable,"-c",SCRIPT],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=45,
            )
            self.assertEqual(
                result.returncode,
                0,
                result.stderr[-7000:]+result.stdout[-3000:],
            )


if __name__ == "__main__":
    unittest.main()
