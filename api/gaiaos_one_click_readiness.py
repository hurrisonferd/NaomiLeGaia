"""Stage 9L: ONE authenticated, bounded, read-only GaiaOS check suite.

One click: deployed source, HEATDEATH, Turso availability, exact technical
sample, genuine historical prerequisite, and current two-record literal read.
Only already-existing approved read operations run. No paid model calls,
memory writes, scheduled tasks, automatic merge/deploy or BIGBANG activation.

All returned values are strict finite enums, booleans, bounded integers and
the public deployed source commit. No private statement/ID/query/source/error
from an underlying tool is ever echoed to the owner browser.
"""
from __future__ import annotations

import re
from typing import Any, Callable

import gaiaos_bigbang_readiness as readiness
import gaiaos_historical_evidence_audit as history
import gaiaos_memory_mode as mode

SCHEMA = "gaiaos.stage9l.owner-one-click-safe-checks.v1"
FULL_HOLD = "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_IDENT = re.compile(r"[A-Z][A-Z0-9_]{0,95}\Z")
_PREP_REASONS = frozenset({
    "NOT_EVALUATED", "RUNTIME_NOT_INITIALIZED", "REMOTE_STORAGE_NOT_CONFIRMED",
    "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED", "SOURCE_WINDOW_INCOMPLETE",
    "TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN",
    "PARTIAL_FIVE_CASE_CONTRACT_UNSATISFIED",
    "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES", "SIX_CASE_CONTRACT_UNSATISFIED",
    "SIX_TECHNICAL_CASES_SELECTED_READ_ONLY", "SOURCE_READ_FAILED",
})
_HISTORY_REASONS = frozenset({
    "RUNTIME_NOT_INITIALIZED", "REMOTE_STORAGE_NOT_CONFIRMED",
    "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED", "BOUNDED_SOURCE_READ_FAILED",
    "BOUNDED_WINDOW_INCOMPLETE", "NO_VERIFIED_OWNER_SUPERSEDES_IN_WINDOW",
    "NO_APPROVED_TECHNICAL_SUPERSESSION_PAIR", "NO_ACTIVE_APPROVED_SUCCESSOR",
    "NO_DISTINCT_HISTORICAL_MARKER", "HISTORICAL_GOVERNING_STATE_READ_FAILED",
    "HISTORICAL_GOVERNING_STATE_UNVERIFIED", "STAGE7_SIX_CASE_CONTRACT_NOT_PREPARED",
    "HISTORICAL_CANDIDATE_PREPARED_UNTESTED",
})
_LITERAL_REASONS = frozenset({
    "NOT_EVALUATED", "TWO_APPROVED_CURRENT_TECHNICAL_RECORDS_REQUIRED",
    "HEATDEATH_RELEASE_LOCK_NOT_VERIFIED", "BOUNDED_SCAN_UNVERIFIED",
    "TARGET_OUTSIDE_VERIFIED_BOUNDED_SCOPE",
    "INSUFFICIENT_DISTINCT_LITERAL_CONCEPTS", "LITERAL_TARGET_ADMISSION_NOT_PROVEN",
    "NATIVE_LEGACY_BASELINE_UNVERIFIED", "UNVERIFIED_GALAXY_RESPONSE",
    "TWO_LITERAL_ANCHORS_AND_LEGACY_PARITY",
    "LITERAL_ANCHOR_MISS_OR_LEGACY_PARITY_FAILURE",
    "LITERAL_PROBE_FAILED_CLOSED",
})
_COUNT_NAMES = (
    "approved_technical_records_in_window",
    "verified_owner_supersedes_in_window",
    "approved_technical_pairs_in_window",
    "active_successor_pairs_in_window",
    "distinct_old_marker_pairs_in_window",
    "governed_historical_pairs_in_window",
)
_HUMAN_GATES = (
    "OWNER_SEMANTIC_ADJUDICATION_REMAINS_MANUAL",
    "GENERAL_SEMANTIC_QUALITY_UNPROVEN",
    "REAL_HISTORICAL_RETRIEVAL_UNPROVEN",
    "SECOND_MODEL_CALL_REQUIRES_NEW_OWNER_CONSENT",
    "DEPLOY_AND_BIGBANG_REQUIRE_EXPLICIT_OWNER_ACTION",
)


