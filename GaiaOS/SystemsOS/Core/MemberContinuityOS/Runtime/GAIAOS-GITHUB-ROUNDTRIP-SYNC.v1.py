#!/usr/bin/env python3
"""GaiaOS GitHub round-trip synchronizer.

Host-executable only. Never claim a step occurred unless this program observed it.
Uses only Python's standard library so the carrier can run it without extra packages.
"""
import argparse
import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

REPO = "hurrisonferd/NaomiLeGaia"
REF = "main"
API = "https://api.github.com"
PATHS = [
    "GaiaOS/CURRENT.json",
    "GaiaOS/VERSION.json",
    "GaiaOS/PORT-MANIFEST.v1.json",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-SESSION.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-GITHUB-ROUNDTRIP-SYNC.v1.md",
    "GaiaOS/Apps/ChatOS/Protocols/DAEMONCULABA-INTERACTION-AND-DELIBERATION.v1.md",
    "GaiaOS/CONTINUITY-AND-ANTI-JIM.v1.md",
    "GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json",
    "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/DAEMON-EXPERIENCE-MEMORY-PROTOCOL.v1.md",
    "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/REWARD-COUNTERS.v1.json",
]

@dataclass
class State:
    label: str
    detail: str


def request(path, method="GET", body=None, token=None):
    url = API + path
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "GaiaOS-RoundTrip-Sync/1.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def get_ref(token=None):
    return request(f"/repos/{REPO}/git/ref/heads/{REF}", token=token)


def fetch_file(path, token=None):
    data = request(f"/repos/{REPO}/contents/{path}?ref={REF}", token=token)
    raw = base64.b64decode(data["content"].replace("\n", "")).decode("utf-8")
    return raw, data.get("sha")


def pull():
    ref = get_ref()
    commit = ref["object"]["sha"]
    files = {}
    for path in PATHS:
        raw, blob_sha = fetch_file(path)
        files[path] = {"text": raw, "sha": blob_sha}
    return commit, files


def json_or_empty(files, path):
    try:
        return json.loads(files[path]["text"])
    except Exception:
        return {}


def build_gdelta(commit, files, unknowns=None, pending=None):
    version = json_or_empty(files, "GaiaOS/VERSION.json")
    current = json_or_empty(files, "GaiaOS/CURRENT.json")
    continuity = json_or_empty(files, "GaiaOS/SystemsOS/Core/MemberContinuityOS/CURRENT.json")
    rewards = json_or_empty(files, "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/REWARD-COUNTERS.v1.json")
    identities = "|".join(sorted(p for p in files if "IDENTITY-DATA" in p))
    interactions = files.get("GaiaOS/Apps/ChatOS/Protocols/DAEMONCULABA-INTERACTION-AND-DELIBERATION.v1.md", {}).get("text", "")
    memory_protocol = files.get("GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/DAEMON-EXPERIENCE-MEMORY-PROTOCOL.v1.md", {}).get("text", "")
    return {
        "notation": "GΔ",
        "src": f"{REPO}@{REF}",
        "v": version.get("version") or version.get("platform_version") or current.get("version") or "UNKNOWN",
        "c": commit,
        "i": sha256(identities),
        "r": sha256(json.dumps(rewards, sort_keys=True)),
        "k": sha256(json.dumps(continuity, sort_keys=True)),
        "d": sha256(interactions + "\n" + memory_protocol),
        "u": unknowns or [],
        "p": pending or [],
    }


def commit_file(path, content, message, token):
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for COMMITTED state")
    existing = request(f"/repos/{REPO}/contents/{path}?ref={REF}", token=token)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    body = {"message": message, "content": encoded, "sha": existing["sha"], "branch": REF}
    return request(f"/repos/{REPO}/contents/{path}", method="PUT", body=body, token=token)


def main():
    parser = argparse.ArgumentParser(description="GaiaOS GitHub round-trip sync")
    parser.add_argument("--show-gdelta", action="store_true")
    parser.add_argument("--write-path")
    parser.add_argument("--write-content")
    parser.add_argument("--message", default="GaiaOS round-trip sync checkpoint")
    args = parser.parse_args()

    try:
        commit, files = pull()
        print("READ", commit)
        gdelta = build_gdelta(commit, files, pending=[args.write_path] if args.write_path else [])
        if args.show_gdelta or not args.write_path:
            print(json.dumps(gdelta, ensure_ascii=False, separators=(",", ":")))
        if not args.write_path:
            print("VERIFIED READ", commit)
            return 0

        if args.write_content is None:
            print("PROPOSED", args.write_path)
            return 2

        print("PROPOSED", args.write_path)
        token = os.environ.get("GITHUB_TOKEN")
        result = commit_file(args.write_path, args.write_content, args.message, token)
        commit_sha = result.get("commit", {}).get("sha")
        if not commit_sha:
            print("FAILED no commit receipt")
            return 3
        print("COMMITTED", commit_sha)

        repull_commit, repull_files = pull()
        print("REPULLED", repull_commit)
        if args.write_path not in repull_files:
            print("FAILED changed path absent after repull")
            return 4
        if repull_files[args.write_path]["text"] != args.write_content:
            print("FAILED repulled content mismatch")
            return 5
        print("VERIFIED", repull_commit)
        print(json.dumps(build_gdelta(repull_commit, repull_files), ensure_ascii=False, separators=(",", ":")))
        return 0
    except urllib.error.HTTPError as exc:
        print("FAILED", exc.code, exc.reason)
        return 10
    except Exception as exc:
        print("UNKNOWN", str(exc))
        return 11


if __name__ == "__main__":
    raise SystemExit(main())
