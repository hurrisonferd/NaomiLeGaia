"""Stage 9V: prepare an owner-local, NO-EFFECT staging identity setup bundle.

Never calls Turso, GitHub, the production database, environment variables or
secrets. Never writes into the original repository. Creates exactly two local
files in a NEW private output directory: staging-only SQL and matching manifest.
The owner must independently provision and inspect the separate database
before manually executing this SQL there.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_SCHEMA = "gaiaos.galaxy.stage9v.owner-local-setup-bundle.v1"
IDENTITY_SCHEMA = "gaiaos.galaxy.stage9v.staging-identity.v1"
_DBNAME = re.compile(r"[a-z][a-z0-9-]{2,62}\Z")
_ROOT = Path(__file__).resolve().parents[1]
_SQL_NAME = "stage9v-new-staging-identity.sql"
_MANIFEST_NAME = "stage9v-local-setup-manifest.json"


def _hold(reason: str) -> dict:
    return {
        "schema": MANIFEST_SCHEMA, "status": reason,
        "execution": "LOCAL_FILE_CREATE_ONLY",
        "database_connections": 0, "production_writes": False,
        "staging_writes": False, "git_updates": False,
        "credentials_used": False, "owner_staging_provisioned": False,
        "writes_performed": [],
    }


def make_sql(marker_uuid: str) -> str:
    """Static schema plus UUIDv4 validated BEFORE interpolation; no SQL injection."""
    if not isinstance(marker_uuid, str):
        raise ValueError("staging UUID missing")
    parsed = uuid.UUID(marker_uuid)
    if parsed.version != 4 or str(parsed) != marker_uuid:
        raise ValueError("staging identity must be canonical UUIDv4")
    return (
        "-- RUN ONLY in a brand-new independently verified owner-controlled\n"
        "-- STAGING Turso database. NEVER in current GaiaOS production Turso.\n"
        "CREATE TABLE galaxy_stage9v_staging_identity (\n"
        "  schema TEXT NOT NULL, environment TEXT NOT NULL,\n"
        "  database_id TEXT PRIMARY KEY, authority TEXT NOT NULL,\n"
        "  status TEXT NOT NULL\n"
        ");\n"
        "INSERT INTO galaxy_stage9v_staging_identity\n"
        "  (schema,environment,database_id,authority,status)\n"
        "VALUES (\n"
        f"  '{IDENTITY_SCHEMA}', 'STAGING_ONLY',\n"
        f"  '{marker_uuid}', 'NAOMI', 'ACTIVE'\n"
        ");\n"
        "CREATE TABLE galaxy_stage9v_canaries (\n"
        "  run_id TEXT PRIMARY KEY, nonce_sha256 TEXT NOT NULL,\n"
        "  database_id TEXT NOT NULL, created_at TEXT NOT NULL\n"
        ");\n"
    )


def create_bundle(*, destination: Path, database_name: str) -> dict:
    """Create an owner-local new directory and a bounded zero-credential bundle.

    No overwrite, no symlink redirection and never a path inside source repo.
    A partial directory on I/O failure remains private and must be inspected.
    """
    if not isinstance(database_name, str) or _DBNAME.fullmatch(database_name) is None:
        return _hold("HOLD_DATABASE_NAME_INVALID")
    if not isinstance(destination, Path):
        return _hold("HOLD_OUTPUT_PATH_INVALID")
    resolved = destination.expanduser().resolve()
    if resolved == _ROOT or _ROOT in resolved.parents:
        return _hold("HOLD_REFUSE_BUNDLE_INSIDE_ORIGINAL_REPOSITORY")
    if resolved.exists() or destination.is_symlink():
        return _hold("HOLD_OUTPUT_DIRECTORY_MUST_BE_NEW")
    if resolved.parent == resolved or not resolved.parent.is_dir():
        return _hold("HOLD_PRIVATE_PARENT_MISSING")
    # Don't generate a bundle in a shared world-writable directory unless it
    # has the sticky bit; avoid opportunistic replacement of its new name.
    parent_stat = resolved.parent.stat()
    if parent_stat.st_mode & 0o002 and not parent_stat.st_mode & 0o1000:
        return _hold("HOLD_UNSAFE_PARENT_DIRECTORY")
    marker = str(uuid.uuid4())
    sql = make_sql(marker).encode("utf-8")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": "OWNER_LOCAL_BUNDLE_CREATED_NOT_PROVISIONED",
        "database_name_label_only": database_name,
        "staging_uuid": marker,
        "staging_sql_sha256": hashlib.sha256(sql).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_repository_changed": False,
        "production_database_accessed": False,
        "staging_database_accessed": False,
        "tokens_included": False,
        "next_gate": "OWNER_INDEPENDENTLY_PROVISIONS_EMPTY_STAGING_DB_AND_INSPECTS_SQL",
        "warnings": [
            "Do not run the generated SQL against the existing production database.",
            "Do not store independent staging credentials in the hurrisonferd-owned repository.",
            "A UUID marker is not proof of provider-level database separation.",
        ],
    }
    try:
        resolved.mkdir(mode=0o700)
        for name, raw in (
            (_SQL_NAME, sql),
            (_MANIFEST_NAME, (
                json.dumps(manifest, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8")),
        ):
            fd = os.open(resolved / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
            except Exception:
                raise
        os.chmod(resolved, 0o700)
    except OSError:
        return _hold("HOLD_LOCAL_BUNDLE_WRITE_FAILED")
    return {
        **_hold("PASS_OWNER_LOCAL_BUNDLE_CREATED"),
        "writes_performed": ["NEW_PRIVATE_LOCAL_SQL_FILE", "NEW_PRIVATE_LOCAL_MANIFEST"],
        "staging_sql_sha256": manifest["staging_sql_sha256"],
        "bundle_files": [_SQL_NAME, _MANIFEST_NAME],
        "secrets_included": False,
        "provider_database_separation_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Generate private staging schema files locally. NO database access."
    )
    cli.add_argument("--destination", required=True)
    cli.add_argument("--database-name", required=True)
    cli.add_argument("--confirm-local-only", action="store_true")
    args = cli.parse_args(argv)
    if not args.confirm_local_only:
        report = _hold("HOLD_EXPLICIT_LOCAL_ONLY_FLAG_REQUIRED")
    else:
        report = create_bundle(
            destination=Path(args.destination), database_name=args.database_name,
        )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS_OWNER_LOCAL_BUNDLE_CREATED" else 2


if __name__ == "__main__":
    sys.exit(main())
