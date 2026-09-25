"""Stage 9I: bounded, model-free dual-source collision readback.

A signed owner COLLISION judgment permits checking two exact owner-selected
substrings against the already-approved A/B records. The existing Phase-3J
literal compiler and GALAXY operational validator remain unchanged.
Two source memberships establish retrieval evidence, NOT semantic entailment.
No model call, memory writes, mode changes or BIGBANG release are available.
"""
from __future__ import annotations

import importlib
from typing import Any

import augury_semantic_receipts as receipts
import augury_semantic_retrieval as shadow
import augury_semantic_sample as sample
import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode

SCHEMA = "gaiaos.augury.collision-two-source-shadow.v1"
PASS = "PASS_TWO_SOURCE_READBACK_ONLY"
FULL_HOLD = "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"


def _hold(reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD", "reason": reason,
        "model_called": False, "owner_receipt_verified": False,
        "quote_exact_verified": [False, False],
        "strict_literal_compiled": [False, False],
        "galaxy_readback_verified": [False, False],
        "legacy_exact_parity": False,
        "collision_entailment_independently_proven": False,
        "general_semantic_quality_proven": False,
        "historical_coverage": False, "full_readiness_status": FULL_HOLD,
        "writes_performed": [], "e_lanes_modified": False,
        "release_activated": False,
    }