def _base() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "HOLD_FAILED_CLOSED",
        "checks": {},
        "next_action": "VERIFY_RELEASE_LOCK_AND_MISSING_CHECKS",
        "human_gates": list(_HUMAN_GATES),
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "full_readiness_status": FULL_HOLD,
        "bigbang_activation_enabled": False,
        "model_called": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
        "record_ids_disclosed": False,
        "statements_disclosed": False,
        "queries_disclosed": False,
        "sources_disclosed": False,
        "key_material_disclosed": False,
        "proof_boundary": (
            "Same-request read-only diagnostic evidence, not production "
            "release, model inference, historical retrieval or general semantics."
        ),
    }


def _reason(raw: Any, permitted: frozenset[str]) -> str:
    if isinstance(raw, str) and raw in permitted and _IDENT.fullmatch(raw):
        return raw
    return "UNRECOGNIZED_OR_UNVERIFIED_RESULT"


def _remote_health(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"status": "HOLD", "reason": "CARRIER_HEALTH_UNAVAILABLE"}
    proof = data.get("deployment_proof")
    if not isinstance(proof, dict):
        return {"status": "HOLD", "reason": "DEPLOYED_SOURCE_UNVERIFIED"}
    commit = proof.get("source_commit")
    verified = (
        data.get("status") == "ok"
        and data.get("service") == "gaiaos-carrier"
        and isinstance(commit, str) and bool(_SHA.fullmatch(commit))
        and proof.get("source_commit_verified") is True
    )
    return {
        "status": "PASS" if verified else "HOLD",
        "reason": "RUNNING_COMMIT_IDENTIFIED"
                  if verified else "DEPLOYED_SOURCE_UNVERIFIED",
        "running_commit": commit if verified else None,
        "proof_boundary": "Source identity reported by this running Render process.",
    }


def _heatdeath(data: Any) -> dict[str, Any]:
    valid = (
        isinstance(data, dict)
        and data.get("schema") == mode.SCHEMA
        and data.get("effective_mode") == mode.HEATDEATH
        and data.get("bigbang_activation_enabled") is False
        and data.get("writes_performed") == []
    )
    return {
        "status": "PASS" if valid else "HOLD",
        "reason": "HEATDEATH_LOCK_VERIFIED"
                  if valid else "HEATDEATH_RELEASE_LOCK_UNVERIFIED",
        "bigbang_activation_enabled": False,
    }


def _storage(data: Any) -> dict[str, Any]:
    valid = (
        isinstance(data, dict)
        and data.get("backend") == "turso_libsql"
        and data.get("remote_configured") is True
    )
    return {
        "status": "PASS" if valid else "HOLD",
        "reason": "TURSO_REMOTE_CONFIGURED"
                  if valid else "REMOTE_STORAGE_NOT_CONFIRMED",
    }


def _preflight(data: Any) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or data.get("schema") != "gaiaos.bigbang.technical-preflight.v1"
        or data.get("release_activated") is not False
        or data.get("writes_performed") != []
        or data.get("e_lanes_modified") is not False
        or data.get("record_ids_disclosed") is not False
        or data.get("statements_disclosed") is not False
        or data.get("queries_disclosed") is not False
        or data.get("review_executed") is not False
    ):
        return {"status": "HOLD", "reason": "TECHNICAL_PREFLIGHT_UNVERIFIED"}
    status = data.get("status")
    if status not in ("HOLD", "PREPARED_UNTESTED"):
        return {"status": "HOLD", "reason": "TECHNICAL_PREFLIGHT_UNVERIFIED"}
    counts = [
        data.get("current_cases_prepared"),
        data.get("distinct_current_records_capped_at_two"),
        data.get("historical_cases_prepared"),
        data.get("negative_cases_prepared"),
    ]
    if any(type(value) is not int or value < 0 or value > 6 for value in counts):
        return {"status": "HOLD", "reason": "TECHNICAL_PREFLIGHT_UNVERIFIED"}
    return {
        "status": status,
        "reason": _reason(data.get("reason"), _PREP_REASONS),
        "current_cases_prepared": counts[0],
        "distinct_current_records": counts[1],
        "historical_cases_prepared": counts[2],
        "partial_five_case_ready": data.get("partial_five_case_ready") is True,
        "historical_retrieval_tested": False,
    }


