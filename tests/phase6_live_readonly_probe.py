"""Read-only remote Phase-6 smoke against Naomi's existing Render carrier.

No credentials are printed, no POST is sent, no data is mutated. Browser's normal
signed-session bootstrap is used only to access GET review and GET verifier.
"""
import html
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HOST = "https://ligeia-api.onrender.com"
EXPECTED_VERSION = "galaxy.phase6.reversible-lifecycle.v1"
EXPECTED_RECORD = "MEM-00b3fbfd4d73404f97a95c238596ab94"

jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(path, timeout=50):
    req = urllib.request.Request(HOST + path, method="GET",
        headers={"User-Agent": "GaiaOS-Phase6-ReadOnly-CI/1.0",
                 "Accept": "application/json,text/html"})
    with client.open(req, timeout=timeout) as r:
        return r.status, r.read(1000000).decode("utf-8")


health_ok = False
for attempt in range(15):
    try:
        code, body = get("/health")
        health_ok = code == 200
        if health_ok:
            print("HEALTH PASS, retry:", attempt)
            break
        print("HEALTH HOLD", code)
    except Exception as exc:
        print("HEALTH WAIT", type(exc).__name__, str(exc)[:130])
    if attempt < 14:
        time.sleep(20)

if not health_ok:
    raise SystemExit("HOLD: Render did not answer /health within bounded retries")

code, manifest = get("/runtime/routes")
routes = json.loads(manifest)
if code != 200 or not routes.get("verify_registered"):
    raise SystemExit("HOLD: runtime route manifest lacks verifier")
print("MANIFEST PASS: /verify registered; source:", routes.get("source"))

review = None
for attempt in range(6):
    try:
        code, body = get("/galaxy/lifecycle/phase6-fixture-review")
        review = json.loads(body)
        if (code == 200 and review.get("version") == EXPECTED_VERSION
                and review.get("execution") == "READ_ONLY"):
            break
        print("PHASE6 WAIT: endpoint not matching current source", review.get("status"))
    except Exception as exc:
        print("PHASE6 WAIT", type(exc).__name__, str(exc)[:130])
    review = None
    if attempt < 5:
        time.sleep(20)

if review is None:
    raise SystemExit("HOLD: Phase6 GET not deployed or not readable")
if review.get("record_id") != EXPECTED_RECORD:
    raise SystemExit("FAIL: wrong controlled fixture record")
if (review.get("writes") != 0 or review.get("physical_delete") is not False
        or review.get("production_retrieval_changed") is not False):
    raise SystemExit("FAIL: Phase6 review proof boundary broken")
print("PHASE6 ROUTE PASS:", review.get("status"),
      "state:", review.get("current_state"), "events:", review.get("event_count"),
      "holds:", review.get("hold_reasons"))

code, control_html = get("/galaxy/lifecycle/phase6-controls")
control_match = re.search(r"<pre[^>]*>(.*?)</pre>", control_html, flags=re.S)
if code != 200 or not control_match:
    raise SystemExit("HOLD: Phase6 control review HTML unavailable")
control = json.loads(html.unescape(control_match.group(1)))
expected_chain = [
    ("BACKGROUND", "ACTIVE", "BACKGROUND",
     "LIFE-39d6922cca684861b56acbcc5e6f281c",
     "MEMREC-a3d9439e02a44106b96163e478a17239"),
    ("ARCHIVED", "BACKGROUND", "ARCHIVED",
     "LIFE-e259f588cdab49139ae4765ca90bcbb4",
     "MEMREC-2598b57ee627444095b1607755d1f77c"),
    ("COMPRESSED", "ARCHIVED", "COMPRESSED",
     "LIFE-c82800edc9c94a42afe4170c152e19fa",
     "MEMREC-ae95eeb0c0ea4c9ab23196777f4444c1"),
    ("ROLLBACK", "COMPRESSED", "ARCHIVED",
     "LIFE-2204bf94189a446e8ac2b731d884bc60",
     "MEMREC-a366ad8e19ef4e96b9c5285b7f75168f"),
    ("REACTIVATE", "ARCHIVED", "ACTIVE",
     "LIFE-c7793ae706f2404c81828606b8470895",
     "MEMREC-b60d42b065124a1cb5ae0d6891a343b2"),
]
if (control.get("controlled_record_id") != EXPECTED_RECORD
        or control.get("current_state") != "ACTIVE"
        or control.get("completed_steps") != 5
        or control.get("next_action") is not None
        or control.get("campaign_complete") is not True
        or control.get("hold_reasons") != []):
    raise SystemExit("HOLD: Phase6 exact campaign is not complete and clean: " + str(control))
