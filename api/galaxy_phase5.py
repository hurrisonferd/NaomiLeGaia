"""GALAXY Phase 5 provenance-backed synthesis/consolidation review.

Initial Phase 5 is intentionally read-only:
- SYNTHESIS != SOURCE REWRITE.
- source history remains intact and inspectable.
- unresolved verified contradiction fails closed.
- recursive synthesis is excluded from the initial slice.
- no synthesis text is invented by this review.
- no MemoryOS or production retrieval mutation occurs here.
"""
from __future__ import annotations

from typing import Any

import galaxy_phase4

VERSION = "galaxy.phase5.synthesis-consolidation.v1"
METHOD = "PROVENANCE_BACKED_CLUSTER_V1"
MIN_SOURCES = 2
MAX_SOURCES = 6

FIXTURE_SOURCE_IDS = (
    galaxy_phase4.FIXTURE_REVISION_ID,
    galaxy_phase4.FIXTURE_CORE_ID,
)


def _normalize_ids(source_record_ids: list[str] | tuple[str, ...]) -> list[str]:
    return [str(value or "").strip() for value in source_record_ids]


def _cluster_relations(
    details: dict[str, dict[str, Any]],
    source_ids: list[str],
) -> list[dict[str, Any]]:
    members = set(source_ids)
    by_edge: dict[str, dict[str, Any]] = {}
    anonymous = 0
    for detail in details.values():
        for edge in list(detail.get("relations") or []):
            if (
                str(edge.get("source_record_id")) in members
                and str(edge.get("target_record_id")) in members
            ):
                edge_id = str(edge.get("edge_id") or "")
                key = edge_id or f"ANON-{anonymous}"
                anonymous += int(not edge_id)
                by_edge[key] = dict(edge)
    return sorted(
        by_edge.values(),
        key=lambda edge: (
            str(edge.get("verified_at") or ""),
            str(edge.get("created_at") or ""),
            str(edge.get("edge_id") or ""),
        ),
    )


