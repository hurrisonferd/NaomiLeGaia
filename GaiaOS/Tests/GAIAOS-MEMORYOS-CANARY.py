"""Source-level canary for the MemoryOS lifecycle."""
from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    os.environ["MEMCONOS_DB_PATH"] = str(Path(tmp) / "memconos.db")

    mem_spec = importlib.util.spec_from_file_location(
        "memcon_runtime",
        "api/memcon_runtime.py",
    )
    memcon = importlib.util.module_from_spec(mem_spec)
    assert mem_spec.loader is not None
    mem_spec.loader.exec_module(memcon)

    memory_spec = importlib.util.spec_from_file_location(
        "gaia_memory_runtime",
        "GaiaOS/SystemsOS/Core/MemoryOS/Runtime/GAIAOS-MEMORY.v1.py",
    )
    memory = importlib.util.module_from_spec(memory_spec)
    assert memory_spec.loader is not None
    memory_spec.loader.exec_module(memory)

    session = memory.start_session("CANARY", "memory lifecycle")
    event = memory.record_event(
        session["session_id"], "NAOMI", "DESIGN_DECISION",
        "MemoryOS should preserve the path from session event to verified durable record.",
        "CANARY",
    )
    candidate = memory.candidate_from_event(
        event["event_id"],
        authority="NAOMI",
        record_type="DESIGN_DECISION",
        scope="MemoryOS",
        statement="MemoryOS should preserve the path from session event to verified durable record.",
        source="GAIAOS-MEMORYOS-CANARY",
        owner="NAOMI",
        why_material="Tests the complete bounded lifecycle.",
    )
    hold = memory.promote_candidate(candidate["candidate_id"], approved=False)
    assert hold["status"] == "HOLD"

    promoted = memory.promote_candidate(candidate["candidate_id"], approved=True)
    assert promoted["status"] == "VERIFIED"
    assert promoted["record_id"]
    assert promoted["write_receipt"]["result"] == "SUCCESS"
    assert promoted["verification"]["observed"] is True

    retrieved = memory.retrieve("verified durable record", scope="MemoryOS")
    assert retrieved["status"] == "OBSERVED"
    assert retrieved["retrieval"]["count"] >= 1

print("GAIAOS_MEMORYOS_CANARY PASS")
