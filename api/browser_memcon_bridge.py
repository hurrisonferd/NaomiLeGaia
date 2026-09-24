"""Explicit browser bridge for live MemconOS and MemoryOS verification."""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import re
import uuid
from urllib.parse import parse_qs

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import gaiaos_app
import gaiaos_api
import memcon_entrypoint
import memcon_runtime
import galaxy_production
import galaxy_quality
import galaxy_phase3_exit
import galaxy_phase4
import galaxy_phase5
import galaxy_phase5_controls
import galaxy_phase6
import galaxy_phase6_controls
import galaxy_phase7
import galaxy_phase7_tombstone
import galaxy_phase7_tombstone_shadow
import galaxy_phase7_isolated_restore
import galaxy_phase7_isolated_restore
import augury_ritual
import solo_chat_runtime
import host_memory_gateway
import gaiaos_verification
import vaskon_runtime

app = memcon_entrypoint.app
_original_chat = gaiaos_api.chat
_memory_runtime = memcon_entrypoint._memory_runtime
TEST_OWNER = "NAOMI_BROWSER_TEST"
GALAXY_CANARY_OWNER_A = "GALAXY_CANARY_A"
GALAXY_CANARY_OWNER_B = "GALAXY_CANARY_B"

app.routes[:] = [
    route for route in app.routes
    if not (getattr(route, "path", None) == "/chat" and getattr(route, "methods", set()) == {"POST"})
]


def _envelope(title: str, body: dict) -> dict:
    return {
        "output": title + "\n\n" + json.dumps(body, ensure_ascii=False, indent=2),
        "model": "gaiaos-carrier-runtime",
        "source": gaiaos_app._deployed_source(),
        "execution": "OBSERVED_RUNTIME",
    }


