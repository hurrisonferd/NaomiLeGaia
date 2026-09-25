"""Stage 7 data-driven read-only readiness gate; no production activation."""
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
    {"kind": "current", "query": "first established memory fact", "record_id": "MEM-A"},
    {"kind": "current", "query": "second established memory fact", "record_id": "MEM-B"},
    {"kind": "current", "query": "third established memory fact", "record_id": "MEM-A"},
    {"kind": "historical", "query": "historical superseded evidence", "record_id": "MEM-OLD"},
    {"kind": "negative", "query": "pumpkin astronomy collision"},
    {"kind": "negative", "query": "unrelated parquet flooring"},
]


class FakeStore:
    _INITIALIZED = True
    def __init__(self):
        self.read_count = 0
        self.write_count = 0
        self.drift = False

    def search_records(self, query, limit, scope):
        self.read_count += 1
        return {
            "records": [{
                "record_id": "MEM-LEGACY", "statement":
                    "legacy record changed" if self.drift and self.read_count > 1
                    else "legacy record unchanged",
                "scope": "MemoryOS", "source": "owner-approved:legacy",
            }],
            "count": 1, "runtime": "isolated-real-contract-fixture",
            "scope_applied": scope, "query_terms_applied": query.split(),
            "query_filter_active": bool(query),
        }

    def write_record(self, *args, **kwargs):
        self.write_count += 1
        raise AssertionError("Readiness may never write")


CONTROL = {
    "schema": mode.SCHEMA, "effective_mode": mode.HEATDEATH,
    "configured_mode": mode.HEATDEATH, "control_version": 2,
    "bigbang_activation_enabled": False, "reason": "PERSISTED_OWNER_EMERGENCY",
}


def record_item(rid: str, *, historical: bool = False) -> dict:
    return {
        "record": {
            "record_id": rid, "scope": "MemoryOS", "status": "ACTIVE",
            "statement": "Owner-approved source statement for " + rid,
            "source": "verified:test:" + rid,
        },
        "source_provenance": "verified:test:" + rid,
        "governing_state": {
            "record_id": rid,
            "state": "HISTORICAL_SUPERSEDED" if historical else "CURRENT",
            "current_default_eligible": not historical,
        },
        "not_identity_authority": True,
    }


