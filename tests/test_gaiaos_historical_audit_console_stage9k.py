"""Stage 9K: phone-sized owner historical audit, no model calls or leaks."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import gaiaos_app as carrier
import gaiaos_historical_evidence_audit as historical
from test_gaiaos_console_browser_contract import ConsoleHTMLParser

ROUTE = "/gaiaos/memory/historical-audit-console"
AUDIT = "/gaiaos/memory/historical-evidence-audit"
KEY = "stage9k-ci-local-key-do-not-use-production"


def safe_fixture():
    return {
        "schema": historical.SCHEMA,
        "status": "HOLD",
        "reason": "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
        "next_action": "Wait for genuine, documented owner history.",
        "bounded_window_complete": True,
        "approved_technical_records_in_window": 3,
        "verified_owner_supersedes_in_window": 0,
        "approved_technical_pairs_in_window": 0,
        "active_successor_pairs_in_window": 0,
        "distinct_old_marker_pairs_in_window": 0,
        "governed_historical_pairs_in_window": 0,
        "historical_case_prepared": False,
        "historical_retrieval_tested": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "record_ids_disclosed": False,
        "statements_disclosed": False,
        "markers_disclosed": False,
        "sources_disclosed": False,
        "model_called": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
        "full_readiness_status":
            "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
    }


# These dynamic checks exercise a genuine JS click handler, not just its
# existence or Python's original template source. This also verifies an
# unauthenticated click never hits the network.
BROWSER_INTERACTION_TEST = r"""
"use strict";
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const script=fs.readFileSync(process.argv[2],"utf8");
const fixture=JSON.parse(fs.readFileSync(process.argv[3],"utf8"));
const ids=["secret","audit","status","summary","result","copy"];
const nodes=Object.create(null),events=Object.create(null);
for(const id of ids){
  nodes[id]={
    value:"",disabled:id==="copy",textContent:"",
    addEventListener(type,fn){
      assert.equal(type,"click");
      assert.equal(events[id],undefined,"Duplicate handler "+id);
      events[id]=fn;
    }
  };
}
let calls=0,copied=null,lastOptions=null;
let response=fixture;
const sandbox={
  document:{getElementById(id){
    assert.ok(Object.hasOwn(nodes,id),"Absent DOM element "+id);
    return nodes[id];
  }},
  fetch:async (url,options)=>{
    calls++;lastOptions={url,...options};
    return {ok:true,status:200,json:async()=>response};
  },
  navigator:{clipboard:{writeText:async value=>{copied=value;}}}
};
(async()=>{
  vm.runInNewContext(script,sandbox,{timeout:1000});
  assert.equal(typeof events.audit,"function");
  assert.equal(typeof events.copy,"function");
  await events.audit();
  assert.equal(calls,0,"No network call without key");
  assert.match(nodes.status.textContent,/key/i);
  assert.equal(nodes.copy.disabled,true);
  nodes.secret.value="local-test-key-only";
  await events.audit();
  assert.equal(calls,1);
  assert.equal(lastOptions.url,"/gaiaos/memory/historical-evidence-audit");
  assert.equal(lastOptions.method,"POST");
  assert.equal(lastOptions.credentials,"same-origin");
  assert.equal(lastOptions.cache,"no-store");
  assert.equal(lastOptions.headers.Authorization,"Bearer local-test-key-only");
  assert.equal(nodes.copy.disabled,false);
  assert.match(nodes.summary.textContent,/No verified/i);
  const redacted=JSON.parse(nodes.result.textContent);
  assert.equal(redacted.historical_retrieval_proven,false);
  assert.equal(redacted.model_called,false);
  assert.deepEqual(redacted.writes_performed,[]);
  assert.equal(redacted.release_activated,false);
  assert.ok(!nodes.result.textContent.includes("LOCAL_SERVER_PRIVATE_"));
  await events.copy();
  const copiedData=JSON.parse(copied);
  assert.equal(copiedData.schema,fixture.schema);
  assert.ok(!copied.includes("local-test-key-only"));
  assert.ok(!copied.includes("LOCAL_SERVER_PRIVATE_"));
  response={...fixture,reason:"LOCAL_SERVER_PRIVATE_STATEMENT"};
  await events.audit();
  assert.equal(nodes.copy.disabled,true,"Unknown response must not copy");
  assert.match(nodes.status.textContent,/HOLD/);
  assert.ok(!nodes.result.textContent.includes("LOCAL_SERVER_PRIVATE_"));
  assert.equal(calls,2);
  // A purported "success" without all safety flags must also be rejected.
  response={...fixture,model_called:true};
  await events.audit();
  assert.equal(nodes.copy.disabled,true);
  assert.match(nodes.status.textContent,/HOLD/);
  assert.equal(calls,3);
  process.stdout.write("STAGE9K_BROWSER_CLICK_SAFETY_PASS\n");
})().catch(error=>{process.stderr.write(String(error.stack||error));process.exitCode=1;});
"""


class HistoricalAuditConsoleTests(unittest.TestCase):
    def test_static_get_is_private_data_free_and_csp_nonce_works(self):
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        page = client.get(ROUTE)
        self.assertEqual(page.status_code, 200)
        self.assertIn("no-store", page.headers.get("cache-control", ""))
        self.assertIn("no-referrer", page.headers.get("referrer-policy", ""))
        self.assertIn("frame-ancestors 'none'",
                      page.headers["content-security-policy"])
        self.assertIn("nonce-", page.headers["content-security-policy"])
        for literal in ('id="audit"', 'id="copy"', 'id="secret"',
                        "Check historical evidence"):
            self.assertIn(literal, page.text)
        self.assertNotIn(KEY, page.text)
        self.assertNotIn("LOCAL_SERVER_PRIVATE_", page.text)
        self.assertNotIn("Run optional AUGURY semantic shadow", page.text)
        self.assertNotIn("private statement A", page.text)

    def test_audit_post_owner_only_without_model_or_memory_mutations(self):
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        with patch.object(
            carrier.base, "API_KEY", KEY,
        ), patch.object(
            historical, "audit", return_value=safe_fixture(),
        ) as core, patch("openai.OpenAI") as sdk:
            denied=client.post(AUDIT)
            self.assertEqual(denied.status_code, 401)
            self.assertEqual(core.call_count, 0)
            allowed=client.post(
                AUDIT, headers={"Authorization":"Bearer "+KEY},
            )
            self.assertEqual(allowed.status_code, 200, allowed.text)
            self.assertIn("no-store",allowed.headers["cache-control"])
            self.assertFalse(allowed.json()["historical_retrieval_proven"])
            self.assertEqual(allowed.json()["writes_performed"],[])
            self.assertNotIn(KEY,allowed.text)
            core.assert_called_once()
            sdk.assert_not_called()

    def test_actual_served_browser_clicks_enforce_key_redact_and_copy(self):
        if shutil.which("node") is None:
            self.fail("Node.js mandatory for actual served JavaScript validation")
        client=TestClient(carrier.app)
        self.addCleanup(client.close)
        response=client.get(ROUTE)
        parser=ConsoleHTMLParser()
        parser.feed(response.text)
        self.assertEqual(len(parser.scripts),1)
        self.assertEqual(set(parser.buttons),{"audit","copy"})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            script=root/"historical-audit-served.js"
            fixture=root/"redacted-fixture.json"
            harness=root/"click-test.js"
            script.write_text(parser.scripts[0][1],encoding="utf-8")
            fixture.write_text(json.dumps({
                **safe_fixture(),
                "secret_extra_field":"LOCAL_SERVER_PRIVATE_DO_NOT_ECHO",
            }),encoding="utf-8")
            harness.write_text(BROWSER_INTERACTION_TEST,encoding="utf-8")
            result=subprocess.run(
                ["node",str(harness),str(script),str(fixture)],
                check=False,text=True,capture_output=True,timeout=15,
            )
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("STAGE9K_BROWSER_CLICK_SAFETY_PASS",result.stdout)

    def test_audit_get_has_no_effect_and_cannot_be_called_without_owner_post(self):
        client=TestClient(carrier.app)
        self.addCleanup(client.close)
        response=client.get(AUDIT)
        self.assertEqual(response.status_code,405)
        page=client.get(ROUTE)
        self.assertEqual(page.status_code,200)


if __name__=="__main__":
    unittest.main(verbosity=2)
