"""Exact, user-confirmed GALAXY Phase-5 shadow-synthesis control boundary.

No code in this module runs at import or review time that changes MemoryOS.
Source exposure != permission to execute. One signed-session, CSRF-protected
browser POST and a fresh explicit operator confirmation are required per step.
"""
from __future__ import annotations

from typing import Any
import galaxy_phase5 as p5

VERSION = "galaxy.phase5.control-exposure.v1"
CONFIRMATIONS = {
    "PROPOSE": p5.PROPOSE_CONFIRMATION,
    "VERIFY": p5.VERIFY_CONFIRMATION,
    "REVOKE": p5.REVOKE_CONFIRMATION,
}
EXPECTED_STATE = {
    "PROPOSE": "SYNTHESIS_PROPOSED",
    "VERIFY": "SYNTHESIS_VERIFIED_SHADOW",
    "REVOKE": "SYNTHESIS_REVOKED",
}
EXPECTED_EDGE_STATE = {
    "PROPOSE": "PROPOSED",
    "VERIFY": "VERIFIED",
    "REVOKE": "REVOKED",
}


def inspect(runtime: Any) -> dict[str, Any]:
    """Read-only status, exact target, and eligible *next* actions."""
    design = p5.mutation_design_review(runtime)
    current = runtime.galaxy_find_synthesis(list(p5.FIXTURE_SOURCE_IDS))
    record = (current or {}).get("record") or {}
    current_id = str(record.get("record_id") or "")
    state = str(record.get("status") or "ABSENT")
    can_propose = (
        design.get("status") == "PASS_READ_ONLY_PHASE5_MUTATION_DESIGN"
        and not current_id
    )
    return {
        "schema": "gaiaos.galaxy.phase5-control-review.v1",
        "version": VERSION,
        "execution": "READ_ONLY",
        "authority": "NAOMI",
        "controlled_source_record_ids": list(p5.FIXTURE_SOURCE_IDS),
        "exact_statement": p5.CONTROLLED_SYNTHESIS_STATEMENT,
        "shadow_scope": p5.SHADOW_SCOPE,
        "current_synthesis_record_id": current_id or None,
        "current_state": state,
        "eligible_actions": {
            "PROPOSE": can_propose,
            "VERIFY": bool(current_id and state == "SYNTHESIS_PROPOSED"),
            "REVOKE": bool(current_id and state == "SYNTHESIS_VERIFIED_SHADOW"),
        },
        "confirmations": dict(CONFIRMATIONS),
        "design_status": design.get("status"),
        "hold_reasons": list(design.get("hold_reasons") or []),
        "memoryos_retrieval_changed": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "writes": 0,
        "proof_boundary": (
            "Status and confirmation pages perform no writes. Each exact controlled "
            "POST must carry a signed browser session, valid CSRF, explicit Naomi "
            "approval and its own step-specific confirmation. Exposure alone "
            "does not authorize any synthesis mutation."
        ),
    }


def execute(
    runtime: Any,
    operation: str,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
    synthesis_record_id: str = "",
    reason: str = "",
) -> dict[str, Any]:
    """Dispatch just one exact controlled shadow step and verify actual readback."""
    operation = str(operation or "").strip().upper()
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Explicit Naomi approval required for Phase-5 control")
    if operation not in CONFIRMATIONS or confirmation != CONFIRMATIONS[operation]:
        raise PermissionError("Unknown operation or exact Phase-5 confirmation mismatch")

    before = inspect(runtime)
    if before["eligible_actions"].get(operation) is not True:
        raise ValueError(f"Phase-5 {operation} is not eligible in current state")
    expected_id = before.get("current_synthesis_record_id") or ""
    requested_id = str(synthesis_record_id or "").strip()
    if operation == "PROPOSE":
        if requested_id:
            raise ValueError("Proposal cannot select arbitrary synthesis record")
    elif not expected_id or requested_id != expected_id:
        raise ValueError("Phase-5 control target must match the unique active fixture")

    sources_before = {}
    for record_id in p5.FIXTURE_SOURCE_IDS:
        detail = runtime.galaxy_record(record_id)
        if not detail or not detail.get("record"):
            raise ValueError("Controlled source disappeared during preflight")
        sources_before[record_id] = dict(detail["record"])

    if operation == "PROPOSE":
        effect = p5.propose_controlled_synthesis(
            runtime,
            authority=authority,
            approved=True,
            confirmation=confirmation,
        )
        effect_id = str((effect.get("effect") or {}).get("synthesis_record_id") or "")
    elif operation == "VERIFY":
        effect = p5.verify_controlled_synthesis(
            runtime,
            requested_id,
            authority=authority,
            approved=True,
            confirmation=confirmation,
        )
        effect_id = requested_id
    else:
        reason = str(reason or "").strip()
        if not reason or len(reason) > 512:
            raise ValueError("Bounded nonempty revocation reason required")
        effect = p5.revoke_controlled_synthesis(
            runtime,
            requested_id,
            authority=authority,
            approved=True,
            reason=reason,
            confirmation=confirmation,
        )
        effect_id = requested_id

    readback = runtime.galaxy_synthesis(effect_id) if effect_id else None
    record = (readback or {}).get("record") or {}
    synthesis = (readback or {}).get("synthesis") or {}
    edges = (readback or {}).get("derived_from_edges") or []
    expected_sources = list(p5.FIXTURE_SOURCE_IDS)
    sources_after = {}
    for record_id in expected_sources:
        detail = runtime.galaxy_record(record_id)
        sources_after[record_id] = dict((detail or {}).get("record") or {})
    checks = {
        "effect_status": effect.get("status") == {
            "PROPOSE": "PROPOSED", "VERIFY": "VERIFIED_SHADOW", "REVOKE": "REVOKED"
        }[operation],
        "record_state_readback": record.get("status") == EXPECTED_STATE[operation],
        "fixed_statement_readback": record.get("statement") == p5.CONTROLLED_SYNTHESIS_STATEMENT,
        "shadow_scope_readback": record.get("scope") == p5.SHADOW_SCOPE,
        "exact_source_set_readback": synthesis.get("source_record_ids") == expected_sources,
        "exact_provenance_edges_readback": (
            len(edges) == len(expected_sources)
            and {edge.get("target_record_id") for edge in edges} == set(expected_sources)
            and all(
                edge.get("source_record_id") == effect_id
                and edge.get("relation_type") == "DERIVED_FROM"
                and edge.get("status") == EXPECTED_EDGE_STATE[operation]
                for edge in edges
            )
        ),
        "source_records_unchanged": sources_before == sources_after,
    }
    return {
        "schema": "gaiaos.galaxy.phase5-control-receipt.v1",
        "version": VERSION,
        "operation": operation,
        "execution": "OBSERVED_RUNTIME_FOR_THIS_CALL",
        "status": "PASS_READBACK" if all(checks.values()) else "HOLD_READBACK",
        "checks": checks,
        "synthesis_record_id": effect_id or None,
        "effect_receipt": effect,
        "readback": readback,
        "source_history_preserved": checks["source_records_unchanged"],
        "physical_delete": False,
        "production_retrieval_changed": False,
        "memoryos_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "Only this controlled fixture and current runtime were checked. "
            "A PASS does not promote the synthesis, prove restart persistence "
            "or authorize production retrieval effects."
        ),
    }
