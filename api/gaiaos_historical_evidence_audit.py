"""Stage 9J: bounded read-only diagnosis of *real* technical history.

Investigate exactly which part of the Stage7 historical prerequisite is absent:
verified directed owner SUPERSEDES, approved technical endpoints, an ACTIVE
successor, distinctive older-version marker, or historical governing state.

This is reconnaissance only. No historical record, edge or query is created;
no GALAXY retrieval/model inference, mode change, or production write occurs.
All returned diagnostics are redacted counts/finite reason codes. A candidate
is NOT historical retrieval proof and cannot unlock BIGBANG.
"""
from __future__ import annotations

from typing import Any

import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_mode as mode

SCHEMA = "gaiaos.galaxy.stage9j.historical-evidence-audit.v1"
FULL_HOLD = "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"

_RECORD_QUERY = (
    "SELECT record_id,authority,scope,statement,source,status "
    "FROM memory_records WHERE scope='MemoryOS' AND ("
    "lower(statement) LIKE '%//pw:preserve//%' OR "
    "lower(statement) LIKE '%power word preserve%' OR "
    "lower(statement) LIKE '%e-lane%' OR "
    "lower(statement) LIKE '%heatdeath%' OR "
    "lower(statement) LIKE '%galaxy%') "
    "ORDER BY created_at DESC LIMIT 101"
)
_EDGE_QUERY = (
    "SELECT source_record_id,target_record_id,authority "
    "FROM memory_relations "
    "WHERE status='VERIFIED' AND relation_type='SUPERSEDES' "
    "AND verified_at IS NOT NULL LIMIT 101"
)

_REASON_ACTION = {
    "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW":
        "Wait for or independently document a genuine owner-authorized historical revision; do not fabricate one.",
    "NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR":
        "Inspect real provenance and bounded eligibility of both ends of a verified owner supersession.",
    "NO_ACTIVE_APPROVED_SUCCESSOR":
        "Confirm the legitimately newer technical record is ACTIVE; do not mutate an unrelated record.",
    "NO_DISTINCT_HISTORICAL_MARKER":
        "Find an authentic old-version marker unique to a real superseded record; do not invent a marker.",
    "HISTORICAL_GOVERNING_STATE_UNVERIFIED":
        "Check governing-state read-only evidence for the old and current records.",
    "HISTORICAL_CANDIDATE_PREPARED_UNTESTED":
        "Run a separately authorized read-only six-case historical retrieval review; no release authorization is implied.",
}


def _shell(reason: str = "NOT_EVALUATED") -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "HOLD",
        "reason": reason,
        "next_action": _REASON_ACTION.get(reason, "Inspect the bounded read-only prerequisite before taking any action."),
        "scope": "MemoryOS",
        "window_limit": 100,
        "bounded_window_complete": False,
        "approved_technical_records_in_window": 0,
        "verified_owner_supersedes_in_window": 0,
        "approved_technical_pairs_in_window": 0,
        "active_successor_pairs_in_window": 0,
        "distinct_old_marker_pairs_in_window": 0,
        "governed_historical_pairs_in_window": 0,
        "historical_case_prepared": False,
        "historical_retrieval_tested": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "full_readiness_status": FULL_HOLD,
        "record_ids_disclosed": False,
        "statements_disclosed": False,
        "markers_disclosed": False,
        "sources_disclosed": False,
        "model_called": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
    }


