"""Stage 9T: enforce pinned export/source bytes and atomic in-memory-only import."""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_archive_preflight as preflight
import galaxy_archive_staging as stage

SECRET = b"staging-only-fixture-key-not-a-real-owner-secret-00000"
SOURCE = b"Source dossier:\nPRIVATE-MEMORY-LINE-001\nPRIVATE-MEMORY-LINE-002\n"
DOCUMENT_ID = "PRIVATE-DOCUMENT-ID-SECRET"
LOCATION = "PRIVATE-SOURCE-LOCATION-SECRET"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def record(n=1, *, scope="MemoryOS", member=None, statement=None, confidence="UNKNOWN", timestamp=None):
    statement = statement or f"PRIVATE-MEMORY-LINE-{n:03d}"
    return {
        "source_record_id": f"event-{n:03d}",
        "scope": scope, "member": member, "record_type": "ARCHIVE_NOTE",
        "statement": statement, "statement_sha256": _sha(statement.encode()),
        "evidence_ref": f"PRIVATE-REF-{n:03d}",
        "original_created_at": timestamp, "date_confidence": confidence,
        "attribution_basis": "EXPLICIT_SOURCE" if member is not None else "UNKNOWN",
    }


def envelope(records=None, *, source=SOURCE, approval_id="stage9t-fixture-0001"):
    records = records if records is not None else [record()]
    packet = {
        "schema": preflight.PACKET_SCHEMA,
        "archive": {
            "source_kind": "CHAT_EXPORT", "source_system": "owner-export",
            "document_id": DOCUMENT_ID, "source_locator": LOCATION,
            "source_content_sha256": _sha(source),
        },
        "records": records,
    }
    raw = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    audit = preflight.preflight_archive_batch(packet)
    approved_items = [
        {
            "index": x["index"], "source_key_sha256": x["source_key_sha256"],
            "statement_sha256": x["statement_sha256"],
            "metadata_sha256": x["metadata_sha256"],
        }
        for x in audit["items"] if x.get("status") == "REVIEW_REQUIRED"
    ]
    approval = {
        "schema": stage.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": stage.TARGET, "historical_status": stage.STAGED_STATUS,
        "approval_id": approval_id, "export_sha256": _sha(raw),
        "source_sha256": _sha(source), "items": approved_items,
    }
    sign = lambda manifest: hmac.new(
        SECRET, stage._canonical(manifest), hashlib.sha256,
    ).hexdigest()
    return {
        "export_bytes": raw, "pinned_export_sha256": _sha(raw),
        "source_bytes": source, "pinned_source_sha256": _sha(source),
        "approval": approval, "signature_hex": sign(approval), "approval_key": SECRET,
    }


