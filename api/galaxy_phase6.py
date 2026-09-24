"""GALAXY Phase 6: exact-fixture reversible lifecycle with append-only history.

Deployed after separate authorization. This primitive is not routed directly;
only the separately guarded finite Phase-6 control adapter may invoke it for the
exact fixture. Lifecycle metadata never rewrites source records or retrieval.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

VERSION = "galaxy.phase6.reversible-lifecycle.v1"
FIXTURE_RECORD_ID = "MEM-00b3fbfd4d73404f97a95c238596ab94"
STATES = ("ACTIVE", "BACKGROUND", "ARCHIVED", "COMPRESSED")
CONFIRMATIONS = {
    "BACKGROUND": "SET_GALAXY_PHASE6_BACKGROUND",
    "ARCHIVED": "SET_GALAXY_PHASE6_ARCHIVED",
    "COMPRESSED": "SET_GALAXY_PHASE6_COMPRESSED",
    "REACTIVATE": "REACTIVATE_GALAXY_PHASE6",
    "ROLLBACK": "ROLLBACK_GALAXY_PHASE6",
}
FORWARD = {"ACTIVE": "BACKGROUND", "BACKGROUND": "ARCHIVED",
           "ARCHIVED": "COMPRESSED"}
SHADOW_ATTENUATION = {
    "ACTIVE": "NONE", "BACKGROUND": "MILD",
    "ARCHIVED": "STRONG", "COMPRESSED": "STRONGEST",
}


def _events(runtime: Any, record_id: str) -> list[dict[str, Any]]:
    with runtime._db() as conn:
        return runtime._fetchall_dicts(
            conn,
            """SELECT * FROM memory_lifecycle_events
               WHERE record_id=? ORDER BY rowid ASC""", (record_id,),
        )


def inspect(runtime: Any, record_id: str = FIXTURE_RECORD_ID) -> dict[str, Any]:
    """Read-only canonical lifecycle, append-only history, and allowed next steps."""
    runtime.initialize()
    record_id = str(record_id or "").strip()
    record = runtime.get_record(record_id) if record_id else None
    if record is None:
        return {
            "schema": "gaiaos.galaxy.phase6-lifecycle-review.v1",
            "version": VERSION, "execution": "READ_ONLY", "status": "HOLD",
            "record_id": record_id, "hold_reasons": ["RECORD_NOT_FOUND"],
            "eligible_actions": {action: False for action in CONFIRMATIONS},
            "writes": 0, "production_retrieval_changed": False,
        }

    with runtime._db() as conn:
        lifecycle = runtime._fetchone_dict(
            conn, "SELECT * FROM memory_lifecycle WHERE record_id=?", (record_id,)
        )
        receipts = runtime._fetchall_dicts(
            conn,
            """SELECT receipt_id,operation,record_id,result FROM runtime_receipts
               WHERE record_id=? AND operation LIKE 'GALAXY_PHASE6_%'""",
            (record_id,),
        )
    receipt_index = {receipt["receipt_id"]: receipt for receipt in receipts}
    events = _events(runtime, record_id)
    current = str((lifecycle or {}).get("state") or "ACTIVE")
    holds: list[str] = []
    if record_id != FIXTURE_RECORD_ID:
        holds.append("OUTSIDE_EXACT_PHASE6_FIXTURE")
    if record.get("scope") != "MemoryOS" or record.get("status") != "ACTIVE":
        holds.append("RECORD_NOT_ACTIVE_MEMORYOS")
    if record.get("record_type") == "SYNTHESIS":
        holds.append("SYNTHESIS_LIFECYCLE_REQUIRES_SEPARATE_DESIGN")
    if current not in STATES:
        holds.append("UNKNOWN_LIFECYCLE_STATE")
    if lifecycle and not events:
        holds.append("EXISTING_LIFECYCLE_ROW_WITHOUT_EVENT_HISTORY")
    if events and not lifecycle:
        holds.append("EVENT_HISTORY_WITHOUT_LIFECYCLE_ROW")
    if len(events) > 64:
        holds.append("HISTORY_REVIEW_BOUND_EXCEEDED")

    previous = None
    expected_from = "ACTIVE"
    seen = set()
    for event in events:
        event_id = event.get("event_id")
        if (not event_id or event_id in seen
                or event.get("previous_event_id") != previous
                or event.get("from_state") != expected_from
                or event.get("to_state") not in STATES
                or event.get("authority") != "NAOMI"
                or not event.get("receipt_id")):
            holds.append("BROKEN_EVENT_HISTORY_CHAIN")
            break
        receipt = receipt_index.get(event["receipt_id"])
        if (not receipt
                or receipt.get("operation") != "GALAXY_PHASE6_" + str(event.get("action"))
                or receipt.get("result") != "SUCCESS"):
            holds.append("EVENT_RECEIPT_MISSING_OR_MISMATCHED")
            break
        try:
            legally_replayed = _target(
                str(event.get("action") or ""), expected_from, events[:len(seen)]
            )
        except ValueError:
            holds.append("ILLEGAL_RECORDED_TRANSITION")
            break
        if legally_replayed != event["to_state"]:
            holds.append("ILLEGAL_RECORDED_TRANSITION")
            break
        seen.add(event_id)
        previous = event_id
        expected_from = event["to_state"]
    if events and (current != expected_from
                   or (lifecycle or {}).get("receipt_id") != events[-1]["receipt_id"]):
        holds.append("LIFECYCLE_HEAD_NOT_AT_HISTORY_TIP")

    eligible = {action: False for action in CONFIRMATIONS}
    if not holds:
        if current in FORWARD:
            eligible[FORWARD[current]] = True
        if current in STATES[1:]:
            eligible["REACTIVATE"] = True
        if events:
            eligible["ROLLBACK"] = True

    return {
        "schema": "gaiaos.galaxy.phase6-lifecycle-review.v1",
        "version": VERSION, "execution": "READ_ONLY",
        "status": "PASS_READ_ONLY" if not holds else "HOLD",
        "record_id": record_id, "record": record, "lifecycle": lifecycle,
        "current_state": current, "latest_event_id": previous,
        "events": events, "event_count": len(events),
        "eligible_actions": eligible, "confirmations": dict(CONFIRMATIONS),
        "shadow_attenuation_preview": SHADOW_ATTENUATION.get(current),
        "hold_reasons": holds, "writes": 0, "physical_delete": False,
        "source_statement_changed": False, "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "Read-only review only; lifecycle effects and attenuation are not "
            "connected to production retrieval. PRUNABLE is reserved for Phase 7. "
            "No generic record mutation or generic lifecycle console is exposed; "
            "the separately authorized exact five-step browser control adapter may "
            "invoke this primitive only for the controlled fixture."
        ),
    }


def _target(operation: str, state: str, events: list[dict[str, Any]]) -> str:
    if operation in STATES[1:] and FORWARD.get(state) == operation:
        return operation
    if operation == "REACTIVATE" and state in STATES[1:]:
        return "ACTIVE"
    if operation == "ROLLBACK" and events:
        prior = str(events[-1].get("from_state") or "")
        if prior in STATES and prior != state:
            return prior
    raise ValueError("Transition is not eligible from the current state")


def execute(
    runtime: Any,
    operation: str,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
    expected_state: str,
    expected_latest_event_id: str | None,
    reason: str,
    record_id: str = FIXTURE_RECORD_ID,
) -> dict[str, Any]:
    """Internal exact-fixture one-step mutation, reachable only through the guarded finite control adapter."""
    operation = str(operation or "").strip().upper()
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Each lifecycle step requires separate Naomi approval")
    if operation not in CONFIRMATIONS or confirmation != CONFIRMATIONS[operation]:
        raise PermissionError("Exact operation-specific confirmation is required")
    if record_id != FIXTURE_RECORD_ID:
        raise ValueError("Phase 6 source slice permits only its exact fixture")
    reason = str(reason or "").strip()
    if not reason or len(reason) > 512:
        raise ValueError("Bounded, nonempty lifecycle reason (1..512) required")

    before = inspect(runtime, record_id)
    if before["status"] != "PASS_READ_ONLY" or not before["eligible_actions"][operation]:
        raise ValueError("Lifecycle review HOLD or operation ineligible")
    if (expected_state != before["current_state"]
            or expected_latest_event_id != before["latest_event_id"]):
        raise ValueError("Stale lifecycle review; repull before requesting a write")
    old = before["current_state"]
    target = _target(operation, old, before["events"])
    old_record = dict(before["record"])
    old_neighborhood = runtime.galaxy_record(record_id)
    created_at = runtime._now()
    event_id = "LIFE-" + uuid.uuid4().hex
    receipt_id = "MEMREC-" + uuid.uuid4().hex
    prior = before["latest_event_id"]

    # CAS on the previous state and receipt guards against competing requests.
    # The event + current state + receipt share one transaction.
    with runtime._db() as conn:
        live = runtime._fetchone_dict(
            conn, "SELECT * FROM memory_lifecycle WHERE record_id=?", (record_id,)
        )
        tip = runtime._fetchone_dict(
            conn,
            """SELECT * FROM memory_lifecycle_events
               WHERE record_id=? ORDER BY rowid DESC LIMIT 1""", (record_id,),
        )
        if ((live or {}).get("state") or "ACTIVE") != old:
            raise ValueError("Concurrent lifecycle state change; no write")
        if (tip or {}).get("event_id") != prior:
            raise ValueError("Concurrent history-tip change; no write")
        if not before["events"]:
            if live:
                raise ValueError("Untraced lifecycle state; no write")
            conn.execute(
                """INSERT INTO memory_lifecycle
                   (record_id,state,changed_at,reason,authority,receipt_id)
                   VALUES (?,?,?,?,?,?)""",
                (record_id, target, created_at, reason, "NAOMI", receipt_id),
            )
        else:
            cursor = conn.execute(
                """UPDATE memory_lifecycle
                   SET state=?,changed_at=?,reason=?,authority=?,receipt_id=?
                   WHERE record_id=? AND state=? AND receipt_id=?""",
                (target, created_at, reason, "NAOMI", receipt_id,
                 record_id, old, before["events"][-1]["receipt_id"]),
            )
            if cursor.rowcount != 1:
                raise ValueError("Lifecycle compare-and-swap conflict; no write")
        conn.execute(
            """INSERT INTO memory_lifecycle_events
               (event_id,record_id,previous_event_id,from_state,to_state,action,
                changed_at,reason,authority,receipt_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (event_id, record_id, prior, old, target, operation,
             created_at, reason, "NAOMI", receipt_id),
        )
        receipt = {
            "receipt_id": receipt_id, "operation": "GALAXY_PHASE6_" + operation,
            "record_id": record_id, "timestamp": created_at,
            "result": "SUCCESS", "event_id": event_id,
            "previous_event_id": prior, "from_state": old, "to_state": target,
            "reason": reason, "runtime": runtime.SCHEMA_VERSION,
        }
        conn.execute(
            """INSERT INTO runtime_receipts
               (receipt_id,operation,record_id,timestamp,result,detail)
               VALUES (?,?,?,?,?,?)""",
            (receipt_id, receipt["operation"], record_id, created_at, "SUCCESS",
             json.dumps(receipt, sort_keys=True)),
        )

    after = inspect(runtime, record_id)
    after_neighborhood = runtime.galaxy_record(record_id)
    with runtime._db() as conn:
        persisted_receipt = runtime._fetchone_dict(
            conn, "SELECT * FROM runtime_receipts WHERE receipt_id=?", (receipt_id,)
        )
    checks = {
        "current_state_readback": after["current_state"] == target,
        "single_event_appended": after["event_count"] == before["event_count"] + 1,
        "prior_history_unchanged": after["events"][:-1] == before["events"],
        "new_event_chain_valid": after["status"] == "PASS_READ_ONLY"
            and after["latest_event_id"] == event_id
            and after["events"][-1]["from_state"] == old
            and after["events"][-1]["to_state"] == target
            and after["events"][-1]["previous_event_id"] == prior,
        "receipt_committed": (persisted_receipt or {}).get("receipt_id") == receipt_id,
        "source_record_unchanged": after["record"] == old_record,
        "relations_and_gravity_unchanged": (
            (after_neighborhood or {}).get("relations") == (old_neighborhood or {}).get("relations")
            and (after_neighborhood or {}).get("gravity") == (old_neighborhood or {}).get("gravity")
            and (after_neighborhood or {}).get("importance") == (old_neighborhood or {}).get("importance")
        ),
    }
    return {
        "schema": "gaiaos.galaxy.phase6-lifecycle-receipt.v1", "version": VERSION,
        "operation": operation, "execution": "OBSERVED_RUNTIME_FOR_THIS_CALL",
        "status": "PASS_READBACK" if all(checks.values()) else "HOLD_READBACK",
        "record_id": record_id, "before_state": old, "after_state": target,
        "checks": checks, "receipt": receipt, "readback": after,
        "physical_delete": False, "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "Only the exact fixture and one current transaction were checked. "
            "The primitive is exposed only through the separately guarded finite "
            "Phase-6 control adapter; no generic lifecycle mutation route is registered. "
            "Restart persistence and production attenuation are not established by this receipt."
        ),
    }
