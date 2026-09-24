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


def operational(runtime: Any, query: str, limit: int = 4) -> dict[str, Any]:
    """GALAXY's default-on, governed, statement-first MemoryOS context lane.

    Use the existing Phase-3 exit admission rules, Phase-2 gravity/Seven Gates
    influence, verified graph edges and Phase-6 lifecycle metadata. This reads
    existing durable evidence only. It never mutates a memory, triggers a
    synthesis, writes an E-LANE, or changes the approved candidate pool.
    """
    import galaxy_phase3_exit

    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 20000:
        return _hold("HOLD_QUERY_INVALID", query="", limit=0)
    query = query.strip()
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RECORDS:
        return _hold("HOLD_LIMIT_INVALID", query=query, limit=0)
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return _hold("HOLD_RUNTIME_NOT_INITIALIZED", query=query, limit=limit)

    try:
        # The upstream finite Phase-3 exit always scans at most 100 scoped
        # records and admits at most four statement-anchored primary records.
        pool = galaxy_phase3_exit.build_candidate_pool(
            runtime, query, scope="MemoryOS", limit=10,
        )
        if pool.get("status") != "PASS":
            return {
                **_hold("HOLD_NO_CONFIDENT_GALAXY_MATCH", query=query, limit=limit),
                "reason": pool.get("reason", "PHASE3_ADMISSION_HOLD"),
                "ranking": "GALAXY_STATEMENT_FIRST_80_20",
                "version": "galaxy.frontdoor.operational.v1",
                "no_broad_fallback": True,
            }
        source_candidates = pool.get("candidates") or []
        if not source_candidates or len(source_candidates) > 4:
            return _hold("HOLD_CANDIDATE_POOL_INVALID", query=query, limit=limit)
        if pool.get("checks", {}).get("all_admitted_candidates_meet_primary_rule") is not True:
            return _hold("HOLD_CANDIDATE_RULE_INVALID", query=query, limit=limit)
        if pool.get("checks", {}).get("linked_context_requires_verified_direct_primary_edge") is not True:
            return _hold("HOLD_GRAPH_RULE_INVALID", query=query, limit=limit)

        current = []
        historical = []
        seen = set()
        for candidate in source_candidates:
            rid = candidate.get("record_id")
            if not isinstance(rid, str) or not rid or rid in seen:
                return _hold("HOLD_CANDIDATE_ID_INVALID", query=query, limit=limit)
            seen.add(rid)
            detail = runtime.galaxy_record(rid)
            if not isinstance(detail, dict) or not isinstance(detail.get("record"), dict):
                return _hold("HOLD_SOURCE_CHANGED", query=query, limit=limit)
            record = detail["record"]
            if record.get("record_id") != rid or record.get("scope") != "MemoryOS":
                return _hold("HOLD_SCOPE_OR_ID_CHANGED", query=query, limit=limit)
            if record.get("statement") != candidate.get("statement"):
                return _hold("HOLD_STATEMENT_CHANGED", query=query, limit=limit)
            governing = runtime.galaxy_governing_state(rid)
            if governing.get("record_id") != rid:
                return _hold("HOLD_GOVERNING_STATE_CHANGED", query=query, limit=limit)
            if governing.get("state") not in (
                "CURRENT", "CURRENT_REVISED_CONTEXT",
                "HISTORICAL_SUPERSEDED", "NONACTIVE_HISTORICAL",
            ):
                return _hold("HOLD_GOVERNING_STATE_INVALID", query=query, limit=limit)

            relevance = candidate.get("relevance") or {}
            coverage = float(relevance.get("coverage") or 0.0)
            gravity = detail.get("gravity") or {}
            # A stored gravity row is acceptable. An absent row is previewed
            # using the approved Phase-2 model without writing a score.
            if gravity:
                gravity_score = float(gravity.get("gravity_score") or 0.0)
                gravity_basis = "STORED"
            else:
                gravity_preview = runtime.galaxy_gravity_preview(rid)
                gravity_score = float(gravity_preview.get("gravity_score") or 0.0)
                gravity_basis = "READ_ONLY_PREVIEW"
            if not 0.0 <= coverage <= 1.0 or not 0.0 <= gravity_score <= 1.0:
                return _hold("HOLD_SCORE_INVALID", query=query, limit=limit)
            score = round(0.8 * coverage + 0.2 * gravity_score, 6)
            item = {
                "record": record,
                "source_provenance": record.get("source"),
                "governing_state": governing,
                "lifecycle": detail.get("lifecycle"),
                "relations": detail.get("relations") or [],
                "importance": detail.get("importance"),
                "gravity": {
                    "score": gravity_score,
                    "basis": gravity_basis,
                    "explicit_importance_included_in_model": True,
                },
                "relevance": relevance,
                "ranking": {
                    "relevance_weight": 0.8,
                    "gravity_weight": 0.2,
                    "score": score,
                    "relevance_tier": coverage,
                    "authority_effect": "NONE",
                },
                "not_identity_authority": True,
            }
            if governing.get("current_default_eligible") is True:
                current.append(item)
            else:
                historical.append(item)

        # Strictly preserve relevance-tier precedence. Gravity and owner
        # importance affect ordering within the relevance tier, never truth,
        # candidate admission or history eligibility.
        current.sort(key=lambda item: (
            -item["ranking"]["relevance_tier"],
            -item["ranking"]["score"],
            item["record"]["record_id"],
        ))
        historical.sort(key=lambda item: (
            -item["ranking"]["relevance_tier"],
            -item["ranking"]["score"],
            item["record"]["record_id"],
        ))
        admitted_ids = {item["record"]["record_id"] for item in current}
        linked = []
        for candidate in pool.get("linked_context_candidates") or []:
            rid = candidate.get("record_id")
            if not isinstance(rid, str) or rid in seen:
                continue
            edges = candidate.get("verified_direct_primary_edges") or []
            if not any(
                edge.get("edge_id")
                and edge.get("source_record_id") in admitted_ids
                or edge.get("edge_id")
                and edge.get("target_record_id") in admitted_ids
                for edge in edges
            ):
                continue
            detail = runtime.galaxy_record(rid)
            if not detail or (detail.get("record") or {}).get("scope") != "MemoryOS":
                return _hold("HOLD_LINKED_SCOPE_INVALID", query=query, limit=limit)
            governing = runtime.galaxy_governing_state(rid)
            linked.append({
                "record": detail["record"],
                "source_provenance": detail["record"].get("source"),
                "governing_state": governing,
                "verified_direct_primary_edges": edges,
                "context_only": True,
                "not_identity_authority": True,
            })
            seen.add(rid)
            if len(linked) >= 2:
                break

        selected = current[:limit]
        return {
            "schema": SCHEMA,
            "version": "galaxy.frontdoor.operational.v1",
            "execution": "READ_ONLY",
            "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL" if selected else "HOLD_NO_CURRENT_MATCH",
            "query": query,
            "scope": "MemoryOS",
            "limit": limit,
            "records": selected,
            "count": len(selected),
            "historical_context": historical,
            "verified_linked_context": linked,
            "ranking": "GALAXY_STATEMENT_FIRST_80_20_RELEVANCE_TIER_GUARDED",
            "galaxy_weighting_applied": True,
            "candidate_pool_status": "PASS",
            "candidate_set_preserved": True,
            "production_retrieval_changed": True,
            "writes_performed": [],
            "memory_context_authority": "NONE",
            "provenance_preserved": True,
            "e_lanes_modified": False,
            "automatic_capture": False,
            "automatic_promotion": False,
            "physical_delete": False,
            "proof_boundary": (
                "GALAXY retrieval is active in this GaiaOS front-door request. "
                "This is bounded statement-first relevance, graph context and "
                "gravity/Seven Gates ranking over existing MemoryOS records, "
                "not a claim of universal semantic understanding or automatic "
                "write authorization. E-LANES, //PW:PRESERVE// and owner approval "
                "remain separate and unchanged."
            ),
        }
    except Exception as exc:
        return {
            **_hold(
                "HOLD_GALAXY_UNAVAILABLE", query=query, limit=limit,
                error_type=type(exc).__name__,
            ),
            "version": "galaxy.frontdoor.operational.v1",
            "no_broad_fallback": True,
        }
