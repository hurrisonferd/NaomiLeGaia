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
SAFE_ADMISSION_REASONS = frozenset({
    "NO_PRIMARY_CANDIDATE", "PRIMARY_CAP_OVERFLOW",
    "EXTERNAL_DOMAIN_DISAMBIGUATOR", "HOLD_SOURCE_UNAVAILABLE",
    "HOLD_NO_CONFIDENT_GALAXY_MATCH",
})


def _hold(reason: str, **detail: Any) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD", "reason": reason,
        "release_activated": False, "mode_control_modified": False,
        "writes_performed": [], "e_lanes_modified": False,
        "results": [], **detail,
    }


def _validate(cases: Any, *, partial: bool = False) -> str | None:
    if partial:
        if not isinstance(cases, list) or len(cases) != 5:
            return "EXACTLY_FIVE_PARTIAL_CASES_REQUIRED"
    elif not isinstance(cases, list) or not 6 <= len(cases) <= 12:
        return "SIX_TO_TWELVE_CASES_REQUIRED"
    counts: Counter[str] = Counter()
    queries: set[str] = set()
    current_ids: set[str] = set()
    for item in cases:
        if not isinstance(item, dict) or set(item) - {"kind", "query", "record_id"}:
            return "CASE_CONTRACT_INVALID"
        kind, query, rid = (item.get(k) for k in ("kind", "query", "record_id"))
        if not isinstance(kind, str) or kind not in KINDS or not isinstance(query, str):
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
    if partial:
        if counts != Counter({"current": 3, "negative": 2}):
            return "PARTIAL_REQUIRES_THREE_CURRENT_TWO_NEGATIVE_NO_HISTORY"
    elif any(counts[k] < n for k, n in REQUIRED.items()):
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
        and packet.get("e_lanes_modified") is not True
        and packet.get("automatic_promotion") is not True
        and packet.get("physical_delete") is not True
        and isinstance(packet.get("records"), list)
        and (
            (packet.get("status") in NO_MATCH and packet.get("records") == [])
            or (
                isinstance(packet.get("historical_context"), list)
                and isinstance(packet.get("verified_linked_context"), list)
            )
        )
    )


