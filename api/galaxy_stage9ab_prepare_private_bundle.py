"""Stage 9AB: ONE owner-private, ZERO-CONNECTION staging bundle prep command.

Never reads secrets, creates a database, connects to Turso, opens a browser,
touches the old shared repo or writes to sovmem-main. The only outputs are
reviewable private files in one brand-new, user-chosen owner-only directory.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path

import galaxy_stage9v_setup_bundle as vsetup
import galaxy_stage9aa_local_schema_bundle as aabundle
import galaxy_stage9ab_owner_local_bootstrap as bootstrap
import galaxy_stage9x_owner_canary as x

SCHEMA = "gaiaos.galaxy.stage9ab.private-one-command-preparation.v1"
ROOT = Path(__file__).resolve().parents[1]


def _out(status: str, *, partial: bool = False) -> dict:
    return {
        "schema": SCHEMA, "status": status,
        "local_files_created": (
            "PARTIAL_PRIVATE_FILES_REQUIRE_MANUAL_INSPECTION" if partial
            else "FOUR_NEW_PRIVATE_REVIEW_FILES" if status.startswith("PASS")
            else "NONE"
        ),
        "database_connections": 0, "credentials_requested": False,
        "remote_staging_accessed": False, "main_accessed": False,
        "github_updated": False,
        "provider_database_separation_verified": False,
        "next_step": (
            "INSPECT_LOCAL_BUNDLE_THEN_RUN_STAGE9AB_DRY_RUN"
            if status.startswith("PASS") else "HOLD_NO_LIVE_DATABASE_ACTION"
        ),
    }


def prepare(*, destination: Path, staging_name: str = "sovmem-staging") -> dict:
    if (not isinstance(destination, Path)
            or not isinstance(staging_name, str)
            or bootstrap._LABEL.fullmatch(staging_name) is None):
        return _out("HOLD_INVALID_ARGUMENTS")
    candidate = destination.expanduser()
    if candidate.is_symlink():
        return _out("HOLD_PRIVATE_DIRECTORY_SYMLINK_FORBIDDEN")
    resolved = candidate.resolve()
    if (resolved == ROOT or ROOT in resolved.parents or resolved.exists()
            or resolved.parent == resolved):
        return _out("HOLD_BRAND_NEW_DIR_REQUIRED_OUTSIDE_SHARED_REPOSITORY")
    try:
        parent = resolved.parent
        info = parent.stat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077
                or (hasattr(os, "getuid") and info.st_uid != os.getuid())):
            return _out("HOLD_PARENT_NOT_OWNER_PRIVATE")
    except OSError:
        return _out("HOLD_PRIVATE_PARENT_MISSING")
    try:
        resolved.mkdir(mode=0o700)
        os.chmod(resolved, 0o700)
    except OSError:
        return _out("HOLD_PRIVATE_DIRECTORY_CREATION_FAILED")
    vdir = resolved / "stage9v"
    adir = resolved / "stage9aa"
    try:
        vresult = vsetup.create_bundle(
            destination=vdir, database_name=staging_name,
        )
        if vresult["status"] != "PASS_OWNER_LOCAL_BUNDLE_CREATED":
            return _out("HOLD_STAGE9V_LOCAL_GENERATOR_FAILED", partial=True)
        aresult = aabundle.create_bundle(
            destination=adir, staging_name_label=staging_name,
        )
        if aresult["status"] != "PASS_LOCAL_SCHEMA_BUNDLE_CREATED":
            return _out("HOLD_STAGE9AA_LOCAL_GENERATOR_FAILED", partial=True)
        vmanifest = bootstrap._private_json(
            str(vdir / vsetup._MANIFEST_NAME)
        )
        amanifest = bootstrap._private_json(
            str(adir / aabundle.MANIFEST_NAME)
        )
        vsql = x._private_file(
            str(vdir / vsetup._SQL_NAME), bootstrap.MAX_BUNDLE_BYTES,
        )
        asql = x._private_file(
            str(adir / aabundle.SQL_NAME), bootstrap.MAX_BUNDLE_BYTES,
        )
        if bootstrap._bundle_verified(
            staging_name=staging_name,
            v_manifest=vmanifest, v_sql=vsql,
            aa_manifest=amanifest, aa_sql=asql,
        ) is None:
            return _out("HOLD_GENERATED_SOURCE_VERIFICATION_FAILED",
                        partial=True)
    except (OSError, ValueError, TypeError, KeyError):
        return _out("HOLD_PRIVATE_FILE_PREPARATION_FAILED", partial=True)
    out = _out("PASS_PRIVATE_BUNDLE_READY_ZERO_CONNECTION")
    out["relative_files"] = [
        "stage9v/" + vsetup._MANIFEST_NAME,
        "stage9v/" + vsetup._SQL_NAME,
        "stage9aa/" + aabundle.MANIFEST_NAME,
        "stage9aa/" + aabundle.SQL_NAME,
    ]
    out["live_staging_provisioned"] = False
    out["main_database_touched"] = False
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="ONE private local bundle creation command; NO database access."
    )
    p.add_argument("--destination", required=True)
    p.add_argument("--staging-name", default="sovmem-staging")
    p.add_argument("--confirm-local-only", action="store_true")
    args = p.parse_args(argv)
    out = (
        prepare(
            destination=Path(args.destination),
            staging_name=args.staging_name,
        ) if args.confirm_local_only
        else _out("HOLD_EXPLICIT_NO_DATABASE_FILE_ONLY_CONFIRMATION_REQUIRED")
    )
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
