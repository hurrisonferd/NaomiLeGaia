"""GALAXY Stage 9AA: staging-only, SELECT-only pre-import schema readiness.

This module does not create a database, schema, canary or historical record.
It can read an independently supplied staging Turso endpoint with a separate
read-only token AFTER owner provisioning and prior Stage 9X canary proof.
Injected/local connections never establish real staging evidence.
No production connection or token, HTTP route, mode change or member E-LANE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Callable

import galaxy_stage9v_staging_turso as v
import galaxy_stage9v_operator_preflight as vread
import galaxy_stage9x_owner_canary as x
import galaxy_stage9y_canonical_staging as y
import galaxy_stage9z_local_rollback as z

SCHEMA = "gaiaos.galaxy.stage9aa.preimport-readonly.v1"
PIN_SCHEMA = "gaiaos.galaxy.stage9aa.independent-canary-pin.v1"
TARGET = "SEPARATE_STAGING_TURSO_PREIMPORT_READ_ONLY"
PIN_KEYS = frozenset((
    "schema", "run_id", "canary_sha256", "staging_uuid_sha256",
    "staging_url_sha256", "production_url_sha256",
))
EXPECTED_TABLES = {
    "galaxy_stage9v_staging_identity": (
        "schema", "environment", "database_id", "authority", "status",
    ),
    "galaxy_stage9v_canaries": vread.EXPECTED_COLUMNS,
    "memory_records": y.RECORD_COLS,
    "galaxy_stage9y_batches": y.BATCH_COLS,
    "galaxy_stage9y_items": y.ITEM_COLS,
    "galaxy_stage9z_rollbacks": z.LEDGER_COLS,
}
EMPTY_TABLES = (
    "memory_records", "galaxy_stage9y_batches",
    "galaxy_stage9y_items", "galaxy_stage9z_rollbacks",
)
MAX_PIN_BYTES = 4096


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _report(status: str, *, queries: int = 0, stage9v_status: str = "NOT_RUN",
            test_connector_injected: bool | None = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "read_only_select_count": queries,
        "stage9v_preflight_status": stage9v_status,
        "schema_layout_verified": False,
        "pinned_same_database_canary_verified": False,
        "preimport_tables_empty_verified": False,
        "staging_turso_remotely_observed": False,
        "test_connector_injected": test_connector_injected,
        "production_database_accessed": False,
        "production_data_modified": False,
        "staging_writes_performed": [],
        "e_lanes_modified": False,
        "gravity_modified": False, "mode_control_modified": False,
        "bigbang_activated": False,
        "provider_database_separation_independently_verified": False,
        "staging_token_readonly_permission_independently_verified": False,
        "live_owner_authentication_verified": False,
        "proof_boundary": (
            "Read-only columns, marker, pinned canary and empty staging "
            "tables only. Does NOT attest provider aliases, credential "
            "permissions, full DDL/constraints, owner authentication, "
            "historical import, restart or release."
        ),
    }


def _canonical_pin(config: Any, pin: Any) -> bool:
    """Reject re-derived, self-attested, switched-host or altered pins."""
    if not isinstance(config, dict) or not isinstance(pin, dict):
        return False
    if set(pin) != PIN_KEYS or pin.get("schema") != PIN_SCHEMA:
        return False
    stage = v._canonical_url(config.get("staging_url"))
    prod = v._canonical_url(config.get("production_url"))
    uuid = config.get("expected_staging_id")
    run = pin.get("run_id")
    canary_sha = pin.get("canary_sha256")
    if (stage is None or prod is None or stage == prod
            or not v._valid_id(uuid)
            or not isinstance(config.get("staging_token"), str)
            or not 16 <= len(config["staging_token"]) <= 8192
            or not isinstance(run, str) or v._RUN.fullmatch(run) is None
            or not isinstance(canary_sha, str)
            or v._HEX.fullmatch(canary_sha) is None):
        return False
    expected = {
        "schema": PIN_SCHEMA, "run_id": run, "canary_sha256": canary_sha,
        "staging_uuid_sha256": _sha(uuid.encode()),
        "staging_url_sha256": _sha(stage.encode()),
        "production_url_sha256": _sha(prod.encode()),
    }
    return pin == expected


def _columns(cursor: Any) -> tuple[str, ...]:
    return tuple(
        col[0] if isinstance(col, (tuple, list))
        else getattr(col, "name", str(col))
        for col in cursor.description
    )


def check_preimport_staging(
    *, config: dict[str, str], pin: dict[str, Any],
    confirm_independent_canary_pin: bool,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """SELECTs ONLY against the separately supplied staging endpoint.

    Source tests inject a local connector and MUST NOT report remote proof.
    A production URL is fingerprinted but never connected; no production
    credential is accepted. A pin derived from this database is NOT
    independently trusted: that provenance remains an external owner check.
    """
    local = connector is not None
    if confirm_independent_canary_pin is not True:
        return _report("HOLD_INDEPENDENT_PIN_CONFIRMATION_REQUIRED",
                       test_connector_injected=local)
    if not _canonical_pin(config, pin):
        return _report("HOLD_CANARY_PIN_OR_ENDPOINT_INVALID",
                       test_connector_injected=local)
    first = vread.check_staging_readiness(
        **config, connector=connector,
    )
    if first.get("status") != "PASS_STAGING_READINESS_READ_ONLY":
        return _report(
            "HOLD_STAGING_IDENTITY_PREFLIGHT",
            queries=first.get("reads_performed", 0),
            stage9v_status=str(first.get("status", "HOLD_UNKNOWN")),
            test_connector_injected=local,
        )
    queries = first["reads_performed"]
    connect = connector if connector is not None else v._connect_live
    conn = None
    status = "HOLD_STAGING_SCHEMA_UNVERIFIED"
    schema_ok = False
    canary_ok = False
    empty_ok = False
    try:
        conn = connect(config["staging_url"], config["staging_token"])
        queries += 1
        if not v._identity(conn, config["expected_staging_id"]):
            status = "HOLD_STAGING_IDENTITY_CHANGED"
        else:
            queries += 1
            objects = conn.execute(
                "SELECT type,name FROM sqlite_master "
                "WHERE type IN ('table','view','trigger')"
            ).fetchall()
            user_tables = set()
            unknown = False
            for kind, name in objects:
                if not isinstance(name, str) or not isinstance(kind, str):
                    unknown = True
                    break
                if name.startswith("sqlite_"):
                    continue
                if kind != "table" or name not in EXPECTED_TABLES:
                    unknown = True
                    break
                user_tables.add(name)
            if unknown or user_tables != set(EXPECTED_TABLES):
                status = "HOLD_UNEXPECTED_OR_MISSING_STAGING_OBJECTS"
            else:
                schema_ok = True
                for table, columns in EXPECTED_TABLES.items():
                    # Each table identifier is a fixed source-code constant.
                    # LIMIT 0 cannot retrieve private historical statements.
                    queries += 1
                    actual = _columns(conn.execute(
                        f"SELECT * FROM {table} LIMIT 0"
                    ))
                    if actual != columns:
                        schema_ok = False
                        break
                if not schema_ok:
                    status = "HOLD_CANONICAL_COLUMN_LAYOUT_MISMATCH"
                else:
                    queries += 1
                    row = v._canary(conn, pin["run_id"])
                    canary_ok = (
                        row is not None
                        and row.get("database_id") == config["expected_staging_id"]
                        and _sha(v._bytes(row)) == pin["canary_sha256"]
                    )
                    if not canary_ok:
                        status = "HOLD_PREVIOUS_CANARY_MISSING_OR_CHANGED"
                    else:
                        queries += 1
                        canary_count = conn.execute(
                            "SELECT COUNT(*) FROM galaxy_stage9v_canaries"
                        ).fetchone()[0]
                        empty_ok = type(canary_count) is int and canary_count == 1
                        for table in EMPTY_TABLES:
                            queries += 1
                            count = conn.execute(
                                f"SELECT COUNT(*) FROM {table}"
                            ).fetchone()[0]
                            if type(count) is not int or count != 0:
                                empty_ok = False
                        status = (
                            "PASS_STAGING_READ_ONLY_PREIMPORT"
                            if empty_ok and not local
                            else "PASS_LOCAL_READ_ONLY_SCHEMA_FIXTURE"
                            if empty_ok else "HOLD_STAGING_PREIMPORT_NOT_EMPTY"
                        )
    except Exception:
        status = "HOLD_STAGING_READ_UNAVAILABLE"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_CONNECTION_CLOSE_FAILED"
    out = _report(
        status, queries=queries, stage9v_status=first["status"],
        test_connector_injected=local,
    )
    out["schema_layout_verified"] = schema_ok
    out["pinned_same_database_canary_verified"] = canary_ok
    out["preimport_tables_empty_verified"] = empty_ok
    out["staging_turso_remotely_observed"] = (
        status == "PASS_STAGING_READ_ONLY_PREIMPORT" and not local
        and first.get("staging_turso_remotely_observed") is True
        and first.get("test_connector_injected") is False
    )
    if schema_ok:
        # Only static, nonsensitive table/column identifiers enter the digest.
        out["column_layout_sha256"] = _sha(
            v._bytes(EXPECTED_TABLES)
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Owner-local STAGING-ONLY read-only preimport readiness."
    )
    parser.add_argument("--pinned-canary-json", required=True)
    parser.add_argument("--confirm-read-only", action="store_true")
    parser.add_argument(
        "--confirm-independent-canary-pin", action="store_true",
    )
    args = parser.parse_args(argv)
    if not (args.confirm_read_only and args.confirm_independent_canary_pin):
        print(json.dumps(_report("HOLD_EXPLICIT_READ_ONLY_CONFIRMATION_REQUIRED")))
        return 2
    config = {
        name: os.environ.get(env, "") for name, env in vread.CONFIG.items()
    }
    if any(not value for value in config.values()):
        print(json.dumps(_report("HOLD_PRIVATE_OPERATOR_CONFIG_MISSING")))
        return 2
    try:
        raw = x._private_file(args.pinned_canary_json, MAX_PIN_BYTES)
        pin = json.loads(
            raw.decode("utf-8"), object_pairs_hook=x._pairs_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (OSError, UnicodeError, ValueError, TypeError):
        print(json.dumps(_report("HOLD_PRIVATE_CANARY_PIN_INVALID")))
        return 2
    result = check_preimport_staging(
        config=config, pin=pin, confirm_independent_canary_pin=True,
    )
    # Status and static schema digest only. No env values or private input.
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_STAGING_READ_ONLY_PREIMPORT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
