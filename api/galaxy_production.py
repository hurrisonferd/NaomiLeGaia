"""Phase 3F guarded, single-process production pilot for GaiaOS MemoryOS.

This is an explicit, leased, three-query production PILOT, not a global rollout.
Startup, expiry, kill switch, failed guards, and test exceptions fail closed to
ordinary unweighted MemoryOS retrieval. No memory records are mutated.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any, Callable

import galaxy_phase3_exit

VERSION = "galaxy.phase3f.guarded-production-pilot.v1"
EXIT_INTEGRATION_VERSION = galaxy_phase3_exit.VERSION
PROFILE = "CURRENT_80_20"
QUERY_INDEXES = (0, 3, 5)
MAX_LEASE_SECONDS = 600
TEST_VALID_SECONDS = 600

_LOCK = threading.RLock()
_STATE: dict[str, Any] = {
    "mode": "OFF",
    "expires_at_monotonic": 0.0,
    "test_thread": None,
    "pilot_id": None,
    "last_test": None,
    "last_rollback": None,
    "last_reason": "STARTUP_FAIL_CLOSED",
}


def _killed() -> bool:
    return os.getenv("GALAXY_PRODUCTION_PILOT_KILL_SWITCH", "").strip() == "1"


def _disable_locked(reason: str) -> None:
    _STATE["mode"] = "OFF"
    _STATE["expires_at_monotonic"] = 0.0
    _STATE["test_thread"] = None
    _STATE["pilot_id"] = None
    _STATE["last_reason"] = reason


def _refresh_locked() -> None:
    if _killed():
        if _STATE["mode"] != "OFF":
            _disable_locked("ENVIRONMENT_KILL_SWITCH")
    elif _STATE["mode"] == "PILOT" and time.monotonic() >= _STATE["expires_at_monotonic"]:
        _disable_locked("LEASE_EXPIRED")
    elif _STATE["mode"] == "TEST" and time.monotonic() >= _STATE["expires_at_monotonic"]:
        _disable_locked("TEST_LEASE_EXPIRED")


def status(runtime: Any) -> dict[str, Any]:
    with _LOCK:
        _refresh_locked()
        mode = _STATE["mode"]
        remaining = max(0, int(_STATE["expires_at_monotonic"] - time.monotonic())) if mode != "OFF" else 0
        last_test = _STATE["last_test"]
        return {
            "schema": "gaiaos.galaxy.phase3f-production-status.v1",
            "version": VERSION,
            "process_boot_id": runtime.BOOT_ID,
            "process_id": os.getpid(),
            "mode": mode,
            "kill_switch_active": _killed(),
            "remaining_lease_seconds": remaining,
            "pilot_id": _STATE["pilot_id"],
            "last_switch_test": last_test,
            "last_rollback": _STATE["last_rollback"],
            "last_reason": _STATE["last_reason"],
            "pilot_query_indexes": list(QUERY_INDEXES),
            "max_lease_seconds": MAX_LEASE_SECONDS,
            "adopted_profile": PROFILE,
            "effect_scope": "SINGLE_CARRIER_PROCESS_EXACT_QUERY_ALLOWLIST_MEMORYOS_ONLY",
            "global_production_weighted_retrieval_enabled": False,
            "ordinary_retrieval_default": "UNWEIGHTED_CONTROL",
            "restart_policy": "OFF",
            "multi_instance_consistency": "NOT_PROVEN; EACH_PROCESS_FAILS_CLOSED_INDEPENDENTLY",
            "authority": "NAOMI",
        }


def _is_allowlisted(runtime: Any, query: str, scope: str | None, limit: int) -> bool:
    if scope != "MemoryOS" or not 2 <= int(limit) <= 10:
        return False
    normalized = " ".join(str(query).lower().split())
    return any(
        normalized == " ".join(runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[i].lower().split())
        for i in QUERY_INDEXES
    )


def retrieve(runtime: Any, query: str, scope: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Real MemoryOS retrieval path: ordinary behavior unless active AND allowlisted.

    Candidate admission uses the existing Phase-3 query-first gate ONLY for
    approved pilot queries. Other queries remain on the exact legacy path.
    Gravity changes rank within the approved candidate pool, never membership.
    """
    legacy = runtime.search_records(query, limit, scope)
    with _LOCK:
        _refresh_locked()
        mode = _STATE["mode"]
        eligible_mode = (
            mode == "PILOT" or
            (mode == "TEST" and _STATE["test_thread"] == threading.get_ident())
        )
        eligible = eligible_mode and not _killed() and _is_allowlisted(runtime, query, scope, limit)
        pilot_id = _STATE["pilot_id"]
    if not eligible:
        legacy["galaxy_production"] = {
            "weighted_applied": False,
            "mode": "UNWEIGHTED_CONTROL",
            "reason": "INACTIVE_OR_OUTSIDE_EXACT_PILOT_ALLOWLIST",
            "global_production_weighted_retrieval_enabled": False,
        }
        return legacy

    try:
        pool = galaxy_phase3_exit.build_candidate_pool(
            runtime, query, scope="MemoryOS", limit=limit
        )
        if pool.get("status") != "PASS":
            raise RuntimeError("PHASE3_EXIT_ADMISSION_HOLD")
        primary_ids = list(pool.get("candidate_record_ids", []))
        context_candidates = list(pool.get("linked_context_candidates", []))
        context_control_ids = [
            str(item.get("record_id")) for item in context_candidates
        ]
        context_score_pool = {
            "candidate_record_ids": context_control_ids,
            "candidates": context_candidates,
        }
        context_scored = runtime._galaxy_phase3c_score_pool(
            context_score_pool, 0.8, 0.2
        )
        context_weighted = list(context_scored.get("weighted_order", []))
        context_weighted_ids = [
            row["record_id"] for row in context_weighted
        ]
        control_ids = primary_ids + context_control_ids
        weighted_ids = primary_ids + context_weighted_ids
        rerank_observed = context_control_ids != context_weighted_ids
        safe = (
            len(primary_ids) >= 1
            and len(control_ids) == len(set(control_ids))
            and bool(context_scored.get("candidate_set_preserved"))
            and set(context_control_ids) == set(context_weighted_ids)
            and bool(context_scored.get("top_relevance_preserved"))
            and int(
                context_scored.get("cross_relevance_tier_inversion_count") or 0
            ) == 0
            and bool(
                pool.get("checks", {}).get(
                    "all_admitted_candidates_meet_primary_rule"
                )
            )
            and bool(
                pool.get("checks", {}).get(
                    "linked_context_requires_verified_direct_primary_edge"
                )
            )
            and pool.get("checks", {}).get(
                "linked_context_admitted_to_primary_lane"
            ) is False
            and bool(
                pool.get("checks", {}).get(
                    "linked_context_ranked_only_within_context_lane"
                )
            )
        )
        if not safe:
            raise RuntimeError("CANDIDATE_OR_RELEVANCE_GUARD_FAILED")
        records = [runtime.get_record(record_id) for record_id in weighted_ids]
        if any(record is None for record in records):
            raise RuntimeError("CANDIDATE_DISAPPEARED_DURING_READ")
        with _LOCK:
            _refresh_locked()
            still_enabled = (
                not _killed() and _STATE["pilot_id"] == pilot_id
                and (
                    _STATE["mode"] == "PILOT" or (
                        _STATE["mode"] == "TEST"
                        and _STATE["test_thread"] == threading.get_ident()
                    )
                )
            )
        if not still_enabled:
            raise RuntimeError("PILOT_LEASE_OR_STATE_CHANGED")
        return {
            "records": records,
            "count": len(records),
            "runtime": runtime.SCHEMA_VERSION,
            "query_terms_applied": runtime._galaxy_query_tokens(query),
            "scope_applied": "MemoryOS",
            "query_filter_active": True,
            "galaxy_production": {
                "weighted_applied": True,
                "mode": mode,
                "pilot_id": pilot_id,
                "coefficient": PROFILE,
                "candidate_admission": "PHASE3_EXIT_LANE_PRESERVING_CONSTELLATION_V2",
                "exit_integration_version": EXIT_INTEGRATION_VERSION,
                "legacy_candidate_set_equivalence_claimed": False,
                "primary_lane_record_ids": primary_ids,
                "linked_context_control_record_ids": context_control_ids,
                "linked_context_weighted_record_ids": context_weighted_ids,
                "linked_context_ranked_only_within_context_lane": True,
                "gravity_effect_lane": "VERIFIED_LINKED_CONTEXT_ONLY",
                "statement_only_primary": True,
                "notes_or_scope_can_create_primary": False,
                "control_record_ids": control_ids,
                "weighted_record_ids": weighted_ids,
                "rerank_observed": rerank_observed,
                "candidate_set_preserved": True,
                "highest_relevance_preserved": bool(
                    context_scored.get("top_relevance_preserved")
                ),
                "cross_relevance_tier_inversions": int(
                    context_scored.get("cross_relevance_tier_inversion_count") or 0
                ),
                "zero_memory_writes": True,
                "global_production_weighted_retrieval_enabled": False,
            },
        }
    except Exception as exc:
        # A bad candidate, a changed lease, or a backend failure must not leave
        # pilot mode enabled. Fall back to the already read legacy result.
        with _LOCK:
            _disable_locked("AUTO_FAIL_CLOSED_" + type(exc).__name__)
        legacy["galaxy_production"] = {
            "weighted_applied": False,
            "mode": "UNWEIGHTED_CONTROL",
            "reason": "AUTO_FAIL_CLOSED",
            "failure_type": type(exc).__name__,
            "global_production_weighted_retrieval_enabled": False,
        }
        return legacy


