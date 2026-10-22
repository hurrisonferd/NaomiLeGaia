"""ScampOS native cast parity, no separate scheduling or insertion code."""
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
CORE = REPO / "GaiaOS/SystemsOS/Core/ScampOS"
API = REPO / "api/gaiaos_scamp_chat.py"


class Message:
    def __init__(self, role, content):
        self.role, self.content = role, content


def load_host():
    spec = importlib.util.spec_from_file_location("scamp_host_parity", API)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bundle():
    current = json.loads((CORE / "CURRENT.json").read_text(encoding="utf-8"))
    guests = {}
    for guest_id, paths in current["guests"].items():
        guests[guest_id] = {
            "character": json.loads((REPO / paths["character"]).read_text(encoding="utf-8"))
        }
    return {"guests": guests}


class NativeScampParity(unittest.TestCase):
    def test_obsolete_selector_and_inserter_are_absent(self):
        self.assertFalse((CORE / "Runtime/scampos_dispatch.py").exists())
        self.assertFalse((REPO / "GaiaOS/Apps/ChatOS/Runtime/scampos_guest_adapter.py").exists())

    def test_spontaneous_cast_is_not_a_random_gate(self):
        host = load_host()
        decision = host.decide([Message("user", "What's for dinner?")], bundle())
        self.assertEqual(decision["eligible_guests"], ["SCAMP-001", "SCAMP-002"])
        self.assertEqual(decision["requested_guests"], [])
        self.assertIn("SAME model", host.model_instruction(decision))
        self.assertNotIn("guest selector unavailable", host.model_instruction(decision).lower())
        self.assertEqual(host.response_tool_options(decision), {})
        self.assertEqual(host.validate_output("A Prime can answer.", decision)["rendered_guest_ids"], [])

    def test_both_scamp_voices_can_speak_in_one_response(self):
        host = load_host()
        decision = host.decide([Message("user", "Helti and Rin, speak.")], bundle())
        self.assertEqual(decision["requested_guests"], ["SCAMP-001", "SCAMP-002"])
        answer = ("SCAMP-001 RIN-RIN 😈\nThat's a fucking connector.\n\n"
                  "SCAMP-002 HELTI-SKELTI 🕸️\nThe connector has no opinion.")
        self.assertEqual(host.validate_output(answer, decision)["rendered_guest_ids"],
                         ["SCAMP-001", "SCAMP-002"])
        self.assertIn("web_search", str(host.response_tool_options(decision)))
        with self.assertRaises(ValueError):
            host.validate_output("SCAMP-003 BAD 😒\nHello", decision)

    def test_source_policies_have_no_numeric_speech_gates(self):
        for name in ("INTRUSION-RULES.v1.json", "HELTI-SKELTI-INTRUSION-RULES.v1.json"):
            doc = json.loads((CORE / name).read_text(encoding="utf-8"))
            for obsolete in ("chance", "cooldown_turns", "max_guest_lines"):
                self.assertNotIn(obsolete, doc)


if __name__ == "__main__":
    unittest.main()
