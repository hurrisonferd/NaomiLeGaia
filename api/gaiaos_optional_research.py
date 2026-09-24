"""Lazy access to optional GALAXY research modules.

Importing this module MUST NOT import a GALAXY module or the optional
AUGURY/RITUAL research surface. A broken experimental GALAXY file therefore
cannot prevent ordinary HEATDEATH browser, MCP, MemoryOS, preservation or
member-local chat from booting. Only a specifically invoked research handler
may resolve a module. Actual HTTP/text command authorization is checked at the
normal browser boundary, not by this pure import adapter.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any


class LazyResearchModule:
    __slots__ = ("_name", "_resolved")

    def __init__(self, name: str):
        if not name or not (name.startswith("galaxy_") or name == "augury_ritual"):
            raise ValueError("Only registered optional research modules may be lazy")
        self._name = name
        self._resolved: Any = None

    def _load(self):
        if self._resolved is None:
            module = import_module(self._name)
            self._resolved = module
        return self._resolved

    def __getattr__(self, attribute: str):
        # Never resolve a research module just to answer Python introspection.
        if attribute.startswith("__"):
            raise AttributeError(attribute)
        return getattr(self._load(), attribute)

    def __repr__(self) -> str:
        return f"<LazyResearchModule {self._name}: deferred>"
