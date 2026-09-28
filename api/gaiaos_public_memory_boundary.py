"""Common read-side barrier for unreleased, owner-staged historical archives.

This pure module has no GALAXY imports, database access or activation controls:
HEATDEATH, MemconOS HTTP/MCP, and the optional GALAXY preview can import it
even when all optional scoring modules are unavailable. Future authorized
archive inspection must use a separately gated owner-local audit path, never
the general chat, memory search or host bootstrap surfaces.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "gaiaos.memory.public-archive-read-boundary.v1"
HOLD = "HOLD_UNRELEASED_ARCHIVE_IN_DIRECT_READ"
SOURCE_PREFIX = "galaxy-archive-v1:"
STAGING_STATUS = "STAGED_HISTORICAL_HOLD"


def unreleased(record: Any) -> bool:
    """Deny forged ACTIVE records carrying the canonical archive source too."""
    if not isinstance(record, dict):
        return True
    status = record.get("status")
    source = record.get("source")
    return (
        isinstance(status, str) and status.strip().upper() == STAGING_STATUS
        or isinstance(source, str)
        and source.lstrip().lower().startswith(SOURCE_PREFIX)
    )


def unreleased_in_search(payload: Any) -> bool:
    """A malformed result also fails closed, without reporting partial rows."""
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return True
    return any(unreleased(record) for record in payload["records"])


def redacted_hold() -> dict[str, Any]:
    """Safe for HTTP/MCP: never include statement, source, ID or private URL."""
    return {
        "schema": SCHEMA,
        "status": HOLD,
        "records": [],
        "count": 0,
        "writes_performed": [],
        "e_lanes_modified": False,
        "proof_boundary": (
            "An unreleased or malformed archival record reached a general "
            "memory-read surface. No partial result or historical source is "
            "returned. An independent, owner-authorized archive audit is required."
        ),
    }
