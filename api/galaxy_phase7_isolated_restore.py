"""GALAXY Phase 7F: restore the exact Phase-7E shadow bundle in isolated RAM.

The production runtime is read only. All reconstruction writes target an
unattached sqlite3 :memory: connection, which is closed after this call.
This is evidence reconstruction research, not MemoryOS restoration or pruning.
"""
from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from typing import Any

import galaxy_phase7_tombstone as contract
import galaxy_phase7_tombstone_shadow as shadow

SCHEMA = "gaiaos.galaxy.phase7-isolated-restore.v1"
VERSION = "galaxy.phase7f.isolated-restore.v1"

EVIDENCE_KEYS = (
    "record",
    "lifecycle",
    "governing_state",
    "relations",
    "synthesis_dependencies",
    "lifecycle_events",
    "receipts",
)
LIST_KEYS = frozenset(("relations", "lifecycle_events", "receipts"))
MONITORED_TABLES = shadow.PROTECTED_TABLES + (
    "galaxy_tombstones_shadow",
    "runtime_receipts",
)


def _snapshot(runtime: Any) -> dict[str, int]:
    """Only SELECT from the existing production store."""
    with runtime._db() as conn:
        return {
            table: int(runtime._fetchone_dict(
                conn, f"SELECT COUNT(*) AS n FROM {table}"
            )["n"])
            for table in MONITORED_TABLES
        }


def _create_isolated_store(
    conn: sqlite3.Connection,
    bundle: dict[str, Any],
    *,
    tombstone_id: str,
    receipt_id: str,
    digest: str,
) -> dict[str, int]:
    """Write exactly the bounded evidence bundle into an unattached RAM store."""
    if set(bundle) != set(EVIDENCE_KEYS):
        raise ValueError("Unexpected or missing synthetic evidence categories")

    conn.execute(
        """CREATE TABLE phase7f_manifest (
               tombstone_id TEXT PRIMARY KEY,
               receipt_id TEXT NOT NULL,
               evidence_sha256 TEXT NOT NULL
           )"""
    )
    conn.execute(
        """CREATE TABLE phase7f_evidence (
               evidence_kind TEXT NOT NULL,
               ordinal INTEGER NOT NULL,
               payload_json TEXT NOT NULL,
               PRIMARY KEY (evidence_kind, ordinal)
           )"""
    )
    conn.execute(
        "INSERT INTO phase7f_manifest VALUES (?,?,?)",
        (tombstone_id, receipt_id, digest),
    )

    counts: dict[str, int] = {}
    for kind in EVIDENCE_KEYS:
        value = bundle[kind]
        if kind in LIST_KEYS:
            if not isinstance(value, list):
                raise ValueError(f"Evidence category {kind} is not a list")
            parts = value
        else:
            if not isinstance(value, dict):
                raise ValueError(f"Evidence category {kind} is not an object")
            parts = [value]
        counts[kind] = len(parts)
        for ordinal, part in enumerate(parts):
            conn.execute(
                "INSERT INTO phase7f_evidence VALUES (?,?,?)",
                (kind, ordinal, contract._canonical_json(part)),
            )
    conn.commit()
    return counts


def _reconstruct_isolated(conn: sqlite3.Connection) -> tuple[dict[str, Any], dict[str, int]]:
    rows = conn.execute(
        "SELECT evidence_kind, ordinal, payload_json "
        "FROM phase7f_evidence ORDER BY evidence_kind, ordinal"
    ).fetchall()
    if any(row[0] not in EVIDENCE_KEYS for row in rows):
        raise ValueError("Unexpected evidence category in isolated store")

    grouped: dict[str, list[Any]] = {kind: [] for kind in EVIDENCE_KEYS}
    for kind, ordinal, payload in rows:
        if ordinal != len(grouped[kind]):
            raise ValueError("Noncontiguous isolated evidence ordinal")
        grouped[kind].append(json.loads(payload))

    rebuilt: dict[str, Any] = {}
    counts: dict[str, int] = {}
    for kind in EVIDENCE_KEYS:
        parts = grouped[kind]
        counts[kind] = len(parts)
        if kind in LIST_KEYS:
            rebuilt[kind] = parts
        else:
            if len(parts) != 1 or not isinstance(parts[0], dict):
                raise ValueError(f"Invalid isolated singleton: {kind}")
            rebuilt[kind] = parts[0]
    return rebuilt, counts


def _source_checks(source: dict[str, Any]) -> dict[str, bool]:
    """Revalidate Phase-7E source rather than trusting a status string."""
    expected = shadow._expected_manifest()
    row = source.get("row") or {}
    receipt = source.get("receipt") or {}
    manifest = source.get("manifest") or {}
    validation = contract.validate_manifest(manifest)
    return {
        "phase7e_readback_pass": source.get("status") == "PASS_DURABLE_SHADOW_READBACK",
        "every_shadow_check_pass": all(source.get("checks", {}).values())
            and len(source.get("checks", {})) == 10,
        "exact_tombstone_id": row.get("tombstone_id") == shadow.TOMBSTONE_ID,
        "exact_subject_id": row.get("subject_record_id") == shadow.SUBJECT_RECORD_ID,
        "exact_naomi_authority": row.get("authority") == "NAOMI",
        "exact_shadow_status": row.get("status") == shadow.SHADOW_STATUS,
        "exact_manifest": manifest == expected,
        "manifest_valid": validation.get("valid") is True,
        "row_digest_exact": row.get("evidence_sha256") == expected["evidence_sha256"],
        "stored_manifest_matches_parsed": _valid_json_object(row.get("manifest_json"))
            and json.loads(row["manifest_json"]) == manifest,
        "original_receipt_link": bool(row.get("receipt_id"))
            and row["receipt_id"] == receipt.get("receipt_id"),
        "original_receipt_success": receipt.get("operation")
            == "GALAXY_PHASE7E_SHADOW_TOMBSTONE_WRITE"
            and receipt.get("record_id") == shadow.SUBJECT_RECORD_ID
            and receipt.get("result") == "SUCCESS",
        "no_extra_shadow_write": source.get("eligible_to_create") is False
            and source.get("writes") == 0,
    }


