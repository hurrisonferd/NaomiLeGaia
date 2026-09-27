"""Read-only Stage 9V operator preflight for a *separate* staging Turso target.

No schema creation, INSERT, UPDATE, DELETE, transaction, canary run, HTTP route,
MemconOS import or default production credentials. A passing preflight verifies
the supplied marker and canary table can be read, NOT provider-level database
separation, staging write permission, live owner identity or restart durability.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Callable

import galaxy_stage9v_staging_turso as probe

SCHEMA = "gaiaos.galaxy.stage9v.operator-readiness.v1"
EXPECTED_COLUMNS = ("run_id", "nonce_sha256", "database_id", "created_at")
CONFIG = {
    "staging_url": "GAIAOS_STAGE9V_STAGING_URL",
    "staging_token": "GAIAOS_STAGE9V_STAGING_TOKEN",
    "production_url": "GAIAOS_STAGE9V_PRODUCTION_URL",
    "expected_staging_id": "GAIAOS_STAGE9V_STAGING_UUID",
}


def _base(status: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status,
        "execution": "READ_ONLY",
        "reads_performed": 0, "writes_performed": [],
        "production_turso_accessed": False,
        "memory_records_modified": False, "gravity_modified": False,
        "e_lanes_modified": False, "mode_control_modified": False,
        "canary_written": False, "staging_turso_remotely_observed": False,
        "provider_database_separation_independently_verified": False,
        "live_owner_authentication_verified": False,
    }


def check_staging_readiness(
    *, staging_url: str, staging_token: str,
    production_url: str, expected_staging_id: str,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Perform only two SELECTs against the explicitly supplied staging URL."""
    staging = probe._canonical_url(staging_url)
    production = probe._canonical_url(production_url)
    if staging is None or production is None or staging == production:
        return _base("HOLD_STAGING_AND_PRODUCTION_URLS_NOT_SEPARATE")
    if not isinstance(staging_token, str) or not 16 <= len(staging_token) <= 8192:
        return _base("HOLD_STAGING_TOKEN_MISSING")
    if not probe._valid_id(expected_staging_id):
        return _base("HOLD_STAGING_UUID_INVALID")
    connect = connector if connector is not None else probe._connect_live
    if not callable(connect):
        return _base("HOLD_CONNECTOR_INVALID")
    conn = None
    reads = 0
    status = "HOLD_SOURCE_UNAVAILABLE"
    try:
        conn = connect(staging_url, staging_token)
        # _identity itself SELECTs once, and refuses missing/duplicated rows.
        reads += 1
        if not probe._identity(conn, expected_staging_id):
            status = "HOLD_STAGING_IDENTITY_UNVERIFIED"
        else:
            reads += 1
            cursor = conn.execute(
                "SELECT run_id,nonce_sha256,database_id,created_at "
                "FROM galaxy_stage9v_canaries LIMIT 0",
            )
            columns = tuple(
                col[0] if isinstance(col, (tuple, list))
                else getattr(col, "name", str(col))
                for col in cursor.description
            )
            status = (
                "PASS_STAGING_READINESS_READ_ONLY"
                if columns == EXPECTED_COLUMNS
                else "HOLD_CANARY_SCHEMA_UNEXPECTED"
            )
    except Exception as exc:
        result = _base("HOLD_STAGING_READ_UNAVAILABLE")
        result["error_type"] = type(exc).__name__
        result["reads_performed"] = reads
        return result
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                # Connection-close errors may be examined by the operator; never
                # echo exception strings, which sometimes contain credentials.
                status = "HOLD_STAGING_CONNECTION_CLOSE_FAILED"
    result = _base(status)
    result["reads_performed"] = reads
    if status == "PASS_STAGING_READINESS_READ_ONLY":
        result.update({
            "staging_url_sha256": probe._sha(staging.encode()),
            "production_url_sha256": probe._sha(production.encode()),
            "staging_uuid_sha256": probe._sha(expected_staging_id.encode()),
            "staging_marker_readback_verified": True,
            "canary_table_select_verified": True,
            "staging_turso_remotely_observed": connector is None,
            "test_connector_injected": connector is not None,
            "next_gate": "SIGNED_SINGLE_STAGING_CANARY_AFTER_INDEPENDENT_PROVIDER_IDENTITY_CHECK",
        })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only GALAXY Stage 9V staging Turso preflight (NO WRITES)."
    )
    parser.add_argument(
        "--confirm-read-only", action="store_true",
        help="Explicitly select the read-only identity/table preflight.",
    )
    args = parser.parse_args(argv)
    if not args.confirm_read_only:
        print(json.dumps(_base("HOLD_EXPLICIT_READ_ONLY_FLAG_REQUIRED"), sort_keys=True))
        return 2
    values = {name: os.environ.get(env, "") for name, env in CONFIG.items()}
    absent = [env for name, env in CONFIG.items() if not values[name]]
    if absent:
        result = _base("HOLD_REQUIRED_OPERATOR_ENV_UNSET")
        result["missing_variable_names"] = absent
        print(json.dumps(result, sort_keys=True))
        return 2
    result = check_staging_readiness(**values)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_STAGING_READINESS_READ_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
