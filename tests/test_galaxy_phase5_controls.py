"""Offline guarded control-exposure tests: no uncontrolled GALAXY Phase-5 writes."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "tests"))

import galaxy_phase5 as p5
import galaxy_phase5_controls as ctrl
from test_galaxy_phase5 import FakeRuntime


class Phase5ControlTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_review_only_is_read_only_and_exact(self):
        result = ctrl.inspect(self.runtime)
        self.assertEqual(result["execution"], "READ_ONLY")
        self.assertTrue(result["eligible_actions"]["PROPOSE"])
        self.assertFalse(result["eligible_actions"]["VERIFY"])
        self.assertFalse(result["eligible_actions"]["REVOKE"])
        self.assertEqual(result["controlled_source_record_ids"], list(p5.FIXTURE_SOURCE_IDS))
        self.assertEqual(self.runtime.writes, 0)

    def test_wrong_confirmation_and_authority_fail_before_write(self):
        for authority, approved, confirmation in [
            ("OTHER", True, ctrl.CONFIRMATIONS["PROPOSE"]),
            ("NAOMI", False, ctrl.CONFIRMATIONS["PROPOSE"]),
            ("NAOMI", True, "WRONG_CONFIRMATION"),
        ]:
            with self.subTest(authority=authority, approved=approved, confirmation=confirmation):
                with self.assertRaises(PermissionError):
                    ctrl.execute(self.runtime, "PROPOSE", authority=authority,
                                 approved=approved, confirmation=confirmation)
                self.assertEqual(self.runtime.writes, 0)

    def test_full_lifecycle_requires_separate_confirmations_and_readback(self):
        source_snapshot = {
            record_id: dict(self.runtime.records[record_id])
            for record_id in p5.FIXTURE_SOURCE_IDS
        }
        proposed = ctrl.execute(
            self.runtime, "PROPOSE", authority="NAOMI", approved=True,
            confirmation=ctrl.CONFIRMATIONS["PROPOSE"],
        )
        self.assertEqual(proposed["status"], "PASS_READBACK", proposed)
        synth_id = proposed["synthesis_record_id"]
        self.assertTrue(all(proposed["checks"].values()))
        self.assertEqual(self.runtime.writes, 1)
        self.assertFalse(proposed["production_retrieval_changed"])
        self.assertEqual(proposed["readback"]["record"]["scope"], p5.SHADOW_SCOPE)
        self.assertNotIn(synth_id, self.runtime.records)

        after_proposal = ctrl.inspect(self.runtime)
        self.assertFalse(after_proposal["eligible_actions"]["PROPOSE"])
        self.assertTrue(after_proposal["eligible_actions"]["VERIFY"])
        with self.assertRaises(ValueError):
            ctrl.execute(self.runtime, "VERIFY", authority="NAOMI", approved=True,
                         confirmation=ctrl.CONFIRMATIONS["VERIFY"],
                         synthesis_record_id="SYNTH-WRONG")
        self.assertEqual(self.runtime.writes, 1)

        verified = ctrl.execute(
            self.runtime, "VERIFY", authority="NAOMI", approved=True,
            confirmation=ctrl.CONFIRMATIONS["VERIFY"],
            synthesis_record_id=synth_id,
        )
        self.assertEqual(verified["status"], "PASS_READBACK", verified)
        self.assertTrue(verified["checks"]["exact_provenance_edges_readback"])
        self.assertTrue(ctrl.inspect(self.runtime)["eligible_actions"]["REVOKE"])
        self.assertEqual(self.runtime.writes, 2)

        revoked = ctrl.execute(
            self.runtime, "REVOKE", authority="NAOMI", approved=True,
            confirmation=ctrl.CONFIRMATIONS["REVOKE"],
            synthesis_record_id=synth_id,
            reason="Controlled revocation receipt",
        )
        self.assertEqual(revoked["status"], "PASS_READBACK", revoked)
        self.assertTrue(all(revoked["checks"].values()))
        self.assertFalse(revoked["physical_delete"])
        self.assertEqual(self.runtime.writes, 3)
        for record_id, before in source_snapshot.items():
            self.assertEqual(self.runtime.records[record_id], before)
        self.assertEqual(self.runtime.syntheses[synth_id]["record"]["status"], "SYNTHESIS_REVOKED")

    def test_cannot_skip_proposal_or_revoke_without_verification(self):
        with self.assertRaises(ValueError):
            ctrl.execute(self.runtime, "VERIFY", authority="NAOMI", approved=True,
                         confirmation=ctrl.CONFIRMATIONS["VERIFY"], synthesis_record_id="SYNTH-1")
        proposed = ctrl.execute(
            self.runtime, "PROPOSE", authority="NAOMI", approved=True,
            confirmation=ctrl.CONFIRMATIONS["PROPOSE"],
        )
        with self.assertRaises(ValueError):
            ctrl.execute(
                self.runtime, "REVOKE", authority="NAOMI", approved=True,
                confirmation=ctrl.CONFIRMATIONS["REVOKE"],
                synthesis_record_id=proposed["synthesis_record_id"],
                reason="premature",
            )
        self.assertEqual(self.runtime.writes, 1)

    def test_control_routes_are_no_js_separate_get_and_post(self):
        bridge = (ROOT / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        docker = (ROOT / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY api/galaxy_phase5_controls.py ./galaxy_phase5_controls.py", docker)
        self.assertIn('@app.get("/galaxy/synthesis/phase5-controls"', bridge)
        self.assertIn('@app.get("/galaxy/synthesis/phase5-controls/confirm/{kind}"', bridge)
        self.assertIn('@app.post("/galaxy/synthesis/phase5-controls/manifest"', bridge)
        self.assertIn('expected_csrf = _ritual_csrf(browser_request)', bridge)
        self.assertIn('hmac.compare_digest(supplied_csrf, expected_csrf)', bridge)
        self.assertIn('galaxy_phase5_controls.execute(', bridge)
        self.assertNotIn('galaxy_phase5_controls.execute(', bridge.split(
            '@app.get("/galaxy/synthesis/phase5-controls"', 1)[1].split(
            '@app.post("/galaxy/synthesis/phase5-controls/manifest"', 1)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
