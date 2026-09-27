"""Source-only historical gravity and mode-compatibility regression tests."""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import galaxy_legacy_gravity as retro


class FakeRuntime:
    _INITIALIZED = True
    GALAXY_SCORE_VERSION = "galaxy.gravity.test.v2"

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE memory_records(record_id TEXT PRIMARY KEY, scope TEXT);
            CREATE TABLE memory_gravity(
                record_id TEXT PRIMARY KEY, gravity_score REAL, score_version TEXT
            );
            INSERT INTO memory_records VALUES ('MEM-A','MemoryOS');
            INSERT INTO memory_records VALUES ('MEM-B','MemoryOS');
            INSERT INTO memory_records VALUES ('MEM-C','MemoryOS');
            INSERT INTO memory_records VALUES ('MEM-D','VERA_E_LANE');
            INSERT INTO memory_gravity VALUES ('MEM-B',0.9,'galaxy.gravity.test.v1');
            INSERT INTO memory_gravity VALUES ('MEM-C',0.7,'galaxy.gravity.test.v2');
        """)
        self.previews = []

    def _db(self):
        return self.conn

    def galaxy_gravity_preview(self, record_id):
        self.previews.append(record_id)
        return {
            "gravity_score": {"MEM-A": 0.45, "MEM-B": 0.65,
                              "MEM-D": 0.55}[record_id],
            "score_version": self.GALAXY_SCORE_VERSION,
        }

    def write_record(self, *args, **kwargs):
        raise AssertionError("read-only gravity audit attempted a memory write")

    def galaxy_calculate_gravity(self, *args, **kwargs):
        raise AssertionError("read-only gravity audit attempted a gravity write")


class HistoricalGravityTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeRuntime()
        self.addCleanup(self.rt.conn.close)

    def test_missing_and_stale_scores_use_preview_not_zero(self):
        missing = retro.resolve_for_retrieval(self.rt, "MEM-A", None)
        self.assertEqual(missing["score"], 0.45)
        self.assertEqual(missing["basis"], "READ_ONLY_PREVIEW")
        self.assertTrue(missing["backfill_required"])
        stale = retro.resolve_for_retrieval(
            self.rt, "MEM-B",
            {"gravity_score": 0.9, "score_version": "galaxy.gravity.test.v1"},
        )
        self.assertEqual(stale["score"], 0.65)
        self.assertEqual(stale["basis"], "STALE_SCORE_PREVIEW")
        self.assertEqual(stale["prior_score_version"], "galaxy.gravity.test.v1")
        current = retro.resolve_for_retrieval(
            self.rt, "MEM-C",
            {"gravity_score": 0.7, "score_version": self.rt.GALAXY_SCORE_VERSION},
        )
        self.assertEqual(current["score"], 0.7)
        self.assertEqual(current["basis"], "STORED")
        self.assertFalse(current["backfill_required"])
        self.assertEqual(self.rt.previews, ["MEM-A", "MEM-B"])

    def test_historical_inventory_is_scoped_paged_and_zero_write(self):
        before = self.rt.conn.total_changes
        page1 = retro.audit_historical_gravity(self.rt, batch_size=2)
        self.assertEqual(page1["status"], "PASS_READ_ONLY_AUDIT", page1)
        self.assertEqual(page1["counts"]["MISSING"], 1)
        self.assertEqual(page1["counts"]["STALE"], 1)
        self.assertEqual(page1["next_cursor"], "MEM-B")
        self.assertTrue(page1["has_more"])
        page2 = retro.audit_historical_gravity(
            self.rt, after_record_id=page1["next_cursor"], batch_size=2,
        )
        self.assertEqual(page2["counts"]["CURRENT"], 1)
        self.assertFalse(page2["has_more"])
        self.assertEqual(page2["inspected"][0]["record_id"], "MEM-C")
        self.assertNotIn("MEM-D", [r["record_id"] for r in page1["inspected"] + page2["inspected"]])
        self.assertEqual(self.rt.conn.total_changes, before)
        self.assertEqual(page1["writes_performed"], [])
        self.assertFalse(page1["mode_control_modified"])
        self.assertFalse(page1["e_lanes_modified"])

    def test_other_existing_scope_requires_explicit_selection(self):
        out = retro.audit_historical_gravity(self.rt, scope="VERA_E_LANE")
        self.assertEqual([x["record_id"] for x in out["inspected"]], ["MEM-D"])
        self.assertEqual(out["inspected"][0]["preview_score"], 0.55)

    def test_invalid_preview_holds_without_zero_imputation(self):
        self.rt.galaxy_gravity_preview = lambda _: {"gravity_score": float("nan"),
                                                   "score_version": self.rt.GALAXY_SCORE_VERSION}
        out = retro.audit_historical_gravity(self.rt, batch_size=1)
        self.assertEqual(out["status"], "PARTIAL_HOLD")
        self.assertEqual(out["counts"]["HOLD"], 1)
        self.assertNotIn("preview_score", out["inspected"][0])
        with self.assertRaises(ValueError):
            retro.resolve_for_retrieval(self.rt, "MEM-A", None)

    def test_uninitialized_and_invalid_input_never_open_database(self):
        self.rt._INITIALIZED = False
        with patch.object(self.rt, "_db", side_effect=AssertionError("opened storage")):
            out = retro.audit_historical_gravity(self.rt)
        self.assertEqual(out["status"], "HOLD_RUNTIME_NOT_INITIALIZED")
        self.rt._INITIALIZED = True
        self.assertEqual(retro.audit_historical_gravity(self.rt, batch_size=0)["status"],
                         "HOLD_BATCH_INVALID")
        self.assertEqual(retro.audit_historical_gravity(self.rt, scope="")["status"],
                         "HOLD_SCOPE_INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
