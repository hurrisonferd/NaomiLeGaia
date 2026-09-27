"""Stage 9S archive preflight: privacy, provenance and zero-write canaries."""
from __future__ import annotations

import copy
import json
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_archive_preflight as archive


def packet(*records):
    return {
        "schema": archive.PACKET_SCHEMA,
        "archive": {
            "source_kind": "CHAT_EXPORT",
            "source_system": "owner-export",
            "document_id": "PRIVATE-DOCUMENT-IDENTIFIER",
            "source_locator": "PRIVATE-ARCHIVE-LOCATION",
            "source_content_sha256": None,
        },
        "records": list(records) if records else [record()],
    }


def record(**overrides):
    item = {
        "source_record_id": "chat-export-event-001",
        "scope": "MemoryOS",
        "member": None,
        "record_type": "NOTE",
        "statement": "PRIVATE-CONTENT-NEVER-EXPOSE",
        "statement_sha256": None,
        "evidence_ref": "PRIVATE-SOURCE-LINE",
        "date_confidence": "UNKNOWN",
        "original_created_at": None,
        "attribution_basis": "UNKNOWN",
    }
    item.update(overrides)
    return item


class ReadOnlyConnection:
    def __init__(self, conn):
        self.conn = conn
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params):
        assert sql.lstrip().upper().startswith("SELECT "), "preflight tried to mutate memory"
        self.reads += 1
        return self.conn.execute(sql, params)


class FakeRuntime:
    _INITIALIZED = True

    def __init__(self, tuple_rows=False):
        self.conn = sqlite3.connect(":memory:")
        if not tuple_rows:
            self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE memory_records (record_id TEXT PRIMARY KEY, scope TEXT,"
            " source TEXT, statement TEXT, notes TEXT)"
        )
        self.readonly = ReadOnlyConnection(self.conn)
        self.calls = 0

    def _db(self):
        self.calls += 1
        return self.readonly

    def close(self):
        self.conn.close()