def review(
    runtime: Any, *,
    owner_receipt: dict[str, Any],
    case_index: int,
    quote_a: str,
    quote_b: str,
    fingerprint_key: str | None,
) -> dict[str, Any]:
    """Two owner-chosen exact quotes, two strict GALAXY readbacks, no effects."""
    if not fingerprint_key or not receipts.verified(
        "owner", owner_receipt, owner_key=fingerprint_key
    ):
        return _hold("SIGNED_OWNER_COLLISION_REQUIRED")
    if type(case_index) is not int or case_index not in (0, 1, 2):
        return _hold("CASE_INDEX_INVALID")
    owner_case = owner_receipt["case_results"][case_index]
    if (
        owner_case["case"] != case_index
        or owner_case["owner_resolution"] != "COLLISION"
        or owner_case["owner_supported_slots"] != [0, 1]
    ):
        return _hold("OWNER_COLLISION_NOT_ADJUDICATED")
    quotes = [quote_a, quote_b]
    if any(
        not isinstance(quote, str) or not 12 <= len(quote) <= 240
        for quote in quotes
    ):
        return _hold("EXACT_TWO_QUOTES_REQUIRED")

    # First validate the exact sample from a fresh, authenticated private
    # owner preview; never permit a caller-provided statement or record ID.
    preview = shadow.owner_oracle_preview(
        runtime, fingerprint_key=fingerprint_key,
    )
    if (
        preview.get("status") != "READY_OWNER_ADJUDICATION"
        or preview.get("sample_fingerprint_bound") is not True
        or preview.get("sample_fingerprint")
            != owner_receipt["sample_fingerprint"]
    ):
        return _hold("SIGNED_OWNER_SAMPLE_CHANGED_OR_UNAVAILABLE")

    prep = readiness.prepare_technical_cases(runtime)
    cases = prep.get("partial_cases") or [
        c for c in prep.get("cases", []) if c.get("kind") != "historical"
    ]
    if readiness._validate(cases, partial=True) is not None:
        return _hold("APPROVED_FIVE_CASE_SAMPLE_UNAVAILABLE")
    ids: list[str] = []
    for case in cases:
        rid = case.get("record_id")
        if case["kind"] == "current" and rid not in ids:
            ids.append(rid)
    if len(ids) != 2 or cases[case_index]["kind"] != "current":
        return _hold("TWO_DISTINCT_CURRENT_RECORDS_REQUIRED")

    try:
        before = mode.mode_status(runtime)
        if (
            before.get("schema") != mode.SCHEMA
            or before.get("effective_mode") != mode.HEATDEATH
            or before.get("bigbang_activation_enabled") is not False
        ):
            return _hold("HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")
        snapshot = runtime.search_records("", 100, "MemoryOS")
        population = snapshot.get("records")
        if (
            not isinstance(population, list) or len(population) > 100
            or snapshot.get("scope_applied") != "MemoryOS"
        ):
            return _hold("BOUNDED_SCOPE_UNVERIFIED")
        scoped = {
            row.get("record_id"): row for row in population
            if isinstance(row, dict)
        }
        statements: list[str] = []
        bound_rows: list[dict[str, str]] = []
        for slot, rid in enumerate(ids):
            row = runtime.get_record(rid)
            governing = runtime.galaxy_governing_state(rid)
            if (
                not isinstance(row, dict) or rid not in scoped
                or row.get("record_id") != rid
                or row.get("scope") != "MemoryOS"
                or row.get("status") != "ACTIVE"
                or row.get("authority") != "NAOMI"
                or not readiness._technical_topics(row)
                or scoped[rid].get("statement") != row.get("statement")
                or not isinstance(row.get("source"), str)
                or not row["source"]
                or governing.get("current_default_eligible") is not True
                or row.get("statement") != preview["records"][slot]["statement"]
            ):
                return _hold("PRIVATE_SOURCE_PROVENANCE_UNVERIFIED")
            statements.append(row["statement"])
            bound_rows.append({
                "record_id": rid, "statement": row["statement"],
                "source": row["source"],
            })
        rebound = sample.fingerprint(
            owner_key=fingerprint_key, records=bound_rows, cases=cases,
        )
        if rebound != owner_receipt["sample_fingerprint"]:
            return _hold("SOURCE_CHANGED_BEFORE_READBACK")
        if any(quote not in statement
               for quote, statement in zip(quotes, statements)):
            return _hold("QUOTE_NOT_EXACT_APPROVED_SOURCE")
        baseline = gateway.read(
            runtime, cases[case_index]["query"], "MemoryOS", 4,
        )
        if (
            baseline.get("status") != "PASS_HEATDEATH"
            or not gateway._validated_legacy(
                baseline.get("retrieval"), "MemoryOS", 4,
            )
        ):
            return _hold("ORIGINAL_LEGACY_BASELINE_UNVERIFIED")
    except Exception:
        return _hold("BOUNDED_PRIVATE_READ_FAILED_CLOSED")

    try:
        galaxy = importlib.import_module("galaxy_frontdoor_context")
        for slot, (quote, statement) in enumerate(zip(quotes, statements)):
            query = shadow._compile_read_only_query(
                runtime, statement, quote, population,
            )
            if query is None:
                return _hold("STRICT_TWO_CONCEPT_QUOTE_COMPILATION_HOLD")
            packet = galaxy.operational(runtime, query, 4)
            if not gateway._galaxy_valid(packet, 4):
                return _hold("STRICT_GALAXY_READBACK_UNVERIFIED")
            returned = {
                item.get("record", {}).get("record_id")
                for item in packet["records"]
            }
            if ids[slot] not in returned:
                return _hold("EXACT_SOURCE_RECORD_NOT_RETRIEVED")
        after = gateway.read(
            runtime, cases[case_index]["query"], "MemoryOS", 4,
        )
        final = mode.mode_status(runtime)
        parity_fields = ("configured_mode", "effective_mode", "control_version")
        parity = (
            after.get("status") == "PASS_HEATDEATH"
            and after.get("retrieval") == baseline["retrieval"]
            and all(before.get(f) == final.get(f) for f in parity_fields)
            and final.get("bigbang_activation_enabled") is False
        )
    except Exception:
        return _hold("DUAL_SOURCE_READBACK_OR_PARITY_UNVERIFIED")
    if not parity:
        return _hold("LEGACY_PARITY_OR_RELEASE_LOCK_CHANGED")

    return {
        "schema": SCHEMA, "status": PASS, "case": case_index,
        "sample_fingerprint": rebound, "sample_fingerprint_bound": True,
        "owner_receipt_verified": True,
        "quote_exact_verified": [True, True],
        "strict_literal_compiled": [True, True],
        "galaxy_readback_verified": [True, True],
        "legacy_exact_parity": True,
        "collision_entailment_independently_proven": False,
        "general_semantic_quality_proven": False,
        "historical_coverage": False, "full_readiness_status": FULL_HOLD,
        "model_called": False, "writes_performed": [],
        "e_lanes_modified": False, "release_activated": False,
        "proof_boundary": (
            "Two owner-chosen exact source quotes independently compiled "
            "and read back under unchanged HEATDEATH parity. Source "
            "membership is not semantic entailment; original Stage7 "
            "historical and general semantic release gates remain HOLD."
        ),
    }
