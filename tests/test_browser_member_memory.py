"""Real gateway lifecycle in a disposable SQLite DB; no remote writes."""
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
import browser_memcon_bridge as bridge
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
observation = {"owner":"VERA","statement":"CI bounded catch-up VERA", "source":"CI-isolated", "why_material":"CI boundary proof"}
assert command("MEMBER-CANDIPULL", observation).status_code == 401
client.cookies.set(base.SESSION_COOKIE, "invalid")
assert command("MEMBER-CANDIPULL", observation).status_code == 401
client.cookies.set(base.SESSION_COOKIE, base._session_token())
for owner in ["NAOMI", "SHARED", "GALAXY", "vera", "VERA ", None, []]:
    assert command("MEMBER-CANDIPULL", {**observation,"owner":owner}).status_code == 422
assert command("MEMBER-CANDIPULL", {**observation,"scope":"ChatOS"}).status_code == 422
assert command("MEMBER-MEMSAV", {"candidate_id":"unknown"}).status_code == 422
with patch.object(bridge.solo_chat_runtime, "write_elane", side_effect=AssertionError("GitHub forbidden")) as lane, \
     patch.object(bridge, "_handle_solo_memsav", side_effect=AssertionError("SOLO forbidden")) as solo:
    for owner in ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]:
        candidate = body(command("MEMBER-CANDIPULL", {**observation,"owner":owner,"statement":"CI bounded catch-up "+owner}))["created"][0]
        assert candidate["owner"] == owner and candidate["scope"] == "Solo:"+owner
        cid = candidate["candidate_id"]
        approval = {"candidate_id":cid,"approved":True,"authority":"NAOMI"}
        for invalid in [False, "true", 1]:
            assert command("MEMBER-MEMSAV", {**approval,"approved":invalid}).status_code == 403
        assert command("MEMBER-MEMSAV", {**approval,"authority":owner}).status_code == 403
        assert store.get_memory_candidate(cid)["status"] == "CANDIDATE"
        with patch.object(bridge, "_browser_session_id", return_value="FOREIGN-SESSION"):
            assert command("MEMBER-MEMSAV", approval).status_code == 403
        with patch.object(store, "get_memory_candidate", return_value={**candidate,"scope":"ChatOS"}):
            assert command("MEMBER-MEMSAV", approval).status_code == 403
        promoted = body(command("MEMBER-MEMSAV", approval))["results"][0]
        assert promoted["status"] == "VERIFIED", promoted
        assert promoted["write_receipt"]["result"] == "SUCCESS", promoted
        assert promoted["write_receipt"]["receipt_id"].startswith("MEMREC-")
        record = store.get_record(promoted["record_id"])
        assert record["statement"] == candidate["statement"]
        assert record["scope"] == "Solo:"+owner
        assert json.loads(record["notes"])["memory_owner"] == owner, record
        assert command("MEMBER-MEMSAV", approval).status_code == 409
    assert lane.call_count == solo.call_count == 0
# Existing ordinary NAOMI candidate behavior remains on its original route.
ordinary = client.post("/chat",json={"messages":[{"role":"user","content":"CI ordinary Naomi observation"},{"role":"user","content":"CANDIPULL"}]})
ordinary_candidates = body(ordinary)["candidates"]
ordinary_candidate = next(c for c in ordinary_candidates if c["statement"] == "CI ordinary Naomi observation")
assert ordinary_candidate["owner"] == "NAOMI"
assert ordinary_candidate["scope"] == "ChatOS"
assert ordinary_candidate["source"] == "browser-chat"
print("PASS: six owners, session authentication, approval, no E-LANE/SOLO, real receipts/readback, ordinary NAOMI")
'''

class BrowserMemberMemoryBoundary(unittest.TestCase):
    def test_real_gateway_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({"PYTHONPATH":str(ROOT/"api")+os.pathsep+env.get("PYTHONPATH",""),
                        "MEMCONOS_DB_PATH":str(Path(temp)/"isolated.sqlite"),
                        "GAIAOS_API_KEY":"CI-ONLY-NOT-OWNER-KEY-1234567890",
                        "OPENAI_API_KEY":"CI-FAKE-NOT-A-PROVIDER-KEY",
                        "RENDER_GIT_COMMIT":"CI-SOURCE"})
            env.pop("TURSO_DATABASE_URL",None)
            env.pop("TURSO_AUTH_TOKEN",None)
            result = subprocess.run([sys.executable,"-c",SCRIPT],cwd=ROOT,env=env,capture_output=True,text=True,timeout=40)
            self.assertEqual(result.returncode,0,result.stderr[-7000:]+result.stdout[-2000:])

if __name__ == "__main__":
    unittest.main()
