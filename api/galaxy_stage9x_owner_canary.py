"""Stage 9X: explicitly invoked OWNER-LOCAL signed staging canary operator.

No HTTP route, workflow with credentials, production connection, archive import,
gravity mutation, E-LANE write or BIGBANG unlock. A local HMAC check establishes
only possession of the supplied key, NOT independently verified owner identity.
No remote Turso connection is made until a strict signed envelope and explicit
operator confirmations have passed; a read-only preflight precedes the canary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Callable

import galaxy_stage9v_operator_preflight as readonly
import galaxy_stage9v_staging_turso as canary

SCHEMA = "gaiaos.galaxy.stage9x.owner-local-canary.v1"
_ROOT = Path(__file__).resolve().parents[1]
CONFIG = readonly.CONFIG
_MAX_MANIFEST_BYTES = 8192


def _report(status: str, *, readiness: str = "NOT_RUN",
            canary_status: str = "NOT_RUN", write_outcome_unknown: bool = False,
            local_hmac_valid: bool = False) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status,
        "read_only_preflight_status": readiness,
        "stage9v_canary_status": canary_status,
        "local_hmac_manifest_verified": local_hmac_valid,
        "staging_turso_reopen_observed": False,
        "provider_database_separation_independently_verified": False,
        "live_owner_identity_verified": False,
        "production_database_accessed": False,
        "production_memory_modified": False,
        "gravity_modified": False, "e_lanes_modified": False,
        "mode_control_modified": False, "bigbang_activated": False,
        "archive_import_performed": False, "memory_backfill_performed": False,
        "staging_write_outcome_unknown": write_outcome_unknown,
        "staging_canary_written": False, "writes_performed": (
            ["STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"] if write_outcome_unknown else []
        ),
        "proof_boundary": (
            "Source/owner-local operator evidence only. Provider-level database "
            "identity and actual owner authentication require separate evidence. "
            "Neither a local signature nor a staging canary authorizes release."
        ),
    }


def _expected(config: dict[str, str], manifest: Any) -> dict[str, Any] | None:
    """Construct the entire permitted signed action BEFORE connecting anywhere."""
    if not isinstance(manifest, dict):
        return None
    stage = canary._canonical_url(config.get("staging_url"))
    prod = canary._canonical_url(config.get("production_url"))
    marker = config.get("expected_staging_id")
    token = config.get("staging_token")
    run = manifest.get("run_id")
    nonce = manifest.get("nonce_sha256")
    if (stage is None or prod is None or stage == prod
            or not canary._valid_id(marker)
            or not isinstance(token, str) or not 16 <= len(token) <= 8192
            or not isinstance(run, str) or canary._RUN.fullmatch(run) is None
            or not isinstance(nonce, str) or canary._HEX.fullmatch(nonce) is None):
        return None
    return {
        "schema": canary.APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": canary.TARGET, "action": "WRITE_ONE_STAGING_CANARY",
        "expected_staging_id": marker,
        "staging_url_sha256": hashlib.sha256(stage.encode()).hexdigest(),
        "production_url_sha256": hashlib.sha256(prod.encode()).hexdigest(),
        "run_id": run, "nonce_sha256": nonce,
    }


def execute_owner_local_canary(
    *, config: dict[str, str], approval: Any, signature_hex: str,
    approval_key: bytes, confirm_provider_identity: bool,
    confirm_separate_owner_approval: bool, confirm_one_canary: bool,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Only the explicit offline operator call can reach the staging connector.

    confirm_provider_identity is an operator assertion, NOT machine verification
    of Turso's control-plane database identity or alias separation.
    An injected connector is a TEST and can never earn the remote-proof status.
    """
    if not all((confirm_provider_identity, confirm_separate_owner_approval,
                confirm_one_canary)):
        return _report("HOLD_EXPLICIT_OPERATOR_CONFIRMATIONS_REQUIRED")
    expected = _expected(config, approval)
    if expected is None or not canary._approval_ok(
        approval, signature_hex, approval_key, expected
    ):
        return _report("HOLD_SIGNED_EXACT_STAGING_ACTION_REQUIRED")
    # Preflight uses SELECT only, closes the connection and does not allow
    # reading production. The canary reconnects and revalidates identity twice.
    pre = readonly.check_staging_readiness(**config, connector=connector)
    if pre.get("status") != "PASS_STAGING_READINESS_READ_ONLY":
        return _report(
            "HOLD_READ_ONLY_PREFLIGHT_NOT_PASSED",
            readiness=str(pre.get("status", "HOLD_UNKNOWN")),
            local_hmac_valid=True,
        )
    result = canary.prove_staging_turso_canary(
        **config, run_id=approval["run_id"],
        nonce_sha256=approval["nonce_sha256"],
        approval=approval, signature_hex=signature_hex,
        approval_key=approval_key, connector=connector,
    )
    stage_status = result.get("status", "HOLD_UNKNOWN")
    unknown = result.get("writes_performed") == [
        "STAGING_CANARY_WRITE_OUTCOME_UNVERIFIED"
    ]
    if stage_status != "PASS_STAGING_CANARY_REOPEN_READBACK":
        return _report(
            "HOLD_CANARY_NOT_VERIFIED", readiness=pre["status"],
            canary_status=stage_status, write_outcome_unknown=unknown,
            local_hmac_valid=True,
        )
    remote = (
        connector is None
        and pre.get("staging_turso_remotely_observed") is True
        and pre.get("test_connector_injected") is False
        and result.get("staging_turso_verified") is True
        and result.get("test_connector_injected") is False
        and result.get("reopen_readback_verified") is True
    )
    out = _report(
        "PASS_REMOTE_STAGING_CANARY_REOPEN" if remote
        else "HOLD_LOCAL_FIXTURE_NOT_REMOTE",
        readiness=pre["status"], canary_status=stage_status,
        local_hmac_valid=True,
    )
    writes = result.get("writes_performed")
    out["writes_performed"] = (
        ["ONE_SEPARATE_STAGING_CANARY"]
        if writes == ["ONE_SEPARATE_STAGING_CANARY"] else []
    )
    out["staging_canary_written"] = writes == ["ONE_SEPARATE_STAGING_CANARY"]
    out["staging_turso_reopen_observed"] = remote
    out["idempotent_replay"] = result.get("idempotent") is True
    out["canary_sha256"] = result.get("canary_sha256")
    # These statements are deliberately NOT upgraded by the operator's
    # confirmation flags. Provider control-plane proof is an external gate.
    return out


