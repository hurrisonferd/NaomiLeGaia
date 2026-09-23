"""Phase 3G read-only audit tests. Fake storage prevents writes and external calls."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_quality as quality
import gaiaos_verification as verifier


class VerifierPhaseStateTests(unittest.TestCase):
    def test_phase3g_and_phase3h_are_authorized_lifecycle_states(self):
        self.assertTrue(verifier._phase3_status_authorized_family(
            "PHASE3G_THREE_LIVE_SLICES_COMPLETE_PHASE3H_READ_ONLY_SOURCE_CI_READY_DEPLOY_PENDING"
        ))
        self.assertTrue(verifier._phase3_status_authorized_family(
            "PHASE3H_CONTAINMENT_SHADOW_LIVE_OBSERVED"
        ))
        self.assertTrue(verifier._phase3_status_authorized_family(
            "PHASE3I_GENERALIZATION_SOURCE_READY"
        ))
        self.assertTrue(verifier._phase3_status_authorized_family(
            "PHASE3J_CONCEPT_BRIDGE_SOURCE_READY"
        ))

    def test_unknown_future_or_unrelated_status_fails_closed(self):
        self.assertFalse(verifier._phase3_status_authorized_family("PHASE4_UNKNOWN"))
        self.assertFalse(verifier._phase3_status_authorized_family("NOT_A_PHASE_STATE"))


class FakeMemory:
    GALAXY_PHASE3C_CALIBRATION_QUERIES = (
        "gravity contextual influence memory retrieval", "other",
        "other", "calibration core revision memory context", "other",
        "satellite calibration core memory context",
    )
    GALAXY_QUERY_STOPWORDS = set()
    GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS = {"planetary", "trajectory", "trajectories", "advertising"}
    GALAXY_QUERY_CONCEPT_ALIASES = {"contextual": "context", "memories": "memory", "retrieval": "memory"}

    def __init__(self):
        self.writes = 0
        self.records = [
            {
                "record_id": "GENERIC", "scope": "MemoryOS",
                "statement": "GALAXY gravity never grants authority.",
                "notes": "calibration revision context",
                "source": "PROTOCOL", "status": "ACTIVE", "created_at": "t1",
                "coverage": 0.8,
            },
            {
                "record_id": "CORE", "scope": "MemoryOS",
                "statement": "The calibration core reports a violet carrier pulse.",
                "notes": "", "source": "OBSERVED", "status": "ACTIVE",
                "created_at": "t2", "coverage": 0.6,
            },
            {
                "record_id": "REV", "scope": "MemoryOS",
                "statement": "An observation revises the calibration core.",
                "notes": "revision", "source": "OBSERVED", "status": "ACTIVE",
                "created_at": "t3", "coverage": 0.8,
            },
        ]

    @staticmethod
    def _galaxy_query_tokens(s):
        import re
        return re.findall(r"[a-z0-9]+", str(s).lower())

    def _galaxy_query_concept(self, token):
        return self.GALAXY_QUERY_CONCEPT_ALIASES.get(token, token)

    def galaxy_phase3_candidate_pool(self, query, *, scope="MemoryOS", limit=10):
        rows = self.records[:limit]
        return {
            "scope_eligible_population_count": len(self.records),
            "candidate_record_ids": [r["record_id"] for r in rows],
            "candidate_count": len(rows),
            "candidates": [
                {"record_id": r["record_id"],
                 "relevance": {
                     "coverage": r["coverage"],
                     "matched_terms": []}}
                for r in rows
            ],
            "ambiguous_record_ids": [],
        }

    def _galaxy_phase3c_score_pool(self, pool, relevance_weight, gravity_weight):
        rows = [
            {"record_id": row["record_id"], "gravity_score": 0.0,
             "weighted_rank": i + 1, "weighted_score": row["relevance"]["coverage"] * 0.8}
            for i, row in enumerate(pool["candidates"])
        ]
        rows.sort(key=lambda row: (-row["weighted_score"], row["weighted_rank"]))
        for index, row in enumerate(rows):
            row["weighted_rank"] = index + 1
        return {"weighted_order": rows, "candidate_set_preserved": True,
                "top_relevance_preserved": True,
                "cross_relevance_tier_inversion_count": 0}

    def search_records(self, query, limit=10, scope=None):
        return {"records": [], "count": 0}

    def galaxy_record(self, record_id):
        row = next((r for r in self.records if r["record_id"] == record_id), None)
        if row is None:
            return None
        relations = (
            [{"edge_id": "EDGE-1", "source_record_id": "REV",
              "target_record_id": "CORE", "relation_type": "REVISES",
              "status": "VERIFIED"}]
            if record_id in ("CORE", "REV") else
            [{"edge_id": "EDGE-NO", "source_record_id": "GENERIC",
              "target_record_id": "CORE", "relation_type": "ASSOCIATED_WITH",
              "status": "PROPOSED"}]
        )
        return {"record": row, "relations": relations}

    def galaxy_governing_state(self, record_id):
        return {"current_default_eligible": True, "state": "CURRENT"}


class QualityReviewTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeMemory()

    def test_metadata_match_is_separate_from_statement_and_scope(self):
        result = quality.review(self.runtime, query_index=3)
        self.assertEqual(result["status"], "OBSERVED_READ_ONLY")
        self.assertEqual(result["topic_anchored_candidate_ids"], ["CORE", "REV"])
        self.assertEqual(result["indirect_or_policy_context_ids"], ["GENERIC"])
        generic = result["records"][0]
        origins = {row["query_term"]: row for row in generic["match_origin"]}
        self.assertFalse(origins["calibration"]["statement"])
        self.assertTrue(origins["calibration"]["notes"])
        self.assertTrue(origins["memory"]["scope_virtual_memory"])
        self.assertFalse(origins["core"]["statement"])
        self.assertEqual(generic["verified_relations"], [])
        self.assertEqual(self.runtime.writes, 0)

    def test_core_not_dropped_by_coverage_shortcut(self):
        result = quality.review(self.runtime, query_index=3)
        core = next(x for x in result["records"] if x["record_id"] == "CORE")
        self.assertEqual(core["query_relevance_coverage"], 0.6)
        self.assertTrue(core["statement_anchor_present"])
        self.assertEqual(core["verified_in_pool_relation_count"], 1)
        self.assertEqual(result["checks"]["cross_relevance_tier_inversions"], 0)
        self.assertFalse(result["provisional_containment_experiment"]["promotion_implemented"])

    def test_missing_record_forces_hold_and_no_write(self):
        self.runtime.galaxy_record = lambda rid: None if rid == "CORE" else FakeMemory.galaxy_record(self.runtime, rid)
        result = quality.review(self.runtime, query_index=3)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["missing_record_ids"], ["CORE"])
        self.assertEqual(self.runtime.writes, 0)

    def test_reject_unapproved_queries_and_large_scans(self):
        with self.assertRaises(ValueError):
            quality.review(self.runtime, query_index=2)
        with self.assertRaises(ValueError):
            quality.review(self.runtime, query_index=3, limit=100)
        self.assertEqual(self.runtime.writes, 0)




class ContainmentShadowTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeMemory()

    def test_focal_core_kept_even_at_point_six_coverage(self):
        result = quality.containment_shadow(self.runtime, query_index=3)
        self.assertEqual(result["status"], "PASS_READ_ONLY_SHADOW")
        self.assertEqual([r["record_id"] for r in result["focal_lane"]], ["REV", "CORE"])
        self.assertEqual(result["linked_context_lane"], [])
        self.assertEqual([r["record_id"] for r in result["other_candidate_audit_lane"]], ["GENERIC"])
        self.assertEqual(result["focal_lane"][1]["original_coverage"], 0.6)
        self.assertEqual(self.runtime.writes, 0)

    def test_unrelated_verified_subgraph_cannot_rescue_noise(self):
        result = quality.containment_shadow(self.runtime, query_index=0)
        self.assertEqual([r["record_id"] for r in result["focal_lane"]], ["GENERIC"])
        self.assertEqual(result["linked_context_lane"], [])
        self.assertEqual(
            {r["record_id"] for r in result["other_candidate_audit_lane"]},
            {"CORE", "REV"},
        )
        self.assertEqual(result["query_concept_alias_groups"]["memory"], ["memory", "retrieval"])
        self.assertEqual(result["focal_lane"][0]["distinct_query_concept_count"], 4)
        self.assertIn("memory", result["focal_lane"][0]["virtual_scope_concepts_without_statement"])

    def test_direct_verified_edge_plus_statement_evidence_admits_linked(self):
        row = {
            "record_id": "LINKED", "scope": "MemoryOS",
            "statement": "Contextual detail about primary evidence.",
            "notes": "", "source": "OBSERVED", "status": "ACTIVE",
            "created_at": "t4", "coverage": 0.6,
        }
        self.runtime.records.append(row)
        original_record = self.runtime.galaxy_record

        def read_record(record_id):
            if record_id == "LINKED":
                return {"record": row, "relations": [{
                    "edge_id": "EDGE-LINKED", "source_record_id": "LINKED",
                    "target_record_id": "GENERIC", "relation_type": "CONTEXT_FOR",
                    "status": "VERIFIED",
                }]}
            return original_record(record_id)

        self.runtime.galaxy_record = read_record
        result = quality.containment_shadow(self.runtime, query_index=0)
        self.assertEqual(result["status"], "PASS_READ_ONLY_SHADOW")
        self.assertEqual([r["record_id"] for r in result["linked_context_lane"]], ["LINKED"])
        self.assertEqual(
            result["linked_context_lane"][0]["focal_link_evidence"][0]["relation_type"],
            "CONTEXT_FOR",
        )

    def test_unverified_relation_never_promotes_linked(self):
        row = {
            "record_id": "LINKED", "scope": "MemoryOS",
            "statement": "Contextual detail about primary evidence.",
            "notes": "", "source": "OBSERVED", "status": "ACTIVE",
            "created_at": "t4", "coverage": 0.6,
        }
        self.runtime.records.append(row)
        original_record = self.runtime.galaxy_record

        def read_record(record_id):
            if record_id == "LINKED":
                return {"record": row, "relations": [{
                    "edge_id": "EDGE-PROPOSED", "source_record_id": "LINKED",
                    "target_record_id": "GENERIC", "relation_type": "CONTEXT_FOR",
                    "status": "PROPOSED",
                }]}
            return original_record(record_id)

        self.runtime.galaxy_record = read_record
        result = quality.containment_shadow(self.runtime, query_index=0)
        self.assertEqual(result["linked_context_lane"], [])
        self.assertIn("LINKED", [
            r["record_id"] for r in result["other_candidate_audit_lane"]
        ])

    def test_no_focal_anchor_holds_instead_of_manufacturing_answer(self):
        self.runtime.records[0]["statement"] = "Generic procedural constraint."
        result = quality.containment_shadow(self.runtime, query_index=0)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["focal_lane"], [])
        self.assertEqual(len(result["other_candidate_audit_lane"]), 3)

    def test_overflow_holds_and_names_record_ids(self):
        for index in range(4):
            self.runtime.records.append({
                "record_id": f"ADDITIONAL-{index}", "scope": "MemoryOS",
                "statement": f"Gravity consideration {index}.",
                "notes": "", "source": "OBSERVED", "status": "ACTIVE",
                "created_at": "t4", "coverage": 0.6,
            })
        original_record = self.runtime.galaxy_record

        def read_record(record_id):
            if record_id.startswith("ADDITIONAL-"):
                row = next(
                    r for r in self.runtime.records if r["record_id"] == record_id
                )
                return {"record": row, "relations": []}
            return original_record(record_id)

        self.runtime.galaxy_record = read_record
        result = quality.containment_shadow(self.runtime, query_index=0)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(len(result["focal_lane"]), 4)
        self.assertEqual(len(result["focal_overflow_record_ids"]), 1)
        self.assertTrue(
            result["checks"]["all_relevance_qualified_candidates_accounted_for"]
        )

    def test_negative_controls_are_read_only_and_strict(self):
        original = self.runtime.galaxy_phase3_candidate_pool

        def gate(query, *, scope="MemoryOS", limit=10):
            if query.startswith(("planetary", "advertising")):
                return {"candidate_count": 0, "candidate_record_ids": []}
            return original(query, scope=scope, limit=limit)

        self.runtime.galaxy_phase3_candidate_pool = gate
        result = quality.containment_shadow(
            self.runtime, query_index=0, negative_controls=True,
        )
        self.assertEqual(result["status"], "PASS_READ_ONLY_SHADOW")
        self.assertEqual(len(result["negative_controls"]), 2)
        self.assertTrue(result["checks"]["negative_controls_zero_candidates"])
        self.assertEqual(self.runtime.writes, 0)

    def test_failed_negative_control_holds_not_ignored(self):
        result = quality.containment_shadow(
            self.runtime, query_index=0, negative_controls=True,
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["checks"]["negative_controls_zero_candidates"])




class GeneralizationSuiteTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeMemory()
        self.cases = (
            {
                "case_id": "CORE_PARAPHRASE",
                "kind": "POSITIVE",
                "difficulty": "MEDIUM",
                "query": "violet carrier pulse",
                "expected_primary_ids": ("CORE",),
                "expected_related_ids": (),
            },
            {
                "case_id": "REVISION_HARD_PARAPHRASE",
                "kind": "POSITIVE",
                "difficulty": "HARD",
                "query": "observation revises calibration",
                "expected_primary_ids": ("REV",),
                "expected_related_ids": ("CORE",),
            },
            {
                "case_id": "PLANETARY_NEGATIVE",
                "kind": "NEGATIVE",
                "difficulty": "CONTROL",
                "query": "planetary gravity trajectories",
                "expected_primary_ids": (),
                "expected_related_ids": (),
            },
        )

    def _install_gate(self, hard_found=True, negative_leak=False):
        def gate(query, *, scope="MemoryOS", limit=10):
            if query == "violet carrier pulse":
                ids = ["CORE"]
            elif query == "observation revises calibration":
                ids = ["REV", "CORE"] if hard_found else ["CORE"]
            elif query == "planetary gravity trajectories":
                ids = ["GENERIC"] if negative_leak else []
            else:
                ids = []
            return {
                "scope_eligible_population_count": len(self.runtime.records),
                "candidate_record_ids": ids,
                "candidate_count": len(ids),
                "candidates": [],
                "ambiguous_record_ids": [],
            }
        self.runtime.galaxy_phase3_candidate_pool = gate

    def test_clean_generalization_suite_passes_read_only(self):
        self._install_gate(hard_found=True, negative_leak=False)
        with patch.object(quality, "PHASE3I_CASES", self.cases):
            result = quality.generalization_suite(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_GENERALIZATION_GATE")
        self.assertTrue(result["checks"]["positive_primary_recall_all"])
        self.assertTrue(result["checks"]["hard_paraphrase_primary_found"])
        self.assertTrue(result["checks"]["negative_controls_zero_candidates"])
        self.assertEqual(self.runtime.writes, 0)

    def test_hard_paraphrase_miss_requires_review(self):
        self._install_gate(hard_found=False, negative_leak=False)
        with patch.object(quality, "PHASE3I_CASES", self.cases):
            result = quality.generalization_suite(self.runtime)
        self.assertEqual(result["status"], "OBSERVED_REVIEW_REQUIRED")
        self.assertFalse(result["checks"]["positive_primary_recall_all"])
        self.assertFalse(result["checks"]["hard_paraphrase_primary_found"])
        hard = next(c for c in result["cases"] if c["case_id"] == "REVISION_HARD_PARAPHRASE")
        self.assertEqual(hard["case_status"], "POSITIVE_PRIMARY_MISS")
        self.assertEqual(self.runtime.writes, 0)

    def test_negative_control_leak_requires_review(self):
        self._install_gate(hard_found=True, negative_leak=True)
        with patch.object(quality, "PHASE3I_CASES", self.cases):
            result = quality.generalization_suite(self.runtime)
        self.assertEqual(result["status"], "OBSERVED_REVIEW_REQUIRED")
        self.assertFalse(result["checks"]["negative_controls_zero_candidates"])
        negative = next(c for c in result["cases"] if c["kind"] == "NEGATIVE")
        self.assertEqual(negative["case_status"], "NEGATIVE_CONTROL_LEAK")

    def test_malformed_candidate_receipt_fails_gate(self):
        def malformed(query, *, scope="MemoryOS", limit=10):
            return {
                "scope_eligible_population_count": 3,
                "candidate_record_ids": ["CORE"],
                "candidate_count": 2,
                "ambiguous_record_ids": [],
            }
        self.runtime.galaxy_phase3_candidate_pool = malformed
        with patch.object(quality, "PHASE3I_CASES", self.cases):
            result = quality.generalization_suite(self.runtime)
        self.assertEqual(result["status"], "OBSERVED_REVIEW_REQUIRED")
        self.assertFalse(result["checks"]["all_receipts_well_formed"])


class ConceptBridgeShadowTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeMemory()
        self.runtime.records[2]["statement"] = (
            "A later controlled observation revises the calibration core toward ultraviolet."
        )
        self.cases = (
            {
                "case_id": "REVISION_HARD_PARAPHRASE",
                "kind": "POSITIVE",
                "difficulty": "HARD",
                "query": "subsequent finding updates the violet calibration result",
                "expected_primary_ids": ("REV",),
                "expected_related_ids": ("CORE",),
            },
            {
                "case_id": "PLANETARY_NEGATIVE",
                "kind": "NEGATIVE",
                "difficulty": "CONTROL",
                "query": "planetary gravity trajectories",
                "expected_primary_ids": (),
                "expected_related_ids": (),
            },
        )

    def test_hard_paraphrase_recovered_statement_first(self):
        with patch.object(quality, "PHASE3I_CASES", self.cases), patch.object(
            quality, "PHASE3J_FIXTURE_IDS", ("GENERIC", "CORE", "REV")
        ):
            result = quality.concept_bridge_shadow(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_CONCEPT_BRIDGE")
        hard = next(c for c in result["cases"] if c["kind"] == "POSITIVE")
        self.assertEqual(hard["bridge_primary_ids"], ["REV"])
        self.assertIn("CORE", hard["verified_linked_context_ids"])
        self.assertTrue(result["checks"]["notes_or_scope_cannot_create_primary"])
        self.assertEqual(self.runtime.writes, 0)

    def test_unexpected_bridge_primary_forces_review(self):
        self.runtime.records[0]["statement"] = (
            "A later finding updates the violet calibration result."
        )
        with patch.object(quality, "PHASE3I_CASES", self.cases), patch.object(
            quality, "PHASE3J_FIXTURE_IDS", ("GENERIC", "CORE", "REV")
        ):
            result = quality.concept_bridge_shadow(self.runtime)
        self.assertEqual(result["status"], "OBSERVED_REVIEW_REQUIRED")
        hard = next(c for c in result["cases"] if c["kind"] == "POSITIVE")
        self.assertIn("GENERIC", hard["unexpected_bridge_primary_ids"])
        self.assertFalse(result["checks"]["no_unexpected_positive_primary"])

    def test_external_negative_stays_zero(self):
        with patch.object(quality, "PHASE3I_CASES", self.cases), patch.object(
            quality, "PHASE3J_FIXTURE_IDS", ("GENERIC", "CORE", "REV")
        ):
            result = quality.concept_bridge_shadow(self.runtime)
        negative = next(c for c in result["cases"] if c["kind"] == "NEGATIVE")
        self.assertEqual(negative["case_status"], "NEGATIVE_CONTROL_PASS")
        self.assertEqual(negative["bridge_primary_ids"], [])
        self.assertEqual(negative["verified_linked_context_ids"], [])

    def test_missing_fixture_fails_closed(self):
        with patch.object(quality, "PHASE3I_CASES", self.cases), patch.object(
            quality, "PHASE3J_FIXTURE_IDS", ("GENERIC", "CORE", "REV", "MISSING")
        ):
            result = quality.concept_bridge_shadow(self.runtime)
        self.assertEqual(result["status"], "OBSERVED_REVIEW_REQUIRED")
        self.assertEqual(result["missing_fixture_ids"], ["MISSING"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
