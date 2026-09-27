"""GALAXY Stage 9V: gated *separate staging Turso* identity/readback canary.

This module has no HTTP route and never touches memory_records, gravity, E-LANES
or mode control. Running it requires an out-of-band provisioned staging database,
independent credentials, a verified identity marker and a separately signed
single-canary approval. A successful isolated CI run is NOT live Turso proof.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlsplit

SCHEMA = "gaiaos.galaxy.stage9v.staging-turso-canary.v1"
APPROVAL_SCHEMA = "gaiaos.galaxy.stage9v.one-canary-approval.v1"
TARGET = "SEPARATE_STAGING_TURSO_CANARY_ONLY"
IDENTITY_SCHEMA = "gaiaos.galaxy.stage9v.staging-identity.v1"
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_RUN = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hold(status: str, *, error_type: str | None = None,
          committed_but_unverified: bool = False) -> dict[str, Any]:
    result = {
        "schema": SCHEMA, "status": status, "target": TARGET,
        "production_memory_records_modified": False,
        "production_gravity_modified": False, "e_lanes_modified": False,
        "mode_control_modified": False, "bigbang_activated": False,
        "writes_performed": (
            ["STAGING_CANARY_COMMITTED_READBACK_UNVERIFIED"]
            if committed_but_unverified else []
        ),
        "live_owner_identity_verified": False,
        "staging_turso_verified": False,
        "production_storage_identity_independently_verified": False,
        "proof_boundary": "No live owner login or production-database identity attestation.",
    }
    if error_type:
        result["error_type"] = error_type
    return result


def _canonical_url(url: Any) -> str | None:
    """Only accept explicit remote libSQL Turso host URLs without credentials."""
    if not isinstance(url, str) or len(url) > 500:
        return None
    try:
        parsed = urlsplit(url.strip())
        if (
            parsed.scheme not in ("libsql", "https")
            or not parsed.hostname or not parsed.hostname.endswith(".turso.io")
            or parsed.hostname == ".turso.io" or parsed.port is not None
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")
            or parsed.netloc.lower() != parsed.hostname.lower()
        ):
            return None
        return "https://" + parsed.hostname.lower()
    except (ValueError, TypeError):
        return None


def _valid_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value.lower() and uuid.UUID(value).version == 4
    except (ValueError, AttributeError):
        return False


def _row(cursor: Any) -> dict[str, Any] | None:
    names = [col[0] if isinstance(col, (tuple, list))
             else getattr(col, "name", str(col)) for col in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row) if hasattr(row, "keys") else dict(zip(names, row))


def _identity(conn: Any, expected_id: str) -> bool:
    try:
        row = _row(conn.execute(
            "SELECT schema,environment,database_id,authority,status "
            "FROM galaxy_stage9v_staging_identity",
        ))
    except Exception:
        return False
    return row == {
        "schema": IDENTITY_SCHEMA, "environment": "STAGING_ONLY",
        "database_id": expected_id, "authority": "NAOMI", "status": "ACTIVE",
    }


def _canary(conn: Any, run_id: str) -> dict[str, Any] | None:
    return _row(conn.execute(
        "SELECT run_id,nonce_sha256,database_id,created_at "
        "FROM galaxy_stage9v_canaries WHERE run_id=?",
        (run_id,),
    ))


def _approval_ok(approval: Any, signature_hex: Any, approval_key: Any,
                 expected: dict[str, Any]) -> bool:
    if (
        not isinstance(approval, dict) or approval != expected
        or not isinstance(approval_key, bytes) or len(approval_key) < 32
        or not isinstance(signature_hex, str)
        or _HEX.fullmatch(signature_hex) is None
    ):
        return False
    try:
        actual = hmac.new(approval_key, _bytes(approval), hashlib.sha256).hexdigest()
    except (ValueError, TypeError, OverflowError):
        return False
    return hmac.compare_digest(signature_hex, actual)


def _connect_live(url: str, token: str) -> Any:
    import libsql
    return libsql.connect(database=url, auth_token=token)


def prove_staging_turso_canary(
    *, staging_url: str, staging_token: str, production_url: str,
    expected_staging_id: str, run_id: str, nonce_sha256: str,
    approval: dict[str, Any], signature_hex: str, approval_key: bytes,
    connector: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Check separate staging identity, commit ONE canary, reopen and read back.

    connector is for isolated CI injection. Live operator code must call without
    connector and guard signing key and URL pins OUTSIDE user-supplied HTTP.
    The configured production URL comparison does NOT prove actual DB separation
    against a database alias; owner must separately verify target + token scope.
    """
    staging = _canonical_url(staging_url)
    production = _canonical_url(production_url)
    if staging is None or production is None or staging == production:
        return _hold("HOLD_STAGING_URL_NOT_SEPARATE_FROM_PRODUCTION")
    if not isinstance(staging_token, str) or not 16 <= len(staging_token) <= 8192:
        return _hold("HOLD_SEPARATE_STAGING_CREDENTIALS_MISSING")
    if not _valid_id(expected_staging_id):
        return _hold("HOLD_STAGING_ID_INVALID")
    if not isinstance(run_id, str) or _RUN.fullmatch(run_id) is None:
        return _hold("HOLD_RUN_ID_INVALID")
    if not isinstance(nonce_sha256, str) or _HEX.fullmatch(nonce_sha256) is None:
        return _hold("HOLD_NONCE_DIGEST_INVALID")
    expected = {
        "schema": APPROVAL_SCHEMA, "authority": "NAOMI",
        "target": TARGET, "action": "WRITE_ONE_STAGING_CANARY",
        "expected_staging_id": expected_staging_id,
        "staging_url_sha256": _sha(staging.encode()),
        "production_url_sha256": _sha(production.encode()),
        "run_id": run_id, "nonce_sha256": nonce_sha256,
    }
    if not _approval_ok(approval, signature_hex, approval_key, expected):
        return _hold("HOLD_OWNER_SIGNED_STAGING_APPROVAL_REQUIRED")
    connect = connector if connector is not None else _connect_live
    if not callable(connect):
        return _hold("HOLD_DRIVER_INVALID")

    conn = None
    committed = False
    duplicate = False
    created_at = None
    try:
        conn = connect(staging_url, staging_token)
        if not _identity(conn, expected_staging_id):
            return _hold("HOLD_STAGING_IDENTITY_NOT_VERIFIED")
        # Tables MUST already have been created independently by a staging
        # administrator. This probe never creates or alters schema.
        old = _canary(conn, run_id)
        if old is not None:
            if old["nonce_sha256"] != nonce_sha256 or old["database_id"] != expected_staging_id:
                return _hold("HOLD_STAGING_RUN_ID_CONFLICT")
            duplicate = True
            created_at = old["created_at"]
        else:
            conn.execute("BEGIN IMMEDIATE")
            # Concurrent duplicate invocation must not silently rewrite a row.
            old = _canary(conn, run_id)
            if old is not None:
                if old["nonce_sha256"] != nonce_sha256 or old["database_id"] != expected_staging_id:
                    conn.rollback()
                    return _hold("HOLD_STAGING_RUN_ID_CONFLICT")
                duplicate = True
                created_at = old["created_at"]
                conn.commit()
            else:
                created_at = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO galaxy_stage9v_canaries "
                    "(run_id,nonce_sha256,database_id,created_at) VALUES (?,?,?,?)",
                    (run_id, nonce_sha256, expected_staging_id, created_at),
                )
                conn.commit()
                committed = True
    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return _hold("HOLD_STAGING_CONNECT_OR_WRITE_FAILED",
                     error_type=type(exc).__name__, committed_but_unverified=committed)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # A new connection must independently retrieve exactly the previously
    # committed row. This proves reconnection readback, not replica/restart.
    again = None
    try:
        again = connect(staging_url, staging_token)
        if not _identity(again, expected_staging_id):
            return _hold("HOLD_REOPENED_STAGING_IDENTITY_CHANGED",
                         committed_but_unverified=committed)
        exact = _canary(again, run_id)
        if exact != {
            "run_id": run_id, "nonce_sha256": nonce_sha256,
            "database_id": expected_staging_id, "created_at": created_at,
        }:
            return _hold("HOLD_STAGING_CANARY_READBACK_CHANGED",
                         committed_but_unverified=committed)
    except Exception as exc:
        return _hold("HOLD_STAGING_REOPEN_READBACK_UNAVAILABLE",
                     error_type=type(exc).__name__, committed_but_unverified=committed)
    finally:
        if again is not None:
            try:
                again.close()
            except Exception:
                pass
    return {
        **_hold("PASS_STAGING_CANARY_REOPEN_READBACK"),
        "staging_turso_verified": connector is None,
        "test_connector_injected": connector is not None,
        "idempotent": duplicate,
        "writes_performed": [] if duplicate else ["ONE_SEPARATE_STAGING_CANARY"],
        "staging_identity_sha256": _sha(expected_staging_id.encode()),
        "canary_sha256": _sha(_bytes({
            "run_id": run_id, "nonce_sha256": nonce_sha256,
            "database_id": expected_staging_id, "created_at": created_at,
        })),
        "reopen_readback_verified": True,
        "schema_changes": False,
        "proof_boundary": (
            "Isolated fixture only; no Turso claim."
            if connector is not None else
            "Remote staging canary readback. Real owner login, production DB "
            "alias attestation, staged memory import, restart/replica durability "
            "and ordinary GaiaOS integration remain separate gates."
        ),
    }