def review_cluster(
    runtime: Any,
    source_record_ids: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Read-only eligibility/provenance review for one bounded synthesis cluster."""
    source_ids = _normalize_ids(source_record_ids)
    hold_reasons: list[str] = []

    if any(not record_id for record_id in source_ids):
        hold_reasons.append("EMPTY_SOURCE_RECORD_ID")
    if len(source_ids) < MIN_SOURCES or len(source_ids) > MAX_SOURCES:
        hold_reasons.append("SOURCE_COUNT_OUTSIDE_INITIAL_PHASE5_BOUNDS")
    if len(set(source_ids)) != len(source_ids):
        hold_reasons.append("DUPLICATE_SOURCE_RECORD_ID")

    details: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for record_id in source_ids:
        if not record_id or record_id in details:
            continue
        detail = runtime.galaxy_record(record_id)
        if not detail or not detail.get("record"):
            missing.append(record_id)
        else:
            details[record_id] = detail
    if missing:
        hold_reasons.append("SOURCE_RECORD_MISSING")

    records = [details[record_id]["record"] for record_id in source_ids if record_id in details]
    scopes = sorted({str(record.get("scope") or "") for record in records})
    if len(scopes) > 1:
        hold_reasons.append("CROSS_SCOPE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE")

    recursive_sources = [
        str(record.get("record_id"))
        for record in records
        if str(record.get("record_type") or "").upper() == "SYNTHESIS"
    ]
    if recursive_sources:
        hold_reasons.append("RECURSIVE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE")

    internal_relations = _cluster_relations(details, source_ids) if details else []
    verified_internal = [
        edge for edge in internal_relations if str(edge.get("status")) == "VERIFIED"
    ]
    historical_internal = [
        edge for edge in internal_relations if str(edge.get("status")) != "VERIFIED"
    ]
    if len(records) >= MIN_SOURCES and not verified_internal:
        hold_reasons.append("NO_VERIFIED_INTERNAL_RELATION")

    contradictions = [
        edge for edge in verified_internal
        if str(edge.get("relation_type")) == "CONTRADICTS"
    ]
    if contradictions:
        hold_reasons.append("UNRESOLVED_VERIFIED_CONTRADICTION_IN_CLUSTER")

    governing_states: dict[str, dict[str, Any]] = {}
    for record_id in source_ids:
        if record_id in details:
            governing_states[record_id] = runtime.galaxy_governing_state(record_id)
    current_eligible = [
        record_id for record_id, state in governing_states.items()
        if state.get("current_default_eligible") is True
    ]
    if records and not current_eligible:
        hold_reasons.append("NO_CURRENT_GOVERNING_SOURCE")

    source_snapshots = [
        {
            "record_id": record_id,
            "scope": details[record_id]["record"].get("scope"),
            "record_type": details[record_id]["record"].get("record_type"),
            "status": details[record_id]["record"].get("status"),
            "statement": details[record_id]["record"].get("statement"),
            "governing_state": governing_states.get(record_id),
        }
        for record_id in source_ids
        if record_id in details
    ]

    return {
        "schema": "gaiaos.galaxy.phase5-cluster-review.v1",
        "version": VERSION,
        "execution": "READ_ONLY",
        "authority": "NAOMI",
        "status": "PASS_READ_ONLY_SYNTHESIS_CLUSTER" if not hold_reasons else "HOLD",
        "method": METHOD,
        "source_record_ids": source_ids,
        "source_count": len(source_ids),
        "scope": scopes[0] if len(scopes) == 1 else None,
        "missing_source_record_ids": missing,
        "recursive_source_record_ids": recursive_sources,
        "source_snapshots": source_snapshots,
        "verified_internal_relations": verified_internal,
        "historical_internal_relations": historical_internal,
        "unresolved_verified_contradictions": contradictions,
        "current_default_eligible_source_ids": current_eligible,
        "synthesis_candidate": {
            "proposed_record_type": "SYNTHESIS",
            "proposed_status": "CANDIDATE_ONLY",
            "method": METHOD,
            "source_record_ids": source_ids,
            "source_provenance_complete": not missing and len(set(source_ids)) == len(source_ids),
            "synthesis_statement_generated": False,
            "synthesis_statement_required_before_manifestation": True,
            "default_retrieval_target_selected": False,
        },
        "hold_reasons": hold_reasons,
        "checks": {
            "synthesis_is_not_source_rewrite": True,
            "consolidation_is_not_deletion": True,
            "source_history_preserved": True,
            "provenance_explicit": not missing and len(set(source_ids)) == len(source_ids),
            "same_scope_initial_slice": len(scopes) == 1,
            "verified_internal_relation_present": bool(verified_internal),
            "verified_contradiction_absent": not contradictions,
            "recursive_synthesis_absent": not recursive_sources,
            "synthesis_statement_generated": False,
            "zero_memory_writes": True,
            "memory_syntheses_row_written": False,
            "derived_from_edges_written": False,
            "production_retrieval_changed": False,
            "unrestricted_global_weighting_enabled": False,
        },
        "next_gate": (
            "DEPLOY_AND_OBSERVE_READ_ONLY_FIXTURE"
            if not hold_reasons
            else "REPAIR_OR_RESOLVE_HOLD"
        ),
        "proof_boundary": (
            "This review proves only bounded source-cluster eligibility and provenance shape. "
            "It creates no synthesis record, provenance row, DERIVED_FROM edge, or retrieval effect."
        ),
    }


def fixture_review(runtime: Any) -> dict[str, Any]:
    """Read-only Phase-5 review over the live-proven Phase-4 revision pair."""
    review = review_cluster(runtime, FIXTURE_SOURCE_IDS)
    checks = {
        "cluster_review_pass": review.get("status") == "PASS_READ_ONLY_SYNTHESIS_CLUSTER",
        "fixture_sources_exact": review.get("source_record_ids") == list(FIXTURE_SOURCE_IDS),
        "verified_relation_visible": bool(review.get("verified_internal_relations")),
        "statement_not_generated": (
            review.get("synthesis_candidate", {}).get("synthesis_statement_generated") is False
        ),
        "source_history_preserved": review.get("checks", {}).get("source_history_preserved") is True,
        "zero_memory_writes": True,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
    }
    status = (
        "PASS_READ_ONLY_PHASE5_FIXTURE_REVIEW"
        if all((
            checks["cluster_review_pass"],
            checks["fixture_sources_exact"],
            checks["verified_relation_visible"],
            checks["statement_not_generated"],
            checks["source_history_preserved"],
        ))
        else "HOLD"
    )
    return {
        "schema": "gaiaos.galaxy.phase5-fixture-review.v1",
        "version": VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": status,
        "fixture_source_record_ids": list(FIXTURE_SOURCE_IDS),
        "cluster_review": review,
        "checks": checks,
        "next_gate": (
            "EXPLICIT_NAOMI_AUTHORIZATION_BEFORE_PHASE5_MUTATION_DESIGN"
            if status == "PASS_READ_ONLY_PHASE5_FIXTURE_REVIEW"
            else "REPAIR_BEFORE_MUTATION_DESIGN"
        ),
        "proof_boundary": (
            "Fixture review is read-only. It proves no synthesis manifestation, "
            "default retrieval selection, source rewriting, deletion, or production retrieval change."
        ),
    }
