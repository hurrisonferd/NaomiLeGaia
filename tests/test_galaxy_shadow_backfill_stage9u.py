"""Stage 9U isolated shadow-gravity plan, CAS, ledger, replay and rollback."""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import math
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_shadow_backfill_stage9u as u

KEY = b"TEST_ONLY_STAGE9U_SIGNING_KEY_NOT_NAOMI_0123456"
MODEL = "galaxy.gravity.fixture.v2"
IDS = ["MEM-LEGACY-A", "MEM-LEGACY-B", "MEM-LEGACY-C"]


def sign(action, batch_id, plan_sha):
    manifest = {
        "schema": u.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": u.TARGET, "action": action, "batch_id": batch_id,
        "plan_sha256": plan_sha,
    }
    return {
        "approval": manifest,
        "signature_hex": hmac.new(KEY, u._json(manifest), hashlib.sha256).hexdigest(),
        "approval_key": KEY,
    }


def make_db():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE memory_records (
        record_id TEXT PRIMARY KEY, authority TEXT NOT NULL, record_type TEXT NOT NULL,
        scope TEXT NOT NULL, statement TEXT NOT NULL, source TEXT NOT NULL,
        status TEXT NOT NULL, version TEXT NOT NULL,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        supersedes TEXT, notes TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE memory_gravity (
        record_id TEXT PRIMARY KEY, gravity_score REAL NOT NULL,
        score_version TEXT NOT NULL, components_json TEXT NOT NULL,
        reason_json TEXT NOT NULL, calculated_at TEXT NOT NULL,
        previous_score REAL
    );
    CREATE TABLE memory_relations (
        edge_id TEXT PRIMARY KEY, source_record_id TEXT NOT NULL,
        target_record_id TEXT NOT NULL, relation_type TEXT NOT NULL,
        strength REAL NOT NULL, status TEXT NOT NULL,
        evidence_json TEXT NOT NULL, classifier TEXT NOT NULL,
        authority TEXT NOT NULL, created_at TEXT NOT NULL, verified_at TEXT
    );
    CREATE TABLE memory_importance (
        record_id TEXT PRIMARY KEY, gate_units INTEGER NOT NULL,
        model_version TEXT NOT NULL, updated_at TEXT NOT NULL,
        authority TEXT NOT NULL, previous_units INTEGER
    );
    CREATE TABLE memory_lifecycle (
        record_id TEXT PRIMARY KEY, state TEXT NOT NULL, changed_at TEXT NOT NULL,
        reason TEXT NOT NULL, authority TEXT NOT NULL, receipt_id TEXT
    );
    CREATE TABLE memory_lifecycle_events (
        event_id TEXT PRIMARY KEY, record_id TEXT NOT NULL, previous_event_id TEXT,
        from_state TEXT NOT NULL, to_state TEXT NOT NULL,
        action TEXT NOT NULL, changed_at TEXT NOT NULL,
        reason TEXT NOT NULL, authority TEXT NOT NULL, receipt_id TEXT NOT NULL
    );
    """)
    for rid in IDS:
        c.execute(
            "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, "NAOMI", "NOTE", "MemoryOS",
             "PRIVATE-STATEMENT-" + rid, "PRIVATE-ORIGINAL-SOURCE", "ACTIVE", "1",
             "2025-04-01T00:00:00Z", "2025-04-01T00:00:00Z", None, ""),
        )
    c.execute(
        "INSERT INTO memory_gravity VALUES (?,?,?,?,?,?,?)",
        (IDS[1], .36, "galaxy.gravity.fixture.v1", '{"old":1}', '{"old":true}', "2025", None),
    )
    c.execute(
        "INSERT INTO memory_gravity VALUES (?,?,?,?,?,?,?)",
        (IDS[2], .9, MODEL, '{"current":1}', '{"current":true}', "2025", None),
    )
    c.execute(
        "INSERT INTO memory_importance VALUES (?,?,?,?,?,?)",
        (IDS[1], 3, "SEVEN_GATES", "2025", "NAOMI", None),
    )
    c.execute(
        "INSERT INTO memory_relations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("EDGE-001", IDS[0], IDS[1], "REINFORCES", .7, "VERIFIED",
         "{}", "MANUAL", "NAOMI", "2025", "2025"),
    )
    c.commit()
    return c


def preview(rid):
    return {
        "record_id": rid, "gravity_score": .61 if rid == IDS[0] else .79,
        "score_version": MODEL,
        "components": {"fixture": {"normalized": .61, "weight": 1.0}},
        "reason": {"model": "FAKE_FIXTURE_ONLY"},
    }


class Stage9UBackfillTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()
        self.addCleanup(self.conn.close)

    def plan(self, ids=None, cb=preview):
        return u.make_shadow_plan(
            self.conn, record_ids=ids if ids is not None else IDS,
            score_version=MODEL, preview=cb,
        )

    def apply(self, result, *, batch_id="stage9u-fixture-0001", sig=None):
        sig = sig if sig is not None else sign("APPLY", batch_id, result["plan_sha256"])
        return u.apply_shadow_plan(
            self.conn, plan=result["plan"], batch_id=batch_id, **sig,
        )

    def rollback(self, result, *, batch_id="stage9u-fixture-0001"):
        return u.rollback_shadow_batch(
            self.conn, batch_id=batch_id, plan_sha256=result["plan_sha256"],
            **sign("ROLLBACK", batch_id, result["plan_sha256"]),
        )

    def test_plan_is_read_only_and_absent_owner_importance_is_not_zero(self):
        before = self.conn.total_changes
        result = self.plan()
        self.assertEqual(result["status"], "PASS_READ_ONLY_PLAN", result)
        self.assertEqual(result["pending_count"], 2)
        self.assertEqual(result["owner_importance_unset_count"], 2)
        self.assertEqual([x["action"] for x in result["plan"]["entries"]],
                         ["UPSERT_SHADOW", "UPSERT_SHADOW", "SKIP_CURRENT"])
        self.assertEqual(result["plan"]["entries"][0]["owner_importance_status"], "UNSET_NOT_ZERO")
        self.assertEqual(result["plan"]["entries"][1]["owner_importance_status"], "OWNER_SET")
        self.assertEqual(self.conn.total_changes, before)
        self.assertFalse(result["preview_model_bound_to_staging_verified"])
        self.assertFalse(result["production_retrieval_changed"])
        self.assertFalse(result["memory_records_modified"])

    def test_atomic_insert_update_skip_and_signed_receipts(self):
        plan = self.plan()
        before = self.conn.execute("SELECT * FROM memory_records ORDER BY record_id").fetchall()
        result = self.apply(plan)
        self.assertEqual(result["status"], "PASS_IN_MEMORY_BACKFILL_READBACK", result)
        self.assertFalse(result["production_writes"])
        self.assertEqual(
            [x["action"] for x in result["receipt"]["items"]],
            ["INSERTED_SHADOW", "UPDATED_SHADOW", "SKIP_CURRENT"],
        )
        self.assertEqual(self.conn.execute(
            "SELECT gravity_score FROM memory_gravity WHERE record_id=?", (IDS[0],),
        ).fetchone()[0], .61)
        self.assertEqual(self.conn.execute(
            "SELECT gravity_score,previous_score FROM memory_gravity WHERE record_id=?", (IDS[1],),
        ).fetchone(), (.79, .36))
        self.assertEqual(self.conn.execute(
            "SELECT gravity_score FROM memory_gravity WHERE record_id=?", (IDS[2],),
        ).fetchone()[0], .9)
        self.assertEqual(self.conn.execute("SELECT * FROM memory_records ORDER BY record_id").fetchall(), before)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9u_item_ledger").fetchone()[0], 3)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9u_batches").fetchone()[0], 1)
        self.assertFalse(self.conn.in_transaction)

    def test_idempotent_replay_does_not_write(self):
        plan = self.plan()
        initial = self.apply(plan)
        self.assertEqual(initial["status"], "PASS_IN_MEMORY_BACKFILL_READBACK")
        before = self.conn.total_changes
        second = self.apply(plan)
        self.assertEqual(second["status"], "PASS_REPLAY_VERIFIED")
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["receipt"], initial["receipt"])
        self.assertEqual(self.conn.total_changes, before)

    def test_rollback_restores_old_version_exactly_and_deletes_new_row(self):
        old = self.conn.execute("SELECT * FROM memory_gravity WHERE record_id=?", (IDS[1],)).fetchone()
        plan = self.plan()
        applied = self.apply(plan)
        self.assertEqual(applied["status"], "PASS_IN_MEMORY_BACKFILL_READBACK")
        rolled = self.rollback(plan)
        self.assertEqual(rolled["status"], "PASS_IN_MEMORY_ROLLBACK_READBACK", rolled)
        self.assertEqual(rolled["restored_count"], 2)
        self.assertIsNone(self.conn.execute(
            "SELECT * FROM memory_gravity WHERE record_id=?", (IDS[0],),
        ).fetchone())
        self.assertEqual(
            self.conn.execute("SELECT * FROM memory_gravity WHERE record_id=?", (IDS[1],)).fetchone(), old,
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM galaxy_stage9u_item_ledger").fetchone()[0], 3,
        )
        self.assertEqual(self.rollback(plan)["status"], "PASS_ALREADY_ROLLED_BACK")
        self.assertEqual(self.apply(plan)["status"], "HOLD_BATCH_ALREADY_ROLLED_BACK")

    def test_invalid_signature_and_unbound_source_rejected(self):
        plan = self.plan()
        invalid = sign("APPLY", "stage9u-fixture-0001", plan["plan_sha256"])
        invalid["signature_hex"] = "0" * 64
        self.assertEqual(self.apply(plan, sig=invalid)["status"], "HOLD_SIGNED_APPROVAL_REQUIRED")
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name='galaxy_stage9u_batches'",
        ).fetchone())
        invalid = sign("APPLY", "stage9u-fixture-0001", plan["plan_sha256"])
        invalid["approval_key"] = b"too-short"
        self.assertEqual(self.apply(plan, sig=invalid)["status"], "HOLD_SIGNED_APPROVAL_REQUIRED")

    def test_relation_or_importance_or_lifecycle_drift_rejects_entire_batch(self):
        mutations = [
            ("relation", "UPDATE memory_relations SET status='REVOKED' WHERE edge_id='EDGE-001'"),
            ("importance", "UPDATE memory_importance SET gate_units=4 WHERE record_id='MEM-LEGACY-B'"),
            ("lifecycle", "INSERT INTO memory_lifecycle VALUES "
             "('MEM-LEGACY-A','BACKGROUND','2026','test','NAOMI','R-1')"),
            ("record", "UPDATE memory_records SET statement='ALTERED' WHERE record_id='MEM-LEGACY-A'"),
            ("gravity", "UPDATE memory_gravity SET gravity_score=.55 WHERE record_id='MEM-LEGACY-B'"),
        ]
        for label, sql in mutations:
            with self.subTest(label=label):
                c = make_db()
                self.addCleanup(c.close)
                plan = u.make_shadow_plan(c, record_ids=IDS, score_version=MODEL, preview=preview)
                c.execute(sql)
                c.commit()
                out = u.apply_shadow_plan(
                    c, plan=plan["plan"], batch_id="stage9u-drift-fixture-0001",
                    **sign("APPLY", "stage9u-drift-fixture-0001", plan["plan_sha256"]),
                )
                self.assertEqual(out["status"], "HOLD_SOURCE_OR_SCORE_DRIFT", out)
                self.assertIsNone(c.execute(
                    "SELECT * FROM memory_gravity WHERE record_id=?", (IDS[0],),
                ).fetchone())
                self.assertFalse(c.in_transaction)

    def test_failure_on_second_insert_rolls_back_gravity_and_receipts(self):
        c = make_db()
        self.addCleanup(c.close)
        plan = u.make_shadow_plan(c, record_ids=[IDS[0], IDS[1]], score_version=MODEL, preview=preview)
        c.execute("""CREATE TRIGGER reject_updated_score BEFORE UPDATE ON memory_gravity
          BEGIN SELECT RAISE(ABORT,'PRIVATE-TRIGGER-TEXT'); END""")
        c.commit()
        result = u.apply_shadow_plan(
            c, plan=plan["plan"], batch_id="stage9u-trigger-fixture-0001",
            **sign("APPLY", "stage9u-trigger-fixture-0001", plan["plan_sha256"]),
        )
        self.assertEqual(result["status"], "HOLD_BACKFILL_FAILED", result)
        self.assertNotIn("PRIVATE-TRIGGER-TEXT", json.dumps(result))
        self.assertIsNone(c.execute(
            "SELECT * FROM memory_gravity WHERE record_id=?", (IDS[0],),
        ).fetchone())
        self.assertEqual(c.execute(
            "SELECT COUNT(*) FROM galaxy_stage9u_item_ledger",
        ).fetchone()[0], 0)
        self.assertFalse(c.in_transaction)

    def test_rollback_refuses_overwrite_when_score_changes(self):
        plan = self.plan()
        self.apply(plan)
        self.conn.execute(
            "UPDATE memory_gravity SET gravity_score=.11 WHERE record_id=?", (IDS[1],),
        )
        self.conn.commit()
        result = self.rollback(plan)
        self.assertEqual(result["status"], "HOLD_ROLLBACK_SCORE_DRIFT")
        self.assertEqual(self.conn.execute(
            "SELECT gravity_score FROM memory_gravity WHERE record_id=?", (IDS[0],),
        ).fetchone()[0], .61)

    def test_replay_refuses_corrupted_score(self):
        plan = self.plan()
        self.apply(plan)
        self.conn.execute(
            "UPDATE memory_gravity SET gravity_score=.11 WHERE record_id=?", (IDS[0],),
        )
        self.conn.commit()
        self.assertEqual(self.apply(plan)["status"], "HOLD_REPLAY_DRIFT")

    def test_historical_hold_and_six_other_scopes_never_backfilled(self):
        self.conn.execute(
            "UPDATE memory_records SET status='STAGED_HISTORICAL_HOLD' WHERE record_id=?",
            (IDS[0],),
        )
        self.conn.commit()
        self.assertEqual(self.plan()["status"], "HOLD_PLAN_FAILED")
        self.conn.execute(
            "UPDATE memory_records SET status='ACTIVE',scope='VERA_E_LANE' WHERE record_id=?",
            (IDS[0],),
        )
        self.conn.commit()
        self.assertEqual(self.plan()["status"], "HOLD_PLAN_FAILED")

    def test_preview_invalid_nan_model_version_or_callback_write(self):
        bad = [
            lambda rid: {**preview(rid), "gravity_score": float("nan")},
            lambda rid: {**preview(rid), "gravity_score": True},
            lambda rid: {**preview(rid), "score_version": "wrong"},
            lambda rid: {**preview(rid), "reason": {"nan": float("nan")}},
        ]
        for cb in bad:
            with self.subTest(cb=cb):
                out = self.plan([IDS[0]], cb=cb)
                self.assertEqual(out["status"], "HOLD_PREVIEW_INVALID")
        def writing_cb(rid):
            self.conn.execute(
                "UPDATE memory_records SET notes='ILLEGAL' WHERE record_id=?", (rid,),
            )
            return preview(rid)
        out = self.plan([IDS[0]], cb=writing_cb)
        self.assertEqual(out["status"], "HOLD_PREVIEW_CALLBACK_WROTE")
        self.assertEqual(self.conn.execute(
            "SELECT notes FROM memory_records WHERE record_id=?", (IDS[0],),
        ).fetchone()[0], "")

    def test_batch_limit_and_duplicate_ids_hold(self):
        self.assertEqual(self.plan([IDS[0]] * 2)["status"], "HOLD_PLAN_ARGUMENTS")
        self.assertEqual(self.plan(["MEM-" + str(i) for i in range(26)])["status"], "HOLD_PLAN_ARGUMENTS")

    def test_disk_and_attached_sqlite_denied(self):
        with tempfile.TemporaryDirectory() as td:
            disk = sqlite3.connect(str(Path(td) / "disk.db"))
            self.addCleanup(disk.close)
            out = u.make_shadow_plan(disk, record_ids=[IDS[0]], score_version=MODEL, preview=preview)
            self.assertEqual(out["status"], "HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
            self.conn.execute("ATTACH DATABASE ? AS extras", (str(Path(td) / "extra.db"),))
            self.assertEqual(self.plan()["status"], "HOLD_NOT_ISOLATED_IN_MEMORY_SQLITE")
            self.conn.execute("DETACH DATABASE extras")

    def test_plan_hash_and_batch_id_cannot_be_reused_for_other_data(self):
        original = self.plan()
        self.apply(original)
        changed = self.plan([IDS[0]])
        # Source has since been scored CURRENT; different manifest, same batch id.
        self.assertEqual(self.apply(changed)["status"], "HOLD_BATCH_ID_COLLISION")

    def test_receipts_exclude_sensitive_statements(self):
        plan = self.plan()
        applied = self.apply(plan)
        public = json.dumps({k: v for k, v in applied.items() if k != "writes_performed"})
        for phrase in ("PRIVATE-STATEMENT", "PRIVATE-ORIGINAL-SOURCE"):
            self.assertNotIn(phrase, public)
        self.assertFalse(applied["receipt"]["live_turso_written"])
        self.assertFalse(applied["receipt"]["real_owner_identity_verified"])
        self.assertFalse(applied["receipt"]["model_callback_production_proven"])


if __name__ == "__main__":
    unittest.main()
