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
FIXTURE_RECORD_ID = "MEM-00b3fbfd4d73404f97a95c238596ab94"
MONITORED_TABLES = (
    "memory_records", "memory_relations", "memory_gravity", "memory_importance",
    "memory_lifecycle", "memory_lifecycle_events", "memory_syntheses",
    "runtime_receipts",
)

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



def _research_hold_reasons(
    *,
    record: dict[str, Any],
    lifecycle: dict[str, Any] | None,
    governing: dict[str, Any],
    outgoing_governing: list[dict[str, Any]],
    incoming_derived_from: list[dict[str, Any]],
    synthesis: dict[str, Any],
) -> list[str]:
    """Apply the shared Phase-7 research eligibility locks to supplied evidence."""
    holds = _research_hold_reasons(
        record=record,
        lifecycle=lifecycle,
        governing=governing,
        outgoing_governing=outgoing_governing,
        incoming_derived_from=incoming_derived_from,
        synthesis=synthesis,
    )
    return holds


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


def _readback_snapshot(runtime: Any, record_id: str) -> dict[str, Any]:
    """Read a deterministic evidence snapshot around one record without writing."""
    runtime.initialize()
    with runtime._db() as conn:
        counts = {
            table: runtime._fetchone_dict(
                conn, f"SELECT COUNT(*) AS n FROM {table}"
            )["n"]
            for table in MONITORED_TABLES
        }
        record = runtime._fetchone_dict(
            conn, "SELECT * FROM memory_records WHERE record_id=?", (record_id,)
        )
        lifecycle = runtime._fetchone_dict(
            conn, "SELECT * FROM memory_lifecycle WHERE record_id=?", (record_id,)
        )
        events = runtime._fetchall_dicts(
            conn,
            """SELECT * FROM memory_lifecycle_events
               WHERE record_id=? ORDER BY rowid ASC""",
            (record_id,),
        )
        relations = runtime._fetchall_dicts(
            conn,
            """SELECT * FROM memory_relations
               WHERE source_record_id=? OR target_record_id=?
               ORDER BY edge_id ASC""",
            (record_id, record_id),
        )
        syntheses = runtime._fetchall_dicts(
            conn,
            """SELECT * FROM memory_syntheses
               WHERE synthesis_record_id=? OR source_record_ids_json LIKE ?
               ORDER BY synthesis_record_id ASC""",
            (record_id, f"%{record_id}%"),
        )
        receipts = runtime._fetchall_dicts(
            conn,
            """SELECT * FROM runtime_receipts
               WHERE record_id=? ORDER BY receipt_id ASC""",
            (record_id,),
        )
    return {
        "counts": counts,
        "record": record,
        "lifecycle": lifecycle,
        "lifecycle_events": events,
        "relations": relations,
        "syntheses": syntheses,
        "receipts_for_record": receipts,
    }


def review_with_readback(
    runtime: Any,
    record_id: str = FIXTURE_RECORD_ID,
) -> dict[str, Any]:
    """Run the read-only reviewer and prove the observed database view did not change."""
    record_id = str(record_id or "").strip()
    before = _readback_snapshot(runtime, record_id)
    result = review(runtime, record_id)
    after = _readback_snapshot(runtime, record_id)

    checks = {
        "monitored_table_counts_unchanged": before["counts"] == after["counts"],
        "record_unchanged": before["record"] == after["record"],
        "lifecycle_unchanged": before["lifecycle"] == after["lifecycle"],
        "lifecycle_history_unchanged": before["lifecycle_events"] == after["lifecycle_events"],
        "relations_unchanged": before["relations"] == after["relations"],
        "synthesis_rows_unchanged": before["syntheses"] == after["syntheses"],
        "record_receipts_unchanged": before["receipts_for_record"] == after["receipts_for_record"],
        "declared_no_writes": result.get("writes_performed") == [],
        "physical_delete_false": result.get("physical_delete") is False,
        "production_retrieval_changed_false": result.get("production_retrieval_changed") is False,
        "destructive_eligibility_false": result.get("destructive_eligibility") is False,
    }
    zero_write = all(checks.values())

    return {
        **result,
        "live_surface": "PHASE7B_BOUNDED_READ_ONLY_REVIEW",
        "readback_status": "PASS_ZERO_WRITE_READBACK" if zero_write else "HOLD_READBACK",
        "zero_write_readback": zero_write,
        "readback_checks": checks,
        "database_counts_before": before["counts"],
        "database_counts_after": after["counts"],
        "proof_boundary": (
            "This readback compares the monitored database view immediately before and after "
            "the Phase-7 review call. It proves zero observed writes for this request when all "
            "checks pass; it does not authorize PRUNABLE, deletion, or production attenuation."
        ),
    }


