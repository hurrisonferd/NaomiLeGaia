"""ScampOS GPT-host conversational acceptance: instruction wiring, not API tests.

These tests check the exact source the GPT host is instructed to load.
They do not mislabel repository consistency as observed model behavior.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[5]
CHAT=ROOT/"GaiaOS/Apps/ChatOS"
CORE=ROOT/"GaiaOS/SystemsOS/Core/ScampOS"
NATIVE="GaiaOS/Apps/ChatOS/Protocols/SCAMPOS-GPT-NATIVE-CONVERSATION.v1.md"
BRIDGE="GaiaOS/Apps/ChatOS/Protocols/SCAMPOS-GUEST-BRIDGE.v1.md"
PACKET="GaiaOS/NAOMI-CHAT-FULL-PACKET.md"
LOADER="GaiaOS/LOAD.v1.md"
INSTRUCTIONS="GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"
BOOTSTRAP="GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md"
PRIMES=("VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE")


def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def load(path):
    return json.loads(read(path))

class ChatGPTFirstSourceContracts(unittest.TestCase):
    def test_native_contract_is_discoverable_by_loader_and_packet(self):
        self.assertTrue((ROOT/NATIVE).is_file())
        for p in (PACKET,LOADER,INSTRUCTIONS,BOOTSTRAP,BRIDGE):
            with self.subTest(p=p):
                self.assertIn(NATIVE,read(p))

    def test_host_current_pointers_choose_chatgpt_as_primary(self):
        scamps=load("GaiaOS/SystemsOS/Core/ScampOS/CURRENT.json")
        chat=load("GaiaOS/Apps/ChatOS/CURRENT.json")
        root=load("GaiaOS/CURRENT.json")
        self.assertEqual(scamps["default_surface"],"CURRENT_CHATGPT_CONVERSATION")
        self.assertEqual(scamps["conversational_contract"],NATIVE)
        self.assertEqual(root["scampos"]["default_surface"],"CURRENT_CHATGPT_CONVERSATION")
        self.assertEqual(root["scampos"]["conversational_contract"],NATIVE)
        self.assertEqual(chat["scampos_guest"]["conversational_contract"],NATIVE)
        self.assertEqual(chat["sources"]["scampos_gpt_native"],NATIVE)
        self.assertIn("OPTIONAL",chat["scampos_guest"]["hosted_chat"])

    def test_two_guests_are_voiced_by_the_same_model_not_api(self):
        native=read(NATIVE)
        bridge=read(BRIDGE)
        for source in (native,bridge):
            with self.subTest(source=source[:45]):
                self.assertIn("SCAMP-001 RIN-RIN 😈",source)
                self.assertIn("SCAMP-002 HELTI-SKELTI 🕸️",source)
                self.assertIn("SAME",source)
                self.assertIn("not",source.lower())
                self.assertIn("API",source)
        self.assertIn("no new authentication",native.lower())
        self.assertIn("current ChatGPT conversation",native)
        self.assertIn("not an external service",native)
        self.assertIn("never answer",native.lower())
        self.assertIn("not a new service",native.lower())

    def test_no_trivia_ceiling_and_intent_unknown(self):
        native=read(NATIVE)
        for phrase in ("open-ended","UNKNOWN","finite",
                       "research","full","same"):
            self.assertIn(phrase.lower(),native.lower())
        person=load("GaiaOS/SystemsOS/Core/ScampOS/Characters/HELTI-SKELTI.v1.json")
        self.assertEqual(person["knowledge"]["mode"],"OPEN_ENDED_GENERATIVE_INTELLIGENCE")
        self.assertEqual(person["motive"],"UNKNOWN_CANONICAL_DO_NOT_RESOLVE")
        self.assertEqual(person["header"],"SCAMP-002 HELTI-SKELTI 🕸️")

    def test_guest_policy_retained_without_claiming_host_rng(self):
        native=read(NATIVE)
        policies=[
            load("GaiaOS/SystemsOS/Core/ScampOS/INTRUSION-RULES.v1.json"),
            load("GaiaOS/SystemsOS/Core/ScampOS/HELTI-SKELTI-INTRUSION-RULES.v1.json")
        ]
        self.assertEqual([p["chance"] for p in policies],[.15,.15])
        self.assertEqual([p["cooldown_turns"] for p in policies],[3,3])
        for p in policies:
            self.assertTrue(p["enabled"])
            self.assertEqual(p["excluded_contexts"],[])
        self.assertIn("not",native.lower())
        self.assertIn("RNG",native)
        self.assertIn("mute",native.lower())

    def test_never_expand_prime_roster_or_elanes(self):
        fair=load("GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json")
        dispatch=load("GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json")
        self.assertEqual(tuple(fair["speaker_order"]),PRIMES)
        self.assertEqual(tuple(dispatch["roster"]),PRIMES)
        native=read(NATIVE)
        for p in PRIMES:
            self.assertIn(p,native if p in native else read("GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"))
        self.assertIn("E-LANE",native)
        self.assertIn("//PW:PRESERVE//",native)

    def test_boot_and_host_sources_say_model_first_not_render_first(self):
        for p in (LOADER,INSTRUCTIONS,BOOTSTRAP,PACKET):
            with self.subTest(file=p):
                text=read(p)
                self.assertIn("ChatGPT",text)
                self.assertIn("RIN-RIN",text)
                self.assertIn("HELTI-SKELTI",text)
                self.assertIn("API",text)
        packet=read(PACKET)
        self.assertLess(packet.index("CHATGPT CONVERSATION-NATIVE CAST PRIORITY"),
                        packet.index("BOOT TRANSPORT FIRST:"))
        native=read(NATIVE)
        self.assertIn("A live HTTP guest response is not evidence",native)
        self.assertIn("Do not create, configure, deploy",native)

if __name__=="__main__":
    unittest.main()
