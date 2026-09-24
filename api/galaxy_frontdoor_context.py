"""Opt-in read-only GALAXY/MemoryOS evidence lane for GaiaOS's primary front door.

This integration begins with the existing legacy scoped retrieval control.
It does not turn on Phase-3 production weighting, merge DictionaryOS context
with stored memories, or change Council authority. It never writes receipts.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "gaiaos.galaxy.frontdoor-memory-context.v1"
VERSION = "galaxy.frontdoor.shadow-legacy-read.v1"
MAX_RECORDS = 6


def _hold(reason: str, *, query: str, limit: int, error_type: str | None = None) -> dict[str, Any]:
    result = {
        "schema": SCHEMA,
        "version": VERSION,
        "execution": "READ_ONLY",
        "status": reason,
        "query": query,
        "scope": "MemoryOS",
        "limit": limit,
        "records": [],
        "count": 0,
        "ranking": "LEGACY_UNWEIGHTED_CONTROL",
        "galaxy_weighting_applied": False,
        "production_retrieval_changed": False,
        "writes_performed": [],
        "memory_context_authority": "NONE",
        "proof_boundary": (
            "An opt-in legacy baseline read is not semantic relevance or automatic "
            "adoption into the Council; an unavailable or inconsistent source HOLDS."
        ),
    }
    if error_type is not None:
        result["error_type"] = error_type
    return result


def preview(runtime: Any, query: str, limit: int = 3) -> dict[str, Any]:
    """Read up to six existing MemoryOS records with provenance and governing state.

    No broad all-record fallback, cross-member scope, proposal, promotion,
    production pilot activation, or recording of this request is permitted.
    """
    if not isinstance(query, str):
        return _hold("HOLD_QUERY_INVALID", query="", limit=0)
    query = query.strip()
    if not query or len(query) > 20000:
        return _hold("HOLD_QUERY_INVALID", query=query[:20000], limit=0)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RECORDS:
        return _hold("HOLD_LIMIT_INVALID", query=query, limit=0)
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return _hold("HOLD_RUNTIME_NOT_INITIALIZED", query=query, limit=limit)

    try:
        result = runtime.search_records(query, limit, "MemoryOS")
        if not isinstance(result, dict):
            return _hold("HOLD_SOURCE_INVALID", query=query, limit=limit)
        if result.get("scope_applied") != "MemoryOS" or result.get("query_filter_active") is not True:
            return _hold("HOLD_SOURCE_FILTER_UNVERIFIED", query=query, limit=limit)
        rows = result.get("records")
        if not isinstance(rows, list) or len(rows) > limit:
            return _hold("HOLD_SOURCE_INVALID", query=query, limit=limit)
        seen: set[str] = set()
        evidence: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                return _hold("HOLD_SOURCE_INVALID", query=query, limit=limit)
            rid = row.get("record_id")
            if not isinstance(rid, str) or not rid or rid in seen or row.get("scope") != "MemoryOS":
                return _hold("HOLD_SOURCE_INVALID", query=query, limit=limit)
            seen.add(rid)
            neighborhood = runtime.galaxy_record(rid)
            governing = runtime.galaxy_governing_state(rid)
            if (
                not isinstance(neighborhood, dict)
                or (neighborhood.get("record") or {}).get("record_id") != rid
                or not isinstance(governing, dict)
                or governing.get("record_id") != rid
                or governing.get("state") not in (
                    "CURRENT", "CURRENT_REVISED_CONTEXT",
                    "HISTORICAL_SUPERSEDED", "NONACTIVE_HISTORICAL"
                )
            ):
                return _hold("HOLD_GOVERNING_STATE_UNVERIFIED", query=query, limit=limit)
            evidence.append({
                "record": row,
                "governing_state": governing,
                "lifecycle": neighborhood.get("lifecycle"),
                "relations": neighborhood.get("relations", []),
                "source_provenance": row.get("source"),
                "not_identity_authority": True,
            })
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "execution": "READ_ONLY",
            "status": "PASS_SHADOW_LEGACY_READ" if evidence else "HOLD_NO_MATCH",
            "query": query,
            "scope": "MemoryOS",
            "limit": limit,
            "records": evidence,
            "count": len(evidence),
            "ranking": "LEGACY_UNWEIGHTED_CONTROL",
            "galaxy_weighting_applied": False,
            "production_retrieval_changed": False,
            "writes_performed": [],
            "memory_context_authority": "NONE",
            "proof_boundary": (
                "Existing MemoryOS evidence is visible as a separate opt-in source lane, "
                "with governing/lifecycle context. This does not enable GALAXY's "
                "general production ranking, automatic memory adoption, or writes."
            ),
        }
    except Exception as exc:
        # Do not return partial or invented memory on a failed source read.
        return _hold("HOLD_SOURCE_UNAVAILABLE", query=query, limit=limit, error_type=type(exc).__name__)
