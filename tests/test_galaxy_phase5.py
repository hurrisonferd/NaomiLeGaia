"""Offline safety tests for GALAXY Phase 5 provenance-backed synthesis review."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_phase5 as p5


class FakeRuntime:
    def __init__(self):
        a, b = p5.FIXTURE_SOURCE_IDS
        self.records = {
            a: {
                "record_id": a,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Later calibration observation revises the core.",
            },
            b: {
                "record_id": b,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Original calibration core observation.",
            },
            "CROSS": {
                "record_id": "CROSS",
                "scope": "OtherScope",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Other-scope record.",
            },
            "ISOLATED": {
                "record_id": "ISOLATED",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "OBSERVATION",
                "statement": "Unrelated isolated record.",
            },
            "SYNTH": {
                "record_id": "SYNTH",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "record_type": "SYNTHESIS",
                "statement": "Existing synthesis.",
            },
        }
        self.edges = {
            "EDGE-REVISES": {
                "edge_id": "EDGE-REVISES",
                "source_record_id": a,
                "target_record_id": b,
                "relation_type": "REVISES",
                "strength": 0.9,
                "status": "VERIFIED",
                "authority": "NAOMI",
                "created_at": "2026-09-20T00:00:00+00:00",
                "verified_at": "2026-09-20T00:01:00+00:00",
            },
            "EDGE-OLD-SUPERSEDES": {
                "edge_id": "EDGE-OLD-SUPERSEDES",
                "source_record_id": a,
                "target_record_id": b,
                "relation_type": "SUPERSEDES",
                "strength": 1.0,
                "status": "REVOKED",
                "authority": "NAOMI",
                "created_at": "2026-09-23T00:00:00+00:00",
                "verified_at": "2026-09-23T00:01:00+00:00",
            },
        }
        self.writes = 0
        self.syntheses = {}
        self.synthesis_seq = 0

    def galaxy_record(self, record_id):
        record = self.records.get(record_id)
        if not record:
            return None
        relations = [
            dict(edge) for edge in self.edges.values()
            if edge["source_record_id"] == record_id
            or edge["target_record_id"] == record_id
        ]
        return {"record": dict(record), "relations": relations}

    def galaxy_governing_state(self, record_id):
        record = self.records[record_id]
        incoming = [
            edge for edge in self.edges.values()
            if edge["target_record_id"] == record_id
            and edge["status"] == "VERIFIED"
            and edge["relation_type"] in {"REVISES", "SUPERSEDES"}
        ]
        supersedes = [e for e in incoming if e["relation_type"] == "SUPERSEDES"]
        revises = [e for e in incoming if e["relation_type"] == "REVISES"]
        if supersedes:
            state = "HISTORICAL_SUPERSEDED"
            eligible = False
        elif revises:
            state = "CURRENT_REVISED_CONTEXT"
            eligible = True
        else:
            state = "CURRENT"
            eligible = True
        return {
            "record_id": record_id,
            "state": state,
            "record_status": record["status"],
            "current_default_eligible": eligible,
            "historical_retrieval_eligible": True,
        }


    def galaxy_find_synthesis(self, source_record_ids):
        wanted = list(source_record_ids)
        for detail in reversed(list(self.syntheses.values())):
            if (
                detail["synthesis"]["source_record_ids"] == wanted
                and detail["record"]["status"] != "SYNTHESIS_REVOKED"
            ):
                return self.galaxy_synthesis(detail["record"]["record_id"])
        return None

    def galaxy_synthesis(self, synthesis_record_id):
        detail = self.syntheses.get(synthesis_record_id)
        if detail is None:
            return None
        return {
            "record": dict(detail["record"]),
            "synthesis": dict(detail["synthesis"]),
            "derived_from_edges": [dict(edge) for edge in detail["derived_from_edges"]],
            "source_records": [
                dict(self.records[source_id])
                for source_id in detail["synthesis"]["source_record_ids"]
            ],
        }

    def galaxy_propose_synthesis(
        self,
        *,
        source_record_ids,
        statement,
        method,
        confidence,
        authority,
        approved,
    ):
        if authority != "NAOMI" or not approved:
            raise PermissionError
        existing = self.galaxy_find_synthesis(source_record_ids)
        if existing is not None:
            return {
                "status": "EXISTING",
                "synthesis": existing,
                "memoryos_retrieval_changed": False,
                "production_retrieval_changed": False,
            }
        self.synthesis_seq += 1
        synthesis_record_id = f"SYNTH-{self.synthesis_seq}"
        record = {
            "record_id": synthesis_record_id,
            "scope": p5.SHADOW_SCOPE,
            "status": "SYNTHESIS_PROPOSED",
            "record_type": "SYNTHESIS",
            "statement": statement,
            "source": "GALAXY_PHASE5_SYNTHESIS",
        }
        synthesis = {
            "synthesis_record_id": synthesis_record_id,
            "source_record_ids": list(source_record_ids),
            "method": method,
            "confidence": confidence,
            "authority": "NAOMI",
        }
        edges = [
            {
                "edge_id": f"EDGE-SYNTH-{self.synthesis_seq}-{index}",
                "source_record_id": synthesis_record_id,
                "target_record_id": source_id,
                "relation_type": "DERIVED_FROM",
                "strength": 1.0,
                "status": "PROPOSED",
                "authority": "NONE",
                "evidence": {"method": method},
            }
            for index, source_id in enumerate(source_record_ids, 1)
        ]
        self.syntheses[synthesis_record_id] = {
            "record": record,
            "synthesis": synthesis,
            "derived_from_edges": edges,
        }
        self.writes += 1
        return {
            "status": "PROPOSED",
            "synthesis_record_id": synthesis_record_id,
            "synthesis": self.galaxy_synthesis(synthesis_record_id),
            "memoryos_retrieval_changed": False,
            "production_retrieval_changed": False,
            "default_retrieval_target_selected": False,
            "physical_delete": False,
        }

    def galaxy_verify_synthesis(self, synthesis_record_id, *, authority, approved):
        if authority != "NAOMI" or not approved:
            raise PermissionError
        detail = self.syntheses[synthesis_record_id]
        if detail["record"]["status"] == "SYNTHESIS_VERIFIED_SHADOW":
            return {
                "status": "VERIFIED_SHADOW",
                "synthesis": self.galaxy_synthesis(synthesis_record_id),
                "idempotent": True,
            }
        if detail["record"]["status"] != "SYNTHESIS_PROPOSED":
            raise ValueError
        detail["record"]["status"] = "SYNTHESIS_VERIFIED_SHADOW"
        for edge in detail["derived_from_edges"]:
            edge["status"] = "VERIFIED"
            edge["authority"] = "NAOMI"
        self.writes += 1
        return {
            "status": "VERIFIED_SHADOW",
            "synthesis_record_id": synthesis_record_id,
            "synthesis": self.galaxy_synthesis(synthesis_record_id),
            "memoryos_retrieval_changed": False,
            "production_retrieval_changed": False,
            "default_retrieval_target_selected": False,
            "physical_delete": False,
        }

    def galaxy_revoke_synthesis(self, synthesis_record_id, *, authority, approved, reason):
        if authority != "NAOMI" or not approved or not reason:
            raise PermissionError
        detail = self.syntheses[synthesis_record_id]
        detail["record"]["status"] = "SYNTHESIS_REVOKED"
        for edge in detail["derived_from_edges"]:
            edge["status"] = "REVOKED"
            edge["authority"] = "NAOMI"
        self.writes += 1
        return {
            "status": "REVOKED",
            "synthesis_record_id": synthesis_record_id,
            "synthesis": self.galaxy_synthesis(synthesis_record_id),
            "history_preserved": True,
            "source_records_preserved": True,
            "physical_delete": False,
            "memoryos_retrieval_changed": False,
            "production_retrieval_changed": False,
            "default_retrieval_target_selected": False,
        }


class Phase5Tests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_fixture_review_passes_read_only(self):
        result = p5.fixture_review(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_PHASE5_FIXTURE_REVIEW", result)
        self.assertTrue(result["checks"]["verified_relation_visible"])
        self.assertFalse(
            result["cluster_review"]["synthesis_candidate"]["synthesis_statement_generated"]
        )
        self.assertEqual(self.runtime.writes, 0)

    def test_duplicate_source_holds(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, a])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("DUPLICATE_SOURCE_RECORD_ID", result["hold_reasons"])

    def test_cross_scope_holds(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, "CROSS"])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "CROSS_SCOPE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE",
            result["hold_reasons"],
        )

    def test_unrelated_cluster_holds_without_verified_relation(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        result = p5.review_cluster(self.runtime, [a, "ISOLATED"])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("NO_VERIFIED_INTERNAL_RELATION", result["hold_reasons"])

    def test_verified_contradiction_holds(self):
        a, b = p5.FIXTURE_SOURCE_IDS
        self.runtime.edges["EDGE-CONTRADICTS"] = {
            "edge_id": "EDGE-CONTRADICTS",
            "source_record_id": a,
            "target_record_id": b,
            "relation_type": "CONTRADICTS",
            "strength": 0.8,
            "status": "VERIFIED",
            "authority": "NAOMI",
            "created_at": "2026-09-23T00:02:00+00:00",
            "verified_at": "2026-09-23T00:03:00+00:00",
        }
        result = p5.review_cluster(self.runtime, [a, b])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "UNRESOLVED_VERIFIED_CONTRADICTION_IN_CLUSTER",
            result["hold_reasons"],
        )

    def test_recursive_synthesis_holds_initial_slice(self):
        a = p5.FIXTURE_SOURCE_IDS[0]
        self.runtime.edges["EDGE-SYNTH"] = {
            "edge_id": "EDGE-SYNTH",
            "source_record_id": "SYNTH",
            "target_record_id": a,
            "relation_type": "DERIVED_FROM",
            "strength": 1.0,
            "status": "VERIFIED",
            "authority": "NAOMI",
            "created_at": "2026-09-23T00:04:00+00:00",
            "verified_at": "2026-09-23T00:05:00+00:00",
        }
        result = p5.review_cluster(self.runtime, ["SYNTH", a])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "RECURSIVE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE",
            result["hold_reasons"],
        )

    def test_mutation_design_review_is_read_only(self):
        before = self.runtime.writes
        result = p5.mutation_design_review(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_PHASE5_MUTATION_DESIGN", result)
        self.assertEqual(result["exact_synthesis_statement"], p5.CONTROLLED_SYNTHESIS_STATEMENT)
        self.assertTrue(result["checks"]["proposal_scope_is_not_memoryos"])
        self.assertTrue(result["checks"]["mutation_route_exposed"])
        self.assertTrue(result["checks"]["mutation_route_requires_signed_session_csrf_and_exact_step_confirmation"])
        self.assertEqual(
            result["next_gate"],
            "DEPLOY_VERIFY_READ_ONLY_CONTROL_REVIEW_THEN_PAUSE_FOR_EXPLICIT_NAOMI_ACTION",
        )
        self.assertEqual(self.runtime.writes, before)

    def test_mutation_requires_exact_confirmation(self):
        with self.assertRaises(PermissionError):
            p5.propose_controlled_synthesis(
                self.runtime,
                authority="NAOMI",
                approved=True,
                confirmation="WRONG",
            )
        self.assertEqual(self.runtime.writes, 0)

    def test_full_shadow_synthesis_lifecycle_is_reversible(self):
        proposal = p5.propose_controlled_synthesis(
            self.runtime,
            authority="NAOMI",
            approved=True,
            confirmation=p5.PROPOSE_CONFIRMATION,
        )
        self.assertEqual(proposal["status"], "PROPOSED", proposal)
        synthesis_record_id = proposal["effect"]["synthesis_record_id"]
        proposed = self.runtime.galaxy_synthesis(synthesis_record_id)
        self.assertEqual(proposed["record"]["scope"], p5.SHADOW_SCOPE)
        self.assertEqual(proposed["record"]["status"], "SYNTHESIS_PROPOSED")
        self.assertTrue(all(
            edge["status"] == "PROPOSED"
            for edge in proposed["derived_from_edges"]
        ))

        verified = p5.verify_controlled_synthesis(
            self.runtime,
            synthesis_record_id,
            authority="NAOMI",
            approved=True,
            confirmation=p5.VERIFY_CONFIRMATION,
        )
        self.assertEqual(verified["status"], "VERIFIED_SHADOW", verified)
        verified_detail = self.runtime.galaxy_synthesis(synthesis_record_id)
        self.assertEqual(
            verified_detail["record"]["status"],
            "SYNTHESIS_VERIFIED_SHADOW",
        )
        self.assertTrue(all(
            edge["status"] == "VERIFIED"
            for edge in verified_detail["derived_from_edges"]
        ))
        self.assertEqual(verified_detail["record"]["scope"], p5.SHADOW_SCOPE)

        revoked = p5.revoke_controlled_synthesis(
            self.runtime,
            synthesis_record_id,
            authority="NAOMI",
            approved=True,
            reason="controlled rollback proof",
            confirmation=p5.REVOKE_CONFIRMATION,
        )
        self.assertEqual(revoked["status"], "REVOKED", revoked)
        revoked_detail = self.runtime.galaxy_synthesis(synthesis_record_id)
        self.assertEqual(revoked_detail["record"]["status"], "SYNTHESIS_REVOKED")
        self.assertTrue(all(
            edge["status"] == "REVOKED"
            for edge in revoked_detail["derived_from_edges"]
        ))
        self.assertIn(p5.FIXTURE_SOURCE_IDS[0], self.runtime.records)
        self.assertIn(p5.FIXTURE_SOURCE_IDS[1], self.runtime.records)
        self.assertFalse(revoked["physical_delete"])
        self.assertFalse(revoked["memoryos_retrieval_changed"])
        self.assertFalse(revoked["production_retrieval_changed"])

    def test_carrier_packages_phase5_module(self):
        root = Path(__file__).resolve().parents[1]
        dockerfile = (root / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY api/galaxy_phase5.py ./galaxy_phase5.py", dockerfile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
