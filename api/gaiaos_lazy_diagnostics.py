"""Lazy, read-only import boundary for optional GALAXY research command modules.

Normal GaiaOS/HEATDEATH application boot must not import experimental GALAXY
modules just to expose their explicitly invoked diagnostics. An unavailable
optional module returns an explicit 503 only when its attribute is requested.
This is not a mode selector, security boundary for diagnostic mutations, or
BIGBANG activation permission.
"""
from __future__ import annotations

import importlib

from fastapi import HTTPException

_ALLOWED = frozenset({
    "galaxy_production", "galaxy_quality", "galaxy_phase3_exit",
    "galaxy_phase4", "galaxy_phase5", "galaxy_phase5_controls",
    "galaxy_phase6", "galaxy_phase6_controls", "galaxy_phase7",
    "galaxy_phase7_tombstone", "galaxy_phase7_tombstone_shadow",
    "galaxy_phase7_isolated_restore", "augury_ritual",
})


class DeferredDiagnosticModule:
    """Proxy that never imports optional code during ordinary application boot."""

    def __init__(self, module_name: str) -> None:
        if module_name not in _ALLOWED:
            raise ValueError("Unregistered optional research module")
        self.module_name = module_name

    def __getattr__(self, attribute: str):
        if attribute.startswith("__"):
            raise AttributeError(attribute)
        try:
            loaded = importlib.import_module(self.module_name)
        except Exception as exc:
            # No attempted generic fallback and no leaking internal error text.
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "HOLD_OPTIONAL_DIAGNOSTIC_UNAVAILABLE",
                    "module": self.module_name,
                    "proof_boundary": (
                        "The normal GaiaOS/HEATDEATH carrier remains available; "
                        "the optional GALAXY research command is unavailable."
                    ),
                },
            ) from exc
        return getattr(loaded, attribute)


def deferred(module_name: str) -> DeferredDiagnosticModule:
    return DeferredDiagnosticModule(module_name)
