"""Strict opt-in GaiaOS owner login: test ACTUAL Render app with no database.

Each test runs in a fresh subprocess. Never call real Turso/OpenAI or log
the synthetic owner key. Legacy public bootstrap is explicitly a separate
pre-cutover compatibility mode, NOT evidence of owner authentication.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = "CI-ONLY-STRONG-SYNTHETIC-OWNER-KEY-NEVER-REAL-20260927"

STRICT = r"""
import base64, hashlib, hmac, json, os, secrets, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

import memcon_runtime as db
assert db._INITIALIZED is False
assert db.STORAGE_BACKEND == "local_sqlite"
db_calls=[]
def inaccessible():
    db_calls.append("CI_DB_UNAVAILABLE")
    raise OSError("CI_PRIVATE_DB_DETAILS_NEVER_EXPOSE")
db._db=inaccessible
import browser_memcon_bridge as app
import gaiaos_api as carrier
assert app.app is not None and db_calls == []
assert carrier.BROWSER_AUTH_MODE == "owner_login"
client=TestClient(app.app,base_url="https://testserver")
key=os.environ["GAIAOS_API_KEY"]
assert len(key)>=32

home=client.get("/")
assert home.status_code==200 and "owner-login" in home.text
assert home.headers.get("set-cookie") is None
assert key not in home.text
assert not db_calls
login_page=client.get("/gaiaos/owner-login")
assert login_page.status_code==200 and "password" in login_page.text
assert login_page.headers["cache-control"]=="no-store"
assert login_page.headers.get("set-cookie") is None
assert key not in login_page.text
login_wrong=client.post("/gaiaos/owner-login",json={"owner_key":"WRONG"})
assert login_wrong.status_code==401 and "set-cookie" not in login_wrong.headers
assert key not in login_wrong.text
assert db_calls==[]
assert client.get("/memconos/health").status_code==401
assert db_calls==[]
assert client.get("/chat/recovery",follow_redirects=False).status_code==303
assert client.post("/chat",json={
    "messages":[{"role":"user","content":"CI generic question"}]
}).status_code==401
assert db_calls==[]

# Legacy publicly bootstrapped cookies must stop working as soon as strict
# mode is enabled, even when the same shared secret has not yet been rotated.
with patch.object(carrier,"BROWSER_AUTH_MODE","legacy_public_bootstrap"):
    legacy=carrier._session_token()
client.cookies.set(carrier.SESSION_COOKIE,legacy,secure=True)
assert client.post("/chat/recovery",json={
    "messages":[{"role":"user","content":"CI generic question"}],
    "recovery_acknowledged":True,"include_memory":False,
}).status_code==401
client.cookies.clear()

for seconds_ago in (28801,-90):
    nonce=f"owner.v2.{int(time.time())-seconds_ago}.{secrets.token_urlsafe(32)}"
    signature=hmac.new(key.encode(),nonce.encode(),hashlib.sha256).hexdigest()
    cookie=base64.urlsafe_b64encode(f"{nonce}.{signature}".encode()).decode()
    client.cookies.set(carrier.SESSION_COOKIE,cookie,secure=True)
    invalid=client.post("/chat/recovery",json={
        "messages":[{"role":"user","content":"CI generic question"}],
        "recovery_acknowledged":True,"include_memory":False,
    })
    assert invalid.status_code==401,invalid.text
    client.cookies.clear()

signed=client.post("/gaiaos/owner-login",json={"owner_key":key})
assert signed.status_code==200,signed.text
cookie=signed.headers["set-cookie"].lower()
assert "httponly" in cookie and "secure" in cookie
assert "samesite=strict" in cookie and "max-age=28800" in cookie
assert key not in signed.text
assert signed.json()["owner_idp_verified"] is False
home_signed=client.get("/")
assert home_signed.status_code==200 and "id='chat'" in home_signed.text
assert home_signed.headers.get("set-cookie") is None
assert db_calls==[]

