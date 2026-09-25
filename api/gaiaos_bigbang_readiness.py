"""Stage 7: read-only, real-store BIGBANG quality and HEATDEATH parity review.

This is a release prerequisite, NEVER an activation command. Ordinary memory
routing and the owner-controlled two-mode system remain unchanged. Only the
authenticated MCP/HTTP review surface may invoke this experimental reader.
"""
from __future__ import annotations

import importlib
from collections import Counter
from typing import Any

import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode
import legacy_memory_reader as legacy

SCHEMA = "gaiaos.bigbang.real-memory-readiness.v1"
KINDS = frozenset({"current", "historical", "negative"})
REQUIRED = {"current": 3, "historical": 1, "negative": 2}
NO_MATCH = frozenset({
    "HOLD_NO_CONFIDENT_GALAXY_MATCH", "HOLD_NO_CURRENT_MATCH", "HOLD_NO_MATCH",
})


def _hold(reason: str, **detail: Any) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD", "reason": reason,
        "release_activated": False, "mode_control_modified": False,
        "writes_performed": [], "e_lanes_modified": False,
        "results": [], **detail,
    }


def _validate(cases: Any) -> str | None:
    if not isinstance(cases, list) or not 6 <= len(cases) <= 12:
        return "SIX_TO_TWELVE_CASES_REQUIRED"
    counts: Counter[str] = Counter()
    queries: set[str] = set()
    current_ids: set[str] = set()
    for item in cases:
        if not isinstance(item, dict) or set(item) - {"kind", "query", "record_id"}:
            return "CASE_CONTRACT_INVALID"
        kind, query, rid = (item.get(k) for k in ("kind", "query", "record_id"))
        if kind not in KINDS or not isinstance(query, str):
            return "CASE_CONTRACT_INVALID"
        q = " ".join(query.casefold().split())
        if not 5 <= len(q) <= 500 or q in queries:
            return "EMPTY_TOO_LONG_OR_DUPLICATE_QUERY"
        queries.add(q)
        if kind == "negative":
            if rid is not None:
                return "NEGATIVE_CASE_MUST_HAVE_NO_RECORD_ID"
        elif not isinstance(rid, str) or not 1 <= len(rid) <= 200:
            return "POSITIVE_CASE_REQUIRES_RECORD_ID"
        if kind == "current":
            current_ids.add(rid)
        counts[kind] += 1
    if any(counts[k] < n for k, n in REQUIRED.items()):
        return "INSUFFICIENT_CURRENT_HISTORICAL_OR_NEGATIVE_COVERAGE"
    if len(current_ids) < 2:
        return "TWO_DISTINCT_CURRENT_RECORDS_REQUIRED"
    return None


def _safe_evidence(packet: Any) -> bool:
    """Check the basic evidence boundary even for negative/historical returns."""
    return (
        isinstance(packet, dict)
        and packet.get("schema") == gateway.GALAXY_SCHEMA
        and packet.get("scope") == "MemoryOS"
        and packet.get("execution") == "READ_ONLY"
        and packet.get("memory_context_authority") == "NONE"
        and packet.get("writes_performed") == []
        and isinstance(packet.get("records"), list)
        and (
            (packet.get("status") in NO_MATCH and packet.get("records") == [])
            or (
                isinstance(packet.get("historical_context"), list)
                and isinstance(packet.get("verified_linked_context"), list)
            )
        )
    )


