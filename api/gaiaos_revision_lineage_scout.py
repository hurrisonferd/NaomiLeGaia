"""Stage 9M: read-only scout for existing *REVISES* relationships.

A verified REVISES edge is a possible lead for human historical review,
never a SUPERSEDES edge and never proof of supersession. There are no writes,
models, invented memories, change of governance, or automatic promotions.
The 100-row windows and source filter match the existing Stage7 preflight.
"""
from __future__ import annotations

from typing import Any

import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as historical
import gaiaos_memory_mode as mode

SCHEMA = "gaiaos.galaxy.stage9m.revision-lineage-scout.v1"
EDGE_QUERY = (
    "SELECT source_record_id,target_record_id,authority "
    "FROM memory_relations WHERE status='VERIFIED' "
    "AND relation_type='REVISES' AND verified_at IS NOT NULL "
    "LIMIT 101"
)
_REASONS = {
    "RUNTIME_NOT_INITIALIZED": "MemoryOS runtime is not initialized.",
    "REMOTE_STORAGE_NOT_CONFIRMED": "Remote MemoryOS configuration is unverified.",
    "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED": "The HEATDEATH release lock could not be verified.",
    "BOUNDED_SOURCE_READ_FAILED": "The read-only source scan failed.",
    "BOUNDED_WINDOW_INCOMPLETE": "The bounded scan is incomplete. No absence is inferred.",
    "NO_VERIFIED_OWNER_REVISES_IN_WINDOW": "No verified owner REVISES relation exists in the audited window.",
    "NO_APPROVED_OWNER_REVISES_PAIR": "Verified owner revisions do not connect two approved real technical memories.",
    "NO_ACTIVE_NEWER_RECORD": "No eligible approved revision has an ACTIVE newer record.",
    "NO_DISTINCT_OLD_VERSION_MARKER": "No approved revision contains a distinctive old-version marker.",
    "REVISES_LEADS_REQUIRE_OWNER_REVIEW": "A possible authentic revision exists. Owner review is required before any supersession.",
    "RELEASE_LOCK_CHANGED_OR_UNVERIFIED": "The protected release state changed or could not be reverified.",
}


def _base(reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD",
        "reason": reason, "explanation": _REASONS[reason],
        "window_complete": False, "approved_technical_records_in_window": 0,
        "verified_owner_revises_in_window": 0,
        "approved_owner_revision_pairs_in_window": 0,
        "active_successor_revision_pairs_in_window": 0,
        "distinct_old_marker_leads_in_window": 0,
        "lead_owner_review_required": False,
        "lead_is_a_supersession": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "full_readiness_status": "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
        "record_ids_disclosed": False, "statements_disclosed": False,
        "markers_disclosed": False, "sources_disclosed": False,
        "model_called": False, "writes_performed": [],
        "e_lanes_modified": False, "release_activated": False,
    }


def scout(runtime: Any) -> dict[str, Any]:
    report = _base("RUNTIME_NOT_INITIALIZED")
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return report
    try:
        storage = runtime.storage_status()
        before = mode.mode_status(runtime)
        if (
            storage.get("backend") != "turso_libsql"
            or storage.get("remote_configured") is not True
        ):
            return _base("REMOTE_STORAGE_NOT_CONFIRMED")
        if (
            before.get("schema") != mode.SCHEMA
            or before.get("effective_mode") != mode.HEATDEATH
            or before.get("bigbang_activation_enabled") is not False
        ):
            return _base("HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")
        with runtime._db() as connection:
            records = runtime._fetchall_dicts(
                connection, historical._RECORD_QUERY,
            )
            revisions = runtime._fetchall_dicts(connection, EDGE_QUERY)
        after = mode.mode_status(runtime)
        if (
            after.get("schema") != mode.SCHEMA
            or after.get("effective_mode") != mode.HEATDEATH
            or after.get("bigbang_activation_enabled") is not False
            or any(before.get(key) != after.get(key)
                   for key in ("effective_mode", "configured_mode", "control_version"))
        ):
            return _base("RELEASE_LOCK_CHANGED_OR_UNVERIFIED")
    except Exception:
        return _base("BOUNDED_SOURCE_READ_FAILED")
    if (
        not isinstance(records, list) or not isinstance(revisions, list)
        or len(records) > 100 or len(revisions) > 100
    ):
        return _base("BOUNDED_WINDOW_INCOMPLETE")
    report = _base("NO_VERIFIED_OWNER_REVISES_IN_WINDOW")
    report["window_complete"] = True
    approved = {
        record["record_id"]: record for record in records
        if isinstance(record, dict)
        and isinstance(record.get("record_id"), str)
        and readiness._technical_topics(record)
    }
    report["approved_technical_records_in_window"] = len(approved)
    owner = [
        edge for edge in revisions
        if isinstance(edge, dict) and edge.get("authority") == "NAOMI"
    ]
    report["verified_owner_revises_in_window"] = len(owner)
    if not owner:
        return report
    pairs = [
        (approved[edge["target_record_id"]],
         approved[edge["source_record_id"]])
        for edge in owner
        if edge.get("source_record_id") in approved
        and edge.get("target_record_id") in approved
        and edge["source_record_id"] != edge["target_record_id"]
    ]
    report["approved_owner_revision_pairs_in_window"] = len(pairs)
    if not pairs:
        report["reason"] = "NO_APPROVED_OWNER_REVISES_PAIR"
    else:
        active = [
            (old, new) for old, new in pairs
            if new.get("status") == "ACTIVE"
        ]
        report["active_successor_revision_pairs_in_window"] = len(active)
        if not active:
            report["reason"] = "NO_ACTIVE_NEWER_RECORD"
        else:
            current_statements = [
                row["statement"].casefold()
                for row in approved.values() if row.get("status") == "ACTIVE"
            ]
            leads = 0
            for old, new in active:
                old_text, newer_text = old["statement"], new["statement"].casefold()
                for found in readiness._OLD_VERSION_MARKER.finditer(old_text):
                    marker = found.group(0).casefold()
                    if (
                        marker not in newer_text
                        and not any(marker in text for text in current_statements
                                    if text != old_text.casefold())
                    ):
                        leads += 1
                        break
            report["distinct_old_marker_leads_in_window"] = leads
            if leads:
                report["status"] = "LEADS_FOUND_OWNER_REVIEW_ONLY"
                report["reason"] = "REVISES_LEADS_REQUIRE_OWNER_REVIEW"
                report["lead_owner_review_required"] = True
            else:
                report["reason"] = "NO_DISTINCT_OLD_VERSION_MARKER"
    report["explanation"] = _REASONS[report["reason"]]
    return report
