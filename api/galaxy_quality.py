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


PHASE3H_VERSION = "galaxy.phase3h.containment-shadow.v1"
PHASE3H_FOCAL_CAP = 4
PHASE3H_LINKED_CAP = 2
PHASE3H_NEGATIVE_CONTROLS = (
    "planetary gravity trajectories",
    "advertising contextual influence",
)


def _unique_query_concepts(origins: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Collapse aliases such as 'memory' and 'retrieval' into one concept."""
    concepts: dict[str, list[str]] = {}
    for term in origins:
        concepts.setdefault(term["concept"], []).append(term["query_term"])
    return concepts


def _evidence_summary(record: dict[str, Any]) -> dict[str, Any]:
    origins = list(record["match_origin"])
    concept_terms = _unique_query_concepts(origins)
    statement = sorted({t["concept"] for t in origins if t["statement"]})
    notes_only = sorted({
        t["concept"] for t in origins if t["notes"] and not t["statement"]
    })
    virtual_scope = sorted({
        t["concept"] for t in origins
        if t["scope_virtual_memory"] and not t["statement"]
    })
    distinct = len(concept_terms)
    return {
        "record_id": record["record_id"],
        "statement": record["statement"],
        "source": record["source"],
        "governing_state": record["governing_state"],
        "current_default_eligible": record["current_default_eligible"],
        "original_weighted_rank": record["weighted_rank"],
        "original_80_20_score": record["weighted_score"],
        "original_coverage": record["query_relevance_coverage"],
        "distinct_query_concept_count": distinct,
        "statement_backed_concepts": statement,
        "notes_backed_only_concepts": notes_only,
        "virtual_scope_concepts_without_statement": virtual_scope,
        "statement_concept_coverage": (
            round(len(statement) / distinct, 6) if distinct else 0.0
        ),
        "alias_groups": {
            concept: tokens for concept, tokens in concept_terms.items()
            if len(tokens) > 1
        },
        "verified_relations": record["verified_relations"],
        "statement_anchor_present": record["statement_anchor_present"],
    }


def containment_shadow(
    runtime: Any, *, query_index: int = 3,
    limit: int = 10, negative_controls: bool = False,
) -> dict[str, Any]:
    """Compare original 80/20 to evidence-separated presentation lanes.

    This never changes candidate admission, production rank, memory, or graph
    state. Phrase anchors only test the three approved calibration queries.
    Metadata/scope matches do not independently admit focal evidence, and
    graph links require VERIFIED direct connection to a focal record.
    """
    diagnostic = review(runtime, query_index=query_index, limit=limit)
    if diagnostic.get("status") != "OBSERVED_READ_ONLY":
        return {
            "schema": "gaiaos.galaxy.phase3h-containment-shadow.v1",
            "status": "HOLD",
            "reason": "PHASE3G_DIAGNOSTIC_INCOMPLETE",
            "quality_review_status": diagnostic.get("status"),
            "no_production_changes": True,
        }
    rows = [_evidence_summary(row) for row in diagnostic["records"]]
    weighted_order = sorted(rows, key=lambda row: row["original_weighted_rank"])
    focal_all = [
        row for row in weighted_order
        if row["statement_anchor_present"] and row["current_default_eligible"] is True
    ]
    focal = focal_all[:PHASE3H_FOCAL_CAP]
    focal_ids = {row["record_id"] for row in focal}
    linked_all = []
    for row in weighted_order:
        if row["record_id"] in focal_ids or row["statement_anchor_present"]:
            continue
        if row["current_default_eligible"] is not True:
            continue
        if not row["statement_backed_concepts"]:
            continue
        direct_verified_edges = [
            edge for edge in row["verified_relations"]
            if (
                edge["source_record_id"] == row["record_id"]
                and edge["target_record_id"] in focal_ids
            ) or (
                edge["target_record_id"] == row["record_id"]
                and edge["source_record_id"] in focal_ids
            )
        ]
        if direct_verified_edges:
            linked_all.append({
                **row, "focal_link_evidence": direct_verified_edges,
            })
    linked = linked_all[:PHASE3H_LINKED_CAP]
    included_ids = focal_ids | {r["record_id"] for r in linked}
    nonfocal = [
        row for row in weighted_order if row["record_id"] not in included_ids
    ]
    historical = [
        row for row in nonfocal if row["current_default_eligible"] is not True
    ]
    audit_only = [
        row for row in nonfocal if row["current_default_eligible"] is True
    ]
    over_cap = len(focal_all) > PHASE3H_FOCAL_CAP or len(linked_all) > PHASE3H_LINKED_CAP
    negative = []
    if negative_controls:
        for query in PHASE3H_NEGATIVE_CONTROLS:
            control = runtime.galaxy_phase3_candidate_pool(
                query, scope="MemoryOS", limit=10,
            )
            control_ids = control.get("candidate_record_ids")
            count = control.get("candidate_count")
            well_formed = (
                isinstance(control_ids, list)
                and isinstance(count, int) and not isinstance(count, bool)
                and count == len(control_ids)
            )
            negative.append({
                "query": query,
                "candidate_count": count,
                "candidate_record_ids": control_ids,
                "receipt_well_formed": well_formed,
                "excluded_by_external_domain_disambiguator": (
                    well_formed and count == 0
                ),
            })
    accounted = len({
        row["record_id"] for row in focal + linked + historical + audit_only
    }) == len(rows) and len(focal) + len(linked) + len(historical) + len(audit_only) == len(rows)
    checks = {
        "all_relevance_qualified_candidates_accounted_for": accounted,
        "primary_lane_requires_statement_anchor": all(
            row["statement_anchor_present"] for row in focal
        ),
        "secondary_requires_verified_direct_focal_edge": all(
            bool(row.get("focal_link_evidence")) for row in linked
        ),
        "source_notes_and_scope_not_sufficient_for_primary": True,
        "aliases_counted_once_in_evidence_summary": True,
        "overflow_requires_manual_review": over_cap,
        "negative_controls_zero_candidates": (
            all(row["excluded_by_external_domain_disambiguator"] for row in negative)
            if negative_controls else None
        ),
        "zero_memory_writes": True,
        "actual_production_retrieval_modified": False,
        "actual_80_20_ranking_modified": False,
        "unrestricted_global_weighting_enabled": False,
    }
    status = (
        "PASS_READ_ONLY_SHADOW"
        if focal and accounted and not over_cap and
        (not negative_controls or checks["negative_controls_zero_candidates"])
        else "HOLD"
    )
    return {
        "schema": "gaiaos.galaxy.phase3h-containment-shadow.v1",
        "version": PHASE3H_VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": status,
        "query_index": query_index,
        "query": diagnostic["query"],
        "diagnostic_anchor": diagnostic["diagnostic_anchor"],
        "scope_eligible_population_count": diagnostic["scope_eligible_population_count"],
        "legacy_sql_record_ids": diagnostic["legacy_sql_record_ids"],
        "original_relevance_pool_count": len(rows),
        "original_weighted_record_ids": [r["record_id"] for r in weighted_order],
        "query_concept_alias_groups": (
            weighted_order[0]["alias_groups"] if weighted_order else {}
        ),
        "focal_lane": focal,
        "linked_context_lane": linked,
        "historical_review_lane": historical,
        "other_candidate_audit_lane": audit_only,
        "focal_overflow_record_ids": [
            r["record_id"] for r in focal_all[PHASE3H_FOCAL_CAP:]
        ],
        "linked_overflow_record_ids": [
            r["record_id"] for r in linked_all[PHASE3H_LINKED_CAP:]
        ],
        "ambiguous_not_admitted_ids": diagnostic["ambiguous_record_ids"],
        "negative_controls": negative,
        "checks": checks,
        "proof_boundary": (
            "Read-only, three-known-query calibration-only shadow. Grouping is "
            "a proposed human-inspectable presentation, NOT a change to "
            "relevance-qualified candidate membership, production 80/20 rank, "
            "global weighting, or memory/governing state. Anchors are literal "
            "phrase clues rather than general semantic reasoning; manual "
            "quality review and broader validation remain necessary."
        ),
    }


PHASE3I_VERSION = "galaxy.phase3i.generalization-suite.v1"

# Controlled fixture oracle for read-only retrieval evaluation. These expected
# IDs are test truth for this calibration corpus, not production relevance rules.
PHASE3I_CASES = (
    {
        "case_id": "GRAVITY_PARAPHRASE",
        "kind": "POSITIVE",
        "difficulty": "MEDIUM",
        "query": "contextual influence should affect memory recall",
        "expected_primary_ids": ("MEM-3883f8127bcd40e28255fdbfa4c98309",),
        "expected_related_ids": (),
    },
    {
        "case_id": "CORE_CONTENT_PARAPHRASE",
        "kind": "POSITIVE",
        "difficulty": "MEDIUM",
        "query": "violet carrier pulse calibration observation",
        "expected_primary_ids": ("MEM-00b3fbfd4d73404f97a95c238596ab94",),
        "expected_related_ids": ("MEM-ffc0c2af5cfa48d7aee7332a290a3d0e",),
    },
    {
        "case_id": "REVISION_HARD_PARAPHRASE",
        "kind": "POSITIVE",
        "difficulty": "HARD",
        "query": "subsequent finding updates the violet calibration result",
        "expected_primary_ids": ("MEM-ffc0c2af5cfa48d7aee7332a290a3d0e",),
        "expected_related_ids": ("MEM-00b3fbfd4d73404f97a95c238596ab94",),
    },
    {
        "case_id": "SATELLITE_PARAPHRASE",
        "kind": "POSITIVE",
        "difficulty": "MEDIUM",
        "query": "side note providing context for the calibration core",
        "expected_primary_ids": ("MEM-1d0092cb66f44996b74604670a853a21",),
        "expected_related_ids": ("MEM-00b3fbfd4d73404f97a95c238596ab94",),
    },
    {
        "case_id": "PLANETARY_NEGATIVE",
        "kind": "NEGATIVE",
        "difficulty": "CONTROL",
        "query": "planetary gravity trajectories",
        "expected_primary_ids": (),
        "expected_related_ids": (),
    },
    {
        "case_id": "ADVERTISING_NEGATIVE",
        "kind": "NEGATIVE",
        "difficulty": "CONTROL",
        "query": "advertising contextual influence",
        "expected_primary_ids": (),
        "expected_related_ids": (),
    },
)


def _phase3i_candidate_evidence(runtime: Any, record_id: str, query: str) -> dict[str, Any]:
    detail = runtime.galaxy_record(record_id)
    if not detail or not detail.get("record"):
        return {"record_id": record_id, "missing": True}
    record = detail["record"]
    origins = _match_origin(runtime, record, query)
    concepts = _unique_query_concepts(origins)
    statement = sorted({row["concept"] for row in origins if row["statement"]})
    notes_only = sorted({
        row["concept"] for row in origins if row["notes"] and not row["statement"]
    })
    scope_only = sorted({
        row["concept"] for row in origins
        if row["scope_virtual_memory"] and not row["statement"] and not row["notes"]
    })
    return {
        "record_id": record_id,
        "statement": record.get("statement"),
        "source": record.get("source"),
        "statement_backed_concepts": statement,
        "notes_backed_only_concepts": notes_only,
        "scope_only_concepts": scope_only,
        "distinct_query_concept_count": len(concepts),
        "alias_groups": {
            concept: tokens for concept, tokens in concepts.items() if len(tokens) > 1
        },
        "metadata_or_scope_only": not bool(statement),
        "missing": False,
    }


def generalization_suite(runtime: Any, *, limit: int = 10) -> dict[str, Any]:
    """Read-only paraphrase and near-miss evaluation of the existing gate.

    This measures the current candidate gate. It does not add aliases, change
    admission thresholds, mutate records, or install Phase3H grouping.
    Expected IDs are a calibration-fixture oracle used only to score these
    predefined cases.
    """
    if not 1 <= int(limit) <= 10:
        raise ValueError("Generalization suite limit must be between 1 and 10")

    cases = []
    all_expected_ids = {
        record_id
        for case in PHASE3I_CASES
        for record_id in (
            tuple(case["expected_primary_ids"]) + tuple(case["expected_related_ids"])
        )
    }
    fixture_missing_ids = sorted(
        record_id for record_id in all_expected_ids
        if not runtime.galaxy_record(record_id)
    )

    for case in PHASE3I_CASES:
        query = str(case["query"])
        pool = runtime.galaxy_phase3_candidate_pool(
            query, scope="MemoryOS", limit=limit,
        )
        candidate_ids = list(pool.get("candidate_record_ids") or [])
        candidate_count = pool.get("candidate_count")
        receipt_well_formed = (
            isinstance(candidate_count, int)
            and not isinstance(candidate_count, bool)
            and candidate_count == len(candidate_ids)
            and len(candidate_ids) == len(set(candidate_ids))
        )
        evidence = [
            _phase3i_candidate_evidence(runtime, record_id, query)
            for record_id in candidate_ids
        ]
        missing_candidate_records = [
            row["record_id"] for row in evidence if row.get("missing")
        ]
        expected_primary = list(case["expected_primary_ids"])
        expected_related = list(case["expected_related_ids"])
        allowed = set(expected_primary + expected_related)
        found_primary = [rid for rid in expected_primary if rid in candidate_ids]
        missing_primary = [rid for rid in expected_primary if rid not in candidate_ids]
        found_related = [rid for rid in expected_related if rid in candidate_ids]
        unexpected = [rid for rid in candidate_ids if rid not in allowed]
        metadata_only = [
            row["record_id"] for row in evidence
            if not row.get("missing") and row.get("metadata_or_scope_only")
        ]
        kind = str(case["kind"])
        if kind == "NEGATIVE":
            case_status = (
                "NEGATIVE_CONTROL_PASS"
                if receipt_well_formed and candidate_count == 0
                else "NEGATIVE_CONTROL_LEAK"
            )
        elif missing_primary:
            case_status = "POSITIVE_PRIMARY_MISS"
        elif unexpected or metadata_only:
            case_status = "POSITIVE_PRIMARY_FOUND_WITH_NOISE"
        else:
            case_status = "POSITIVE_PRIMARY_FOUND_CLEAN"

        cases.append({
            "case_id": case["case_id"],
            "kind": kind,
            "difficulty": case["difficulty"],
            "query": query,
            "scope_eligible_population_count": pool.get("scope_eligible_population_count"),
            "candidate_count": candidate_count,
            "candidate_record_ids": candidate_ids,
            "ambiguous_record_ids": list(pool.get("ambiguous_record_ids") or []),
            "receipt_well_formed": receipt_well_formed,
            "expected_primary_ids": expected_primary,
            "expected_primary_found_ids": found_primary,
            "expected_primary_missing_ids": missing_primary,
            "expected_related_ids": expected_related,
            "expected_related_found_ids": found_related,
            "unexpected_candidate_ids": unexpected,
            "metadata_or_scope_only_candidate_ids": metadata_only,
            "missing_candidate_record_ids": missing_candidate_records,
            "candidate_evidence": evidence,
            "case_status": case_status,
        })

    positives = [case for case in cases if case["kind"] == "POSITIVE"]
    negatives = [case for case in cases if case["kind"] == "NEGATIVE"]
    positive_primary_recall_all = all(
        not case["expected_primary_missing_ids"] for case in positives
    )
    negatives_zero = all(
        case["case_status"] == "NEGATIVE_CONTROL_PASS" for case in negatives
    )
    receipts_well_formed = all(case["receipt_well_formed"] for case in cases)
    no_missing_candidate_records = all(
        not case["missing_candidate_record_ids"] for case in cases
    )
    no_metadata_only_positive_candidates = all(
        not case["metadata_or_scope_only_candidate_ids"] for case in positives
    )
    hard_case = next(
        case for case in cases if case["case_id"] == "REVISION_HARD_PARAPHRASE"
    )
    hard_paraphrase_primary_found = not bool(hard_case["expected_primary_missing_ids"])

    generalization_gate_pass = all((
        not fixture_missing_ids,
        positive_primary_recall_all,
        negatives_zero,
        receipts_well_formed,
        no_missing_candidate_records,
        no_metadata_only_positive_candidates,
        hard_paraphrase_primary_found,
    ))
    return {
        "schema": "gaiaos.galaxy.phase3i-generalization-suite.v1",
        "version": PHASE3I_VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": (
            "PASS_READ_ONLY_GENERALIZATION_GATE"
            if generalization_gate_pass else "OBSERVED_REVIEW_REQUIRED"
        ),
        "case_count": len(cases),
        "cases": cases,
        "checks": {
            "fixture_records_present": not fixture_missing_ids,
            "positive_primary_recall_all": positive_primary_recall_all,
            "negative_controls_zero_candidates": negatives_zero,
            "all_receipts_well_formed": receipts_well_formed,
            "all_candidate_records_inspected": no_missing_candidate_records,
            "no_metadata_or_scope_only_positive_candidates": no_metadata_only_positive_candidates,
            "hard_paraphrase_primary_found": hard_paraphrase_primary_found,
            "zero_memory_writes": True,
            "production_candidate_admission_modified": False,
            "actual_80_20_ranking_modified": False,
            "phase3h_grouping_installed_in_production": False,
            "unrestricted_global_weighting_enabled": False,
        },
        "fixture_missing_ids": fixture_missing_ids,
        "proof_boundary": (
            "Read-only evaluation of the EXISTING relevance gate against a small "
            "controlled paraphrase/near-miss fixture suite. Expected record IDs are "
            "test oracle labels, not retrieval rules. PASS would not prove universal "
            "semantic reasoning; REVIEW_REQUIRED identifies concrete generalization "
            "or precision failures to engineer before any production activation."
        ),
    }
