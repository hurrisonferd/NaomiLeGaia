"""Stage 8: public route/deployed-revision evidence without secrets or memory reads."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import gaiaos_api as carrier


class DeploymentProofTests(unittest.TestCase):
    def test_environment_owner_key_normalization_without_secret_disclosure(self):
        from fastapi import HTTPException
        samples = (
            (None, None), ("", ""), ("   ", "   "),
            (" key-with-leading-and-trailing-spaces ", "key-with-leading-and-trailing-spaces"),
            ("\\nkey-no-surrounding-whitespace\\t", "\\nkey-no-surrounding-whitespace\\t"),
            ("key with internal space", "key with internal space"),
        )
        for raw, expected in samples:
            with self.subTest(raw_present=raw is not None):
                self.assertEqual(carrier._normalized_owner_key(raw), expected)
        # A genuinely padded environment key should authenticate when the
        # browser has trimmed its copied value, but not permit arbitrary keys.
        with patch.object(carrier, "API_KEY", carrier._normalized_owner_key(
            "  ci-only-owner-key  "
        )):
            carrier._authorize("Bearer ci-only-owner-key")
            with self.assertRaises(HTTPException) as denied:
                carrier._authorize("Bearer wrong-ci-key")
            self.assertEqual(denied.exception.status_code, 401)
        with patch.object(carrier, "API_KEY", "   "):
            with self.assertRaises(HTTPException) as invalid:
                carrier._authorize("Bearer    ")
            self.assertEqual(invalid.exception.status_code, 503)

    def test_public_configuration_proof_contains_no_key_material(self):
        with patch.object(carrier, "API_KEY", "private-test-sentinel"), patch.object(
            carrier, "AUTH_KEY_WHITESPACE_NORMALIZED", True
        ):
            proof = carrier.health()["authorization_config"]
        self.assertTrue(proof["api_key_loaded"])
        self.assertTrue(proof["environment_outer_whitespace_normalized"])
        self.assertFalse(proof["key_material_disclosed"])
        self.assertNotIn("private-test-sentinel", repr(proof))

    def test_openai_health_proof_requires_nonblank_key(self):
        for raw, expected in ((None, False), ("", False), ("   ", False), ("ci-provider-key", True)):
            with self.subTest(raw_present=raw is not None), patch.object(
                carrier, "OPENAI_API_KEY", raw
            ):
                self.assertIs(carrier.health()["openai_configured"], expected)

    def test_deployed_sha_and_registered_post_are_reported(self):
        routes = [
            SimpleNamespace(path="/gaiaos/memory/readiness", methods={"POST"}),
            SimpleNamespace(path="/gaiaos/memory/augury-semantic-shadow", methods={"POST"}),
            SimpleNamespace(path="/health", methods={"GET"}),
        ]
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "stage8-fixture-sha"}), patch.object(
            carrier.app.router, "routes", routes
        ):
            response = carrier.health()
        self.assertEqual(response["status"], "ok")
        proof = response["deployment_proof"]
        self.assertEqual(proof["source_commit"], "stage8-fixture-sha")
        self.assertTrue(proof["source_commit_verified"])
        self.assertTrue(proof["stage7_readiness_route_registered"])
        self.assertTrue(proof["stage9f_semantic_shadow_route_registered"])
        self.assertNotIn("memory_records", response)
        self.assertNotIn("database_url", str(response).lower())

    def test_absent_commit_and_route_are_explicit_unknowns(self):
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": ""}), patch.object(
            carrier.app.router, "routes", [SimpleNamespace(path="/health", methods={"GET"})]
        ):
            proof = carrier.health()["deployment_proof"]
        self.assertIsNone(proof["source_commit"])
        self.assertFalse(proof["source_commit_verified"])
        self.assertFalse(proof["stage7_readiness_route_registered"])
        self.assertFalse(proof["stage9f_semantic_shadow_route_registered"])

    def test_get_only_route_cannot_masquerade_as_readiness(self):
        with patch.object(
            carrier.app.router, "routes",
            [SimpleNamespace(path="/gaiaos/memory/readiness", methods={"GET"})],
        ):
            self.assertFalse(
                carrier.health()["deployment_proof"]["stage7_readiness_route_registered"]
            )


if __name__ == "__main__":
    unittest.main()
