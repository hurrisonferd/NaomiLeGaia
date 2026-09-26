"""Stage 9L: isolated one-click safe suite, actual DOM click, no provider calls."""
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
import gaiaos_one_click_readiness as suite
import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as historical
import gaiaos_memory_mode as mode
from test_gaiaos_console_browser_contract import ConsoleHTMLParser


KEY = "ci-only-bearer-for-oneclick-tests"
SHA = "a" * 40
PAGE = "/gaiaos/memory/one-click-console"
POST = "/gaiaos/memory/one-click-readiness"


class SyntheticStore:
    _INITIALIZED = True

    def __init__(self):
        self.storage_reads = 0
        self.write_calls = 0

    def storage_status(self):
        self.storage_reads += 1
        return {"backend": "turso_libsql", "remote_configured": True}

    def write_record(self, *_args, **_kwargs):
        self.write_calls += 1
        raise AssertionError("One-click suite must never write")


def health():
    return {
        "status": "ok", "service": "gaiaos-carrier",
        "deployment_proof": {
            "source_commit": SHA, "source_commit_verified": True,
        },
        "EXTRA_SECRET_FROM_HOST": "DO_NOT_EXPOSE_HOST_PRIVATE_DATA",
    }


CONTROL = {
    "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH, "control_version": 7,
    "bigbang_activation_enabled": False, "writes_performed": [],
}
PREFLIGHT = {
    "schema": "gaiaos.bigbang.technical-preflight.v1",
    "status": "HOLD", "reason": "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES",
    "current_cases_prepared": 3,
    "distinct_current_records_capped_at_two": 2,
    "historical_cases_prepared": 0, "negative_cases_prepared": 2,
    "partial_five_case_ready": True,
    "review_executed": False,
    "record_ids_disclosed": False, "statements_disclosed": False,
    "queries_disclosed": False,
    "release_activated": False, "writes_performed": [],
    "e_lanes_modified": False,
}
HISTORY = {
    "schema": historical.SCHEMA, "status": "HOLD",
    "reason": "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
    "bounded_window_complete": True,
    "historical_case_prepared": False,
    "approved_technical_records_in_window": 2,
    "verified_owner_supersedes_in_window": 0,
    "approved_technical_pairs_in_window": 0,
    "active_successor_pairs_in_window": 0,
    "distinct_old_marker_pairs_in_window": 0,
    "governed_historical_pairs_in_window": 0,
    "record_ids_disclosed": False, "statements_disclosed": False,
    "markers_disclosed": False, "sources_disclosed": False,
    "historical_retrieval_proven": False,
    "historical_retrieval_tested": False,
    "general_semantic_quality_proven": False,
    "release_activated": False, "writes_performed": [],
    "e_lanes_modified": False, "model_called": False,
    "private": "DO_NOT_EXPOSE_PRIVATE_RECORD_IDS",
}
LITERAL = {
    "schema": "gaiaos.bigbang.technical-literal-wiring.v1",
    "status": "PASS_LITERAL_WIRING_ONLY",
    "reason": "TWO_LITERAL_ANCHORS_AND_LEGACY_PARITY",
    "case_count": 2,
    "case_results": [
        {"case": 0, "expected_record_in_current_results": True,
         "private_statement": "DO_NOT_EXPOSE_PRIVATE_STATEMENT"},
        {"case": 1, "expected_record_in_current_results": True},
    ],
    "legacy_exact_parity": True,
    "literal_wiring_test_only": True,
    "semantic_paraphrase_quality_tested": False,
    "record_ids_disclosed": False, "statements_disclosed": False,
    "queries_disclosed": False, "tokens_disclosed": False,
    "release_activated": False, "writes_performed": [],
    "e_lanes_modified": False,
}


def prepared():
    return SyntheticStore()


