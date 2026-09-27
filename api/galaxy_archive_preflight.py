"""Bounded, read-only source/provenance preflight for historical GALAXY imports.

No HTTP route, no production mutation, no E-LANE write authority and no
automatic attribution. The later approved importer must independently prove
source authenticity, owner consent, durable receipts and exact readback.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any

SCHEMA = "gaiaos.galaxy.archive-preflight.v1"
PACKET_SCHEMA = "gaiaos.galaxy.archive-batch.v1"
MAX_BATCH = 50
MAX_PACKET_BYTES = 512_000
MEMBERS = frozenset(("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"))
KINDS = frozenset(("GITHUB", "LIBRARY", "CHAT_EXPORT", "OTHER"))
DATE_CONFIDENCE = frozenset(("EXACT", "DAY_ONLY", "UNKNOWN"))
ATTRIBUTION = frozenset(("EXPLICIT_SOURCE", "ARCHIVE_LABEL", "UNKNOWN"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _text(value: Any, limit: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _valid_date(value: Any, confidence: str) -> bool:
    if confidence == "UNKNOWN":
        return value is None
    if not isinstance(value, str):
        return False
    try:
        if confidence == "DAY_ONLY":
            return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and bool(date.fromisoformat(value))
        if confidence == "EXACT":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None and parsed.utcoffset() is not None
    except (TypeError, ValueError):
        return False
    return False


def _base(status: str, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": status,
        "execution": "READ_ONLY",
        "items": items or [],
        "writes_performed": [],
        "e_lanes_modified": False,
        "gravity_rows_modified": False,
        "mode_control_modified": False,
        "provenance_verified": False,
        "archive_bytes_verified": False,
        "owner_approved_for_import": False,
        "proof_boundary": "Preflight only; archive contents and attribution require independent source verification and owner approval.",
    }


def _inspect(item: Any, archive: dict[str, Any], index: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    public: dict[str, Any] = {"index": index, "status": "HOLD_INVALID_RECORD"}
    if not isinstance(item, dict):
        return public, None
    source_record_id = item.get("source_record_id")
    scope = item.get("scope")
    member = item.get("member")
    statement = item.get("statement")
    record_type = item.get("record_type")
    evidence_ref = item.get("evidence_ref")
    confidence = item.get("date_confidence")
    attribution = item.get("attribution_basis")
    if (not _text(source_record_id, 200) or not _text(statement, 8000)
            or not _text(record_type, 80) or not _text(evidence_ref, 500)
            or not isinstance(confidence, str) or confidence not in DATE_CONFIDENCE
            or not isinstance(attribution, str) or attribution not in ATTRIBUTION):
        return public, None
    if not _valid_date(item.get("original_created_at"), confidence):
        public["status"] = "HOLD_DATE_UNVERIFIED"
        return public, None
    if scope == "MemoryOS":
        if member is not None:
            public["status"] = "HOLD_MEMBER_SCOPE_CONFLICT"
            return public, None
        target = "MemoryOS"
    elif scope == "E_LANE" and isinstance(member, str) and member in MEMBERS:
        target = "E_LANE:" + member
    else:
        public["status"] = "HOLD_SCOPE_OR_MEMBER_INVALID"
        return public, None
    statement_sha = hashlib.sha256(statement.encode("utf-8")).hexdigest()
    if item.get("statement_sha256") is not None and item["statement_sha256"] != statement_sha:
        public["status"] = "HOLD_STATEMENT_HASH_MISMATCH"
        return public, None
    source_key = _digest({
        "system": archive["source_system"],
        "document": archive["document_id"],
        "record": source_record_id,
        "scope": scope,
        "member": member,
    })
    metadata_sha = _digest({
        "record_type": record_type, "evidence_ref": evidence_ref,
        "original_created_at": item.get("original_created_at"),
        "date_confidence": confidence, "attribution_basis": attribution,
    })
    public.update({
        "source_key_sha256": source_key,
        "statement_sha256": statement_sha,
        "metadata_sha256": metadata_sha,
        "proposed_record_id": "MEM-ARCH-" + source_key[:24] if scope == "MemoryOS" else None,
        "target": target,
        "status": "REVIEW_REQUIRED" if scope == "MemoryOS" else "LANE_REVIEW_REQUIRED",
    })
    if scope == "E_LANE" and attribution != "EXPLICIT_SOURCE":
        public["status"] = "HOLD_UNVERIFIED_MEMBER_ATTRIBUTION"
    return public, {
        "source_tag": "galaxy-archive-v1:" + source_key,
        "scope": scope,
        "statement_sha256": statement_sha,
        "metadata_sha256": metadata_sha,
        "source_key_sha256": source_key,
    }


def preflight_archive_batch(packet: Any, *, runtime: Any = None) -> dict[str, Any]:
    """Validate up to 50 archive entries and optionally check MemoryOS collisions.

    Only a read-only SQL SELECT is permitted. E-LANE entries are ALWAYS held for
    separate member-native, source-verified review; this cannot edit their files.
    Output intentionally excludes statements, document names and evidence text.
    """
    if not isinstance(packet, dict) or packet.get("schema") != PACKET_SCHEMA:
        return _base("HOLD_PACKET_SCHEMA")
    try:
        if len(json.dumps(packet, ensure_ascii=False).encode("utf-8")) > MAX_PACKET_BYTES:
            return _base("HOLD_PACKET_OVERSIZE")
    except (TypeError, ValueError, OverflowError):
        return _base("HOLD_PACKET_INVALID")
    archive = packet.get("archive")
    if (not isinstance(archive, dict) or not isinstance(archive.get("source_kind"), str)
            or archive.get("source_kind") not in KINDS
            or not _text(archive.get("source_system"), 120)
            or not _text(archive.get("document_id"), 300)
            or not _text(archive.get("source_locator"), 500)):
        return _base("HOLD_ARCHIVE_PROVENANCE")
    archive_hash = archive.get("source_content_sha256")
    if archive_hash is not None and (
        not isinstance(archive_hash, str) or re.fullmatch(r"[0-9a-f]{64}", archive_hash) is None
    ):
        return _base("HOLD_ARCHIVE_DIGEST_INVALID")
    records = packet.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_BATCH:
        return _base("HOLD_BATCH_SIZE")

    public: list[dict[str, Any]] = []
    internals: list[dict[str, Any] | None] = []
    seen: dict[str, int] = {}
    for index, item in enumerate(records):
        exposed, internal = _inspect(item, archive, index)
        public.append(exposed)
        internals.append(internal)
        if internal is None:
            continue
        key = internal["source_key_sha256"]
        if key in seen:
            prev = seen[key]
            if (internals[prev]["statement_sha256"] == internal["statement_sha256"]
                    and internals[prev]["metadata_sha256"] == internal["metadata_sha256"]):
                exposed["status"] = "DUPLICATE_IN_BATCH"
            else:
                exposed["status"] = "HOLD_SOURCE_ID_CONFLICT"
                public[prev]["status"] = "HOLD_SOURCE_ID_CONFLICT"
        else:
            seen[key] = index

    if runtime is not None:
        if getattr(runtime, "_INITIALIZED", False) is not True:
            return _base("HOLD_RUNTIME_NOT_INITIALIZED")
        lookup = [(i, internal) for i, internal in enumerate(internals)
                  if internal is not None and public[i]["status"] == "REVIEW_REQUIRED"]
        if lookup:
            tags = [internal["source_tag"] for _, internal in lookup]
            proposed_ids = [public[i]["proposed_record_id"] for i, _ in lookup]
            placeholders = ",".join("?" for _ in tags)
            id_placeholders = ",".join("?" for _ in proposed_ids)
            try:
                with runtime._db() as conn:
                    cursor = conn.execute(
                        "SELECT record_id, scope, source, statement, notes "
                        f"FROM memory_records WHERE source IN ({placeholders}) "
                        f"OR record_id IN ({id_placeholders})",
                        tuple(tags + proposed_ids),
                    )
                    names = [col[0] if isinstance(col, (tuple, list)) else col.name
                             for col in cursor.description]
                    matches = [dict(row) if hasattr(row, "keys")
                               else dict(zip(names, row)) for row in cursor.fetchall()]
            except Exception as exc:
                result = _base("HOLD_STORAGE_UNAVAILABLE")
                result["error_type"] = type(exc).__name__
                return result
            by_source: dict[str, list[dict[str, Any]]] = {}
            by_id: dict[str, dict[str, Any]] = {}
            for match in matches:
                by_source.setdefault(match["source"], []).append(match)
                by_id[match["record_id"]] = match
            for index, internal in lookup:
                matching = by_source.get(internal["source_tag"], [])
                proposed = public[index]["proposed_record_id"]
                occupied = by_id.get(proposed)
                if occupied is not None and occupied["source"] != internal["source_tag"]:
                    public[index]["status"] = "HOLD_RECORD_ID_COLLISION"
                    continue
                if not matching:
                    continue
                if len(matching) != 1:
                    public[index]["status"] = "HOLD_DUPLICATE_STORED_SOURCE"
                    continue
                row = matching[0]
                try:
                    provenance = json.loads(row.get("notes") or "{}").get("galaxy_archive") or {}
                except (ValueError, TypeError, AttributeError):
                    provenance = {}
                if (row["scope"] == "MemoryOS"
                        and isinstance(row.get("statement"), str)
                        and hashlib.sha256(row["statement"].encode("utf-8")).hexdigest()
                        == internal["statement_sha256"]
                        and provenance.get("source_key_sha256") == internal["source_key_sha256"]
                        and provenance.get("metadata_sha256") == internal["metadata_sha256"]):
                    public[index]["status"] = "ALREADY_PRESENT_VERIFIED_METADATA"
                    public[index]["existing_record_id"] = row["record_id"]
                else:
                    public[index]["status"] = "HOLD_EXISTING_SOURCE_CONFLICT"

    statuses = [item["status"] for item in public]
    if any(s.startswith("HOLD_") for s in statuses):
        state = "PARTIAL_HOLD"
    elif any(s in ("REVIEW_REQUIRED", "LANE_REVIEW_REQUIRED") for s in statuses):
        state = "PASS_PREFLIGHT_REVIEW_REQUIRED"
    else:
        state = "PASS_NO_NEW_CANDIDATES"
    result = _base(state, public)
    result["counts"] = {s: statuses.count(s) for s in sorted(set(statuses))}
    result["batch_count"] = len(records)
    result["store_comparison"] = "READ_ONLY" if runtime is not None else "NOT_PERFORMED"
    return result
