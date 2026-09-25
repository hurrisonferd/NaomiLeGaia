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

    def test_five_case_partial_pass_does_not_satisfy_six_case_gate(self):
        cases = [c for c in CASES if c["kind"] != "historical"]
        def operational(runtime, query, limit):
            self.assertIs(runtime, self.rt)
            self.assertEqual(limit, 4)
            case = next(c for c in cases if c["query"] == query)
            return packet(case["kind"], case.get("record_id"))
        with patch("galaxy_frontdoor_context.operational", side_effect=operational):
            partial = readiness.review(self.rt, cases, partial=True)
        self.assertEqual(partial["status"], "PASS_PARTIAL_CURRENT_NEGATIVE_ONLY")
        self.assertFalse(partial["historical_coverage"])
        self.assertTrue(partial["legacy_exact_parity"])
        self.assertEqual([r["kind"] for r in partial["results"]],
                         ["current", "current", "current", "negative", "negative"])
        self.assertFalse(partial["release_activated"])
        self.assertEqual(partial["writes_performed"], [])
        self.assertEqual(self.rt.write_count, 0)
        full = readiness.review(self.rt, cases)
        self.assertEqual(full["status"], "HOLD")
        self.assertEqual(full["reason"], "SIX_TO_TWELVE_CASES_REQUIRED")

    def test_partial_fails_closed_on_negative_match_or_history(self):
        cases = [c for c in CASES if c["kind"] != "historical"]
        with self.subTest("historical forbidden"):
            invalid = readiness.review(self.rt, CASES, partial=True)
            self.assertEqual(invalid["status"], "HOLD")
        with self.subTest("negative matched"):
            def operational(runtime, query, limit):
                case = next(c for c in cases if c["query"] == query)
                if case["kind"] == "negative":
                    return packet("current", "MEM-A")
                return packet(case["kind"], case.get("record_id"))
            with patch("galaxy_frontdoor_context.operational", side_effect=operational):
                outcome = readiness.review(self.rt, cases, partial=True)
            self.assertEqual(outcome["status"], "HOLD")
            self.assertFalse(outcome["results"][3]["pass"])
            self.assertFalse(outcome["release_activated"])

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


