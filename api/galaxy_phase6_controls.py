"""Exact, finite GALAXY Phase-6 live lifecycle control campaign.

This adapter narrows galaxy_phase6.execute() to one exact fixture and one exact
five-step proof campaign. It does not authorize generic lifecycle operations.
Every step still requires a fresh signed-session browser confirmation.
"""
from __future__ import annotations

from typing import Any
import galaxy_phase6 as p6

VERSION = "galaxy.phase6.control-exposure.v1"
CAMPAIGN = (
    ("BACKGROUND", "BACKGROUND"),
    ("ARCHIVED", "ARCHIVED"),
    ("COMPRESSED", "COMPRESSED"),
    ("ROLLBACK", "ARCHIVED"),
    ("REACTIVATE", "ACTIVE"),
)
REASONS = {
    "BACKGROUND": "Controlled Phase-6 live proof: ACTIVE to BACKGROUND",
    "ARCHIVED": "Controlled Phase-6 live proof: BACKGROUND to ARCHIVED",
    "COMPRESSED": "Controlled Phase-6 live proof: ARCHIVED to COMPRESSED",
    "ROLLBACK": "Controlled Phase-6 live proof: rollback COMPRESSED to ARCHIVED",
    "REACTIVATE": "Controlled Phase-6 live proof: reactivate ARCHIVED to ACTIVE",
}


def _history_signature(state: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (str(event.get("action") or ""), str(event.get("to_state") or ""))
        for event in state.get("events") or []
    ]


def inspect(runtime: Any) -> dict[str, Any]:
    """Read-only finite-campaign status and exactly one permitted next action."""
    state = p6.inspect(runtime, p6.FIXTURE_RECORD_ID)
    signature = _history_signature(state)
    expected_prefix = list(CAMPAIGN[:len(signature)])
    holds = list(state.get("hold_reasons") or [])
    if signature != expected_prefix:
        holds.append("PHASE6_CAMPAIGN_HISTORY_NOT_EXPECTED_PREFIX")
    if len(signature) > len(CAMPAIGN):
        holds.append("PHASE6_CAMPAIGN_ALREADY_EXCEEDED")

    next_action = None
    complete = False
    if not holds and state.get("status") == "PASS_READ_ONLY":
        if len(signature) == len(CAMPAIGN):
            complete = True
        else:
            candidate = CAMPAIGN[len(signature)][0]
            if state.get("eligible_actions", {}).get(candidate) is True:
                next_action = candidate
            else:
                holds.append("EXPECTED_CAMPAIGN_ACTION_NOT_ELIGIBLE")

    return {
        "schema": "gaiaos.galaxy.phase6-control-review.v1",
        "version": VERSION,
        "execution": "READ_ONLY",
        "authority": "NAOMI",
        "controlled_record_id": p6.FIXTURE_RECORD_ID,
        "campaign": [
            {"index": i + 1, "operation": op, "expected_state": target}
            for i, (op, target) in enumerate(CAMPAIGN)
        ],
        "completed_steps": len(signature),
        "history_signature": signature,
        "current_state": state.get("current_state"),
        "latest_event_id": state.get("latest_event_id"),
        "next_action": next_action,
        "campaign_complete": complete,
        "confirmation": p6.CONFIRMATIONS.get(next_action) if next_action else None,
        "reason": REASONS.get(next_action) if next_action else None,
        "hold_reasons": holds,
        "underlying_review": state,
        "writes": 0,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "Only the exact five-step fixture campaign is exposed. This review writes "
            "nothing. Each next step requires a fresh signed browser session, CSRF "
            "proof, exact confirmation token, expected state and expected history tip."
        ),
    }


def execute(
    runtime: Any,
    operation: str,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
    expected_state: str,
    expected_latest_event_id: str | None,
) -> dict[str, Any]:
    """Execute exactly the single next campaign step after fresh explicit consent."""
    operation = str(operation or "").strip().upper()
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Explicit Naomi approval required for Phase-6 live control")
    before = inspect(runtime)
    if before["hold_reasons"]:
        raise ValueError("Phase-6 control campaign is on HOLD")
    if before["campaign_complete"]:
        raise ValueError("Phase-6 control campaign is already complete")
    if operation != before["next_action"]:
        raise ValueError("Only the exact next Phase-6 campaign action is permitted")
    if confirmation != p6.CONFIRMATIONS[operation]:
        raise PermissionError("Exact Phase-6 step confirmation mismatch")
    if expected_state != before["current_state"]:
        raise ValueError("Stale Phase-6 current state")
    if expected_latest_event_id != before["latest_event_id"]:
        raise ValueError("Stale Phase-6 history tip")

    effect = p6.execute(
        runtime,
        operation,
        authority=authority,
        approved=True,
        confirmation=confirmation,
        expected_state=expected_state,
        expected_latest_event_id=expected_latest_event_id,
        reason=REASONS[operation],
        record_id=p6.FIXTURE_RECORD_ID,
    )
    after = inspect(runtime)
    expected_step = before["completed_steps"] + 1
    expected_target = CAMPAIGN[before["completed_steps"]][1]
    checks = {
        "underlying_effect_passed": effect.get("status") == "PASS_READBACK",
        "exact_step_advanced_once": after.get("completed_steps") == expected_step,
        "expected_state_readback": after.get("current_state") == expected_target,
        "exact_history_prefix_preserved": (
            after.get("history_signature") == list(CAMPAIGN[:expected_step])
        ),
        "no_control_hold_after_step": not after.get("hold_reasons"),
        "source_record_unchanged": effect.get("checks", {}).get("source_record_unchanged") is True,
        "prior_history_unchanged": effect.get("checks", {}).get("prior_history_unchanged") is True,
        "receipt_committed": effect.get("checks", {}).get("receipt_committed") is True,
        "production_retrieval_unchanged": effect.get("production_retrieval_changed") is False,
        "physical_delete_false": effect.get("physical_delete") is False,
    }
    return {
        "schema": "gaiaos.galaxy.phase6-control-receipt.v1",
        "version": VERSION,
        "operation": operation,
        "execution": "OBSERVED_RUNTIME_FOR_THIS_CALL",
        "status": "PASS_READBACK" if all(checks.values()) else "HOLD_READBACK",
        "controlled_record_id": p6.FIXTURE_RECORD_ID,
        "checks": checks,
        "effect_receipt": effect,
        "control_readback": after,
        "campaign_complete": after.get("campaign_complete") is True,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "PASS applies only to this one explicit campaign step and its immediate "
            "readback. Restart persistence remains a later separately observed proof."
        ),
    }
