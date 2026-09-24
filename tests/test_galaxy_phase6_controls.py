"""Offline exact-control tests for the finite GALAXY Phase-6 live campaign."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import memcon_runtime as runtime
import galaxy_phase6 as p6
import galaxy_phase6_controls as ctrl


class Phase6ControlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.originals = (runtime.DB_PATH, runtime.STORAGE_BACKEND, runtime._INITIALIZED)
        runtime.DB_PATH = Path(self.temporary.name) / "phase6-controls.sqlite3"
        runtime.STORAGE_BACKEND = "local_sqlite"
        runtime._INITIALIZED = False
        runtime.initialize()
        runtime.write_record(
            authority="NAOMI", record_type="OBSERVATION", scope="MemoryOS",
            statement="Original violet calibration core observation.",
            source="GALAXY_PHASE6_CONTROL_TEST", approved=True,
            record_id=p6.FIXTURE_RECORD_ID,
        )

    def tearDown(self):
        runtime.DB_PATH, runtime.STORAGE_BACKEND, runtime._INITIALIZED = self.originals
        self.temporary.cleanup()

    def _execute_next(self):
        state = ctrl.inspect(runtime)
        action = state["next_action"]
        return ctrl.execute(
            runtime, action, authority="NAOMI", approved=True,
            confirmation=p6.CONFIRMATIONS[action],
            expected_state=state["current_state"],
            expected_latest_event_id=state["latest_event_id"],
        )

    def test_initial_control_review_is_read_only_and_exact(self):
        before = p6.inspect(runtime)
        state = ctrl.inspect(runtime)
        after = p6.inspect(runtime)
        self.assertEqual(state["execution"], "READ_ONLY")
        self.assertEqual(state["controlled_record_id"], p6.FIXTURE_RECORD_ID)
        self.assertEqual(state["next_action"], "BACKGROUND")
        self.assertEqual(state["completed_steps"], 0)
        self.assertFalse(state["campaign_complete"])
        self.assertEqual(before, after)
        self.assertEqual(state["writes"], 0)

    def test_only_exact_next_action_and_fresh_confirmation_are_accepted(self):
        state = ctrl.inspect(runtime)
        with self.assertRaises(ValueError):
            ctrl.execute(
                runtime, "ARCHIVED", authority="NAOMI", approved=True,
                confirmation=p6.CONFIRMATIONS["ARCHIVED"],
                expected_state="ACTIVE", expected_latest_event_id=None,
            )
        with self.assertRaises(PermissionError):
            ctrl.execute(
                runtime, "BACKGROUND", authority="OTHER", approved=True,
                confirmation=p6.CONFIRMATIONS["BACKGROUND"],
                expected_state="ACTIVE", expected_latest_event_id=None,
            )
        with self.assertRaises(PermissionError):
            ctrl.execute(
                runtime, "BACKGROUND", authority="NAOMI", approved=True,
                confirmation="WRONG",
                expected_state="ACTIVE", expected_latest_event_id=None,
            )
        self.assertEqual(ctrl.inspect(runtime)["completed_steps"], 0)
        self.assertEqual(state["history_signature"], [])

    def test_full_exact_campaign_passes_stepwise_and_finishes_active(self):
        source_before = runtime.get_record(p6.FIXTURE_RECORD_ID)
        retrieval_before = runtime.search_records("violet", scope="MemoryOS")
        expected = [
            ("BACKGROUND", "BACKGROUND"),
            ("ARCHIVED", "ARCHIVED"),
            ("COMPRESSED", "COMPRESSED"),
            ("ROLLBACK", "ARCHIVED"),
            ("REACTIVATE", "ACTIVE"),
        ]
        for index, (action, target) in enumerate(expected, 1):
            state = ctrl.inspect(runtime)
            self.assertEqual(state["next_action"], action)
            receipt = self._execute_next()
            self.assertEqual(receipt["status"], "PASS_READBACK", receipt)
            self.assertTrue(all(receipt["checks"].values()), receipt)
            self.assertEqual(receipt["control_readback"]["current_state"], target)
            self.assertEqual(receipt["control_readback"]["completed_steps"], index)
            self.assertFalse(receipt["physical_delete"])
            self.assertFalse(receipt["production_retrieval_changed"])

        final = ctrl.inspect(runtime)
        self.assertTrue(final["campaign_complete"])
        self.assertIsNone(final["next_action"])
        self.assertEqual(final["current_state"], "ACTIVE")
        self.assertEqual(final["history_signature"], expected)
        self.assertEqual(runtime.get_record(p6.FIXTURE_RECORD_ID), source_before)
        self.assertEqual(runtime.search_records("violet", scope="MemoryOS"), retrieval_before)

    def test_stale_state_or_history_tip_fails_before_extra_event(self):
        first = self._execute_next()
        self.assertEqual(first["status"], "PASS_READBACK")
        current = ctrl.inspect(runtime)
        count = current["completed_steps"]
        with self.assertRaises(ValueError):
            ctrl.execute(
                runtime, "ARCHIVED", authority="NAOMI", approved=True,
                confirmation=p6.CONFIRMATIONS["ARCHIVED"],
                expected_state="ACTIVE",
                expected_latest_event_id=current["latest_event_id"],
            )
        with self.assertRaises(ValueError):
            ctrl.execute(
                runtime, "ARCHIVED", authority="NAOMI", approved=True,
                confirmation=p6.CONFIRMATIONS["ARCHIVED"],
                expected_state="BACKGROUND",
                expected_latest_event_id="LIFE-STALE",
            )
        self.assertEqual(ctrl.inspect(runtime)["completed_steps"], count)

    def test_unexpected_prior_history_holds_entire_control_campaign(self):
        before = p6.inspect(runtime)
        p6.execute(
            runtime, "BACKGROUND", authority="NAOMI", approved=True,
            confirmation=p6.CONFIRMATIONS["BACKGROUND"],
            expected_state=before["current_state"],
            expected_latest_event_id=before["latest_event_id"],
            reason="outside control adapter but valid primitive",
        )
        mid = p6.inspect(runtime)
        p6.execute(
            runtime, "REACTIVATE", authority="NAOMI", approved=True,
            confirmation=p6.CONFIRMATIONS["REACTIVATE"],
            expected_state=mid["current_state"],
            expected_latest_event_id=mid["latest_event_id"],
            reason="unexpected campaign branch",
        )
        state = ctrl.inspect(runtime)
        self.assertIn("PHASE6_CAMPAIGN_HISTORY_NOT_EXPECTED_PREFIX", state["hold_reasons"])
        self.assertIsNone(state["next_action"])

    def test_browser_routes_are_separate_get_preview_and_csrf_post(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        docker = (ROOT / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY api/galaxy_phase6_controls.py ./galaxy_phase6_controls.py", docker)
        self.assertIn('@app.get("/galaxy/lifecycle/phase6-controls"', bridge)
        self.assertIn('@app.get("/galaxy/lifecycle/phase6-controls/confirm/{kind}"', bridge)
        self.assertIn('@app.post("/galaxy/lifecycle/phase6-controls/manifest"', bridge)
        self.assertIn("expected_csrf = _ritual_csrf(browser_request)", bridge)
        self.assertIn("hmac.compare_digest(supplied_csrf, expected_csrf)", bridge)
        segment = bridge.split(
            '@app.get("/galaxy/lifecycle/phase6-controls"', 1
        )[1].split(
            '@app.post("/galaxy/lifecycle/phase6-controls/manifest"', 1
        )[0]
        self.assertNotIn("galaxy_phase6_controls.execute(", segment)
        self.assertIn("galaxy_phase6_controls.execute(", bridge)


if __name__ == "__main__":
    unittest.main(verbosity=2)