def review(runtime: Any, cases: Any) -> dict[str, Any]:
    """Test the *configured store*; never seed records, mutate, or switch modes.

    PASS means only this explicitly supplied sample passed in this one process.
    It is not representative-corpus certification, deployment proof or consent
    to enable BIGBANG.
    """
    invalid = _validate(cases)
    if invalid:
        return _hold(invalid)
    if getattr(runtime, "_INITIALIZED", False) is not True:
        return _hold("RUNTIME_NOT_INITIALIZED")
    try:
        first = mode.mode_status(runtime)
        if first.get("schema") != mode.SCHEMA:
            return _hold("MODE_CONTROL_UNVERIFIED")
        if first.get("effective_mode") != mode.HEATDEATH or first.get(
            "bigbang_activation_enabled"
        ) is not False:
            return _hold("REVIEW_REQUIRES_RELEASE_LOCKED_HEATDEATH")
        baseline_query = next(
            item["query"] for item in cases if item["kind"] == "current"
        )
        before = gateway.read(runtime, baseline_query, "MemoryOS", 4)
        if before.get("status") != "PASS_HEATDEATH" or not gateway._validated_legacy(
            before.get("retrieval"), "MemoryOS", 4
        ):
            return _hold("NATIVE_LEGACY_BASELINE_UNVERIFIED")
        # Lazy load: an absent/broken GALAXY cannot block normal carrier boot.
        galaxy = importlib.import_module("galaxy_frontdoor_context")
        results: list[dict[str, Any]] = []
        for index, case in enumerate(cases):
            packet = galaxy.operational(runtime, case["query"], 4)
            if not _safe_evidence(packet):
                return _hold("UNVERIFIED_GALAXY_RESPONSE", failed_case=index,
                             results=results)
            current = packet["records"]
            historical = packet.get("historical_context", [])
            current_ids = [
                item.get("record", {}).get("record_id") for item in current
            ]
            historical_ids = [
                item.get("record", {}).get("record_id") for item in historical
            ]
            kind, wanted = case["kind"], case.get("record_id")
            if kind == "current":
                valid = (
                    gateway._galaxy_valid(packet, 4)
                    and wanted in current_ids
                    and wanted not in historical_ids
                )
            elif kind == "historical":
                valid = (
                    packet.get("status") == "HOLD_NO_CURRENT_MATCH"
                    and not current and not packet["verified_linked_context"]
                    and wanted in historical_ids
                    and all(
                        isinstance(item, dict)
                        and isinstance(item.get("record"), dict)
                        and item["record"].get("scope") == "MemoryOS"
                        and item["record"].get("source")
                        and item.get("source_provenance")
                            == item["record"].get("source")
                        and isinstance(item.get("governing_state"), dict)
                        and item["governing_state"].get("current_default_eligible")
                            is False
                        for item in historical
                    )
                )
            else:
                valid = (
                    packet.get("status") in NO_MATCH
                    and not current and not historical
                    and not packet.get("verified_linked_context", [])
                )
            results.append({
                "case": index, "kind": kind, "pass": bool(valid),
                "observed_status": packet.get("status"),
                "current_ids": current_ids, "historical_ids": historical_ids,
            })
        after = gateway.read(runtime, baseline_query, "MemoryOS", 4)
        final = mode.mode_status(runtime)
        mode_fields = ("effective_mode", "configured_mode", "control_version")
        parity = (
            after.get("status") == "PASS_HEATDEATH"
            and after.get("retrieval") == before["retrieval"]
            and all(first.get(field) == final.get(field) for field in mode_fields)
            and final.get("bigbang_activation_enabled") is False
        )
        passed = all(row["pass"] for row in results) and parity
        return {
            "schema": SCHEMA,
            "status": "PASS_READ_ONLY_SAMPLE_ONLY" if passed else "HOLD",
            "reason": "SAMPLE_AND_LEGACY_PARITY" if passed
                      else "CASE_FAILURE_OR_LEGACY_PARITY_FAILURE",
            "sample_count": len(cases),
            "counts": dict(Counter(item["kind"] for item in cases)),
            "results": results,
            "legacy_exact_parity": parity,
            "mode_control_unchanged": all(
                first.get(field) == final.get(field) for field in mode_fields
            ),
            "release_activated": False,
            "mode_control_modified": False, "writes_performed": [],
            "e_lanes_modified": False,
            "proof_boundary": (
                "Data-driven read-only sample on this process/store only. "
                "Real-world coverage, source/deploy parity, Turso/restart "
                "and independent HEATDEATH recovery remain separate gates. "
                "BIGBANG activation stays locked until separate Naomi approval."
            ),
        }
    except Exception as exc:
        return _hold("REVIEW_FAILED_CLOSED", error_type=type(exc).__name__)
