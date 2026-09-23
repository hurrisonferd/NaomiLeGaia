"""GALAXY Phase-3 Exit Integration.

This module is the finite integration gate after the live Phase3J PASS. It
adopts only the validated statement-first relevance rule inside the already
bounded Phase3F pilot surface. It is read-only: it never writes MemoryOS,
never changes global aliases, and never enables the pilot.

Primary candidate membership is statement-only. Notes and virtual scope are
excluded from primary evidence. VERIFIED direct graph neighbors are surfaced
as a separate linked-context lane and are not admitted into the weighted
record list.
"""
from __future__ import annotations

from typing import Any

import galaxy_quality

VERSION = "galaxy.phase3-exit-integration.v1"
PRIMARY_MIN_CONCEPTS = galaxy_quality.PHASE3J_PRIMARY_MIN_CONCEPTS
PRIMARY_MIN_COVERAGE = galaxy_quality.PHASE3J_PRIMARY_MIN_COVERAGE
PRIMARY_CAP = 4
LINKED_CONTEXT_CAP = 2
SCAN_LIMIT = 100
PILOT_QUERY_INDEXES = (0, 3, 5)


def _statement_evidence(runtime: Any, statement: str, query: str) -> dict[str, Any]:
    """Reuse the exact Phase3J concept bridge that passed live review."""
    return galaxy_quality._phase3j_statement_evidence(runtime, statement, query)


def build_candidate_pool(
    runtime: Any,
    query: str,
    *,
    scope: str = "MemoryOS",
    limit: int = 10,
) -> dict[str, Any]:
    """Build one bounded statement-first production-pilot candidate pool.

    This is only an admission/ranking input for the guarded pilot. It does not
    activate the pilot and performs no writes.
    """
    if scope != "MemoryOS":
        return {
            "status": "HOLD",
            "reason": "MEMORYOS_SCOPE_REQUIRED",
            "candidate_record_ids": [],
            "candidate_count": 0,
            "candidates": [],
            "linked_context_lane": [],
            "zero_memory_writes": True,
        }
    if int(limit) != 10:
        return {
            "status": "HOLD",
            "reason": "EXACT_BOUNDED_LIMIT_REQUIRED",
            "candidate_record_ids": [],
            "candidate_count": 0,
            "candidates": [],
            "linked_context_lane": [],
            "zero_memory_writes": True,
        }

    query_tokens = runtime._galaxy_query_tokens(query)
    external_terms = sorted(
        token for token in query_tokens
        if token in getattr(runtime, "GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS", set())
    )
    if external_terms:
        return {
            "status": "HOLD",
            "reason": "EXTERNAL_DOMAIN_DISAMBIGUATOR",
            "external_domain_terms": external_terms,
            "candidate_record_ids": [],
            "candidate_count": 0,
            "candidates": [],
            "linked_context_lane": [],
            "zero_memory_writes": True,
        }

    snapshot = runtime.search_records("", SCAN_LIMIT, scope)
    rows = list(snapshot.get("records") or [])
    evidence_rows: list[dict[str, Any]] = []
    for position, record in enumerate(rows):
        record_id = str(record.get("record_id") or "")
        evidence = _statement_evidence(
            runtime, str(record.get("statement") or ""), query
        )
        evidence_rows.append({
            "record_id": record_id,
            "statement": record.get("statement"),
            "scope": record.get("scope"),
            "source": record.get("source"),
            "scan_position": position,
            **evidence,
        })

    primary = [
        row for row in evidence_rows
        if row["matched_statement_concept_count"] >= PRIMARY_MIN_CONCEPTS
        and row["statement_concept_coverage"] >= PRIMARY_MIN_COVERAGE
    ]
    primary.sort(
        key=lambda row: (
            -row["statement_concept_coverage"],
            -row["matched_statement_concept_count"],
            row["scan_position"],
            row["record_id"],
        )
    )

    overflow = [row["record_id"] for row in primary[PRIMARY_CAP:]]
    primary = primary[:PRIMARY_CAP]
    primary_ids = [row["record_id"] for row in primary]
    primary_set = set(primary_ids)

    linked: list[dict[str, Any]] = []
    for row in evidence_rows:
        if row["record_id"] in primary_set or row["matched_statement_concept_count"] < 1:
            continue
        detail = runtime.galaxy_record(row["record_id"])
        if not detail:
            continue
        direct_edges = []
        for edge in detail.get("relations", []):
            if edge.get("status") != "VERIFIED":
                continue
            source = edge.get("source_record_id")
            target = edge.get("target_record_id")
            if (
                source == row["record_id"] and target in primary_set
            ) or (
                target == row["record_id"] and source in primary_set
            ):
                direct_edges.append({
                    "edge_id": edge.get("edge_id"),
                    "relation_type": edge.get("relation_type"),
                    "source_record_id": source,
                    "target_record_id": target,
                })
        if direct_edges:
            linked.append({
                **row,
                "verified_direct_primary_edges": direct_edges,
            })

    linked.sort(
        key=lambda row: (
            -row["statement_concept_coverage"],
            -row["matched_statement_concept_count"],
            row["scan_position"],
            row["record_id"],
        )
    )
    linked_overflow = [row["record_id"] for row in linked[LINKED_CONTEXT_CAP:]]
    linked = linked[:LINKED_CONTEXT_CAP]

    candidates = [
        {
            "record_id": row["record_id"],
            "statement": row["statement"],
            "scope": row["scope"],
            "source": row["source"],
            "evidence_lane": "PRIMARY_STATEMENT",
            "relevance": {
                "coverage": row["statement_concept_coverage"],
                "matched_concepts": row["matched_statement_concepts"],
                "matched_concept_count": row["matched_statement_concept_count"],
                "statement_only": True,
                "notes_used": False,
                "scope_virtual_match_used": False,
            },
        }
        for row in primary
    ]

    checks = {
        "primary_statement_only": True,
        "notes_or_scope_cannot_create_primary": True,
        "all_admitted_candidates_meet_primary_rule": all(
            row["matched_statement_concept_count"] >= PRIMARY_MIN_CONCEPTS
            and row["statement_concept_coverage"] >= PRIMARY_MIN_COVERAGE
            for row in primary
        ),
        "linked_context_requires_verified_direct_primary_edge": all(
            bool(row.get("verified_direct_primary_edges")) for row in linked
        ),
        "linked_context_admitted_to_weighted_records": False,
        "primary_cap_respected": not overflow,
        "zero_memory_writes": True,
        "production_aliases_modified": False,
        "unrestricted_global_weighting_enabled": False,
    }
    status = (
        "PASS"
        if primary and not overflow and all(checks.values())
        else "HOLD"
    )

    return {
        "schema": "gaiaos.galaxy.phase3-exit-candidate-pool.v1",
        "version": VERSION,
        "status": status,
        "reason": (
            "STATEMENT_FIRST_POOL_READY"
            if status == "PASS"
            else ("PRIMARY_CAP_OVERFLOW" if overflow else "NO_PRIMARY_CANDIDATE")
        ),
        "query": query,
        "scope": scope,
        "scope_eligible_population_count": len(rows),
        "candidate_record_ids": primary_ids,
        "candidate_count": len(primary_ids),
        "candidates": candidates,
        "primary_evidence": primary,
        "primary_overflow_record_ids": overflow,
        "linked_context_lane": linked,
        "linked_context_record_ids": [row["record_id"] for row in linked],
        "linked_context_overflow_record_ids": linked_overflow,
        "checks": checks,
        "zero_memory_writes": True,
        "proof_boundary": (
            "Bounded Phase-3 Exit Integration admission only. Primary evidence is "
            "statement-only using the live-validated Phase3J bridge. VERIFIED graph "
            "neighbors are reported separately and never enter weighted records. "
            "This does not enable the pilot or global weighting."
        ),
    }


