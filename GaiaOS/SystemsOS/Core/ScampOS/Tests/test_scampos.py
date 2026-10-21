"""ScampOS two-guest source and dispatch canaries."""
import importlib.util,json,unittest
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
CORE=REPO/"GaiaOS/SystemsOS/Core/ScampOS"

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

scamp=load("scamp_dispatch_test",CORE/"Runtime/scampos_dispatch.py")
adapter=load("scamp_adapter_test",REPO/"GaiaOS/Apps/ChatOS/Runtime/scampos_guest_adapter.py")
RIN="SCAMP-001 RIN-RIN 😈"
HELTI="SCAMP-002 HELTI-SKELTI 🕸️"

class ScampTests(unittest.TestCase):
    def test_registry_has_two_canonical_unique_guests(self):
        reg=scamp.load_registry()
        self.assertEqual(list(reg),["SCAMP-001","SCAMP-002"])
        self.assertEqual(reg["SCAMP-001"]["character"]["header"],RIN)
        self.assertEqual(reg["SCAMP-002"]["character"]["header"],HELTI)
        for id,guest in reg.items():
            self.assertFalse(guest["character"]["prime_member"])
            self.assertFalse(guest["character"]["tool_access"])
            self.assertEqual(guest["policy"]["excluded_contexts"],[])

    def test_renamed_rin_retains_traits_without_old_canonical_file(self):
        self.assertTrue((CORE/"Characters/RINRIN.v1.json").exists())  # Historical continuity alias preserved
        self.assertTrue((CORE/"Characters/RIN-RIN.v1.json").exists())
        character=scamp.load_registry()["SCAMP-001"]["character"]
        self.assertEqual(character["id"],"SCAMP-001")
        self.assertIn("RINRIN",character["legacy_name_aliases"])
        self.assertIn("object_confusion",character["foundational_mechanisms"])

    def test_both_guests_independent_chance(self):
        for guest in ("SCAMP-001","SCAMP-002"):
            self.assertTrue(scamp.select(9,context="unknown",guest_id=guest,roll=0)["appear"])
            self.assertFalse(scamp.select(9,context="unknown",guest_id=guest,roll=.99)["appear"])

    def test_all_topics_eligible_for_each(self):
        for guest in ("SCAMP-001","SCAMP-002"):
            for context in ("medical","mental_health","financial","urgent","grief",
                            "serious","critical_operations","unknown"):
                with self.subTest(guest=guest,context=context):
                    self.assertTrue(scamp.select(5,context=context,guest_id=guest,roll=0)["appear"])

    def test_independent_cooldowns(self):
        d=scamp.select_guests(5,last_turns={"SCAMP-001":4},
                              rolls={"SCAMP-001":0,"SCAMP-002":0})
        self.assertEqual(d["guest_id"],"SCAMP-002")
        self.assertEqual(d["evaluations"]["SCAMP-001"]["reason"],"COOLDOWN")

    def test_rotating_collision(self):
        for turn,expected in [(5,"SCAMP-001"),(6,"SCAMP-002"),(7,"SCAMP-001")]:
            with self.subTest(turn=turn):
                d=scamp.select_guests(turn,rolls={"SCAMP-001":0,"SCAMP-002":0})
                self.assertEqual(d["guest_id"],expected)
                self.assertTrue(d["collision"])

    def test_explicit_guest_wins_collision(self):
        d=scamp.select_guests(5,rolls={"SCAMP-001":0,"SCAMP-002":.99},
                              explicit_guests={"SCAMP-002"})
        self.assertEqual(d["guest_id"],"SCAMP-002")
        self.assertEqual(d["reason"],"EXPLICIT")

    def test_user_mutes_scoped(self):
        d=scamp.select_guests(5,rolls={"SCAMP-001":0,"SCAMP-002":0},
                              muted_guests={"SCAMP-001"})
        self.assertEqual(d["guest_id"],"SCAMP-002")
        d=scamp.select_guests(5,rolls={"SCAMP-001":0,"SCAMP-002":0},
                              muted_guests={"SCAMP-001","SCAMP-002"})
        self.assertFalse(d["appear"])

    def test_probability_and_state_validation(self):
        with self.assertRaises(ValueError):scamp.select(5,last_turn=5)
        with self.assertRaises(ValueError):scamp.select(5,roll=1)
        with self.assertRaises(ValueError):
            scamp.select_guests(5,explicit_guests={"SCAMP-404"})

    def test_exact_header_rendering(self):
        self.assertEqual(scamp.render_guest("Hi"),RIN+"\nHi")
        self.assertEqual(scamp.render_guest("DNS is a naming system.","SCAMP-002"),
                         HELTI+"\nDNS is a naming system.")

    def test_adapter_multi_guest(self):
        d=adapter.decide_guests(6,rolls={"SCAMP-001":0,"SCAMP-002":0})
        self.assertEqual(d["guest_id"],"SCAMP-002")
        text=adapter.insert_guest("BEFORE","Knowledge","AFTER",d)
        self.assertEqual(text,"BEFORE\n\n"+HELTI+"\nKnowledge\n\nAFTER")
        with self.assertRaises(ValueError):
            adapter.insert_guest("Before","Bad","After",{**d,"header":RIN})

    def test_unbounded_knowledge_not_a_fixed_fact_list(self):
        current=json.loads((CORE/"CURRENT.json").read_text(encoding="utf-8"))
        helti=current["guests"]["SCAMP-002"]
        self.assertNotIn("knowledge",helti)
        self.assertEqual(current["knowledge_mode"],
                         "GENERATIVE_MODEL_KNOWLEDGE_OPTIONAL_LIVE_RESEARCH")
        profile=scamp.load_registry()["SCAMP-002"]["character"]
        self.assertEqual(profile["knowledge"]["mode"],"OPEN_ENDED_GENERATIVE_INTELLIGENCE")
        self.assertNotIn("source",profile["knowledge"])
        api=(REPO/"api/gaiaos_api.py").read_text(encoding="utf-8")
        host=(REPO/"api/gaiaos_scamp_chat.py").read_text(encoding="utf-8")
        self.assertNotIn("HELTI-SKELTI-FACTS.v1.json",api)
        self.assertNotIn('fact["line"]',host)
        self.assertNotIn('facts[(turn-',host)

    def test_six_prime_roster_and_elanes_not_mutated(self):
        fair=REPO/"GaiaOS/SystemsOS/Core/FairyOS"
        spec=json.loads((fair/"COUNCIL-PRESENTATION-SPEC.v1.json").read_text(encoding="utf-8"))
        matrix=json.loads((fair/"OPERATOR-DISPATCH-MATRIX.v1.json").read_text(encoding="utf-8"))
        expected=["VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE"]
        self.assertEqual(spec["speaker_order"],expected)
        self.assertEqual(matrix["roster"],expected)
        for name in ("RIN-RIN","HELTI-SKELTI"):
            self.assertNotIn(name,spec["members"])
            self.assertNotIn(name,matrix["members"])

if __name__=="__main__":unittest.main()
