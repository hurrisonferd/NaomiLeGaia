"""ScampOS experiment canaries, independent of the actual ChatGPT runtime."""
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
CORE = REPO / "GaiaOS/SystemsOS/Core/ScampOS"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("test source unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scamp = load("scamp_canary_runtime", CORE / "Runtime/scampos_dispatch.py")
chatos = load("scamp_canary_adapter", REPO / "GaiaOS/Apps/ChatOS/Runtime/scampos_guest_adapter.py")


class TestScampOS(unittest.TestCase):
    def test_exact_guest_header(self):
        self.assertEqual(scamp.load_policy()["guest_header"], "SCAMP-01 RINRIN 😈")
        self.assertEqual(scamp.render_guest("Terrible advice."),
                         "SCAMP-01 RINRIN 😈\nTerrible advice.")

    def test_probability(self):
        self.assertTrue(scamp.select(9, context="playful", roll=0.02)["appear"])
        self.assertFalse(scamp.select(9, context="playful", roll=0.9)["appear"])

    def test_cooldown(self):
        self.assertFalse(scamp.select(5, context="playful", last_turn=4, roll=0)["appear"])
        self.assertTrue(scamp.select(8, context="playful", last_turn=4, roll=0)["appear"])

    def test_explicit(self):
        self.assertTrue(scamp.select(5, context="casual", last_turn=4,
                                     roll=0.9, explicit=True)["appear"])

    def test_all_contexts_eligible(self):
        for context in ["unknown", "mental_health", "financial", "serious",
                        "medical", "grief", "urgent", "critical_operations"]:
            with self.subTest(context=context):
                self.assertTrue(scamp.select(5, context=context, roll=0)["appear"])
                self.assertFalse(scamp.select(5, context=context, roll=0.99)["appear"])
                self.assertTrue(scamp.select(5, context=context, explicit=True, roll=0.99)["appear"])

    def test_manual_mute(self):
        self.assertFalse(scamp.select(5, context="playful", explicit=True, muted=True)["appear"])

    def test_guest_adapter(self):
        decision = chatos.decide_guest(11, context="creative", roll=0.02)
        text = chatos.insert_guest("PRIME BEFORE", "GUEST", "PRIME AFTER", decision)
        self.assertEqual(text, "PRIME BEFORE\n\nSCAMP-01 RINRIN 😈\nGUEST\n\nPRIME AFTER")
        with self.assertRaises(ValueError):
            chatos.insert_guest("PRIME", "GUEST", "PRIME", {"appear": True, "header": "WRONG"})

    def test_original_six_still_six(self):
        fairy = REPO / "GaiaOS/SystemsOS/Core/FairyOS"
        presentation = json.loads((fairy / "COUNCIL-PRESENTATION-SPEC.v1.json").read_text(encoding="utf-8"))
        dispatch = json.loads((fairy / "OPERATOR-DISPATCH-MATRIX.v1.json").read_text(encoding="utf-8"))
        six = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]
        self.assertEqual(presentation["speaker_order"], six)
        self.assertEqual(dispatch["roster"], six)
        self.assertNotIn("RINRIN", presentation["members"])
        self.assertNotIn("RINRIN", dispatch["members"])

    def test_malformed_state(self):
        with self.assertRaises(ValueError):
            scamp.select(5, context="casual", last_turn=5)
        with self.assertRaises(ValueError):
            scamp.select(5, context="casual", roll=1)


if __name__ == "__main__":
    unittest.main()
