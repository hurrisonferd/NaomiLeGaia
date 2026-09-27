"""GALAXY 9AB: owner-local, guarded EMPTY staging bootstrap, no browser SQL.

Source-only draft. The CLI is DRY RUN by default, imports no remote
credentials into GitHub, and never connects to a production URL. ONLY an
explicit future owner-run --apply may create schema in an independently
reviewed, empty STAGING Turso using a staging-only token. This module is
not owner authentication, alias attestation or production release evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from typing import Any, Callable
from urllib.parse import urlsplit

import galaxy_stage9v_setup_bundle as vsetup
import galaxy_stage9v_staging_turso as v
import galaxy_stage9x_owner_canary as x
import galaxy_stage9aa_local_schema_bundle as aabundle
import galaxy_stage9aa_preimport_readonly as aa

SCHEMA = "gaiaos.galaxy.stage9ab.guarded-staging-bootstrap.v1"
TARGET = "EMPTY_OWNER_CONTROLLED_STAGING_ONLY"
_LABEL = re.compile(r"[a-z][a-z0-9-]{2,62}\Z")
MAX_BUNDLE_BYTES = 16_384
TABLES = frozenset(aa.EXPECTED_TABLES)
ZERO_TABLES = (
    "memory_records", "galaxy_stage9y_batches",
    "galaxy_stage9y_items", "galaxy_stage9z_rollbacks",
)


def _report(status: str, *, injected: bool = False,
            ambiguous: bool = False, performed: bool = False) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "test_connector_injected": injected,
        "owner_identity_independently_verified": False,
        "provider_database_separation_independently_verified": False,
        "staging_token_scope_independently_verified": False,
        "production_database_connected": False,
        "production_database_modified": False,
        "sovmem_main_modified": False,
        "e_lanes_modified": False, "gravity_modified": False,
        "bigbang_activated": False, "historical_rows_imported": 0,
        "staging_write_outcome_unknown": ambiguous,
        "writes_performed": (
            ["STAGING_SCHEMA_SETUP_OUTCOME_UNVERIFIED"] if ambiguous
            else ["SIX_STAGING_TABLES_AND_ONE_MARKER_INSERTED"] if performed
            else []
        ),
        "next_gate": (
            "OWNER_REVIEWS_INDEPENDENT_PROVIDER_ID_AND_SINGLE_STAGE9X_CANARY"
            if performed else "NO_REMOTE_ACTION_AUTHORIZED_BY_THIS_RECEIPT"
        ),
        "proof_boundary": (
            "A local fixture pass is never live Turso proof. A live schema "
            "readback is not provider alias, owner identity, token-scope, "
            "replica/restart, archive import, rollback or production proof."
        ),
    }


def _hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _private_json(path: str) -> dict[str, Any]:
    raw = x._private_file(path, MAX_BUNDLE_BYTES)
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=x._pairs_unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    if not isinstance(value, dict):
        raise ValueError("invalid private manifest")
    return value


def _bundle_verified(
    *, staging_name: str,
    v_manifest: Any, v_sql: Any,
    aa_manifest: Any, aa_sql: Any,
) -> str | None:
    """Compare private file bytes with static, reviewed source generators.

    Never execute arbitrary SQL from a caller-supplied file.
    Returns the UUID only if both private manifests and SQL match exactly.
    """
    if not isinstance(staging_name, str) or _LABEL.fullmatch(staging_name) is None:
        return None
    if (not isinstance(v_manifest, dict) or not isinstance(aa_manifest, dict)
            or not isinstance(v_sql, bytes) or not isinstance(aa_sql, bytes)
            or len(v_sql) > MAX_BUNDLE_BYTES or len(aa_sql) > MAX_BUNDLE_BYTES):
        return None
    marker = v_manifest.get("staging_uuid")
    if not v._valid_id(marker):
        return None
    if (v_manifest.get("schema") != vsetup.MANIFEST_SCHEMA
            or v_manifest.get("status") != "OWNER_LOCAL_BUNDLE_CREATED_NOT_PROVISIONED"
            or v_manifest.get("database_name_label_only") != staging_name
            or v_manifest.get("tokens_included") is not False
            or v_manifest.get("staging_database_accessed") is not False
            or aa_manifest.get("schema") != aabundle.SCHEMA
            or aa_manifest.get("status") != "OWNER_LOCAL_SCHEMA_FILES_ONLY_NOT_PROVISIONED"
            or aa_manifest.get("staging_name_label_only") != staging_name
            or aa_manifest.get("tokens_included") is not False
            or aa_manifest.get("live_staging_provisioned") is not False):
        return None
    try:
        expected_v_sql = vsetup.make_sql(marker).encode("utf-8")
        expected_aa_sql = aabundle.canonical_sql().encode("utf-8")
        expected_layout = aa._sha(v._bytes(aa.EXPECTED_TABLES))
    except (TypeError, ValueError):
        return None
    if (v_sql != expected_v_sql or aa_sql != expected_aa_sql
            or v_manifest.get("staging_sql_sha256") != _hex(v_sql)
            or aa_manifest.get("source_sql_sha256") != _hex(aa_sql)
            or aa_manifest.get("expected_layout_sha256") != expected_layout):
        return None
    return marker


def _commands(marker: str) -> tuple[str, ...]:
    """Deterministically compile ONLY the reviewed static generator output."""
    src = vsetup.make_sql(marker) + aabundle.canonical_sql()
    stmts = []
    for part in src.split(";"):
        without_comments = re.sub(r"(?m)^--[^\n]*(?:\n|$)", "", part).strip()
        if without_comments:
            stmts.append(without_comments)
    prefixes = (
        "CREATE TABLE galaxy_stage9v_staging_identity",
        "INSERT INTO galaxy_stage9v_staging_identity",
        "CREATE TABLE galaxy_stage9v_canaries",
        "CREATE TABLE memory_records",
        "CREATE TABLE galaxy_stage9y_batches",
        "CREATE TABLE galaxy_stage9y_items",
        "CREATE TABLE galaxy_stage9z_rollbacks",
    )
    if len(stmts) != len(prefixes) or any(
        not stmt.startswith(prefix + " ") and not stmt.startswith(prefix + "\n")
        and not stmt.startswith(prefix + "(")
        for stmt, prefix in zip(stmts, prefixes)
    ):
        raise ValueError("unexpected source DDL")
    return tuple(stmts)


def _known_empty(conn: Any) -> bool:
    """Freshly created Turso must have NO tables, views or triggers."""
    cursor = conn.execute(
        "SELECT type,name FROM sqlite_master "
        "WHERE type IN ('table','view','trigger')"
    )
    for kind, name in cursor.fetchall():
        if not (kind == "table" and name == "sqlite_sequence"):
            return False
    return True


def _exact_new_schema(conn: Any, marker: str) -> bool:
    """Inspect exact table names, column layouts, marker and ZERO test rows."""
    try:
        raw = conn.execute(
            "SELECT type,name FROM sqlite_master "
            "WHERE type IN ('table','view','trigger')"
        ).fetchall()
        objects = {(kind, name) for kind, name in raw
                   if not name.startswith("sqlite_")}
        if objects != {("table", table) for table in TABLES}:
            return False
        for table, expected in aa.EXPECTED_TABLES.items():
            cursor = conn.execute(f"SELECT * FROM {table} LIMIT 0")
            if aa._columns(cursor) != expected:
                return False
        if not v._identity(conn, marker):
            return False
        if conn.execute(
            "SELECT COUNT(*) FROM galaxy_stage9v_canaries"
        ).fetchone()[0] != 0:
            return False
        for table in ZERO_TABLES:
            if conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] != 0:
                return False
        return True
    except Exception:
        return False


def _host_has_label(url: str, label: str) -> bool:
    try:
        host = urlsplit(url).hostname
        return isinstance(host, str) and host.startswith(label + "-")
    except (TypeError, ValueError):
        return False


def bootstrap_staging(
    *, staging_name: str, main_name: str,
    v_manifest: dict[str, Any], v_sql: bytes,
    aa_manifest: dict[str, Any], aa_sql: bytes,
    staging_url: str = "", main_url: str = "", staging_token: str = "",
    confirm_apply: bool = False, confirm_provider_ids_reviewed: bool = False,
    confirm_staging_only: bool = False, confirm_main_untouched: bool = False,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Dry run validates private source artifacts without connecting.

    When separately invoked with four explicit approvals, refuses mismatched
    host labels, missing staging-only token or an existing nonempty database.
    Cannot assert genuinely independent control-plane database identity.
    """
    injected = connector is not None
    marker = _bundle_verified(
        staging_name=staging_name, v_manifest=v_manifest, v_sql=v_sql,
        aa_manifest=aa_manifest, aa_sql=aa_sql,
    )
    if marker is None:
        return _report("HOLD_PRIVATE_SCHEMA_BUNDLE_INVALID", injected=injected)
    if not confirm_apply:
        return _report("PASS_PRIVATE_BUNDLE_DRY_RUN_NO_CONNECTION",
                       injected=injected)
    if not all((
        confirm_provider_ids_reviewed is True,
        confirm_staging_only is True,
        confirm_main_untouched is True,
    )):
        return _report("HOLD_EXPLICIT_OWNER_STAGING_APPROVAL_REQUIRED",
                       injected=injected)
    stage = v._canonical_url(staging_url)
    main = v._canonical_url(main_url)
    if (not isinstance(main_name, str)
            or _LABEL.fullmatch(main_name) is None or main_name == staging_name
            or stage is None or main is None or stage == main
            or not _host_has_label(staging_url, staging_name)
            or not _host_has_label(main_url, main_name)):
        return _report("HOLD_STAGING_MAIN_ADDRESS_OR_NAME_INVALID",
                       injected=injected)
    if (not isinstance(staging_token, str)
            or not 16 <= len(staging_token) <= 8192):
        return _report("HOLD_STAGING_ONLY_TOKEN_REQUIRED", injected=injected)

    connect = connector if injected else v._connect_live
    conn = None
    write_attempted = False
    committed = False
    replay = False
    status: str | None = None
    try:
        conn = connect(staging_url, staging_token)
        # Observe an EMPTY target with SELECTs before BEGIN IMMEDIATE.
        if _known_empty(conn):
            conn.execute("BEGIN IMMEDIATE")
            if not _known_empty(conn):
                conn.rollback()
                status = "HOLD_STAGING_CHANGED_BEFORE_TRANSACTION"
            else:
                for stmt in _commands(marker):
                    write_attempted = True
                    conn.execute(stmt)
                if not _exact_new_schema(conn, marker):
                    raise ValueError("transactional staged schema readback mismatch")
                conn.commit()
                committed = True
        elif _exact_new_schema(conn, marker):
            # Safe recovery of an uncertain earlier commit. Verify again from
            # another connection. No CREATE IF NOT EXISTS, no surprise writes.
            replay = True
        else:
            status = "HOLD_STAGING_NOT_EMPTY_OR_PARTIAL_SCHEMA"
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return _report("HOLD_STAGING_SETUP_OR_COMMIT_UNVERIFIED",
                       injected=injected, ambiguous=write_attempted)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                status = "HOLD_STAGING_CONNECTION_CLOSE_FAILED"
    if status is not None:
        return _report(status, injected=injected,
                       ambiguous=write_attempted and (committed or status.endswith("FAILED")))
    second = None
    status = None
    try:
        second = connect(staging_url, staging_token)
        if not _exact_new_schema(second, marker):
            status = "HOLD_FRESH_STAGING_SCHEMA_READBACK_CHANGED"
    except Exception:
        status = "HOLD_FRESH_STAGING_SCHEMA_UNAVAILABLE"
    finally:
        if second is not None:
            try:
                second.close()
            except Exception:
                status = "HOLD_FRESH_STAGING_CLOSE_UNVERIFIED"
    if status is not None:
        return _report(status, injected=injected, ambiguous=committed)
    report = _report(
        "PASS_LOCAL_STAGING_SCHEMA_REOPEN_FIXTURE" if injected and not replay
        else "PASS_LOCAL_STAGING_SCHEMA_EXACT_REPLAY_NO_WRITE" if injected
        else "PASS_STAGING_SCHEMA_REOPEN_OBSERVED" if not replay
        else "PASS_STAGING_SCHEMA_EXACT_REPLAY_NO_WRITE",
        injected=injected, performed=committed,
    )
    report.update({
        "new_staging_tables_verified": len(TABLES),
        "stage9v_marker_sha256": _hex(marker.encode()),
        "reviewed_bundle_sha256": _hex(v_sql + aa_sql),
        "fresh_separate_connection_readback": True,
        "idempotent_read_only_replay": replay,
        "staging_remotely_observed": not injected,
    })
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run owner-private two-bundle STAGING bootstrap; "
                    "NO DB connection without explicit --apply + approvals."
    )
    parser.add_argument("--stage9v-manifest", required=True)
    parser.add_argument("--stage9v-sql", required=True)
    parser.add_argument("--stage9aa-manifest", required=True)
    parser.add_argument("--stage9aa-sql", required=True)
    parser.add_argument("--staging-name", default="sovmem-staging")
    parser.add_argument("--main-name", default="sovmem-main")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-provider-ids-reviewed", action="store_true")
    parser.add_argument("--confirm-staging-only", action="store_true")
    parser.add_argument("--confirm-main-untouched", action="store_true")
    args = parser.parse_args(argv)
    try:
        vmanifest = _private_json(args.stage9v_manifest)
        asmanifest = _private_json(args.stage9aa_manifest)
        vsql = x._private_file(args.stage9v_sql, MAX_BUNDLE_BYTES)
        assql = x._private_file(args.stage9aa_sql, MAX_BUNDLE_BYTES)
    except (OSError, UnicodeError, ValueError, TypeError):
        out = _report("HOLD_OWNER_PRIVATE_BUNDLE_FILES_INVALID")
        print(json.dumps(out, sort_keys=True))
        return 2
    config = {}
    if args.apply:
        config = {
            "staging_url": os.environ.get("GAIAOS_STAGE9V_STAGING_URL", ""),
            "main_url": os.environ.get("GAIAOS_STAGE9V_PRODUCTION_URL", ""),
            "staging_token": os.environ.get("GAIAOS_STAGE9V_STAGING_TOKEN", ""),
        }
        if os.environ.get("GAIAOS_STAGE9V_STAGING_UUID") != vmanifest.get("staging_uuid"):
            out = _report("HOLD_STAGING_UUID_PRIVATE_CONFIG_MISMATCH")
            print(json.dumps(out, sort_keys=True))
            return 2
    out = bootstrap_staging(
        staging_name=args.staging_name, main_name=args.main_name,
        v_manifest=vmanifest, v_sql=vsql,
        aa_manifest=asmanifest, aa_sql=assql,
        confirm_apply=args.apply,
        confirm_provider_ids_reviewed=args.confirm_provider_ids_reviewed,
        confirm_staging_only=args.confirm_staging_only,
        confirm_main_untouched=args.confirm_main_untouched,
        **config,
    )
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