def review_suite(runtime: Any) -> dict[str, Any]:
    """Read-only preflight for the exact existing three-query pilot allowlist."""
    cases = []
    for index in PILOT_QUERY_INDEXES:
        query = runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[index]
        pool = build_candidate_pool(runtime, query, scope="MemoryOS", limit=10)
        cases.append({
            "query_index": index,
            "query": query,
            "status": pool.get("status"),
            "candidate_record_ids": pool.get("candidate_record_ids", []),
            "candidate_count": pool.get("candidate_count", 0),
            "linked_context_record_ids": pool.get("linked_context_record_ids", []),
            "primary_overflow_record_ids": pool.get("primary_overflow_record_ids", []),
            "checks": pool.get("checks", {}),
        })
    passed = all(case["status"] == "PASS" for case in cases)
    return {
        "schema": "gaiaos.galaxy.phase3-exit-integration-review.v1",
        "version": VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": "PASS_READ_ONLY_PREFLIGHT" if passed else "HOLD",
        "query_indexes": list(PILOT_QUERY_INDEXES),
        "cases": cases,
        "checks": {
            "all_three_bounded_pools_ready": passed,
            "zero_memory_writes": True,
            "pilot_activated": False,
            "unrestricted_global_weighting_enabled": False,
        },
        "next_gate": "FRESH_GUARDED_SWITCH_TEST" if passed else "REPAIR_BEFORE_SWITCH_TEST",
        "proof_boundary": (
            "Read-only preflight of the candidate admission that the existing guarded "
            "pilot will use. PASS does not activate weighted retrieval."
        ),
    }
