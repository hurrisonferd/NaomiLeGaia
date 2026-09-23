"""Offline safety tests for GALAXY Phase 4 revision/supersession semantics."""
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import galaxy_phase4 as p4


class FakeRuntime:
    def __init__(self):
        self.records = {
            p4.FIXTURE_REVISION_ID: {
                "record_id": p4.FIXTURE_REVISION_ID,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Later calibration observation revises the core.",
            },
            p4.FIXTURE_CORE_ID: {
                "record_id": p4.FIXTURE_CORE_ID,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Original calibration core observation.",
            },
            "NEW": {
                "record_id": "NEW",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "New current observation.",
            },
            "OLD": {
                "record_id": "OLD",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Older observation.",
            },
            "OTHER": {
                "record_id": "OTHER",
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Another possible successor.",
            },
            "CROSS": {
                "record_id": "CROSS",
                "scope": "OtherScope",
                "status": "ACTIVE",
                "statement": "Other-scope observation.",
            },
        }
        self.edges = {
            "EDGE-FIXTURE-REVISES": {
                "edge_id": "EDGE-FIXTURE-REVISES",
                "source_record_id": p4.FIXTURE_REVISION_ID,
                "target_record_id": p4.FIXTURE_CORE_ID,
                "relation_type": "REVISES",
                "strength": 0.9,
                "status": "VERIFIED",
                "evidence": {"fixture": True},
                "classifier": "TEST",
                "authority": "NAOMI",
                "verified_at": "2026-09-23T00:00:00+00:00",
            }
        }
        self.writes = 0

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

    def galaxy_relation(self, edge_id):
        edge = self.edges.get(edge_id)
        return dict(edge) if edge else None

    def galaxy_governing_state(self, record_id):
        record = self.records[record_id]
        incoming = [
            edge for edge in self.edges.values()
            if edge["target_record_id"] == record_id
            and edge["status"] == "VERIFIED"
            and edge["relation_type"] in {"REVISES", "SUPERSEDES"}
        ]
        revises = [e for e in incoming if e["relation_type"] == "REVISES"]
        supersedes = [e for e in incoming if e["relation_type"] == "SUPERSEDES"]
        active = record["status"] == "ACTIVE"
        if not active:
            state = "NONACTIVE_HISTORICAL"
            eligible = False
            companion = False
        elif supersedes:
            state = "HISTORICAL_SUPERSEDED"
            eligible = False
            companion = True
        elif revises:
            state = "CURRENT_REVISED_CONTEXT"
            eligible = True
            companion = True
        else:
            state = "CURRENT"
            eligible = True
            companion = False
        return {
            "record_id": record_id,
            "state": state,
            "record_status": record["status"],
            "current_default_eligible": eligible,
            "historical_retrieval_eligible": True,
            "revision_companion_required_when_material": companion,
            "incoming_verified_revises": revises,
            "incoming_verified_supersedes": supersedes,
        }

    def galaxy_propose_relation(
        self,
        *,
        source_record_id,
        target_record_id,
        relation_type,
        strength,
        evidence,
        classifier,
    ):
        for edge in self.edges.values():
            if (
                edge["source_record_id"] == source_record_id
                and edge["target_record_id"] == target_record_id
                and edge["relation_type"] == relation_type
                and edge["status"] in {"PROPOSED", "VERIFIED"}
            ):
                return {"status": "EXISTING", "relation": dict(edge), "retrieval_effect": "NONE"}
        edge_id = "EDGE-" + uuid.uuid4().hex
        edge = {
            "edge_id": edge_id,
            "source_record_id": source_record_id,
            "target_record_id": target_record_id,
            "relation_type": relation_type,
            "strength": float(strength),
            "status": "PROPOSED",
            "evidence": dict(evidence),
            "classifier": classifier,
            "authority": "NONE",
            "verified_at": None,
        }
        self.edges[edge_id] = edge
        self.writes += 1
        return {"status": "PROPOSED", "relation": dict(edge), "retrieval_effect": "NONE"}

    def galaxy_verify_relation(self, edge_id, *, authority, approved):
        if authority != "NAOMI" or not approved:
            raise PermissionError
        edge = self.edges[edge_id]
        edge["status"] = "VERIFIED"
        edge["authority"] = "NAOMI"
        edge["verified_at"] = "2026-09-23T01:00:00+00:00"
        self.writes += 1
        return {"status": "VERIFIED", "relation": dict(edge), "retrieval_effect": "NONE"}

    def galaxy_revoke_relation(self, edge_id, *, authority, approved, reason):
        if authority != "NAOMI" or not approved:
            raise PermissionError
        edge = self.edges[edge_id]
        edge["status"] = "REVOKED"
        edge["authority"] = "NAOMI"
        edge["evidence"] = {
            **dict(edge.get("evidence") or {}),
            "revocation": {"authority": "NAOMI", "reason": reason},
        }
        self.writes += 1
        return {
            "status": "REVOKED",
            "relation": dict(edge),
            "history_preserved": True,
            "physical_delete": False,
        }