class Fake:
    def __init__(self):
        self.calls=[]
        self.responses=SimpleNamespace(create=self.create)
    def create(self,**kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Synthetic generic only.")

fake=Fake()
with patch.object(carrier,"OpenAI",return_value=fake),\
     patch.object(carrier,"_load_bundle",return_value={
         "gaiaos":{"source":"CI-OWNER-LOGIN-NOT-REAL-DEPLOY"}
     }),\
     patch.object(carrier,"_carrier_instructions",return_value="CI generic"):
    ok=client.post("/chat/recovery",json={
        "messages":[{"role":"user","content":"CI generic question"}],
        "recovery_acknowledged":True,"include_memory":False,
    })
assert ok.status_code==200,ok.text
assert ok.json()["recovery_receipt"]["status"]=="PASS_EXPLICIT_PLAIN_CHAT_NO_MEMORY"
assert len(fake.calls)==1 and db_calls==[]
assert not Path(os.environ["MEMCONOS_DB_PATH"]).exists()

logout=client.post("/gaiaos/owner-logout")
assert logout.status_code==200,logout.text
assert "max-age=0" in logout.headers["set-cookie"].lower()
assert client.post("/chat/recovery",json={
    "messages":[{"role":"user","content":"CI generic question"}],
    "recovery_acknowledged":True,"include_memory":False,
}).status_code==401
assert db_calls==[]

# Strict startup without a strong configured key must HOLD, not fall back
# to unauthenticated REST, login or old public browser-cookie bootstrap.
with patch.object(carrier,"API_KEY",None):
    assert client.get("/").status_code==200
    assert client.get("/gaiaos/owner-login").status_code==503
    assert client.get("/memconos/health").status_code==503
    assert client.post("/chat",json={
        "messages":[{"role":"user","content":"CI generic question"}]
    }).status_code==503
assert db_calls==[]
print(json.dumps({"status":"PASS_STRICT_OWNER_LOGIN_ACTUAL_RENDER",
"public_cookie_issued":False,"legacy_session_reused":False,
"server_expiry_enforced":True,"strong_config_required":True,
"backend_queries":len(db_calls),"host_model_requests":len(fake.calls),
"human_idp_verified":False}))
"""

LEGACY = r"""
import json
from fastapi.testclient import TestClient
import browser_memcon_bridge as app
import gaiaos_api as carrier
assert carrier.BROWSER_AUTH_MODE=="legacy_public_bootstrap"
client=TestClient(app.app,base_url="https://testserver")
res=client.get("/")
assert res.status_code==200 and "set-cookie" in res.headers
assert res.cookies.get(carrier.SESSION_COOKIE)
print(json.dumps({"status":"PASS_LEGACY_COMPATIBILITY_NOT_OWNER_LOGIN"}))
"""


class StrictOwnerLoginTests(unittest.TestCase):
    def run_isolated(self, code: str, mode: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="gaiaos-owner-login-ci-") as tmp:
            env=dict(os.environ)
            for k in ("TURSO_DATABASE_URL","TURSO_AUTH_TOKEN","MEMCONOS_DB_PATH"):
                env.pop(k,None)
            env.update({
                "PYTHONPATH":str(ROOT / "api"),
                "GAIAOS_API_KEY":KEY,
                "OPENAI_API_KEY":"CI-FAKE-MODEL-NOT-REAL",
                "GAIAOS_BROWSER_AUTH_MODE":mode,
                "MEMCONOS_DB_PATH":str(Path(tmp)/"unused.sqlite"),
                "RENDER_GIT_COMMIT":"CI-NOT-DEPLOYED",
            })
            run=subprocess.run([sys.executable,"-c",textwrap.dedent(code)],
                               cwd=ROOT,env=env,text=True,capture_output=True,
                               check=False,timeout=45)
            self.assertEqual(run.returncode,0,run.stderr[-6500:]+run.stdout[-1500:])
            return __import__("json").loads(run.stdout.strip().splitlines()[-1])

    def test_strict_owner_login_actual_render_with_database_unavailable(self):
        result=self.run_isolated(STRICT,"owner_login")
        self.assertEqual(result["status"],"PASS_STRICT_OWNER_LOGIN_ACTUAL_RENDER")
        self.assertEqual(result["backend_queries"],0)
        self.assertFalse(result["human_idp_verified"])

    def test_legacy_mode_preserved_only_as_pre_cutover_compatibility(self):
        result=self.run_isolated(LEGACY,"legacy_public_bootstrap")
        self.assertEqual(result["status"],"PASS_LEGACY_COMPATIBILITY_NOT_OWNER_LOGIN")


if __name__=="__main__":
    unittest.main()
