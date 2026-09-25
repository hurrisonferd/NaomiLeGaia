"""Tests for the public, no-secret Stage 9F live deployment verifier."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import gaiaos_stage9f_deployment_verify as verify


def passing_health(commit: str = "ci-stage9f-commit") -> dict:
    return {
        "status": "ok",
        "service": "gaiaos-carrier",
        "authorization_config": {
            "api_key_loaded": True,
            "key_material_disclosed": False,
        },
        "openai_configured": True,
        "openai_key_outer_whitespace_normalized": False,
        "openai_model_configured": True,
        "openai_model_outer_whitespace_normalized": False,
        "deployment_proof": {
            "source_commit": commit,
            "source_commit_verified": True,
            "stage7_readiness_route_registered": True,
            "stage9f_semantic_shadow_route_registered": True,
        },
    }


class Stage9FLiveDeploymentVerifierTests(unittest.TestCase):
    def test_exact_public_health_contract_passes_without_effects(self):
        result = verify.evaluate_health(
            passing_health(), "ci-stage9f-commit"
        )
        self.assertEqual(result["status"], "PASS_LIVE_HEALTH_PRECONDITIONS")
        self.assertTrue(
            result["safe_to_request_separate_semantic_shadow_authorization"]
        )
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["semantic_shadow_invoked"])
        self.assertFalse(result["memory_read_performed"])
        self.assertFalse(result["model_call_performed"])
        self.assertEqual(result["writes_performed"], [])
        self.assertFalse(result["bigbang_activation_performed"])

    def test_wrong_live_commit_holds(self):
        result = verify.evaluate_health(
            passing_health("old-live-commit"), "intended-new-commit"
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["checks"]["source_commit_matches"])
        self.assertFalse(
            result["safe_to_request_separate_semantic_shadow_authorization"]
        )

    def test_every_required_precondition_fails_closed(self):
        fields = (
            ("status", "down"),
            ("service", "other-service"),
            ("authorization_config.api_key_loaded", False),
            ("authorization_config.key_material_disclosed", True),
            ("openai_configured", False),
            ("openai_model_configured", False),
            ("deployment_proof.source_commit_verified", False),
            ("deployment_proof.stage7_readiness_route_registered", False),
            ("deployment_proof.stage9f_semantic_shadow_route_registered", False),
        )
        for field, value in fields:
            payload = passing_health()
            target = payload
            parts = field.split(".")
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = value
            with self.subTest(field=field):
                result = verify.evaluate_health(payload, "ci-stage9f-commit")
                self.assertEqual(result["status"], "HOLD")
                self.assertFalse(
                    result["safe_to_request_separate_semantic_shadow_authorization"]
                )

    def test_normalization_observations_are_informational_not_secret(self):
        payload = passing_health()
        payload["openai_key_outer_whitespace_normalized"] = True
        payload["openai_model_outer_whitespace_normalized"] = True
        result = verify.evaluate_health(payload, "ci-stage9f-commit")
        self.assertEqual(result["status"], "PASS_LIVE_HEALTH_PRECONDITIONS")
        self.assertTrue(
            result["configuration_observations"][
                "openai_key_outer_whitespace_normalized"
            ]
        )
        self.assertTrue(
            result["configuration_observations"][
                "openai_model_outer_whitespace_normalized"
            ]
        )

    def test_network_or_parse_failure_returns_redacted_hold(self):
        with patch.object(
            verify, "fetch_health", side_effect=ValueError("private fixture detail")
        ):
            result = verify.verify_live("ci-stage9f-commit")
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["error_type"], "ValueError")
        self.assertNotIn("private fixture detail", repr(result))
        self.assertFalse(result["model_call_performed"])
        self.assertFalse(result["memory_read_performed"])
        self.assertEqual(result["writes_performed"], [])

    def test_empty_expected_commit_is_never_accepted(self):
        with self.assertRaises(ValueError):
            verify.evaluate_health(passing_health(), "   ")


if __name__ == "__main__":
    unittest.main()
