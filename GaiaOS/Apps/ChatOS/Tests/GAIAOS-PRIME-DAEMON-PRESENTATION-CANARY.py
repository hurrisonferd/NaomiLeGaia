#!/usr/bin/env python3
"""Unit and source-integration regression canary for canonical six-speaker presentation.

Read-only: no model, network, MemoryOS, E-LANE or head-pat mutation.
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "api"))
import gaiaos_presentation_guard as guard

SPEC_PATH = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json"
EXPR_PATH = ROOT / "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json"
STATIC_PATH = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/STATIC-IDENTITY-EMOJI.v1.json"
PROFILES_PATH = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"
API_PATH = ROOT / "api/gaiaos_api.py"
SOLO_PATH = ROOT / "api/solo_chat_runtime.py"
BOOT_PATH = ROOT / "api/gaiaos_app.py"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PresentationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = (read(SPEC_PATH), read(EXPR_PATH), read(STATIC_PATH), read(PROFILES_PATH))
        cls.roster = guard.validate_sources(*cls.sources)

    def check(self, text, expected=()):
        return guard.validate_output(text, *self.sources, expected_members=expected)

    def test_01_six_member_canonical_source_agreement(self):
        self.assertEqual(
            self.roster, ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
        )
        expected = {
            "VERA": "46 · VERA 💚 🦋 (˘‿˘)",
            "ANVIL": "58 · ANVIL 💗 ⌚ (¬‿¬)",
            "SELENE": "60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)",
            "ORIN": "56 · ORIN 🩵 🪐 (☆▽☆)",
            "KESTREL": "90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و",
            "NIMUE": "62 · NIMUE 💙 🍄 (－‸ლ)",
        }
        for name, header in expected.items():
            with self.subTest(name=name):
                self.assertEqual(guard.canonical_header(name, *self.sources[:2]), header)

    def test_02_full_cast_valid_and_accent_provenance(self):
        output = "\n\n".join(
            guard.canonical_header(name, *self.sources[:2]) + "\nUnique content."
            for name in self.roster
        )
        receipt = self.check(output, self.roster)
        self.assertEqual(receipt["speaker_count"], 6)
        for card in receipt["speakers"]:
            self.assertEqual(
                card["accent"], self.sources[0]["members"][card["member"]]["accent"]
            )

    def test_03_wrong_headers_observed_in_real_conversation_fail_closed(self):
        bad = [
            "46 · VERA 💚 🐍 (˘‿˘)",
            "58 · ANVIL 🖤 ⚒️ (ಠ_ಠ)",
            "60 · SELENE 💜 🎛️ (˶ᵔ ᵕ ᵔ˶)",
            "62 · NIMUE 🤍 🌙 (－‸ლ)",
            "90 · KESTREL 💖 🏍️ (✧ω✧)",
        ]
        for header in bad:
            with self.subTest(header=header):
                with self.assertRaises(guard.PresentationGuardError):
                    self.check(header + "\nContent.")

    def test_04_missing_number_marker_kaomoji_or_markdown_fails(self):
        bad = [
            "VERA 💚 🦋 (˘‿˘)",
            "46 · VERA 💚 🦋",
            "73 · VERA 💚 🦋 (˘‿˘)",
            "46 · VERA 🦋 💚 (˘‿˘)",
            "46 · VERA 💚 🦋 (˘‿˘) (¬_¬)",
            "## 46 · VERA 💚 🦋 (˘‿˘)",
            "**46 · VERA 💚 🦋 (˘‿˘)**",
        ]
        for header in bad:
            with self.subTest(header=header):
                with self.assertRaises(guard.PresentationGuardError):
                    self.check(header + "\nContent.")

    def test_05_dynamic_expression_allowlist_and_default_fallback(self):
        for name in self.roster:
            expr = self.sources[1]["members"][name]
            for state, value in expr["expressions"].items():
                header = guard.canonical_header(name, *self.sources[:2], expression_state=state)
                self.assertTrue(header.endswith(value))
                self.assertEqual(self.check(header + "\nContent.")["speaker_count"], 1)
            self.assertEqual(
                guard.canonical_header(name, *self.sources[:2], expression_state="UNREGISTERED"),
                guard.canonical_header(name, *self.sources[:2]),
            )

    def test_06_explicit_cast_selection_and_omissions(self):
        self.assertEqual(
            guard.expected_members_from_request("EVERYONE, REPORT IN", self.roster), self.roster
        )
        self.assertEqual(
            guard.expected_members_from_request("COUNCIL EVERYONE", self.roster), self.roster
        )
        self.assertEqual(
            guard.expected_members_from_request("ASK NIMUE", self.roster), ("NIMUE",)
        )
        self.assertEqual(
            guard.expected_members_from_request("What does Vera think about this?", self.roster), ()
        )
        with self.assertRaises(guard.PresentationGuardError):
            self.check(guard.canonical_header("ORIN", *self.sources[:2]) + "\nHi.", self.roster)
        with self.assertRaises(guard.PresentationGuardError):
            self.check("Unattributed chat reply", self.roster)

    def test_07_solo_to_duo_to_full_to_solo(self):
        for selected in [
            ("ORIN",),
            ("ORIN", "KESTREL"),
            self.roster,
            ("KESTREL",),
        ]:
            output = "\n".join(
                guard.canonical_header(n, *self.sources[:2]) + "\nContent."
                for n in selected
            )
            self.assertEqual(self.check(output, selected)["speaker_count"], len(selected))

    def test_08_solo_renderer_inserts_header_and_rejects_cross_member(self):
        result, receipt = guard.render_solo("Content only.", "ORIN", *self.sources)
        self.assertTrue(result.startswith(guard.canonical_header("ORIN", *self.sources[:2])))
        self.assertEqual(receipt["speaker_count"], 1)
        result2, receipt2 = guard.render_solo(result, "ORIN", *self.sources)
        self.assertEqual(result2, result)
        self.assertEqual(receipt2["speaker_count"], 1)
        with self.assertRaises(guard.PresentationGuardError):
            guard.render_solo("90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و\nHi.", "ORIN", *self.sources)
        with self.assertRaises(guard.PresentationGuardError):
            guard.render_solo("56 · ORIN 🩵 🪐 (¬‿¬)\nHi.", "ORIN", *self.sources)

    def test_09_separate_member_source_drift_rejected(self):
        tests = [
            (0, lambda x: x["members"]["VERA"].update(heart="💜")),
            (1, lambda x: x["members"]["ANVIL"].update(default="")),
            (2, lambda x: x["members"]["SELENE"].update(static_interest_emoji="🍞")),
            (3, lambda x: x["members"]["NIMUE"].update(accent="#ff00ff")),
            (3, lambda x: x["members"]["ORIN"].update(gematria_number=99)),
        ]
        for idx, mutate in tests:
            args = [copy.deepcopy(x) for x in self.sources]
            mutate(args[idx])
            with self.subTest(source_index=idx):
                with self.assertRaises(guard.PresentationGuardError):
                    guard.validate_sources(*args)

    def test_10_plain_ordinary_chat_and_code_samples_unaffected(self):
        self.assertEqual(self.check("Today we should review the receipts.")["speaker_count"], 0)
        sample = "Here is a historical incorrect example:\n" + "\x60" * 3 + "\n46 · VERA 💚 🐍 (˘‿˘)\n" + "\x60" * 3
        self.assertEqual(self.check(sample)["speaker_count"], 0)
        self.assertEqual(self.check("> 58 · ANVIL 🖤 ⚒️ (ಠ_ಠ)")["speaker_count"], 0)

    def test_11_pinned_runtime_wiring_present(self):
        api = API_PATH.read_text(encoding="utf-8")
        solo = SOLO_PATH.read_text(encoding="utf-8")
        boot = BOOT_PATH.read_text(encoding="utf-8")
        self.assertIn("gaiaos_presentation_guard.validate_output(", api)
        self.assertIn("expected_members_from_request(", api)
        self.assertIn("gaiaos_presentation_guard.render_solo(", solo)
        self.assertIn('checks["four_source_identity_alignment"]', boot)


if __name__ == "__main__":
    unittest.main(verbosity=2)
