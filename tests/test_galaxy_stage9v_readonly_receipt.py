"""Stage 9V: validate redacted evidence and owner-only workflow trigger.

Tests operate on synthetic READ-ONLY report objects. There are no real Turso
tokens, staging endpoints, provider calls, canary writes or release actions.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import galaxy_stage9v_readiness_receipt as receipt
import galaxy_stage9v_operator_preflight as readiness

COMMIT = "a" * 40
RUN = "36336191238"
PRIVATE = "PRIVATE-TOKEN-DO-NOT-ECHO"


def good_report():
    result = readiness._base("PASS_STAGING_READINESS_READ_ONLY")
    result.update({
        "reads_performed": 2,
        "staging_turso_remotely_observed": True,
        "test_connector_injected": False,
        "staging_marker_readback_verified": True,
        "canary_table_select_verified": True,
        "staging_url_sha256": hashlib.sha256(b"separately pinned staging").hexdigest(),
        "production_url_sha256": hashlib.sha256(b"independently pinned production").hexdigest(),
        "staging_uuid_sha256": hashlib.sha256(b"owner-pinned UUID").hexdigest(),
        "next_gate": "SIGNED_SINGLE_STAGING_CANARY_AFTER_INDEPENDENT_PROVIDER_IDENTITY_CHECK",
    })
    return result


class Stage9VReadinessReceiptTests(unittest.TestCase):
    def test_genuine_shape_remote_select_produces_narrow_receipt_only(self):
        source = good_report()
        result = receipt.make_receipt(source, commit=COMMIT, run_id=RUN)
        self.assertEqual(result["status"], "PASS_REMOTE_STAGING_READ_ONLY")
        self.assertEqual(result["source_commit"], COMMIT)
        self.assertEqual(result["github_run_id"], RUN)
        self.assertTrue(result["remote_staging_select_observed"])
        self.assertFalse(result["release_activated"])
        self.assertFalse(result["real_owner_authentication_verified"])
        self.assertFalse(result["provider_database_separation_independently_verified"])
        self.assertFalse(result["staging_canary_written"])
        self.assertEqual(result["writes_performed"], [])
        self.assertNotIn("staging_url_sha256", result)
        self.assertNotIn("production_url_sha256", result)
        self.assertNotIn("staging_uuid_sha256", result)
        self.assertNotIn("token", json.dumps(result).lower().replace("source_file_or_token_included", ""))
        self.assertEqual(len(result["receipt_sha256"]), 64)

    def test_mocked_local_connector_cannot_claim_remote_staging(self):
        source = good_report()
        source["test_connector_injected"] = True
        source["staging_turso_remotely_observed"] = False
        result = receipt.make_receipt(source, commit=COMMIT, run_id=RUN)
        self.assertEqual(result["status"], "HOLD_UNVERIFIED")
        self.assertFalse(result["remote_staging_select_observed"])

    def test_fail_closed_for_missing_reads_effects_schema_or_endpoint_fingerprints(self):
        base = good_report()
        mutations = (
            {"reads_performed": 1},
            {"reads_performed": True},
            {"writes_performed": ["MALICIOUS-STAGING-INSERT"]},
            {"production_turso_accessed": True},
            {"canary_written": True},
            {"memory_records_modified": True},
            {"e_lanes_modified": True},
            {"mode_control_modified": True},
            {"gravity_modified": True},
            {"staging_marker_readback_verified": False},
            {"canary_table_select_verified": False},
            {"staging_turso_remotely_observed": False},
            {"test_connector_injected": True},
            {"staging_url_sha256": base["production_url_sha256"]},
            {"staging_uuid_sha256": "not-sha256"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                altered = {**base, **mutation}
                result = receipt.make_receipt(altered, commit=COMMIT, run_id=RUN)
                self.assertEqual(result["status"], "HOLD_UNVERIFIED")
                self.assertFalse(result["remote_staging_select_observed"])
                self.assertFalse(result["release_activated"])
        for field, value in (
            ("schema", "fake-schema"),
            ("execution", "WRITE_ENABLED"),
            ("status", "PASS_NOT_AN_ALLOWED_STATUS?"),
        ):
            with self.subTest(field=field):
                altered = {**base, field: value}
                with self.assertRaises(ValueError):
                    receipt.make_receipt(altered, commit=COMMIT, run_id=RUN)

    def test_unknown_or_private_report_fields_never_enter_receipts(self):
        for extra, value in (
            ("staging_token", PRIVATE),
            ("raw_statement", "PRIVATE-MEMORY-LINE"),
            ("exception_message", "PRIVATE-TURSO-CREDENTIAL"),
        ):
            with self.subTest(extra=extra):
                altered = {**good_report(), extra: value}
                with self.assertRaises(ValueError):
                    receipt.make_receipt(altered, commit=COMMIT, run_id=RUN)

    def test_holds_are_never_promoted_to_remote_pass(self):
        report = readiness._base("HOLD_STAGING_IDENTITY_UNVERIFIED")
        report["reads_performed"] = 1
        response = receipt.make_receipt(report, commit=COMMIT, run_id=RUN)
        self.assertEqual(response["status"], "HOLD_UNVERIFIED")
        self.assertEqual(response["preflight_status"], "HOLD_STAGING_IDENTITY_UNVERIFIED")

    def test_commit_and_run_id_must_be_real_formats(self):
        report = good_report()
        for commit, run_id in (
            ("bad-commit", RUN), (COMMIT, "bad-run-id"), (COMMIT.upper(), RUN),
        ):
            with self.subTest(commit=commit, run_id=run_id):
                with self.assertRaises(ValueError):
                    receipt.make_receipt(report, commit=commit, run_id=run_id)

    def test_cli_writes_allowlisted_receipt_without_raw_private_data(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "raw-private.json"
            destination = Path(root) / "public-receipt.json"
            source.write_text(json.dumps(good_report()), encoding="utf-8")
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                code = receipt.main([
                    "--report", str(source), "--output", str(destination),
                    "--commit", COMMIT, "--run-id", RUN,
                ])
            self.assertEqual(code, 0)
            result = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS_REMOTE_STAGING_READ_ONLY")
            self.assertNotIn("staging_url_sha256", result)
            self.assertEqual(json.loads(sink.getvalue())["status"], result["status"])
            self.assertNotIn("owner-pinned UUID", destination.read_text())
            self.assertNotIn(PRIVATE, destination.read_text())

    def test_cli_rejects_private_extra_fields_and_oversize_no_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "raw-private.json"
            output = Path(root) / "public.json"
            private = {**good_report(), "staging_token": PRIVATE}
            for payload in (
                json.dumps(private).encode(),
                b"X" * (receipt.MAX_REPORT_BYTES + 1),
                b'{"schema":"invalid","status":"PASS_STAGING_READINESS_READ_ONLY"}',
            ):
                with self.subTest(size=len(payload)):
                    source.write_bytes(payload)
                    sink = io.StringIO()
                    with contextlib.redirect_stdout(sink):
                        code = receipt.main([
                            "--report", str(source), "--output", str(output),
                            "--commit", COMMIT, "--run-id", RUN,
                        ])
                    self.assertEqual(code, 2)
                    self.assertFalse(output.exists())
                    self.assertNotIn(PRIVATE, sink.getvalue())
                    self.assertEqual(json.loads(sink.getvalue())["status"], "HOLD_RECEIPT_INVALID")


class Stage9VManualWorkflowPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(
            (ROOT / ".github/workflows/galaxy-stage9v-real-staging-readonly.yml").read_text(
                encoding="utf-8"
            ), Loader=yaml.BaseLoader,
        )

    def test_manual_only_owner_main_explicit_choice(self):
        wf = self.workflow
        self.assertEqual(list(wf["on"]), ["workflow_dispatch"])
        self.assertEqual(wf["permissions"], {"contents": "read"})
        choices = wf["on"]["workflow_dispatch"]["inputs"]["confirmation"]
        self.assertEqual(choices["default"], "ABORT")
        self.assertEqual(choices["options"], ["ABORT", "STAGING_READ_ONLY"])
        jobs = wf["jobs"]
        self.assertEqual(set(jobs), {"verify-readonly-staging"})
        job = jobs["verify-readonly-staging"]
        for necessary in (
            "github.repository_owner == 'Ligeia621'",
            "github.repository != 'hurrisonferd/NaomiLeGaia'",
            "github.ref == 'refs/heads/main'",
            "github.actor == 'Ligeia621'",
            "github.triggering_actor == 'Ligeia621'",
            "github.run_attempt == 1",
            "inputs.confirmation == 'STAGING_READ_ONLY'",
        ):
            self.assertIn(necessary, job["if"])
        self.assertEqual(job["environment"], "gaiaos-stage9v-read-only")
        self.assertIn("github.repository_owner == 'Ligeia621'", job["if"])
        self.assertIn("github.repository != 'hurrisonferd/NaomiLeGaia'", job["if"])
        self.assertLessEqual(int(job["timeout-minutes"]), 5)

    def test_no_autotrigger_production_credentials_schema_or_write_code(self):
        steps = self.workflow["jobs"]["verify-readonly-staging"]["steps"]
        self.assertEqual(steps[0]["with"]["persist-credentials"], "false")
        probe_step = next(step for step in steps if "GAIAOS_STAGE9V_STAGING_TOKEN" in step.get("env", {}))
        self.assertEqual(
            set(probe_step["env"]),
            set(readiness.CONFIG.values()),
        )
        env_text = json.dumps(probe_step["env"])
        self.assertNotIn("TURSO_DATABASE_AUTH_TOKEN", env_text)
        self.assertNotIn("OPENAI_API_KEY", env_text)
        self.assertNotIn("GAIAOS_API_KEY", env_text)
        script = probe_step["run"]
        self.assertIn("galaxy_stage9v_operator_preflight.py --confirm-read-only", script)
        self.assertIn("galaxy_stage9v_readiness_receipt.py", script)
        self.assertNotIn("prove_staging_turso_canary", script)
        self.assertNotIn("INSERT INTO", script)
        self.assertNotIn("turso db", script)
        self.assertIn("set +x", script)
        self.assertIn("umask 077", script)
        artifact = next(step for step in steps if step.get("uses", "").startswith("actions/upload-artifact"))
        self.assertIn("stage9v-public-receipt.json", artifact["with"]["path"])
        self.assertNotIn("stage9v-private-report.json", artifact["with"]["path"])
        self.assertLessEqual(int(artifact["with"]["retention-days"]), 7)


if __name__ == "__main__":
    unittest.main()