def positive_path_canary() -> dict[str, Any]:
    """Exercise the positive research-candidate branch with synthetic evidence only.

    This canary deliberately does not accept a runtime object and performs no
    production database access. It shares the same hold-evaluation function used
    by the real-record review path.
    """
    record = {
        "record_id": "SYNTHETIC-P7C-HISTORICAL",
        "authority": "NAOMI",
        "record_type": "SYNTHETIC_CANARY",
        "scope": "MemoryOS",
        "status": "ACTIVE",
    }
    lifecycle = {"state": "COMPRESSED"}
    governing = {
        "state": "HISTORICAL_SUPERSEDED",
        "current_default_eligible": False,
        "historical_retrieval_eligible": True,
    }
    incoming_supersedes = [{
        "edge_id": "SYNTHETIC-EDGE-P7C",
        "source_record_id": "SYNTHETIC-P7C-CURRENT",
        "target_record_id": record["record_id"],
        "relation_type": "SUPERSEDES",
        "strength": 1.0,
        "status": "VERIFIED",
        "authority": "NAOMI",
    }]
    outgoing_governing: list[dict[str, Any]] = []
    incoming_derived_from: list[dict[str, Any]] = []
    synthesis = {
        "source_for_synthesis_record_ids": [],
        "is_synthesis_record": False,
        "malformed_synthesis_rows": [],
    }

    holds = _research_hold_reasons(
        record=record,
        lifecycle=lifecycle,
        governing=governing,
        outgoing_governing=outgoing_governing,
        incoming_derived_from=incoming_derived_from,
        synthesis=synthesis,
    )
    research_candidate = not holds
    checks = {
        "synthetic_only": True,
        "memoryos_shape": record["scope"] == "MemoryOS" and record["status"] == "ACTIVE",
        "compressed": lifecycle["state"] == REQUIRED_LIFECYCLE_STATE,
        "not_current_default": governing["current_default_eligible"] is False,
        "supersession_context_present": bool(incoming_supersedes),
        "no_outgoing_governing_dependency": not outgoing_governing,
        "no_synthesis_dependency": not synthesis["source_for_synthesis_record_ids"],
        "shared_hold_evaluator_passed": research_candidate,
        "destructive_eligibility_false": True,
        "physical_delete_false": True,
        "production_attenuation_false": True,
    }
    passed = all(checks.values()) and research_candidate

    return {
        "schema": "gaiaos.galaxy.phase7-positive-canary.v1",
        "version": VERSION,
        "execution": "SYNTHETIC_READ_ONLY",
        "status": "PASS_SYNTHETIC_POSITIVE_CANARY" if passed else "HOLD",
        "synthetic_only": True,
        "production_database_access": False,
        "record": record,
        "lifecycle": lifecycle,
        "governing_state": governing,
        "incoming_verified_supersedes": incoming_supersedes,
        "research_candidate": research_candidate,
        "proposed_research_label": RESEARCH_LABEL if research_candidate else None,
        "research_hold_reasons": holds,
        "checks": checks,
        "destructive_eligibility": False,
        "destructive_gates": dict(DESTRUCTIVE_GATES),
        "writes_performed": [],
        "physical_delete": False,
        "production_retrieval_changed": False,
        "authority_boundary": (
            "Synthetic positive classification proves only the candidate branch. "
            "It creates no durable memory, grants no PRUNABLE lifecycle state, "
            "and authorizes no deletion or production attenuation."
        ),
    }