def _history(data: Any) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or data.get("schema") != history.SCHEMA
        or data.get("status") not in ("HOLD", "CANDIDATE_PRESENT_UNTESTED")
        or data.get("release_activated") is not False
        or data.get("writes_performed") != []
        or data.get("e_lanes_modified") is not False
        or data.get("model_called") is not False
        or data.get("record_ids_disclosed") is not False
        or data.get("statements_disclosed") is not False
        or data.get("markers_disclosed") is not False
        or data.get("sources_disclosed") is not False
        or data.get("historical_retrieval_proven") is not False
        or data.get("historical_retrieval_tested") is not False
        or data.get("general_semantic_quality_proven") is not False
        or type(data.get("bounded_window_complete")) is not bool
    ):
        return {"status": "HOLD", "reason": "HISTORICAL_AUDIT_UNVERIFIED"}
    reason = _reason(data.get("reason"), _HISTORY_REASONS)
    valid_candidate = (
        data["status"] == "CANDIDATE_PRESENT_UNTESTED"
        and reason == "HISTORICAL_CANDIDATE_PREPARED_UNTESTED"
        and data.get("historical_case_prepared") is True
    )
    if data["status"] == "CANDIDATE_PRESENT_UNTESTED" and not valid_candidate:
        return {"status": "HOLD", "reason": "HISTORICAL_AUDIT_UNVERIFIED"}
    out = {
        "status": data["status"],
        "reason": reason,
        "bounded_window_complete": data["bounded_window_complete"],
        "historical_case_prepared": valid_candidate,
        "historical_retrieval_proven": False,
    }
    if out["bounded_window_complete"]:
        counts = {k: data.get(k) for k in _COUNT_NAMES}
        if any(type(v) is not int or v < 0 or v > 100 for v in counts.values()):
            return {"status": "HOLD", "reason": "HISTORICAL_COUNTS_UNVERIFIED"}
        out["counts"] = counts
    return out


def _literal(data: Any) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or data.get("schema") != "gaiaos.bigbang.technical-literal-wiring.v1"
        or data.get("status") not in ("HOLD", "PASS_LITERAL_WIRING_ONLY")
        or data.get("release_activated") is not False
        or data.get("writes_performed") != []
        or data.get("e_lanes_modified") is not False
        or data.get("record_ids_disclosed") is not False
        or data.get("statements_disclosed") is not False
        or data.get("queries_disclosed") is not False
        or data.get("tokens_disclosed") is not False
        or data.get("literal_wiring_test_only") is not True
        or data.get("semantic_paraphrase_quality_tested") is not False
    ):
        return {"status": "HOLD", "reason": "LITERAL_PROBE_UNVERIFIED"}
    rows = data.get("case_results")
    if not isinstance(rows, list) or len(rows) > 2:
        return {"status": "HOLD", "reason": "LITERAL_PROBE_UNVERIFIED"}
    hits = [
        row.get("expected_record_in_current_results")
        for row in rows if isinstance(row, dict)
    ]
    if len(hits) != len(rows) or any(type(hit) is not bool for hit in hits):
        return {"status": "HOLD", "reason": "LITERAL_PROBE_UNVERIFIED"}
    parity = data.get("legacy_exact_parity") is True
    success = (
        data["status"] == "PASS_LITERAL_WIRING_ONLY"
        and len(hits) == 2 and all(hits) and parity
    )
    if data["status"] == "PASS_LITERAL_WIRING_ONLY" and not success:
        return {"status": "HOLD", "reason": "LITERAL_PROBE_UNVERIFIED"}
    return {
        "status": data["status"],
        "reason": _reason(data.get("reason"), _LITERAL_REASONS),
        "record_hits": hits,
        "legacy_exact_parity": parity,
        "semantic_quality_tested": False,
    }


