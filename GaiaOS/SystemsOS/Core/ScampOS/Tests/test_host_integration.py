"""Source-wired ScampOS integration canaries."""
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
API = REPO / "api"
CORE = REPO / "GaiaOS/SystemsOS/Core/ScampOS"

spec = importlib.util.spec_from_file_location("scamp_host_canary", API / "gaiaos_scamp_chat.py")
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

class Message:
    def __init__(self,role,content):
        self.role=role
        self.content=content

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.bundle={
            "character":json.loads((CORE/"Characters/RINRIN.v1.json").read_text(encoding="utf-8")),
            "policy":json.loads((CORE/"INTRUSION-RULES.v1.json").read_text(encoding="utf-8")),
        }

    def test_spontaneous_without_summons(self):
        decision=host.decide([Message("user","That Cyberpunk jacket is ridiculous.")],self.bundle,roll=0.01)
        self.assertTrue(decision["appear"])
        self.assertEqual(decision["reason"],"CHANCE")
        self.assertEqual(decision["context"],"gaming")

    def test_all_topics_remain_eligible(self):
        for sample in ("Rin, my tonsil hurts", "Rin, I'm afraid of eviction",
                       "I'm thinking about suicide", "Rin, I need to pay my debt",
                       "My throat hurts", "Rent is due", "Terrible emergency"):
            with self.subTest(sample=sample):
                result=host.decide([Message("user",sample)],self.bundle,roll=0.01)
                self.assertTrue(result["appear"])

    def test_cooldown_and_manual_mute(self):
        history=[Message("user","game"),Message("assistant",host.HEADER+"\ntext"),
                 Message("user","lol cyberpunk")]
        self.assertFalse(host.decide(history,self.bundle,roll=0.001)["appear"])
        self.assertFalse(host.decide([Message("user","game")],self.bundle,roll=0.001,muted=True)["appear"])

    def test_in_chat_mute_and_reenable(self):
        messages=[Message("user","Mute Rin"),Message("assistant","Done"),
                  Message("user","lol Cyberpunk")]
        self.assertFalse(host.decide(messages,self.bundle,roll=0)["appear"])
        messages.extend([Message("assistant","Okay"),Message("user","Unmute Rin")])
        self.assertTrue(host.decide(messages,self.bundle,roll=0.99)["appear"])

    def test_explicit_casual_summon_without_keyword_context(self):
        self.assertTrue(host.decide([Message("user","Rin, get in here")],
                                    self.bundle,roll=0.99)["appear"])

    def test_exact_guest_header(self):
        decision=host.decide([Message("user","lol gaming")],self.bundle,roll=0)
        self.assertEqual(host.validate_output(host.HEADER+"\nA bad pun",decision)["status"],"PASS_GUEST_RENDERED")
        with self.assertRaises(ValueError):
            host.validate_output("SCAMP-01 RINRIN 😈 (invented)\nA bad pun",decision)

    def test_no_incorrect_intrusions(self):
        decision=host.decide([Message("user","My throat hurts")],self.bundle,roll=0.99)
        with self.assertRaises(ValueError):
            host.validate_output(host.HEADER+"\nBad timing",decision)
        self.assertEqual(host.validate_output("60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)\nHi",decision)["status"],"PASS_NO_GUEST_SELECTED")

    def test_real_api_path_wired(self):
        api=(API/"gaiaos_api.py").read_text(encoding="utf-8")
        boot=(API/"gaiaos_app.py").read_text(encoding="utf-8")
        for snippet in ("scampos_bundle", "gaiaos_scamp_chat.decide(",
                        "gaiaos_scamp_chat.model_instruction(",
                        "gaiaos_scamp_chat.validate_output("):
            self.assertIn(snippet,api)
        self.assertIn('"scampos_guest": _guest_boot_metadata()',boot)

    def test_six_prime_lanes_untouched(self):
        fair=REPO/"GaiaOS/SystemsOS/Core/FairyOS"
        data=json.loads((fair/"COUNCIL-PRESENTATION-SPEC.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(data["speaker_order"],["VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE"])
        self.assertNotIn("RINRIN",data["members"])

if __name__=="__main__": unittest.main()
