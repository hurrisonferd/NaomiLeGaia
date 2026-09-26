"""Stage 9L: single-click owner control panel, static CSP-bound HTML only."""
from __future__ import annotations

PAGE = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaiaOS · One-click safe checks</title>
<style nonce="__NONCE__">
:root{color-scheme:dark;font:16px system-ui;background:#111922;color:#f2f5f9}
body{max-width:640px;margin:auto;padding:17px;line-height:1.45}
h1{font-size:1.5rem}p,small{color:#c6d6e1}
section{border:1px solid #657d92;border-radius:12px;padding:14px;margin:15px 0}
input,button{width:100%;box-sizing:border-box;padding:13px;margin:7px 0;border-radius:9px;font:inherit}
input{background:#223447;border:1px solid #a3bed0;color:#fff}
button{background:#296a78;border:1px solid #aed1dd;color:#fff;font-weight:700}
button:disabled{opacity:.53}small{display:block;margin-top:9px}
#summary{font-weight:700;font-size:1.12rem}
.check{display:flex;gap:13px;padding:10px 0;border-bottom:1px solid #334a5a;align-items:flex-start}
.check .status{font-weight:700;min-width:65px;text-align:right}
.check .label{flex:1}
.pass{color:#8adead}.hold{color:#f6c984}
pre{background:#1c2d3b;padding:12px;border-radius:9px;white-space:pre-wrap;
overflow-wrap:anywhere;font:12px ui-monospace,monospace}
</style></head><body><main>
<h1>GaiaOS · One-click checks</h1>
<p>One safe check of the running carrier, HEATDEATH, MemoryOS, current retrieval,
and real historical prerequisites. No model calls, memory writes or BIGBANG activation.</p>
<section>
<label for="secret">Private GaiaOS API key</label>
<input id="secret" type="password" autocomplete="off" autocapitalize="off"
spellcheck="false" placeholder="Enter only on this page">
<button id="run" type="button">Run all safe checks</button>
<p id="status" role="status" aria-live="polite">No checks run.</p>
<div id="summary" role="status" aria-live="polite"></div>
<div id="checks"></div>
<small>Human judgments, paid model calls, deployment and BIGBANG still require
separate explicit decisions. This button never performs them.</small>
</section>
<section>
<h2>One redacted report</h2>
<pre id="report">Run the checks to prepare a safe report.</pre>
<button id="copy" type="button" disabled>Copy redacted report</button>
<small>Share only this report, not the private API key, memory statements or record IDs.</small>
</section>
</main>
<script nonce="__NONCE__">
"use strict";
const byId=id=>document.getElementById(id);
const steps=[
 ["deployment","Running carrier"],
 ["heatdeath","HEATDEATH safeguard"],
 ["memory_storage","MemoryOS connection"],
 ["technical_sample","Approved current memories"],
 ["historical_evidence","Real historical evidence"],
 ["current_literal_readback","Current retrieval and parity"]
];
const validStatuses={
 deployment:["PASS","HOLD"],
 heatdeath:["PASS","HOLD"],
 memory_storage:["PASS","HOLD","SKIPPED"],
 technical_sample:["HOLD","PREPARED_UNTESTED","SKIPPED"],
 historical_evidence:["HOLD","CANDIDATE_PRESENT_UNTESTED","SKIPPED"],
 current_literal_readback:["HOLD","PASS_LITERAL_WIRING_ONLY","SKIPPED"]
};
const actions={
 VERIFY_RELEASE_LOCK_AND_MISSING_CHECKS:"Safeguards or checks need review.",
 VERIFY_HEATDEATH_RELEASE_LOCK:"Verify HEATDEATH before running memory checks.",
 RESTORE_REMOTE_MEMORYOS_READ_ACCESS:"Check the remote MemoryOS connection.",
 VERIFY_RUNNING_DEPLOYMENT_COMMIT:"Verify which commit is running on Render.",
 REVIEW_APPROVED_CURRENT_TECHNICAL_MEMORIES:"Check that two approved current memories are eligible.",
 RESOLVE_REAL_HISTORICAL_EVIDENCE_GAP:"A genuine historical prerequisite is still missing.",
 INSPECT_CURRENT_LITERAL_READBACK:"Inspect the current read-only retrieval result.",
 OWNER_REVIEW_HISTORICAL_AND_SEMANTIC_EVIDENCE:
  "Safe checks finished. Historical and semantic release proof still requires review."
};
const historyReasons={
 NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW:"No verified owner supersession found.",
 NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR:"No supersession connects two approved technical memories.",
 NO_ACTIVE_APPROVED_SUCCESSOR:"An approved newer memory is not ACTIVE.",
 NO_DISTINCT_HISTORICAL_MARKER:"The older memory has no distinctive version marker.",
 HISTORICAL_GOVERNING_STATE_UNVERIFIED:"Historical governing state is not verified.",
 HISTORICAL_GOVERNING_STATE_READ_FAILED:"Historical governing state could not be read.",
 HISTORICAL_CANDIDATE_PREPARED_UNTESTED:"A real historical candidate exists, but retrieval is untested.",
 STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED:"The full six-case history sample is not ready.",
 BOUNDED_WINDOW_INCOMPLETE:"The bounded history window is incomplete."
};
const reasons=new Set([
 "RUNNING_COMMIT_IDENTIFIED","DEPLOYED_SOURCE_UNVERIFIED","CARRIER_HEALTH_UNAVAILABLE",
 "HEATDEATH_LOCK_VERIFIED","HEATDEATH_RELEASE_LOCK_UNVERIFIED",
 "RELEASE_LOCK_CHANGED_OR_UNVERIFIED","RELEASE_LOCK_UNVERIFIED",
 "TURSO_REMOTE_CONFIGURED","REMOTE_STORAGE_NOT_CONFIRMED",
 "NOT_EVALUATED","RUNTIME_NOT_INITIALIZED","HEATDEATH_RELEASE_LOCK_NOT_VERIFIED",
 "SOURCE_WINDOW_INCOMPLETE","TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN",
 "PARTIAL_FIVE_CASE_CONTRACT_UNSATISFIED","NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES",
 "SIX_CASE_CONTRACT_UNSATISFIED","SIX_TECHNICAL_CASES_SELECTED_READ_ONLY","SOURCE_READ_FAILED",
 "TECHNICAL_PREFLIGHT_UNVERIFIED","TECHNICAL_PREFLIGHT_FAILED_CLOSED",
 "BOUNDED_SOURCE_READ_FAILED","BOUNDED_WINDOW_INCOMPLETE",
 "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW","NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR",
 "NO_ACTIVE_APPROVED_SUCCESSOR","NO_DISTINCT_HISTORICAL_MARKER",
 "HISTORICAL_GOVERNING_STATE_READ_FAILED","HISTORICAL_GOVERNING_STATE_UNVERIFIED",
 "STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED","HISTORICAL_CANDIDATE_PREPARED_UNTESTED",
 "HISTORICAL_AUDIT_UNVERIFIED","HISTORICAL_AUDIT_FAILED_CLOSED",
 "HISTORICAL_COUNTS_UNVERIFIED","TWO_APPROVED_CURRENT_RECORDS_REQUIRED",
 "TWO_APPROVED_CURRENT_TECHNICAL_RECORDS_REQUIRED","BOUNDED_SCAN_UNVERIFIED",
 "TARGET_OUTSIDE_VERIFIED_BOUNDED_SCOPE","INSUFFICIENT_DISTINCT_LITERAL_CONCEPTS",
 "LITERAL_TARGET_ADMISSION_NOT_PROVEN","NATIVE_LEGACY_BASELINE_UNVERIFIED",
 "UNVERIFIED_GALAXY_RESPONSE","TWO_LITERAL_ANCHORS_AND_LEGACY_PARITY",
 "LITERAL_ANCHOR_MISS_OR_LEGACY_PARITY_FAILURE",
 "LITERAL_PROBE_FAILED_CLOSED","LITERAL_PROBE_UNVERIFIED",
 "UNRECOGNIZED_OR_UNVERIFIED_RESULT"
]);
let redacted=null;
function safeResult(source){
 if(!source||source.schema!=="gaiaos.stage9l.owner-one-click-safe-checks.v1"||
   !["SAFE_CHECKS_COMPLETE_RELEASE_LOCKED","HOLD_FAILED_CLOSED"].includes(source.status)||
   source.release_activated!==false||source.bigbang_activation_enabled!==false||
   source.model_called!==false||source.e_lanes_modified!==false||
   source.historical_retrieval_proven!==false||
   source.general_semantic_quality_proven!==false||
   source.record_ids_disclosed!==false||source.statements_disclosed!==false||
   source.queries_disclosed!==false||source.sources_disclosed!==false||
   source.key_material_disclosed!==false||
   !Array.isArray(source.writes_performed)||source.writes_performed.length!==0||
   !source.checks||typeof source.checks!=="object"||
   !Object.prototype.hasOwnProperty.call(actions,source.next_action)){
   throw Error("Unexpected response. No report was copied.");
 }
 const report={
  schema:source.schema,status:source.status,checks:{},
  next_action:source.next_action,full_readiness_status:
   "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
  historical_retrieval_proven:false,general_semantic_quality_proven:false,
  model_called:false,writes_performed:[],e_lanes_modified:false,
  bigbang_activation_enabled:false,release_activated:false
 };
 for(const [key] of steps){
   const check=source.checks[key];
   if(!check||!validStatuses[key].includes(check.status)||
      typeof check.reason!=="string"||!reasons.has(check.reason)){
     throw Error("A check returned an unrecognized status.");
   }
   const clean={status:check.status,reason:check.reason};
   if(key==="deployment"&&check.status==="PASS"){
     if(typeof check.running_commit!=="string"||
        !/^[a-f0-9]{40}$/.test(check.running_commit)){
        throw Error("Invalid running source identity.");
     }
     clean.running_commit=check.running_commit;
   }
   if(key==="technical_sample"&&check.status!=="SKIPPED"&&
      Number.isInteger(check.distinct_current_records)&&
      check.distinct_current_records>=0&&check.distinct_current_records<=2){
      clean.distinct_current_records=check.distinct_current_records;
   }
   if(key==="historical_evidence"&&check.status!=="SKIPPED"){
     if(typeof check.bounded_window_complete!=="boolean"){
       throw Error("Historical audit completeness unknown.");
     }
     clean.bounded_window_complete=check.bounded_window_complete;
     clean.historical_case_prepared=check.historical_case_prepared===true;
     if(clean.bounded_window_complete){
       if(!check.counts||typeof check.counts!=="object"){
         throw Error("Historical counts unverified.");
       }
       clean.counts={};
       const names=[
        "approved_technical_records_in_window","verified_owner_supersedes_in_window",
        "approved_technical_pairs_in_window","active_successor_pairs_in_window",
        "distinct_old_marker_pairs_in_window","governed_historical_pairs_in_window"
       ];
       for(const name of names){
         const value=check.counts[name];
         if(!Number.isInteger(value)||value<0||value>100){
           throw Error("Historical count outside safe bounds.");
         }
         clean.counts[name]=value;
       }
     }
   }
   if(key==="current_literal_readback"&&check.status!=="SKIPPED"){
     if(typeof check.legacy_exact_parity!=="boolean"||
       !Array.isArray(check.record_hits)||check.record_hits.length>2||
       check.record_hits.some(value=>typeof value!=="boolean")){
       throw Error("Literal readback shape unverified.");
     }
     clean.legacy_exact_parity=check.legacy_exact_parity;
     clean.record_hits=check.record_hits;
   }
   report.checks[key]=clean;
 }
 return report;
}
function label(check){
 if(check.status==="PASS"||check.status==="PASS_LITERAL_WIRING_ONLY"){
   return ["PASS","pass"];
 }
 if(check.status==="PREPARED_UNTESTED"||
    check.status==="CANDIDATE_PRESENT_UNTESTED"){
   return ["READY*","hold"];
 }
 if(check.status==="SKIPPED")return ["SKIP","hold"];
 return ["HOLD","hold"];
}
function render(report){
 byId("checks").replaceChildren();
 for(const [key,title] of steps){
   const row=document.createElement("div");
   row.className="check";
   const name=document.createElement("div");name.className="label";
   name.textContent=title;
   const result=document.createElement("span");
   const [caption,tone]=label(report.checks[key]);
   result.className="status "+tone;result.textContent=caption;
   row.appendChild(name);row.appendChild(result);
   byId("checks").appendChild(row);
 }
 const history=report.checks.historical_evidence;
 const detail=historyReasons[history.reason];
 byId("summary").textContent=detail||actions[report.next_action];
 byId("report").textContent=JSON.stringify(report,null,2);
}
byId("run").addEventListener("click",async()=>{
 const key=byId("secret").value.trim();
 if(!key){byId("status").textContent="Enter the private API key here first.";return;}
 redacted=null;byId("copy").disabled=true;
 byId("run").disabled=true;byId("summary").textContent="";
 byId("checks").replaceChildren();byId("report").textContent="Checking…";
 byId("status").textContent="Running six bounded, read-only checks. No model call…";
 try{
  const response=await fetch("/gaiaos/memory/one-click-readiness",{
   method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
   headers:{"Authorization":"Bearer "+key}
  });
  if(!response.ok){
   if(response.status===401)throw Error("Invalid or missing private key.");
   throw Error("Safe checks unavailable (HTTP "+response.status+").");
  }
  redacted=safeResult(await response.json());
  render(redacted);byId("copy").disabled=false;
  byId("status").textContent=redacted.status==="SAFE_CHECKS_COMPLETE_RELEASE_LOCKED"
   ?"Safe checks finished. BIGBANG remains locked."
   :"HOLD: safeguards need review. Nothing was activated.";
 }catch(error){
  byId("status").textContent="HOLD: "+error.message;
  byId("summary").textContent="";
  byId("report").textContent="No verified report to copy.";
 }finally{byId("run").disabled=false;}
});
byId("copy").addEventListener("click",async()=>{
 if(!redacted)return;
 try{
  await navigator.clipboard.writeText(JSON.stringify(redacted,null,2));
  byId("status").textContent="Redacted report copied. No API key or memory text included.";
 }catch(error){
  byId("status").textContent="Clipboard unavailable. Select the redacted report above.";
 }
});
</script></body></html>
"""


def render(nonce: str) -> str:
    if not isinstance(nonce, str) or not nonce:
        raise ValueError("CSP nonce required")
    return PAGE.replace("__NONCE__", nonce)
