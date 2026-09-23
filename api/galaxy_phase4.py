"""GALAXY Phase 4 bounded revision/supersession semantics.

Source design is conservative by construction:
- REVISES != SUPERSEDES.
- source=B, target=A means B REVISES/SUPERSEDES A.
- SUPERSEDES requires a VERIFIED REVISES edge for the same pair first.
- reverse revision/supersession edges and competing superseders fail closed.
- revocation changes edge state to REVOKED; it never deletes memory or edges.
- no production retrieval path is enabled here.
"""
from __future__ import annotations

from typing import Any

VERSION = "galaxy.phase4.revision-supersession.v1"
ALLOWED_RELATIONS = frozenset({"REVISES", "SUPERSEDES"})
CLASSIFIER = "GALAXY_PHASE4_REVISION_LADDER_V1"
FIXTURE_REVISION_ID = "MEM-ffc0c2af5cfa48d7aee7332a290a3d0e"
FIXTURE_CORE_ID = "MEM-00b3fbfd4d73404f97a95c238596ab94"


def _relation_type(value: str) -> str:
    relation_type = str(value or "").strip().upper()
    if relation_type not in ALLOWED_RELATIONS:
        raise ValueError("Phase 4 relation_type must be REVISES or SUPERSEDES")
    return relation_type


def _detail(runtime: Any, record_id: str) -> dict[str, Any]:
    detail = runtime.galaxy_record(record_id)
    if not detail or not detail.get("record"):
        raise KeyError(record_id)
    return detail


def _pair_edges(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
) -> list[dict[str, Any]]:
    relations = list(_detail(runtime, source_record_id).get("relations") or [])
    return [
        edge for edge in relations
        if str(edge.get("source_record_id")) == source_record_id
        and str(edge.get("target_record_id")) == target_record_id
        and str(edge.get("relation_type")) in ALLOWED_RELATIONS
    ]


def _verified_pair_edges(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
) -> list[dict[str, Any]]:
    return [
        edge for edge in _pair_edges(runtime, source_record_id, target_record_id)
        if str(edge.get("status")) == "VERIFIED"
    ]


def _reverse_verified_edges(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
) -> list[dict[str, Any]]:
    relations = list(_detail(runtime, target_record_id).get("relations") or [])
    return [
        edge for edge in relations
        if str(edge.get("source_record_id")) == target_record_id
        and str(edge.get("target_record_id")) == source_record_id
        and str(edge.get("relation_type")) in ALLOWED_RELATIONS
        and str(edge.get("status")) == "VERIFIED"
    ]


def _competing_superseders(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
) -> list[dict[str, Any]]:
    relations = list(_detail(runtime, target_record_id).get("relations") or [])
    return [
        edge for edge in relations
        if str(edge.get("target_record_id")) == target_record_id
        and str(edge.get("source_record_id")) != source_record_id
        and str(edge.get("relation_type")) == "SUPERSEDES"
        and str(edge.get("status")) == "VERIFIED"
    ]


def _project_target_state(current: dict[str, Any], relation_type: str) -> dict[str, Any]:
    relation_type = _relation_type(relation_type)
    current_state = str(current.get("state") or "")
    active = str(current.get("record_status") or "").upper() == "ACTIVE"

    if not active:
        projected_state = "NONACTIVE_HISTORICAL"
        eligible = False
        companion = False
    elif relation_type == "SUPERSEDES":
        projected_state = "HISTORICAL_SUPERSEDED"
        eligible = False
        companion = True
    elif current_state == "HISTORICAL_SUPERSEDED":
        projected_state = current_state
        eligible = False
        companion = True
    else:
        projected_state = "CURRENT_REVISED_CONTEXT"
        eligible = True
        companion = True

    return {
        "state": projected_state,
        "current_default_eligible": eligible,
        "historical_retrieval_eligible": True,
        "revision_companion_required_when_material": companion,
    }