def packet(kind: str, rid: str | None = None) -> dict:
    current = [record_item(rid)] if kind == "current" else []
    history = [record_item(rid, historical=True)] if kind == "historical" else []
    if kind == "current":
        status = "PASS_GALAXY_OPERATIONAL_RETRIEVAL"
    elif kind == "historical":
        status = "HOLD_NO_CURRENT_MATCH"
    else:
        status = "HOLD_NO_CONFIDENT_GALAXY_MATCH"
    return {
        "schema": gateway.GALAXY_SCHEMA, "execution": "READ_ONLY",
        "scope": "MemoryOS", "status": status, "records": current,
        "count": len(current), "historical_context": history,
        "reason": "NO_PRIMARY_CANDIDATE" if kind == "negative" else None,
        "verified_linked_context": [],
        "ranking": gateway.GALAXY_RANKING,
        "galaxy_weighting_applied": kind == "current",
        "candidate_set_preserved": True, "provenance_preserved": True,
        "memory_context_authority": "NONE",
        "automatic_capture": False, "automatic_promotion": False,
        "physical_delete": False, "e_lanes_modified": False,
        "writes_performed": [],
    }


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.rt = FakeStore()
        self.mode_patch = patch.object(mode, "mode_status", return_value=CONTROL)
        self.mode_patch.start()
        self.addCleanup(self.mode_patch.stop)

    def run_sample(self, replacements=None):
        replacements = replacements or {}
        def operational(runtime, query, limit):
            self.assertIs(runtime, self.rt)
            self.assertEqual(limit, 4)
            kind = next(c for c in CASES if c["query"] == query)
            return replacements.get(query, packet(kind["kind"], kind.get("record_id")))
        with patch("galaxy_frontdoor_context.operational", side_effect=operational):
            return readiness.review(self.rt, CASES)

    def test_full_bounded_sample_parity_and_protected_lanes(self):
        result = self.run_sample()
        self.assertEqual(result["status"], "PASS_READ_ONLY_SAMPLE_ONLY", result)
        self.assertTrue(result["legacy_exact_parity"])
        self.assertTrue(result["mode_control_unchanged"])
        self.assertEqual(len(result["results"]), 6)
        self.assertEqual(self.rt.write_count, 0)
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["e_lanes_modified"])
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["mode_control_modified"])

    def test_false_positive_and_missing_primary_fail_quality(self):
        for bad in (
            packet("current", "MEM-A"),
            packet("negative"),
        ):
            with self.subTest(bad=bad["status"]):
                out = self.run_sample({
                    "pumpkin astronomy collision": bad
                    if bad["status"].startswith("PASS") else
                    packet("current", "MEM-A"),
                    "second established memory fact": packet("negative"),
                })
                self.assertEqual(out["status"], "HOLD")
                self.assertFalse(out["release_activated"])

    def test_negative_must_reach_actual_scan_not_a_blocked_preflight(self):
        bad = packet("negative")
        bad["reason"] = "EXTERNAL_DOMAIN_DISAMBIGUATOR"
        out = self.run_sample({"pumpkin astronomy collision": bad})
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["results"][4]["pass"])

    def test_untrusted_mutation_marker_cannot_pass_negative(self):
        bad = packet("negative")
        bad["e_lanes_modified"] = True
        out = self.run_sample({"pumpkin astronomy collision": bad})
        self.assertEqual(out["reason"], "UNVERIFIED_GALAXY_RESPONSE")

    def test_superseded_record_never_counts_as_current(self):
        out = self.run_sample({
            "historical superseded evidence": packet("current", "MEM-OLD"),
        })
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["results"][3]["pass"])

    def test_native_legacy_change_blocks_sample_pass(self):
        self.rt.drift = True
        out = self.run_sample()
        self.assertEqual(out["status"], "HOLD")
        self.assertFalse(out["legacy_exact_parity"])

    def test_bad_or_insufficient_samples_hold_before_reads(self):
        for cases in (
            [], CASES[:-1], CASES[:], [*CASES, CASES[0]],
            [{**CASES[0], "record_id": None}, *CASES[1:]],
        ):
            with self.subTest(case_count=len(cases)):
                if cases == CASES:
                    continue
                out = readiness.review(self.rt, cases)
                self.assertEqual(out["status"], "HOLD")
        self.assertEqual(self.rt.read_count, 0)
        bad_kind = [dict(CASES[0], kind=[]), *CASES[1:]]
        self.assertEqual(readiness.review(self.rt, bad_kind)["status"], "HOLD")

    def test_uninitialized_and_broken_galaxy_fail_closed(self):
        self.rt._INITIALIZED = False
        self.assertEqual(readiness.review(self.rt, CASES)["reason"],
                         "RUNTIME_NOT_INITIALIZED")
        self.rt._INITIALIZED = True
        with patch.object(readiness.importlib, "import_module",
                          side_effect=ImportError("GALAXY missing")):
            out = readiness.review(self.rt, CASES)
        self.assertEqual(out["reason"], "REVIEW_FAILED_CLOSED")
        self.assertFalse(out["release_activated"])

    def test_review_is_exposed_over_authenticated_http_and_mcp(self):
        import gaiaos_app as carrier
        request = carrier.BigbangReadinessRequest(cases=CASES)
        with patch.object(carrier.base, "_authorize") as auth, patch.object(
            readiness, "review", return_value={"status": "test"}
        ) as review:
            http = carrier.gaia_bigbang_readiness_http(
                request, authorization="Bearer test"
            )
            mcp = carrier.gaia_bigbang_readiness(CASES)
        self.assertEqual(http["status"], "test")
        self.assertEqual(mcp["status"], "test")
        auth.assert_called_once_with("Bearer test")
        self.assertEqual(review.call_count, 2)

    def test_release_locked_and_preserve_invariants_still_source_present(self):
        import inspect
        self.assertNotIn("engage_bigbang", inspect.getsource(mode))
        source = (ROOT / "GaiaOS" / "Plans" /
                  "PRESERVE-AND-SIX-E-LANES-PERMANENT-DESIGN-INVARIANT.v1.md"
                  ).read_text()
        self.assertIn("//PW:PRESERVE//", source)
        for name in ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"):
            self.assertTrue((ROOT / "GaiaOS" / "SystemsOS" / "Core" / "FairyOS"
                             / "IDENTITY-DATA" / (name+"-EXPERIENCES.v1.md")
                             ).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
