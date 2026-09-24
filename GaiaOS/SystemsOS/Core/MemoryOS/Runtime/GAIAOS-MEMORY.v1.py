"""Bounded GaiaOS conversation-to-memory lifecycle orchestrator."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import memcon_runtime
import gaiaos_memory_gateway

SCHEMA_VERSION = "gaiaos.memoryos.runtime.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _fingerprint(statement: str, scope: str, owner: str) -> str:
    raw = f"{owner}|{scope}|{' '.join(statement.lower().split())}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def start_session(source: str, subject: str = "") -> dict[str, Any]:
    session_id = _id("SESSION")
    memcon_runtime.initialize()
    memcon_runtime.create_session(session_id, source, subject)
    return {
        "schema": SCHEMA_VERSION,
        "session_id": session_id,
        "status": "OBSERVED",
        "source": source,
        "subject": subject,
    }


def record_event(session_id: str, actor: str, event_type: str, statement: str,
                 source: str, relation: str = "PART_OF") -> dict[str, Any]:
    event_id = _id("EVENT")
    memcon_runtime.create_session_event(
        event_id=event_id,
        session_id=session_id,
        actor=actor,
        event_type=event_type,
        statement=statement,
        source=source,
        relation=relation,
    )
    return {
        "schema": SCHEMA_VERSION,
        "event_id": event_id,
        "session_id": session_id,
        "status": "OBSERVED",
    }


def classify_event(event_id: str, record_type: str, scope: str, owner: str,
                   why_material: str, other_voices: list[str] | None = None,
                   tension: str = "") -> dict[str, Any]:
    event = memcon_runtime.get_session_event(event_id)
    if event is None:
        raise KeyError(event_id)
    return {
        "schema": SCHEMA_VERSION,
        "event_id": event_id,
        "record_type": record_type,
        "scope": scope,
        "owner": owner,
        "why_material": why_material,
        "other_voices": other_voices or [],
        "tension": tension,
        "status": "CLASSIFIED",
    }


def candidate_from_event(event_id: str, *, authority: str, record_type: str,
                         scope: str, statement: str, source: str, owner: str,
                         why_material: str, other_voices: list[str] | None = None,
                         tension: str = "") -> dict[str, Any]:
    event = memcon_runtime.get_session_event(event_id)
    if event is None:
        raise KeyError(event_id)
    fingerprint = _fingerprint(statement, scope, owner)
    existing = memcon_runtime.find_fingerprint(fingerprint)
    candidate_id = _id("CANDIDATE")
    candidate = {
        "candidate_id": candidate_id,
        "event_id": event_id,
        "authority": authority,
        "record_type": record_type,
        "scope": scope,
        "statement": statement,
        "source": source,
        "owner": owner,
        "why_material": why_material,
        "other_voices": other_voices or [],
        "tension": tension,
        "fingerprint": fingerprint,
        "duplicate_of": existing,
        "status": "CANDIDATE",
        "created_at": _now(),
    }
    memcon_runtime.create_memory_candidate(candidate)
    return {"schema": SCHEMA_VERSION, **candidate}


def promote_candidate(candidate_id: str, approved: bool, authority: str = "NAOMI") -> dict[str, Any]:
    candidate = memcon_runtime.get_memory_candidate(candidate_id)
    if candidate is None:
        raise KeyError(candidate_id)
    if authority != "NAOMI" or not approved:
        return {
            "schema": SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "status": "HOLD",
            "reason": "Explicit Naomi approval is required for durable promotion",
            "effect_authority": "NONE",
        }
    if candidate.get("duplicate_of"):
        return {
            "schema": SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "status": "HOLD",
            "reason": "Candidate matches an existing durable record",
            "duplicate_of": candidate["duplicate_of"],
            "effect_authority": "NONE",
        }
    result = memcon_runtime.write_record(
        authority="NAOMI",
        approved=True,
        record_type=candidate["record_type"],
        scope=candidate["scope"],
        statement=candidate["statement"],
        source=candidate["source"],
        notes=json.dumps({
            "memory_owner": candidate["owner"],
            "why_material": candidate["why_material"],
            "event_id": candidate["event_id"],
            "other_voices": candidate["other_voices"],
            "tension": candidate["tension"],
        }, sort_keys=True),
    )
    record_id = result["record"]["record_id"]
    memcon_runtime.mark_candidate(candidate_id, "COMMITTED", record_id)
    verification = memcon_runtime.get_record(record_id)
    verified = bool(verification and verification.get("record_id") == record_id
                    and verification.get("statement") == candidate["statement"])
    status = "VERIFIED" if verified else "COMMITTED"
    if verified:
        memcon_runtime.mark_candidate(candidate_id, "VERIFIED", record_id)
    return {
        "schema": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "status": status,
        "record_id": record_id,
        "write_receipt": result["receipt"],
        "verification": {"observed": verified, "record_id": record_id},
    }


def retrieve(query: str, scope: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Preserve the legacy retrieval envelope while exposing gated GALAXY evidence.

    No implicit GALAXY import or write path: the independent gateway owns
    read-mode selection and any request-local fallback. CANDIPULL/MEMSAV,
    six member E-LANES, receipts and mutation permissions are untouched.
    """
    packet = gaiaos_memory_gateway.read(memcon_runtime, query, scope, limit)
    return {
        "schema": SCHEMA_VERSION,
        "status": ("OBSERVED" if packet.get("retrieval") is not None else "HOLD"),
        "retrieval": packet.get("retrieval"),
        "galaxy_context": packet.get("galaxy_context"),
        "memory_gateway": {
            key: value for key, value in packet.items()
            if key not in ("retrieval", "galaxy_context")
        },
        "context_authority": "NONE",
        "retrieval_is_not_identity_adoption": True,
    }