def review_pair(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
    relation_type: str = "REVISES",
) -> dict[str, Any]:
    """Read-only review of one proposed Phase-4 relation."""
    relation_type = _relation_type(relation_type)
    source_record_id = str(source_record_id or "").strip()
    target_record_id = str(target_record_id or "").strip()
    if not source_record_id or not target_record_id:
        raise ValueError("source_record_id and target_record_id are required")
    if source_record_id == target_record_id:
        return {
            "schema": "gaiaos.galaxy.phase4-pair-review.v1",
            "version": VERSION,
            "execution": "READ_ONLY",
            "status": "HOLD",
            "hold_reasons": ["SELF_RELATION_FORBIDDEN"],
            "source_record_id": source_record_id,
            "target_record_id": target_record_id,
            "relation_type": relation_type,
            "zero_memory_writes": True,
            "production_retrieval_changed": False,
        }

    source = _detail(runtime, source_record_id)["record"]
    target = _detail(runtime, target_record_id)["record"]
    before_source = runtime.galaxy_governing_state(source_record_id)
    before_target = runtime.galaxy_governing_state(target_record_id)
    pair_verified = _verified_pair_edges(runtime, source_record_id, target_record_id)
    reverse_verified = _reverse_verified_edges(runtime, source_record_id, target_record_id)
    competing = _competing_superseders(runtime, source_record_id, target_record_id)

    verified_revises = [
        edge for edge in pair_verified
        if edge.get("relation_type") == "REVISES"
    ]
    verified_same = [
        edge for edge in pair_verified
        if edge.get("relation_type") == relation_type
    ]

    hold_reasons: list[str] = []
    if str(source.get("scope")) != str(target.get("scope")):
        hold_reasons.append("CROSS_SCOPE_PAIR_NOT_ALLOWED_IN_INITIAL_PHASE4_SLICE")
    if reverse_verified:
        hold_reasons.append("DIRECT_REVISION_CYCLE_RISK")
    if competing:
        hold_reasons.append("COMPETING_VERIFIED_SUPERSEDER")
    if relation_type == "SUPERSEDES" and not verified_revises and not verified_same:
        hold_reasons.append("SUPERSEDES_REQUIRES_VERIFIED_REVISES_SAME_PAIR")

    projected_target = _project_target_state(before_target, relation_type)
    return {
        "schema": "gaiaos.galaxy.phase4-pair-review.v1",
        "version": VERSION,
        "execution": "READ_ONLY",
        "authority": "NAOMI",
        "status": "PASS_READ_ONLY_REVIEW" if not hold_reasons else "HOLD",
        "source_record_id": source_record_id,
        "target_record_id": target_record_id,
        "relation_type": relation_type,
        "direction_semantics": "B REVISES/SUPERSEDES A => source=B, target=A",
        "source_scope": source.get("scope"),
        "target_scope": target.get("scope"),
        "existing_verified_pair_edges": pair_verified,
        "existing_verified_same_relation": verified_same,
        "verified_revises_prerequisite_present": bool(verified_revises),
        "reverse_verified_revision_edges": reverse_verified,
        "competing_verified_superseders": competing,
        "before": {
            "source_governing_state": before_source,
            "target_governing_state": before_target,
        },
        "projected_after_verification": {
            "source_governing_state": before_source,
            "target_governing_state": projected_target,
        },
        "hold_reasons": hold_reasons,
        "checks": {
            "revises_is_not_supersedes": True,
            "newer_is_not_automatically_truer": True,
            "history_preserved": True,
            "physical_delete": False,
            "same_scope_initial_slice": str(source.get("scope")) == str(target.get("scope")),
            "direct_cycle_absent": not reverse_verified,
            "competing_superseder_absent": not competing,
            "supersedes_prerequisite_satisfied": (
                relation_type == "REVISES"
                or bool(verified_revises)
                or bool(verified_same)
            ),
            "zero_memory_writes": True,
            "production_retrieval_changed": False,
            "unrestricted_global_weighting_enabled": False,
        },
        "next_gate": (
            "EXPLICIT_NAOMI_RELATION_PROPOSAL_AUTHORIZATION"
            if not hold_reasons and not verified_same
            else "ALREADY_VERIFIED_REVIEW_ONLY"
            if verified_same and not hold_reasons
            else "REPAIR_OR_RESOLVE_HOLD"
        ),
        "proof_boundary": (
            "This is a deterministic read-only relation/governance preview. "
            "It does not propose, verify, revoke, delete, or alter production retrieval."
        ),
    }


