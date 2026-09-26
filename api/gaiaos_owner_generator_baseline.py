"""Stage 9Q: owner-label versus generator-target baseline, without a model call.

Caller MUST first HMAC-verify the archived owner receipt, verify the archived
two-source collision receipt, rebind their fingerprint to the current eligible
MemoryOS sample, and check HEATDEATH before and after the live read. This
module is deliberately pure. It compares an owner's bounded signed labels to
the *question generator's proposed targets*, never to model predictions.
It is NOT a new semantic-quality, historical-retrieval or release gate.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "gaiaos.galaxy.stage9q.owner-generator-baseline.v1"
HOLD_REASON = "OWNER_LABEL_CONTRACT_UNVERIFIED"
STATUS = "BOUNDED_OWNER_GENERATOR_BASELINE_ONLY"
FINGERPRINT = re.compile(r"sf1_[0-9a-f]{32}\Z")
SUPPORT = {
    "A": ([0], 0),
    "B": ([1], 1),
    "COLLISION": ([0, 1], None),
    "UNKNOWN": ([], None),
}


def hold() -> dict[str, Any]:
    """Fail closed without suggesting an empty or successful evaluation."""
    return {
        "schema": SCHEMA, "status": "HOLD", "reason": HOLD_REASON,
        "model_receipt_compared": False, "independent_entailment_proven": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "model_called": False, "writes_performed": [], "e_lanes_modified": False,
        "release_activated": False,
    }


def classify_verified_owner_receipt(owner: Any) -> dict[str, Any]:
    """Classify three CURRENT owner judgments after the caller's HMAC check.

    Negative controls are included in the bound five-question fingerprint but
    are NOT independently owner-adjudicated by this archived three-row receipt.
    A supported collision target is never a uniquely correct answer.
    The entire result is finite aggregate data; private records, questions,
    owner key, fingerprint and per-case source slots stay server-side.
    """
    if (
        not isinstance(owner, dict)
        or owner.get("schema")
            != "gaiaos.augury.semantic-owner-oracle-redacted.v1"
        or owner.get("status") != "OWNER_ORACLE_RECORDED"
        or owner.get("sample_fingerprint_bound") is not True
        or not isinstance(owner.get("sample_fingerprint"), str)
        or FINGERPRINT.fullmatch(owner["sample_fingerprint"]) is None
        or owner.get("case_count") != 3
        or owner.get("model_called") is not False
        or owner.get("writes_performed") != []
        or owner.get("release_activated") is not False
        or not isinstance(owner.get("case_results"), list)
        or len(owner["case_results"]) != 3
    ):
        return hold()

    unique = nonunique = unsupported = unknown = collisions = 0
    for index, row in enumerate(owner["case_results"]):
        if not isinstance(row, dict) or type(row.get("case")) is not int:
            return hold()
        resolution = row.get("owner_resolution")
        if row["case"] != index or resolution not in SUPPORT:
            return hold()
        supported, owner_slot = SUPPORT[resolution]
        target = row.get("generator_expected_slot")
        if (
            type(target) is not int or target not in (0, 1)
            or row.get("owner_slot") != owner_slot
            or row.get("owner_supported_slots") != supported
            or row.get("generator_expected_supported") is not
               (target in supported)
            or row.get("generator_expected_is_unique_owner_answer") is not
               (len(supported) == 1 and target in supported)
        ):
            return hold()
        if resolution == "COLLISION":
            collisions += 1
        if resolution == "UNKNOWN":
            unknown += 1
        elif target not in supported:
            unsupported += 1
        elif len(supported) == 1:
            unique += 1
        else:
            nonunique += 1

    if unique + nonunique + unsupported + unknown != 3:
        return hold()
    return {
        "schema": SCHEMA, "status": STATUS,
        "reason": "SIGNED_OWNER_LABELS_VS_GENERATOR_TARGETS",
        "owner_labeled_current_cases": 3,
        "owner_collision_cases": collisions,
        "owner_unknown_cases": unknown,
        "generator_unique_owner_support": unique,
        "generator_nonunique_owner_support": nonunique,
        "generator_not_owner_supported": unsupported,
        "negative_controls_owner_adjudicated": 0,
        "model_receipt_compared": False,
        "independent_entailment_proven": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "model_called": False, "writes_performed": [], "e_lanes_modified": False,
        "release_activated": False,
    }
