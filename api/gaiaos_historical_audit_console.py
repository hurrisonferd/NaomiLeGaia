"""Stage 9K: small static owner-only historical audit console.

A deliberately separate, low-complexity page. Static GET returns no private
memory, server secret, diagnostics or authenticated state. The owner explicitly
clicks one button to POST to the already locked-down Stage 9J audit route.
No model access, database write, provider call or recurring task exists here.
"""
from __future__ import annotations

PAGE = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GaiaOS · Historical evidence check</title>
<style nonce="__NONCE__">
:root{color-scheme:dark;font:16px system-ui;background:#111922;color:#f0f4f8}
body{max-width:540px;margin:0 auto;padding:20px;line-height:1.48}
h1{font-size:1.48rem;margin-bottom:8px}
p,small{color:#c5d4e1}
section{border:1px solid #687d91;border-radius:12px;padding:16px;margin:16px 0}
label{display:block;font-weight:650;margin:12px 0 4px}
input,button{width:100%;box-sizing:border-box;padding:13px;margin:7px 0;border-radius:9px;font:inherit}
input{background:#223347;border:1px solid #9bb4c7;color:#fff}
button{background:#316881;border:1px solid #a1c9db;color:#fff;font-weight:700}
button:disabled{opacity:.55}
#summary{font-size:1.12rem;font-weight:650;margin-top:10px}
pre{font:12px ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;
background:#192935;padding:12px;border-radius:8px}
a{color:#b7dff3}
small{display:block;margin-top:10px}
</style></head><body>
<main>
<h1>GaiaOS · Historical evidence check</h1>
<p>One read-only check to identify what real historical evidence is missing.
This does not call AUGURY, change memories, or unlock BIGBANG.</p>
<section>
<label for="secret">Your private GaiaOS API key</label>
<input id="secret" type="password" autocomplete="off" autocapitalize="off"
spellcheck="false" placeholder="Paste here, not into chat">
<button id="audit" type="button">Check historical evidence</button>
<p id="status" role="status" aria-live="polite">No check performed.</p>
<div id="summary" role="status" aria-live="polite"></div>
<small>Your key stays on this same-origin page; it is never included in the result.
Only a successful, bounded audit displays numerical findings.</small>
</section>
<section>
<h2>Redacted result</h2>
<pre id="result">Run the check to create a safe, redacted result.</pre>
<button id="copy" type="button" disabled>Copy redacted result</button>
<small>Share only the redacted JSON. Do not share the API key, source statements,
record identifiers, or screenshots of private technical review.</small>
</section>
</main>
<script nonce="__NONCE__">
"use strict";
const byId=id=>document.getElementById(id);
const endpoint="/gaiaos/memory/historical-evidence-audit";
const explanations=Object.freeze({
  NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW:
    "No verified owner-authorized supersession was found in the bounded sample.",
  NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR:
    "A supersession exists, but it does not connect two approved technical memories.",
  NO_ACTIVE_APPROVED_SUCCESSOR:
    "A matching pair exists, but its newer approved memory is not ACTIVE.",
  NO_DISTINCT_HISTORICAL_MARKER:
    "A matching pair exists, but the older memory has no unique version marker.",
  HISTORICAL_GOVERNING_STATE_UNVERIFIED:
    "The source relationship exists, but its historical governing state is unverified.",
  HISTORICAL_GOVERNING_STATE_READ_FAILED:
    "The historical governing state could not be read safely.",
  HISTORICAL_CANDIDATE_PREPARED_UNTESTED:
    "A real historical candidate is present. Historical retrieval has NOT been tested.",
  STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED:
    "Some historical evidence exists, but the full Stage 7 sample is not ready.",
  BOUNDED_WINDOW_INCOMPLETE:
    "There are more records than the safe audit window. No conclusion was drawn.",
  BOUNDED_SOURCE_READ_FAILED:
    "The bounded source check could not complete.",
  REMOTE_STORAGE_NOT_CONFIRMED:
    "The configured remote MemoryOS storage could not be confirmed.",
  RUNTIME_NOT_INITIALIZED:
    "The MemoryOS runtime is not initialized.",
  HEATDEATH_RELEASE_LOCK_NOT_VERIFIED:
    "The HEATDEATH protection could not be verified. No audit was run."
});
const countFields=[
  "approved_technical_records_in_window",
  "verified_owner_supersedes_in_window",
  "approved_technical_pairs_in_window",
  "active_successor_pairs_in_window",
  "distinct_old_marker_pairs_in_window",
  "governed_historical_pairs_in_window"
];
let redacted=null;
function safeResult(source){
  if(!source||source.schema!=="gaiaos.galaxy.stage9j.historical-evidence-audit.v1"||
     !["HOLD","CANDIDATE_PRESENT_UNTESTED"].includes(source.status)||
     typeof source.reason!=="string"||
     !/^[A-Z][A-Z0-9_]*$/.test(source.reason)||
     source.model_called!==false||source.release_activated!==false||
     source.historical_retrieval_proven!==false||
     source.historical_retrieval_tested!==false||
     source.general_semantic_quality_proven!==false||
     source.record_ids_disclosed!==false||
     source.statements_disclosed!==false||
     source.sources_disclosed!==false||
     source.markers_disclosed!==false||
     source.e_lanes_modified!==false||
     !Array.isArray(source.writes_performed)||source.writes_performed.length!==0||
     typeof source.bounded_window_complete!=="boolean"){
    throw Error("The audit response did not meet its read-only privacy contract.");
  }
  if(!Object.prototype.hasOwnProperty.call(explanations,source.reason)){
    throw Error("Unknown audit result. No private response was copied.");
  }
  const out={
    schema:source.schema,status:source.status,reason:source.reason,
    explanation:explanations[source.reason],
    bounded_window_complete:source.bounded_window_complete,
    historical_case_prepared:source.historical_case_prepared===true,
    historical_retrieval_tested:false,historical_retrieval_proven:false,
    general_semantic_quality_proven:false,
    full_readiness_status:"HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
    model_called:false,writes_performed:[],e_lanes_modified:false,
    release_activated:false
  };
  if(source.bounded_window_complete){
    for(const field of countFields){
      const value=source[field];
      if(!Number.isInteger(value)||value<0||value>100){
        throw Error("Bounded audit count is invalid.");
      }
      out[field]=value;
    }
  }
  return out;
}
byId("audit").addEventListener("click",async()=>{
  const key=byId("secret").value.trim();
  if(!key){byId("status").textContent="Enter your private API key in this page first.";return;}
  redacted=null;byId("copy").disabled=true;
  byId("audit").disabled=true;
  byId("summary").textContent="";
  byId("result").textContent="Checking…";
  byId("status").textContent="Checking approved historical evidence. No model call…";
  try{
    const response=await fetch(endpoint,{
      method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
      headers:{"Authorization":"Bearer "+key}
    });
    if(!response.ok){
      if(response.status===401)throw Error("Invalid or missing private API key.");
      throw Error("Historical audit unavailable (HTTP "+response.status+").");
    }
    const raw=await response.json();
    redacted=safeResult(raw);
    byId("summary").textContent=redacted.explanation;
    byId("result").textContent=JSON.stringify(redacted,null,2);
    byId("copy").disabled=false;
    byId("status").textContent=redacted.historical_case_prepared
      ?"Candidate found, but historical retrieval and BIGBANG remain unproven."
      :"Diagnostic complete. Missing prerequisites remain HOLD.";
  }catch(error){
    byId("summary").textContent="";
    byId("result").textContent="No verified result to copy.";
    byId("status").textContent="HOLD: "+error.message;
  }finally{byId("audit").disabled=false;}
});
byId("copy").addEventListener("click",async()=>{
  if(!redacted)return;
  try{
    await navigator.clipboard.writeText(JSON.stringify(redacted,null,2));
    byId("status").textContent="Redacted result copied. No private memories or key included.";
  }catch(error){
    byId("status").textContent="Clipboard unavailable. Select and copy the redacted JSON above.";
  }
});
</script></body></html>
"""


def render(nonce: str) -> str:
    if not isinstance(nonce, str) or not nonce:
        raise ValueError("Nonce required")
    return PAGE.replace("__NONCE__", nonce)
