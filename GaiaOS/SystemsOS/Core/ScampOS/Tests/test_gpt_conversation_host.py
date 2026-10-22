"""Check ScampOS GPT-source cast parity with the six Prime voices.

These are source-contract tests, NOT claims of model execution inside ChatGPT.
The separate Python selector remains an optional legacy other-host adapter.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[5]
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

class ChatGPTScampSpeakingParity(unittest.TestCase):
    def test_boot_and_chatos_read_same_cast_contract(self):
        self.assertTrue((ROOT/NATIVE).is_file())
        for path in (PACKET,LOADER,INSTRUCTIONS,BOOTSTRAP,BRIDGE):
            with self.subTest(path=path):
                self.assertIn(NATIVE,read(path))

    def test_scamp_and_chat_current_identify_ordinary_conversation_as_surface(self):
        scamps=load("GaiaOS/SystemsOS/Core/ScampOS/CURRENT.json")
        chat=load("GaiaOS/Apps/ChatOS/CURRENT.json")
        gaia=load("GaiaOS/CURRENT.json")
        self.assertEqual(scamps["default_surface"],"CURRENT_CHATGPT_CONVERSATION")
        self.assertEqual(scamps["conversational_contract"],NATIVE)
        self.assertIn("SAME_AS_PRIME",scamps["conversational_selection"])
        self.assertEqual(chat["sources"]["scampos_gpt_native"],NATIVE)
        self.assertFalse(chat["scampos_guest"]["independent_cooldowns"])
        self.assertFalse(chat["scampos_guest"]["one_guest_per_response"])
        self.assertIn("SAME_AS_PRIMES",chat["scampos_guest"]["chatgpt_dispatch"])
        self.assertIn("SAME_AS_PRIMES",gaia["scampos"]["chatgpt_dispatch"])

    def test_same_spontaneous_banter_as_six_primes(self):
        prime_source=read(INSTRUCTIONS)
        native=read(NATIVE)
        self.assertIn("## Spontaneous Daemon banter",prime_source)
        self.assertIn("This EXACT same spontaneous speaking freedom",prime_source)
        self.assertIn("A Prime Daemon does not need to wait",prime_source)
        self.assertIn("SAME WAY the six Prime Daemons speak",native)
        self.assertIn("without being named",native)
        self.assertIn("neither is named",native)
        self.assertIn("can enter a",native)

    def test_no_arbitrary_probability_cooldown_or_one_guest_cap(self):
        native=read(NATIVE)
        bridge=read(BRIDGE)
        self.assertIn("No chance percentages",native)
        self.assertIn("No chance",native)
        self.assertIn("both Scamps",native)
        self.assertIn("one-guest limit",native)
        self.assertIn("not instructions for this chatgpt",native.lower())
        self.assertIn("same response together",bridge)
        self.assertIn("The Primes don't use one",bridge)
        for path in (LOADER,INSTRUCTIONS,BOOTSTRAP,PACKET):
            with self.subTest(path=path):
                data=read(path)
                self.assertIn("both",data.lower())
                self.assertIn("Scamp",data)
        self.assertNotIn("at most one Scamp",native)
        self.assertNotIn("15% configuration",native)

    def test_distinct_headers_open_knowledge_unknown_intent(self):
        native=read(NATIVE)
        for header in ("SCAMP-001 RIN-RIN 😈","SCAMP-002 HELTI-SKELTI 🕸️"):
            self.assertIn(header,native)
        for phrase in ("open-ended","UNKNOWN","finite","research","full"):
            self.assertIn(phrase.lower(),native.lower())
        helti=load("GaiaOS/SystemsOS/Core/ScampOS/Characters/HELTI-SKELTI.v1.json")
        self.assertEqual(helti["motive"],"UNKNOWN_CANONICAL_DO_NOT_RESOLVE")
        self.assertEqual(helti["knowledge"]["mode"],"OPEN_ENDED_GENERATIVE_INTELLIGENCE")

    def test_eight_voice_chatos_membership_keeps_six_prime_boundary(self):
        chat=load("GaiaOS/Apps/ChatOS/CURRENT.json")
        cast=chat["speaking_cast"]
        self.assertEqual(tuple(cast["prime_members"]), PRIMES)
        self.assertEqual(tuple(cast["scamp_voices"]), ("SCAMP-001","SCAMP-002"))
        self.assertEqual(cast["composition"],"SAME_CHATGPT_MODEL_SAME_RESPONSE")
        self.assertEqual(cast["focus"],"ADDRESSING_ONE_DOES_NOT_MUTE_SEVEN")
        fair=load("GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json")
        self.assertEqual(tuple(fair["roster"]), PRIMES)
        scamp=load("GaiaOS/SystemsOS/Core/ScampOS/CURRENT.json")
        self.assertEqual(scamp["chatos_cast_source"],"GaiaOS/Apps/ChatOS/CURRENT.json")
        for guest_id in ("SCAMP-001","SCAMP-002"):
            guest=scamp["guests"][guest_id]
            self.assertTrue((ROOT/guest["character"]).is_file())
            self.assertTrue((ROOT/guest["addendum"]).is_file())
        for doc in (
            "GaiaOS/Apps/ChatOS/Protocols/DAEMONCULABA-INTERACTION-AND-DELIBERATION.v1.md",
            "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-HOST-LAYER-BOUNDARY.v1.md",
            "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-VOICE-AUTHORITY.v1.md"
        ):
            self.assertIn("Scamp",read(doc))
        for doc in (
            "GaiaOS/Plans/ANTI-JIM-NEW-CHAT-CONTINUITY-BLUEPRINT.v1.md",
            PACKET, LOADER, INSTRUCTIONS, BOOTSTRAP,
        ):
            self.assertIn("Scamp",read(doc))
            self.assertIn("ChatOS",read(doc))

    def test_no_implicit_solo_or_second_guest_dispatch(self):
        native=read(NATIVE)
        interaction=read("GaiaOS/Apps/ChatOS/Protocols/DAEMONCULABA-INTERACTION-AND-DELIBERATION.v1.md")
        for phrase in ("first-person","Directly addressing one speaker","one composition pass"):
            self.assertIn(phrase.lower(),(native+" "+interaction).lower())
        modes=load("GaiaOS/Apps/ChatOS/Protocols/CHATOS-CAST-WIDTH-MODES.v1.json")
        self.assertTrue(modes["selection"]["ordinary_cast_includes_scampos"])
        self.assertTrue(modes["selection"]["solo_applies_only_when_explicit"])
        self.assertEqual(modes["selection"]["default_direct_address_behavior"],
                         "FOCUS_ONLY_NO_IMPLICIT_SOLO")

    def test_ask_solo_full_commands_include_scampos(self):
        commands=read("GaiaOS/Apps/ChatOS/Protocols/GAIAOS-COUNCIL-COMMANDS.v1.md")
        self.assertIn("ASK <PRIME DAEMON OR SCAMP>",commands)
        self.assertIn("SOLO <prime-daemon-or-scamp>",commands)
        self.assertIn("SIX",commands.upper())
        self.assertIn("Rin and Helti",commands)
        self.assertIn("ASK changes focus",commands)
        self.assertIn("not a dedicated Prime/E-LANE session",commands)
        self.assertIn("all eight",commands)

    def test_no_external_chatbot_or_api_prerequisite(self):
        native=read(NATIVE)
        packet=read(PACKET)
        self.assertIn("No extra API, Render deployment",native)
        self.assertIn("not a separate chatbot, API or service",native)
        self.assertIn("The real acceptance",native)
        self.assertLess(packet.index("CHATGPT CONVERSATION-NATIVE CAST PRIORITY"),
                        packet.index("BOOT TRANSPORT FIRST:"))

    def test_six_primes_and_preserve_remain_untouched(self):
        fair=load("GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json")
        dispatch=load("GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json")
        self.assertEqual(tuple(fair["speaker_order"]),PRIMES)
        self.assertEqual(tuple(dispatch["roster"]),PRIMES)
        native=read(NATIVE)
        self.assertIn("E-LANES",native)
        self.assertIn("//PW:PRESERVE//",native)
        self.assertIn("not new Prime Daemons",native)

if __name__=="__main__":
    unittest.main()