class OneClickSuiteTests(unittest.TestCase):
    def setUp(self):
        self.runtime = prepared()

    def run_fixture(self, *, preflight=None, hist=None, lit=None, control=None):
        with patch.object(
            mode, "mode_status", return_value=control or CONTROL
        ) as lock, patch.object(
            readiness, "technical_preflight",
            return_value=preflight if preflight is not None else PREFLIGHT,
        ) as source, patch.object(
            historical, "audit",
            return_value=hist if hist is not None else HISTORY,
        ) as history_read, patch.object(
            readiness, "technical_literal_wiring_probe",
            return_value=lit if lit is not None else LITERAL,
        ) as literal, patch("openai.OpenAI") as sdk:
            result = suite.run(self.runtime, carrier_health=health)
            sdk.assert_not_called()
        return result, lock, source, history_read, literal

    def test_one_action_runs_six_checks_but_never_claims_semantic_or_release(self):
        report, lock, source, history_read, literal = self.run_fixture()
        self.assertEqual(report["status"], "SAFE_CHECKS_COMPLETE_RELEASE_LOCKED")
        self.assertEqual(list(report["checks"]), [
            "deployment", "heatdeath", "memory_storage",
            "technical_sample", "historical_evidence", "current_literal_readback",
        ])
        self.assertEqual(report["checks"]["deployment"]["running_commit"], SHA)
        self.assertEqual(report["checks"]["heatdeath"]["status"], "PASS")
        self.assertEqual(report["checks"]["memory_storage"]["status"], "PASS")
        self.assertTrue(report["checks"]["technical_sample"]["partial_five_case_ready"])
        self.assertEqual(
            report["checks"]["historical_evidence"]["reason"],
            "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
        )
        self.assertEqual(
            report["checks"]["current_literal_readback"]["record_hits"], [True, True]
        )
        self.assertTrue(report["checks"]["current_literal_readback"]["legacy_exact_parity"])
        self.assertEqual(lock.call_count, 2)
        source.assert_called_once_with(self.runtime)
        history_read.assert_called_once_with(self.runtime)
        literal.assert_called_once_with(self.runtime)
        self.assertEqual(self.runtime.storage_reads, 1)
        self.assertEqual(self.runtime.write_calls, 0)
        self.assertEqual(report["writes_performed"], [])
        self.assertFalse(report["model_called"])
        self.assertFalse(report["general_semantic_quality_proven"])
        self.assertFalse(report["historical_retrieval_proven"])
        self.assertFalse(report["release_activated"])
        self.assertFalse(report["bigbang_activation_enabled"])
        all_text=str(report)
        for secret in (
            "DO_NOT_EXPOSE_HOST_PRIVATE_DATA",
            "DO_NOT_EXPOSE_PRIVATE_RECORD_IDS",
            "DO_NOT_EXPOSE_PRIVATE_STATEMENT",
            KEY,
        ):
            self.assertNotIn(secret, all_text)

    def test_no_heatdeath_means_no_memory_scans_and_no_release(self):
        unsafe = {**CONTROL, "effective_mode": mode.BIGBANG,
                  "bigbang_activation_enabled": True}
        report, lock, source, history_read, literal = self.run_fixture(
            control=unsafe,
        )
        self.assertEqual(report["status"], "HOLD_FAILED_CLOSED")
        self.assertEqual(report["next_action"], "VERIFY_HEATDEATH_RELEASE_LOCK")
        self.assertEqual(report["checks"]["heatdeath"]["status"], "HOLD")
        self.assertEqual(report["checks"]["memory_storage"]["status"], "SKIPPED")
        self.assertEqual(self.runtime.storage_reads, 0)
        source.assert_not_called()
        history_read.assert_not_called()
        literal.assert_not_called()
        self.assertFalse(report["release_activated"])

    def test_storage_unavailable_short_circuits_all_memory_scans(self):
        self.runtime.storage_status = lambda: {
            "backend": "sqlite", "remote_configured": False,
        }
        report, lock, source, history_read, literal = self.run_fixture()
        self.assertEqual(report["status"], "HOLD_FAILED_CLOSED")
        self.assertEqual(report["next_action"], "RESTORE_REMOTE_MEMORYOS_READ_ACCESS")
        self.assertEqual(report["checks"]["memory_storage"]["status"], "HOLD")
        source.assert_not_called()
        history_read.assert_not_called()
        literal.assert_not_called()

    def test_release_lock_drift_forces_end_of_suite_hold(self):
        after = {**CONTROL, "control_version": 8}
        with patch.object(mode, "mode_status", side_effect=[CONTROL, after]), patch.object(
            readiness, "technical_preflight", return_value=PREFLIGHT,
        ), patch.object(
            historical, "audit", return_value=HISTORY,
        ), patch.object(
            readiness, "technical_literal_wiring_probe", return_value=LITERAL,
        ):
            result = suite.run(self.runtime, carrier_health=health)
        self.assertEqual(result["status"], "HOLD_FAILED_CLOSED")
        self.assertEqual(
            result["checks"]["heatdeath"]["reason"], "RELEASE_LOCK_CHANGED_OR_UNVERIFIED",
        )
        self.assertFalse(result["release_activated"])

    def test_no_two_approved_current_records_skips_literal_readback(self):
        prep = {
            **PREFLIGHT, "status": "HOLD",
            "reason": "TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN",
            "distinct_current_records_capped_at_two": 1,
            "current_cases_prepared": 0,
            "partial_five_case_ready": False,
        }
        result, lock, source, history_read, literal = self.run_fixture(
            preflight=prep,
        )
        self.assertEqual(
            result["checks"]["current_literal_readback"]["status"], "SKIPPED",
        )
        literal.assert_not_called()
        self.assertEqual(
            result["next_action"], "REVIEW_APPROVED_CURRENT_TECHNICAL_MEMORIES",
        )

    def test_unknown_reason_and_suspicious_source_fields_are_never_forwarded(self):
        corrupted = {
            **HISTORY,
            "reason": "SECRET_PRIVATE_OWNER_RECORD_ID_IN_ERROR",
            "private_statement": "DO_NOT_EXPOSE_ANY_RAW_MEMORY",
        }
        result, *_ = self.run_fixture(hist=corrupted)
        self.assertEqual(
            result["checks"]["historical_evidence"]["reason"],
            "UNRECOGNIZED_OR_UNVERIFIED_RESULT",
        )
        self.assertNotIn("SECRET_PRIVATE_OWNER",str(result))
        self.assertNotIn("DO_NOT_EXPOSE_ANY_RAW_MEMORY",str(result))
        self.assertFalse(result["historical_retrieval_proven"])

    def test_fake_success_flags_are_rejected_not_upgraded(self):
        forged = {**LITERAL, "writes_performed": ["PRIVATE_WRITE"]}
        result, *_ = self.run_fixture(lit=forged)
        self.assertEqual(
            result["checks"]["current_literal_readback"]["status"], "HOLD"
        )
        self.assertFalse(result["release_activated"])
        self.assertNotIn("PRIVATE_WRITE",str(result))

    def test_unverified_health_is_a_specific_gate_not_an_imaginary_sha(self):
        with patch.object(
            mode, "mode_status", return_value=CONTROL
        ), patch.object(
            readiness, "technical_preflight", return_value=PREFLIGHT
        ), patch.object(
            historical, "audit", return_value=HISTORY
        ), patch.object(
            readiness, "technical_literal_wiring_probe", return_value=LITERAL
        ):
            result = suite.run(
                self.runtime,
                carrier_health=lambda: {
                    **health(),
                    "deployment_proof": {
                        "source_commit": "PRIVATE_SECRET_AND_NOT_A_COMMIT",
                        "source_commit_verified": True,
                    },
                },
            )
        self.assertEqual(result["checks"]["deployment"]["status"], "HOLD")
        self.assertNotIn("PRIVATE_SECRET",str(result))
        self.assertEqual(result["next_action"], "VERIFY_RUNNING_DEPLOYMENT_COMMIT")


