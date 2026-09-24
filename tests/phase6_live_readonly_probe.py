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

code, verified_html = get("/verify", timeout=65)
match = re.search(r"<pre[^>]*>(.*?)</pre>", verified_html, flags=re.S)
if code != 200 or not match:
    raise SystemExit("HOLD: verifier HTML not available with browser cookie")
verifier = json.loads(html.unescape(match.group(1)))
names = {
    "carrier:phase6-lifecycle-module",
    "carrier:phase6-lifecycle-boundaries",
    "carrier:/galaxy/phase6-fixture-review",
    "carrier-route:/galaxy/phase6-fixture-review",
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
print("PASS: source deployed and exact Phase6 read-only live review completed. NO MUTATIONS.")
