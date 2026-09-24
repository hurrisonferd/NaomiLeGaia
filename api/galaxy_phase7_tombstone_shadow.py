"""GALAXY Phase 7E durable shadow tombstone persistence.

This slice may write exactly one synthetic tombstone manifest into the dedicated
shadow table plus one runtime receipt. It never deletes or mutates MemoryOS source
records, lifecycle history, relations, synthesis provenance, gravity, or importance.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import galaxy_phase7_tombstone as contract

VERSION = "galaxy.phase7.shadow-tombstone-persistence.v1"
SCHEMA = "gaiaos.galaxy.phase7-shadow-tombstone.v1"

TOMBSTONE_ID = "TOMB-P7E-SYNTHETIC-HISTORICAL-V1"
SUBJECT_RECORD_ID = "SYNTHETIC-P7D-HISTORICAL"
CONFIRMATION = "WRITE_GALAXY_PHASE7E_SYNTHETIC_SHADOW_TOMBSTONE"
SHADOW_STATUS = "DURABLE_SHADOW_RESEARCH_ONLY"

PROTECTED_TABLES = (
    "memory_records",
    "memory_relations",
    "memory_gravity",
    "memory_importance",
    "memory_lifecycle",
    "memory_lifecycle_events",
    "memory_syntheses",
)


def _protected_counts(runtime: Any) -> dict[str, int]:
    runtime.initialize()
    with runtime._db() as conn:
        return {
            table: int(runtime._fetchone_dict(
                conn, f"SELECT COUNT(*) AS n FROM {table}"
            )["n"])
            for table in PROTECTED_TABLES
        }


def _expected_manifest() -> dict[str, Any]:
    result = contract.synthetic_tombstone_contract_canary()
    if result.get("status") != "PASS_SYNTHETIC_TOMBSTONE_CONTRACT_CANARY":
        raise ValueError("Phase-7D synthetic tombstone contract is not passing")
    manifest = result.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError("Phase-7D manifest missing")
    return manifest


def inspect(runtime: Any) -> dict[str, Any]:
    """Read-only inspection of the one allowed Phase-7E shadow tombstone."""
    runtime.initialize()
    expected = _expected_manifest()
    with runtime._db() as conn:
        row = runtime._fetchone_dict(
            conn,
            "SELECT * FROM galaxy_tombstones_shadow WHERE tombstone_id=?",
            (TOMBSTONE_ID,),
        )
        receipt = None
        if row and row.get("receipt_id"):
            receipt = runtime._fetchone_dict(
                conn,
                "SELECT * FROM runtime_receipts WHERE receipt_id=?",
                (row["receipt_id"],),
            )

    if row is None:
        return {
            "schema": SCHEMA,
            "version": VERSION,
            "execution": "READ_ONLY",
            "status": "PASS_READY_FOR_EXPLICIT_SHADOW_WRITE",
            "tombstone_id": TOMBSTONE_ID,
            "subject_record_id": SUBJECT_RECORD_ID,
            "shadow_row_present": False,
            "eligible_to_create": True,
            "confirmation_required": CONFIRMATION,
            "writes": 0,
            "memoryos_mutation": False,
            "physical_delete": False,
            "production_retrieval_changed": False,
            "destructive_eligibility": False,
        }

    try:
        stored_manifest = json.loads(row.get("manifest_json") or "{}")
    except json.JSONDecodeError:
        stored_manifest = {}
    validation = contract.validate_manifest(stored_manifest)
    checks = {
        "exact_tombstone_id": row.get("tombstone_id") == TOMBSTONE_ID,
        "exact_subject_id": row.get("subject_record_id") == SUBJECT_RECORD_ID,
        "shadow_status": row.get("status") == SHADOW_STATUS,
        "authority_naomi": row.get("authority") == "NAOMI",
        "manifest_valid": validation.get("valid") is True,
        "manifest_exact": stored_manifest == expected,
        "evidence_sha256_exact": row.get("evidence_sha256") == expected.get("evidence_sha256"),
        "receipt_present": bool(receipt),
        "receipt_operation_exact": (receipt or {}).get("operation") == "GALAXY_PHASE7E_SHADOW_TOMBSTONE_WRITE",
        "receipt_success": (receipt or {}).get("result") == "SUCCESS",
    }
    passed = all(checks.values())
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "execution": "READ_ONLY",
        "status": "PASS_DURABLE_SHADOW_READBACK" if passed else "HOLD_SHADOW_READBACK",
        "tombstone_id": TOMBSTONE_ID,
        "subject_record_id": SUBJECT_RECORD_ID,
        "shadow_row_present": True,
        "eligible_to_create": False,
        "row": row,
        "manifest": stored_manifest,
        "manifest_validation": validation,
        "receipt": receipt,
        "checks": checks,
        "writes": 0,
        "memoryos_mutation": False,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "destructive_eligibility": False,
        "proof_boundary": (
            "A PASS proves only that one exact synthetic research manifest is durably "
            "readable from the isolated shadow table in this runtime. It does not prove "
            "restart persistence until a separately observed post-restart readback."
        ),
    }


def execute(
    runtime: Any,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
) -> dict[str, Any]:
    """Write exactly one synthetic shadow tombstone after explicit Naomi action."""
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Explicit Naomi approval required for Phase-7E shadow write")
    if confirmation != CONFIRMATION:
        raise PermissionError("Exact Phase-7E shadow-tombstone confirmation required")

    before = inspect(runtime)
    if before.get("status") != "PASS_READY_FOR_EXPLICIT_SHADOW_WRITE":
        raise ValueError("Phase-7E shadow tombstone is not eligible for creation")

    manifest = _expected_manifest()
    manifest_json = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    before_counts = _protected_counts(runtime)
    created_at = runtime._now()
    receipt_id = "MEMREC-" + uuid.uuid4().hex
    receipt = {
        "receipt_id": receipt_id,
        "operation": "GALAXY_PHASE7E_SHADOW_TOMBSTONE_WRITE",
        "record_id": SUBJECT_RECORD_ID,
        "timestamp": created_at,
        "result": "SUCCESS",
        "tombstone_id": TOMBSTONE_ID,
        "evidence_sha256": manifest["evidence_sha256"],
        "shadow_only": True,
        "memoryos_mutation": False,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "runtime": runtime.SCHEMA_VERSION,
    }

    with runtime._db() as conn:
        existing = runtime._fetchone_dict(
            conn,
            "SELECT tombstone_id FROM galaxy_tombstones_shadow WHERE tombstone_id=?",
            (TOMBSTONE_ID,),
        )
        if existing:
            raise ValueError("Concurrent or duplicate Phase-7E shadow tombstone; no write")
        conn.execute(
            """INSERT INTO galaxy_tombstones_shadow
               (tombstone_id,subject_record_id,manifest_json,evidence_sha256,status,
                created_at,authority,receipt_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                TOMBSTONE_ID,
                SUBJECT_RECORD_ID,
                manifest_json,
                manifest["evidence_sha256"],
                SHADOW_STATUS,
                created_at,
                "NAOMI",
                receipt_id,
            ),
        )
        conn.execute(
            """INSERT INTO runtime_receipts
               (receipt_id,operation,record_id,timestamp,result,detail)
               VALUES (?,?,?,?,?,?)""",
            (
                receipt_id,
                receipt["operation"],
                SUBJECT_RECORD_ID,
                created_at,
                "SUCCESS",
                json.dumps(receipt, ensure_ascii=False, sort_keys=True),
            ),
        )

    after = inspect(runtime)
    after_counts = _protected_counts(runtime)
    checks = {
        "shadow_readback_pass": after.get("status") == "PASS_DURABLE_SHADOW_READBACK",
        "protected_table_counts_unchanged": before_counts == after_counts,
        "manifest_digest_readback": (after.get("row") or {}).get("evidence_sha256") == manifest["evidence_sha256"],
        "receipt_readback": (after.get("receipt") or {}).get("receipt_id") == receipt_id,
        "memoryos_mutation_false": True,
        "physical_delete_false": True,
        "production_retrieval_changed_false": True,
    }
    return {
        "schema": "gaiaos.galaxy.phase7-shadow-tombstone-receipt.v1",
        "version": VERSION,
        "execution": "OBSERVED_RUNTIME_FOR_THIS_CALL",
        "status": "PASS_READBACK" if all(checks.values()) else "HOLD_READBACK",
        "tombstone_id": TOMBSTONE_ID,
        "subject_record_id": SUBJECT_RECORD_ID,
        "checks": checks,
        "protected_counts_before": before_counts,
        "protected_counts_after": after_counts,
        "receipt": receipt,
        "readback": after,
        "writes_performed": [
            "galaxy_tombstones_shadow:INSERT_EXACT_SYNTHETIC_FIXTURE",
            "runtime_receipts:INSERT_PHASE7E_RECEIPT",
        ],
        "memoryos_mutation": False,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "destructive_eligibility": False,
        "tombstone_protocol_implemented": False,
        "destructive_restore_proven": False,
        "proof_boundary": (
            "This receipt may prove one exact shadow manifest write and immediate readback. "
            "It does not prove restart persistence, MemoryOS restoration, deletion safety, "
            "production attenuation, or destructive authorization."
        ),
    }
