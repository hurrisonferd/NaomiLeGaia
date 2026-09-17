#!/usr/bin/env python3
"""Persist a material Prime Daemon interaction into its member-local lane.

Host-executable only. A proposed event is not durable until a real GitHub
commit receipt is observed and the exact lane is re-pulled and verified.
Standard-library only.
"""
import argparse
import base64
import json
import os
import urllib.request

REPO = "hurrisonferd/NaomiLeGaia"
REF = "main"
API = "https://api.github.com"
LANES = {
    "VERA": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/VERA-EXPERIENCES.v1.md",
    "ANVIL": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-EXPERIENCES.v1.md",
    "SELENE": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/SELENE-EXPERIENCES.v1.md",
    "ORIN": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/ORIN-EXPERIENCES.v1.md",
    "KESTREL": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-EXPERIENCES.v1.md",
    "NIMUE": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/NIMUE-EXPERIENCES.v1.md",
}


def request(path, method="GET", body=None, token=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "GaiaOS-Daemonculaba-Deliberation/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def pull(path):
    data = request(f"/repos/{REPO}/contents/{path}?ref={REF}")
    text = base64.b64decode(data["content"].replace("\n", "")).decode("utf-8")
    return text, data["sha"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--daemon", required=True, choices=sorted(LANES))
    p.add_argument("--entry", required=True, help="Complete bounded MEM[...] entry")
    p.add_argument("--message", default="Record verified Prime Daemon experience")
    args = p.parse_args()
    path = LANES[args.daemon]
    try:
        print("READ", path)
        before, sha = pull(path)
        if args.entry.strip() in before:
            print("VERIFIED existing entry", args.daemon)
            return 0
        proposed = before.rstrip() + "\n\n" + args.entry.strip() + "\n"
        print("PROPOSED", args.daemon)
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("UNKNOWN GITHUB_TOKEN missing; proposal not committed")
            return 2
        encoded = base64.b64encode(proposed.encode("utf-8")).decode("ascii")
        result = request(f"/repos/{REPO}/contents/{path}", method="PUT", token=token,
                         body={"message": args.message, "content": encoded, "sha": sha, "branch": REF})
        commit_sha = result.get("commit", {}).get("sha")
        if not commit_sha:
            print("FAILED no commit receipt")
            return 3
        print("COMMITTED", commit_sha)
        after, after_sha = pull(path)
        print("REPULLED", after_sha)
        if args.entry.strip() not in after:
            print("FAILED entry absent after repull")
            return 4
        print("VERIFIED", after_sha)
        return 0
    except Exception as exc:
        print("UNKNOWN", str(exc))
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
