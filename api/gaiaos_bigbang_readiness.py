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
                    packet.get("status") == "HOLD_NO_CONFIDENT_GALAXY_MATCH"
                    and packet.get("reason") == "NO_PRIMARY_CANDIDATE"
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
        "historical_cases_prepared": 0,
        "negative_cases_prepared": 2,
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
                "FROM memory_records WHERE scope='MemoryOS' "
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
        if len(chosen) < 2:
            return hold("TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN")
        cases = [
            {"kind": "current", "query": TECHNICAL_QUERIES[topic][0],
             "record_id": record["record_id"]}
            for topic, record in chosen
        ]
        cases.append({
            "kind": "current", "query": TECHNICAL_QUERIES[chosen[0][0]][1],
            "record_id": chosen[0][1]["record_id"],
        })
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
            return hold("NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES")
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
                "observed_status": row.get("observed_status"),
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
