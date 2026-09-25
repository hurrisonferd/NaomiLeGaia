"""Focused, isolated Stage-7 release-locked read-only sample gate tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

import gaiaos_bigbang_readiness as readiness
import gaiaos_memory_gateway as gateway
import gaiaos_memory_mode as mode


CASES = [
    {"kind": "current", "query": "current approved gravity context", "record_id": "A"},
    {"kind": "current", "query": "current source record context", "record_id": "B"},
    {"kind": "current", "query": "latest approved gravity context", "record_id": "A"},
    {"kind": "historical", "query": "superseded earlier gravity findings", "record_id": "OLD"},
    {"kind": "negative", "query": "unrelated coconut cake frosting"},
    {"kind": "negative", "query": "unrelated watercolor pigment brushes"},
]


def record(rid: str, current: bool = True) -> dict:
    source = "fixture:" + rid
    return {
        "record": {
            "record_id": rid, "statement": "verified fixture " + rid,
            "scope": "MemoryOS", "status": "ACTIVE", "source": source,
        },
        "source_provenance": source,
        "governing_state": {
            "record_id": rid,
            "state": "CURRENT" if current else "HISTORICAL_SUPERSEDED",
            "current_default_eligible": current,
        },
        "not_identity_authority": True,
    }


def packet(kind: str, rid: str | None = None) -> dict:
    if kind == "negative":
        # Real GALAXY _hold() deliberately lacks context arrays.
        return {
            "schema": gateway.GALAXY_SCHEMA, "scope": "MemoryOS",
            "execution": "READ_ONLY",
            "status": "HOLD_NO_CONFIDENT_GALAXY_MATCH",
            "count": 0, "records": [], "memory_context_authority": "NONE",
            "writes_performed": [],
        }
    current = [record(rid)] if kind == "current" else []
    historical = [record(rid, False)] if kind == "historical" else []
    return {
        "schema": gateway.GALAXY_SCHEMA, "scope": "MemoryOS",
        "execution": "READ_ONLY",
        "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL" if current
                  else "HOLD_NO_CURRENT_MATCH",
        "ranking": gateway.GALAXY_RANKING,
        "galaxy_weighting_applied": True, "candidate_set_preserved": True,
        "provenance_preserved": True, "memory_context_authority": "NONE",
        "automatic_capture": False, "automatic_promotion": False,
        "physical_delete": False, "e_lanes_modified": False,
        "writes_performed": [], "records": current, "count": len(current),
        "historical_context": historical, "verified_linked_context": [],
    }


def native() -> dict:
    return {
        "records": [{
            "record_id": "LEGACY", "scope": "MemoryOS",
            "statement": "legacy unchanged", "source": "fixture:legacy",
        }],
        "count": 1, "scope_applied": "MemoryOS",
        "query_terms_applied": ["current"], "query_filter_active": True,
        "runtime": "isolated-fixture",
    }


def control(selected="HEATDEATH") -> dict:
    return {
        "schema": mode.SCHEMA, "effective_mode": selected,
        "configured_mode": selected, "control_version": 7,
        "bigbang_activation_enabled": False,
    }


class FakeStore:
    _INITIALIZED = True
    def write_record(self, *args, **kwargs):
        raise AssertionError("readiness review must never write")


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeStore()
        self.results = {
            case["query"]: packet(case["kind"], case.get("record_id"))
            for case in CASES
        }

    def run_review(self, *, before=None, after=None, initial=None, final=None):
        original = native()
        gateway_result = lambda data: {
            "status": "PASS_HEATDEATH", "retrieval": data,
        }
        reads = [gateway_result(before or original),
                 gateway_result(after or original)]
        def operational(runtime, query, limit):
            self.assertIs(runtime, self.rt)
            self.assertEqual(limit, 4)
            return self.results[query]
        with patch.object(mode, "mode_status", side_effect=[
            initial or control(), final or control()
        ]), patch.object(gateway, "read", side_effect=reads) as legacy, patch(
            "gaiaos_bigbang_readiness.importlib.import_module",
            return_value=type("Reader", (), {"operational": staticmethod(operational)})()
        ) as loader:
            out = readiness.review(self.rt, CASES)
        return out, legacy, loader

    def test_real_shape_negative_hold_and_historical_sample_pass(self):
        out, legacy, loader = self.run_review()
        self.assertEqual(out["status"], "PASS_READ_ONLY_SAMPLE_ONLY", out)
        self.assertEqual(len(out["results"]), 6)
        self.assertTrue(out["legacy_exact_parity"])
        self.assertTrue(out["mode_control_unchanged"])
        self.assertFalse(out["release_activated"])
        self.assertFalse(out["e_lanes_modified"])
        self.assertEqual(out["writes_performed"], [])
        self.assertEqual(legacy.call_count, 2)
        loader.assert_called_once_with("galaxy_frontdoor_context")

    def test_negative_false_positive_blocks_release(self):
        self.results[CASES[4]["query"]] = packet("current", "UNRELATED")
        out, _, _ = self.run_review()
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["results"][4]["pass"])
        self.assertFalse(out["release_activated"])

    def test_historical_record_as_current_blocks_release(self):
        self.results[CASES[3]["query"]] = packet("current", "OLD")
        out, _, _ = self.run_review()
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["results"][3]["pass"])

    def test_source_failure_or_invalid_pass_evidence_holds(self):
        self.results[CASES[0]["query"]] = {
            "schema": gateway.GALAXY_SCHEMA, "scope": "MemoryOS",
            "execution": "READ_ONLY", "status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
            "records": [record("A")], "writes_performed": [],
            "memory_context_authority": "NONE",
        }
        out, _, _ = self.run_review()
        self.assertEqual(out["status"], "HOLD")
        self.assertEqual(out["reason"], "UNVERIFIED_GALAXY_RESPONSE")

    def test_legacy_parity_failure_blocks_release(self):
        altered = native()
        altered["records"] = [{**altered["records"][0], "statement": "changed"}]
        out, _, _ = self.run_review(after=altered)
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["legacy_exact_parity"])

    def test_control_change_blocks_release(self):
        out, _, _ = self.run_review(final={**control(), "control_version": 8})
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["mode_control_unchanged"])

    def test_live_bigbang_is_not_enabled_by_review(self):
        with patch.object(mode, "mode_status", return_value=control("BIGBANG")):
            out = readiness.review(self.rt, CASES)
        self.assertEqual(out["reason"], "REVIEW_REQUIRES_RELEASE_LOCKED_HEATDEATH")
        self.assertFalse(out["release_activated"])

    def test_bad_cases_and_missing_runtime_hold_before_reads(self):
        for invalid in ([], CASES[:5], CASES + [CASES[0]]):
            self.assertEqual(readiness.review(self.rt, invalid)["status"], "HOLD")
        self.rt._INITIALIZED = False
        with patch.object(mode, "mode_status", side_effect=AssertionError("read occurred")):
            out = readiness.review(self.rt, CASES)
        self.assertEqual(out["reason"], "RUNTIME_NOT_INITIALIZED")

    def test_broken_galaxy_import_fails_closed(self):
        with patch.object(mode, "mode_status", return_value=control()), patch.object(
            gateway, "read", return_value={"status":"PASS_HEATDEATH","retrieval":native()}
        ), patch("gaiaos_bigbang_readiness.importlib.import_module",
                 side_effect=ImportError("optional module unavailable")):
            out = readiness.review(self.rt, CASES)
        self.assertEqual(out["reason"], "REVIEW_FAILED_CLOSED")
        self.assertEqual(out["error_type"], "ImportError")
        self.assertFalse(out["release_activated"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