class Stage9TStagingTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)

    def run_stage(self, payload=None, conn=None):
        args = payload if payload is not None else envelope()
        return stage.stage_approved_export(
            staging_connection=conn if conn is not None else self.conn, **args,
        )

    def test_one_record_staged_with_exact_readback_and_no_production_claims(self):
        out = self.run_stage()
        self.assertEqual(out["status"], "PASS_IN_MEMORY_STAGING_READBACK", out)
        self.assertTrue(out["source_bytes_digest_verified"])
        self.assertTrue(out["export_bytes_digest_verified"])
        self.assertFalse(out["production_writes"])
        self.assertFalse(out["e_lanes_modified"])
        self.assertFalse(out["gravity_rows_modified"])
        self.assertFalse(out["mode_control_modified"])
        self.assertFalse(out["owner_live_authorization_proven"])
        receipt = out["receipt"]
        self.assertFalse(receipt["real_owner_identity_verified"])
        self.assertFalse(receipt["original_attribution_independently_verified"])
        self.assertFalse(receipt["live_storage_written"])
        self.assertEqual(len(receipt["items"]), 1)
        rid = receipt["items"][0]["record_id"]
        row = self.conn.execute(
            "SELECT authority,scope,statement,status,created_at,notes FROM memory_records "
            "WHERE record_id=?", (rid,),
        ).fetchone()
        self.assertEqual(row[0], "NAOMI")
        self.assertEqual(row[1], "MemoryOS")
        self.assertEqual(row[2], "PRIVATE-MEMORY-LINE-001")
        self.assertEqual(row[3], stage.STAGED_STATUS)
        note = json.loads(row[5])["galaxy_archive"]
        self.assertEqual(note["date_confidence"], "UNKNOWN")
        self.assertIsNone(note["original_created_at"])
        self.assertEqual(note["source_content_sha256"], _sha(SOURCE))
        self.assertTrue(note["original_lifecycle_unverified"])
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM galaxy_stage9t_item_receipts",
        ).fetchone()[0], 1)
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM galaxy_stage9t_approvals",
        ).fetchone()[0], 1)
        self.assertFalse(self.conn.in_transaction)

    def test_exact_replay_is_verified_and_zero_write(self):
        payload = envelope()
        initial = self.run_stage(payload)
        before = self.conn.total_changes
        replay = self.run_stage(payload)
        self.assertEqual(replay["status"], "PASS_STAGING_REPLAY_VERIFIED")
        self.assertTrue(replay["idempotent"])
        self.assertEqual(replay["receipt"], initial["receipt"])
        self.assertEqual(replay["writes_performed"], [])
        self.assertEqual(before, self.conn.total_changes)

    def test_new_approval_same_source_gets_existing_verified(self):
        first = self.run_stage(envelope())
        second = self.run_stage(envelope(approval_id="stage9t-fixture-0002"))
        self.assertEqual(second["status"], "PASS_IN_MEMORY_STAGING_READBACK")
        self.assertEqual(second["receipt"]["items"][0]["result"], "EXISTING_VERIFIED")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9t_approvals").fetchone()[0], 2)

    def test_approval_signature_or_key_cannot_be_forged(self):
        for change in ("signature_hex", "approval_key"):
            with self.subTest(change=change):
                payload = envelope()
                payload[change] = "0" * 64 if change == "signature_hex" else b"X" * 40
                result = self.run_stage(payload)
                self.assertEqual(result["status"], "HOLD_APPROVAL_SIGNATURE_INVALID")
        self.assertEqual(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_records'",
        ).fetchone(), None)

    def test_manifest_tampering_or_missing_key_fails_before_schema(self):
        payload = envelope()
        payload["approval"]["authority"] = "OTHER"
        self.assertEqual(
            self.run_stage(payload)["status"], "HOLD_APPROVAL_DOES_NOT_MATCH_EXPORT",
        )
        payload = envelope()
        payload["approval_key"] = b"too-short"
        self.assertEqual(
            self.run_stage(payload)["status"], "HOLD_APPROVAL_KEY_OR_SIGNATURE",
        )
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name='memory_records'",
        ).fetchone())

    def test_independent_pins_cannot_be_self_attested(self):
        export = envelope()
        export["pinned_export_sha256"] = "0" * 64
        self.assertEqual(self.run_stage(export)["status"], "HOLD_EXPORT_DIGEST_MISMATCH")
        original = envelope()
        original["pinned_source_sha256"] = "0" * 64
        self.assertEqual(self.run_stage(original)["status"], "HOLD_ORIGINAL_SOURCE_DIGEST_MISMATCH")
        misleading = envelope()
        obj = json.loads(misleading["export_bytes"])
        obj["archive"]["source_content_sha256"] = "0" * 64
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
        misleading["export_bytes"] = raw
        misleading["pinned_export_sha256"] = _sha(raw)
        self.assertEqual(
            self.run_stage(misleading)["status"], "HOLD_SOURCE_PIN_NOT_IN_MANIFEST",
        )

    def test_actual_statement_must_occur_in_pinned_source_bytes(self):
        payload = envelope([record(statement="INVENTED-STATEMENT-NOT-IN-SOURCE")])
        self.assertEqual(
            self.run_stage(payload)["status"],
            "HOLD_STATEMENT_NOT_FOUND_IN_PINNED_SOURCE",
        )

    def test_duplicate_json_keys_are_rejected_even_when_export_pinned(self):
        payload = envelope()
        raw = payload["export_bytes"].decode()
        bad = raw.replace('"schema":', '"schema":"duplicated","schema":', 1).encode()
        payload["export_bytes"] = bad
        payload["pinned_export_sha256"] = _sha(bad)
        self.assertEqual(self.run_stage(payload)["status"], "HOLD_EXPORT_JSON_INVALID")

    def test_non_memory_e_lane_records_cannot_enter_staging(self):
        for member in (*sorted(preflight.MEMBERS), "VASKON"):
            payload = envelope([record(scope="E_LANE", member=member)])
            self.assertIn(
                self.run_stage(payload)["status"],
                ("HOLD_NON_MEMORY_OR_CONFLICTED_BATCH", "HOLD_ARCHIVE_PREFLIGHT"),
            )
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name='memory_records'",
        ).fetchone())

    def test_batch_is_atomic_when_second_insert_fails(self):
        stage._init_staging(self.conn)
        second = envelope([record(1), record(2)])
        audit = preflight.preflight_archive_batch(json.loads(second["export_bytes"]))
        rid = audit["items"][1]["proposed_record_id"]
        self.conn.execute(
            "CREATE TRIGGER simulate_second_insert BEFORE INSERT ON memory_records "
            "WHEN NEW.record_id=? BEGIN SELECT RAISE(ABORT,'PRIVATE-INJECTED-FAILURE'); END".replace(
                "WHEN NEW.record_id=?", f"WHEN NEW.record_id='{rid}'",
            )
        )
        self.conn.commit()
        result = self.run_stage(second)
        self.assertEqual(result["status"], "HOLD_STAGING_FAILED", result)
        self.assertEqual(result["error_type"], "IntegrityError")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9t_item_receipts").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9t_approvals").fetchone()[0], 0)
        self.assertNotIn("PRIVATE-INJECTED-FAILURE", json.dumps(result))

    def test_reused_approval_id_with_different_export_is_a_hold(self):
        initial = self.run_stage(envelope())
        changed = self.run_stage(
            envelope([record(2)], approval_id="stage9t-fixture-0001"),
        )
        self.assertEqual(initial["status"], "PASS_IN_MEMORY_STAGING_READBACK")
        self.assertEqual(changed["status"], "HOLD_APPROVAL_ID_REUSED_DIFFERENT_CONTENT")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0], 1)

    def test_exact_source_collision_fails_closed(self):
        payload = envelope()
        audit = preflight.preflight_archive_batch(json.loads(payload["export_bytes"]))
        item = audit["items"][0]
        stage._init_staging(self.conn)
        self.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                item["proposed_record_id"], "NAOMI", "NOTE", "MemoryOS",
                "DIFFERENT-STORED-CONTENT", "galaxy-archive-v1:" + item["source_key_sha256"],
                stage.STAGED_STATUS, "1", "2026-09-27", "2026-09-27", None, "{}",
            ),
        )
        self.conn.commit()
        before = self.conn.total_changes
        result = self.run_stage(payload)
        self.assertEqual(result["status"], "HOLD_STAGING_SOURCE_CONFLICT")
        self.assertEqual(self.conn.total_changes, before)

    def test_different_source_using_same_proposed_id_cannot_be_overwritten(self):
        payload = envelope()
        item = preflight.preflight_archive_batch(json.loads(payload["export_bytes"]))["items"][0]
        stage._init_staging(self.conn)
        self.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                item["proposed_record_id"], "NAOMI", "NOTE", "MemoryOS",
                "OTHER", "completely-different-source", stage.STAGED_STATUS, "1",
                "2026-09-27", "2026-09-27", None, "{}",
            ),
        )
        self.conn.commit()
        result = self.run_stage(payload)
        self.assertEqual(result["status"], "HOLD_STAGING_COLLISION")

    def test_replay_fails_when_imported_row_was_modified(self):
        payload = envelope()
        initial = self.run_stage(payload)
        rid = initial["receipt"]["items"][0]["record_id"]
        self.conn.execute(
            "UPDATE memory_records SET statement=? WHERE record_id=?",
            ("SILENTLY-ALTERED", rid),
        )
        self.conn.commit()
        result = self.run_stage(payload)
        self.assertEqual(result["status"], "HOLD_STAGING_REPLAY_DRIFT")
        self.assertFalse(self.conn.in_transaction)

    def test_disk_or_attached_sqlite_is_rejected_with_no_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            dbfile = str(Path(temp) / "live-disk.db")
            disk = sqlite3.connect(dbfile)
            self.addCleanup(disk.close)
            rejected = self.run_stage(conn=disk)
            self.assertEqual(rejected["status"], "HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
            self.assertIsNone(disk.execute(
                "SELECT name FROM sqlite_master WHERE name='memory_records'",
            ).fetchone())
            otherfile = str(Path(temp) / "attached.db")
            self.conn.execute("ATTACH DATABASE ? AS other", (otherfile,))
            rejected = self.run_stage()
            self.assertEqual(rejected["status"], "HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
            self.conn.execute("DETACH DATABASE other")

    def test_source_and_export_caps_fail_closed(self):
        payload = envelope()
        payload["source_bytes"] = b"X" * (stage.MAX_SOURCE_BYTES + 1)
        self.assertEqual(
            self.run_stage(payload)["status"], "HOLD_BYTES_OR_TRUSTED_PINS_MISSING",
        )
        payload = envelope()
        payload["export_bytes"] = b""
        self.assertEqual(
            self.run_stage(payload)["status"], "HOLD_BYTES_OR_TRUSTED_PINS_MISSING",
        )

    def test_receipts_do_not_echo_private_content_or_locations(self):
        out = self.run_stage()
        output = json.dumps(out)
        for private in ("PRIVATE-MEMORY-LINE-001", DOCUMENT_ID, LOCATION, "PRIVATE-REF-001"):
            self.assertNotIn(private, output)
        self.assertIn("source_sha256", output)
        self.assertIn("receipt_sha256", output)


if __name__ == "__main__":
    unittest.main()
