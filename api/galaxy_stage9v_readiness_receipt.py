"""Stage 9V: emit a narrow, non-sensitive CI artifact from READ-ONLY preflight.

Never copy URL hashes, staging identifiers, tokens, source snippets or raw error
messages into the GitHub artifact. This receipt is a GitHub workflow observation,
NOT proof of independent provider identity or real owner authentication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "gaiaos.galaxy.stage9v.readonly-ci-receipt.v1"
REPORT_SCHEMA = "gaiaos.galaxy.stage9v.operator-readiness.v1"
PASS = "PASS_STAGING_READINESS_READ_ONLY"
MAX_REPORT_BYTES = 8192
SHA = re.compile(r"[0-9a-f]{40}\Z")
RUN = re.compile(r"[0-9]{1,24}\Z")

# Never hash arbitrarily extended private reports into an exported receipt.
REPORT_KEYS = frozenset({
    "schema", "status", "execution", "reads_performed", "writes_performed",
    "production_turso_accessed", "memory_records_modified",
    "gravity_modified", "e_lanes_modified", "mode_control_modified",
    "canary_written", "staging_turso_remotely_observed",
    "provider_database_separation_independently_verified",
    "live_owner_authentication_verified", "staging_url_sha256",
    "production_url_sha256", "staging_uuid_sha256",
    "staging_marker_readback_verified", "canary_table_select_verified",
    "test_connector_injected", "next_gate", "error_type",
    "missing_variable_names",
})


def make_receipt(report: Any, *, commit: str, run_id: str) -> dict[str, Any]:
    """Allowlist fields only. Fail closed on contradictory or missing proof."""
    if not isinstance(commit, str) or SHA.fullmatch(commit) is None:
        raise ValueError("unverified source commit")
    if not isinstance(run_id, str) or RUN.fullmatch(run_id) is None:
        raise ValueError("invalid workflow run")
    if not isinstance(report, dict):
        raise ValueError("preflight report must be an object")
    if any(not isinstance(key, str) for key in report) or not set(report) <= REPORT_KEYS:
        raise ValueError("unrecognized report fields, possibly sensitive")
    status = report.get("status")
    if not isinstance(status, str) or not re.fullmatch(r"(PASS|HOLD)_[A-Z0-9_]{1,100}", status):
        raise ValueError("unrecognized preflight result")
    if report.get("schema") != REPORT_SCHEMA or report.get("execution") != "READ_ONLY":
        raise ValueError("preflight schema or execution mismatch")
    assert_zero_effect = all((
        report.get("writes_performed") == [],
        report.get("production_turso_accessed") is False,
        report.get("memory_records_modified") is False,
        report.get("gravity_modified") is False,
        report.get("e_lanes_modified") is False,
        report.get("mode_control_modified") is False,
        report.get("canary_written") is False,
        report.get("provider_database_separation_independently_verified") is False,
        report.get("live_owner_authentication_verified") is False,
    ))
    remote_pass = (
        status == PASS and assert_zero_effect
        and report.get("staging_turso_remotely_observed") is True
        and report.get("test_connector_injected") is False
        and report.get("staging_marker_readback_verified") is True
        and report.get("canary_table_select_verified") is True
        and report.get("reads_performed") == 2
    )
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")
    receipt = {
        "schema": SCHEMA,
        "status": "PASS_REMOTE_STAGING_READ_ONLY" if remote_pass else "HOLD_UNVERIFIED",
        "preflight_status": status,
        "execution": "READ_ONLY",
        "source_commit": commit,
        "github_run_id": run_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "preflight_report_sha256": hashlib.sha256(canonical).hexdigest(),
        "preflight_read_count": report.get("reads_performed") if isinstance(
            report.get("reads_performed"), int
        ) and not isinstance(report.get("reads_performed"), bool) else None,
        "remote_staging_select_observed": remote_pass,
        "writes_performed": [],
        "source_file_or_token_included": False,
        "real_owner_authentication_verified": False,
        "provider_database_separation_independently_verified": False,
        "staging_canary_written": False,
        "production_records_modified": False,
        "release_activated": False,
        "proof_boundary": (
            "Remote staging identity and canary-table SELECT only. Independent "
            "provider database/alias separation, owner authentication, "
            "staging write/readback, restart durability and production release "
            "are NOT proven."
        ),
    }
    receipt["receipt_sha256"] = hashlib.sha256(json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Whitelist-only readiness receipt; never log private config."
    )
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    destination = Path(args.output)
    try:
        raw = Path(args.report).read_bytes()
        if len(raw) > MAX_REPORT_BYTES:
            raise ValueError("report too large")
        report = json.loads(raw.decode("utf-8"))
        receipt = make_receipt(report, commit=args.commit, run_id=args.run_id)
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        # Never propagate raw exception strings or the report to action logs.
        print(json.dumps({"status": "HOLD_RECEIPT_INVALID", "error_type": type(exc).__name__}))
        return 2
    try:
        destination.write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        print(json.dumps({"status": "HOLD_RECEIPT_WRITE_FAILED", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps({
        "status": receipt["status"],
        "github_run_id": receipt["github_run_id"],
        "source_commit": receipt["source_commit"],
        "release_activated": False,
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))
    return 0 if receipt["status"] == "PASS_REMOTE_STAGING_READ_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
