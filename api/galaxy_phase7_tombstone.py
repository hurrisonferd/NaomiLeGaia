"""GALAXY Phase 7D synthetic tombstone/restore contract research.

This module proves an in-memory evidence-preservation contract only.
It never reads or writes the production database and grants no destructive authority.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

VERSION = "galaxy.phase7.tombstone-contract-research.v1"
SCHEMA = "gaiaos.galaxy.phase7-tombstone-contract.v1"

TOMBSTONE_PROTOCOL_IMPLEMENTED = False
DESTRUCTIVE_RESTORE_PROVEN = False
PHYSICAL_PRUNING_ENABLED = False
PRODUCTION_ATTENUATION_ENABLED = False

REQUIRED_MANIFEST_FIELDS = (
    "schema",
    "version",
    "record_id",
    "evidence_bundle",
    "evidence_sha256",
    "restore_recipe",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def build_manifest(evidence_bundle: dict[str, Any]) -> dict[str, Any]:
    """Build a synthetic tombstone manifest without external storage or mutation."""
    bundle = deepcopy(evidence_bundle)
    record = bundle.get("record") or {}
    record_id = str(record.get("record_id") or "").strip()
    if not record_id:
        raise ValueError("record.record_id required")

    return {
        "schema": SCHEMA,
        "version": VERSION,
        "record_id": record_id,
        "evidence_bundle": bundle,
        "evidence_sha256": _digest(bundle),
        "restore_recipe": "RESTORE_EXACT_EVIDENCE_BUNDLE_IN_MEMORY_ONLY",
        "synthetic_contract_only": True,
        "durable_tombstone_written": False,
        "production_database_access": False,
        "destructive_authority": False,
    }


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate manifest completeness and evidence integrity, fail closed."""
    missing = [
        field for field in REQUIRED_MANIFEST_FIELDS
        if field not in manifest
    ]
    bundle = manifest.get("evidence_bundle")
    expected = str(manifest.get("evidence_sha256") or "")
    actual = _digest(bundle) if isinstance(bundle, dict) else ""
    record_id = ""
    if isinstance(bundle, dict):
        record_id = str((bundle.get("record") or {}).get("record_id") or "")

    checks = {
        "required_fields_present": not missing,
        "schema_matches": manifest.get("schema") == SCHEMA,
        "version_matches": manifest.get("version") == VERSION,
        "record_id_matches_bundle": bool(record_id) and manifest.get("record_id") == record_id,
        "evidence_hash_matches": bool(expected) and expected == actual,
        "synthetic_contract_only": manifest.get("synthetic_contract_only") is True,
        "durable_tombstone_written_false": manifest.get("durable_tombstone_written") is False,
        "production_database_access_false": manifest.get("production_database_access") is False,
        "destructive_authority_false": manifest.get("destructive_authority") is False,
    }
    valid = all(checks.values())

    return {
        "valid": valid,
        "status": "PASS_MANIFEST_VALID" if valid else "HOLD_MANIFEST_INVALID",
        "missing_fields": missing,
        "checks": checks,
        "expected_sha256": expected,
        "actual_sha256": actual,
    }


def restore_in_memory(manifest: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the evidence bundle only after the manifest validates."""
    validation = validate_manifest(manifest)
    if not validation["valid"]:
        return {
            "status": "HOLD_RESTORE_REFUSED",
            "restored": False,
            "validation": validation,
            "restored_bundle": None,
        }
    return {
        "status": "PASS_IN_MEMORY_RESTORE",
        "restored": True,
        "validation": validation,
        "restored_bundle": deepcopy(manifest["evidence_bundle"]),
    }


def synthetic_tombstone_contract_canary() -> dict[str, Any]:
    """Prove manifest completeness and exact in-memory round trip on synthetic evidence."""
    original = {
        "record": {
            "record_id": "SYNTHETIC-P7D-HISTORICAL",
            "authority": "NAOMI",
            "record_type": "SYNTHETIC_CANARY",
            "scope": "MemoryOS",
            "statement": "Synthetic Phase-7D evidence bundle.",
            "status": "ACTIVE",
            "version": "1",
        },
        "lifecycle": {
            "state": "COMPRESSED",
            "reason": "Synthetic tombstone contract research only",
        },
        "governing_state": {
            "state": "HISTORICAL_SUPERSEDED",
            "current_default_eligible": False,
            "historical_retrieval_eligible": True,
        },
        "relations": [{
            "edge_id": "SYNTHETIC-EDGE-P7D",
            "source_record_id": "SYNTHETIC-P7D-CURRENT",
            "target_record_id": "SYNTHETIC-P7D-HISTORICAL",
            "relation_type": "SUPERSEDES",
            "status": "VERIFIED",
            "authority": "NAOMI",
        }],
        "synthesis_dependencies": {
            "source_for_synthesis_record_ids": [],
            "is_synthesis_record": False,
        },
        "lifecycle_events": [{
            "event_id": "SYNTHETIC-LIFE-P7D",
            "from_state": "ARCHIVED",
            "to_state": "COMPRESSED",
            "authority": "NAOMI",
        }],
        "receipts": [{
            "receipt_id": "SYNTHETIC-RECEIPT-P7D",
            "record_id": "SYNTHETIC-P7D-HISTORICAL",
        }],
    }

    manifest = build_manifest(original)
    validation = validate_manifest(manifest)
    restoration = restore_in_memory(manifest)
    restored = restoration.get("restored_bundle")

    checks = {
        "synthetic_only": True,
        "production_database_access_false": manifest["production_database_access"] is False,
        "durable_tombstone_written_false": manifest["durable_tombstone_written"] is False,
        "manifest_valid": validation["valid"],
        "restore_completed_in_memory": restoration["restored"] is True,
        "round_trip_exact": restored == original,
        "round_trip_hash_exact": _digest(restored) == manifest["evidence_sha256"],
        "tombstone_protocol_implemented_false": TOMBSTONE_PROTOCOL_IMPLEMENTED is False,
        "destructive_restore_proven_false": DESTRUCTIVE_RESTORE_PROVEN is False,
        "physical_pruning_false": PHYSICAL_PRUNING_ENABLED is False,
        "production_attenuation_false": PRODUCTION_ATTENUATION_ENABLED is False,
    }
    passed = all(checks.values())

    return {
        "schema": SCHEMA,
        "version": VERSION,
        "execution": "SYNTHETIC_IN_MEMORY_ONLY",
        "status": "PASS_SYNTHETIC_TOMBSTONE_CONTRACT_CANARY" if passed else "HOLD",
        "manifest": manifest,
        "validation": validation,
        "restoration": restoration,
        "checks": checks,
        "writes_performed": [],
        "physical_delete": False,
        "production_retrieval_changed": False,
        "destructive_eligibility": False,
        "destructive_gates": {
            "tombstone_protocol_implemented": TOMBSTONE_PROTOCOL_IMPLEMENTED,
            "destructive_restore_proven": DESTRUCTIVE_RESTORE_PROVEN,
            "physical_pruning_enabled": PHYSICAL_PRUNING_ENABLED,
            "production_attenuation_enabled": PRODUCTION_ATTENUATION_ENABLED,
        },
        "proof_boundary": (
            "Phase 7D proves only that a synthetic evidence bundle can be represented by "
            "a complete integrity-checked manifest and reconstructed exactly in memory. "
            "No durable tombstone exists and no destructive restore or deletion is proven."
        ),
    }