def _private_file(path: str, max_size: int) -> bytes:
    """Require a regular, owner-only local file OUTSIDE the current repo."""
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ValueError("symlink input forbidden")
    resolved = candidate.resolve(strict=True)
    if resolved == _ROOT or _ROOT in resolved.parents:
        raise ValueError("private inputs cannot live in source repository")
    info = resolved.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
            or info.st_size == 0 or info.st_size > max_size):
        raise ValueError("unsafe private input file")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ValueError("private input not owned by current user")
    raw = resolved.read_bytes()
    if not raw or len(raw) > max_size:
        raise ValueError("private input size changed")
    return raw


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest field")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Owner-local staging-only signed one-canary runner. NO PRODUCTION."
    )
    parser.add_argument("--approval-json", required=True)
    parser.add_argument("--signature-file", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--confirm-provider-identity", action="store_true")
    parser.add_argument("--confirm-separate-owner-approval", action="store_true")
    parser.add_argument("--confirm-one-staging-canary", action="store_true")
    args = parser.parse_args(argv)
    if not all((
        args.confirm_provider_identity, args.confirm_separate_owner_approval,
        args.confirm_one_staging_canary,
    )):
        print(json.dumps(_report("HOLD_EXPLICIT_OPERATOR_CONFIRMATIONS_REQUIRED")))
        return 2
    config = {name: os.environ.get(env, "") for name, env in CONFIG.items()}
    if any(not value for value in config.values()):
        print(json.dumps(_report("HOLD_STAGING_ONLY_CONFIGURATION_MISSING")))
        return 2
    try:
        approval = json.loads(
            _private_file(args.approval_json, _MAX_MANIFEST_BYTES).decode("utf-8"),
            object_pairs_hook=_pairs_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
        signature = _private_file(args.signature_file, 128).decode("ascii").strip()
        key = _private_file(args.key_file, 1024)
    except (OSError, UnicodeError, ValueError, TypeError):
        print(json.dumps(_report("HOLD_PRIVATE_SIGNED_INPUT_INVALID")))
        return 2
    result = execute_owner_local_canary(
        config=config, approval=approval, signature_hex=signature,
        approval_key=key, confirm_provider_identity=True,
        confirm_separate_owner_approval=True, confirm_one_canary=True,
    )
    # Only the fixed, redacted allowlist returned by execute_owner_local_canary
    # reaches stdout. Never log private config, manifest, signature or key.
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_REMOTE_STAGING_CANARY_REOPEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