def _record_ids(retrieval: dict[str, Any]) -> list[str]:
    return [str(item["record_id"]) for item in retrieval["retrieval"]["records"]]


def switch_test(runtime: Any, retrieval: Callable[[str, str, int], dict[str, Any]]) -> dict[str, Any]:
    """Exercise the INTEGRATED MemoryOS retrieval path ON, then OFF.

    TEST mode is visible only to this request's thread. Other concurrent
    requests stay unweighted, including if the test fails.
    """
    with _LOCK:
        _refresh_locked()
        if _STATE["mode"] != "OFF" or _killed():
            return {"status": "HOLD", "reason": "PILOT_NOT_OFF_OR_KILL_SWITCH", "state": status(runtime)}
        queries = [runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[i] for i in QUERY_INDEXES]
        before: list[list[str]] = []
        weighted_receipts: list[dict[str, Any]] = []
        errors: list[str] = []
        test_id = "PHASE3F-TEST-" + uuid.uuid4().hex
        try:
            before = [_record_ids(retrieval(q, "MemoryOS", 10)) for q in queries]
            _STATE["mode"] = "TEST"
            _STATE["pilot_id"] = test_id
            _STATE["test_thread"] = threading.get_ident()
            _STATE["expires_at_monotonic"] = time.monotonic() + 60
            for index, q in zip(QUERY_INDEXES, queries):
                result = retrieval(q, "MemoryOS", 10)
                pilot = result["retrieval"].get("galaxy_production") or {}
                ids = _record_ids(result)
                ok = (
                    pilot.get("weighted_applied") is True
                    and pilot.get("candidate_set_preserved") is True
                    and pilot.get("highest_relevance_preserved") is True
                    and pilot.get("cross_relevance_tier_inversions") == 0
                    and pilot.get("candidate_admission")
                    == "PHASE3_EXIT_LANE_PRESERVING_CONSTELLATION_V2"
                    and pilot.get("linked_context_ranked_only_within_context_lane")
                    is True
                    and ids == pilot.get("weighted_record_ids")
                )
                weighted_receipts.append({
                    "source_query_index": index,
                    "query": q,
                    "status": "PASS" if ok else "HOLD",
                    "candidate_count": len(ids),
                    "weighted_record_ids": ids,
                    "control_record_ids": pilot.get("control_record_ids", []),
                    "rerank_observed": pilot.get("rerank_observed") is True,
                    "candidate_admission": pilot.get("candidate_admission"),
                    "primary_lane_record_ids": pilot.get("primary_lane_record_ids", []),
                    "linked_context_control_record_ids": pilot.get(
                        "linked_context_control_record_ids", []
                    ),
                    "linked_context_weighted_record_ids": pilot.get(
                        "linked_context_weighted_record_ids", []
                    ),
                })
                if not ok:
                    errors.append("INTEGRATED_RETRIEVAL_GUARD_FAILED_FOR_QUERY_" + str(index))
                    break
        except Exception as exc:
            errors.append("SWITCH_TEST_EXCEPTION_" + type(exc).__name__)
        finally:
            _disable_locked("SWITCH_TEST_FINALLY_ROLLBACK")
        try:
            after = [_record_ids(retrieval(q, "MemoryOS", 10)) for q in queries]
            restored = before == after and len(before) == len(QUERY_INDEXES)
        except Exception as exc:
            restored = False
            after = []
            errors.append("ROLLBACK_READ_EXCEPTION_" + type(exc).__name__)
        at_least_one_real_rerank = any(
            item.get("rerank_observed") is True for item in weighted_receipts
        )
        passed = restored and len(weighted_receipts) == len(QUERY_INDEXES) and all(
            item["status"] == "PASS" for item in weighted_receipts
        ) and at_least_one_real_rerank and not errors and _STATE["mode"] == "OFF"
        receipt = {
            "schema": "gaiaos.galaxy.phase3f-live-switch-test.v1",
            "execution": "OBSERVED_RUNTIME",
            "status": "PASS" if passed else "HOLD",
            "test_id": test_id,
            "process_boot_id": runtime.BOOT_ID,
            "mode_after": _STATE["mode"],
            "effect_scope": "INTEGRATED_MEMORYOS_RETRIEVAL_TEST_THREAD_ONLY",
            "before_unweighted_control": before,
            "during_weighted": weighted_receipts,
            "after_unweighted_control": after,
            "unweighted_control_restored_exactly": restored,
            "at_least_one_real_rerank_observed": at_least_one_real_rerank,
            "exit_integration_version": EXIT_INTEGRATION_VERSION,
            "zero_memory_writes": True,
            "global_production_weighted_retrieval_enabled": False,
            "errors": errors,
            "next_gate": "GUARDED_10_MINUTE_PILOT" if passed else "REPAIR_BEFORE_ACTIVATION",
            "proof_boundary": (
                "This exercises the real MemoryOS retrieval adapter in a bounded "
                "test-thread-only ON/OFF cycle. It does not establish multi-instance "
                "rollout or restore a previously global weighted mode."
            ),
        }
        _STATE["last_test"] = {
            "status": receipt["status"],
            "test_id": test_id,
            "process_boot_id": runtime.BOOT_ID,
            "completed_monotonic": time.monotonic(),
        }
        _STATE["last_rollback"] = {
            "status": "PASS" if restored else "HOLD",
            "reason": "SWITCH_TEST",
            "test_id": test_id,
        }
        return receipt


