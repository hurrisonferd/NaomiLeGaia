"""Stage 9AF: adversarial, source-backed LOCAL fixture for import-to-chat tests.

This is deliberately a TEST ADAPTER, not MemconOS, a Turso adapter, a release
gate, or a source of trusted chat evidence. Build it ONLY from an actual signed
Stage 9Y fixture after full row/ledger and canary verification. It reads the
same disposable disk file each time to detect rollback and later row mutation,
and can lie about the governing state/graph on purpose to test Stage 9AE.

No remote credentials, network, real personal memory, HTTP route, production
write, lifecycle mutation, or E-LANE interface exists in this module.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import galaxy_stage9y_canonical_staging as y
import galaxy_stage9z_local_rollback as z

SCHEMA = "gaiaos.galaxy.stage9af.local-import-to-chat-fixture.v1"
SAFE_ID = "MEM-STAGE9AF-SYNTHETIC-CURRENT"
EDGE_ID = "EDGE-STAGE9AF-FORGED-VERIFIED"
SAFE_ROW = {
    "record_id": SAFE_ID,
    "authority": "SYNTHETIC_TEST_ONLY", "record_type": "TEST",
    "scope": "MemoryOS", "statement": "synthetic current calibration memory",
    "source": "stage9af:synthetic:never-stored",
    "status": "ACTIVE", "version": "1",
    "created_at": "2026-09-27", "updated_at": "2026-09-27",
    "supersedes": None, "notes": "{}",
}


class SignedLocalArchiveRuntime:
    """Fake legacy/GALAXY runtime that reads REAL Stage 9Y fixture rows.

    External callers receive only a bounded signed-record subset. Fabricated
    CURRENT governing state and VERIFIED graph edge are explicitly malicious
    test conditions, never statements about any real source or real user.
    """

    _INITIALIZED = True

    def __init__(self, conn: sqlite3.Connection, ids: tuple[str, ...],
                 *, include_synthetic_current: bool = False):
        self._conn = conn
        self._ids = ids
        self._synthetic_current = include_synthetic_current
        self.reads: list[str] = []

    def _stored(self, rid: str) -> dict[str, Any] | None:
        if rid not in self._ids:
            return None
        return y._stored_record(self._conn, rid)

    def search_records(self, query: str = "", limit: int = 10,
                       scope: str | None = None) -> dict[str, Any]:
        self.reads.append("LEGACY_READ_LOCAL_FIXTURE")
        words = query.lower().split()
        selected = []
        candidates = ([SAFE_ROW] if self._synthetic_current else [])
        candidates += [
            row for rid in self._ids if (row := self._stored(rid)) is not None
        ]
        for row in candidates:
            if (scope is None or row["scope"] == scope) and all(
                word in row["statement"].lower() for word in words
            ):
                selected.append(dict(row))
        selected = selected[:max(1, min(int(limit), 100))]
        return {
            "records": selected, "count": len(selected),
            "runtime": "STAGE9AF_SIGNED_LOCAL_FIXTURE_ONLY",
            "query_terms_applied": words, "scope_applied": scope,
            "query_filter_active": bool(words),
        }

    def galaxy_record(self, rid: str) -> dict[str, Any] | None:
        self.reads.append("GALAXY_READ_LOCAL_FIXTURE")
        row = dict(SAFE_ROW) if self._synthetic_current and rid == SAFE_ID \
            else self._stored(rid)
        if row is None:
            return None
        relations = (
            [{
                "edge_id": EDGE_ID, "source_record_id": rid,
                "target_record_id": SAFE_ID, "status": "VERIFIED",
            }] if rid in self._ids and self._synthetic_current else []
        )
        return {
            "record": row,
            "gravity": {"gravity_score": .99, "score_version": "SYNTHETIC-UNTRUSTED"},
            "lifecycle": {"state": "ACTIVE"},
            "importance": {"gate_units": 7000},
            "relations": relations,
        }

    def galaxy_governing_state(self, rid: str) -> dict[str, Any]:
        self.reads.append("FORGED_GOVERNING_STATE_TEST_ONLY")
        return {
            "record_id": rid, "state": "CURRENT",
            "current_default_eligible": True,
        }

    def _db(self):
        raise AssertionError("Stage 9AF must not expose a persistent control/write DB")

    def write_record(self, *args: Any, **kwargs: Any) -> None:
        raise AssertionError("Stage 9AF read fixture must never write")

    def galaxy_calculate_gravity(self, *args: Any, **kwargs: Any) -> None:
        raise AssertionError("Stage 9AF must never write or calculate gravity")

    def proof(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "PASS_SIGNED_LOCAL_FIXTURE_ONLY",
            "original_signed_ledger_verified_at_creation": True,
            "held_signed_record_count": len(self._ids),
            "model_and_provider_verified": False,
            "live_owner_authorization_proven": False,
            "live_turso_connected": False,
            "real_sovmem_main_connected": False,
            "original_gaiaos_production_connected": False,
            "bigbang_activated": False,
            "e_lanes_modified": False,
            "fixture_runtime_deliberately_forges_governing_state": True,
        }


def open_signed_local_archive_runtime(
    *, fixture_connection: sqlite3.Connection,
    fixture_root: str | Path, config: dict[str, str],
    original_manifest: dict[str, Any], original_signature: str,
    original_key: bytes, original_receipt: dict[str, Any],
    confirm_synthetic_local_only: bool,
    include_synthetic_current: bool = False,
) -> SignedLocalArchiveRuntime | None:
    """Verify signed same-database Stage9Y evidence BEFORE exposing test rows.

    Refuse rolled-back receipts, altered/imported ACTIVE rows, unknown schema,
    changed marker/canary, attached/non-native/outside-repo file targets and
    invalid independent HMAC. No lazy reparsing of untrusted unsigned records.
    """
    if confirm_synthetic_local_only is not True:
        return None
    if (not isinstance(include_synthetic_current, bool)
            or not isinstance(original_manifest, dict)
            or not isinstance(original_receipt, dict)
            or not isinstance(original_key, bytes) or len(original_key) < 32):
        return None
    conn = fixture_connection
    if y._fixture_path(conn, fixture_root) is None:
        return None
    if not z._protected_schema(conn):
        return None
    try:
        if not y._schema_and_identity(
            conn, original_manifest["expected_staging_id"],
            original_manifest["canary_run_id"],
            original_manifest["canary_sha256"],
        ):
            return None
        batch = y._row(conn.execute(
            f"SELECT {','.join(y.BATCH_COLS)} FROM galaxy_stage9y_batches "
            "WHERE approval_id=?", (original_manifest["approval_id"],),
        ))
        if batch is None or batch["status"] != y.STATUS:
            return None
        if not z._original_signed(
            original_manifest, original_signature, original_key, config,
            batch, original_receipt,
        ):
            return None
        if not y._check_receipt(
            conn, original_receipt, z._items(original_receipt),
        ):
            return None
        ids = tuple(item["record_id"] for item in original_receipt["items"])
        if not 1 <= len(ids) <= y.BATCH_CAP or len(ids) != len(set(ids)):
            return None
        for rid in ids:
            row = y._stored_record(conn, rid)
            if (row is None or row["scope"] != "MemoryOS"
                    or row["status"] != y.STATUS
                    or not row["source"].startswith("galaxy-archive-v1:")):
                return None
    except (KeyError, TypeError, ValueError, OverflowError, sqlite3.Error):
        return None
    return SignedLocalArchiveRuntime(
        conn, ids, include_synthetic_current=include_synthetic_current,
    )
