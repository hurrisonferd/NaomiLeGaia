"""Offline SQLite integration checks for GALAXY Phase 6 source-only lifecycle."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import memcon_runtime as runtime
import galaxy_phase6 as p6


class Phase6LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.originals = (runtime.DB_PATH, runtime.STORAGE_BACKEND,
                          runtime._INITIALIZED)
        runtime.DB_PATH = Path(self.temporary.name) / "phase6-test.sqlite3"
        runtime.STORAGE_BACKEND = "local_sqlite"
        runtime._INITIALIZED = False
        runtime.initialize()
        runtime.write_record(
            authority="NAOMI", record_type="OBSERVATION", scope="MemoryOS",
            statement="Original violet calibration core observation.",
            source="GALAXY_PHASE6_OFFLINE_TEST", approved=True,
            record_id=p6.FIXTURE_RECORD_ID,
        )

    def tearDown(self):
        (runtime.DB_PATH, runtime.STORAGE_BACKEND,
         runtime._INITIALIZED) = self.originals
        self.temporary.cleanup()

    def _run(self, operation, *, reason="Authorized bounded Phase-6 test"):
        before = p6.inspect(runtime)
        return p6.execute(
            runtime, operation, authority="NAOMI", approved=True,
            confirmation=p6.CONFIRMATIONS[operation],
            expected_state=before["current_state"],
            expected_latest_event_id=before["latest_event_id"],
            reason=reason,
        )

    def _counts(self):
        with runtime._db() as conn:
            life = runtime._fetchone_dict(
                conn, "SELECT COUNT(*) AS n FROM memory_lifecycle"
            )["n"]
            events = runtime._fetchone_dict(
                conn, "SELECT COUNT(*) AS n FROM memory_lifecycle_events"
            )["n"]
            receipts = runtime._fetchone_dict(
                conn, "SELECT COUNT(*) AS n FROM runtime_receipts"
            )["n"]
        return life, events, receipts

    def test_read_only_review_creates_no_lifecycle_state(self):
        before = self._counts()
        initial = p6.inspect(runtime)
        self.assertEqual(initial["status"], "PASS_READ_ONLY", initial)
        self.assertEqual(initial["execution"], "READ_ONLY")
        self.assertEqual(initial["current_state"], "ACTIVE")
        self.assertIsNone(initial["latest_event_id"])
        self.assertEqual(initial["event_count"], 0)
        self.assertTrue(initial["eligible_actions"]["BACKGROUND"])
        self.assertFalse(initial["eligible_actions"]["ROLLBACK"])
        self.assertFalse(initial["eligible_actions"]["REACTIVATE"])
        self.assertNotIn("PRUNABLE", initial["eligible_actions"])
        self.assertEqual(before, self._counts())

    def test_full_progression_rollback_reactivation_and_preserved_history(self):
        record = runtime.get_record(p6.FIXTURE_RECORD_ID)
        before_neighbors = runtime.galaxy_record(p6.FIXTURE_RECORD_ID)
        before_retrieval = runtime.search_records("violet", scope="MemoryOS")
        baseline_receipts = self._counts()[2]

        for operation, expected in (
            ("BACKGROUND", "BACKGROUND"),
            ("ARCHIVED", "ARCHIVED"),
            ("COMPRESSED", "COMPRESSED"),
            ("ROLLBACK", "ARCHIVED"),
            ("REACTIVATE", "ACTIVE"),
        ):
            receipt = self._run(operation)
            self.assertEqual(receipt["status"], "PASS_READBACK", receipt)
            self.assertTrue(all(receipt["checks"].values()), receipt)
            self.assertEqual(receipt["after_state"], expected)
            self.assertEqual(receipt["readback"]["record"], record)
            self.assertFalse(receipt["production_retrieval_changed"])
            self.assertFalse(receipt["physical_delete"])

        final = p6.inspect(runtime)
        self.assertEqual(final["event_count"], 5)
        self.assertEqual(
            [e["to_state"] for e in final["events"]],
            ["BACKGROUND", "ARCHIVED", "COMPRESSED", "ARCHIVED", "ACTIVE"],
        )
        self.assertEqual(self._counts(), (1, 5, baseline_receipts + 5))
        self.assertEqual(runtime.get_record(p6.FIXTURE_RECORD_ID), record)
        self.assertEqual(runtime.galaxy_record(p6.FIXTURE_RECORD_ID)["relations"],
                         before_neighbors["relations"])
        self.assertEqual(runtime.search_records("violet", scope="MemoryOS"),
                         before_retrieval)

    def test_first_transition_rolls_back_to_implicit_active(self):
        self._run("BACKGROUND")
        self.assertEqual(self._run("ROLLBACK")["after_state"], "ACTIVE")
        self.assertEqual(self._counts()[1], 2)
        self.assertFalse(p6.inspect(runtime)["eligible_actions"]["REACTIVATE"])

    def test_approval_confirmation_stage_and_stale_tip_are_enforced(self):
        before = p6.inspect(runtime)
        baseline = self._counts()
        cases = (
            dict(operation="BACKGROUND", authority="OTHER", approved=True,
                 confirmation=p6.CONFIRMATIONS["BACKGROUND"]),
            dict(operation="BACKGROUND", authority="NAOMI", approved=False,
                 confirmation=p6.CONFIRMATIONS["BACKGROUND"]),
            dict(operation="BACKGROUND", authority="NAOMI", approved=True,
                 confirmation="UNSIGNED"),
        )
        for kwargs in cases:
            with self.assertRaises(PermissionError):
                p6.execute(runtime, expected_state="ACTIVE",
                           expected_latest_event_id=None, reason="test", **kwargs)
        for operation in ("ARCHIVED", "COMPRESSED", "REACTIVATE", "ROLLBACK",
                          "PRUNABLE"):
            with self.assertRaises((ValueError, PermissionError)):
                p6.execute(
                    runtime, operation, authority="NAOMI", approved=True,
                    confirmation=p6.CONFIRMATIONS.get(operation, ""),
                    expected_state="ACTIVE", expected_latest_event_id=None,
                    reason="test",
                )
        with self.assertRaises(ValueError):
            p6.execute(runtime, "BACKGROUND", authority="NAOMI",
                       approved=True, confirmation=p6.CONFIRMATIONS["BACKGROUND"],
                       expected_state="ACTIVE", expected_latest_event_id=None,
                       reason="")
        with self.assertRaises(ValueError):
            p6.execute(runtime, "BACKGROUND", authority="NAOMI",
                       approved=True, confirmation=p6.CONFIRMATIONS["BACKGROUND"],
                       expected_state="ACTIVE", expected_latest_event_id=None,
                       reason="oversized" * 100)
        with self.assertRaises(ValueError):
            p6.execute(runtime, "BACKGROUND", authority="NAOMI",
                       approved=True, confirmation=p6.CONFIRMATIONS["BACKGROUND"],
                       expected_state="ACTIVE", expected_latest_event_id=None,
                       reason="test", record_id="MEM-NOT-FIXTURE")
        self.assertEqual(self._counts(), baseline)

        self._run("BACKGROUND")
        with self.assertRaises(ValueError):
            p6.execute(runtime, "ARCHIVED", authority="NAOMI", approved=True,
                       confirmation=p6.CONFIRMATIONS["ARCHIVED"],
                       expected_state="ACTIVE", expected_latest_event_id=None,
                       reason="stale review")
        self.assertEqual(self._counts()[1], 1)
        self.assertEqual(before["event_count"], 0)

    def test_untraced_lifecycle_head_and_tampered_chain_hold_closed(self):
        with runtime._db() as conn:
            conn.execute(
                """INSERT INTO memory_lifecycle
                   (record_id,state,changed_at,reason,authority,receipt_id)
                   VALUES (?,?,?,?,?,?)""",
                (p6.FIXTURE_RECORD_ID, "ARCHIVED", runtime._now(),
                 "legacy without receipt history", "NAOMI", "MISSING"),
            )
        self.assertIn("EXISTING_LIFECYCLE_ROW_WITHOUT_EVENT_HISTORY",
                      p6.inspect(runtime)["hold_reasons"])
        self.assertFalse(any(p6.inspect(runtime)["eligible_actions"].values()))
        with runtime._db() as conn:
            conn.execute("DELETE FROM memory_lifecycle WHERE record_id=?",
                         (p6.FIXTURE_RECORD_ID,))
        self._run("BACKGROUND")
        with runtime._db() as conn:
            conn.execute(
                """UPDATE memory_lifecycle_events
                   SET previous_event_id='FORGED'
                   WHERE record_id=?""", (p6.FIXTURE_RECORD_ID,),
            )
        broken = p6.inspect(runtime)
        self.assertEqual(broken["status"], "HOLD")
        self.assertIn("BROKEN_EVENT_HISTORY_CHAIN", broken["hold_reasons"])
        count = self._counts()
        with self.assertRaises(ValueError):
            p6.execute(
                runtime, "ARCHIVED", authority="NAOMI", approved=True,
                confirmation=p6.CONFIRMATIONS["ARCHIVED"],
                expected_state="BACKGROUND",
                expected_latest_event_id="FORGED", reason="must hold",
            )
        self.assertEqual(self._counts(), count)

    def test_missing_nonfixture_or_nonactive_records_hold(self):
        self.assertEqual(p6.inspect(runtime, "MEM-MISSING")["status"], "HOLD")
        with runtime._db() as conn:
            conn.execute("UPDATE memory_records SET status='REVOKED' WHERE record_id=?",
                         (p6.FIXTURE_RECORD_ID,))
        self.assertIn("RECORD_NOT_ACTIVE_MEMORYOS",
                      p6.inspect(runtime)["hold_reasons"])

    def test_no_phase6_mutation_route_or_unsafe_docker_omission(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text()
        docker = (ROOT / "api" / "Dockerfile").read_text()
        self.assertIn("COPY api/galaxy_phase6.py ./galaxy_phase6.py", docker)
        self.assertIn('@app.get("/galaxy/lifecycle/phase6-fixture-review"', bridge)
        self.assertIn("galaxy_phase6.inspect(memcon_runtime)", bridge)
        self.assertNotIn("galaxy_phase6.execute(", bridge)
        self.assertNotIn('@app.post("/galaxy/lifecycle/phase6-', bridge)


if __name__ == "__main__":
    unittest.main(verbosity=2)