class Stage9TechnicalPreflight(unittest.TestCase):
    """Never inspect production records or depend on an actual remote database."""

    def setUp(self):
        import sqlite3
        import tempfile
        self.temp = tempfile.TemporaryDirectory(prefix="stage9-private-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "test.sqlite")
        with sqlite3.connect(self.path) as db:
            db.executescript("""
                CREATE TABLE memory_records (
                    record_id TEXT, authority TEXT, scope TEXT, statement TEXT,
                    source TEXT, status TEXT, created_at TEXT
                );
                CREATE TABLE memory_relations (
                    source_record_id TEXT, target_record_id TEXT,
                    authority TEXT, status TEXT, relation_type TEXT,
                    verified_at TEXT
                );
            """)
        class FakeRuntime:
            _INITIALIZED = True
            storage_status = staticmethod(lambda: {
                "backend": "turso_libsql", "remote_configured": True,
            })
            _fetchall_dicts = staticmethod(
                lambda c, q: [dict(r) for r in c.execute(q).fetchall()]
            )
        self.fake = FakeRuntime()
        def db_open():
            c = sqlite3.connect(self.path)
            c.row_factory = sqlite3.Row
            return c
        self.fake._db = db_open
        import memcon_runtime
        self.fake._galaxy_query_tokens = staticmethod(
            memcon_runtime._galaxy_query_tokens
        )
        self.fake._galaxy_query_concept = memcon_runtime._galaxy_query_concept
        def get_record(record_id):
            with db_open() as conn:
                row = conn.execute(
                    "SELECT * FROM memory_records WHERE record_id=?",
                    (record_id,),
                ).fetchone()
            return dict(row) if row is not None else None
        self.fake.get_record = get_record
        self.mode_patch = patch.object(mode, "mode_status", return_value={
            "schema": mode.SCHEMA, "effective_mode": "HEATDEATH",
            "bigbang_activation_enabled": False,
        })
        self.mode_patch.start()
        self.addCleanup(self.mode_patch.stop)

    def _insert(self, rid, statement, source="naomi-owner-save", status="ACTIVE"):
        import sqlite3
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO memory_records VALUES (?,?,?,?,?,?,?)",
                (rid, "NAOMI", "MemoryOS", statement, source, status, rid),
            )

    def _supersedes(self, old, new, relation="SUPERSEDES", status="VERIFIED"):
        import sqlite3
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO memory_relations VALUES (?,?,?,?,?,?)",
                (new, old, "NAOMI", status, relation, "2026-09-24"),
            )

    def _seed(self):
        self._insert("current-a", "Power Word preserve safeguards all memory")
        self._insert("current-b", "six independent E-LANES keep their identity")
        self._insert("history", "HEATDEATH v1.2 historical rollback guard")
        self._insert("successor", "HEATDEATH v2.0 replaces old rollback guard")
        self._supersedes("history", "successor")

    def test_six_approved_cases_are_prepared_without_exposing_records(self):
        self._seed()
        prep = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(prep["preview"]["status"], "PREPARED_UNTESTED")
        self.assertEqual(len(prep["cases"]), 6)
        self.assertEqual([c["kind"] for c in prep["cases"]],
                         ["current", "current", "current", "historical",
                          "negative", "negative"])
        self.assertNotEqual(prep["cases"][0]["record_id"],
                            prep["cases"][1]["record_id"])
        public = str(prep["preview"])
        for secret in ("history", "successor", "current-a", "current-b",
                       "v1.2", "v2.0", "naomi-owner-save"):
            self.assertNotIn(secret, public)
        self.assertEqual(prep["preview"]["writes_performed"], [])
        self.assertFalse(prep["preview"]["review_executed"])

    def test_distinct_same_topic_records_use_distinct_queries(self):
        self._insert("galaxy-a", "GALAXY uses query relevance first")
        self._insert("galaxy-b", "GALAXY gravity never grants authority")
        self._insert("galaxy-old", "GALAXY v1.2 historical admission")
        self._insert("galaxy-new", "GALAXY v2.0 supersedes historical admission")
        self._supersedes("galaxy-old", "galaxy-new")
        result = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(result["preview"]["status"], "PREPARED_UNTESTED")
        self.assertEqual(result["preview"]["technical_topics"], ["GALAXY"])
        self.assertEqual(result["preview"]["distinct_current_records_capped_at_two"], 2)
        cases = result["cases"]
        self.assertEqual(len(cases), 6)
        self.assertEqual(len({x["record_id"] for x in cases[:3]}), 2)
        self.assertEqual(len({x["query"] for x in cases[:3]}), 3)
        self.assertEqual(cases[3]["record_id"], "galaxy-old")
        self.assertNotIn("galaxy-old", str(result["preview"]))

    def test_only_one_same_topic_record_keeps_hold(self):
        self._insert("galaxy-only", "GALAXY preserves owner authority")
        result = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(result["preview"]["status"], "HOLD")
        self.assertEqual(result["preview"]["distinct_current_records_capped_at_two"], 1)
        self.assertEqual(result["preview"]["reason"],
                         "TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN")
        self.assertEqual(result["cases"], [])

    def test_partial_prepared_when_real_history_unavailable(self):
        self._insert("galaxy-a", "GALAXY relevance stays query-first")
        self._insert("galaxy-b", "GALAXY gravity never grants authority")
        prep = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(prep["preview"]["status"], "HOLD")
        self.assertEqual(prep["preview"]["reason"],
                         "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES")
        self.assertTrue(prep["preview"]["partial_five_case_ready"])
        self.assertEqual(prep["cases"], [])
        self.assertEqual(len(prep["partial_cases"]), 5)
        self.assertEqual([c["kind"] for c in prep["partial_cases"]],
                         ["current", "current", "current", "negative", "negative"])
        with patch.object(readiness, "review", side_effect=AssertionError(
            "Full Stage 7 review must not run without real history"
        )):
            full = readiness.technical_sample_review(self.fake)
        self.assertEqual(full["status"], "HOLD")
        self.assertFalse(full["review_executed"])

    def test_read_only_target_query_audit_reports_only_numeric_evidence(self):
        self._insert("galaxy-a", "GALAXY relevance stays query-first")
        self._insert("galaxy-b", "GALAXY gravity never grants authority")
        prep = readiness.prepare_technical_cases(self.fake)
        audit = readiness._target_query_audit(self.fake, prep["partial_cases"])
        self.assertEqual(audit["status"], "READ_ONLY_TARGET_QUERY_AUDIT")
        self.assertEqual(len(audit["measurements"]), 3)
        for row in audit["measurements"]:
            self.assertIs(type(row["target_meets_statement_admission"]), bool)
            self.assertGreaterEqual(row["matched_concept_count"], 0)
            self.assertGreaterEqual(row["query_concept_count"], 0)
            self.assertEqual(row["minimum_matching_concepts"], 2)
            self.assertGreater(row["minimum_coverage"], 0.66)
        serialized = str(audit)
        for sensitive in ("galaxy-a", "galaxy-b",
                          "relevance stays query-first",
                          "gravity never grants authority",
                          "naomi-owner-save"):
            self.assertNotIn(sensitive, serialized)
        self.assertEqual(prep["preview"]["status"], "HOLD")

    def test_query_audit_fails_closed_on_unapproved_target(self):
        self._insert("galaxy-fixture", "GALAXY fixture-only example",
                     source="synthetic-calibration-fixture")
        case = {"kind": "current",
                "query": "GALAXY fixture-only example",
                "record_id": "galaxy-fixture"}
        audit = readiness._target_query_audit(self.fake, [case])
        self.assertEqual(audit["status"], "HOLD_TARGET_RECORD_UNVERIFIED")
        self.assertEqual(audit["measurements"], [])
        self.assertNotIn("galaxy-fixture", str(audit))

    def test_partial_review_redacts_ids_and_cannot_be_full_pass(self):
        self._insert("galaxy-a", "GALAXY relevance stays query-first")
        self._insert("galaxy-b", "GALAXY gravity never grants authority")
        secret = "MEM-SENSITIVE-NEVER-EXPOSE"
        with patch.object(readiness, "review", return_value={
            "status": "PASS_PARTIAL_CURRENT_NEGATIVE_ONLY",
            "reason": "PARTIAL_FIVE_CASE_PARITY_NO_HISTORICAL",
            "legacy_exact_parity": True,
            "results": [{"case": 0, "kind": "current", "pass": True,
                         "observed_status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                         "current_ids": [secret], "historical_ids": [secret]}],
        }) as actual:
            outcome = readiness.technical_partial_sample_review(self.fake)
        actual.assert_called_once()
        self.assertTrue(actual.call_args.kwargs["partial"])
        self.assertEqual(outcome["status"], "HOLD")
        self.assertEqual(outcome["full_readiness_status"],
                         "HOLD_MISSING_HISTORICAL_PROOF")
        self.assertEqual(outcome["partial_review_status"],
                         "PASS_PARTIAL_CURRENT_NEGATIVE_ONLY")
        self.assertFalse(outcome["historical_coverage"])
        self.assertNotIn(secret, str(outcome))
        self.assertNotIn("galaxy-a", str(outcome))
        self.assertNotIn("galaxy-b", str(outcome))
        self.assertEqual(outcome["writes_performed"], [])
        self.assertFalse(outcome["release_activated"])

    def test_mobile_console_is_static_and_partial_post_needs_owner_bearer(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        secret = "isolated-stage9c-test-key"
        client = TestClient(carrier.app)
        self.addCleanup(client.close)
        with patch.object(carrier.base, "API_KEY", secret), patch.object(
            readiness, "technical_partial_sample_review",
            side_effect=AssertionError("No unauthorized memory access")
        ):
            page = client.get("/gaiaos/memory/technical-partial-console")
            self.assertEqual(page.status_code, 200)
            self.assertIn("default-src 'none'",
                          page.headers["content-security-policy"])
            self.assertEqual(page.headers["cache-control"], "no-store")
            self.assertIn('type="password"', page.text)
            self.assertIn("target_query_audit:result.target_query_audit", page.text)
            self.assertIn('credentials:"same-origin"', page.text)
            self.assertIn('redirect:"error"', page.text)
            self.assertNotIn(secret, page.text)
            self.assertNotIn("__NONCE__", page.text)
            denied = client.post("/gaiaos/memory/technical-partial-review")
            self.assertEqual(denied.status_code, 401)
            self.assertEqual(denied.json()["detail"], "OWNER_AUTH_HEADER_NOT_RECEIVED")
            malformed = client.post(
                "/gaiaos/memory/technical-partial-review",
                headers={"Authorization": "Basic invalid"},
            )
            self.assertEqual(malformed.status_code, 401)
            self.assertEqual(malformed.json()["detail"],
                             "OWNER_AUTH_BEARER_SCHEME_MISSING")
            mismatch = client.post(
                "/gaiaos/memory/technical-partial-review",
                headers={"Authorization": "Bearer wrong-test-value"},
            )
            self.assertEqual(mismatch.status_code, 401)
            self.assertEqual(mismatch.json()["detail"],
                             "OWNER_AUTH_HEADER_RECEIVED_BUT_KEY_MISMATCH")
            self.assertNotIn(secret, str(mismatch.json()))
            client.cookies.set(carrier.base.SESSION_COOKIE,
                               carrier.base._session_token())
            denied = client.post("/gaiaos/memory/technical-partial-review")
            self.assertEqual(denied.status_code, 401)
            self.assertEqual(denied.json()["detail"], "OWNER_AUTH_HEADER_NOT_RECEIVED")
        with patch.object(carrier.base, "API_KEY", None):
            unavailable = client.post("/gaiaos/memory/technical-partial-review")
            self.assertEqual(unavailable.status_code, 503)
        with patch.object(carrier.base, "API_KEY", secret), patch.object(
            readiness, "technical_partial_sample_review",
            return_value={"status": "HOLD", "writes_performed": []}
        ) as allowed:
            granted = client.post(
                "/gaiaos/memory/technical-partial-review",
                headers={"Authorization": "Bearer "+secret}
            )
            self.assertEqual(granted.status_code, 200)
            allowed.assert_called_once()

    def test_revises_is_not_supersedes(self):
        self._seed()
        import sqlite3
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE memory_relations SET relation_type='REVISES'")
        result = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(result["preview"]["status"], "HOLD")
        self.assertEqual(result["preview"]["reason"],
                         "NO_VERIFIED_DISTINCT_TECHNICAL_SUPERSEDES")
        self.assertEqual(result["cases"], [])

    def test_fixture_sources_cannot_become_real_technical_cases(self):
        self._insert("fixture-a", "Power Word preserve safeguards memory",
                     source="GALAXY_CANARY_FIXTURE")
        self._insert("real-b", "six independent E-LANES keep identity")
        result = readiness.prepare_technical_cases(self.fake)
        self.assertEqual(result["preview"]["reason"],
                         "TWO_DISTINCT_CURRENT_TECHNICAL_RECORDS_NOT_PROVEN")

    def test_no_review_is_run_when_historical_evidence_missing(self):
        self._insert("current-a", "Power Word preserve safeguards memory")
        self._insert("current-b", "six independent E-LANES keep identity")
        with patch.object(readiness, "review",
                          side_effect=AssertionError("unapproved review")):
            result = readiness.technical_sample_review(self.fake)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["review_executed"])

    def test_actual_reviewer_output_is_redacted_for_browser(self):
        self._seed()
        secret = "MEM-DO-NOT-REVEAL"
        with patch.object(readiness, "review", return_value={
            "status": "PASS_READ_ONLY_SAMPLE_ONLY",
            "reason": "SAMPLE_AND_LEGACY_PARITY",
            "legacy_exact_parity": True,
            "results": [{"case": 0, "kind": "current", "pass": True,
                         "observed_status": "PASS_GALAXY_OPERATIONAL_RETRIEVAL",
                         "current_ids": [secret], "historical_ids": [secret]}],
        }):
            result = readiness.technical_sample_review(self.fake)
        self.assertEqual(result["status"], "PASS_READ_ONLY_SAMPLE_ONLY")
        self.assertTrue(result["legacy_exact_parity"])
        self.assertNotIn(secret, str(result))
        self.assertNotIn("HEATDEATH v1.2 historical rollback guard", str(result))
        self.assertEqual(result["writes_performed"], [])


    def test_owner_api_is_required_even_if_carrier_has_no_key(self):
        from fastapi.testclient import TestClient
        import gaiaos_app as carrier
        with TestClient(carrier.app) as client:
            with patch.object(carrier.base, "API_KEY", None):
                r = client.post("/gaiaos/memory/technical-review")
            self.assertEqual(r.status_code, 503)
            with patch.object(carrier.base, "API_KEY", "ci-only-not-real"):
                r = client.post("/gaiaos/memory/technical-review")
            self.assertEqual(r.status_code, 401)
