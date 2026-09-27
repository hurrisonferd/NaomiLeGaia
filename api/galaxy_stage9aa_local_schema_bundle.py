"""Stage 9AA: create local, private, NO-EFFECT canonical staging SQL bundle.

Writes exactly two new private files outside source repositories; never accesses
Turso, GitHub, production, env secrets or any database. Complements the Stage 9V
owner-local bundle, which supplies separate identity and canary tables.
Do NOT execute generated SQL before independent owner DB identity review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9v_staging_turso as v

SCHEMA = "gaiaos.galaxy.stage9aa.private-schema-bundle.v1"
SOURCE_ROOT = Path(__file__).resolve().parents[1]
SQL_NAME = "stage9aa-canonical-preimport-tables.sql"
MANIFEST_NAME = "stage9aa-local-schema-manifest.json"
_LABEL = re.compile(r"[a-z][a-z0-9-]{2,62}\Z")


def canonical_sql() -> str:
    """Four extra tables with exact Stage 9Y/9Z fixture-column compatibility."""
    return (
        "-- REVIEW FIRST. Apply ONLY to Naomi's newly provisioned,\n"
        "-- independently attested, EMPTY staging Turso database AFTER\n"
        "-- its separate Stage 9V identity and canary setup.\n"
        "-- NEVER run in original/production Turso. Source-only local bundle.\n"
        "CREATE TABLE memory_records (\n"
        "  record_id TEXT PRIMARY KEY,\n"
        "  authority TEXT NOT NULL,\n"
        "  record_type TEXT NOT NULL,\n"
        "  scope TEXT NOT NULL,\n"
        "  statement TEXT NOT NULL,\n"
        "  source TEXT NOT NULL,\n"
        "  status TEXT NOT NULL,\n"
        "  version TEXT NOT NULL,\n"
        "  created_at TEXT NOT NULL,\n"
        "  updated_at TEXT NOT NULL,\n"
        "  supersedes TEXT,\n"
        "  notes TEXT NOT NULL DEFAULT ''\n"
        ");\n"
        "CREATE TABLE galaxy_stage9y_batches (\n"
        "  approval_id TEXT PRIMARY KEY,\n"
        "  manifest_sha256 TEXT NOT NULL,\n"
        "  export_sha256 TEXT NOT NULL,\n"
        "  source_sha256 TEXT NOT NULL,\n"
        "  canary_sha256 TEXT NOT NULL,\n"
        "  receipt_json TEXT NOT NULL,\n"
        "  receipt_hmac_sha256 TEXT NOT NULL,\n"
        "  status TEXT NOT NULL,\n"
        "  created_at TEXT NOT NULL\n"
        ");\n"
        "CREATE TABLE galaxy_stage9y_items (\n"
        "  receipt_id TEXT PRIMARY KEY,\n"
        "  approval_id TEXT NOT NULL,\n"
        "  record_id TEXT NOT NULL,\n"
        "  source_key_sha256 TEXT NOT NULL,\n"
        "  statement_sha256 TEXT NOT NULL,\n"
        "  metadata_sha256 TEXT NOT NULL,\n"
        "  row_sha256 TEXT NOT NULL,\n"
        "  result TEXT NOT NULL,\n"
        "  UNIQUE(approval_id, source_key_sha256)\n"
        ");\n"
        "CREATE TABLE galaxy_stage9z_rollbacks (\n"
        "  rollback_id TEXT PRIMARY KEY,\n"
        "  import_approval_id TEXT NOT NULL UNIQUE,\n"
        "  rollback_manifest_sha256 TEXT NOT NULL,\n"
        "  import_receipt_sha256 TEXT NOT NULL,\n"
        "  receipt_json TEXT NOT NULL,\n"
        "  receipt_hmac_sha256 TEXT NOT NULL,\n"
        "  status TEXT NOT NULL,\n"
        "  created_at TEXT NOT NULL\n"
        ");\n"
    )


def _hold(status: str) -> dict:
    return {
        "schema": SCHEMA, "status": status,
        "execution": "LOCAL_PRIVATE_FILE_CREATION_ONLY",
        "database_connections": 0, "production_accessed": False,
        "remote_staging_accessed": False, "credentials_used": False,
        "git_updated": False, "writes_performed": [],
        "live_owner_authentication_verified": False,
        "provider_database_separation_verified": False,
    }


def create_bundle(*, destination: Path, staging_name_label: str) -> dict:
    if (not isinstance(destination, Path)
            or not isinstance(staging_name_label, str)
            or _LABEL.fullmatch(staging_name_label) is None):
        return _hold("HOLD_INVALID_PRIVATE_BUNDLE_ARGUMENTS")
    if destination.expanduser().is_symlink():
        return _hold("HOLD_SYMLINK_OUTPUT_FORBIDDEN")
    resolved = destination.expanduser().resolve()
    if (resolved == SOURCE_ROOT or SOURCE_ROOT in resolved.parents
            or resolved.exists() or resolved.parent == resolved):
        return _hold("HOLD_PRIVATE_NEW_DIRECTORY_REQUIRED_OUTSIDE_REPO")
    try:
        parent = resolved.parent
        s = parent.stat()
        if (not parent.is_dir() or s.st_mode & 0o077
                or (hasattr(os, "getuid") and s.st_uid != os.getuid())):
            return _hold("HOLD_PARENT_DIRECTORY_MUST_BE_OWNER_ONLY")
    except OSError:
        return _hold("HOLD_PARENT_DIRECTORY_UNAVAILABLE")
    sql = canonical_sql().encode("utf-8")
    manifest = {
        "schema": SCHEMA,
        "status": "OWNER_LOCAL_SCHEMA_FILES_ONLY_NOT_PROVISIONED",
        "staging_name_label_only": staging_name_label,
        "source_sql_sha256": hashlib.sha256(sql).hexdigest(),
        "expected_layout_sha256": aa._sha(v._bytes(aa.EXPECTED_TABLES)),
        "additional_table_names": [
            "memory_records", "galaxy_stage9y_batches",
            "galaxy_stage9y_items", "galaxy_stage9z_rollbacks",
        ],
        "requires_independent_stage9v_identity_canary_setup": True,
        "live_staging_provisioned": False,
        "production_database_accessed": False,
        "tokens_included": False,
        "next_gate": "OWNER_REVIEWS_SQL_AND_INDEPENDENTLY_ATTESTS_NEW_STAGING_TARGET",
    }
    try:
        resolved.mkdir(mode=0o700)
        for filename, raw in (
            (SQL_NAME, sql),
            (MANIFEST_NAME, (
                json.dumps(manifest, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8")),
        ):
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            flags |= getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(resolved / filename, flags, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
            os.chmod(resolved / filename, 0o600)
        os.chmod(resolved, 0o700)
    except OSError:
        return _hold("HOLD_PRIVATE_BUNDLE_FILE_CREATION_FAILED")
    out = _hold("PASS_LOCAL_SCHEMA_BUNDLE_CREATED")
    out.update({
        "writes_performed": ["NEW_LOCAL_PRIVATE_SQL", "NEW_LOCAL_PRIVATE_MANIFEST"],
        "files": [SQL_NAME, MANIFEST_NAME],
        "sql_sha256": manifest["source_sql_sha256"],
        "expected_layout_sha256": manifest["expected_layout_sha256"],
        "production_release_activated": False,
    })
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate private preimport SQL; NEVER connects to any DB."
    )
    parser.add_argument("--destination", required=True)
    parser.add_argument("--staging-name-label", required=True)
    parser.add_argument("--confirm-local-file-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm_local_file_only:
        out = _hold("HOLD_EXPLICIT_LOCAL_ONLY_FLAG_REQUIRED")
    else:
        out = create_bundle(
            destination=Path(args.destination),
            staging_name_label=args.staging_name_label,
        )
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"] == "PASS_LOCAL_SCHEMA_BUNDLE_CREATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
