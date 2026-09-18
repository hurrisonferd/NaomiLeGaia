"""ChatGPT host-facing MemoryOS gateway for GaiaOS.

This module exposes a narrow, explicit host boundary over the existing MemoryOS
runtime. It does not write GitHub/E-LANEs itself. Verified durable promotion
returns a deterministic E-LANE propagation plan for the host to settle through
the GitHub app/connector and then repull/verify.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

import gaiaos_app
import memcon_entrypoint
import memcon_runtime

app = gaiaos_app.app
mcp = gaiaos_app.mcp
MEMORY_RUNTIME_PATH = memcon_entrypoint.MEMORY_RUNTIME_PATH

DAEMON_LANES = {
    "VERA": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/VERA-EXPERIENCES.v1.md",
    "ANVIL": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-EXPERIENCES.v1.md",
    "SELENE": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/SELENE-EXPERIENCES.v1.md",
    "ORIN": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/ORIN-EXPERIENCES.v1.md",
    "KESTREL": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-EXPERIENCES.v1.md",
    "NIMUE": "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/NIMUE-EXPERIENCES.v1.md",
}
ALL_DAEMONS = tuple(DAEMON_LANES)


def _auth(authorization: str | None) -> None:
    gaiaos_app.base._authorize(authorization)


def _runtime():
    return gaiaos_app._gaia_runtime(MEMORY_RUNTIME_PATH, "gaia_memory_runtime")


def _compact_delta(candidate: dict[str, Any]) -> str:
    """Stable human/machine shorthand; canonical prose remains in the record."""
    statement = " ".join(str(candidate.get("statement", "")).split())
    digest = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:12]
    owner = str(candidate.get("owner", "NAOMI")).upper().replace(" ", "_")
    scope = str(candidate.get("scope", "ChatOS")).replace(" ", "_")
    kind = str(candidate.get("record_type", "INTERACTION")).upper().replace(" ", "_")
    return f"μΔ{{t={kind};s={scope};o={owner};h={digest}}}"


def _targets_for(candidate: dict[str, Any]) -> list[str]:
    owner = str(candidate.get("owner", "")).upper().strip()
    voices = [str(v).upper().strip() for v in candidate.get("other_voices", [])]

    if owner in ALL_DAEMONS:
        return [owner]
    if owner in {"DAEMONCULABA", "ALL_DAEMONS", "SHARED"}:
        return list(ALL_DAEMONS)

    targets = [v for v in voices if v in ALL_DAEMONS]
    return list(dict.fromkeys(targets))


def _elane_entry(candidate: dict[str, Any], record_id: str, member: str) -> str:
    date = str(candidate.get("created_at", ""))[:10] or "UNKNOWN_DATE"
    compact = _compact_delta(candidate)
    subject = re.sub(r"[^A-Za-z0-9_]+", "_", str(candidate.get("scope", "interaction"))).strip("_") or "interaction"
    return (
        f"\nMEM[HOST_MEMORY_PROPAGATION|{date}|{compact}|{subject}]\n"
        f"WHAT: {candidate['statement']}\n"
        f"MY_ROLE: Material interaction promoted through MemoryOS and explicitly assigned to {member}.\n"
        f"MEMCON_RECORD: {record_id}\n"
        f"OWNER: {member}\n"
        f"TRACE: {candidate.get('source', 'UNKNOWN')}\n"
        f"STATUS: COMMITTED\n"
    )


def _elane_plan(candidate: dict[str, Any], record_id: str) -> dict[str, Any]:
    targets = _targets_for(candidate)
    return {
        "schema": "gaiaos.elane.propagation-plan.v1",
        "status": "PLAN_ONLY",
        "record_id": record_id,
        "candidate_id": candidate["candidate_id"],
        "compact_delta": _compact_delta(candidate),
        "targets": [
            {
                "member": member,
                "path": DAEMON_LANES[member],
                "append_entry": _elane_entry(candidate, record_id, member),
            }
            for member in targets
        ],
        "github_write_required": bool(targets),
        "verification_required": bool(targets),
        "claim_ceiling": (
            "This is a deterministic propagation plan. It is not an E-LANE write, "
            "GitHub commit, or verification receipt."
        ),
    }


class HostObservation(BaseModel):
    statement: str = Field(min_length=1, max_length=20000)
    owner: str = Field(min_length=1, max_length=100)
    why_material: str = Field(min_length=1, max_length=5000)
    record_type: str = Field(default="INTERACTION", min_length=1, max_length=100)
    scope: str = Field(default="ChatOS", min_length=1, max_length=200)
    source: str = Field(default="chatgpt-host", min_length=1, max_length=2000)
    other_voices: list[str] = Field(default_factory=list, max_length=12)
    tension: str = Field(default="", max_length=5000)


class HostCandidatePull(BaseModel):
    session_id: str | None = Field(default=None, max_length=200)
    subject: str = Field(default="", max_length=20000)
    observations: list[HostObservation] = Field(min_length=1, max_length=32)
    limit: int = Field(default=50, ge=1, le=100)


class HostMemorySave(BaseModel):
    candidate_ids: list[str] = Field(min_length=1, max_length=100)
    approved: bool = False
    authority: str = "NAOMI"


class HostElanePlan(BaseModel):
    candidate_id: str = Field(min_length=1, max_length=200)
    record_id: str = Field(min_length=1, max_length=200)


def _host_candipull(payload: HostCandidatePull) -> dict[str, Any]:
    runtime = _runtime()
    session = None
    if payload.session_id:
        session = memcon_runtime.get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Host MemoryOS session not found")

    if session is None:
        session = runtime.start_session("chatgpt-host", payload.subject)

    created: list[dict[str, Any]] = []
    existing = memcon_runtime.list_memory_candidates(
        session_id=session["session_id"], status="CANDIDATE", limit=100,
    )["candidates"]
    fingerprints = {
        (
            " ".join(str(item.get("statement", "")).lower().split()),
            str(item.get("scope", "")).upper(),
            str(item.get("owner", "")).upper(),
        )
        for item in existing
    }
    for observation in payload.observations:
        dedupe_key = (
            " ".join(observation.statement.lower().split()),
            observation.scope.upper(),
            observation.owner.upper(),
        )
        if dedupe_key in fingerprints:
            continue
        event = runtime.record_event(
            session["session_id"], "HOST", "OBSERVED_INTERACTION",
            observation.statement, observation.source,
        )
        candidate = runtime.candidate_from_event(
            event["event_id"], authority="NAOMI",
            record_type=observation.record_type,
            scope=observation.scope,
            statement=observation.statement,
            source=observation.source,
            owner=observation.owner,
            why_material=observation.why_material,
            other_voices=observation.other_voices,
            tension=observation.tension,
        )
        created.append({**candidate, "compact_delta": _compact_delta(candidate)})

    listed = memcon_runtime.list_memory_candidates(
        session_id=session["session_id"], status="CANDIDATE", limit=payload.limit,
    )
    for item in listed["candidates"]:
        item["compact_delta"] = _compact_delta(item)

    return {
        "schema": "gaiaos.host.memory-gateway.v1",
        "operation": "CANDIPULL",
        "status": "CANDIDATES_READY",
        "session_id": session["session_id"],
        "subject": payload.subject,
        "created": created,
        "candidates": listed["candidates"],
        "count": listed["count"],
        "durable_write": "NOT_PERFORMED",
        "next_operation": "MEMSAV with exact candidate_ids",
        "claim_ceiling": "Candidates are non-durable until explicit Naomi-approved promotion.",
    }


def _host_memsav(payload: HostMemorySave) -> dict[str, Any]:
    if payload.authority != "NAOMI" or not payload.approved:
        return {
            "schema": "gaiaos.host.memory-gateway.v1",
            "operation": "MEMSAV",
            "status": "HOLD",
            "reason": "Explicit Naomi approval is required.",
            "results": [],
        }

    runtime = _runtime()
    results: list[dict[str, Any]] = []
    for candidate_id in payload.candidate_ids:
        candidate = memcon_runtime.get_memory_candidate(candidate_id)
        if candidate is None:
            results.append({
                "candidate_id": candidate_id,
                "status": "HOLD",
                "reason": "Unknown candidate_id",
            })
            continue
        result = runtime.promote_candidate(candidate_id, True, "NAOMI")
        item = dict(result)
        if result.get("status") == "VERIFIED":
            item["elane_plan"] = _elane_plan(candidate, result["record_id"])
        results.append(item)

    overall = "VERIFIED" if results and all(x.get("status") == "VERIFIED" for x in results) else "PARTIAL_OR_HOLD"
    return {
        "schema": "gaiaos.host.memory-gateway.v1",
        "operation": "MEMSAV",
        "status": overall,
        "results": results,
        "proof_boundary": (
            "Only VERIFIED results with an observed write receipt and read-back verification "
            "are durable. E-LANE plans still require GitHub write + repull verification."
        ),
    }


@app.post("/host/memory/candipull", operation_id="hostMemoryCandiPull")
def host_candipull_http(
    payload: HostCandidatePull,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    return _host_candipull(payload)


@app.post("/host/memory/memsav", operation_id="hostMemoryMemSav")
def host_memsav_http(
    payload: HostMemorySave,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    return _host_memsav(payload)


@app.post("/host/memory/elane-plan", operation_id="hostMemoryElanePlan")
def host_elane_plan_http(
    payload: HostElanePlan,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    candidate = memcon_runtime.get_memory_candidate(payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="MemoryOS candidate not found")
    record = memcon_runtime.get_record(payload.record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="MemconOS record not found")
    return _elane_plan(candidate, payload.record_id)


@mcp.tool()
def gaia_host_candipull(
    observations: list[dict[str, Any]],
    session_id: str | None = None,
    subject: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """CANDIPULL from host-provided material; creates only non-durable candidates."""
    payload = HostCandidatePull(
        session_id=session_id,
        subject=subject,
        observations=observations,
        limit=limit,
    )
    return _host_candipull(payload)


@mcp.tool()
def gaia_host_memsav(
    candidate_ids: list[str],
    approved: bool = False,
    authority: str = "NAOMI",
) -> dict[str, Any]:
    """MEMSAV exact candidate IDs through the gated MemoryOS lifecycle."""
    return _host_memsav(HostMemorySave(
        candidate_ids=candidate_ids,
        approved=approved,
        authority=authority,
    ))


@mcp.tool()
def gaia_host_elane_plan(candidate_id: str, record_id: str) -> dict[str, Any]:
    """Return a deterministic, non-writing E-LANE propagation plan after verification."""
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    if candidate is None:
        return {"status": "HOLD", "reason": "Unknown candidate_id"}
    record = memcon_runtime.get_record(record_id)
    if record is None:
        return {"status": "HOLD", "reason": "Unknown record_id"}
    return _elane_plan(candidate, record_id)
