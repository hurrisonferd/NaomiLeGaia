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
    def test_deployed_sha_and_registered_post_are_reported(self):
        routes = [
            SimpleNamespace(path="/gaiaos/memory/readiness", methods={"POST"}),
            SimpleNamespace(path="/health", methods={"GET"}),
        ]
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "stage8-fixture-sha"}), patch.object(
            carrier.app, "routes", routes
        ):
            response = carrier.health()
        self.assertEqual(response["status"], "ok")
        proof = response["deployment_proof"]
        self.assertEqual(proof["source_commit"], "stage8-fixture-sha")
        self.assertTrue(proof["source_commit_verified"])
        self.assertTrue(proof["stage7_readiness_route_registered"])
        self.assertNotIn("memory_records", response)
        self.assertNotIn("database_url", str(response).lower())

    def test_absent_commit_and_route_are_explicit_unknowns(self):
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": ""}), patch.object(
            carrier.app, "routes", [SimpleNamespace(path="/health", methods={"GET"})]
        ):
            proof = carrier.health()["deployment_proof"]
        self.assertIsNone(proof["source_commit"])
        self.assertFalse(proof["source_commit_verified"])
        self.assertFalse(proof["stage7_readiness_route_registered"])

    def test_get_only_route_cannot_masquerade_as_readiness(self):
        with patch.object(
            carrier.app, "routes",
            [SimpleNamespace(path="/gaiaos/memory/readiness", methods={"GET"})],
        ):
            self.assertFalse(
                carrier.health()["deployment_proof"]["stage7_readiness_route_registered"]
            )


if __name__ == "__main__":
    unittest.main()