def activate(runtime: Any, *, authority: str, approved: bool, lease_seconds: int = 600) -> dict[str, Any]:
    """Explicit, temporary, three-query process pilot. Never global."""
    with _LOCK:
        _refresh_locked()
        test = _STATE["last_test"]
        ready = bool(
            authority == "NAOMI" and approved is True and not _killed()
            and _STATE["mode"] == "OFF"
            and test and test["status"] == "PASS"
            and test["process_boot_id"] == runtime.BOOT_ID
            and time.monotonic() - test["completed_monotonic"] <= TEST_VALID_SECONDS
            and 30 <= int(lease_seconds) <= MAX_LEASE_SECONDS
        )
        if not ready:
            return {"status": "HOLD", "reason": "AUTHORITY_OR_FRESH_TEST_OR_LEASE_REQUIRED", "state": status(runtime)}
        _STATE["mode"] = "PILOT"
        _STATE["expires_at_monotonic"] = time.monotonic() + int(lease_seconds)
        _STATE["test_thread"] = None
        _STATE["pilot_id"] = "PHASE3F-PILOT-" + uuid.uuid4().hex
        _STATE["last_reason"] = "EXPLICIT_NAOMI_PILOT_ACTIVATION"
        return {
            "schema": "gaiaos.galaxy.phase3f-pilot-activation.v1",
            "status": "PILOT_ACTIVE",
            "authority": authority,
            "approved": True,
            "pilot_id": _STATE["pilot_id"],
            "query_indexes": list(QUERY_INDEXES),
            "lease_seconds": int(lease_seconds),
            "rollback_target": "UNWEIGHTED_CONTROL",
            "global_production_weighted_retrieval_enabled": False,
            "state": status(runtime),
        }


