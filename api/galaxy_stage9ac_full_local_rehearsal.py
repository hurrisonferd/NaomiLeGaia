"""Stage 9AC: ONE full, disposable LOCAL rehearsal of GALAXY's staging path.

Exercises real predecessor MODULES against a newly created, disposable disk
SQLite database and a separate untouched SOVMEM-main synthetic sentinel.
The optional REAL libsql driver opens ONLY that local file through an injected
connector. No HTTP, remote Turso, user records, repo secrets or production
modules. Fixture HMACs simulate signatures and are NOT owner authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import galaxy_archive_preflight as s
import galaxy_archive_staging as t
import galaxy_stage9v_staging_turso as v
import galaxy_stage9x_owner_canary as x
import galaxy_stage9y_canonical_staging as y
import galaxy_stage9z_local_rollback as z
import galaxy_stage9aa_preimport_readonly as aa
import galaxy_stage9ab_owner_local_bootstrap as ab
import galaxy_stage9ab_prepare_private_bundle as prep
import galaxy_stage9v_setup_bundle as vsetup
import galaxy_stage9aa_local_schema_bundle as aabundle

SCHEMA = "gaiaos.galaxy.stage9ac.full-local-migration-rehearsal.v1"
STAGE = "libsql://sovmem-staging-stage9ac-fixture.turso.io"
MAIN = "libsql://sovmem-main-stage9ac-fixture.turso.io"
TOKEN = "STAGE9AC-SYNTHETIC-LOCAL-ONLY-UNUSABLE-REMOTE-CREDENTIAL"
CANARY_KEY = b"stage9ac-local-canary-test-key-never-owner-key-000001"
IMPORT_KEY = b"stage9ac-local-import-test-key-never-owner-key-000001"
ROLLBACK_KEY = b"stage9ac-local-rollback-test-key-distinct-000001"
RUN_ID = "STAGE9AC-SYNTHETIC-CANARY-0001"
APPROVAL_ID = "STAGE9AC-SYNTHETIC-IMPORT-0001"
ROLLBACK_ID = "STAGE9AC-SYNTHETIC-ROLLBACK-0001"
SOURCE = (
    b"STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY-001\n"
    b"STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY-002\n"
)
EXPECTED = {
    "private_bundle": "PASS_PRIVATE_BUNDLE_READY_ZERO_CONNECTION",
    "bootstrap": "PASS_LOCAL_STAGING_SCHEMA_REOPEN_FIXTURE",
    "canary": "HOLD_LOCAL_FIXTURE_NOT_REMOTE",
    "preimport": "PASS_LOCAL_READ_ONLY_SCHEMA_FIXTURE",
    "import": "PASS_LOCAL_CANONICAL_STAGING_REOPEN_FIXTURE",
    "import_replay": "PASS_LOCAL_EXACT_REPLAY_ZERO_WRITE",
    "rollback": "PASS_LOCAL_ROLLBACK_RECEIPT_REOPEN",
    "rollback_replay": "PASS_LOCAL_ROLLBACK_EXACT_REPLAY_ZERO_WRITE",
    "resurrection": "HOLD_PREVIOUSLY_ROLLED_BACK_SOURCE",
    "postrollback_preimport": "HOLD_STAGING_PREIMPORT_NOT_EMPTY",
    "postcanary_bootstrap": "HOLD_STAGING_NOT_EMPTY_OR_PARTIAL_SCHEMA",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _report(status: str, *, driver: str, steps: dict | None = None,
            boundary: str = "") -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status,
        "driver": driver,
        "test_only": True, "execution": "DISPOSABLE_LOCAL_FILES_ONLY",
        "step_statuses": steps or {},
        "actual_turso_connected": False,
        "actual_sovmem_staging_connected": False,
        "actual_sovmem_main_connected": False,
        "original_gaiaos_production_connected": False,
        "owner_authenticated": False,
        "provider_database_separation_verified": False,
        "production_writes": False, "remote_staging_writes": False,
        "bigbang_activated": False, "e_lanes_modified": False,
        "gravity_modified": False,
        "source_data": "SYNTHETIC_ONLY_NO_REAL_MEMORY",
        "proof_boundary": boundary or (
            "Single-process synthetic integration on disposable local files. "
            "No provider identity, credential scope, remote libSQL, replica "
            "durability, actual archived data or deployed chat proof."
        ),
    }


def _synthetic_export():
    rows = []
    for n in (1, 2):
        statement = f"STAGE9AC-SYNTHETIC-ARCHIVED-MEMORY-{n:03d}"
        rows.append({
            "source_record_id": f"synthetic-event-{n:03d}",
            "scope": "MemoryOS", "member": None,
            "record_type": "ARCHIVE_NOTE",
            "statement": statement, "statement_sha256": _sha(statement.encode()),
            "evidence_ref": f"STAGE9AC-SYNTHETIC-EVIDENCE-{n:03d}",
            "original_created_at": None, "date_confidence": "UNKNOWN",
            "attribution_basis": "UNKNOWN",
        })
    packet = {
        "schema": s.PACKET_SCHEMA,
        "archive": {
            "source_kind": "CHAT_EXPORT",
            "source_system": "synthetic-local-fixture",
            "document_id": "STAGE9AC-SYNTHETIC-NO-USER-DOCUMENT",
            "source_locator": "STAGE9AC-SYNTHETIC-NO-USER-LOCATOR",
            "source_content_sha256": _sha(SOURCE),
        },
        "records": rows,
    }
    return t._canonical(packet)


class _OnlyLocalStaging:
    """Always reject any other endpoint, regardless of injected test driver."""
    def __init__(self, stage_file: Path, driver: str):
        self.stage_file = stage_file
        self.driver = driver
        self.opens = 0

    def __call__(self, url: str, token: str):
        if url != STAGE or token != TOKEN:
            raise ValueError("unexpected nonlocal fixture target")
        self.opens += 1
        if self.driver == "libsql":
            import libsql
            return libsql.connect(database=str(self.stage_file))
        return sqlite3.connect(self.stage_file)


def run_local_rehearsal(*, driver: str = "native") -> dict[str, Any]:
    """Full synthetic chain; never accepts an external DB or real credentials."""
    if driver not in ("native", "libsql"):
        return _report("HOLD_UNKNOWN_LOCAL_DRIVER", driver=str(driver))
    stages: dict[str, str] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="stage9ac-local-only-") as tmp:
            root = Path(tmp)
            root.chmod(0o700)
            main = root / "sovmem-main-untouched-sentinel.db"
            legacy = root / "original-gaiaos-untouched-sentinel.db"
            for path, sentinel in (
                (main, "SYNTHETIC-MAIN-UNCHANGED"),
                (legacy, "SYNTHETIC-ORIGINAL-UNCHANGED"),
            ):
                with sqlite3.connect(path) as db:
                    db.execute("CREATE TABLE untouched (value TEXT NOT NULL)")
                    db.execute("INSERT INTO untouched VALUES (?)", (sentinel,))
            originals = {p: p.read_bytes() for p in (main, legacy)}
            dest = root / "owner-private-setup"
            generated = prep.prepare(destination=dest)
            stages["private_bundle"] = generated["status"]
            if stages["private_bundle"] != EXPECTED["private_bundle"]:
                return _report("HOLD_SYNTHETIC_BUNDLE", driver=driver, steps=stages)
            vdir = dest / "stage9v"
            adir = dest / "stage9aa"
            vm = ab._private_json(str(vdir / vsetup._MANIFEST_NAME))
            am = ab._private_json(str(adir / aabundle.MANIFEST_NAME))
            vs = x._private_file(str(vdir / vsetup._SQL_NAME), ab.MAX_BUNDLE_BYTES)
            ass = x._private_file(str(adir / aabundle.SQL_NAME), ab.MAX_BUNDLE_BYTES)
            marker = vm["staging_uuid"]
            stagefile = root / "disposable-staging.db"
            connector = _OnlyLocalStaging(stagefile, driver)
            setup = dict(
                staging_name="sovmem-staging", main_name="sovmem-main",
                v_manifest=vm, v_sql=vs, aa_manifest=am, aa_sql=ass,
                staging_url=STAGE, main_url=MAIN, staging_token=TOKEN,
                connector=connector,
            )
            dry = ab.bootstrap_staging(**setup)
            if (dry["status"] != "PASS_PRIVATE_BUNDLE_DRY_RUN_NO_CONNECTION"
                    or connector.opens != 0 or stagefile.exists()):
                return _report("HOLD_BOOTSTRAP_DRY_RUN", driver=driver, steps=stages)
            initialized = ab.bootstrap_staging(
                **setup, confirm_apply=True,
                confirm_provider_ids_reviewed=True,
                confirm_staging_only=True, confirm_main_untouched=True,
            )
            stages["bootstrap"] = initialized["status"]
            if stages["bootstrap"] != EXPECTED["bootstrap"]:
                return _report("HOLD_BOOTSTRAP_LOCAL", driver=driver, steps=stages)

            conf = {
                "staging_url": STAGE, "production_url": MAIN,
                "staging_token": TOKEN, "expected_staging_id": marker,
            }
            nonce = _sha(b"STAGE9AC-SYNTHETIC-LOCAL-NONCE")
            canary_manifest = {
                "schema": v.APPROVAL_SCHEMA, "authority": "NAOMI",
                "target": v.TARGET, "action": "WRITE_ONE_STAGING_CANARY",
                "expected_staging_id": marker,
                "staging_url_sha256": _sha(v._canonical_url(STAGE).encode()),
                "production_url_sha256": _sha(v._canonical_url(MAIN).encode()),
                "run_id": RUN_ID, "nonce_sha256": nonce,
            }
            canary_sig = hmac.new(
                CANARY_KEY, v._bytes(canary_manifest), hashlib.sha256,
            ).hexdigest()
            canary = x.execute_owner_local_canary(
                config=conf, approval=canary_manifest,
                signature_hex=canary_sig, approval_key=CANARY_KEY,
                confirm_provider_identity=True,
                confirm_separate_owner_approval=True, confirm_one_canary=True,
                connector=connector,
            )
            stages["canary"] = canary["status"]
            if (stages["canary"] != EXPECTED["canary"]
                    or canary.get("stage9v_canary_status") !=
                    "PASS_STAGING_CANARY_REOPEN_READBACK"
                    or canary.get("staging_turso_reopen_observed") is not False
                    or canary.get("staging_canary_written") is not True):
                return _report("HOLD_LOCAL_CANARY", driver=driver, steps=stages)
            pin = {
                "schema": aa.PIN_SCHEMA, "run_id": RUN_ID,
                "canary_sha256": canary["canary_sha256"],
                "staging_uuid_sha256": _sha(marker.encode()),
                "staging_url_sha256": canary_manifest["staging_url_sha256"],
                "production_url_sha256": canary_manifest["production_url_sha256"],
            }
            first_preflight = aa.check_preimport_staging(
                config=conf, pin=pin, confirm_independent_canary_pin=True,
                connector=connector,
            )
            stages["preimport"] = first_preflight["status"]
            if (stages["preimport"] != EXPECTED["preimport"]
                    or first_preflight["staging_turso_remotely_observed"]
                    or not first_preflight["preimport_tables_empty_verified"]):
                return _report("HOLD_LOCAL_PREIMPORT", driver=driver, steps=stages)

            raw = _synthetic_export()
            verified = t._verified_packet(raw, _sha(raw), SOURCE, _sha(SOURCE))
            if isinstance(verified, str):
                return _report("HOLD_LOCAL_SYNTHETIC_EXPORT", driver=driver, steps=stages)
            _, items = verified
            original_conf = {k: conf[k] for k in (
                "staging_url", "production_url", "expected_staging_id"
            )}
            original_manifest = y._expected_manifest(
                config=original_conf,
                approval={
                    "approval_id": APPROVAL_ID, "canary_run_id": RUN_ID,
                    "canary_sha256": canary["canary_sha256"],
                },
                export_hash=_sha(raw), source_hash=_sha(SOURCE), items=items,
            )
            original_sig = hmac.new(
                IMPORT_KEY, y._bytes(original_manifest), hashlib.sha256,
            ).hexdigest()
            params = dict(
                config=original_conf, export_bytes=raw,
                pinned_export_sha256=_sha(raw),
                source_bytes=SOURCE, pinned_source_sha256=_sha(SOURCE),
                approval=original_manifest, signature_hex=original_sig,
                approval_key=IMPORT_KEY, confirm_separate_fixture=True,
                confirm_owner_source_review=True,
                confirm_canary_evidence_review=True,
            )
            with sqlite3.connect(stagefile) as native:
                params["fixture_connection"] = native
                params["fixture_root"] = root
                imported = y.stage_historical_fixture(**params)
                stages["import"] = imported["status"]
                if stages["import"] != EXPECTED["import"]:
                    return _report("HOLD_LOCAL_IMPORT", driver=driver, steps=stages)
                imported_again = y.stage_historical_fixture(**params)
                stages["import_replay"] = imported_again["status"]
                if (stages["import_replay"] != EXPECTED["import_replay"]
                        or imported_again.get("writes_performed") != []):
                    return _report("HOLD_IMPORT_REPLAY", driver=driver, steps=stages)
                post_import = aa.check_preimport_staging(
                    config=conf, pin=pin,
                    confirm_independent_canary_pin=True, connector=connector,
                )
                if post_import["status"] != "HOLD_STAGING_PREIMPORT_NOT_EMPTY":
                    return _report("HOLD_NONEMPTY_IMPORT_GATE", driver=driver, steps=stages)
                rollback_manifest = z.expected_rollback_manifest(
                    original_manifest=original_manifest,
                    original_receipt=imported["receipt"],
                    rollback_id=ROLLBACK_ID,
                )
                rollback_sig = hmac.new(
                    ROLLBACK_KEY, y._bytes(rollback_manifest), hashlib.sha256,
                ).hexdigest()
                rollback_params = dict(
                    fixture_connection=native, fixture_root=root,
                    config=original_conf, original_manifest=original_manifest,
                    original_signature=original_sig, original_key=IMPORT_KEY,
                    rollback_manifest=rollback_manifest,
                    rollback_signature=rollback_sig, rollback_key=ROLLBACK_KEY,
                    confirm_exact_rollback=True,
                    confirm_no_live_target=True, confirm_retained_ledger=True,
                )
                rolled = z.rollback_local_import(**rollback_params)
                stages["rollback"] = rolled["status"]
                if stages["rollback"] != EXPECTED["rollback"]:
                    return _report("HOLD_LOCAL_ROLLBACK", driver=driver, steps=stages)
                rolled_again = z.rollback_local_import(**rollback_params)
                stages["rollback_replay"] = rolled_again["status"]
                if (stages["rollback_replay"] != EXPECTED["rollback_replay"]
                        or rolled_again.get("writes_performed") != []):
                    return _report("HOLD_LOCAL_ROLLBACK_REPLAY", driver=driver, steps=stages)
                # Second approval with SAME source must not resurrect deleted
                # rows, even after the first import batch ledger is retained.
                second_manifest = y._expected_manifest(
                    config=original_conf, approval={
                        "approval_id": "STAGE9AC-SYNTHETIC-SECOND-APPROVAL",
                        "canary_run_id": RUN_ID,
                        "canary_sha256": canary["canary_sha256"],
                    }, export_hash=_sha(raw), source_hash=_sha(SOURCE),
                    items=items,
                )
                second = y.stage_historical_fixture(**{
                    **params, "approval": second_manifest,
                    "signature_hex": hmac.new(
                        IMPORT_KEY, y._bytes(second_manifest),
                        hashlib.sha256,
                    ).hexdigest(),
                })
                stages["resurrection"] = second["status"]
                if stages["resurrection"] != EXPECTED["resurrection"]:
                    return _report("HOLD_RESURRECTION_NOT_BLOCKED", driver=driver, steps=stages)
                proof = {
                    table: native.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0] for table in (
                        "memory_records", "galaxy_stage9v_canaries",
                        "galaxy_stage9y_batches", "galaxy_stage9y_items",
                        "galaxy_stage9z_rollbacks",
                    )
                }
                if proof != {
                    "memory_records": 0, "galaxy_stage9v_canaries": 1,
                    "galaxy_stage9y_batches": 1, "galaxy_stage9y_items": 2,
                    "galaxy_stage9z_rollbacks": 1,
                }:
                    return _report("HOLD_LOCAL_FINAL_LEDGER_COUNTS", driver=driver, steps=stages)
            post_rollback = aa.check_preimport_staging(
                config=conf, pin=pin,
                confirm_independent_canary_pin=True, connector=connector,
            )
            stages["postrollback_preimport"] = post_rollback["status"]
            if stages["postrollback_preimport"] != EXPECTED["postrollback_preimport"]:
                return _report("HOLD_ROLLBACK_LEDGER_HIDDEN", driver=driver, steps=stages)
            after_canary = ab.bootstrap_staging(
                **setup, confirm_apply=True, confirm_provider_ids_reviewed=True,
                confirm_staging_only=True, confirm_main_untouched=True,
            )
            stages["postcanary_bootstrap"] = after_canary["status"]
            if stages["postcanary_bootstrap"] != EXPECTED["postcanary_bootstrap"]:
                return _report("HOLD_BOOTSTRAP_REENTRY", driver=driver, steps=stages)
            if any(p.read_bytes() != raw for p, raw in originals.items()):
                return _report("HOLD_MAIN_OR_ORIGINAL_SENTINEL_CHANGED",
                               driver=driver, steps=stages)
            if stages != EXPECTED:
                return _report("HOLD_INCOMPLETE_LOCAL_CHAIN", driver=driver, steps=stages)
            result = _report("PASS_FULL_SYNTHETIC_LOCAL_CHAIN",
                             driver=driver, steps=stages)
            result.update({
                "fully_reconciled_synthetic_rows": 2,
                "preserved_import_item_receipts": 2,
                "preserved_signed_rollback_receipts": 1,
                "fresh_local_connection_readbacks": True,
                "main_and_original_sentinel_byte_identical": True,
                "same_approval_import_and_rollback_replays_zero_write": True,
                "new_approval_rolled_back_source_blocked": True,
                "local_connector_open_count": connector.opens,
            })
            return result
    except Exception as exc:
        result = _report("HOLD_LOCAL_REHEARSAL_EXCEPTION",
                         driver=driver, steps=stages)
        result["exception_type"] = type(exc).__name__
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DISPOSABLE LOCAL synthetic GALAXY integration rehearsal ONLY"
    )
    parser.add_argument("--local-fixture-only", action="store_true")
    parser.add_argument("--driver", choices=("native", "libsql"),
                        default="native")
    args = parser.parse_args(argv)
    if not args.local_fixture_only:
        report = _report("HOLD_EXPLICIT_LOCAL_FIXTURE_FLAG_REQUIRED",
                         driver=args.driver)
    else:
        report = run_local_rehearsal(driver=args.driver)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS_FULL_SYNTHETIC_LOCAL_CHAIN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
