"""Stage 9W: release-locked normal browser-chat GALAXY context preparation.

This is an opt-in-by-approved-mode, read-only bridge, not a new release switch.
The original HEATDEATH chat route must work even if this module, MemconOS or
GALAXY cannot import. No user-supplied browser JSON can become trusted evidence.
"""
from __future__ import annotations

from typing import Any

CONTEXT_LIMIT = 4


def prepare_for_browser(query: Any) -> dict[str, Any] | None:
    """Server-side only; accept the last actual user message, not older turns.

    Every failure returns None to preserve the original chat path. If a later
    release authorizes BIGBANG, normal /chat can consume verified, bounded
    context. This module cannot grant that authorization or mutate any store.
    """
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 20000:
        return None
    try:
        import gaiaos_memory_mode as mode
        import memcon_runtime as runtime

        # Stage 2's actual mode_status is the source of truth. It currently
        # always returns HEATDEATH; this bridge alone cannot activate BIGBANG.
        control = mode.mode_status(runtime)
        if not isinstance(control, dict) or (
            control.get("schema") != mode.SCHEMA
            or control.get("effective_mode") != mode.BIGBANG
            or control.get("configured_mode") != mode.BIGBANG
            or control.get("bigbang_activation_enabled") is not True
        ):
            return None
        import gaiaos_memory_gateway as gateway
        packet = gateway.read(runtime, query.strip(), scope="MemoryOS", limit=CONTEXT_LIMIT)
        if not isinstance(packet, dict) or (
            packet.get("status") != "PASS_BIGBANG"
            or packet.get("effective_mode") != mode.BIGBANG
            or packet.get("galaxy_applied") is not True
            or packet.get("fallback_occurred") is not False
            or packet.get("writes_performed") != []
            or packet.get("e_lanes_modified") is not False
        ):
            return None
        import gaiaos_chat_memory as evidence
        result = evidence.prepare(packet)
        return result if result is not None and evidence.validate_prepared(result) else None
    except Exception:
        # In particular, missing GALAXY modules, missing remote drivers,
        # uninitialized Turso, or a scoring model error cannot break HEATDEATH.
        return None