def rollback(runtime: Any, *, reason: str = "EXPLICIT_OPERATOR_ROLLBACK") -> dict[str, Any]:
    """Idempotent kill operation, even after the lease already expired."""
    with _LOCK:
        _refresh_locked()
        previous = _STATE["mode"]
        previous_id = _STATE["pilot_id"]
        _disable_locked(reason)
        _STATE["last_test"] = None  # Require fresh switch test before any reactivation.
        _STATE["last_rollback"] = {
            "status": "PASS", "reason": reason,
            "previous_mode": previous, "previous_pilot_id": previous_id,
        }
        return {
            "schema": "gaiaos.galaxy.phase3f-pilot-rollback.v1",
            "status": "ROLLED_BACK" if previous != "OFF" else "ALREADY_OFF",
            "previous_mode": previous,
            "previous_pilot_id": previous_id,
            "mode_after": "OFF",
            "global_production_weighted_retrieval_enabled": False,
            "state": status(runtime),
        }


def live_rollback_proof(runtime: Any, retrieval: Callable[[str, str, int], dict[str, Any]]) -> dict[str, Any]:
    """Observe actual active pilot retrieval, disable it, verify ordinary retrieval.

    A finally block enforces the OFF transition even if a live read fails.
    """
    with _LOCK:
        _refresh_locked()
        if _STATE["mode"] != "PILOT":
            return {"status": "HOLD", "reason": "NO_ACTIVE_PILOT_TO_ROLL_BACK", "state": status(runtime)}
        queries = [runtime.GALAXY_PHASE3C_CALIBRATION_QUERIES[i] for i in QUERY_INDEXES]
        expected_control: list[list[str]] = []
        during: list[dict[str, Any]] = []
        errors: list[str] = []
        pilot_id = _STATE["pilot_id"]
        try:
            expected_control = [
                [r["record_id"] for r in runtime.search_records(q, 10, "MemoryOS")["records"]]
                for q in queries
            ]
            for index, q in zip(QUERY_INDEXES, queries):
                result = retrieval(q, "MemoryOS", 10)
                state = result["retrieval"].get("galaxy_production") or {}
                during.append({
                    "source_query_index": index,
                    "pilot_applied": state.get("weighted_applied") is True,
                    "candidate_set_preserved": state.get("candidate_set_preserved") is True,
                    "highest_relevance_preserved": state.get("highest_relevance_preserved") is True,
                    "cross_relevance_tier_inversions": state.get("cross_relevance_tier_inversions"),
                    "record_ids": _record_ids(result),
                })
                if not during[-1]["pilot_applied"]:
                    errors.append("PILOT_NOT_APPLIED_" + str(index))
        except Exception as exc:
            errors.append("PILOT_READ_EXCEPTION_" + type(exc).__name__)
        finally:
            _disable_locked("LIVE_ROLLBACK_PROOF_FINALLY")
            _STATE["last_test"] = None
        try:
            after = [_record_ids(retrieval(q, "MemoryOS", 10)) for q in queries]
            restored = after == expected_control and len(after) == len(QUERY_INDEXES)
        except Exception as exc:
            after = []
            restored = False
            errors.append("POST_ROLLBACK_EXCEPTION_" + type(exc).__name__)
        passed = bool(
            restored and len(during) == len(QUERY_INDEXES)
            and all(item["pilot_applied"] and item["candidate_set_preserved"]
                    and item["highest_relevance_preserved"]
                    and item["cross_relevance_tier_inversions"] == 0 for item in during)
            and not errors and _STATE["mode"] == "OFF"
        )
        receipt = {
            "schema": "gaiaos.galaxy.phase3f-live-pilot-rollback.v1",
            "execution": "OBSERVED_RUNTIME",
            "status": "PASS" if passed else "HOLD",
            "pilot_id": pilot_id,
            "process_boot_id": runtime.BOOT_ID,
            "during_active_pilot": during,
            "before_legacy_record_ids": expected_control,
            "after_legacy_record_ids": after,
            "exact_legacy_restoration": restored,
            "mode_after": _STATE["mode"],
            "global_production_weighted_retrieval_enabled": False,
            "errors": errors,
            "proof_boundary": "One-process three-query active pilot rollback proof; no multi-instance claim.",
        }
        _STATE["last_rollback"] = {
            "status": receipt["status"], "reason": "LIVE_ACTIVE_PILOT",
            "pilot_id": pilot_id,
        }
        return receipt
