"""Stage-2 HEATDEATH control, intentionally independent of every GALAXY module.

This is the shared, durable, fail-closed MODE CONTROL ONLY, not yet a routed
application kill switch. Until ordinary chat, MCP and startup recovery are
wired and live-proven, BIGBANG re-entry is disabled in this module.

No implicit migration or write occurs while reading the mode. An explicitly
approved HEATDEATH request creates/updates one additive control table in the
existing configured database. Read failure and invalid configuration fail to
HEATDEATH, never to an invented BIGBANG success.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA = "gaiaos.memory-mode-control.v1"
TABLE = "gaiaos_memory_mode_control"
HEATDEATH = "HEATDEATH"
BIGBANG = "BIGBANG"
OVERRIDES = (
    "GAIAOS_FORCE_HEATDEATH",
    "GALAXY_FRONTDOOR_KILL_SWITCH",
    "GALAXY_PRODUCTION_PILOT_KILL_SWITCH",
)

_DDL = """
CREATE TABLE IF NOT EXISTS gaiaos_memory_mode_control (
    control_id INTEGER PRIMARY KEY CHECK(control_id = 1),
    selected_mode TEXT NOT NULL CHECK(selected_mode IN ('HEATDEATH', 'BIGBANG')),
    authority TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
)
"""


def _result(*, configured: str | None, reason: str,
            version: int | None = None, override: str | None = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "effective_mode": HEATDEATH,
        "configured_mode": configured,
        "reason": reason,
        "control_version": version,
        "override": override,
        "bigbang_activation_enabled": False,
        "writes_performed": [],
        "scope": "MODE_SELECTION_ONLY_NOT_APPLICATION_WIRING",
        "proof_boundary": (
            "HEATDEATH is the only currently executable mode decision. "
            "This module does not yet switch ordinary chat, MCP or other "
            "carrier routes and does not prove production recovery."
        ),
    }


def mode_status(runtime: Any, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Read the shared control on each call; emergency overrides always win.

    Absence of the table, malformed rows or an unavailable backend fail closed.
    Later BIGBANG activation will require an independently verified release
    gate and explicit Naomi authorization; this stage cannot activate it.
    """
    environment = os.environ if environ is None else environ
    for key in OVERRIDES:
        value = str(environment.get(key, "")).strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return _result(configured=None, reason="EMERGENCY_ENV_OVERRIDE", override=key)
        if value not in {"", "0", "false", "no", "off"}:
            return _result(configured=None, reason="INVALID_EMERGENCY_OVERRIDE", override=key)

    try:
        with runtime._db() as conn:
            row = conn.execute(
                "SELECT selected_mode, authority, approved_at, version "
                "FROM gaiaos_memory_mode_control WHERE control_id=1"
            ).fetchone()
        if row is None:
            return _result(configured=None, reason="NO_PERSISTED_CONTROL")
        selected, authority, approved_at, version = row
        if (selected not in (HEATDEATH, BIGBANG)
                or authority != "NAOMI" or not isinstance(approved_at, str)
                or not approved_at):
            return _result(configured=None, reason="INVALID_PERSISTED_CONTROL")
        if selected == BIGBANG:
            return _result(
                configured=BIGBANG, version=int(version),
                reason="BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED",
            )
        return _result(
            configured=HEATDEATH, version=int(version),
            reason="PERSISTED_OWNER_EMERGENCY",
        )
    except Exception as exc:
        label = str(exc).lower()
        reason = ("NO_PERSISTED_CONTROL" if "no such table" in label
                  else "HOLD_SHARED_CONTROL_UNAVAILABLE")
        return {
            **_result(configured=None, reason=reason),
            "error_type": type(exc).__name__,
        }


def engage_heatdeath(runtime: Any, *, authority: str, approved: bool,
                     reason: str) -> dict[str, Any]:
    """Explicit owner-approved idempotent emergency write; read back afterward.

    No BIGBANG writer exists in this stage. When the authoritative store is
    down, the operator must use the environment HEATDEATH override instead.
    """
    if authority != "NAOMI" or approved is not True:
        return {
            **_result(configured=None, reason="HOLD_OWNER_APPROVAL_REQUIRED"),
            "status": "HOLD",
        }
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        return {
            **_result(configured=None, reason="HOLD_REASON_REQUIRED"),
            "status": "HOLD",
        }
    try:
        with runtime._db() as conn:
            conn.execute(_DDL)
            conn.execute(
                """
                INSERT INTO gaiaos_memory_mode_control
                  (control_id, selected_mode, authority, approved_at, reason, version)
                VALUES (1, 'HEATDEATH', 'NAOMI', ?, ?, 1)
                ON CONFLICT(control_id) DO UPDATE SET
                  selected_mode='HEATDEATH', authority='NAOMI',
                  approved_at=excluded.approved_at,
                  reason=excluded.reason,
                  version=gaiaos_memory_mode_control.version+1
                """,
                (datetime.now(timezone.utc).isoformat(), reason.strip()),
            )
        # Verify from a fresh connection, not an in-memory flag.
        with runtime._db() as conn:
            proof = conn.execute(
                "SELECT selected_mode, authority, version "
                "FROM gaiaos_memory_mode_control WHERE control_id=1"
            ).fetchone()
        if not proof or proof[0] != HEATDEATH or proof[1] != "NAOMI":
            return {
                **_result(configured=None, reason="HOLD_WRITE_READBACK_MISMATCH"),
                "status": "HOLD",
            }
        return {
            **_result(configured=HEATDEATH,
                      reason="PERSISTED_OWNER_EMERGENCY",
                      version=int(proof[2])),
            "status": "PASS_HEATDEATH_CONTROL_PERSISTED",
            "writes_performed": [TABLE],
            "readback_verified": True,
        }
    except Exception as exc:
        return {
            **_result(configured=None, reason="HOLD_SHARED_CONTROL_WRITE_FAILED"),
            "status": "HOLD",
            "error_type": type(exc).__name__,
            "readback_verified": False,
        }
