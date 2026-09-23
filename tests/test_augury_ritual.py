"""Offline guardrails for AUGURY/RITUAL Phase 1 and Phase-4 first Ritual family."""
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import augury_ritual as ar
import galaxy_phase4 as p4


class FakeRuntime:
    def __init__(self):
        self.records = {
            ar.SOURCE_ID: {
                "record_id": ar.SOURCE_ID,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Later calibration observation revises the core.",
            },
            ar.TARGET_ID: {
                "record_id": ar.TARGET_ID,
                "scope": "MemoryOS",
                "status": "ACTIVE",
                "statement": "Original calibration core observation.",
            },
        }
        self.edges = {
            "EDGE-BASE-REVISES": {
                "edge_id": "EDGE-BASE-REVISES",
                "source_record_id": ar.SOURCE_ID,
                "target_record_id": ar.TARGET_ID,
                "relation_type": "REVISES",
                "strength": 0.9,
                "status": "VERIFIED",
                "evidence": {"fixture": True},
                "classifier": "TEST",
                "authority": "NAOMI",
                "created_at": "2026-09-20T01:00:00+00:00",
                "verified_at": "2026-09-20T01:01:00+00:00",
            }
        }
        self.writes = 0

    def galaxy_record(self, record_id):
        record = self.records.get(record_id)
        if record is None:
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
        if record["status"] != "ACTIVE":
            state, eligible, companion = "NONACTIVE_HISTORICAL", False, False
        elif supersedes:
            state, eligible, companion = "HISTORICAL_SUPERSEDED", False, True
        elif revises:
            state, eligible, companion = "CURRENT_REVISED_CONTEXT", True, True
        else:
            state, eligible, companion = "CURRENT", True, False
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
        self, *, source_record_id, target_record_id, relation_type,
        strength, evidence, classifier
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
            "created_at": "2026-09-23T15:00:00+00:00",
            "verified_at": None,
        }
        self.edges[edge_id] = edge
        self.writes += 1
        return {"status": "PROPOSED", "relation": dict(edge), "retrieval_effect": "NONE"}

    def galaxy_verify_relation(self, edge_id, *, authority, approved):
        if authority != "NAOMI" or approved is not True:
            raise PermissionError
        edge = self.edges[edge_id]
        edge["status"] = "VERIFIED"
        edge["authority"] = "NAOMI"
        edge["verified_at"] = "2026-09-23T15:01:00+00:00"
        self.writes += 1
        return {"status": "VERIFIED", "relation": dict(edge), "retrieval_effect": "NONE"}

    def galaxy_revoke_relation(self, edge_id, *, authority, approved, reason):
        if authority != "NAOMI" or approved is not True:
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