class Stage9SArchivePreflightTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeRuntime()
        self.addCleanup(self.rt.close)

    def test_memoryos_candidate_is_only_ready_for_review(self):
        before = self.rt.conn.total_changes
        result = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(result["status"], "PASS_PREFLIGHT_REVIEW_REQUIRED")
        self.assertEqual(result["items"][0]["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["store_comparison"], "READ_ONLY")
        self.assertEqual(self.rt.conn.total_changes, before)
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["owner_approved_for_import"])
        self.assertFalse(result["archive_bytes_verified"])
        self.assertFalse(result["provenance_verified"])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["gravity_rows_modified"])
        self.assertFalse(result["mode_control_modified"])

    def test_exactly_six_lanes_remain_separate_and_never_query_memoryos(self):
        entries = [
            record(scope="E_LANE", member=member, attribution_basis="EXPLICIT_SOURCE",
                   source_record_id="shared-source-event")
            for member in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
        ]
        result = archive.preflight_archive_batch(packet(*entries), runtime=self.rt)
        self.assertEqual(result["status"], "PASS_PREFLIGHT_REVIEW_REQUIRED")
        self.assertEqual([x["status"] for x in result["items"]], ["LANE_REVIEW_REQUIRED"] * 6)
        self.assertEqual(len({x["source_key_sha256"] for x in result["items"]}), 6)
        self.assertEqual(self.rt.calls, 0)
        self.assertEqual(
            {x["target"] for x in result["items"]},
            {"E_LANE:" + member for member in archive.MEMBERS},
        )
        self.assertFalse(result["e_lanes_modified"])

    def test_archival_member_label_cannot_fake_individual_authorship(self):
        for basis in ("ARCHIVE_LABEL", "UNKNOWN"):
            result = archive.preflight_archive_batch(
                packet(record(scope="E_LANE", member="VERA", attribution_basis=basis))
            )
            self.assertEqual(result["status"], "PARTIAL_HOLD")
            self.assertEqual(result["items"][0]["status"], "HOLD_UNVERIFIED_MEMBER_ATTRIBUTION")
        bad = archive.preflight_archive_batch(
            packet(record(scope="E_LANE", member="VASKON",
                          attribution_basis="EXPLICIT_SOURCE"))
        )
        self.assertEqual(bad["items"][0]["status"], "HOLD_SCOPE_OR_MEMBER_INVALID")
        wrong = archive.preflight_archive_batch(packet(record(member="ORIN")))
        self.assertEqual(wrong["items"][0]["status"], "HOLD_MEMBER_SCOPE_CONFLICT")

    def test_date_is_explicit_and_unknown_remains_unknown(self):
        for confidence, timestamp in [
            ("UNKNOWN", None),
            ("DAY_ONLY", "2026-09-27"),
            ("EXACT", "2026-09-27T11:00:00-04:00"),
            ("EXACT", "2026-09-27T15:00:00Z"),
        ]:
            res = archive.preflight_archive_batch(
                packet(record(date_confidence=confidence, original_created_at=timestamp))
            )
            self.assertEqual(res["items"][0]["status"], "REVIEW_REQUIRED")
        for confidence, timestamp in [
            ("UNKNOWN", "2026-09-27"),
            ("DAY_ONLY", "2026-02-30"),
            ("EXACT", "2026-09-27T11:00:00"),
            ("EXACT", None),
        ]:
            res = archive.preflight_archive_batch(
                packet(record(date_confidence=confidence, original_created_at=timestamp))
            )
            self.assertEqual(res["items"][0]["status"], "HOLD_DATE_UNVERIFIED")

    def test_exact_duplicates_are_stable_and_idempotent(self):
        r1 = archive.preflight_archive_batch(packet())
        r2 = archive.preflight_archive_batch(packet())
        self.assertEqual(r1["items"][0]["source_key_sha256"], r2["items"][0]["source_key_sha256"])
        self.assertEqual(r1["items"][0]["proposed_record_id"], r2["items"][0]["proposed_record_id"])
        result = archive.preflight_archive_batch(packet(record(), record()))
        self.assertEqual([x["status"] for x in result["items"]],
                         ["REVIEW_REQUIRED", "DUPLICATE_IN_BATCH"])

    def test_conflicting_same_source_or_metadata_is_a_hold(self):
        result = archive.preflight_archive_batch(
            packet(record(), record(statement="A contradicting version"))
        )
        self.assertEqual(result["status"], "PARTIAL_HOLD")
        self.assertEqual([x["status"] for x in result["items"]],
                         ["HOLD_SOURCE_ID_CONFLICT", "HOLD_SOURCE_ID_CONFLICT"])
        changed_date = archive.preflight_archive_batch(
            packet(record(), record(date_confidence="DAY_ONLY",
                                    original_created_at="2026-09-27"))
        )
        self.assertEqual([x["status"] for x in changed_date["items"]],
                         ["HOLD_SOURCE_ID_CONFLICT", "HOLD_SOURCE_ID_CONFLICT"])

    def test_existing_exact_source_requires_provenance_metadata(self):
        prepared = archive.preflight_archive_batch(packet())["items"][0]
        self.rt.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?)",
            ("MEM-ARCH-EXISTING", "MemoryOS",
             "galaxy-archive-v1:" + prepared["source_key_sha256"],
             record()["statement"],
             json.dumps({"galaxy_archive": {
                 "source_key_sha256": prepared["source_key_sha256"],
                 "metadata_sha256": prepared["metadata_sha256"],
             }})),
        )
        before = self.rt.conn.total_changes
        result = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(result["items"][0]["status"], "ALREADY_PRESENT_VERIFIED_METADATA")
        self.assertEqual(result["items"][0]["existing_record_id"], "MEM-ARCH-EXISTING")
        self.assertEqual(result["status"], "PASS_NO_NEW_CANDIDATES")
        self.assertEqual(self.rt.conn.total_changes, before)

    def test_existing_lookalike_without_metadata_holds(self):
        prepared = archive.preflight_archive_batch(packet())["items"][0]
        tag = "galaxy-archive-v1:" + prepared["source_key_sha256"]
        self.rt.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?)",
            ("MEM-OLD", "MemoryOS", tag, record()["statement"], ""),
        )
        result = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(result["items"][0]["status"], "HOLD_EXISTING_SOURCE_CONFLICT")
        self.rt.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?)",
            ("MEM-OLD-TWO", "MemoryOS", tag, record()["statement"], ""),
        )
        second = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(second["items"][0]["status"], "HOLD_DUPLICATE_STORED_SOURCE")

    def test_different_existing_text_or_scope_cannot_be_overwritten(self):
        prepared = archive.preflight_archive_batch(packet())["items"][0]
        self.rt.conn.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?)",
            ("MEM-OTHER", "ANVIL_E_LANE",
             "galaxy-archive-v1:" + prepared["source_key_sha256"], "different", "{}"),
        )
        before = self.rt.conn.total_changes
        res = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(res["items"][0]["status"], "HOLD_EXISTING_SOURCE_CONFLICT")
        self.assertEqual(self.rt.conn.total_changes, before)

    def test_tuple_cursor_rows_are_supported(self):
        other = FakeRuntime(tuple_rows=True)
        self.addCleanup(other.close)
        result = archive.preflight_archive_batch(packet(), runtime=other)
        self.assertEqual(result["items"][0]["status"], "REVIEW_REQUIRED")

    def test_missing_runtime_or_storage_error_fails_closed(self):
        self.rt._INITIALIZED = False
        result = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(result["status"], "HOLD_RUNTIME_NOT_INITIALIZED")
        self.rt._INITIALIZED = True
        self.rt._db = lambda: (_ for _ in ()).throw(RuntimeError("PRIVATE-DB-SECRET"))
        result = archive.preflight_archive_batch(packet(), runtime=self.rt)
        self.assertEqual(result["status"], "HOLD_STORAGE_UNAVAILABLE")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertNotIn("PRIVATE-DB-SECRET", json.dumps(result))

    def test_invalid_untrusted_types_never_raise(self):
        cases = [
            ("archive", "source_kind", []),
            ("archive", "source_content_sha256", []),
            ("record", "date_confidence", []),
            ("record", "attribution_basis", []),
            ("record", "scope", []),
            ("record", "member", []),
            ("record", "statement", {}),
        ]
        for target, field, value in cases:
            with self.subTest(field=field):
                payload = packet()
                if target == "archive":
                    payload["archive"][field] = value
                else:
                    payload["records"][0][field] = value
                result = archive.preflight_archive_batch(payload)
                self.assertTrue(result["status"].startswith("HOLD_")
                                or result["status"] == "PARTIAL_HOLD")

    def test_batch_caps_source_hashes_and_private_output(self):
        too_many = archive.preflight_archive_batch(packet(*[record() for _ in range(51)]))
        self.assertEqual(too_many["status"], "HOLD_BATCH_SIZE")
        huge = packet()
        huge["padding"] = "x" * archive.MAX_PACKET_BYTES
        self.assertEqual(archive.preflight_archive_batch(huge)["status"],
                         "HOLD_PACKET_OVERSIZE")
        bad_hash = archive.preflight_archive_batch(
            packet(record(statement_sha256="0" * 64))
        )
        self.assertEqual(bad_hash["items"][0]["status"], "HOLD_STATEMENT_HASH_MISMATCH")
        normal = archive.preflight_archive_batch(packet())
        output = json.dumps(normal)
        for secret in ("PRIVATE-CONTENT-NEVER-EXPOSE", "PRIVATE-DOCUMENT-IDENTIFIER",
                       "PRIVATE-ARCHIVE-LOCATION", "PRIVATE-SOURCE-LINE"):
            self.assertNotIn(secret, output)


if __name__ == "__main__":
    unittest.main()