BROWSER_HARNESS = r"""
"use strict";
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const script=fs.readFileSync(process.argv[2],"utf8");
const fixture=JSON.parse(fs.readFileSync(process.argv[3],"utf8"));
const ids=["secret","run","status","summary","checks","report","copy"];
const nodes=Object.create(null),events=Object.create(null);
function makeNode(){
 return {
   value:"",textContent:"",disabled:false,className:"",
   children:[],
   addEventListener(type,fn){
     assert.equal(type,"click");
     assert.equal(events[this.id],undefined);
     events[this.id]=fn;
   },
   replaceChildren(){this.children=[];},
   appendChild(node){this.children.push(node);}
 };
}
for(const id of ids){nodes[id]=makeNode();nodes[id].id=id;}
nodes.copy.disabled=true;
let calls=0,copied=null,lastRequest=null;
let response=fixture;
const context={
 document:{
  getElementById(id){
   assert.ok(Object.hasOwn(nodes,id),"Unknown element "+id);
   return nodes[id];
  },
  createElement(){return makeNode();}
 },
 fetch:async(url,options)=>{
  calls++;lastRequest={url,...options};
  return {ok:true,status:200,json:async()=>response};
 },
 navigator:{clipboard:{writeText:async value=>{copied=value;}}}
};
(async()=>{
 vm.runInNewContext(script,context,{timeout:1000,filename:"served-one-click.js"});
 assert.equal(typeof events.run,"function");
 assert.equal(typeof events.copy,"function");
 await events.run();
 assert.equal(calls,0,"Missing key must prevent network");
 assert.match(nodes.status.textContent,/key/i);
 assert.equal(nodes.copy.disabled,true);
 nodes.secret.value="ci-plain-local-key";
 await events.run();
 assert.equal(calls,1,"One click must make exactly one authenticated request");
 assert.equal(lastRequest.url,"/gaiaos/memory/one-click-readiness");
 assert.equal(lastRequest.method,"POST");
 assert.equal(lastRequest.credentials,"same-origin");
 assert.equal(lastRequest.cache,"no-store");
 assert.equal(lastRequest.headers.Authorization,"Bearer ci-plain-local-key");
 assert.equal(nodes.checks.children.length,6);
 assert.equal(nodes.copy.disabled,false);
 const report=JSON.parse(nodes.report.textContent);
 assert.equal(report.model_called,false);
 assert.equal(report.release_activated,false);
 assert.equal(report.general_semantic_quality_proven,false);
 assert.equal(report.checks.current_literal_readback.status,"PASS_LITERAL_WIRING_ONLY");
 assert.ok(!nodes.report.textContent.includes("DO_NOT_EXPOSE"));
 await events.copy();
 const copiedJSON=JSON.parse(copied);
 assert.equal(copiedJSON.schema,fixture.schema);
 assert.ok(!copied.includes("ci-plain-local-key"));
 assert.ok(!copied.includes("DO_NOT_EXPOSE"));
 response={...fixture,model_called:true};
 await events.run();
 assert.equal(nodes.copy.disabled,true,"Unsafe response cannot be copied");
 assert.match(nodes.status.textContent,/HOLD/);
 assert.equal(calls,2);
 response={...fixture,checks:{...fixture.checks,
  historical_evidence:{...fixture.checks.historical_evidence,
   reason:"DO_NOT_EXPOSE_OWNER_MEMORY_STATEMENT"}}};
 await events.run();
 assert.equal(nodes.copy.disabled,true);
 assert.ok(!nodes.report.textContent.includes("DO_NOT_EXPOSE"));
 assert.equal(calls,3);
 process.stdout.write("STAGE9L_ONE_CLICK_BROWSER_PASS\n");
})().catch(error=>{process.stderr.write(String(error.stack||error));process.exitCode=1;});
"""


