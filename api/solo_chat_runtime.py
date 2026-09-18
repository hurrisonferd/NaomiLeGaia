"""Dedicated GaiaOS Prime Daemon SOLO runtime."""
from __future__ import annotations
import json
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