def fixture_review(runtime: Any) -> dict[str, Any]:
    """Read-only Phase-4 smoke suite over the controlled revision/core pair."""
    revises = review_pair(
        runtime, FIXTURE_REVISION_ID, FIXTURE_CORE_ID, "REVISES"
    )
    supersedes = review_pair(
        runtime, FIXTURE_REVISION_ID, FIXTURE_CORE_ID, "SUPERSEDES"
    )
    checks = {
        "revises_review_ready": revises.get("status") == "PASS_READ_ONLY_REVIEW",
        "verified_revises_visible": bool(
            revises.get("verified_revises_prerequisite_present")
        ),
        "supersedes_review_ready_after_verified_revises": (
            supersedes.get("status") == "PASS_READ_ONLY_REVIEW"
            and supersedes.get("checks", {}).get(
                "supersedes_prerequisite_satisfied"
            ) is True
        ),
        "history_preserved": (
            revises.get("checks", {}).get("history_preserved") is True
            and supersedes.get("checks", {}).get("history_preserved") is True
        ),
        "zero_memory_writes": True,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
    }
    status = (
        "PASS_READ_ONLY_PHASE4_FIXTURE_REVIEW"
        if all((
            checks["revises_review_ready"],
            checks["verified_revises_visible"],
            checks["supersedes_review_ready_after_verified_revises"],
            checks["history_preserved"],
        ))
        else "HOLD"
    )
    return {
        "schema": "gaiaos.galaxy.phase4-fixture-review.v1",
        "version": VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": status,
        "revises": revises,
        "supersedes": supersedes,
        "checks": checks,
        "next_gate": (
            "EXPLICIT_NAOMI_AUTHORIZATION_BEFORE_ANY_PHASE4_MUTATION_ROUTE"
            if status == "PASS_READ_ONLY_PHASE4_FIXTURE_REVIEW"
            else "REPAIR_BEFORE_MUTATION"
        ),
        "proof_boundary": (
            "Fixture review proves only read-only Phase-4 semantics on the controlled "
            "revision/core pair. No relation mutation or production retrieval effect occurs."
        ),
    }


def propose_transition(
    runtime: Any,
    source_record_id: str,
    target_record_id: str,
    relation_type: str,
    *,
    strength: float,
    evidence: dict[str, Any],
    authority: str,
    approved: bool,
    confirmation: str,
) -> dict[str, Any]:
    """Create only a PROPOSED Phase-4 edge after an explicit Naomi action."""
    relation_type = _relation_type(relation_type)
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Phase-4 proposal requires explicit Naomi approval")
    if confirmation != "PROPOSE_GALAXY_PHASE4_RELATION":
        raise PermissionError("Exact Phase-4 proposal confirmation required")

    review = review_pair(
        runtime, source_record_id, target_record_id, relation_type
    )
    if review.get("status") != "PASS_READ_ONLY_REVIEW":
        return {
            "schema": "gaiaos.galaxy.phase4-proposal.v1",
            "version": VERSION,
            "status": "HOLD",
            "review": review,
            "mutation_performed": False,
        }
    if review.get("existing_verified_same_relation"):
        return {
            "schema": "gaiaos.galaxy.phase4-proposal.v1",
            "version": VERSION,
            "status": "ALREADY_VERIFIED",
            "review": review,
            "mutation_performed": False,
        }

    result = runtime.galaxy_propose_relation(
        source_record_id=source_record_id,
        target_record_id=target_record_id,
        relation_type=relation_type,
        strength=float(strength),
        evidence=dict(evidence or {}),
        classifier=CLASSIFIER,
    )
    return {
        "schema": "gaiaos.galaxy.phase4-proposal.v1",
        "version": VERSION,
        "status": result.get("status"),
        "proposal": result,
        "governing_state_changed": False,
        "production_retrieval_changed": False,
        "physical_delete": False,
    }


