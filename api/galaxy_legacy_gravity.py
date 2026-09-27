"""Release-locked, read-only inventory of pre-GALAXY memory gravity.

This module is an optional BIGBANG research component, never an import of the
HEATDEATH writer or retrieval path. Neither function changes Turso, lifecycle,
owner importance, the six E-LANES, or the mode controller.
"""
from __future__ import annotations

import math
from typing import Any

SCHEMA = "gaiaos.galaxy.legacy-gravity-audit.v1"
MAX_BATCH = 50


def _valid_score(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0.0 <= value <= 1.0
    )


def resolve_for_retrieval(runtime: Any, record_id: str,
                          stored: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve current or historical gravity without treating absent as zero.

    An unscored or stale record gets a read-only preview using the active model.
    This function is invoked ONLY from the optional GALAXY reader. Never import
    or invoke it from HEATDEATH, nor use it for candidate admission.
    """
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("record_id must be nonempty")
    expected = getattr(runtime, "GALAXY_SCORE_VERSION", None)
    if expected is not None and (not isinstance(expected, str) or not expected):
        raise ValueError("invalid active gravity model version")
    stored = stored or {}
    old_version = stored.get("score_version")
    current = bool(stored) and (expected is None or old_version == expected)
    if current:
        value = stored.get("gravity_score")
        if not _valid_score(value):
            raise ValueError("invalid stored gravity score")
        return {
            "score": float(value),
            "basis": "STORED",
            "score_version": old_version,
            "backfill_required": False,
        }
    preview = runtime.galaxy_gravity_preview(record_id)
    if not isinstance(preview, dict):
        raise ValueError("gravity preview unavailable")
    value = preview.get("gravity_score")
    version = preview.get("score_version")
    if not _valid_score(value) or (expected is not None and version != expected):
        raise ValueError("gravity preview invalid or not at active model version")
    return {
        "score": float(value),
        "basis": "STALE_SCORE_PREVIEW" if stored else "READ_ONLY_PREVIEW",
        "score_version": version,
        "prior_score_version": old_version,
        "backfill_required": True,
    }


def audit_historical_gravity(runtime: Any, *, scope: str | None = "MemoryOS",
                             after_record_id: str | None = None,
                             batch_size: int = 25) -> dict[str, Any]:
    """Inventory one bounded stable-ID page, preview gaps, perform zero writes.

    This is an internal research function, not a route and not a migration.
    External archives require a separately approved, provenance-bearing import.
    The cursor is the last successfully *inspected* durable record ID.
    """
    base = {
        "schema": SCHEMA, "scope": scope, "execution": "READ_ONLY",
        "writes_performed": [], "e_lanes_modified": False,
        "mode_control_modified": False, "production_retrieval_changed": False,
        "source_imported": False,
    }
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return {**base, "status": "HOLD_RUNTIME_NOT_INITIALIZED"}
    if (scope is not None and (not isinstance(scope, str) or not scope.strip())):
        return {**base, "status": "HOLD_SCOPE_INVALID"}
    if after_record_id is not None and (
        not isinstance(after_record_id, str) or not after_record_id.strip()
        or len(after_record_id) > 200
    ):
        return {**base, "status": "HOLD_CURSOR_INVALID"}
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 1 <= batch_size <= MAX_BATCH:
        return {**base, "status": "HOLD_BATCH_INVALID"}
    expected = getattr(runtime, "GALAXY_SCORE_VERSION", None)
    if not isinstance(expected, str) or not expected:
        return {**base, "status": "HOLD_MODEL_VERSION_UNAVAILABLE"}
    try:
        conditions = []
        args: list[Any] = []
        if after_record_id is not None:
            conditions.append("r.record_id > ?")
            args.append(after_record_id)
        if scope is not None:
            conditions.append("r.scope = ?")
            args.append(scope)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = (
            "SELECT r.record_id, g.gravity_score, g.score_version "
            "FROM memory_records r LEFT JOIN memory_gravity g "
            "ON g.record_id = r.record_id" + where +
            " ORDER BY r.record_id LIMIT ?"
        )
        args.append(batch_size + 1)
        with runtime._db() as conn:
            cursor = conn.execute(sql, tuple(args))
            names = [
                col[0] if isinstance(col, (tuple, list)) else col.name
                for col in cursor.description
            ]
            raw_rows = cursor.fetchall()
        rows = [
            dict(row) if hasattr(row, "keys")
            else dict(zip(names, row))
            for row in raw_rows
        ]
    except Exception as exc:
        return {**base, "status": "HOLD_STORAGE_UNAVAILABLE",
                "error_type": type(exc).__name__}

    has_more = len(rows) > batch_size
    rows = rows[:batch_size]
    inspected = []
    counts = {"CURRENT": 0, "MISSING": 0, "STALE": 0, "HOLD": 0}
    for row in rows:
        rid = row["record_id"]
        prior_version = row["score_version"]
        prior_score = row["gravity_score"]
        if prior_version is None and prior_score is None:
            kind = "MISSING"
        elif prior_version != expected:
            kind = "STALE"
        else:
            kind = "CURRENT"
        item = {"record_id": rid, "gravity_status": kind,
                "stored_version": prior_version,
                "active_version": expected}
        if kind == "CURRENT":
            if not _valid_score(prior_score):
                item["gravity_status"] = "HOLD"
                item["reason"] = "INVALID_CURRENT_SCORE"
        else:
            try:
                preview = resolve_for_retrieval(
                    runtime, rid,
                    {"gravity_score": prior_score, "score_version": prior_version}
                    if kind == "STALE" else None,
                )
                item["preview_score"] = preview["score"]
                item["preview_version"] = preview["score_version"]
                item["backfill_candidate"] = True
            except Exception as exc:
                item["gravity_status"] = "HOLD"
                item["reason"] = "PREVIEW_UNAVAILABLE"
                item["error_type"] = type(exc).__name__
        counts[item["gravity_status"]] += 1
        inspected.append(item)
    return {
        **base,
        "status": "PARTIAL_HOLD" if counts["HOLD"] else "PASS_READ_ONLY_AUDIT",
        "active_score_version": expected, "inspected": inspected,
        "counts": counts, "has_more": has_more,
        "next_cursor": rows[-1]["record_id"] if rows and has_more else None,
        "backfill_candidate_count": counts["MISSING"] + counts["STALE"],
        "proof_boundary": "Only existing durable records were inspected. No score was stored.",
    }