class Phase4Tests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_fixture_review_passes_read_only(self):
        result = p4.fixture_review(self.runtime)
        self.assertEqual(result["status"], "PASS_READ_ONLY_PHASE4_FIXTURE_REVIEW", result)
        self.assertTrue(result["checks"]["verified_revises_visible"])
        self.assertTrue(result["checks"]["supersedes_review_ready_after_verified_revises"])
        self.assertEqual(self.runtime.writes, 0)

    def test_supersedes_requires_verified_revises_same_pair(self):
        result = p4.review_pair(self.runtime, "NEW", "OLD", "SUPERSEDES")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "SUPERSEDES_REQUIRES_VERIFIED_REVISES_SAME_PAIR",
            result["hold_reasons"],
        )

    def test_cross_scope_holds(self):
        result = p4.review_pair(self.runtime, "NEW", "CROSS", "REVISES")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(
            "CROSS_SCOPE_PAIR_NOT_ALLOWED_IN_INITIAL_PHASE4_SLICE",
            result["hold_reasons"],
        )

    def test_reverse_verified_edge_holds_cycle(self):
        self.runtime.edges["EDGE-REVERSE"] = {
            "edge_id": "EDGE-REVERSE",
            "source_record_id": "OLD",
            "target_record_id": "NEW",
            "relation_type": "REVISES",
            "strength": 0.8,
            "status": "VERIFIED",
            "evidence": {},
            "classifier": "TEST",
            "authority": "NAOMI",
            "verified_at": "2026-09-23T00:00:00+00:00",
        }
        result = p4.review_pair(self.runtime, "NEW", "OLD", "REVISES")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("DIRECT_REVISION_CYCLE_RISK", result["hold_reasons"])

    def test_competing_superseder_holds(self):
        self.runtime.edges["EDGE-OTHER-SUPERSEDES"] = {
            "edge_id": "EDGE-OTHER-SUPERSEDES",
            "source_record_id": "OTHER",
            "target_record_id": "OLD",
            "relation_type": "SUPERSEDES",
            "strength": 1.0,
            "status": "VERIFIED",
            "evidence": {},
            "classifier": "TEST",
            "authority": "NAOMI",
            "verified_at": "2026-09-23T00:00:00+00:00",
        }
        result = p4.review_pair(self.runtime, "NEW", "OLD", "REVISES")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("COMPETING_VERIFIED_SUPERSEDER", result["hold_reasons"])

    def test_mutation_requires_exact_naomi_confirmation(self):
        with self.assertRaises(PermissionError):
            p4.propose_transition(
                self.runtime,
                "NEW",
                "OLD",
                "REVISES",
                strength=0.9,
                evidence={"why": "test"},
                authority="NAOMI",
                approved=True,
                confirmation="WRONG",
            )
        self.assertEqual(self.runtime.writes, 0)

    def test_full_revision_supersession_and_reversible_unwind(self):
        proposal = p4.propose_transition(
            self.runtime,
            "NEW",
            "OLD",
            "REVISES",
            strength=0.9,
            evidence={"why": "new evidence changes interpretation"},
            authority="NAOMI",
            approved=True,
            confirmation="PROPOSE_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(proposal["status"], "PROPOSED", proposal)
        revises_id = proposal["proposal"]["relation"]["edge_id"]

        verified = p4.verify_transition(
            self.runtime,
            revises_id,
            authority="NAOMI",
            approved=True,
            confirmation="VERIFY_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(verified["status"], "VERIFIED", verified)
        self.assertEqual(
            verified["after"]["target_governing_state"]["state"],
            "CURRENT_REVISED_CONTEXT",
        )

        super_proposal = p4.propose_transition(
            self.runtime,
            "NEW",
            "OLD",
            "SUPERSEDES",
            strength=1.0,
            evidence={"why": "explicit governing replacement"},
            authority="NAOMI",
            approved=True,
            confirmation="PROPOSE_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(super_proposal["status"], "PROPOSED", super_proposal)
        supersedes_id = super_proposal["proposal"]["relation"]["edge_id"]

        superseded = p4.verify_transition(
            self.runtime,
            supersedes_id,
            authority="NAOMI",
            approved=True,
            confirmation="VERIFY_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(
            superseded["after"]["target_governing_state"]["state"],
            "HISTORICAL_SUPERSEDED",
        )
        self.assertFalse(
            superseded["after"]["target_governing_state"]["current_default_eligible"]
        )

        wrong_unwind = p4.revoke_transition(
            self.runtime,
            revises_id,
            authority="NAOMI",
            approved=True,
            reason="rollback test",
            confirmation="REVOKE_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(wrong_unwind["status"], "HOLD")
        self.assertEqual(wrong_unwind["reason"], "REVOKE_SUPERSEDES_BEFORE_REVISES")

        revoke_super = p4.revoke_transition(
            self.runtime,
            supersedes_id,
            authority="NAOMI",
            approved=True,
            reason="rollback supersession",
            confirmation="REVOKE_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(revoke_super["status"], "REVOKED", revoke_super)
        self.assertEqual(
            revoke_super["after"]["target_governing_state"]["state"],
            "CURRENT_REVISED_CONTEXT",
        )

        revoke_revises = p4.revoke_transition(
            self.runtime,
            revises_id,
            authority="NAOMI",
            approved=True,
            reason="rollback revision",
            confirmation="REVOKE_GALAXY_PHASE4_RELATION",
        )
        self.assertEqual(revoke_revises["status"], "REVOKED", revoke_revises)
        self.assertEqual(
            revoke_revises["after"]["target_governing_state"]["state"],
            "CURRENT",
        )
        self.assertEqual(self.runtime.edges[supersedes_id]["status"], "REVOKED")
        self.assertEqual(self.runtime.edges[revises_id]["status"], "REVOKED")
        self.assertIn("OLD", self.runtime.records)
        self.assertIn("NEW", self.runtime.records)

    def test_carrier_packages_phase4_module(self):
        root = Path(__file__).resolve().parents[1]
        dockerfile = (root / "api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY api/galaxy_phase4.py ./galaxy_phase4.py", dockerfile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