def _valid_json_object(raw: Any) -> bool:
    try:
        return isinstance(json.loads(raw), dict)
    except (TypeError, ValueError):
        return False


def restore_from_readback(source: dict[str, Any]) -> dict[str, Any]:
    """Restore only from independently validated Phase-7E readback, in isolated RAM."""
    checks = _source_checks(source)
    response = {
        "schema": SCHEMA,
        "version": VERSION,
        "execution": "ISOLATED_SQLITE_IN_MEMORY_ONLY",
        "source_tombstone_id": shadow.TOMBSTONE_ID,
        "source_subject_record_id": shadow.SUBJECT_RECORD_ID,
        "source_receipt_id": (source.get("row") or {}).get("receipt_id"),
        "source_evidence_sha256": (source.get("row") or {}).get("evidence_sha256"),
        "source_checks": checks,
        "production_writes_performed": [],
        "production_memoryos_restore": False,
        "memoryos_mutation": False,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "destructive_eligibility": False,
        "tombstone_protocol_implemented": False,
        "destructive_restore_proven": False,
    }
    if not all(checks.values()):
        return {
            **response,
            "status": "HOLD_SHADOW_SOURCE_INVALID",
            "restored": False,
            "isolated_store_created": False,
            "isolated_store_discarded": True,
            "proof_boundary": "Invalid or missing shadow evidence never enters the isolated restore.",
        }

    manifest = source["manifest"]
    original = deepcopy(manifest["evidence_bundle"])
    conn = sqlite3.connect(":memory:")
    try:
        isolated_only = conn.execute("PRAGMA database_list").fetchall() == [(0, "main", "")]
        if not isolated_only:
            return {
                **response,
                "status": "HOLD_ISOLATION_FAILED",
                "restored": False,
                "isolated_store_created": False,
                "isolated_store_discarded": True,
                "proof_boundary": "Restore refused because the SQLite store is not unattached RAM.",
            }
        counts_written = _create_isolated_store(
            conn,
            original,
            tombstone_id=shadow.TOMBSTONE_ID,
            receipt_id=source["row"]["receipt_id"],
            digest=manifest["evidence_sha256"],
        )
        restored, counts_read = _reconstruct_isolated(conn)
        metadata = conn.execute(
            "SELECT tombstone_id, receipt_id, evidence_sha256 FROM phase7f_manifest"
        ).fetchall()
        restored_digest = contract._digest(restored)
        restore_checks = {
            "unattached_in_memory_database": isolated_only,
            "one_exact_isolated_manifest": metadata == [(
                shadow.TOMBSTONE_ID,
                source["row"]["receipt_id"],
                manifest["evidence_sha256"],
            )],
            "all_evidence_categories_recovered": set(restored) == set(EVIDENCE_KEYS),
            "isolated_row_counts_exact": counts_written == counts_read,
            "reconstruction_structurally_exact": restored == original,
            "reconstruction_digest_exact": restored_digest == manifest["evidence_sha256"],
            "source_receipt_preserved": source["receipt"]["receipt_id"]
                == source["row"]["receipt_id"],
            "no_production_restore": True,
            "no_physical_delete": True,
            "no_production_attenuation": True,
        }
        passed = all(restore_checks.values())
        return {
            **response,
            "status": "PASS_ISOLATED_RESTORE" if passed else "HOLD_ISOLATED_RESTORE",
            "restored": passed,
            "isolated_store_created": True,
            "isolated_store_discarded": True,
            "isolated_row_counts": counts_read,
            "isolated_manifest_count": len(metadata),
            "restored_evidence_sha256": restored_digest,
            "restored_evidence_bundle": restored if passed else None,
            "restore_checks": restore_checks,
            "proof_boundary": (
                "One exact synthetic Phase-7E shadow manifest was reconstructed into an "
                "unattached temporary in-memory SQLite store, compared to the saved "
                "evidence and then discarded. This is not restoration into MemoryOS, "
                "physical pruning, destructive restore safety or disaster recovery."
            ),
        }
    finally:
        conn.close()


def review(runtime: Any) -> dict[str, Any]:
    """Read-only runtime wrapper around the isolated in-memory restore."""
    runtime.initialize()
    before = _snapshot(runtime)
    source = shadow.inspect(runtime)
    result = restore_from_readback(source)
    after = _snapshot(runtime)
    counts_unchanged = before == after
    exact_source_postreadback = shadow.inspect(runtime)
    same_source = (
        source.get("status") == exact_source_postreadback.get("status")
        and (source.get("row") or {}).get("receipt_id")
            == (exact_source_postreadback.get("row") or {}).get("receipt_id")
        and (source.get("row") or {}).get("evidence_sha256")
            == (exact_source_postreadback.get("row") or {}).get("evidence_sha256")
    )
    passed = (
        result["status"] == "PASS_ISOLATED_RESTORE"
        and counts_unchanged
        and same_source
    )
    return {
        **result,
        "status": "PASS_ISOLATED_RESTORE" if passed else (
            "HOLD_RUNTIME_READBACK" if not counts_unchanged or not same_source
            else result["status"]
        ),
        "restored": passed,
        "runtime_counts_before": before,
        "runtime_counts_after": after,
        "runtime_counts_unchanged": counts_unchanged,
        "same_shadow_source_after": same_source,
        "production_writes_performed": [],
    }
