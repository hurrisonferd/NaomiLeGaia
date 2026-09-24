"""Independent legacy MemoryOS retrieval adapter.

The adapter deliberately imports no GALAXY components.  Preserve the existing
memcon_runtime.search_records(query, limit, scope) contract exactly, including
its query-term AND semantics, optional scope, limit clamp, empty-query behavior,
record ordering, history visibility, and native return envelope.

The frozen pre-BIGBANG source snapshot lives at
legacy/source-snapshot-pre-bigbang-20260924
(7e4851c2fef77d78bccf51d493d1c100cc99c52d). This adapter is not, by itself, proof of
a separately deployable full legacy carrier or a functioning kill switch.
"""
from __future__ import annotations

from typing import Any

BASELINE_SOURCE_COMMIT = "7e4851c2fef77d78bccf51d493d1c100cc99c52d"
BASELINE_BRANCH = "legacy/source-snapshot-pre-bigbang-20260924"


def read(runtime: Any, query: str = "", scope: str | None = None,
         limit: int = 10) -> dict[str, Any]:
    """Delegate unmodified to the currently authoritative legacy reader."""
    return runtime.search_records(query, limit, scope)


def read_deployed(query: str = "", scope: str | None = None,
                  limit: int = 10) -> dict[str, Any]:
    """Import only the durable storage runtime; never import GALAXY modules."""
    import memcon_runtime
    return read(memcon_runtime, query, scope, limit)