@app.post("/chat", operation_id="browserChatWithMemoryRuntime")
async def browser_chat(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    payload = await browser_request.json()
    messages = payload.get("messages", [])
    last_message = messages[-1].get("content", "").strip() if messages else ""
    if re.match(r"^\\s*//C:82//\\s*$", last_message, flags=re.IGNORECASE):
        messages[-1]["content"] = "CONJURE:VASKON"
        last_message = "CONJURE:VASKON"
    if last_message.lower().rstrip(".") == "load gaiaos":
        # Deterministic browser boot: do not ask the language model to infer loaded state.
        # Anti-Jim requires a fresh validated source-derived boot packet for this session.
        return _envelope(
            "GAIAOS = ACTIVE / VERIFIED",
            gaiaos_app._boot_packet("BROWSER_CHAT_COMMAND"),
        )
    if last_message.lower().rstrip(".") == "test the live memconos canary at the current pinned revision":
        return _envelope("LIVE MEMCONOS CANARY EXECUTED", memcon_runtime.canary())
    if last_message.lower().rstrip(".") == "start the live memoryos lifecycle test":
        return _start_lifecycle()
    if last_message.lower().rstrip(".") == "approve the pending memoryos candidate":
        return _approve_lifecycle()
    if _is_command(last_message, "SOLO"):
        return _handle_solo(last_message, browser_request)
    if _is_command(last_message, "ENDSOLO"):
        return _handle_endsolo(browser_request)
    solo = memcon_runtime.get_solo_session(_browser_session_id(browser_request))
    if solo:
        return solo_chat_runtime.respond(
            [{"role": m.get("role"), "content": m.get("content")} for m in messages],
            solo,
        )
    if _is_preserve_command(last_message):
        return _handle_preserve(messages, browser_request)
    if _is_galaxy_command(last_message, "ORBIT"):
        return _handle_galaxy_orbit(last_message)
    if _is_galaxy_command(last_message, "GRAVITY"):
        return _handle_galaxy_gravity(last_message)
    if re.match(r"^\s*GALAXY\s+CANARY\s+START\s*[.!]?\s*$", last_message, flags=re.IGNORECASE):
        return _handle_galaxy_canary_start()
    if re.match(r"^\s*GALAXY\s+CANARY\s+APPROVE\s*[.!]?\s*$", last_message, flags=re.IGNORECASE):
        return _handle_galaxy_canary_approve()
    if re.match(r"^\s*GALAXY\s+PROPOSE(?:\s+.*)?$", last_message, flags=re.IGNORECASE):
        return _handle_galaxy_relation_propose(last_message)
    if re.match(r"^\s*GALAXY\s+VERIFY(?:\s+.*)?$", last_message, flags=re.IGNORECASE):
        return _handle_galaxy_relation_verify(last_message)
    if _is_command(last_message, "CANDIPULL"):
        return _handle_candipull(messages, browser_request)
    if _is_command(last_message, "MEMSAV"):
        return _handle_memsav(last_message)
    return _original_chat(gaiaos_api.ChatRequest.model_validate(payload), browser_request)


def _handle_solo(command: str, request: Request) -> dict:
    daemon = re.sub(r"^SOLO\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip().upper()
    if not daemon:
        return _envelope("SOLO HOLD", {"status": "HOLD", "reason": "Prime Daemon name required."})
    try:
        result = solo_chat_runtime.activate(_browser_session_id(request), daemon)
    except ValueError as exc:
        return _envelope("SOLO HOLD", {"status": "HOLD", "reason": str(exc)})
    return _envelope("SOLO SESSION ESTABLISHED", result)

def _handle_endsolo(request: Request) -> dict:
    session_id = _browser_session_id(request)
    current = memcon_runtime.get_solo_session(session_id)
    memcon_runtime.end_solo_session(session_id)
    return _envelope("SOLO SESSION ENDED", {
        "status": "SOLO_INACTIVE",
        "previous_daemon": current.get("daemon") if current else None,
        "session_id": session_id,
    })


def _handle_solo_candipull(messages: list[dict], request: Request, solo: dict) -> dict:
    daemon = str(solo["daemon"]).upper()
    substantive = [
        str(m.get("content","")).strip() for m in messages[:-1]
        if str(m.get("role","")).lower() == "user"
        and str(m.get("content","")).strip()
        and not _is_command(str(m.get("content","")), "SOLO")
        and not _is_command(str(m.get("content","")), "CANDIPULL")
        and not _is_command(str(m.get("content","")), "MEMSAV")
    ]
    if not substantive:
        return _envelope("SOLO CANDIPULL HOLD", {"status":"HOLD","reason":"No substantive interaction available."})
    candidate = solo_chat_runtime.candidate(_browser_session_id(request), daemon, substantive[-1])
    return _envelope("SOLO CANDIDATE READY", {
        "status":"CANDIDATE_READY","daemon":daemon,"candidate":candidate,
        "memory_scope":f"Solo:{daemon}","other_e_lanes":"DENIED",
        "next_command":"MEMSAV <candidate_id>",
    })

def _handle_solo_memsav(command: str, request: Request, solo: dict) -> dict:
    body = re.sub(r"^MEMSAV\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()
    if not body:
        return _envelope("SOLO MEMSAV HOLD", {"status":"HOLD","reason":"Exact candidate_id required."})
    candidate_id = body.split()[0]
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    daemon = str(solo["daemon"]).upper()
    if not candidate:
        return _envelope("SOLO MEMSAV HOLD", {"status":"HOLD","reason":"Unknown candidate_id"})
    if str(candidate.get("owner","")).upper() != daemon or str(candidate.get("scope","")) != f"Solo:{daemon}":
        return _envelope("SOLO MEMSAV HOLD", {
            "status":"HOLD","reason":"Candidate is outside this SOLO member-local scope.",
            "daemon":daemon,"candidate_id":candidate_id,
        })
    entry = (
        f"MEM[EXPERIENCE_PRESERVATION|{candidate.get('created_at','')[:10]}|"
        f"SOLO {daemon}|dedicated_conversation]\n"
        f"WHAT: {candidate.get('statement','')}\n"
        f"MY_ROLE: Material interaction preserved through dedicated SOLO conversation.\n"
        f"TRACE: candidate {candidate_id}; session {candidate.get('event_id')}\n"
        f"STATUS: COMMITTED"
    )
    result = solo_chat_runtime.write_elane(_browser_session_id(request), daemon, entry, approved=True)
    if result.get("status") == "COMMITTED":
        memcon_runtime.mark_candidate(candidate_id, "VERIFIED", result.get("commit_sha"))
        result["candidate_id"] = candidate_id
        result["readback_required"] = True
    return _envelope("SOLO MEMSAV", result)


def _is_command(text: str, command: str) -> bool:
    return bool(re.match(rf"^\s*{re.escape(command)}(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _is_galaxy_command(text: str, word: str) -> bool:
    return bool(re.match(rf"^\s*(?://)?PW:{re.escape(word)}(?://)?(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _galaxy_command_body(command: str, word: str) -> str:
    return re.sub(rf"^\s*(?://)?PW:{re.escape(word)}(?://)?\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()


def _handle_galaxy_orbit(command: str) -> dict:
    """Read-only Phase 1 inspection. No edge is inferred or written by this command."""
    record_id = _galaxy_command_body(command, "ORBIT").split()[0] if _galaxy_command_body(command, "ORBIT") else ""
    if not record_id:
        return _envelope("PW:ORBIT", {
            "status": "READY",
            "galaxy": memcon_runtime.galaxy_status(),
            "usage": "//PW:ORBIT// MEM-<record_id>",
            "writes_performed": [],
        })
    result = memcon_runtime.galaxy_record(record_id)
    if result is None:
        return _envelope("PW:ORBIT HOLD", {"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id})
    return _envelope("PW:ORBIT", {"status": "OBSERVED", "record_id": record_id, "orbit": result, "writes_performed": []})


def _handle_galaxy_gravity(command: str) -> dict:
    """Read/preview Phase-2 gravity without silently writing a score."""
    record_id = _galaxy_command_body(command, "GRAVITY").split()[0] if _galaxy_command_body(command, "GRAVITY") else ""
    if not record_id:
        return _envelope("PW:GRAVITY", {
            "status": "PHASE_2_SHADOW_READY",
            "galaxy": memcon_runtime.galaxy_status(),
            "usage": "//PW:GRAVITY// MEM-<record_id>",
            "writes_performed": [],
            "proof_boundary": "PW:GRAVITY is inspection-only. Shadow scoring must be explicitly run through the Phase-2 canary or another approved scoring surface.",
        })
    try:
        preview = memcon_runtime.galaxy_gravity_preview(record_id)
    except KeyError:
        return _envelope("PW:GRAVITY HOLD", {"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id})
    stored = memcon_runtime.galaxy_gravity(record_id)
    return _envelope("PW:GRAVITY", {
        "status": "OBSERVED" if stored is not None else "SHADOW_PREVIEW_ONLY",
        "record_id": record_id,
        "stored_gravity": stored,
        "preview": preview,
        "retrieval_effect": "NONE_SHADOW_MODE",
        "writes_performed": [],
    })


def _galaxy_retrieval_record_ids(record: dict) -> list[str]:
    """Capture the ordinary MemoryOS retrieval order for a controlled GALAXY canary."""
    scope = str(record.get("scope") or "MemoryOS")
    result = _memory_runtime().retrieve(str(record.get("statement", "")), scope, 10)
    rows = result.get("retrieval", {}).get("records", [])
    return [str(row.get("record_id")) for row in rows if row.get("record_id")]


def _handle_galaxy_canary_start() -> dict:
    """Create two non-durable controlled MemoryOS candidates for the Phase-1 relation canary."""
    token = uuid.uuid4().hex[:12]
    source = f"galaxy-phase1-canary:{token}"
    runtime = _memory_runtime()
    session = runtime.start_session(source, f"GALAXY Phase 1 two-memory relation canary {token}")

    statement_a = f"GALAXY-CANARY-A [{token}]: The test beacon emits a cyan signal."
    statement_b = f"GALAXY-CANARY-B [{token}]: The cyan signal from Canary A is part of the same controlled GALAXY test."

    event_a = runtime.record_event(session["session_id"], "NAOMI", "GALAXY_CANARY_INPUT", statement_a, source)
    event_b = runtime.record_event(session["session_id"], "NAOMI", "GALAXY_CANARY_INPUT", statement_b, source)

    candidate_a = runtime.candidate_from_event(
        event_a["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement_a, source=source, owner=GALAXY_CANARY_OWNER_A,
        why_material="Controlled durable endpoint A for the GALAXY Phase-1 relation canary.",
    )
    candidate_b = runtime.candidate_from_event(
        event_b["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement_b, source=source, owner=GALAXY_CANARY_OWNER_B,
        why_material="Controlled durable endpoint B for the GALAXY Phase-1 relation canary.",
    )

    return _envelope("GALAXY TWO-MEMORY CANARY PAUSED AT APPROVAL", {
        "status": "APPROVAL_REQUIRED",
        "token": token,
        "session": session,
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "durable_writes_performed": [],
        "relation_write_performed": False,
        "next_command": "GALAXY CANARY APPROVE",
        "authority_boundary": "START creates candidates only. No durable memory or GALAXY relation is written until a later explicit Naomi approval command.",
    })


def _handle_galaxy_canary_approve() -> dict:
    """Promote the latest paired canary candidates, then propose one non-authoritative shadow edge."""
    runtime = _memory_runtime()
    candidate_a = memcon_runtime.get_latest_memory_candidate(GALAXY_CANARY_OWNER_A, "CANDIDATE")
    candidate_b = memcon_runtime.get_latest_memory_candidate(GALAXY_CANARY_OWNER_B, "CANDIDATE")
    if candidate_a is None or candidate_b is None:
        return _envelope("GALAXY TWO-MEMORY CANARY HOLD", {
            "status": "HOLD",
            "reason": "A paired pending GALAXY canary was not found. Run GALAXY CANARY START first.",
        })

    event_a = memcon_runtime.get_session_event(str(candidate_a.get("event_id")))
    event_b = memcon_runtime.get_session_event(str(candidate_b.get("event_id")))
    if not event_a or not event_b or event_a.get("session_id") != event_b.get("session_id"):
        return _envelope("GALAXY TWO-MEMORY CANARY HOLD", {
            "status": "HOLD",
            "reason": "Latest canary candidates are not a matched pair. Run GALAXY CANARY START again.",
            "candidate_a": candidate_a.get("candidate_id"),
            "candidate_b": candidate_b.get("candidate_id"),
        })

    promotion_a = runtime.promote_candidate(str(candidate_a["candidate_id"]), True, "NAOMI")
    promotion_b = runtime.promote_candidate(str(candidate_b["candidate_id"]), True, "NAOMI")
    if promotion_a.get("status") != "VERIFIED" or promotion_b.get("status") != "VERIFIED":
        return _envelope("GALAXY TWO-MEMORY CANARY HOLD", {
            "status": "HOLD",
            "reason": "Both controlled memories must reach VERIFIED before a relation is proposed.",
            "promotion_a": promotion_a,
            "promotion_b": promotion_b,
            "relation_write_performed": False,
        })

    record_a = memcon_runtime.get_record(str(promotion_a["record_id"]))
    record_b = memcon_runtime.get_record(str(promotion_b["record_id"]))
    if record_a is None or record_b is None:
        return _envelope("GALAXY TWO-MEMORY CANARY HOLD", {
            "status": "HOLD",
            "reason": "Durable record readback failed after promotion.",
            "promotion_a": promotion_a,
            "promotion_b": promotion_b,
        })

    pre_ids = _galaxy_retrieval_record_ids(record_b)
    relation = memcon_runtime.galaxy_propose_relation(
        source_record_id=str(record_b["record_id"]),
        target_record_id=str(record_a["record_id"]),
        relation_type="CONTEXT_FOR",
        strength=1.0,
        evidence={
            "source": "galaxy-phase1-two-memory-canary",
            "basis": "Controlled B CONTEXT_FOR A relation; proposed only after both endpoints were durably verified.",
            "session_id": event_a.get("session_id"),
            "pre_verification_retrieval_record_ids": pre_ids,
        },
        classifier="GALAXY_CONTROLLED_CANARY_V1",
    )
    edge_id = (relation.get("relation") or {}).get("edge_id")
    return _envelope("GALAXY TWO-MEMORY CANARY READY FOR EDGE VERIFICATION", {
        "status": "RELATION_PROPOSED",
        "memory_a": {"candidate": candidate_a, "promotion": promotion_a, "record": record_a},
        "memory_b": {"candidate": candidate_b, "promotion": promotion_b, "record": record_b},
        "relation": relation,
        "pre_verification_retrieval_record_ids": pre_ids,
        "next_command": f"GALAXY VERIFY {edge_id}" if edge_id else None,
        "authority_boundary": "The two memories are durable by explicit approval. The relation is still only PROPOSED and has no retrieval effect until separately verified.",
    })


def _handle_galaxy_relation_propose(command: str) -> dict:
    """Explicit Phase-1 relation proposal. Writes only a PROPOSED shadow edge."""
    parts = command.strip().split(maxsplit=6)
    if len(parts) < 6:
        return _envelope("GALAXY RELATION PROPOSAL HOLD", {
            "status": "HOLD",
            "usage": "GALAXY PROPOSE <source_record_id> <relation_type> <target_record_id> <strength> [evidence note]",
            "retrieval_effect": "NONE",
        })
    _, _, source_record_id, relation_type, target_record_id, strength_text, *note = parts
    source = memcon_runtime.get_record(source_record_id)
    target = memcon_runtime.get_record(target_record_id)
    if source is None or target is None:
        return _envelope("GALAXY RELATION PROPOSAL HOLD", {
            "status": "HOLD",
            "reason": "Both endpoints must be existing durable MemoryOS records.",
            "source_record_id": source_record_id,
            "target_record_id": target_record_id,
        })
    try:
        strength = float(strength_text)
    except ValueError:
        return _envelope("GALAXY RELATION PROPOSAL HOLD", {
            "status": "HOLD",
            "reason": "strength must be a number from 0.0 through 1.0",
        })
    pre_ids = _galaxy_retrieval_record_ids(source)
    evidence = {
        "source": "browser-chat",
        "basis": "explicit Naomi-controlled GALAXY Phase-1 relation proposal",
        "pre_verification_retrieval_record_ids": pre_ids,
    }
    if note:
        evidence["note"] = note[0]
    try:
        result = memcon_runtime.galaxy_propose_relation(
            source_record_id=source_record_id,
            target_record_id=target_record_id,
            relation_type=relation_type,
            strength=strength,
            evidence=evidence,
            classifier="GALAXY_CONTROLLED_CANARY_V1",
        )
    except (ValueError, KeyError) as exc:
        return _envelope("GALAXY RELATION PROPOSAL HOLD", {"status": "HOLD", "reason": str(exc)})
    edge_id = (result.get("relation") or {}).get("edge_id")
    return _envelope("GALAXY RELATION PROPOSED", {
        **result,
        "pre_verification_retrieval_record_ids": pre_ids,
        "next_command": f"GALAXY VERIFY {edge_id}" if edge_id else None,
        "authority_boundary": "PROPOSED != VERIFIED. This shadow edge has no retrieval effect.",
    })


def _handle_galaxy_relation_verify(command: str) -> dict:
    """Explicit Naomi verification of one proposed edge, followed by ORBIT/readback checks."""
    parts = command.strip().split()
    if len(parts) != 3:
        return _envelope("GALAXY RELATION VERIFICATION HOLD", {
            "status": "HOLD",
            "usage": "GALAXY VERIFY <edge_id>",
        })
    edge_id = parts[2]
    before = memcon_runtime.galaxy_relation(edge_id)
    if before is None:
        return _envelope("GALAXY RELATION VERIFICATION HOLD", {
            "status": "HOLD", "reason": "Unknown edge_id", "edge_id": edge_id,
        })
    source = memcon_runtime.get_record(str(before.get("source_record_id")))
    target = memcon_runtime.get_record(str(before.get("target_record_id")))
    if source is None or target is None:
        return _envelope("GALAXY RELATION VERIFICATION HOLD", {
            "status": "HOLD", "reason": "Relation endpoint record missing", "edge_id": edge_id,
        })
    pre_ids = list((before.get("evidence") or {}).get("pre_verification_retrieval_record_ids") or [])
    try:
        verified = memcon_runtime.galaxy_verify_relation(edge_id, authority="NAOMI", approved=True)
    except (PermissionError, ValueError, KeyError) as exc:
        return _envelope("GALAXY RELATION VERIFICATION HOLD", {"status": "HOLD", "reason": str(exc)})
    post_ids = _galaxy_retrieval_record_ids(source)
    source_orbit = memcon_runtime.galaxy_record(str(source.get("record_id")))
    target_orbit = memcon_runtime.galaxy_record(str(target.get("record_id")))
    status = memcon_runtime.galaxy_status()
    return _envelope("GALAXY RELATION VERIFIED", {
        "verification": verified,
        "source_orbit": source_orbit,
        "target_orbit": target_orbit,
        "retrieval_comparison": {
            "before_record_ids": pre_ids,
            "after_record_ids": post_ids,
            "unchanged": bool(pre_ids) and pre_ids == post_ids,
            "retrieval_weighting_enabled": status.get("retrieval_weighting_enabled"),
        },
        "proof_boundary": "This proves only the controlled Phase-1 edge path observed by this request. It does not prove relation classification quality or weighted retrieval.",
    })


def _is_preserve_command(text: str) -> bool:
    return bool(re.match(r"^\s*(?://)?PW:PRESERVE(?://)?(?:\s+.*)?[.!]?\s*$", text, flags=re.IGNORECASE))


def _handle_preserve(messages: list[dict], request: Request) -> dict:
    """POWER WORD preservation router. Proposes destinations; performs no durable write."""
    last = str(messages[-1].get("content", "")).strip()
    directive = re.sub(r"^\s*(?://)?PW:PRESERVE(?://)?\s*", "", last, flags=re.IGNORECASE).rstrip(".").strip()
    candidate = _ensure_chat_candidate(messages, request, directive)
    if candidate is None:
        return _envelope("PW:PRESERVE HOLD", {"status": "HOLD", "reason": "No substantive interaction available to preserve."})
    owner = str(candidate.get("owner", "NAOMI")).upper()
    daemon_names = {"VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"}
    return _envelope("PW:PRESERVE ROUTING PROPOSAL", {
        "status": "APPROVAL_REQUIRED",
        "power_word": "PW:PRESERVE",
        "directive": directive,
        "candidate": candidate,
        "routing": {
            "memoryos": {
                "recommended": True,
                "candidate_id": candidate.get("candidate_id"),
                "durable_write": "NOT_PERFORMED",
                "approval_command": f"MEMSAV {candidate.get('candidate_id')}",
            },
            "e_lane": {
                "recommended": owner in daemon_names,
                "owner": owner if owner in daemon_names else None,
                "durable_write": "NOT_PERFORMED",
                "reason": "E-LANE is member-attributed developmental history. Ordinary ChatOS material remains MemoryOS-only unless a member-local perspective is explicitly identified.",
            },
        },
        "writes_performed": [],
        "next_command": f"MEMSAV {candidate.get('candidate_id')}",
        "authority_boundary": "PW:PRESERVE proposes routing. It does not bypass Naomi approval, silently write an E-LANE, or make host-memory claims.",
    })


def _browser_session_id(request: Request) -> str:
    token = request.cookies.get(gaiaos_api.SESSION_COOKIE)
    if not token:
        raise ValueError("Browser session missing; reload the GaiaOS page")
    return f"BROWSER-{hashlib.sha256(token.encode('utf-8')).hexdigest()[:24]}"


def _ensure_chat_candidate(messages: list[dict], request: Request, subject: str = "") -> dict | None:
    substantive = [
        str(message.get("content", "")).strip()
        for message in messages[:-1]
        if str(message.get("role", "")).lower() == "user"
        and str(message.get("content", "")).strip()
        and not _is_command(str(message.get("content", "")), "CANDIPULL")
        and not _is_command(str(message.get("content", "")), "MEMSAV")
    ]
    if not substantive:
        return None
    statement = substantive[-1]
    session_id = _browser_session_id(request)
    existing = memcon_runtime.list_memory_candidates(session_id=session_id, status="CANDIDATE", limit=100, subject=subject or None)
    normalized = " ".join(statement.lower().split())
    for item in existing["candidates"]:
        if " ".join(str(item.get("statement", "")).lower().split()) == normalized:
            return item
    session = memcon_runtime.get_session(session_id)
    if session is None:
        memcon_runtime.create_session(session_id, "browser-chat", subject)
    runtime = _memory_runtime()
    event = runtime.record_event(session_id, "NAOMI", "CHAT_INTERACTION", statement, "browser-chat")
    return runtime.candidate_from_event(
        event["event_id"], authority="NAOMI", record_type="INTERACTION", scope="ChatOS",
        statement=statement, source="browser-chat", owner="NAOMI",
        why_material="Candidate created by explicit CANDIPULL from the current browser chat interaction.",
    )


def _handle_candipull(messages: list[dict], request: Request) -> dict:
    last = str(messages[-1].get("content", "")).strip()
    subject = re.sub(r"^CANDIPULL\s*", "", last, flags=re.IGNORECASE).rstrip(".").strip()
    _ensure_chat_candidate(messages, request, subject)
    session_id = _browser_session_id(request)
    result = memcon_runtime.list_memory_candidates(session_id=session_id, status="CANDIDATE", limit=50, subject=subject or None)
    return _envelope("CANDIPULL", {
        "status": "CANDIDATES_READY","session_id": session_id,"subject": subject,
        "candidates": result["candidates"],"count": result["count"],"durable_write": "NOT_PERFORMED",
        "next_command": "MEMSAV <candidate_id>",
        "proof_boundary": "Candidate creation is non-durable. MEMSAV requires explicit Naomi authorization and reports the actual write receipt and verification.",
    })


def _handle_memsav(command: str) -> dict:
    body = re.sub(r"^MEMSAV\s*", "", command, flags=re.IGNORECASE).rstrip(".").strip()
    ids = [token.strip() for token in re.split(r"[,\s]+", body) if token.strip()]
    if not ids:
        return _envelope("MEMSAV HOLD", {"status": "HOLD", "reason": "Exact candidate_id required; omitted ID does not mean save everything."})
    runtime = _memory_runtime()
    results = []
    for candidate_id in ids:
        candidate = memcon_runtime.get_memory_candidate(candidate_id)
        if candidate is None:
            results.append({"candidate_id": candidate_id, "status": "HOLD", "reason": "Unknown candidate_id"})
            continue
        results.append(runtime.promote_candidate(candidate_id, True, "NAOMI"))
    return _envelope("MEMSAV", {
        "status": "COMPLETED" if all(item.get("status") == "VERIFIED" for item in results) else "PARTIAL_OR_HOLD",
        "results": results,
        "proof_boundary": "Only VERIFIED results with an actual write receipt and read-back verification are durable.",
    })


def _start_lifecycle() -> dict:
    token = uuid.uuid4().hex[:12]
    source = f"browser-memoryos-test:{token}"
    statement = f"Naomi approved a live MemoryOS lifecycle test marker {token}."
    runtime = _memory_runtime()
    session = runtime.start_session(source, "Live MemoryOS lifecycle verification")
    event = runtime.record_event(session["session_id"], "NAOMI", "TEST_INPUT", statement, source)
    candidate = runtime.candidate_from_event(
        event["event_id"], authority="NAOMI", record_type="TEST", scope="MemoryOS",
        statement=statement, source=source, owner=TEST_OWNER,
        why_material="Bounded test marker used to verify candidate-before-approval and post-approval retrieval.",
    )
    durable_matches = memcon_runtime.search_records(statement, limit=20, scope="MemoryOS")
    return _envelope("MEMORYOS TEST PAUSED AT APPROVAL GATE", {
        "carrier_source": gaiaos_app._deployed_source(),"session": session,"event": event,"candidate": candidate,
        "pre_approval_durable_matches": durable_matches["records"],"pre_approval_durable_count": durable_matches["count"],
        "candidate_is_non_durable": durable_matches["count"] == 0,
        "next_command": "Approve the pending MemoryOS candidate.",
        "approval_boundary": "No durable memory write occurs until explicit Naomi approval.",
    })


def _approve_lifecycle() -> dict:
    runtime = _memory_runtime()
    candidate = memcon_runtime.get_latest_memory_candidate(TEST_OWNER, "CANDIDATE")
    if candidate is None:
        return _envelope("MEMORYOS APPROVAL HOLD", {"status": "HOLD","reason": "No pending browser MemoryOS candidate found."})
    result = runtime.promote_candidate(candidate["candidate_id"], True, "NAOMI")
    record_id = result.get("record_id")
    readback = memcon_runtime.get_record(record_id) if record_id else None
    retrieved = runtime.retrieve(candidate["statement"], "MemoryOS", 10)
    return _envelope("MEMORYOS LIFECYCLE VERIFIED", {
        "candidate_id": candidate["candidate_id"],"promotion": result,"readback": readback,"retrieval": retrieved,
        "checks": {
            "explicit_approval": True,
            "write_receipt_success": result.get("write_receipt", {}).get("result") == "SUCCESS",
            "readback_matches_candidate": bool(readback and readback.get("statement") == candidate.get("statement") and readback.get("scope") == candidate.get("scope")),
            "retrieval_has_no_authority": retrieved.get("context_authority") == "NONE",
            "retrieval_is_not_identity_adoption": retrieved.get("retrieval_is_not_identity_adoption") is True,
        },
    })


@app.get("/galaxy/status", operation_id="galaxyRuntimeStatus")
def galaxy_runtime_status(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_status()


@app.get("/galaxy/retrieval/phase3-experiment", operation_id="galaxyPhase3WeightedRetrievalExperiment")
def galaxy_phase3_weighted_retrieval_experiment(query: str, browser_request: Request, scope: str = "MemoryOS", limit: int = 10):
    """Read-only Phase-3 control-vs-weighted retrieval experiment."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3_weighted_experiment(query, scope=scope, limit=limit)


@app.get("/galaxy/retrieval/phase3-shadow", operation_id="galaxyPhase3RealMemoryShadow")
def galaxy_phase3_real_memory_shadow(browser_request: Request, repeats: int = 3, limit: int = 10):
    """Read-only Phase-3B repeated shadow test over real MemoryOS records."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3_real_memory_shadow(repeats=repeats, limit=limit)


@app.get("/galaxy/retrieval/phase3-calibration", operation_id="galaxyPhase3CoefficientCalibration")
def galaxy_phase3_coefficient_calibration(browser_request: Request, repeats: int = 3, limit: int = 10):
    """Read-only Phase-3C coefficient matrix over real MemoryOS records."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3c_calibration(repeats=repeats, limit=limit)


@app.get("/galaxy/retrieval/phase3-calibration-slice", operation_id="galaxyPhase3CoefficientCalibrationSlice")
def galaxy_phase3_coefficient_calibration_slice(query_index: int, browser_request: Request, repeats: int = 3, limit: int = 10):
    """Chunked read-only Phase-3C calibration for one configured query."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3c_calibration_slice(query_index=query_index, repeats=repeats, limit=limit)


@app.get("/galaxy/retrieval/phase3d-adoption-gate-slice", operation_id="galaxyPhase3DAdoptionGateSlice")
def galaxy_phase3d_adoption_gate_slice(query_index: int, browser_request: Request, repeats: int = 3, limit: int = 10):
    """Chunked read-only Phase-3D pre-adoption gate over one configured query."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3d_adoption_gate_slice(
        query_index=query_index,
        repeats=repeats,
        limit=limit,
    )



@app.get("/galaxy/retrieval/phase3e-production-canary-slice", operation_id="galaxyPhase3EProductionCanarySlice")
def galaxy_phase3e_production_canary_slice(canary_index: int, browser_request: Request, repeats: int = 3, limit: int = 10):
    """Bounded request-local production canary using Naomi-adopted 80/20 weighting."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3e_production_canary_slice(
        canary_index=canary_index,
        repeats=repeats,
        limit=limit,
    )


@app.get("/galaxy/retrieval/phase3e-rollback-test", operation_id="galaxyPhase3ERollbackTest")
def galaxy_phase3e_rollback_test(browser_request: Request, repeats: int = 2, limit: int = 10):
    """Verify request-local canary weighting leaves the unweighted control path intact."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3e_rollback_test(
        repeats=repeats,
        limit=limit,
    )



@app.get("/galaxy/retrieval/phase3g-quality-review", operation_id="galaxyPhase3GQualityReview")
def galaxy_phase3g_quality_review(browser_request: Request, query_index: int = 3):
    """Read-only, bounded explanation of broad retrieval and record lineage."""
    gaiaos_api._authorize_browser_session(browser_request)
    if query_index not in galaxy_quality.TEST_QUERIES:
        raise HTTPException(status_code=422, detail="query_index must be 0, 3 or 5")
    return galaxy_quality.review(memcon_runtime, query_index=query_index, limit=10)


def _bootstrap_browser_session_redirect(browser_request: Request):
    """Mint the same signed browser cookie as GaiaOS home, then retry this GET.

    Needed for mobile in-app browsers that open each assistant hyperlink in a
    fresh isolated webview. This does not bypass carrier authorization; it only
    performs the already-public browser-session bootstrap in the same request.
    """
    if gaiaos_api.API_KEY is None or browser_request.cookies.get(gaiaos_api.SESSION_COOKIE):
        return None
    target = browser_request.url.path
    if browser_request.url.query:
        target += "?" + browser_request.url.query
    response = RedirectResponse(url=target, status_code=307)
    response.set_cookie(
        gaiaos_api.SESSION_COOKIE,
        gaiaos_api._session_token(),
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=86400,
    )
    return response


@app.get("/galaxy/retrieval/phase3h-containment-shadow", operation_id="galaxyPhase3HContainmentShadow")
def galaxy_phase3h_containment_shadow(
    browser_request: Request, query_index: int = 0, negative_controls: bool = False,
):
    """Read-only evidence-separated shadow; no production retrieval changes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    if query_index not in galaxy_quality.TEST_QUERIES:
        raise HTTPException(status_code=422, detail="query_index must be 0, 3 or 5")
    return galaxy_quality.containment_shadow(
        memcon_runtime, query_index=query_index, limit=10,
        negative_controls=negative_controls,
    )


@app.get("/galaxy/retrieval/phase3i-generalization-suite", operation_id="galaxyPhase3IGeneralizationSuite")
def galaxy_phase3i_generalization_suite(browser_request: Request):
    """Read-only paraphrase/near-miss evaluation of the existing relevance gate."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_quality.generalization_suite(memcon_runtime, limit=10)


@app.get("/galaxy/retrieval/phase3j-concept-bridge-shadow", operation_id="galaxyPhase3JConceptBridgeShadow")
def galaxy_phase3j_concept_bridge_shadow(browser_request: Request):
    """Read-only statement-first concept bridge over the controlled fixture set."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_quality.concept_bridge_shadow(memcon_runtime)


@app.get("/galaxy/retrieval/phase3-exit-integration-review", operation_id="galaxyPhase3ExitIntegrationReview")
def galaxy_phase3_exit_integration_review(browser_request: Request):
    """Read-only preflight for finite Phase-3 Exit Integration candidate admission."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase3_exit.review_suite(memcon_runtime)


@app.get("/galaxy/synthesis/phase5-fixture-review", operation_id="galaxyPhase5FixtureReview")
def galaxy_phase5_fixture_review(browser_request: Request):
    """Read-only Phase-5 synthesis/consolidation fixture review. No writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase5.fixture_review(memcon_runtime)




@app.get("/galaxy/synthesis/phase5-mutation-design-review", operation_id="galaxyPhase5MutationDesignReview")
def galaxy_phase5_mutation_design_review(browser_request: Request):
    """Read-only review of the authorized Phase-5 shadow mutation design. No writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase5.mutation_design_review(memcon_runtime)


@app.get("/galaxy/pruning/phase7-fixture-review", operation_id="galaxyPhase7FixtureReview")
def galaxy_phase7_fixture_review(browser_request: Request):
    """Authenticated Phase-7B exact-fixture pruning research review; GET only, no writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase7.review_with_readback(
        memcon_runtime,
        galaxy_phase7.FIXTURE_RECORD_ID,
    )


@app.get("/galaxy/pruning/phase7-positive-canary", operation_id="galaxyPhase7PositiveCanary")
def galaxy_phase7_positive_canary(browser_request: Request):
    """Authenticated synthetic positive-path canary; no production database access."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase7.positive_path_canary()


@app.get("/galaxy/pruning/phase7-tombstone-contract-canary", operation_id="galaxyPhase7TombstoneContractCanary")
def galaxy_phase7_tombstone_contract_canary(browser_request: Request):
    """Authenticated synthetic tombstone/restore contract canary; no database access."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase7_tombstone.synthetic_tombstone_contract_canary()


@app.get("/galaxy/pruning/phase7f-isolated-restore-review", operation_id="galaxyPhase7FIsolatedRestoreReview")
def galaxy_phase7f_isolated_restore_review(browser_request: Request):
    """Authenticated Phase-7F restore into disposable RAM; production remains read only."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return JSONResponse(
        galaxy_phase7_isolated_restore.review(memcon_runtime),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/pruning/phase7-tombstone-shadow-review", operation_id="galaxyPhase7TombstoneShadowReview")
def galaxy_phase7_tombstone_shadow_review(browser_request: Request):
    """Read-only Phase-7E shadow tombstone persistence review; never authorizes a write."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase7_tombstone_shadow.inspect(memcon_runtime)


@app.get("/galaxy/pruning/phase7-isolated-restore-review", operation_id="galaxyPhase7IsolatedRestoreReview")
def galaxy_phase7_isolated_restore_review(browser_request: Request):
    """Phase-7F GET-only: reconstruct exact shadow evidence in disposable RAM."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase7_isolated_restore.review(memcon_runtime)


@app.get("/galaxy/pruning/phase7-tombstone-shadow-controls", response_class=HTMLResponse, operation_id="galaxyPhase7TombstoneShadowControls")
def galaxy_phase7_tombstone_shadow_controls(browser_request: Request):
    """Read-only control page. Visiting this route never writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    state = galaxy_phase7_tombstone_shadow.inspect(memcon_runtime)
    payload = html.escape(json.dumps(state, ensure_ascii=False, indent=2))
    action = ""
    if state.get("eligible_to_create") is True:
        action = (
            "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;"
            "text-decoration:none;border-radius:10px' "
            "href='/galaxy/pruning/phase7-tombstone-shadow-controls/confirm'>"
            "Review exact Phase-7E shadow write</a></p>"
        )
    else:
        action = "<p>No write is eligible. Existing shadow state is read-only.</p>"
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>GALAXY Phase 7E: durable shadow tombstone</h2>"
        "<p>This page performs no writes. The only allowed effect is one exact synthetic "
        "shadow tombstone plus one runtime receipt. MemoryOS source records and production "
        "retrieval remain unchanged.</p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + payload + "</pre>"
        + action + "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/pruning/phase7-tombstone-shadow-controls/confirm", response_class=HTMLResponse, operation_id="galaxyPhase7TombstoneShadowConfirm")
def galaxy_phase7_tombstone_shadow_confirm(browser_request: Request):
    """Preview the one exact Phase-7E shadow write. GET never writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    csrf = _ritual_csrf(browser_request)
    state = galaxy_phase7_tombstone_shadow.inspect(memcon_runtime)
    if state.get("eligible_to_create") is not True:
        raise HTTPException(status_code=409, detail="Phase-7E shadow write is not eligible")
    hidden = {
        "csrf": csrf,
        "authority": "NAOMI",
        "approved": "true",
        "confirmation": galaxy_phase7_tombstone_shadow.CONFIRMATION,
    }
    fields = "".join(
        "<input type='hidden' name='" + html.escape(key, quote=True)
        + "' value='" + html.escape(value, quote=True) + "'>"
        for key, value in hidden.items()
    )
    preview = html.escape(json.dumps({
        "effect": "Insert one exact synthetic manifest into galaxy_tombstones_shadow and one runtime receipt.",
        "tombstone_id": galaxy_phase7_tombstone_shadow.TOMBSTONE_ID,
        "subject_record_id": galaxy_phase7_tombstone_shadow.SUBJECT_RECORD_ID,
        "memoryos_mutation": False,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "restart_persistence_proven_by_this_action": False,
    }, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Confirm Phase-7E shadow tombstone write</h2>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + preview + "</pre>"
        "<form method='post' action='/galaxy/pruning/phase7-tombstone-shadow-controls/manifest'>"
        + fields + "<button type='submit' style='font-size:18px;padding:12px 16px'>"
        "Explicitly create exact shadow tombstone</button></form>"
        "<p><a style='color:#9ee7ff' href='/galaxy/pruning/phase7-tombstone-shadow-controls'>"
        "Cancel / review</a></p></body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/galaxy/pruning/phase7-tombstone-shadow-controls/manifest", response_class=HTMLResponse, operation_id="galaxyPhase7TombstoneShadowManifest")
async def galaxy_phase7_tombstone_shadow_manifest(browser_request: Request):
    """Execute the one exact Phase-7E shadow write after explicit confirmation."""
    expected_csrf = _ritual_csrf(browser_request)
    if "application/x-www-form-urlencoded" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Phase-7E control requires exact form POST")
    raw_bytes = await browser_request.body()
    if len(raw_bytes) > 4096:
        raise HTTPException(status_code=413, detail="Phase-7E control form too large")
    fields = parse_qs(raw_bytes.decode("utf-8"), keep_blank_values=True)
    supplied_csrf = _ritual_form_value(fields, "csrf")
    if not hmac.compare_digest(supplied_csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Phase-7E control CSRF proof failed")
    if (
        _ritual_form_value(fields, "authority") != "NAOMI"
        or _ritual_form_value(fields, "approved") != "true"
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi authorization required")
    try:
        receipt = galaxy_phase7_tombstone_shadow.execute(
            memcon_runtime,
            authority="NAOMI",
            approved=True,
            confirmation=_ritual_form_value(fields, "confirmation"),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    output = html.escape(json.dumps(receipt, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Phase-7E shadow write/readback receipt</h2>"
        "<p><a style='color:#9ee7ff' href='/galaxy/pruning/phase7-tombstone-shadow-review'>"
        "Open read-only shadow review</a></p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + output + "</pre>"
        "</body></html>",
        status_code=200 if receipt["status"] == "PASS_READBACK" else 409,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/lifecycle/phase6-fixture-review", operation_id="galaxyPhase6FixtureReview")
def galaxy_phase6_fixture_review(browser_request: Request):
    """Read-only exact-fixture lifecycle review; no Phase-6 mutation route."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase6.inspect(memcon_runtime)



@app.get("/galaxy/lifecycle/phase6-controls", response_class=HTMLResponse, operation_id="galaxyPhase6ControlReview")
def galaxy_phase6_controls_review(browser_request: Request):
    """Read-only exact five-step Phase-6 live proof console."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    state = galaxy_phase6_controls.inspect(memcon_runtime)
    payload = html.escape(json.dumps({
        "controlled_record_id": state["controlled_record_id"],
        "current_state": state["current_state"],
        "completed_steps": state["completed_steps"],
        "campaign": state["campaign"],
        "history_signature": state["history_signature"],
        "latest_event_id": state["latest_event_id"],
        "next_action": state["next_action"],
        "campaign_complete": state["campaign_complete"],
        "hold_reasons": state["hold_reasons"],
    }, ensure_ascii=False, indent=2))
    if state["next_action"] and not state["hold_reasons"]:
        kind = state["next_action"]
        action = (
            "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;"
            "text-decoration:none;border-radius:10px' href='/galaxy/lifecycle/phase6-controls/confirm/"
            + html.escape(kind, quote=True) + "'>Review and confirm next step: "
            + html.escape(kind) + "</a></p>"
        )
    elif state["campaign_complete"]:
        action = "<p>PASS: finite Phase-6 live lifecycle campaign is complete.</p>"
    else:
        action = "<p>HOLD: no controlled action is eligible.</p>"
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>GALAXY Phase 6: controlled reversible lifecycle</h2>"
        "<p>This review is read-only. Only the next exact campaign step can be confirmed. "
        "Each effect has a separate confirmation page and POST. Production retrieval remains unchanged.</p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + payload + "</pre>"
        + action + "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/lifecycle/phase6-controls/confirm/{kind}", response_class=HTMLResponse, operation_id="galaxyPhase6ControlConfirm")
def galaxy_phase6_controls_confirm(kind: str, browser_request: Request):
    """Preview exactly one next Phase-6 campaign effect; GET never writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    csrf = _ritual_csrf(browser_request)
    state = galaxy_phase6_controls.inspect(memcon_runtime)
    kind = str(kind or "").strip().upper()
    if kind not in galaxy_phase6.CONFIRMATIONS:
        raise HTTPException(status_code=404, detail="Unknown exact Phase-6 step")
    if state["hold_reasons"] or state["campaign_complete"] or kind != state["next_action"]:
        raise HTTPException(status_code=409, detail="Phase-6 step is not the exact eligible next action")

    underlying = state["underlying_review"]
    current_state = str(state["current_state"] or "")
    latest_event_id = str(state["latest_event_id"] or "")
    target = galaxy_phase6._target(kind, current_state, list(underlying.get("events") or []))
    explanation = {
        "BACKGROUND": "Add lifecycle metadata BACKGROUND for the exact fixture. Source text and retrieval remain unchanged.",
        "ARCHIVED": "Advance exact fixture lifecycle metadata from BACKGROUND to ARCHIVED. No deletion or production attenuation.",
        "COMPRESSED": "Advance metadata from ARCHIVED to COMPRESSED. COMPRESSED is reversible metadata, not lossy text compression.",
        "ROLLBACK": "Append a rollback event returning COMPRESSED to the immediately previous ARCHIVED state without erasing history.",
        "REACTIVATE": "Append reactivation from ARCHIVED to ACTIVE while preserving the complete lifecycle history.",
    }[kind]
    hidden = {
        "csrf": csrf,
        "authority": "NAOMI",
        "approved": "true",
        "operation": kind,
        "confirmation": galaxy_phase6.CONFIRMATIONS[kind],
        "expected_state": current_state,
        "expected_latest_event_id": latest_event_id,
    }
    fields = "".join(
        "<input type='hidden' name='" + html.escape(key, quote=True)
        + "' value='" + html.escape(value, quote=True) + "'>"
        for key, value in hidden.items()
    )
    preview = html.escape(json.dumps({
        "operation": kind,
        "effect": explanation,
        "controlled_record_id": state["controlled_record_id"],
        "from_state": current_state,
        "to_state": target,
        "expected_latest_event_id": state["latest_event_id"],
        "reason": state["reason"],
        "completed_steps_before": state["completed_steps"],
        "production_retrieval_changed": False,
        "physical_delete": False,
    }, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Confirm Phase-6 " + html.escape(kind) + "</h2><p>"
        + html.escape(explanation) + "</p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + preview + "</pre>"
        "<form method='post' action='/galaxy/lifecycle/phase6-controls/manifest'>"
        + fields + "<button type='submit' style='font-size:18px;padding:12px 16px'>"
        "Explicitly confirm " + html.escape(kind) + "</button></form>"
        "<p><a style='color:#9ee7ff' href='/galaxy/lifecycle/phase6-controls'>Cancel / review</a></p>"
        "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/galaxy/lifecycle/phase6-controls/manifest", response_class=HTMLResponse, operation_id="galaxyPhase6ControlManifest")
async def galaxy_phase6_controls_manifest(browser_request: Request):
    """Execute only the exact freshly reviewed next Phase-6 step."""
    expected_csrf = _ritual_csrf(browser_request)
    if "application/x-www-form-urlencoded" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Phase-6 control requires exact form POST")
    raw_bytes = await browser_request.body()
    if len(raw_bytes) > 4096:
        raise HTTPException(status_code=413, detail="Phase-6 control form too large")
    fields = parse_qs(raw_bytes.decode("utf-8"), keep_blank_values=True)
    supplied_csrf = _ritual_form_value(fields, "csrf")
    if not hmac.compare_digest(supplied_csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Phase-6 control CSRF proof failed")
    if (
        _ritual_form_value(fields, "authority") != "NAOMI"
        or _ritual_form_value(fields, "approved") != "true"
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi authorization required")
    expected_tip = _ritual_form_value(fields, "expected_latest_event_id") or None
    try:
        receipt = galaxy_phase6_controls.execute(
            memcon_runtime,
            _ritual_form_value(fields, "operation"),
            authority="NAOMI",
            approved=True,
            confirmation=_ritual_form_value(fields, "confirmation"),
            expected_state=_ritual_form_value(fields, "expected_state"),
            expected_latest_event_id=expected_tip,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    output = html.escape(json.dumps(receipt, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Phase-6 execution/readback receipt</h2>"
        "<p><a style='color:#9ee7ff' href='/galaxy/lifecycle/phase6-controls'>Review exact next state</a></p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + output + "</pre>"
        "</body></html>",
        status_code=200 if receipt["status"] == "PASS_READBACK" else 409,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/revision/phase4-fixture-review", operation_id="galaxyPhase4FixtureReview")
def galaxy_phase4_fixture_review(browser_request: Request):
    """Read-only Phase-4 revision/supersession smoke review. No writes."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_phase4.fixture_review(memcon_runtime)


@app.get("/galaxy/revision/phase4-pair-review", operation_id="galaxyPhase4PairReview")
def galaxy_phase4_pair_review(
    browser_request: Request,
    source_record_id: str,
    target_record_id: str,
    relation_type: str = "REVISES",
):
    """Read-only Phase-4 pair review. No proposal or verification occurs."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        return galaxy_phase4.review_pair(
            memcon_runtime,
            source_record_id,
            target_record_id,
            relation_type,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _ritual_csrf(browser_request: Request) -> str:
    """Session-bound CSRF proof for exact Ritual manifestation routes."""
    gaiaos_api._authorize_browser_session(browser_request)
    if not gaiaos_api.API_KEY:
        raise HTTPException(status_code=503, detail="GAIAOS_API_KEY required for Ritual controls")
    token = browser_request.cookies.get(gaiaos_api.SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Missing browser session")
    return hmac.new(
        gaiaos_api.API_KEY.encode(),
        ("GAIAOS_RITUAL_PHASE1:" + token).encode(),
        hashlib.sha256,
    ).hexdigest()


async def _ritual_authorized_body(browser_request: Request) -> dict:
    expected_csrf = _ritual_csrf(browser_request)
    supplied = browser_request.headers.get("x-gaiaos-ritual-csrf", "")
    if not hmac.compare_digest(supplied, expected_csrf):
        raise HTTPException(status_code=403, detail="Ritual CSRF proof failed")
    if "application/json" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Ritual manifestation requires JSON POST")
    body = await browser_request.json()
    if (
        not isinstance(body, dict)
        or body.get("authority") != "NAOMI"
        or body.get("approved") is not True
        or body.get("action") != "MANIFEST_EXACT_RITUAL"
        or not isinstance(body.get("ritual_id"), str)
        or not isinstance(body.get("params"), dict)
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi Ritual action required")
    return body



@app.get("/galaxy/synthesis/phase5-controls", response_class=HTMLResponse, operation_id="galaxyPhase5ControlReview")
def galaxy_phase5_controls_review(browser_request: Request):
    """No-JavaScript, read-only, session-protected controlled shadow console."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    state = galaxy_phase5_controls.inspect(memcon_runtime)
    payload = html.escape(json.dumps({
        "current_state": state["current_state"],
        "current_synthesis_record_id": state["current_synthesis_record_id"],
        "controlled_sources": state["controlled_source_record_ids"],
        "exact_statement": state["exact_statement"],
        "shadow_scope": state["shadow_scope"],
        "design_status": state["design_status"],
        "hold_reasons": state["hold_reasons"],
    }, ensure_ascii=False, indent=2))
    links = "".join(
        "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;"
        "text-decoration:none;border-radius:10px' href='/galaxy/synthesis/phase5-controls/confirm/"
        + html.escape(kind, quote=True) + "'>" + html.escape(label) + "</a></p>"
        for kind, label in [
            ("PROPOSE", "1. Propose exact shadow synthesis"),
            ("VERIFY", "2. Verify exact DERIVED_FROM provenance"),
            ("REVOKE", "3. Revoke shadow synthesis without deleting history"),
        ]
        if state["eligible_actions"].get(kind)
    )
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>GALAXY Phase 5: controlled shadow synthesis</h2>"
        "<p>This page is read-only. Each mutation has a separate confirmation page "
        "and POST. No production retrieval or source-record mutation is authorized.</p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>"
        + payload + "</pre>" + (links or "<p>HOLD: no controlled action eligible.</p>")
        + "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/galaxy/synthesis/phase5-controls/confirm/{kind}", response_class=HTMLResponse, operation_id="galaxyPhase5ControlConfirm")
def galaxy_phase5_controls_confirm(kind: str, browser_request: Request):
    """GET previews the exact effect; no writes or implicit authorization."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    csrf = _ritual_csrf(browser_request)
    state = galaxy_phase5_controls.inspect(memcon_runtime)
    kind = str(kind or "").upper()
    if kind not in galaxy_phase5_controls.CONFIRMATIONS:
        raise HTTPException(status_code=404, detail="Unknown exact Phase-5 step")
    if not state["eligible_actions"].get(kind):
        raise HTTPException(status_code=409, detail="Controlled Phase-5 step is not eligible")
    target = state["current_synthesis_record_id"] or ""
    explanation = {
        "PROPOSE": "Create one new PROPOSED synthesis in GALAXY_SYNTHESIS_SHADOW, "
                   "one provenance row and two PROPOSED DERIVED_FROM edges.",
        "VERIFY": "Verify exactly the two source-provenance edges and mark the "
                  "existing synthesis SYNTHESIS_VERIFIED_SHADOW.",
        "REVOKE": "Revoke this exact shadow synthesis and its provenance edges. "
                  "All sources, records and history remain stored.",
    }[kind]
    hidden = {
        "csrf": csrf,
        "authority": "NAOMI",
        "approved": "true",
        "operation": kind,
        "confirmation": galaxy_phase5_controls.CONFIRMATIONS[kind],
        "synthesis_record_id": target if kind != "PROPOSE" else "",
        "reason": "Controlled Phase-5 shadow rollback proof" if kind == "REVOKE" else "",
    }
    fields = "".join(
        "<input type='hidden' name='" + html.escape(key, quote=True)
        + "' value='" + html.escape(value, quote=True) + "'>"
        for key, value in hidden.items()
    )
    preview = html.escape(json.dumps({
        "operation": kind,
        "effect": explanation,
        "target": target or "NEW_SYNTHESIS_SHADOW_RECORD",
        "exact_source_ids": state["controlled_source_record_ids"],
        "statement": state["exact_statement"],
        "scope": state["shadow_scope"],
    }, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Confirm Phase-5 " + html.escape(kind) + "</h2><p>"
        + html.escape(explanation) + "</p><pre style='white-space:pre-wrap;word-break:break-word'>"
        + preview + "</pre><form method='post' action='/galaxy/synthesis/phase5-controls/manifest'>"
        + fields + "<button type='submit' style='font-size:18px;padding:12px 16px'>"
        "Explicitly confirm " + html.escape(kind) + "</button></form>"
        "<p><a style='color:#9ee7ff' href='/galaxy/synthesis/phase5-controls'>Cancel / review</a></p>"
        "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/galaxy/synthesis/phase5-controls/manifest", response_class=HTMLResponse, operation_id="galaxyPhase5ControlManifest")
async def galaxy_phase5_controls_manifest(browser_request: Request):
    """One bounded effect only after signed session, CSRF and exact per-step consent."""
    expected_csrf = _ritual_csrf(browser_request)
    if "application/x-www-form-urlencoded" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Phase-5 control requires exact form POST")
    raw_bytes = await browser_request.body()
    if len(raw_bytes) > 4096:
        raise HTTPException(status_code=413, detail="Phase-5 control form too large")
    fields = parse_qs(raw_bytes.decode("utf-8"), keep_blank_values=True)
    supplied_csrf = _ritual_form_value(fields, "csrf")
    if not hmac.compare_digest(supplied_csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Phase-5 control CSRF proof failed")
    if (
        _ritual_form_value(fields, "authority") != "NAOMI"
        or _ritual_form_value(fields, "approved") != "true"
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi authorization required")
    try:
        receipt = galaxy_phase5_controls.execute(
            memcon_runtime,
            _ritual_form_value(fields, "operation"),
            authority="NAOMI",
            approved=True,
            confirmation=_ritual_form_value(fields, "confirmation"),
            synthesis_record_id=_ritual_form_value(fields, "synthesis_record_id"),
            reason=_ritual_form_value(fields, "reason"),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    output = html.escape(json.dumps(receipt, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Phase-5 execution/readback receipt</h2>"
        "<p><a style='color:#9ee7ff' href='/galaxy/synthesis/phase5-controls'>Review current state</a></p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + output + "</pre>"
        "</body></html>",
        status_code=200 if receipt["status"] == "PASS_READBACK" else 409,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/ritual/status", operation_id="auguryRitualPhase1Status")
def augury_ritual_phase1_status(browser_request: Request):
    """Read-only AUGURY/RITUAL Phase-1 status and controlled Phase-4 state."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    gaiaos_api._authorize_browser_session(browser_request)
    return augury_ritual.phase1_status(memcon_runtime)


@app.get("/ritual/phase4/review", response_class=HTMLResponse, operation_id="auguryRitualPhase4Review")
def augury_ritual_phase4_review(browser_request: Request):
    """Human-operated exact Ritual console. GET is strictly read-only."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    csrf = _ritual_csrf(browser_request)
    state = augury_ritual.phase1_status(memcon_runtime)
    start_json = html.escape(json.dumps(state, ensure_ascii=False, indent=2))
    script = """
<script>
const csrf = __CSRF__;
const SOURCE = __SOURCE__;
const TARGET = __TARGET__;
const PROPOSE = __PROPOSE__;
const VERIFY = __VERIFY__;
const REVOKE = __REVOKE__;

async function getStatus() {
  const r = await fetch("/ritual/status", {credentials:"same-origin"});
  return await r.json();
}
async function refresh() {
  const result = await getStatus();
  document.getElementById("receipt").textContent = JSON.stringify(result,null,2);
}
async function manifest(kind) {
  const state = await getStatus();
  const fixture = state.phase4_controlled_fixture || {};
  let ritual_id, params, confirmation, prompt;
  if (kind === "PROPOSE") {
    ritual_id = PROPOSE;
    params = {source_record_id:SOURCE, target_record_id:TARGET};
    confirmation = "MANIFEST_GALAXY_PHASE4_PROPOSE_SUPERSEDES_CONTROLLED_FIXTURE";
    prompt = "Propose the exact controlled SUPERSEDES edge? This writes a PROPOSED relation but does not change governing state.";
  } else if (kind === "VERIFY") {
    const ids = fixture.proposed_edge_ids || [];
    if (ids.length !== 1) {
      document.getElementById("receipt").textContent = "HOLD: expected exactly one PROPOSED controlled SUPERSEDES edge; found " + ids.length;
      return;
    }
    ritual_id = VERIFY;
    params = {edge_id:ids[0]};
    confirmation = "MANIFEST_GALAXY_PHASE4_VERIFY_SUPERSEDES_CONTROLLED_FIXTURE";
    prompt = "VERIFY controlled SUPERSEDES? This changes the target governing state to HISTORICAL_SUPERSEDED while preserving history.";
  } else if (kind === "REVOKE") {
    const ids = fixture.verified_edge_ids || [];
    if (ids.length !== 1) {
      document.getElementById("receipt").textContent = "HOLD: expected exactly one VERIFIED controlled SUPERSEDES edge; found " + ids.length;
      return;
    }
    ritual_id = REVOKE;
    params = {edge_id:ids[0], reason:"Controlled Phase-4 Ritual rollback proof"};
    confirmation = "MANIFEST_GALAXY_PHASE4_REVOKE_SUPERSEDES_CONTROLLED_FIXTURE";
    prompt = "REVOKE controlled SUPERSEDES and restore CURRENT_REVISED_CONTEXT? Edge/history will be preserved as REVOKED.";
  } else {
    return;
  }
  if (!window.confirm(prompt)) return;
  const r = await fetch("/ritual/manifest", {
    method:"POST",
    credentials:"same-origin",
    headers:{"Content-Type":"application/json","X-GaiaOS-Ritual-CSRF":csrf},
    body:JSON.stringify({
      authority:"NAOMI",
      approved:true,
      action:"MANIFEST_EXACT_RITUAL",
      ritual_id:ritual_id,
      params:params,
      confirmation:confirmation
    })
  });
  const result = await r.json();
  document.getElementById("receipt").textContent =
    (r.ok ? "" : "HTTP " + r.status + "\n") + JSON.stringify(result,null,2);
}
</script>
"""
    script = (
        script.replace("__CSRF__", json.dumps(csrf))
        .replace("__SOURCE__", json.dumps(augury_ritual.SOURCE_ID))
        .replace("__TARGET__", json.dumps(augury_ritual.TARGET_ID))
        .replace("__PROPOSE__", json.dumps(augury_ritual.PROPOSE_ID))
        .replace("__VERIFY__", json.dumps(augury_ritual.VERIFY_ID))
        .replace("__REVOKE__", json.dumps(augury_ritual.REVOKE_ID))
    )
    page = (
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>AUGURY ↔ RITUAL Phase 1: GALAXY Phase 4 controlled manifestation</h2>"
        "<p>AUGURY natural-language manifestation is disabled. These are exact Rituals over one controlled fixture pair.</p>"
        "<p>Required sequence: propose SUPERSEDES → verify SUPERSEDES → revoke SUPERSEDES. "
        "Each mutation requires a separate confirmation. The pre-existing REVISES edge is never revoked here.</p>"
        "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;text-decoration:none;border-radius:10px' href='/ritual/phase4/confirm/PROPOSE'>1. Propose controlled SUPERSEDES</a></p>"
        "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;text-decoration:none;border-radius:10px' href='/ritual/phase4/confirm/VERIFY'>2. Verify controlled SUPERSEDES</a></p>"
        "<p><a style='display:inline-block;padding:12px 16px;background:#eee;color:#111;text-decoration:none;border-radius:10px' href='/ritual/phase4/confirm/REVOKE'>3. Revoke controlled SUPERSEDES</a></p>"
        "<p><button onclick=\"refresh()\">Refresh status</button></p>"
        "<pre id='receipt' style='white-space:pre-wrap;word-break:break-word'>"
        + start_json + "</pre>" + script + "</body></html>"
    )
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})



def _ritual_form_value(fields: dict[str, list[str]], key: str) -> str:
    values = fields.get(key) or []
    return str(values[0]) if values else ""


@app.get("/ritual/phase4/confirm/{kind}", response_class=HTMLResponse, operation_id="auguryRitualPhase4Confirm")
def augury_ritual_phase4_confirm(kind: str, browser_request: Request):
    """No-JavaScript confirmation surface for iOS/in-app browsers."""
    bootstrap = _bootstrap_browser_session_redirect(browser_request)
    if bootstrap is not None:
        return bootstrap
    csrf = _ritual_csrf(browser_request)
    kind = str(kind or "").upper()
    state = augury_ritual.phase1_status(memcon_runtime)
    fixture = state.get("phase4_controlled_fixture") or {}

    if kind == "PROPOSE":
        ritual_id = augury_ritual.PROPOSE_ID
        confirmation = "MANIFEST_GALAXY_PHASE4_PROPOSE_SUPERSEDES_CONTROLLED_FIXTURE"
        summary = (
            "Propose the exact controlled SUPERSEDES edge. "
            "This writes one PROPOSED relation and does not change governing state."
        )
        params = {
            "source_record_id": augury_ritual.SOURCE_ID,
            "target_record_id": augury_ritual.TARGET_ID,
        }
    elif kind == "VERIFY":
        ids = list(fixture.get("proposed_edge_ids") or [])
        if len(ids) != 1:
            return HTMLResponse(
                "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
                "<h2>Ritual HOLD</h2><p>Expected exactly one PROPOSED controlled SUPERSEDES edge; found "
                + html.escape(str(len(ids))) +
                ".</p><p><a style='color:#9ee7ff' href='/ritual/phase4/review'>Back to review</a></p>"
                "</body></html>",
                status_code=409,
                headers={"Cache-Control": "no-store"},
            )
        ritual_id = augury_ritual.VERIFY_ID
        confirmation = "MANIFEST_GALAXY_PHASE4_VERIFY_SUPERSEDES_CONTROLLED_FIXTURE"
        summary = (
            "Verify the exact proposed SUPERSEDES edge. "
            "This changes the target governing state to HISTORICAL_SUPERSEDED while preserving history."
        )
        params = {"edge_id": ids[0]}
    elif kind == "REVOKE":
        ids = list(fixture.get("verified_edge_ids") or [])
        if len(ids) != 1:
            return HTMLResponse(
                "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
                "<h2>Ritual HOLD</h2><p>Expected exactly one VERIFIED controlled SUPERSEDES edge; found "
                + html.escape(str(len(ids))) +
                ".</p><p><a style='color:#9ee7ff' href='/ritual/phase4/review'>Back to review</a></p>"
                "</body></html>",
                status_code=409,
                headers={"Cache-Control": "no-store"},
            )
        ritual_id = augury_ritual.REVOKE_ID
        confirmation = "MANIFEST_GALAXY_PHASE4_REVOKE_SUPERSEDES_CONTROLLED_FIXTURE"
        summary = (
            "Revoke the exact verified SUPERSEDES edge. "
            "The edge/history remains preserved as REVOKED and governing state returns to CURRENT_REVISED_CONTEXT."
        )
        params = {
            "edge_id": ids[0],
            "reason": "Controlled Phase-4 Ritual rollback proof",
        }
    else:
        raise HTTPException(status_code=404, detail="Unknown controlled Ritual step")

    hidden = [
        ("csrf", csrf),
        ("authority", "NAOMI"),
        ("approved", "true"),
        ("action", "MANIFEST_EXACT_RITUAL"),
        ("ritual_id", ritual_id),
        ("confirmation", confirmation),
    ]
    for key, value in params.items():
        hidden.append((f"param_{key}", str(value)))
    fields = "".join(
        "<input type='hidden' name='" + html.escape(key, quote=True) +
        "' value='" + html.escape(value, quote=True) + "'>"
        for key, value in hidden
    )
    details = html.escape(json.dumps({
        "ritual_id": ritual_id,
        "params": params,
        "current_target_governing_state": fixture.get("target_governing_state"),
    }, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Confirm exact Ritual</h2><p>" + html.escape(summary) + "</p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + details + "</pre>"
        "<form method='post' action='/ritual/manifest-form'>" + fields +
        "<button type='submit' style='font-size:18px;padding:12px 16px'>Confirm this exact Ritual</button>"
        "</form><p><a style='color:#9ee7ff' href='/ritual/phase4/review'>Cancel / back to review</a></p>"
        "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/ritual/manifest-form", response_class=HTMLResponse, operation_id="manifestExactRitualForm")
async def manifest_exact_ritual_form(browser_request: Request):
    """No-JavaScript exact manifestation path with the same session/CSRF/authority gates."""
    expected_csrf = _ritual_csrf(browser_request)
    if "application/x-www-form-urlencoded" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Ritual form requires URL-encoded POST")
    raw = (await browser_request.body()).decode("utf-8")
    fields = parse_qs(raw, keep_blank_values=True)
    supplied_csrf = _ritual_form_value(fields, "csrf")
    if not hmac.compare_digest(supplied_csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Ritual CSRF proof failed")
    if (
        _ritual_form_value(fields, "authority") != "NAOMI"
        or _ritual_form_value(fields, "approved") != "true"
        or _ritual_form_value(fields, "action") != "MANIFEST_EXACT_RITUAL"
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi Ritual action required")

    ritual_id = _ritual_form_value(fields, "ritual_id")
    params = {
        key[len("param_"):]: values[0]
        for key, values in fields.items()
        if key.startswith("param_") and values
    }
    try:
        result = augury_ritual.manifest(
            memcon_runtime,
            ritual_id,
            params,
            authority="NAOMI",
            approved=True,
            confirmation=_ritual_form_value(fields, "confirmation"),
        )
    except (KeyError, ValueError, PermissionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
    return HTMLResponse(
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>Ritual manifestation receipt</h2>"
        "<p><a style='color:#9ee7ff' href='/ritual/phase4/review'>Back to review</a></p>"
        "<pre style='white-space:pre-wrap;word-break:break-word'>" + output + "</pre>"
        "</body></html>",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/ritual/manifest", operation_id="manifestExactRitual")
async def manifest_exact_ritual(browser_request: Request):
    """Manifest only an exact Grimoire-bound Phase-1 Ritual after explicit authority."""
    body = await _ritual_authorized_body(browser_request)
    try:
        return augury_ritual.manifest(
            memcon_runtime,
            body["ritual_id"],
            body["params"],
            authority="NAOMI",
            approved=True,
            confirmation=str(body.get("confirmation") or ""),
        )
    except (KeyError, ValueError, PermissionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _galaxy_production_csrf(browser_request: Request) -> str:
    """Session-bound CSRF proof. Mutation routes fail closed without server API key."""
    gaiaos_api._authorize_browser_session(browser_request)
    if not gaiaos_api.API_KEY:
        raise HTTPException(status_code=503, detail="GAIAOS_API_KEY required for production controls")
    token = browser_request.cookies.get(gaiaos_api.SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Missing browser session")
    return hmac.new(
        gaiaos_api.API_KEY.encode(),
        ("GALAXY_PHASE3F_PRODUCTION:" + token).encode(),
        hashlib.sha256,
    ).hexdigest()


async def _galaxy_production_authorized_body(browser_request: Request, expected_action: str) -> dict:
    expected_csrf = _galaxy_production_csrf(browser_request)
    supplied = browser_request.headers.get("x-gaiaos-production-csrf", "")
    if not hmac.compare_digest(supplied, expected_csrf):
        raise HTTPException(status_code=403, detail="Production CSRF proof failed")
    if "application/json" not in browser_request.headers.get("content-type", "").lower():
        raise HTTPException(status_code=415, detail="Production controls require JSON POST")
    body = await browser_request.json()
    if (
        not isinstance(body, dict)
        or body.get("authority") != "NAOMI"
        or body.get("approved") is not True
        or body.get("action") != expected_action
    ):
        raise HTTPException(status_code=403, detail="Explicit Naomi production action required")
    return body


@app.get("/galaxy/production/status", operation_id="galaxyProductionPilotStatus")
def galaxy_production_pilot_status(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return galaxy_production.status(memcon_runtime)


@app.get("/galaxy/production/review", response_class=HTMLResponse, operation_id="galaxyProductionReview")
def galaxy_production_review(browser_request: Request):
    """Explicit human-operated production pilot console. GET itself has zero effects."""
    csrf = _galaxy_production_csrf(browser_request)
    state = galaxy_production.status(memcon_runtime)
    start_json = html.escape(json.dumps(state, ensure_ascii=False, indent=2))
    # JS literal is JSON encoded; no user input or secrets are interpolated into markup.
    script = """
<script>
const csrf = __CSRF__;
async function run(action) {
  const labels = {
    "RUN_SWITCH_TEST": "RUN integrated ON/OFF switch test?",
    "ACTIVATE_10_MINUTE_PILOT": "Activate the three-query production pilot for up to 10 minutes?",
    "RUN_ACTIVE_ROLLBACK_PROOF": "Exercise active pilot and immediately roll back to ordinary retrieval?",
    "EMERGENCY_ROLLBACK": "Disable pilot weighting immediately?"
  };
  if (!window.confirm(labels[action])) return;
  const paths = {
    "RUN_SWITCH_TEST": "switch-test",
    "ACTIVATE_10_MINUTE_PILOT": "activate",
    "RUN_ACTIVE_ROLLBACK_PROOF": "rollback-proof",
    "EMERGENCY_ROLLBACK": "rollback"
  };
  try {
    const r = await fetch("/galaxy/production/" + paths[action], {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json", "X-GaiaOS-Production-CSRF": csrf},
      body: JSON.stringify({authority:"NAOMI", approved:true, action:action,
        confirmation:action==="ACTIVATE_10_MINUTE_PILOT"?"ACTIVATE_80_20_EXACT_QUERY_PILOT":""})
    });
    const result = await r.json();
    document.getElementById("receipt").textContent = JSON.stringify(result,null,2);
    if (!r.ok) document.getElementById("receipt").textContent = "HTTP " + r.status + "\\n" + JSON.stringify(result,null,2);
  } catch(e) {
    document.getElementById("receipt").textContent = String(e);
  }
}
async function refresh() {
  const r = await fetch("/galaxy/production/status", {credentials:"same-origin"});
  document.getElementById("receipt").textContent = JSON.stringify(await r.json(),null,2);
}
</script>
""".replace("__CSRF__", json.dumps(csrf))
    page = (
        "<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<body style='background:#101318;color:#e7f3f4;font:16px system-ui;padding:16px'>"
        "<h2>GALAXY Phase 3F: guarded production pilot</h2>"
        "<p>Naomi-authorized 80/20, one carrier process, three exact MemoryOS queries, "
        "10-minute maximum. Ordinary retrieval remains the default. No full global rollout.</p>"
        "<p>Required sequence: switch test, optional short pilot, active rollback proof. "
        "Every restart fails OFF. Kill switch: GALAXY_PRODUCTION_PILOT_KILL_SWITCH=1.</p>"
        "<p><button onclick=\"run('RUN_SWITCH_TEST')\">1. Live ON/OFF switch test</button></p>"
        "<p><button onclick=\"run('ACTIVATE_10_MINUTE_PILOT')\">2. Activate 10-minute pilot</button></p>"
        "<p><button onclick=\"run('RUN_ACTIVE_ROLLBACK_PROOF')\">3. Prove active rollback</button></p>"
        "<p><button onclick=\"run('EMERGENCY_ROLLBACK')\">Emergency rollback</button> "
        "<button onclick=\"refresh()\">Refresh status</button></p>"
        "<pre id='receipt' style='white-space:pre-wrap;word-break:break-word'>"
        + start_json + "</pre>" + script + "</body></html>"
    )
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@app.post("/galaxy/production/switch-test", operation_id="galaxyProductionLiveSwitchTest")
async def galaxy_production_live_switch_test(browser_request: Request):
    await _galaxy_production_authorized_body(browser_request, "RUN_SWITCH_TEST")
    return galaxy_production.switch_test(
        memcon_runtime, memcon_entrypoint._memory_runtime().retrieve
    )


@app.post("/galaxy/production/activate", operation_id="galaxyProductionActivate")
async def galaxy_production_activate(browser_request: Request):
    body = await _galaxy_production_authorized_body(browser_request, "ACTIVATE_10_MINUTE_PILOT")
    if body.get("confirmation") != "ACTIVATE_80_20_EXACT_QUERY_PILOT":
        raise HTTPException(status_code=403, detail="Exact pilot activation confirmation required")
    return galaxy_production.activate(
        memcon_runtime, authority="NAOMI", approved=True, lease_seconds=600
    )


@app.post("/galaxy/production/rollback-proof", operation_id="galaxyProductionActiveRollbackProof")
async def galaxy_production_active_rollback_proof(browser_request: Request):
    await _galaxy_production_authorized_body(browser_request, "RUN_ACTIVE_ROLLBACK_PROOF")
    return galaxy_production.live_rollback_proof(
        memcon_runtime, memcon_entrypoint._memory_runtime().retrieve
    )


@app.post("/galaxy/production/rollback", operation_id="galaxyProductionEmergencyRollback")
async def galaxy_production_emergency_rollback(browser_request: Request):
    await _galaxy_production_authorized_body(browser_request, "EMERGENCY_ROLLBACK")
    return galaxy_production.rollback(memcon_runtime, reason="EXPLICIT_NAOMI_EMERGENCY_ROLLBACK")


@app.get("/galaxy/retrieval/phase3-canary", operation_id="galaxyPhase3MulticandidateCanary")
def galaxy_phase3_multicandidate_canary(browser_request: Request):
    """Explicit Naomi-authorized isolated multi-candidate Phase-3 calibration canary."""
    gaiaos_api._authorize_browser_session(browser_request)
    return memcon_runtime.galaxy_phase3_multicandidate_canary(authority="NAOMI", approved=True)


@app.get("/galaxy/canary/start", response_class=HTMLResponse)
def galaxy_canary_start_page(browser_request: Request):
    """Direct browser canary path. Does not depend on OPENAI_API_KEY."""
    bootstrap_session = gaiaos_api.API_KEY is not None and not browser_request.cookies.get(gaiaos_api.SESSION_COOKIE)
    if not bootstrap_session:
        gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _handle_galaxy_canary_start()
        output = html.escape(result["output"])
        response = HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GALAXY two-memory canary</h1>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "<p><a style='font-size:22px' href='/galaxy/canary/approve'>Approve the two controlled memories</a></p>"
            "<p>This approval performs the two durable MemoryOS writes, then creates only a PROPOSED shadow edge.</p>"
            "</body></html>"
        )
        if bootstrap_session:
            response.set_cookie(gaiaos_api.SESSION_COOKIE, gaiaos_api._session_token(), httponly=True, samesite="lax", secure=True, max_age=86400)
        return response
    except Exception as exc:
        return _error_page("GALAXY canary start failed", exc)


@app.get("/galaxy/canary/approve", response_class=HTMLResponse)
def galaxy_canary_approve_page(browser_request: Request):
    """Explicit browser approval step for the paired controlled memories."""
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _handle_galaxy_canary_approve()
        output = html.escape(result["output"])
        payload = {}
        try:
            payload = json.loads(result["output"].split("\n\n", 1)[1])
        except (ValueError, json.JSONDecodeError, IndexError):
            payload = {}
        edge_id = ((payload.get("relation") or {}).get("relation") or {}).get("edge_id")
        verify_link = (
            f"<p><a style='font-size:22px' href='/galaxy/canary/verify/{html.escape(str(edge_id))}'>Verify proposed GALAXY edge</a></p>"
            if edge_id else
            "<p>No edge_id was returned. Do not claim verification.</p>"
        )
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GALAXY canary approval</h1>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            + verify_link +
            "<p>The edge remains PROPOSED until the separate verification click.</p>"
            "</body></html>"
        )
    except Exception as exc:
        return _error_page("GALAXY canary approval failed", exc)


@app.get("/galaxy/canary/verify/{edge_id}", response_class=HTMLResponse)
def galaxy_canary_verify_page(edge_id: str, browser_request: Request):
    """Explicit edge verification plus ORBIT/readback/retrieval comparison, no OpenAI dependency."""
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _handle_galaxy_relation_verify(f"GALAXY VERIFY {edge_id}")
        output = html.escape(result["output"])
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GALAXY edge verification</h1>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "<p><a href='/galaxy/status'>View GALAXY status</a></p>"
            "</body></html>"
        )
    except Exception as exc:
        return _error_page("GALAXY edge verification failed", exc)


@app.get("/galaxy/record/{record_id}", operation_id="galaxyRecordInspection")
def galaxy_record_inspection(record_id: str, browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = memcon_runtime.galaxy_record(record_id)
    if result is None:
        return JSONResponse({"status": "HOLD", "reason": "Unknown durable record_id", "record_id": record_id}, status_code=404)
    return result


@app.post("/memoryos/browser-test", operation_id="browserMemoryOSLifecycleTest")
async def browser_memoryos_test(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    payload = await browser_request.json()
    action = str(payload.get("action", "")).strip().lower()
    if action == "start":
        return _start_lifecycle()
    if action == "approve":
        return _approve_lifecycle()
    return {"status": "ERROR", "detail": "action must be start or approve"}


def _error_page(title: str, exc: Exception) -> HTMLResponse:
    detail = f"{type(exc).__name__}: {exc}"
    return HTMLResponse(
        "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        f"<h1>{html.escape(title)}</h1>"
        f"<pre style='white-space:pre-wrap'>{html.escape(detail)}</pre>"
        "<p>Runtime action was not reported as successful.</p></body></html>",
        status_code=500,
    )


@app.get("/memoryos/start", response_class=HTMLResponse)
def memoryos_start(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _start_lifecycle()
        output = html.escape(result["output"])
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS start</h1>" + f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "<p><a style='font-size:22px' href='/memoryos/approve'>Approve pending candidate</a></p></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS start failed", exc)


@app.get("/memoryos/approve", response_class=HTMLResponse)
def memoryos_approve(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = _approve_lifecycle()
        output = html.escape(result["output"])
        # _approve_lifecycle returns a carrier envelope; promotion lives inside its JSON output.
        # Parse that observed payload so the UI cannot silently lose the verified record_id.
        approved_payload = {}
        try:
            approved_payload = json.loads(result["output"].split("\n\n", 1)[1])
        except (KeyError, IndexError, json.JSONDecodeError):
            approved_payload = {}
        record_id = approved_payload.get("promotion", {}).get("record_id")
        continuity_action = ""
        if record_id:
            from urllib.parse import urlencode
            continuity_url = "/memoryos/continuity?" + urlencode({"record_id": str(record_id)})
            continuity_action = (
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href='" + html.escape(continuity_url, quote=True) + "'>"
                "Continue with this exact record</a></p>"
                "<p>The record ID above was supplied directly by the verified promotion receipt. No manual transcription is required.</p>"
            )
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>MemoryOS approval</h1>" + continuity_action
            + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS approval failed", exc)


@app.get("/memoryos/test", response_class=HTMLResponse)
def memoryos_test_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    return HTMLResponse("""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaiaOS MemoryOS Test</title></head><body style="font-family:-apple-system;padding:20px;background:#111;color:#eee">
<h1>MemoryOS lifecycle test</h1><p>Direct carrier-runtime test. No JavaScript.</p>
<p><a style="font-size:24px" href="/memoryos/start">1. Start test</a></p>
<p><a style="font-size:24px" href="/memoryos/approve">2. Approve pending candidate</a></p>
</body></html>""")



@app.get("/persistence/canary", response_class=HTMLResponse, operation_id="restartPersistenceCanary")
def restart_persistence_canary(browser_request: Request, token: str | None = None):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = memcon_runtime.restart_canary(token)
        if token is None and result.get("status") == "ARMED":
            # Pin the newly armed marker into the browser URL immediately. This
            # prevents a refresh from silently creating a different marker.
            pinned_url = "/persistence/canary?token=" + str(result["token"])
            return RedirectResponse(url=pinned_url, status_code=303)
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("status") == "PASS":
            action = "<p><strong>RESTART PERSISTENCE PROVEN.</strong> The marker survived into a different carrier process boot.</p>"
        else:
            action = (
                "<p><strong>Marker pinned.</strong> Restart or redeploy the Render service now. "
                "When it is back online, return to this exact page and tap the button below.</p>"
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href=''>Check after restart</a></p>"
                "<p>Refreshing this page is also safe: the marker is stored in this page's URL and will not be replaced.</p>"
            )
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS Restart Persistence Canary</h1>"
            + action + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>")
    except Exception as exc:
        return _error_page("Restart persistence canary failed", exc)


def _continuity_identity() -> dict:
    return {
        "boot_id": memcon_runtime.BOOT_ID,
        "render_instance_id": memcon_runtime.RENDER_INSTANCE_ID or None,
        "process_fingerprint": memcon_runtime._process_fingerprint(),
    }


def _safe_debug_value(value):
    try:
        return {"type": type(value).__name__, "repr": repr(value)}
    except Exception as exc:
        return {"type": type(value).__name__, "repr_error": type(exc).__name__}


def _memoryos_raw_read_diagnostic(record_id: str) -> dict:
    """Read-only backend interrogation. Never returns credentials."""
    with memcon_runtime._db() as conn:
        exact_cursor = conn.execute("SELECT * FROM memory_records WHERE record_id = ?", (record_id,))
        exact_description = getattr(exact_cursor, "description", None)
        exact_rows = exact_cursor.fetchall()
        broad_cursor = conn.execute("SELECT * FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT ?", ("MemoryOS", 10))
        broad_description = getattr(broad_cursor, "description", None)
        broad_rows = broad_cursor.fetchall()
        sql_probe_cursor = conn.execute(
            """SELECT record_id, length(record_id), hex(record_id), quote(record_id),
                      typeof(record_id), record_id = ?,
                      length(?) AS requested_length, hex(?) AS requested_hex,
                      quote(?) AS requested_quote, typeof(?) AS requested_type
               FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT 10""",
            (record_id, record_id, record_id, record_id, record_id, "MemoryOS"),
        )
        sql_probe_description = getattr(sql_probe_cursor, "description", None)
        sql_probe_rows = sql_probe_cursor.fetchall()
    def describe(desc):
        return [{"type": type(col).__name__, "repr": repr(col), "name": getattr(col, "name", None)} for col in (desc or [])]
    def rows(raw):
        return [{"row_type": type(row).__name__, "values": [_safe_debug_value(v) for v in row]} for row in raw]
    return {
        "backend": memcon_runtime.STORAGE_BACKEND,
        "requested": {"repr": repr(record_id), "length": len(record_id), "codepoints": [ord(ch) for ch in record_id]},
        "exact_query": {"description": describe(exact_description), "row_count": len(exact_rows), "rows": rows(exact_rows)},
        "broad_query": {"description": describe(broad_description), "row_count": len(broad_rows), "rows": rows(broad_rows)},
        "sql_value_probe": {"description": describe(sql_probe_description), "row_count": len(sql_probe_rows), "rows": rows(sql_probe_rows)},
        "proof_boundary": "Read-only raw driver and SQL value evidence. No persistence conclusion is implied by this diagnostic alone.",
    }

@app.get("/memoryos/raw-diagnostic", response_class=HTMLResponse, operation_id="memoryOSRawDiagnostic")
def memoryos_raw_diagnostic(browser_request: Request, record_id: str):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        diagnostic = _memoryos_raw_read_diagnostic(record_id)
        output = html.escape(json.dumps(diagnostic, ensure_ascii=False, indent=2))
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'><h1>MemoryOS raw read diagnostic</h1><pre style='white-space:pre-wrap'>" + output + "</pre></body></html>")
    except Exception as exc:
        return _error_page("MemoryOS raw diagnostic failed", exc)


@app.get("/memoryos/continuity", response_class=HTMLResponse, operation_id="memoryOSContinuityTest")
def memoryos_continuity(
    browser_request: Request,
    record_id: str,
    prior_boot: str | None = None,
    prior_render: str | None = None,
    prior_pid: int | None = None,
    prior_ticks: str | None = None,
):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        record = memcon_runtime.get_record(record_id)
        if record is None:
            # Read-only diagnostics: identify the active backend and show whether
            # any recent MemoryOS records are visible there. This prevents a
            # missing row from being misreported as a persistence conclusion.
            visible_records = memcon_runtime.search_records("", 10, "MemoryOS")
            id_comparison = [{"requested_repr": repr(record_id), "requested_length": len(record_id), "visible_repr": repr(item.get("record_id")), "visible_length": len(str(item.get("record_id", ""))), "python_exact_equal": item.get("record_id") == record_id, "requested_codepoints": [ord(ch) for ch in record_id], "visible_codepoints": [ord(ch) for ch in str(item.get("record_id", ""))]} for item in visible_records.get("records", [])]
            diagnostic = {
                "schema": "gaiaos.memoryos.continuity-diagnostic.v2",
                "status": "HOLD",
                "record_id": record_id,
                "exact_record_retrieved": False,
                "storage": memcon_runtime.storage_status(),
                "memoryos_records_visible": visible_records,
                "record_id_comparison": id_comparison,
                "carrier": _continuity_identity(),
                "interpretation": (
                    "The requested record is not visible in the currently configured runtime store. "
                    "This diagnostic does not determine whether it was deleted, written to another backend, "
                    "or never durably committed there."
                ),
                "next_action": "Do not restart. Use the canonical record_id from the visible durable record if this request contains a transcription error.",
            }
            output = html.escape(json.dumps(diagnostic, ensure_ascii=False, indent=2))
            return HTMLResponse(
                "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
                "<h1>MemoryOS continuity HOLD</h1><p>The exact record was not found. Read-only diagnostics follow.</p>"
                f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>",
                status_code=404,
            )

        current = _continuity_identity()
        current_pf = current["process_fingerprint"]
        if prior_boot is None:
            params = {
                "record_id": record_id,
                "prior_boot": current["boot_id"],
                "prior_render": current["render_instance_id"] or "",
                "prior_pid": str(current_pf.get("pid", "")),
                "prior_ticks": str(current_pf.get("proc_start_ticks", "")),
            }
            from urllib.parse import urlencode
            return RedirectResponse(url="/memoryos/continuity?" + urlencode(params), status_code=303)

        prior = {
            "boot_id": prior_boot,
            "render_instance_id": prior_render or None,
            "process_fingerprint": {"pid": prior_pid, "proc_start_ticks": prior_ticks},
        }
        boot_changed = current["boot_id"] != prior["boot_id"]
        render_changed = bool(current["render_instance_id"] and prior["render_instance_id"] and current["render_instance_id"] != prior["render_instance_id"])
        process_changed = (
            current_pf.get("pid") != prior_pid
            or str(current_pf.get("proc_start_ticks")) != str(prior_ticks)
        )
        different_carrier = boot_changed or render_changed or process_changed
        exact_record_retrieved = record.get("record_id") == record_id
        status = "PASS" if (different_carrier and exact_record_retrieved) else "NOT_RESTARTED"
        result = {
            "schema": "gaiaos.memoryos.continuity-receipt.v1",
            "status": status,
            "record_id": record_id,
            "record_retrieved": True,
            "record": record,
            "storage": memcon_runtime.storage_status(),
            "current_carrier": current,
            "prior_carrier": prior,
            "checks": {
                "boot_id_changed": boot_changed,
                "render_instance_changed": render_changed,
                "process_fingerprint_changed": process_changed,
                "different_carrier_observed": different_carrier,
                "exact_record_retrieved": exact_record_retrieved,
            },
            "proof_boundary": (
                "PASS proves this exact MemoryOS record was retrieved after an observed carrier identity change. "
                "It does not prove every MemoryOS operation or every failure mode."
            ),
        }
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        if status == "PASS":
            action = "<p><strong>MEMORYOS CONTINUITY PROVEN.</strong> Exact record retrieved after carrier identity changed.</p>"
        else:
            action = (
                "<p><strong>Baseline pinned.</strong> Do not change this URL. Restart Render once, wait for it to return, "
                "then tap the button below.</p>"
                "<p><a style='display:inline-block;font-size:22px;padding:12px 16px;background:#eee;color:#111;"
                "text-decoration:none;border-radius:10px' href=''>Check after restart</a></p>"
            )
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS MemoryOS Continuity Test</h1>" + action
            + f"<pre style='white-space:pre-wrap'>{output}</pre></body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS continuity test failed", exc)


@app.get("/memoryos/continuity/recover", response_class=HTMLResponse, operation_id="memoryOSContinuityRecover")
def memoryos_continuity_recover(browser_request: Request):
    """Read-only recovery for a lost pinned tab using an independently preserved pre-restart baseline."""
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        # Resolve the canonical record from durable evidence, not a hand-copied ID.
        expected_source = "browser-memoryos-test:371a6d98a3bd"
        with memcon_runtime._db() as conn:
            canonical_cursor = conn.execute(
                "SELECT record_id FROM memory_records WHERE scope = ? AND source = ? ORDER BY created_at DESC LIMIT 1",
                ("MemoryOS", expected_source),
            )
            canonical_row = canonical_cursor.fetchone()
        if canonical_row is None:
            raise RuntimeError("Canonical continuity record was not found by its durable source marker")
        record_id = str(canonical_row[0])
        prior = {
            "boot_id": "BOOT-bf2621aa5b3c49039789b452515a98bd",
            "render_instance_id": "srv-dafvq6ijnfac739rih70-hibernate-66bc89c57-5k4kv",
            "process_fingerprint": {"pid": 7, "proc_start_ticks": "1225523065"},
        }
        record = memcon_runtime.get_record(record_id)
        # Independent read-only witness: ask the configured database directly
        # whether the exact ID exists, and also list recent MemoryOS IDs. This
        # separates durable-row presence from any higher-level retrieval bug.
        with memcon_runtime._db() as conn:
            exact_cursor = conn.execute(
                "SELECT record_id, authority, record_type, scope, statement, source, status, version, created_at, updated_at, supersedes, notes FROM memory_records WHERE record_id = ?",
                (record_id,),
            )
            exact_rows = exact_cursor.fetchall()
            broad_cursor = conn.execute(
                "SELECT record_id, scope, source, created_at, updated_at FROM memory_records WHERE scope = ? ORDER BY created_at DESC LIMIT 10",
                ("MemoryOS",),
            )
            broad_rows = broad_cursor.fetchall()
        raw_exact = [_safe_debug_value(list(row)) for row in exact_rows]
        raw_broad = [_safe_debug_value(list(row)) for row in broad_rows]
        broad_ids = [str(row[0]) for row in broad_rows]
        raw_exact_present = any(str(row[0]) == record_id for row in exact_rows)
        broad_exact_present = record_id in broad_ids
        current = _continuity_identity()
        current_pf = current["process_fingerprint"]
        boot_changed = current["boot_id"] != prior["boot_id"]
        render_changed = bool(current["render_instance_id"] and current["render_instance_id"] != prior["render_instance_id"])
        process_changed = (
            current_pf.get("pid") != prior["process_fingerprint"]["pid"]
            or str(current_pf.get("proc_start_ticks")) != prior["process_fingerprint"]["proc_start_ticks"]
        )
        different_carrier = boot_changed or render_changed or process_changed
        exact_record_retrieved = bool(record and record.get("record_id") == record_id)
        status = "PASS" if (different_carrier and exact_record_retrieved) else "HOLD"
        result = {
            "schema": "gaiaos.memoryos.continuity-recovery-receipt.v2",
            "status": status,
            "baseline_source": "operator-preserved pre-restart screenshot",
            "record_identity_source": "durable MemoryOS source marker resolved by database",
            "record_id": record_id,
            "record_retrieved": record is not None,
            "record": record,
            "raw_database_witness": {
                "exact_sql_present": raw_exact_present,
                "broad_scan_contains_exact_id": broad_exact_present,
                "exact_rows": raw_exact,
                "recent_memoryos_rows": raw_broad,
                "interpretation": (
                    "If either raw presence check is true while record_retrieved is false, the durable row exists and the higher-level retrieval path is defective. "
                    "If both raw presence checks are false, this endpoint has not found the named row in the configured database."
                ),
            },
            "storage": memcon_runtime.storage_status(),
            "prior_carrier": prior,
            "current_carrier": current,
            "checks": {
                "boot_id_changed": boot_changed,
                "render_instance_changed": render_changed,
                "process_fingerprint_changed": process_changed,
                "different_carrier_observed": different_carrier,
                "exact_record_retrieved": exact_record_retrieved,
            },
            "proof_boundary": (
                "PASS proves the exact named MemoryOS record is readable now and that the live carrier identity differs "
                "from the independently preserved pre-restart baseline. The prior baseline values came from the operator's "
                "pre-restart screenshot, not from durable server-side pinning. It does not prove every MemoryOS operation "
                "or universal cross-host continuity."
            ),
        }
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        heading = "MEMORYOS RECOVERY CONTINUITY PROVEN" if status == "PASS" else "MemoryOS recovery continuity HOLD"
        return HTMLResponse(
            "<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            f"<h1>{heading}</h1><pre style='white-space:pre-wrap'>{output}</pre></body></html>"
        )
    except Exception as exc:
        return _error_page("MemoryOS continuity recovery failed", exc)


@app.get("/runtime/routes", operation_id="runtimeRouteManifest")
def runtime_route_manifest():
    """Unauthenticated bounded route manifest for deployment verification."""
    routes = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = sorted(getattr(route, "methods", set()) or [])
        if path in {"/health", "/verify", "/runtime/routes"}:
            routes.append({"path": path, "methods": methods})
    return {
        "status": "ok",
        "service": "gaiaos-carrier",
        "source": gaiaos_app._deployed_source(),
        "routes": routes,
        "verify_registered": any(r["path"] == "/verify" and "GET" in r["methods"] for r in routes),
    }


@app.get("/verify", response_class=HTMLResponse, operation_id="verificationPage")
def verification_page(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = gaiaos_verification.run_verification()
    output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
    return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
        "<h1>GaiaOS Implementation Verification</h1>"
        "<p>Every PASS below is an observation from this running carrier process.</p>"
        f"<pre style='white-space:pre-wrap'>{output}</pre>"
        "</body></html>")



@app.get("/vaskon/test", response_class=HTMLResponse, operation_id="liveVaskonTest")
def live_vaskon_test(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    try:
        result = vaskon_runtime.run_live_test()
        output = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        return HTMLResponse("<html><body style='font-family:-apple-system;padding:20px;background:#111;color:#eee'>"
            "<h1>GaiaOS Live VASKON Runtime Test</h1>"
            "<p>Every field below is an observation from this running carrier process.</p>"
            f"<pre style='white-space:pre-wrap'>{output}</pre>"
            "</body></html>")
    except Exception as exc:
        return _error_page("Live VASKON test failed", exc)

@app.post("/verify", operation_id="verificationRun")
async def verification_run(browser_request: Request):
    gaiaos_api._authorize_browser_session(browser_request)
    result = gaiaos_verification.run_verification()
    return _envelope("GAIAOS IMPLEMENTATION VERIFICATION", result)


# Normal browser chat behavior remains available for all non-test requests.
