"""Stage 9N: privately classify why existing verified REVISES endpoints are ineligible.

This is a *diagnostic*, not an operator to create/verify SUPERSEDES. It scans
the unchanged Stage 7 100-record technical window and existing VERIFIED owner
REVISES edges. At most ten such edges may receive extra narrow parameterized
SELECTs for missing endpoints. Status, scope, authority, provenance and
technical-topic outcomes are exposed as finite per-role aggregates only;
record identifiers, statements, sources, markers, SQL and keys stay private.

Do not treat a REVISES relation as evidence that two memories supersede.
"""
from __future__ import annotations

from typing import Any

import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as historical
import gaiaos_memory_mode as mode
import gaiaos_revision_lineage_scout as lineage

SCHEMA = "gaiaos.galaxy.stage9n.revision-endpoint-diagnostic.v1"
MAX_EDGES = 10
REASONS = (
    "ELIGIBLE_REAL_TECHNICAL",
    "MISSING_RECORD",
    "WRONG_SCOPE",
    "NON_OWNER_AUTHORITY",
    "EXCLUDED_PROVENANCE",
    "NON_TECHNICAL_STATEMENT",
    "OUTSIDE_BOUNDED_WINDOW",
    "SELF_REFERENTIAL_REVISION",
)
_TARGETED_RECORD = (
    "SELECT record_id,authority,scope,statement,source,status "
    "FROM memory_records WHERE record_id = ? LIMIT 2"
)
_FULL_HOLD = "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"


def _base(reason: str, *, checked: int = 0) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD", "reason": reason,
        "window_complete": False, "endpoint_scan_complete": False,
        "owner_revision_edges_checked": checked,
        "older_endpoint_reasons": {},
        "newer_endpoint_reasons": {},
        "lead_owner_review_required": False,
        "relation_created": False,
        "lead_is_a_supersession": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "full_readiness_status": _FULL_HOLD,
        "record_ids_disclosed": False, "statements_disclosed": False,
        "sources_disclosed": False, "markers_disclosed": False,
        "model_called": False, "writes_performed": [],
        "e_lanes_modified": False, "release_activated": False,
    }


def _category(row: Any, *, in_window: bool) -> str:
    """Explain only the first existing source-eligibility barrier."""
    if not isinstance(row, dict):
        return "MISSING_RECORD"
    if row.get("scope") != "MemoryOS":
        return "WRONG_SCOPE"
    if row.get("authority") != "NAOMI":
        return "NON_OWNER_AUTHORITY"
    if any(
        token in str(row.get("source") or "").casefold()
        for token in readiness._EXCLUDED_SOURCES
    ):
        return "EXCLUDED_PROVENANCE"
    statement = row.get("statement")
    if (
        not isinstance(statement, str)
        or not any(
            phrase in statement.casefold()
            for patterns in readiness.TECHNICAL_TOPICS.values()
            for phrase in patterns
        )
    ):
        return "NON_TECHNICAL_STATEMENT"
    if not in_window:
        return "OUTSIDE_BOUNDED_WINDOW"
    if not readiness._technical_topics(row):
        return "NON_TECHNICAL_STATEMENT"
    return "ELIGIBLE_REAL_TECHNICAL"


