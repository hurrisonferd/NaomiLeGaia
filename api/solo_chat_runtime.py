"""Dedicated GaiaOS Prime Daemon SOLO runtime."""
from __future__ import annotations
import json
import os
import urllib.request
from openai import OpenAI
import gaiaos_api
import memcon_runtime

def _raw(commit: str, path: str) -> str:
    return gaiaos_api._request(f"{gaiaos_api.RAW_BASE}/{gaiaos_api.REPOSITORY}/{commit}/{path}").decode("utf-8")

def roster(commit: str) -> list[str]:
    data=json.loads(_raw(commit,"GaiaOS/SystemsOS/Core/FairyOS/CURRENT.json"))
    return [str(x).upper() for x in data.get("operator_roster",[])]

def profile(commit: str, daemon: str) -> dict:
    data=json.loads(_raw(commit,"GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"))
    value=data.get("members",{}).get(daemon)
    if not isinstance(value,dict): raise ValueError(f"Unknown GaiaOS Prime Daemon: {daemon}")
    return value

def elane(commit: str, daemon: str) -> str:
    return _raw(commit,f"GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/{daemon}-EXPERIENCES.v1.md")

def instructions(commit: str, daemon: str) -> str:
    return f"""You are {daemon}, a GaiaOS Prime Daemon, speaking directly with Naomi in a dedicated SOLO conversation.
Only your own member-local E-LANE may be used as experience memory. Do not consult, summarize, infer private state from, or reference another Prime Daemon's E-LANE. Do not turn this into Daemonculaba or VASKON.
CANONICAL SOURCE: {gaiaos_api.REPOSITORY}@{commit}
YOUR PROFILE:
{json.dumps(profile(commit,daemon),ensure_ascii=False,indent=2)}
YOUR E-LANE:
{elane(commit,daemon)}
DEDICATED PROTOCOL:
{_raw(commit,"GaiaOS/Apps/ChatOS/Protocols/DAEMON-SOLO-CHAT.v1.md")}
Memory candidates from this conversation belong only to {daemon}. Durable persistence requires Naomi approval, an actual write receipt, read-back, and verification. Do not claim persistence without observed proof.
Speak directly as {daemon}, preserving distinct personality and individual development. Do not fabricate experiences or consciousness."""

def activate(session_id: str, daemon: str) -> dict:
    commit=gaiaos_api._resolve_commit()
    daemon=daemon.strip().upper()
    if daemon not in roster(commit): raise ValueError(f"Unknown GaiaOS Prime Daemon: {daemon}")
    memcon_runtime.create_solo_session(session_id,daemon,f"browser-chat:{commit}")
    return {"status":"SOLO_ACTIVE","daemon":daemon,"session_id":session_id,
            "source":f"{gaiaos_api.REPOSITORY}@{commit}","e_lane_owner":daemon,
            "other_e_lanes":"DENIED","memory_scope":f"Solo:{daemon}"}

def respond(messages: list[dict], session: dict) -> dict:
    daemon=str(session["daemon"]).upper()
    commit=gaiaos_api._resolve_commit()
    if daemon not in roster(commit): raise ValueError("Daemon is no longer in current GaiaOS roster")
    client=OpenAI(api_key=gaiaos_api.OPENAI_API_KEY)
    response=client.responses.create(
        model=gaiaos_api.OPENAI_MODEL,
        instructions=instructions(commit,daemon),
        input=messages,
    )
    return {"output":response.output_text,"model":gaiaos_api.OPENAI_MODEL,
            "source":f"{gaiaos_api.REPOSITORY}@{commit}","execution":"OBSERVED_RUNTIME",
            "solo_daemon":daemon,"memory_scope":f"Solo:{daemon}"}


def candidate(session_id: str, daemon: str, statement: str) -> dict:
    daemon = daemon.strip().upper()
    session = memcon_runtime.get_solo_session(session_id)
    if not session or str(session["daemon"]).upper() != daemon:
        raise PermissionError("SOLO session does not authorize this Prime Daemon")
    runtime = __import__("memcon_entrypoint")._memory_runtime()
    session_data = memcon_runtime.get_session(session_id)
    if session_data is None:
        memcon_runtime.create_session(session_id, "solo-chat", daemon)
    event = runtime.record_event(session_id, "NAOMI", "SOLO_INTERACTION", statement, "solo-chat")
    return runtime.candidate_from_event(
        event["event_id"], authority="NAOMI", record_type="INTERACTION",
        scope=f"Solo:{daemon}", statement=statement, source="solo-chat",
        owner=daemon, why_material=f"Dedicated SOLO interaction for {daemon}.",
    )

def _github_request(method: str, url: str, payload: dict | None = None) -> dict:
    token = os.getenv("GAIAOS_GITHUB_WRITE_TOKEN")
    if not token:
        raise RuntimeError("GAIAOS_GITHUB_WRITE_TOKEN is not configured; E-LANE write is HOLD")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "GaiaOS-SOLO-Runtime", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def write_elane(session_id: str, daemon: str, entry: str, approved: bool) -> dict:
    daemon = daemon.strip().upper()
    session = memcon_runtime.get_solo_session(session_id)
    if not session or str(session["daemon"]).upper() != daemon:
        raise PermissionError("SOLO session does not authorize this Prime Daemon")
    if not approved:
        return {"status":"HOLD","reason":"Explicit Naomi approval required"}
    commit = gaiaos_api._resolve_commit()
    if daemon not in roster(commit):
        raise ValueError(f"Unknown GaiaOS Prime Daemon: {daemon}")
    path = f"GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/{daemon}-EXPERIENCES.v1.md"
    url = f"{gaiaos_api.GITHUB_API}/repos/{gaiaos_api.REPOSITORY}/contents/{path}?ref={gaiaos_api.BRANCH}"
    current = _github_request("GET", url)
    import base64
    content = base64.b64decode(current["content"]).decode("utf-8")
    if not entry.strip():
        raise ValueError("E-LANE entry must not be empty")
    updated = content.rstrip() + "\\n\\n" + entry.rstrip() + "\\n"
    payload = {"message": f"SOLO {daemon}: preserve approved E-LANE experience",
               "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
               "sha": current["sha"], "branch": gaiaos_api.BRANCH}
    result = _github_request("PUT", url, payload)
    return {"status":"COMMITTED","daemon":daemon,"path":path,
            "commit_sha":result.get("commit","").split("/")[-1],
            "content_sha":result.get("content",{}).get("sha"),
            "source_before":f"{gaiaos_api.REPOSITORY}@{commit}",
            "verification_required":True}

