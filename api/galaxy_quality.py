"""GALAXY Phase 3G read-only candidate-quality inspection.

The audit separates source-statement evidence, record notes, and virtual scope
matching. It does not mutate memory, override operator judgment, or change any
production retrieval path.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "galaxy.phase3g.retrieval-quality-review.v1"
TEST_QUERIES = {
    0: "gravity",
    3: "calibration core",
    5: "calibration core",
}


def _normalized(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(text or "").lower()))


def _match_origin(runtime: Any, record: dict[str, Any], query: str) -> list[dict[str, Any]]:
    statement_tokens = runtime._galaxy_query_tokens(record.get("statement") or "")
    notes_tokens = runtime._galaxy_query_tokens(record.get("notes") or "")
    statement_concepts = {runtime._galaxy_query_concept(t) for t in statement_tokens}
    notes_concepts = {runtime._galaxy_query_concept(t) for t in notes_tokens}
    scope_memory = str(record.get("scope") or "").lower() == "memoryos"
    return [
        {
            "query_term": token,
            "concept": runtime._galaxy_query_concept(token),
            "statement": token in statement_tokens or runtime._galaxy_query_concept(token) in statement_concepts,
            "notes": token in notes_tokens or runtime._galaxy_query_concept(token) in notes_concepts,
            "scope_virtual_memory": scope_memory and runtime._galaxy_query_concept(token) == "memory",
        }
        for token in runtime._galaxy_query_tokens(query)
    ]


def review(runtime: Any, *, query_index: int = 3, limit: int = 10) -> dict[str, Any]:
    """Inspect a bounded set of real MemoryOS records with no writes.

    Being explicitly about the query's anchor is a diagnostic distinction, not
    a universal relevance metric or an automatically approved promotion gate.
    """
    if query_index not in TEST_QUERIES:
        raise ValueError("Only approved calibration query indexes 0, 3, 5 are inspectable")
    if not 1 <= int(limit) <= 10:
        raise ValueError("Review limit must be between 1 and 10")

    query = runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[query_index]
    anchor = TEST_QUERIES[query_index]
    pool = runtime.galaxy_phase3_candidate_pool(query, scope="MemoryOS", limit=limit)
    scored = runtime._galaxy_phase3c_score_pool(pool, 0.8, 0.2)
    weighted = {entry["record_id"]: entry for entry in scored["weighted_order"]}
    legacy = runtime.search_records(query, limit, "MemoryOS")
    candidate_ids = list(pool["candidate_record_ids"])
    if len(candidate_ids) != len(set(candidate_ids)):
        return {
            "schema": "gaiaos.galaxy.phase3g-quality-review.v1",
            "status": "HOLD",
            "reason": "DUPLICATE_CANDIDATE_IDS",
            "zero_memory_writes": True,
            "production_retrieval_changed": False,
        }

    results = []
    missing = []
    for item in pool["candidates"]:
        record_id = item["record_id"]
        detail = runtime.galaxy_record(record_id)
        if not detail or not detail.get("record"):
            missing.append(record_id)
            continue
        record = detail["record"]
        origins = _match_origin(runtime, record, query)
        statement_anchor = _normalized(anchor) in _normalized(record.get("statement") or "")
        governing = runtime.galaxy_governing_state(record_id)
        verified = [
            {
                "edge_id": edge["edge_id"],
                "relation_type": edge["relation_type"],
                "source_record_id": edge["source_record_id"],
                "target_record_id": edge["target_record_id"],
                "other_record_in_pool": (
                    (
                        edge["target_record_id"] if edge["source_record_id"] == record_id
                        else edge["source_record_id"]
                    ) in candidate_ids
                ),
            }
            for edge in detail.get("relations", [])
            if edge.get("status") == "VERIFIED"
        ]
        score = weighted[record_id]
        results.append({
            "record_id": record_id,
            "statement": record.get("statement"),
            "source": record.get("source"),
            "record_status": record.get("status"),
            "created_at": record.get("created_at"),
            "notes_excerpt": str(record.get("notes") or "")[:320],
            "query_relevance_coverage": item["relevance"]["coverage"],
            "matched_terms": item["relevance"]["matched_terms"],
            "match_origin": origins,
            "statement_anchor_present": statement_anchor,
            "audit_group": (
                "TOPIC_ANCHORED_CANDIDATE"
                if statement_anchor else "INDIRECT_OR_POLICY_CONTEXT_REQUIRES_REVIEW"
            ),
            "weighted_rank": score["weighted_rank"],
            "weighted_score": score["weighted_score"],
            "gravity_score": score["gravity_score"],
            "current_default_eligible": governing.get("current_default_eligible"),
            "governing_state": governing.get("state"),
            "verified_relations": verified,
            "verified_in_pool_relation_count": sum(e["other_record_in_pool"] for e in verified),
        })

    anchored = [r["record_id"] for r in results if r["statement_anchor_present"]]
    indirect = [r["record_id"] for r in results if not r["statement_anchor_present"]]
    return {
        "schema": "gaiaos.galaxy.phase3g-quality-review.v1",
        "status": "OBSERVED_READ_ONLY" if not missing else "HOLD",
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "version": VERSION,
        "query_index": query_index,
        "query": query,
        "diagnostic_anchor": anchor,
        "scope_eligible_population_count": pool["scope_eligible_population_count"],
        "legacy_sql_record_ids": [r["record_id"] for r in legacy["records"]],
        "candidate_count": len(candidate_ids),
        "topic_anchored_candidate_ids": anchored,
        "indirect_or_policy_context_ids": indirect,
        "ambiguous_record_ids": pool["ambiguous_record_ids"],
        "missing_record_ids": missing,
        "records": results,
        "checks": {
            "all_pool_candidates_inspected": len(results) == len(candidate_ids),
            "gravity_introduced_no_candidates": bool(scored["candidate_set_preserved"]),
            "highest_relevance_preserved": bool(scored["top_relevance_preserved"]),
            "cross_relevance_tier_inversions": scored["cross_relevance_tier_inversion_count"],
            "zero_memory_writes": True,
            "ordinary_memoryos_retrieval_changed": False,
            "global_production_weighting_enabled": False,
        },
        "provisional_containment_experiment": {
            "focus": "Direct statement anchor and verified graph edges before metadata-only matches",
            "initial_focal_slot_cap": 4,
            "optional_contextual_slot_cap": 2,
            "minimum_relevance_for_plain_indirect_context": 0.8,
            "disallow_unverified_graph_edge_as_promotion_proof": True,
            "promotion_implemented": False,
        },
        "proof_boundary": (
            "This read-only diagnostic exposes where each query term matched "
            "(statement, notes or MemoryOS scope) and verified graph edges. "
            "An explicit phrase anchor is a topic-coherence clue, not a universal "
            "semantic classifier. No production candidate admission, weighting, "
            "memory records or governing status have been changed."
        ),
    }