def audit(
    runtime: Any, *,
    expected_verified_owner_edges: int,
    expected_approved_records: int,
) -> dict[str, Any]:
    """Classify at most ten existing owner edges on the unchanged bounded scan.

    Both expected counts come from the immediately preceding owner-invoked
    Stage 9M report; a changed source between checks fails closed.
    """
    if (
        type(expected_verified_owner_edges) is not int
        or not 1 <= expected_verified_owner_edges <= 100
        or type(expected_approved_records) is not int
        or not 0 <= expected_approved_records <= 100
    ):
        return _base("INVALID_PARENT_SAMPLE")
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return _base("RUNTIME_NOT_INITIALIZED")
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
        with runtime._db() as conn:
            window = runtime._fetchall_dicts(conn, historical._RECORD_QUERY)
            revisions = runtime._fetchall_dicts(conn, lineage.EDGE_QUERY)
            if (
                not isinstance(window, list)
                or not isinstance(revisions, list)
                or len(window) > 100 or len(revisions) > 100
            ):
                return _base("BOUNDED_WINDOW_INCOMPLETE")
            window_by_id = {
                row["record_id"]: row
                for row in window
                if isinstance(row, dict)
                and isinstance(row.get("record_id"), str)
            }
            approved = {
                rid: row for rid, row in window_by_id.items()
                if readiness._technical_topics(row)
            }
            owner = [
                edge for edge in revisions
                if isinstance(edge, dict) and edge.get("authority") == "NAOMI"
            ]
            if (
                len(owner) != expected_verified_owner_edges
                or len(approved) != expected_approved_records
            ):
                return _base("PARENT_SAMPLE_CHANGED")
            if len(owner) > MAX_EDGES:
                return _base("TOO_MANY_EDGES_FOR_BOUNDED_DIAGNOSIS")
            ids = set()
            for edge in owner:
                old_id = edge.get("target_record_id")
                new_id = edge.get("source_record_id")
                if (
                    not isinstance(old_id, str) or not old_id
                    or not isinstance(new_id, str) or not new_id
                ):
                    return _base("MALFORMED_VERIFIED_EDGE")
                ids.update((old_id, new_id))
            # One narrow, read-only lookup for each endpoint outside the
            # *already* scanned Stage 7 source population (<=20 unique IDs).
            endpoint_rows = dict(window_by_id)
            for rid in ids - window_by_id.keys():
                rows = runtime._fetchall_dicts(conn, _TARGETED_RECORD, (rid,))
                if not isinstance(rows, list) or len(rows) > 1:
                    return _base("TARGETED_ENDPOINT_READ_UNVERIFIED")
                if rows:
                    row = rows[0]
                    if row.get("record_id") != rid:
                        return _base("TARGETED_ENDPOINT_READ_UNVERIFIED")
                    endpoint_rows[rid] = row
        after = mode.mode_status(runtime)
    except Exception:
        return _base("BOUNDED_ENDPOINT_READ_FAILED")

    if (
        after.get("schema") != mode.SCHEMA
        or after.get("effective_mode") != mode.HEATDEATH
        or after.get("bigbang_activation_enabled") is not False
        or any(
            before.get(key) != after.get(key)
            for key in ("effective_mode", "configured_mode", "control_version")
        )
    ):
        return _base("RELEASE_LOCK_CHANGED_OR_UNVERIFIED")

    older = {reason: 0 for reason in REASONS}
    newer = {reason: 0 for reason in REASONS}
    for edge in owner:
        old_id = edge["target_record_id"]
        new_id = edge["source_record_id"]
        if old_id == new_id:
            old_reason = new_reason = "SELF_REFERENTIAL_REVISION"
        else:
            old_reason = _category(
                endpoint_rows.get(old_id), in_window=old_id in window_by_id
            )
            new_reason = _category(
                endpoint_rows.get(new_id), in_window=new_id in window_by_id
            )
        older[old_reason] += 1
        newer[new_reason] += 1
    older = {reason: count for reason, count in older.items() if count}
    newer = {reason: count for reason, count in newer.items() if count}
    if (
        older.get("ELIGIBLE_REAL_TECHNICAL", 0) == len(owner)
        and newer.get("ELIGIBLE_REAL_TECHNICAL", 0) == len(owner)
    ):
        return _base("PARENT_SCOUT_DISAGREEMENT")
    report = _base("INELIGIBLE_ENDPOINTS_CLASSIFIED", checked=len(owner))
    report.update({
        "status": "CLASSIFIED_EXISTING_REVISION_ONLY",
        "window_complete": True,
        "endpoint_scan_complete": True,
        "older_endpoint_reasons": older,
        "newer_endpoint_reasons": newer,
        "lead_owner_review_required": True,
    })
    return report