def verify_transition(
    runtime: Any,
    edge_id: str,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
) -> dict[str, Any]:
    """Verify one PROPOSED Phase-4 edge after re-running all pair guards."""
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Phase-4 verification requires explicit Naomi approval")
    if confirmation != "VERIFY_GALAXY_PHASE4_RELATION":
        raise PermissionError("Exact Phase-4 verification confirmation required")

    edge = runtime.galaxy_relation(edge_id)
    if edge is None:
        raise KeyError(edge_id)
    relation_type = _relation_type(str(edge.get("relation_type") or ""))
    source_record_id = str(edge.get("source_record_id"))
    target_record_id = str(edge.get("target_record_id"))
    review = review_pair(
        runtime, source_record_id, target_record_id, relation_type
    )
    if review.get("status") != "PASS_READ_ONLY_REVIEW":
        return {
            "schema": "gaiaos.galaxy.phase4-verification.v1",
            "version": VERSION,
            "status": "HOLD",
            "review": review,
            "mutation_performed": False,
        }

    before_source = runtime.galaxy_governing_state(source_record_id)
    before_target = runtime.galaxy_governing_state(target_record_id)
    verified = runtime.galaxy_verify_relation(
        edge_id, authority=authority, approved=approved
    )
    after_source = runtime.galaxy_governing_state(source_record_id)
    after_target = runtime.galaxy_governing_state(target_record_id)
    return {
        "schema": "gaiaos.galaxy.phase4-verification.v1",
        "version": VERSION,
        "status": "VERIFIED",
        "relation": verified,
        "before": {
            "source_governing_state": before_source,
            "target_governing_state": before_target,
        },
        "after": {
            "source_governing_state": after_source,
            "target_governing_state": after_target,
        },
        "history_preserved": True,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
    }


def revoke_transition(
    runtime: Any,
    edge_id: str,
    *,
    authority: str,
    approved: bool,
    reason: str,
    confirmation: str,
) -> dict[str, Any]:
    """Revoke a VERIFIED Phase-4 edge, preserving edge and record history."""
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Phase-4 revocation requires explicit Naomi approval")
    if confirmation != "REVOKE_GALAXY_PHASE4_RELATION":
        raise PermissionError("Exact Phase-4 revocation confirmation required")

    edge = runtime.galaxy_relation(edge_id)
    if edge is None:
        raise KeyError(edge_id)
    relation_type = _relation_type(str(edge.get("relation_type") or ""))
    source_record_id = str(edge.get("source_record_id"))
    target_record_id = str(edge.get("target_record_id"))

    if relation_type == "REVISES":
        verified = _verified_pair_edges(
            runtime, source_record_id, target_record_id
        )
        if any(item.get("relation_type") == "SUPERSEDES" for item in verified):
            return {
                "schema": "gaiaos.galaxy.phase4-revocation.v1",
                "version": VERSION,
                "status": "HOLD",
                "reason": "REVOKE_SUPERSEDES_BEFORE_REVISES",
                "mutation_performed": False,
            }

    before_source = runtime.galaxy_governing_state(source_record_id)
    before_target = runtime.galaxy_governing_state(target_record_id)
    revoked = runtime.galaxy_revoke_relation(
        edge_id,
        authority=authority,
        approved=approved,
        reason=reason,
    )
    after_source = runtime.galaxy_governing_state(source_record_id)
    after_target = runtime.galaxy_governing_state(target_record_id)
    return {
        "schema": "gaiaos.galaxy.phase4-revocation.v1",
        "version": VERSION,
        "status": "REVOKED",
        "relation": revoked,
        "before": {
            "source_governing_state": before_source,
            "target_governing_state": before_target,
        },
        "after": {
            "source_governing_state": after_source,
            "target_governing_state": after_target,
        },
        "history_preserved": True,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
    }
