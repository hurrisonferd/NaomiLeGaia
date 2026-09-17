#!/usr/bin/env python3
"""Bounded GaiaOS AgencyOS orchestration runtime."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

CAPABILITIES = {
    "READ": {"approval_required": False, "reversible": True, "provider": "GaiaOS source/runtime"},
    "CREATE": {"approval_required": True, "reversible": True, "provider": "WorkspaceOS"},
    "MODIFY": {"approval_required": True, "reversible": True, "provider": "WorkspaceOS"},
    "EXECUTE": {"approval_required": True, "reversible": False, "provider": "EXTERNAL_PROVIDER_UNREGISTERED"},
    "COMMUNICATE": {"approval_required": True, "reversible": False, "provider": "EXTERNAL_PROVIDER_UNREGISTERED"},
    "DEPLOY": {"approval_required": True, "reversible": False, "provider": "EXTERNAL_PROVIDER_UNREGISTERED"},
}

LANES = {
    "frame": "VERA", "architecture": "VERA", "assumption": "VERA",
    "proof": "ANVIL", "boundary": "ANVIL", "verify": "ANVIL", "permission": "ANVIL",
    "user": "SELENE", "usability": "SELENE", "care": "SELENE", "experience": "SELENE",
    "research": "ORIN", "discover": "ORIN", "explore": "ORIN", "signal": "ORIN",
    "coordinate": "KESTREL", "plan": "KESTREL", "implement": "KESTREL", "build": "KESTREL",
    "missing": "NIMUE", "omission": "NIMUE", "risk": "NIMUE", "failure": "NIMUE",
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _assign(goal: str) -> list[str]:
    low=goal.lower()
    selected=[]
    for token,member in LANES.items():
        if token in low and member not in selected:
            selected.append(member)
    return selected or ["KESTREL","ANVIL"]

def plan(goal: str, capabilities: list[str] | None = None) -> dict[str, Any]:
    goal=goal.strip()
    requested=[str(x).upper() for x in (capabilities or ["READ","CREATE"])]
    unknown=[x for x in requested if x not in CAPABILITIES]
    selected=[x for x in requested if x in CAPABILITIES]
    lanes=_assign(goal)
    subproblems=[
        {"id":"context","task":"Resolve relevant source and current state","lane":"VERA","capability":"READ"},
        {"id":"constraints","task":"Check boundaries, proof ceiling, and approval needs","lane":"ANVIL","capability":"READ"},
        {"id":"work","task":"Coordinate the concrete work plan","lane":"KESTREL","capability":selected[0] if selected else "READ"},
        {"id":"omissions","task":"Check for missing dependencies and failure modes","lane":"NIMUE","capability":"READ"},
    ]
    if "ORIN" in lanes: subproblems.append({"id":"discovery","task":"Explore relevant alternatives and signals","lane":"ORIN","capability":"READ"})
    if "SELENE" in lanes: subproblems.append({"id":"livability","task":"Check usability and aftercare implications","lane":"SELENE","capability":"READ"})
    return {
        "schema":"gaiaos.agencyos.plan.v2","plan_id":f"PLAN-{uuid.uuid4().hex}",
        "authority":"NAOMI","goal":goal,
        "cycle":["GOAL","DECOMPOSE","ASSIGN","PLAN","APPROVE","EXECUTE","OBSERVE","VERIFY","REPLAN","DELIVER"],
        "assigned_lanes":lanes,"subproblems":subproblems,
        "capabilities":[{"name":x,**CAPABILITIES[x]} for x in selected],
        "unknown_capabilities":unknown,"status":"PROPOSED","effect_authority":"NONE",
        "claim_ceiling":"Proposed orchestration only. No external action occurred."
    }

def execute_capability(capability: str, approved: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    capability=capability.upper()
    if capability not in CAPABILITIES:
        return {"status":"UNKNOWN","capability":capability,"reason":"capability not registered"}
    meta=CAPABILITIES[capability]
    if meta["approval_required"] and not approved:
        return {"status":"HOLD","capability":capability,"reason":"explicit Naomi approval required","effect_authority":"NONE"}
    if capability=="READ":
        return {"status":"EXECUTED","capability":"READ","observed":True,"receipt":f"AGENCY-{uuid.uuid4().hex}","timestamp":_now(),"result":payload or {}}
    return {"status":"HOLD","capability":capability,"provider":meta["provider"],"reason":"provider is not registered for this effect class yet","effect_authority":"NONE","claim_ceiling":"Capability class exists, but provider execution is not implemented."}