def audit(runtime: Any) -> dict[str, Any]:
    """Compare only the same bounded owner-technical window as Stage7.

    Every count is a count within the complete 100-row window, NOT a
    declaration about unscanned records or the whole Turso database.
    """
    report = _shell()
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return {**report, "reason": "RUNTIME_NOT_INITIALIZED"}
    try:
        backend = runtime.storage_status()
        if (
            backend.get("backend") != "turso_libsql"
            or backend.get("remote_configured") is not True
        ):
            return {**report, "reason": "REMOTE_STORAGE_NOT_CONFIRMED"}
        control = mode.mode_status(runtime)
        if (
            control.get("schema") != mode.SCHEMA
            or control.get("effective_mode") != mode.HEATDEATH
            or control.get("bigbang_activation_enabled") is not False
        ):
            return {**report, "reason": "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED"}
        with runtime._db() as conn:
            records = runtime._fetchall_dicts(conn, _RECORD_QUERY)
            edges = runtime._fetchall_dicts(conn, _EDGE_QUERY)
    except Exception:
        return {**report, "reason": "BOUNDED_SOURCE_READ_FAILED"}
    if (
        not isinstance(records, list) or not isinstance(edges, list)
        or len(records) > 100 or len(edges) > 100
    ):
        return {**report, "reason": "BOUNDED_WINDOW_INCOMPLETE"}
    report["bounded_window_complete"] = True
    approved = {
        row["record_id"]: row
        for row in records
        if isinstance(row, dict)
        and isinstance(row.get("record_id"), str)
        and readiness._technical_topics(row)
    }
    report["approved_technical_records_in_window"] = len(approved)
    owner_edges = [
        edge for edge in edges
        if isinstance(edge, dict) and edge.get("authority") == "NAOMI"
    ]
    report["verified_owner_supersedes_in_window"] = len(owner_edges)
    if not owner_edges:
        return {
            **report, "reason": "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
            "next_action": _REASON_ACTION["NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW"],
        }

    matching_pairs = [
        (approved[edge["target_record_id"]],
         approved[edge["source_record_id"]])
        for edge in owner_edges
        if edge.get("source_record_id") in approved
        and edge.get("target_record_id") in approved
        and edge["source_record_id"] != edge["target_record_id"]
    ]
    report["approved_technical_pairs_in_window"] = len(matching_pairs)
    if not matching_pairs:
        code = "NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR"
        return {**report, "reason": code, "next_action": _REASON_ACTION[code]}
    active_pairs = [
        (old, new) for old, new in matching_pairs
        if new.get("status") == "ACTIVE"
    ]
    report["active_successor_pairs_in_window"] = len(active_pairs)
    if not active_pairs:
        code = "NO_ACTIVE_APPROVED_SUCCESSOR"
        return {**report, "reason": code, "next_action": _REASON_ACTION[code]}

    superseded_ids = {old["record_id"] for old, _ in active_pairs}
    current_statements = [
        row["statement"].casefold()
        for row in approved.values()
        if row.get("status") == "ACTIVE"
        and row["record_id"] not in superseded_ids
    ]
    unique_marker_pairs = []
    for old, new in active_pairs:
        for found in readiness._OLD_VERSION_MARKER.finditer(old["statement"]):
            marker = found.group(0).casefold()
            if marker in new["statement"].casefold():
                continue
            if any(marker in statement for statement in current_statements):
                continue
            unique_marker_pairs.append((old, new))
            break
    report["distinct_old_marker_pairs_in_window"] = len(unique_marker_pairs)
    if not unique_marker_pairs:
        code = "NO_DISTINCT_HISTORICAL_MARKER"
        return {**report, "reason": code, "next_action": _REASON_ACTION[code]}

    good = 0
    for old, new in unique_marker_pairs:
        try:
            old_state = runtime.galaxy_governing_state(old["record_id"])
            new_state = runtime.galaxy_governing_state(new["record_id"])
        except Exception:
            # No record/source/SQL details, and no false proof on partial reads.
            return {
                **report, "reason": "HISTORICAL_GOVERNING_STATE_READ_FAILED",
                "governed_historical_pairs_in_window": 0,
            }
        if (
            old_state.get("record_id") == old["record_id"]
            and old_state.get("state") == "HISTORICAL_SUPERSEDED"
            and old_state.get("current_default_eligible") is False
            and old_state.get("historical_retrieval_eligible") is True
            and new_state.get("record_id") == new["record_id"]
            and new_state.get("current_default_eligible") is True
        ):
            good += 1
    report["governed_historical_pairs_in_window"] = good
    if not good:
        code = "HISTORICAL_GOVERNING_STATE_UNVERIFIED"
        return {**report, "reason": code, "next_action": _REASON_ACTION[code]}

    # Independently cross-check the production Stage7 sample preparer; even
    # perfect raw evidence is not sufficient if its six-case policy says HOLD.
    prep = readiness.prepare_technical_cases(runtime)
    if (
        prep.get("preview", {}).get("status") != "PREPARED_UNTESTED"
        or prep.get("preview", {}).get("historical_cases_prepared") != 1
        or readiness._validate(prep.get("cases")) is not None
    ):
        return {
            **report, "reason": "STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED",
            "next_action": "Inspect the existing Stage7 case contract; never weaken its admission requirements.",
        }
    code = "HISTORICAL_CANDIDATE_PREPARED_UNTESTED"
    return {
        **report, "status": "CANDIDATE_PRESENT_UNTESTED",
        "reason": code, "next_action": _REASON_ACTION[code],
        "historical_case_prepared": True,
        "historical_retrieval_tested": False,
        "historical_retrieval_proven": False,
        "release_activated": False,
    }
