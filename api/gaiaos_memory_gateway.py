"""BIGBANG/HEATDEATH Stage 3: one bounded read-only memory gateway.

The gateway imports ONLY the existing legacy reader and the durable emergency
mode service at startup. BIGBANG's GALAXY module is imported only inside a
release-gated BIGBANG request. A GALAXY import/runtime failure cannot prevent
the legacy gateway from being imported or from returning an already-verified
legacy result.

This module is a SOURCE-ONLY gateway. Ordinary GaiaOS chat/MCP entry points
are NOT switched over at Stage 3; BIGBANG is still locked in the Stage-2
mode service. The native legacy retrieval result is never changed or replaced
with fabricated memories. No reading path authorizes a memory write.
"""
from __future__ import annotations

import importlib
from typing import Any

import gaiaos_memory_mode as mode
import legacy_memory_reader as legacy

SCHEMA = "gaiaos.memory-gateway.v1"
GALAXY_SCHEMA = "gaiaos.galaxy.frontdoor-memory-context.v1"
GALAXY_RANKING = "GALAXY_STATEMENT_FIRST_80_20_RELEVANCE_TIER_GUARDED"
GALAXY_LIMIT = 4
NON_MATCH_STATUSES = frozenset({
    "HOLD_NO_CONFIDENT_GALAXY_MATCH",
    "HOLD_NO_CURRENT_MATCH",
    "HOLD_NO_MATCH",
})


def _hold(reason: str, *, control_reason: str | None = None,
          error_type: str | None = None) -> dict[str, Any]:
    """Never construct plausible empty recall in place of a failed legacy read."""
    result = {
        "schema": SCHEMA,
        "status": reason,
        "effective_mode": mode.HEATDEATH,
        "configured_mode": None,
        "control_reason": control_reason,
        "retrieval": None,
        "galaxy_context": None,
        "galaxy_applied": False,
        "fallback_occurred": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "memory_context_authority": "NONE",
        "proof_boundary": (
            "The gateway cannot verify legacy evidence. No records are returned; "
            "a HOLD is not successful recall or successful failover."
        ),
    }
    if error_type:
        result["error_type"] = error_type
    return result


def _validated_legacy(payload: Any, scope: str | None, limit: int) -> bool:
    """Require the original native envelope, not a made-up success wrapper."""
    if not isinstance(payload, dict):
        return False
    records = payload.get("records")
    return (
        isinstance(records, list)
        and all(isinstance(record, dict) for record in records)
        and isinstance(payload.get("count"), int)
        and not isinstance(payload.get("count"), bool)
        and payload["count"] == len(records)
        and len(records) <= max(1, min(limit, 100))
        and payload.get("scope_applied") == scope
        and isinstance(payload.get("query_terms_applied"), list)
        and isinstance(payload.get("query_filter_active"), bool)
        and isinstance(payload.get("runtime"), str)
    )


def _galaxy_valid(payload: Any, requested_limit: int) -> bool:
    """Fail closed when GALAXY's contract or provenance is incomplete."""
    if not isinstance(payload, dict):
        return False
    records = payload.get("records")
    if (
        payload.get("schema") != GALAXY_SCHEMA
        or payload.get("status") != "PASS_GALAXY_OPERATIONAL_RETRIEVAL"
        or payload.get("ranking") != GALAXY_RANKING
        or payload.get("galaxy_weighting_applied") is not True
        or payload.get("memory_context_authority") != "NONE"
        or payload.get("automatic_capture") is not False
        or payload.get("automatic_promotion") is not False
        or payload.get("e_lanes_modified") is not False
        or payload.get("physical_delete") is not False
        or payload.get("writes_performed") != []
        or not isinstance(records, list)
        or not records
        or len(records) > requested_limit
        or payload.get("count") != len(records)
        or not isinstance(payload.get("historical_context"), list)
        or not isinstance(payload.get("verified_linked_context"), list)
    ):
        return False
    seen: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            return False
        record = item.get("record")
        state = item.get("governing_state")
        if not isinstance(record, dict) or not isinstance(state, dict):
            return False
        rid = record.get("record_id")
        if (
            not isinstance(rid, str) or not rid or rid in seen
            or record.get("scope") != "MemoryOS"
            or not record.get("source")
            or item.get("source_provenance") != record.get("source")
            or state.get("record_id") != rid
            or state.get("current_default_eligible") is not True
            or item.get("not_identity_authority") is not True
        ):
            return False
        seen.add(rid)
    return True


