#!/usr/bin/env python3
"""Bounded GaiaOS evolution proposal runtime."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

def propose(observation: str, weakness: str, change: str, benefit: str, surfaces: list[str], canary: str, rollback: str) -> dict:
    return {
        "schema":"gaiaos.evolutionos.proposal.v1",
        "proposal_id":f"EVOL-{uuid.uuid4().hex}",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "authority":"NAOMI",
        "status":"PROPOSED",
        "observation":observation,
        "weakness":weakness,
        "proposed_change":change,
        "expected_benefit":benefit,
        "affected_surfaces":surfaces,
        "canary":canary,
        "rollback":rollback,
        "automatic_adoption":False,
        "effect_authority":"NONE",
        "claim_ceiling":"Proposal only. No canonical source or deployed behavior changed."
    }