class AuguryRitualPhase1Tests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()

    def test_phase1_explicitly_does_not_claim_general_augury(self):
        state = ar.phase1_status(self.runtime)
        self.assertFalse(state["augury"]["general_natural_language_parser_implemented"])
        self.assertFalse(state["ritual"]["natural_language_manifestation_allowed"])
        self.assertEqual(self.runtime.writes, 0)

    def test_grimoire_has_exact_phase4_family(self):
        ids = {r["ritual_id"] for r in ar.load_grimoire()["rituals"]}
        self.assertEqual(ids, {ar.PROPOSE_ID, ar.VERIFY_ID, ar.REVOKE_ID})

    def test_compile_is_read_only_and_target_exact(self):
        valid = ar.compile_exact(
            self.runtime,
            ar.PROPOSE_ID,
            {"source_record_id": ar.SOURCE_ID, "target_record_id": ar.TARGET_ID},
        )
        self.assertEqual(valid["resolution"], "VALID", valid)
        self.assertFalse(valid["manifestation_performed"])
        self.assertEqual(self.runtime.writes, 0)

        wrong = ar.compile_exact(
            self.runtime,
            ar.PROPOSE_ID,
            {"source_record_id": ar.SOURCE_ID, "target_record_id": "NOT-TARGET"},
        )
        self.assertEqual(wrong["resolution"], "HOLD")
        self.assertIn("CONTROLLED_TARGET_MISMATCH", wrong["errors"])
        self.assertEqual(self.runtime.writes, 0)

    def test_manifestation_requires_exact_confirmation(self):
        with self.assertRaises(PermissionError):
            ar.manifest(
                self.runtime,
                ar.PROPOSE_ID,
                {"source_record_id": ar.SOURCE_ID, "target_record_id": ar.TARGET_ID},
                authority="NAOMI",
                approved=True,
                confirmation="WRONG",
            )
        self.assertEqual(self.runtime.writes, 0)

    def test_controlled_ritual_full_cycle_restores_revised_context(self):
        proposed = ar.manifest(
            self.runtime,
            ar.PROPOSE_ID,
            {"source_record_id": ar.SOURCE_ID, "target_record_id": ar.TARGET_ID},
            authority="NAOMI",
            approved=True,
            confirmation=ar.CONFIRMATIONS[ar.PROPOSE_ID],
        )
        self.assertEqual(proposed["status"], "PASS", proposed)
        edge_id = proposed["effect"]["proposal"]["relation"]["edge_id"]
        self.assertEqual(
            self.runtime.galaxy_governing_state(ar.TARGET_ID)["state"],
            "CURRENT_REVISED_CONTEXT",
        )

        verified = ar.manifest(
            self.runtime,
            ar.VERIFY_ID,
            {"edge_id": edge_id},
            authority="NAOMI",
            approved=True,
            confirmation=ar.CONFIRMATIONS[ar.VERIFY_ID],
        )
        self.assertEqual(verified["status"], "PASS", verified)
        self.assertEqual(
            verified["after_target_governing_state"]["state"],
            "HISTORICAL_SUPERSEDED",
        )
        self.assertTrue(verified["after_target_governing_state"]["historical_retrieval_eligible"])

        revoked = ar.manifest(
            self.runtime,
            ar.REVOKE_ID,
            {"edge_id": edge_id, "reason": "controlled rollback proof"},
            authority="NAOMI",
            approved=True,
            confirmation=ar.CONFIRMATIONS[ar.REVOKE_ID],
        )
        self.assertEqual(revoked["status"], "PASS", revoked)
        self.assertEqual(
            revoked["after_target_governing_state"]["state"],
            "CURRENT_REVISED_CONTEXT",
        )
        self.assertEqual(self.runtime.edges[edge_id]["status"], "REVOKED")
        self.assertEqual(self.runtime.edges["EDGE-BASE-REVISES"]["status"], "VERIFIED")
        self.assertIn(ar.SOURCE_ID, self.runtime.records)
        self.assertIn(ar.TARGET_ID, self.runtime.records)

    def test_verify_cannot_target_unrelated_edge(self):
        self.runtime.edges["EDGE-BAD"] = {
            "edge_id": "EDGE-BAD",
            "source_record_id": ar.SOURCE_ID,
            "target_record_id": ar.TARGET_ID,
            "relation_type": "REVISES",
            "strength": 1.0,
            "status": "PROPOSED",
            "evidence": {},
            "classifier": "TEST",
            "authority": "NONE",
            "created_at": "2026-09-23T15:00:00+00:00",
            "verified_at": None,
        }
        result = ar.compile_exact(self.runtime, ar.VERIFY_ID, {"edge_id": "EDGE-BAD"})
        self.assertEqual(result["resolution"], "HOLD")
        self.assertIn("RELATION_TYPE_MISMATCH", result["errors"])

    def test_source_and_carrier_surface_present(self):
        root = Path(__file__).resolve().parents[1]
        docker = (root / "api" / "Dockerfile").read_text(encoding="utf-8")
        bridge = (root / "api" / "browser_memcon_bridge.py").read_text(encoding="utf-8")
        self.assertIn("COPY api/augury_ritual.py ./augury_ritual.py", docker)
        self.assertIn('/ritual/phase4/review', bridge)
        self.assertIn('/ritual/manifest', bridge)
        self.assertIn('X-GaiaOS-Ritual-CSRF', bridge)
        self.assertIn('MANIFEST_EXACT_RITUAL', bridge)


if __name__ == "__main__":
    unittest.main(verbosity=2)