def read(runtime: Any, query: str = "", scope: str | None = None,
         limit: int = 10) -> dict[str, Any]:
    """Return legacy's exact native result plus an optional gated GALAXY lane.

    HEATDEATH and BIGBANG are the only modes. A BIGBANG error explicitly falls
    back to the ALREADY RETRIEVED legacy result for this request; it does not
    silently mutate the durable mode control or grant restart persistence.
    """
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return _hold("HOLD_RUNTIME_NOT_INITIALIZED")
    if (
        not isinstance(query, str)
        or (scope is not None and (not isinstance(scope, str) or not scope))
        or isinstance(limit, bool) or not isinstance(limit, int)
    ):
        return _hold("HOLD_INPUT_INVALID")

    try:
        control = mode.mode_status(runtime)
    except Exception as exc:
        control = {
            "schema": mode.SCHEMA,
            "effective_mode": mode.HEATDEATH,
            "configured_mode": None,
            "reason": "HOLD_MODE_CONTROL_UNAVAILABLE",
            "bigbang_activation_enabled": False,
            "error_type": type(exc).__name__,
        }
    if not isinstance(control, dict) or control.get("schema") != mode.SCHEMA:
        control = {
            "effective_mode": mode.HEATDEATH,
            "configured_mode": None,
            "reason": "HOLD_MODE_CONTROL_INVALID",
            "bigbang_activation_enabled": False,
        }
    selected = control.get("effective_mode")
    bigbang_authorized = (
        selected == mode.BIGBANG
        and control.get("bigbang_activation_enabled") is True
        and control.get("configured_mode") == mode.BIGBANG
    )
    effective = mode.BIGBANG if bigbang_authorized else mode.HEATDEATH
    control_reason = control.get("reason", "HOLD_MODE_CONTROL_INVALID")

    try:
        original = legacy.read(runtime, query, scope, limit)
    except Exception as exc:
        return {
            **_hold("HOLD_LEGACY_UNAVAILABLE", control_reason=control_reason,
                    error_type=type(exc).__name__),
            "configured_mode": control.get("configured_mode"),
        }
    if not _validated_legacy(original, scope, limit):
        return {
            **_hold("HOLD_LEGACY_CONTRACT_INVALID", control_reason=control_reason),
            "configured_mode": control.get("configured_mode"),
        }

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PASS_HEATDEATH",
        "effective_mode": mode.HEATDEATH,
        "configured_mode": control.get("configured_mode"),
        "control_reason": control_reason,
        "retrieval": original,
        "galaxy_context": None,
        "galaxy_applied": False,
        "fallback_occurred": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "memory_context_authority": "NONE",
        "proof_boundary": (
            "The legacy retrieval envelope is returned unmodified from current "
            "authorized records; no memory writes, identity adoption, or "
            "application-route integration are implied."
        ),
    }
    if effective == mode.HEATDEATH:
        return result
    if scope not in (None, "MemoryOS") or not query.strip():
        return {
            **result,
            "status": "PASS_BIGBANG_LEGACY_SCOPE_ONLY",
            "effective_mode": mode.BIGBANG,
            "proof_boundary": (
                "BIGBANG is authorized but this scope/empty query is serviced "
                "by original legacy retrieval only. No GALAXY evidence is inferred."
            ),
        }

    # The GALAXY import must stay BELOW the emergency/legacy return path.
    try:
        galaxy = importlib.import_module("galaxy_frontdoor_context")
        if not hasattr(galaxy, "operational"):
            raise AttributeError("GALAXY operational reader is unavailable")
        context_limit = min(max(1, limit), GALAXY_LIMIT)
        enhanced = galaxy.operational(runtime, query, context_limit)
        if (
            isinstance(enhanced, dict)
            and enhanced.get("schema") == GALAXY_SCHEMA
            and enhanced.get("status") in NON_MATCH_STATUSES
            and enhanced.get("records") == []
            and enhanced.get("writes_performed") == []
        ):
            return {
                **result,
                "status": "HOLD_BIGBANG_NO_CONFIDENT_MATCH",
                "effective_mode": mode.BIGBANG,
                "galaxy_context": enhanced,
                "proof_boundary": (
                    "GALAXY returned an explicit no-match HOLD. Legacy evidence "
                    "remains visible in its original lane, but no semantic "
                    "GALAXY match may be inferred from legacy keyword results."
                ),
            }
        if not _galaxy_valid(enhanced, context_limit):
            raise ValueError("GALAXY evidence contract failed validation")
        return {
            **result,
            "status": "PASS_BIGBANG",
            "effective_mode": mode.BIGBANG,
            "galaxy_context": enhanced,
            "galaxy_applied": True,
            "proof_boundary": (
                "GALAXY passed the bounded read-only evidence contract in this "
                "gateway request. This is not ordinary-chat deployment proof "
                "or permission to promote, synthesize, delete or alter E-LANES."
            ),
        }
    except Exception as exc:
        return {
            **result,
            "status": "PASS_HEATDEATH_FALLBACK",
            "effective_mode": mode.HEATDEATH,
            "fallback_occurred": True,
            "fallback_reason": "GALAXY_IMPORT_OR_RUNTIME_OR_CONTRACT_FAILURE",
            "galaxy_error_type": type(exc).__name__,
            "manual_emergency_latch_required": True,
            "proof_boundary": (
                "GALAXY failed; this request explicitly fell back to a verified "
                "legacy result. The persistent mode switch has NOT been changed. "
                "A separate approved HEATDEATH latch is required before claiming "
                "restart-wide or cross-instance failover."
            ),
        }