def review(runtime: Any, cases: Any, *, partial: bool = False) -> dict[str, Any]:
    """Test the *configured store*; never seed records, mutate, or switch modes.

    PASS means only this explicitly supplied sample passed in this one process.
    It is not representative-corpus certification, deployment proof or consent
    to enable BIGBANG.
    """
    invalid = _validate(cases, partial=partial)
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
                    packet.get("status") == "HOLD_NO_CONFIDENT_GALAXY_MATCH"
                    and packet.get("reason") == "NO_PRIMARY_CANDIDATE"
                    and not current and not historical
                    and not packet.get("verified_linked_context", [])
                )
            results.append({
                "case": index, "kind": kind, "pass": bool(valid),
                "observed_status": packet.get("status"),
                "admission_reason": packet.get("reason")
                    if packet.get("reason") in SAFE_ADMISSION_REASONS
                    else "OTHER_OR_UNREPORTED",
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
            "status": ("PASS_PARTIAL_CURRENT_NEGATIVE_ONLY" if partial else
                       "PASS_READ_ONLY_SAMPLE_ONLY") if passed else "HOLD",
            "reason": ("PARTIAL_FIVE_CASE_PARITY_NO_HISTORICAL" if partial
                       else "SAMPLE_AND_LEGACY_PARITY") if passed
                      else "CASE_FAILURE_OR_LEGACY_PARITY_FAILURE",
            "historical_coverage": not partial,
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


# Stage 9: owner's approved GaiaOS-technical subset only. The existing
# bearer-authorized full reviewer is unchanged. Public-browser convenience
# is deliberately restricted to a redacted preparation verdict.
TECHNICAL_TOPICS = {
    "PRESERVE": ("//pw:preserve//", "power word preserve"),
    "E_LANES": ("e-lanes", "e-lane"),
    "HEATDEATH": ("heatdeath",),
    "GALAXY": ("galaxy",),
}
TECHNICAL_QUERIES = {
    "PRESERVE": (
        "What must the Power Word PRESERVE command protect?",
        "How does //PW:PRESERVE// preserve continuity?",
    ),
    "E_LANES": (
        "Why are all six E-LANES independently preserved?",
        "Which independent E-LANES survive recovery?",
    ),
    "HEATDEATH": (
        "How does HEATDEATH protect original legacy memory retrieval?",
        "What does the HEATDEATH fallback preserve?",
    ),
    "GALAXY": (
        "How does GALAXY control memory relevance and authority?",
        "Which GALAXY constraints protect memory retrieval?",
    ),
}
TECHNICAL_NEGATIVES = (
    "quantum marmalade platypus orchestra",
    "pineapple telescope opera confetti",
)
_EXCLUDED_SOURCES = ("fixture", "canary", "synthetic", "calibration", "test")
# Only explicit old-version markers can produce a distinct historical query.
# Never infer that REVISES or a lower version number means SUPERSEDES.
_OLD_VERSION_MARKER = __import__("re").compile(
    r"\b(?:v[0-9]+(?:[._-][0-9]+){1,3}|phase[ -]?[0-9][a-z]|[0-9]{2}_[0-9]{2})\b",
    __import__("re").IGNORECASE,
)


def _technical_topics(row: dict[str, Any]) -> list[str]:
    """Exclude known fixture origins. Technical keywords alone are not authority."""
    if (
        row.get("scope") != "MemoryOS"
        or row.get("authority") != "NAOMI"
        or not isinstance(row.get("statement"), str)
        or any(flag in str(row.get("source") or "").casefold()
               for flag in _EXCLUDED_SOURCES)
    ):
        return []
    statement = row["statement"].casefold()
    return [
        name for name, patterns in TECHNICAL_TOPICS.items()
        if any(pattern in statement for pattern in patterns)
    ]


def prepare_technical_cases(runtime: Any) -> dict[str, Any]:
    """SELECT-only six-case discovery. Cases stay server-side, never browser-visible.

    A historical case needs an explicit verified incoming SUPERSEDES edge
    between approved technical MemoryOS records AND a distinctive old-version
    marker absent from current technical records. No fabricated history.
    """
    preview: dict[str, Any] = {
        "schema": "gaiaos.bigbang.technical-preflight.v1",
        "status": "HOLD",
        "reason": "NOT_EVALUATED",
        "scope": "MemoryOS",
        "technical_topics": [],
        "current_cases_prepared": 0,
        "distinct_current_records_capped_at_two": 0,
        "historical_cases_prepared": 0,
        "negative_cases_prepared": 2,
        "partial_five_case_ready": False,
        "record_ids_disclosed": False,
        "statements_disclosed": False,
        "queries_disclosed": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
        "review_executed": False,
        "proof_boundary": (
            "Bounded SELECT-only candidate preparation, not a live retrieval "
            "quality result or BIGBANG authorization. Missing evidence HOLDS."
        ),
    }

    def hold(reason: str) -> dict[str, Any]:
        return {"preview": {**preview, "reason": reason}, "cases": []}

    if getattr(runtime, "_INITIALIZED", False) is not True:
        return hold("RUNTIME_NOT_INITIALIZED")
    try:
        backend = runtime.storage_status()
        if (backend.get("backend") != "turso_libsql"
                or backend.get("remote_configured") is not True):
            return hold("REMOTE_STORAGE_NOT_CONFIRMED")
        control = mode.mode_status(runtime)
        if (control.get("schema") != mode.SCHEMA
                or control.get("effective_mode") != mode.HEATDEATH
                or control.get("bigbang_activation_enabled") is not False):
            return hold("HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")
        with runtime._db() as conn:
            # 101 rows distinguish a bounded scan from assumed complete coverage.
            records = runtime._fetchall_dicts(
                conn,
                "SELECT record_id, authority, scope, statement, source, status "
                "FROM memory_records WHERE scope='MemoryOS' AND ("
                "lower(statement) LIKE '%//pw:preserve//%' OR "
                "lower(statement) LIKE '%power word preserve%' OR "
                "lower(statement) LIKE '%e-lane%' OR "
                "lower(statement) LIKE '%heatdeath%' OR "
                "lower(statement) LIKE '%galaxy%') "
                "ORDER BY created_at DESC LIMIT 101",
            )
            supersedes = runtime._fetchall_dicts(
                conn,
                "SELECT source_record_id, target_record_id, authority "
                "FROM memory_relations "
                "WHERE status='VERIFIED' AND relation_type='SUPERSEDES' "
                "AND verified_at IS NOT NULL LIMIT 101",
            )
        if len(records) > 100 or len(supersedes) > 100:
            return hold("SOURCE_WINDOW_INCOMPLETE")
        real = {row["record_id"]: row for row in records
                if _technical_topics(row) and isinstance(row.get("record_id"), str)}
        by_topic: dict[str, list[dict[str, Any]]] = {
            topic: [] for topic in TECHNICAL_TOPICS
        }
        superseded_ids = {
            edge["target_record_id"]
            for edge in supersedes
            if edge.get("authority") == "NAOMI"
            and edge.get("source_record_id") in real
            and edge.get("target_record_id") in real
            and real[edge["source_record_id"]].get("status") == "ACTIVE"
        }
        for record in real.values():
            if record.get("status") != "ACTIVE" or record["record_id"] in superseded_ids:
                continue
            for topic in _technical_topics(record):
                by_topic[topic].append(record)
        preview["technical_topics"] = [
            topic for topic, rows in by_topic.items() if rows
        ]
        # Exactly two independently grounded current records, plus a second
        # paraphrase of one. Never repeat one record as two distinct records.
        chosen: list[tuple[str, dict[str, Any]]] = []
        used: set[str] = set()
        for topic, rows in by_topic.items():
            item = next(
                (r for r in rows if r["record_id"] not in used), None
            )
            if item is not None:
                chosen.append((topic, item))
                used.add(item["record_id"])
            if len(chosen) == 2:
                break
        # Topic diversity is preferred, not mandatory. Stage 7 requires two
        # different current RECORDS, even when both concern GALAXY.
        if len(chosen) < 2:
            for topic, rows in by_topic.items():
                for record in rows:
                    if record["record_id"] not in used:
                        chosen.append((topic, record))
                        used.add(record["record_id"])
                    if len(chosen) == 2:
                        break
                if len(chosen) == 2:
                    break
        preview["distinct_current_records_capped_at_two"] = len(chosen)
        if len(chosen) < 2:
            return hold("TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN")
        if chosen[0][0] == chosen[1][0]:
            topic = chosen[0][0]
            third_query = {
                "PRESERVE": "Why must Power Word PRESERVE remain available?",
                "E_LANES": "How are six independent E-LANES protected?",
                "HEATDEATH": "What prevents HEATDEATH from activating BIGBANG?",
                "GALAXY": "Which GALAXY rules separate relevance and authority?",
            }[topic]
            queries = (*TECHNICAL_QUERIES[topic], third_query)
        else:
            queries = (
                TECHNICAL_QUERIES[chosen[0][0]][0],
                TECHNICAL_QUERIES[chosen[1][0]][0],
                TECHNICAL_QUERIES[chosen[0][0]][1],
            )
        cases = [
            {"kind": "current", "query": queries[0],
             "record_id": chosen[0][1]["record_id"]},
            {"kind": "current", "query": queries[1],
             "record_id": chosen[1][1]["record_id"]},
            {"kind": "current", "query": queries[2],
             "record_id": chosen[0][1]["record_id"]},
        ]
        preview["current_cases_prepared"] = 3
        # Match the older record by a verified directed relation, not text
        # resemblance or REVISES. Only distinctive technical version markers
        # can become historical retrieval queries.
        history: dict[str, Any] | None = None
        active_statements = [
            row["statement"].casefold()
            for rows in by_topic.values() for row in rows
        ]
        for edge in supersedes:
            old = real.get(edge.get("target_record_id"))
            new = real.get(edge.get("source_record_id"))
            if (edge.get("authority") != "NAOMI" or not old or not new
                    or new.get("status") != "ACTIVE"):
                continue
            for match in _OLD_VERSION_MARKER.finditer(old["statement"]):
                marker = match.group(0)
                if (marker.casefold() in new["statement"].casefold()
                        or any(marker.casefold() in s for s in active_statements)):
                    continue
                # Distinct version marker is still merely a prospective query.
                topic = _technical_topics(old)[0]
                q = f"{topic.replace('_', ' ')} historical {marker} behavior"
                history = {"kind": "historical", "query": q,
                           "record_id": old["record_id"]}
                break
            if history is not None:
                break
        if history is None:
            # Do not invent a historical record. Retain the three approved
            # current cases and two negatives privately for a distinct five-case
            # diagnostic. This never satisfies the six-case release gate.
            partial_cases = cases + [
                {"kind": "negative", "query": q} for q in TECHNICAL_NEGATIVES
            ]
            if _validate(partial_cases, partial=True) is not None:
                return hold("PARTIAL_FIVE_CASE_CONTRACT_UNSATISFIED")
            preview["partial_five_case_ready"] = True
            return {
                "preview": {**preview,
                            "reason": "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES"},
                "cases": [], "partial_cases": partial_cases,
            }
        cases.append(history)
        preview["historical_cases_prepared"] = 1
        cases.extend(
            {"kind": "negative", "query": q}
            for q in TECHNICAL_NEGATIVES
        )
        if _validate(cases) is not None:
            return hold("SIX_CASE_CONTRACT_UNSATISFIED")
        preview["status"] = "PREPARED_UNTESTED"
        preview["reason"] = "SIX_TECHNICAL_CASES_SELECTED_READ_ONLY"
        return {"preview": preview, "cases": cases}
    except Exception as exc:
        # Never return SQL details, row content, statements, source or secrets.
        return {
            "preview": {**preview, "reason": "SOURCE_READ_FAILED",
                        "error_type": type(exc).__name__},
            "cases": [],
        }


def technical_preflight(runtime: Any) -> dict[str, Any]:
    """Public-browser-safe result: no record IDs, statements or queries."""
    return prepare_technical_cases(runtime)["preview"]


def technical_sample_review(runtime: Any) -> dict[str, Any]:
    """Execute only an already prepared six-case sample; redact full reviewer."""
    prep = prepare_technical_cases(runtime)
    if not prep["cases"]:
        return prep["preview"]
    packet = review(runtime, prep["cases"])
    return {
        **prep["preview"],
        "status": packet.get("status", "HOLD"),
        "reason": packet.get("reason", "REVIEW_FAILED_CLOSED"),
        "review_executed": True,
        "legacy_exact_parity": packet.get("legacy_exact_parity") is True,
        "case_results": [
            {
                "case": row.get("case"), "kind": row.get("kind"),
                "pass": row.get("pass") is True,
                "admission_reason": row.get("admission_reason")
                    if row.get("admission_reason") in SAFE_ADMISSION_REASONS
                    else "OTHER_OR_UNREPORTED",
                "observed_status": (
                    row.get("observed_status")
                    if row.get("observed_status") in {
                        "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                        "HOLD_NO_CURRENT_MATCH",
                        "HOLD_NO_CONFIDENT_GALAXY_MATCH",
                        "HOLD_NO_MATCH",
                    } else "UNRECOGNIZED_STATUS"
                ),
            }
            for row in packet.get("results", [])
            if isinstance(row, dict)
        ],
        "release_activated": False,
        "writes_performed": [],
        "proof_boundary": (
            "Only the approved technical six-case sample was reviewed. "
            "All queries, records, IDs and underlying statements are redacted. "
            "No general release or production switch is authorized."
        ),
    }

def _target_query_audit(runtime: Any, cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Bearer-only numeric check on expected target statement, never raw memory."""
    try:
        import galaxy_phase3_exit as phase3
        measurements = []
        for index, case in enumerate(cases):
            if case.get("kind") != "current":
                continue
            record = runtime.get_record(case["record_id"])
            if (not isinstance(record, dict) or not _technical_topics(record)
                    or record.get("status") != "ACTIVE"):
                return {"status": "HOLD_TARGET_RECORD_UNVERIFIED", "measurements": []}
            evidence = phase3._statement_evidence(
                runtime, record["statement"], case["query"], scope="MemoryOS",
            )
            matched = int(evidence["matched_statement_concept_count"])
            coverage = float(evidence["statement_concept_coverage"])
            measurements.append({
                "case": index, "kind": "current",
                "target_meets_statement_admission": bool(
                    matched >= phase3.PRIMARY_MIN_CONCEPTS
                    and coverage >= phase3.PRIMARY_MIN_COVERAGE
                ),
                "matched_concept_count": matched,
                "query_concept_count": len(evidence["query_concepts"]),
                "concept_coverage": coverage,
                "minimum_matching_concepts": phase3.PRIMARY_MIN_CONCEPTS,
                "minimum_coverage": round(phase3.PRIMARY_MIN_COVERAGE, 6),
            })
        return {"status": "READ_ONLY_TARGET_QUERY_AUDIT",
                "measurements": measurements,
                "proof_boundary": (
                    "Selected target statement versus staged question only, "
                    "not a retrieval PASS or license to weaken admission."
                )}
    except Exception:
        return {"status": "HOLD_TARGET_QUERY_AUDIT_UNAVAILABLE",
                "measurements": []}


def technical_partial_sample_review(runtime: Any) -> dict[str, Any]:
    """Owner-only five-case diagnostic; missing history remains a release HOLD."""
    prep = prepare_technical_cases(runtime)
    cases = prep.get("partial_cases")
    if cases is None and prep["cases"]:
        cases = [c for c in prep["cases"] if c["kind"] != "historical"]
    if not cases:
        return prep["preview"]
    packet = review(runtime, cases, partial=True)
    audit = _target_query_audit(runtime, cases)
    return {
        **prep["preview"],
        "target_query_audit": audit,
        "partial_review_executed": True,
        "partial_review_status": packet.get("status", "HOLD"),
        "partial_review_reason": packet.get("reason", "REVIEW_FAILED_CLOSED"),
        "historical_coverage": False,
        "full_readiness_status": "HOLD_MISSING_HISTORICAL_PROOF",
        "legacy_exact_parity": packet.get("legacy_exact_parity") is True,
        "case_results": [
            {
                "case": row.get("case"), "kind": row.get("kind"),
                "pass": row.get("pass") is True,
                "admission_reason": row.get("admission_reason")
                    if row.get("admission_reason") in SAFE_ADMISSION_REASONS
                    else "OTHER_OR_UNREPORTED",
                "observed_status": (
                    row.get("observed_status")
                    if row.get("observed_status") in {
                        "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                        "HOLD_NO_CURRENT_MATCH",
                        "HOLD_NO_CONFIDENT_GALAXY_MATCH",
                        "HOLD_NO_MATCH",
                    } else "UNRECOGNIZED_STATUS"
                ),
            }
            for row in packet.get("results", [])
            if isinstance(row, dict)
        ],
        "record_ids_disclosed": False,
        "statements_disclosed": False,
        "queries_disclosed": False,
        "release_activated": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "proof_boundary": (
            "Exactly three current and two adversarial negative cases; the "
            "historical release gate remains HOLD. No record IDs, queries, "
            "statements or secrets leave this redacted result."
        ),
    }

def technical_literal_wiring_probe(runtime: Any) -> dict[str, Any]:
    """Optional, owner-only literal retrieval smoke test, NOT semantic quality.

    The previous fixed prose questions overlap their actual selected records
    by only one concept. Select two distinct existing technical records, form
    short literal anchors from their own statements, then check the original
    admission engine and native HEATDEATH parity. No new records or mutations.
    Never send statements, IDs, tokens, questions or source fields to callers.
    """
    shell: dict[str, Any] = {
        "schema": "gaiaos.bigbang.technical-literal-wiring.v1",
        "status": "HOLD", "reason": "NOT_EVALUATED",
        "literal_wiring_test_only": True,
        "semantic_paraphrase_quality_tested": False,
        "full_readiness_status": "HOLD_HISTORICAL_AND_SEMANTIC_NOT_PROVEN",
        "case_count": 0, "case_results": [],
        "legacy_exact_parity": False,
        "record_ids_disclosed": False, "statements_disclosed": False,
        "queries_disclosed": False, "tokens_disclosed": False,
        "release_activated": False, "writes_performed": [],
        "e_lanes_modified": False,
    }

    def hold(reason: str) -> dict[str, Any]:
        return {**shell, "reason": reason}

    prep = prepare_technical_cases(runtime)
    samples = prep.get("partial_cases") or prep.get("cases") or []
    current = []
    used: set[str] = set()
    for case in samples:
        rid = case.get("record_id")
        if case.get("kind") == "current" and isinstance(rid, str) and rid not in used:
            current.append(case)
            used.add(rid)
        if len(current) == 2:
            break
    if len(current) != 2:
        return hold("TWO_APPROVED_CURRENT_TECHNICAL_RECORDS_REQUIRED")

    try:
        import galaxy_quality
        import galaxy_phase3_exit as phase3

        control = mode.mode_status(runtime)
        if (control.get("schema") != mode.SCHEMA
                or control.get("effective_mode") != mode.HEATDEATH
                or control.get("bigbang_activation_enabled") is not False):
            return hold("HEATDEATH_RELEASE_LOCK_NOT_VERIFIED")

        # The production Phase-3 admission scan reads at most 100 MemoryOS
        # records. Check that the selected records are inside that exact window.
        snapshot = runtime.search_records("", 100, "MemoryOS")
        scoped = snapshot.get("records")
        if not isinstance(scoped, list) or len(scoped) > 100:
            return hold("BOUNDED_SCAN_UNVERIFIED")
        scoped_by_id = {r.get("record_id"): r for r in scoped if isinstance(r, dict)}
        external = getattr(runtime, "GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS", set())

        anchored = []
        for case in current:
            rid = case["record_id"]
            record = runtime.get_record(rid)
            if (rid not in scoped_by_id or not isinstance(record, dict)
                    or not _technical_topics(record) or record.get("status") != "ACTIVE"):
                return hold("TARGET_OUTSIDE_VERIFIED_BOUNDED_SCOPE")

            # Select distinctive existing surface tokens only. A literal smoke
            # result never constitutes paraphrase quality; do not tune thresholds.
            tokens = runtime._galaxy_query_tokens(record["statement"])[:80]
            candidates: dict[str, str] = {}
            for token in tokens:
                if token in external or token == "memory":
                    continue
                concept = galaxy_quality._phase3j_concept(runtime, token)
                if concept not in candidates:
                    candidates[concept] = token
            if len(candidates) < 2:
                return hold("INSUFFICIENT_DISTINCT_LITERAL_CONCEPTS")

            # Prefer concepts that are uncommon elsewhere in this bounded corpus.
            frequencies: dict[str, int] = {c: 0 for c in candidates}
            for row in scoped:
                if row.get("record_id") == rid:
                    continue
                concepts = {
                    galaxy_quality._phase3j_concept(runtime, tok)
                    for tok in runtime._galaxy_query_tokens(
                        str(row.get("statement") or "")
                    )[:80]
                }
                for c in frequencies:
                    if c in concepts:
                        frequencies[c] += 1
            ordered = sorted(candidates, key=lambda c: (frequencies[c], c))
            query = " ".join(candidates[c] for c in ordered[:2])
            evidence = phase3._statement_evidence(
                runtime, record["statement"], query, scope="MemoryOS"
            )
            if (evidence["matched_statement_concept_count"] < phase3.PRIMARY_MIN_CONCEPTS
                    or evidence["statement_concept_coverage"] < phase3.PRIMARY_MIN_COVERAGE):
                return hold("LITERAL_TARGET_ADMISSION_NOT_PROVEN")
            anchored.append((rid, query))

        baseline = gateway.read(runtime, anchored[0][1], "MemoryOS", 4)
        if (baseline.get("status") != "PASS_HEATDEATH"
                or not gateway._validated_legacy(baseline.get("retrieval"), "MemoryOS", 4)):
            return hold("NATIVE_LEGACY_BASELINE_UNVERIFIED")

        galaxy = importlib.import_module("galaxy_frontdoor_context")
        results = []
        for index, (rid, query) in enumerate(anchored):
            packet = galaxy.operational(runtime, query, 4)
            if not _safe_evidence(packet):
                return hold("UNVERIFIED_GALAXY_RESPONSE")
            current_ids = [
                item.get("record", {}).get("record_id")
                for item in packet["records"]
            ]
            results.append({
                "case": index, "kind": "literal_anchor",
                "expected_record_in_current_results": bool(
                    gateway._galaxy_valid(packet, 4) and rid in current_ids
                ),
                "observed_status": packet.get("status")
                    if packet.get("status") in {
                        "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                        "HOLD_NO_CONFIDENT_GALAXY_MATCH",
                        "HOLD_NO_CURRENT_MATCH"
                    } else "OTHER_OR_UNREPORTED",
                "admission_reason": packet.get("reason")
                    if packet.get("reason") in SAFE_ADMISSION_REASONS
                    else "OTHER_OR_UNREPORTED",
            })

        after = gateway.read(runtime, anchored[0][1], "MemoryOS", 4)
        final = mode.mode_status(runtime)
        fields = ("effective_mode", "configured_mode", "control_version")
        parity = (
            after.get("status") == "PASS_HEATDEATH"
            and after.get("retrieval") == baseline["retrieval"]
            and all(control.get(x) == final.get(x) for x in fields)
            and final.get("bigbang_activation_enabled") is False
        )
        passed = all(row["expected_record_in_current_results"] for row in results)
        return {
            **shell,
            "status": "PASS_LITERAL_WIRING_ONLY" if passed and parity else "HOLD",
            "reason": "TWO_LITERAL_ANCHORS_AND_LEGACY_PARITY" if passed and parity
                      else "LITERAL_ANCHOR_MISS_OR_LEGACY_PARITY_FAILURE",
            "case_count": len(results),
            "case_results": results,
            "legacy_exact_parity": parity,
            "proof_boundary": (
                "Literal token anchors selected from existing owner-approved "
                "statements. This is a wiring smoke test only; the original "
                "three paraphrase misses and missing historical supersession "
                "remain unsatisfied quality and release evidence."
            ),
        }
    except Exception:
        return hold("LITERAL_PROBE_FAILED_CLOSED")
