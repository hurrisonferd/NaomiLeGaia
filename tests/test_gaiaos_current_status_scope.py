"""Reconcile scoped GALAXY source status without implying live deployment."""
import json
import unittest
from pathlib import Path

CURRENT = Path(__file__).resolve().parents[1] / "GaiaOS" / "CURRENT.json"

class CurrentStatusScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.summary = cls.status["proof_ceiling"]

    def test_later_source_does_not_report_stage9f_predeploy_as_current(self):
        self.assertIn("Stage 9Q model-free owner-label baseline", self.summary)
        self.assertNotIn("Current main source is pre-deploy ready for Stage 9F", self.summary)
        self.assertIn("9Q's source merge and CI do not prove a live Stage 9Q", self.summary)

    def test_historical_live_evidence_is_scoped(self):
        self.assertIn("2026-09-25 owner-relayed Stage 9N", self.summary)
        self.assertIn("owner-relayed Stage 9P live observation", self.summary)
        self.assertIn("do not establish present Turso health", self.summary)

    def test_evidence_hold_cannot_erase_independent_success(self):
        self.assertIn("nested diagnostic HOLD does not invalidate", self.summary)
        self.assertIn("historical evidence remained HOLD", self.summary)

    def test_release_and_safeguard_wording_unchanged(self):
        self.assertIn("BIGBANG is locked", self.summary)
        self.assertIn("//PW:PRESERVE// plus all six separate E-LANES", self.summary)
        self.assertFalse(
            self.status.get("galaxy", {}).get("production_weighted_retrieval_enabled", False)
        )

if __name__ == "__main__":
    unittest.main()