def run(
    runtime: Any, *,
    carrier_health: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Run safe checks sequentially. Failure is per-step; release remains HOLD."""
    result = _base()
    checks = result["checks"]
    try:
        checks["deployment"] = _remote_health(carrier_health())
    except Exception:
        checks["deployment"] = {"status": "HOLD", "reason": "CARRIER_HEALTH_UNAVAILABLE"}

    try:
        before = mode.mode_status(runtime)
        checks["heatdeath"] = _heatdeath(before)
    except Exception:
        before = None
        checks["heatdeath"] = _heatdeath(None)
    if checks["heatdeath"]["status"] != "PASS":
        checks["memory_storage"] = {"status": "SKIPPED", "reason": "RELEASE_LOCK_UNVERIFIED"}
        checks["technical_sample"] = {"status": "SKIPPED", "reason": "RELEASE_LOCK_UNVERIFIED"}
        checks["historical_evidence"] = {"status": "SKIPPED", "reason": "RELEASE_LOCK_UNVERIFIED"}
        checks["current_literal_readback"] = {"status": "SKIPPED", "reason": "RELEASE_LOCK_UNVERIFIED"}
        result["next_action"] = "VERIFY_HEATDEATH_RELEASE_LOCK"
        return result

    try:
        checks["memory_storage"] = _storage(runtime.storage_status())
    except Exception:
        checks["memory_storage"] = _storage(None)
    if checks["memory_storage"]["status"] != "PASS":
        for name in ("technical_sample", "historical_evidence", "current_literal_readback"):
            checks[name] = {"status": "SKIPPED", "reason": "REMOTE_STORAGE_NOT_CONFIRMED"}
        result["next_action"] = "RESTORE_REMOTE_MEMORYOS_READ_ACCESS"
        return result

    try:
        checks["technical_sample"] = _preflight(readiness.technical_preflight(runtime))
    except Exception:
        checks["technical_sample"] = {
            "status": "HOLD", "reason": "TECHNICAL_PREFLIGHT_FAILED_CLOSED",
        }
    try:
        checks["historical_evidence"] = _history(history.audit(runtime))
    except Exception:
        checks["historical_evidence"] = {
            "status": "HOLD", "reason": "HISTORICAL_AUDIT_FAILED_CLOSED",
        }

    # Actual read-only literal proof requires two independently approved
    # current records. No model inference and no synthetic production writes.
    if checks["technical_sample"].get("distinct_current_records") == 2:
        try:
            checks["current_literal_readback"] = _literal(
                readiness.technical_literal_wiring_probe(runtime)
            )
        except Exception:
            checks["current_literal_readback"] = {
                "status": "HOLD", "reason": "LITERAL_PROBE_FAILED_CLOSED",
            }
    else:
        checks["current_literal_readback"] = {
            "status": "SKIPPED", "reason": "TWO_APPROVED_CURRENT_RECORDS_REQUIRED",
        }

    try:
        after = mode.mode_status(runtime)
    except Exception:
        after = None
    if (
        _heatdeath(after)["status"] != "PASS"
        or not isinstance(before, dict) or not isinstance(after, dict)
        or any(before.get(k) != after.get(k)
               for k in ("configured_mode", "effective_mode", "control_version"))
    ):
        checks["heatdeath"] = {
            "status": "HOLD", "reason": "RELEASE_LOCK_CHANGED_OR_UNVERIFIED",
        }
        result["next_action"] = "VERIFY_HEATDEATH_RELEASE_LOCK"
        return result

    result["status"] = "SAFE_CHECKS_COMPLETE_RELEASE_LOCKED"
    historical = checks["historical_evidence"]
    technical = checks["technical_sample"]
    literal = checks["current_literal_readback"]
    if checks["deployment"]["status"] != "PASS":
        result["next_action"] = "VERIFY_RUNNING_DEPLOYMENT_COMMIT"
    elif technical["status"] == "HOLD" and not technical.get("partial_five_case_ready"):
        result["next_action"] = "REVIEW_APPROVED_CURRENT_TECHNICAL_MEMORIES"
    elif historical["status"] == "HOLD":
        result["next_action"] = "RESOLVE_REAL_HISTORICAL_EVIDENCE_GAP"
    elif literal["status"] != "PASS_LITERAL_WIRING_ONLY":
        result["next_action"] = "INSPECT_CURRENT_LITERAL_READBACK"
    else:
        result["next_action"] = "OWNER_REVIEW_HISTORICAL_AND_SEMANTIC_EVIDENCE"
    return result
