#!/usr/bin/env python3
"""Bounded GaiaOS agency/orchestration runtime."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from typing import Any

CAPABILITIES = {
    "READ": {"approval_required": False, "reversible": True},
    "CREATE": {"approval_required": True, "reversible": True},
    "MODIFY": {"approval_required": True, "reversible": True},
    "EXECUTE": {"approval_required": True, "reversible": False},
    "COMMUNICATE": {"approval_required": True, "reversible": False},
    "DEPLOY": {"approval_required": True, "reversible": False},
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def plan(goal: str, capabilities: list[str] | None = None) -> dict[str, Any]:
    goal = goal.strip()
    requested = [str(x).upper() for x in (capabilities or ["READ","CREATE"])]
    unknown = [x for x in requested if x not in CAPABILITIES]
    selected = [x for x in requested if x in CAPABILITIES]
    return {
        "schema": "gaiaos.agencyos.plan.v1",
        "plan_id": f"PLAN-{uuid.uuid4().hex}",
        "authority": "NAOMI",
        "goal": goal,
        "cycle": ["GOAL","DECOMPOSE","ASSIGN","PLAN","APPROVE","EXECUTE","OBSERVE","VERIFY","REPLAN","DELIVER"],
        "capabilities": [{"name": x, **CAPABILITIES[x]} for x in selected],
        "unknown_capabilities": unknown,
        "status": "PROPOSED",
        "effect_authority": "NONE",
        "claim_ceiling": "This is a proposed orchestration plan. No external action has occurred."
    }

def execute_capability(capability: str, approved: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    capability = capability.upper()
    if capability not in CAPABILITIES:
        return {"status":"UNKNOWN","capability":capability,"reason":"capability not registered"}
    if CAPABILITIES[capability]["approval_required"] and not approved:
        return {"status":"HOLD","capability":capability,"reason":"explicit Naomi approval required","effect_authority":"NONE"}
    if capability == "READ":
        return {"status":"EXECUTED","capability":"READ","observed":True,"receipt":f"AGENCY-{uuid.uuid4().hex}","timestamp":_now(),"result":payload or {}}
    return {
        "status":"HOLD",
        "capability":capability,
        "reason":"No provider is registered for this effect class yet",
        "effect_authority":"NONE",
        "claim_ceiling":"Capability class exists, but provider execution is not implemented."
    }
