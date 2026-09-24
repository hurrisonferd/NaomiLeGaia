"""GALAXY Phase 7A read-only pruning research.

This module classifies bounded research candidates only.
It does not mutate lifecycle state, delete records, or alter production retrieval.
"""
from __future__ import annotations

import json
from typing import Any

VERSION = "galaxy.phase7.pruning-research.v1"
SCHEMA = "gaiaos.galaxy.phase7-pruning-research.v1"

PHYSICAL_PRUNING_ENABLED = False
PRODUCTION_ATTENUATION_ENABLED = False
RESEARCH_LABEL = "PRUNABLE_RESEARCH_ONLY"
REQUIRED_LIFECYCLE_STATE = "COMPRESSED"

DESTRUCTIVE_GATES = {
    "tombstone_protocol_implemented": False,
    "destructive_restore_proven": False,
    "destructive_canary_proven": False,
    "naomi_destructive_policy_authorized": False,
    "physical_pruning_enabled": PHYSICAL_PRUNING_ENABLED,
    "production_attenuation_enabled": PRODUCTION_ATTENUATION_ENABLED,
}


def _synthesis_dependencies(runtime: Any, record_id: str) -> dict[str, Any]:
    runtime.initialize()
    with runtime._db() as conn:
        rows = runtime._fetchall_dicts(
            conn,
            """SELECT synthesis_record_id,source_record_ids_json,method,confidence,
                      created_at,authority
               FROM memory_syntheses
               ORDER BY created_at ASC""",
        )

    source_for: list[str] = []
    is_synthesis = False
    malformed_rows: list[str] = []
    for row in rows:
        synthesis_id = str(row.get("synthesis_record_id") or "")
        if synthesis_id == record_id:
            is_synthesis = True
        try:
            source_ids = json.loads(row.get("source_record_ids_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            malformed_rows.append(synthesis_id)
            continue
        if record_id in [str(item) for item in source_ids]:
            source_for.append(synthesis_id)

    return {
        "source_for_synthesis_record_ids": source_for,
        "is_synthesis_record": is_synthesis,
        "malformed_synthesis_rows": malformed_rows,
    }


def review(runtime: Any, record_id: str) -> dict[str, Any]:
    """Return a zero-write Phase-7 pruning research review for one record."""
    record_id = str(record_id or "").strip()
    if not record_id:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "execution": "READ_ONLY",
            "status": "HOLD",
            "record_id": record_id,
            "research_candidate": False,
            "research_hold_reasons": ["RECORD_ID_REQUIRED"],
            "destructive_eligibility": False,
            "destructive_gates": dict(DESTRUCTIVE_GATES),
            "writes_performed": [],
            "physical_delete": False,
            "production_retrieval_changed": False,
        }

    record = runtime.get_record(record_id)
    if record is None:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "execution": "READ_ONLY",
            "status": "HOLD",
            "record_id": record_id,
            "research_candidate": False,
            "research_hold_reasons": ["RECORD_NOT_FOUND"],
            "destructive_eligibility": False,
            "destructive_gates": dict(DESTRUCTIVE_GATES),
            "writes_performed": [],
            "physical_delete": False,
            "production_retrieval_changed": False,
        }

    neighborhood = runtime.galaxy_record(record_id) or {}
    lifecycle = neighborhood.get("lifecycle")
    governing = runtime.galaxy_governing_state(record_id)
    relations = list(neighborhood.get("relations") or [])
    verified = [edge for edge in relations if str(edge.get("status")) == "VERIFIED"]

    outgoing_governing = [
        edge for edge in verified
        if str(edge.get("source_record_id")) == record_id
        and str(edge.get("relation_type")) in {"REVISES", "SUPERSEDES"}
    ]
    incoming_supersedes = [
        edge for edge in verified
        if str(edge.get("target_record_id")) == record_id
        and str(edge.get("relation_type")) == "SUPERSEDES"
    ]
    incoming_derived_from = [
        edge for edge in verified
        if str(edge.get("target_record_id")) == record_id
        and str(edge.get("relation_type")) == "DERIVED_FROM"
    ]

    synthesis = _synthesis_dependencies(runtime, record_id)

    holds: list[str] = []
    if str(record.get("scope") or "") != "MemoryOS":
        holds.append("NOT_MEMORYOS_SCOPE")
    if str(record.get("status") or "") != "ACTIVE":
        holds.append("MEMORYOS_RECORD_NOT_ACTIVE")
    if not lifecycle or str(lifecycle.get("state") or "") != REQUIRED_LIFECYCLE_STATE:
        holds.append("LIFECYCLE_NOT_COMPRESSED")
    if bool(governing.get("current_default_eligible")):
        holds.append("CURRENT_DEFAULT_ELIGIBLE")
    if outgoing_governing:
        holds.append("GOVERNS_OTHER_RECORDS")
    if incoming_derived_from or synthesis["source_for_synthesis_record_ids"]:
        holds.append("SYNTHESIS_PROVENANCE_DEPENDENCY")
    if synthesis["is_synthesis_record"]:
        holds.append("SYNTHESIS_RECORD_REQUIRES_SEPARATE_POLICY")
    if synthesis["malformed_synthesis_rows"]:
        holds.append("MALFORMED_SYNTHESIS_PROVENANCE")

    research_candidate = not holds
    status = "PASS_READ_ONLY_RESEARCH_CANDIDATE" if research_candidate else "HOLD"

    return {
        "schema": SCHEMA,
        "version": VERSION,
        "execution": "READ_ONLY",
        "status": status,
        "record_id": record_id,
        "record": record,
        "lifecycle": lifecycle,
        "governing_state": governing,
        "verified_relation_count": len(verified),
        "incoming_verified_supersedes": incoming_supersedes,
        "outgoing_verified_governing_relations": outgoing_governing,
        "incoming_verified_derived_from": incoming_derived_from,
        "synthesis_dependencies": synthesis,
        "research_candidate": research_candidate,
        "proposed_research_label": RESEARCH_LABEL if research_candidate else None,
        "research_hold_reasons": holds,
        "destructive_eligibility": False,
        "destructive_gates": dict(DESTRUCTIVE_GATES),
        "writes_performed": [],
        "physical_delete": False,
        "production_retrieval_changed": False,
        "authority_boundary": (
            "Phase 7A may identify a research candidate only. "
            "It cannot set PRUNABLE, delete evidence, attenuate production retrieval, "
            "or infer destructive authority."
        ),
    }