events = review.get("events") or []
if review.get("event_count") != 5 or len(events) != 5:
    raise SystemExit("HOLD: Phase6 campaign does not have exactly five persisted events")
for idx, (action, from_state, to_state, event_id, receipt_id) in enumerate(expected_chain):
    e = events[idx]
    if (e.get("action") != action or e.get("from_state") != from_state
            or e.get("to_state") != to_state or e.get("event_id") != event_id
            or e.get("receipt_id") != receipt_id):
        print("CHAIN DETAIL:", json.dumps(events, sort_keys=True))
        raise SystemExit("HOLD: Phase6 exact five-event chain mismatch at index " + str(idx))
    if idx == 0:
        if e.get("previous_event_id") is not None:
            raise SystemExit("HOLD: first Phase6 event unexpectedly has a predecessor")
    elif e.get("previous_event_id") != expected_chain[idx - 1][3]:
        raise SystemExit("HOLD: Phase6 previous_event_id chain broken at index " + str(idx))
if review.get("latest_event_id") != expected_chain[-1][3]:
    raise SystemExit("HOLD: Phase6 latest event is not the exact REACTIVATE event")
print("PHASE6 CONTROL REVIEW PASS: state:", control.get("current_state"),
      "steps:", control.get("completed_steps"), "campaign_complete:",
      control.get("campaign_complete"), "latest_event:", review.get("latest_event_id"))

code, verified_html = get("/verify", timeout=65)
match = re.search(r"<pre[^>]*>(.*?)</pre>", verified_html, flags=re.S)
if code != 200 or not match:
    raise SystemExit("HOLD: verifier HTML not available with browser cookie")
verifier = json.loads(html.unescape(match.group(1)))
names = {
    "carrier:phase6-lifecycle-module",
    "carrier:phase6-lifecycle-boundaries",
    "carrier:phase6-control-module",
    "carrier:phase6-control-boundaries",
    "carrier:/galaxy/phase6-fixture-review",
    "carrier:/galaxy/phase6-control-review",
    "carrier:/galaxy/phase6-control-manifest",
    "carrier-route:/galaxy/phase6-fixture-review",
    "carrier-route:/galaxy/phase6-control-review",
    "carrier-route:/galaxy/phase6-control-manifest",
    "carrier:phase6-control-read-only-self-test",
}
observed = {c.get("name"): c for c in verifier.get("checks", [])}
missing = names - observed.keys()
failed = [n for n in names if observed.get(n, {}).get("status") != "PASS"]
print("VERIFY SUMMARY:", verifier.get("summary"))
print("PHASE6 VERIFIER:", {n:observed.get(n,{}).get("status") for n in sorted(names)})
if missing or failed:
    raise SystemExit("HOLD: Phase6 verifier checks missing/failed: " +
                     str(sorted(missing | set(failed))))
if verifier.get("summary", {}).get("failed") != 0:
    failed_checks = [
        {"name": c.get("name"), "detail": c.get("detail"), "extra": {
            k:v for k,v in c.items() if k not in {"name","status","detail"}
        }}
        for c in verifier.get("checks", []) if c.get("status") != "PASS"
    ]
    print("WARNING: other carrier verification checks failed; Phase6 checks PASS")
    print("FAILED VERIFIER CHECKS:", json.dumps(failed_checks, sort_keys=True))
if review.get("status") != "PASS_READ_ONLY":
    raise SystemExit("HOLD: Phase6 source deployed, but fixture read-only review held: " +
                     str(review.get("hold_reasons")))
print("PASS: source deployed; exact complete five-step Phase6 campaign chain read back live. NO NEW MUTATIONS.")