class OneClickRouteAndBrowserTests(unittest.TestCase):
    def test_new_static_page_is_nonces_no_store_and_contains_no_secrets(self):
        client=TestClient(carrier.app)
        self.addCleanup(client.close)
        page=client.get(PAGE)
        self.assertEqual(page.status_code,200)
        self.assertIn("no-store",page.headers["cache-control"])
        self.assertIn("no-referrer",page.headers["referrer-policy"])
        self.assertIn("script-src 'nonce-",page.headers["content-security-policy"])
        for mark in ('id="run"','id="copy"','id="secret"',
                     "/gaiaos/memory/one-click-readiness"):
            self.assertIn(mark,page.text)
        self.assertNotIn(KEY,page.text)
        self.assertNotIn("DO_NOT_EXPOSE",page.text)

    def test_post_requires_owner_bearer_and_never_calls_model(self):
        client=TestClient(carrier.app)
        self.addCleanup(client.close)
        fixture_case=OneClickSuiteTests()
        fixture_case.setUp()
        report, *_ = fixture_case.run_fixture()
        with patch.object(carrier.base,"API_KEY",KEY),patch.object(
            suite,"run",return_value=report,
        ) as core,patch("openai.OpenAI") as sdk:
            self.assertEqual(client.post(POST).status_code,401)
            core.assert_not_called()
            response=client.post(POST,headers={"Authorization":"Bearer "+KEY})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.headers["cache-control"],"no-store")
            self.assertEqual(response.json()["schema"],suite.SCHEMA)
            core.assert_called_once()
            sdk.assert_not_called()
            self.assertNotIn(KEY,response.text)
        self.assertEqual(client.get(POST).status_code,405)

    def test_actual_served_dom_button_copies_only_strict_redacted_data(self):
        if shutil.which("node") is None:
            self.fail("Node.js is mandatory for GaiaOS console tests")
        client=TestClient(carrier.app)
        self.addCleanup(client.close)
        page=client.get(PAGE)
        parser=ConsoleHTMLParser()
        parser.feed(page.text)
        self.assertEqual(set(parser.buttons),{"run","copy"})
        self.assertEqual(len(parser.scripts),1)
        fixture_case=OneClickSuiteTests()
        fixture_case.setUp()
        report,*_=fixture_case.run_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            script=root/"served.js"
            fixture=root/"fixture.json"
            harness=root/"click-test.js"
            script.write_text(parser.scripts[0][1],encoding="utf-8")
            fixture.write_text(json.dumps({
                **report,"private_blob":"DO_NOT_EXPOSE_SECRET_RECORD",
            }),encoding="utf-8")
            harness.write_text(BROWSER_HARNESS,encoding="utf-8")
            result=subprocess.run(
                ["node",str(harness),str(script),str(fixture)],
                check=False,text=True,capture_output=True,timeout=15
            )
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("STAGE9L_ONE_CLICK_BROWSER_PASS",result.stdout)


if __name__=="__main__":
    unittest.main(verbosity=2)
