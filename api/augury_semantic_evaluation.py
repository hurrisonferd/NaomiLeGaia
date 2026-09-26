"""Stage 9O: model-free classification of owner-adjudicated semantic receipts.

Called only *after* Stage 9H has verified both receipts with the owner's
private HMAC key and compared their identical fingerprints. This module
does not inspect real statements, call a provider, access MemoryOS or
produce release readiness. Counts describe one three-current/two-negative
bounded sample only. Distinct fingerprints and fresh owner judgments
would be required for any later broader evaluation.
"""
from __future__ import annotations

from typing import Any

import augury_semantic_sample as sample

SCHEMA = "gaiaos.augury.stage9o.owner-labeled-audit.v1"
FULL_HOLD = "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"
_CLASSES = frozenset({
    "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED",
    "OWNER_MODEL_AGREE_COLLISION_UNVERIFIED",
    "OWNER_MODEL_AGREE_UNKNOWN",
    "MODEL_SELECTED_MEMBER_BUT_MISSED_COLLISION",
    "MODEL_OWNER_DISAGREE",
})
_OWNER = frozenset({"A", "B", "COLLISION", "UNKNOWN"})


def _hold() -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD_UNVERIFIED_RECEIPT_PAIR",
        "owner_labeled_current_cases": 0,
        "attested_negative_controls": 0,
        "independent_semantic_entailment_proven": False,
        "general_semantic_quality_proven": False,
        "historical_retrieval_proven": False,
        "full_readiness_status": FULL_HOLD,
        "model_called_now": False, "writes_performed": [],
        "e_lanes_modified": False, "release_activated": False,
    }


def audit(
    compared: Any, model_receipt: Any, owner_receipt: Any,
) -> dict[str, Any]:
    """Read only canonical Stage9H results; return strict aggregate counts.

    This is NOT a public validator. Callers must first establish both HMACs
    with receipts.verified and identical sample identity through Stage9H.
    Direct misuse or any malformed shape fails closed without echoing input.
    """
    result = _hold()
    if (
        not isinstance(compared, dict)
        or compared.get("schema") != sample.COMPARE_SCHEMA
        or compared.get("status") not in
            ("HOLD", "AGREEMENT_ON_BOUNDED_SAMPLE_ONLY")
        or compared.get("sample_match_verified") is not True
        or compared.get("model_called") is not False
        or compared.get("writes_performed") != []
        or compared.get("release_activated") is not False
        or compared.get("general_semantic_quality_proven") is not False
        or not isinstance(model_receipt, dict)
        or not isinstance(owner_receipt, dict)
        or model_receipt.get("sample_fingerprint")
            != owner_receipt.get("sample_fingerprint")
        or model_receipt.get("sample_fingerprint")
            != compared.get("sample_fingerprint")
        or model_receipt.get("model_called") is not True
        or owner_receipt.get("model_called") is not False
        or model_receipt.get("legacy_exact_parity") is not True
        or not isinstance(compared.get("case_results"), list)
        or len(compared["case_results"]) != 3
        or not isinstance(model_receipt.get("case_results"), list)
        or len(model_receipt["case_results"]) != 5
        or not isinstance(owner_receipt.get("case_results"), list)
        or len(owner_receipt["case_results"]) != 3
    ):
        return result

    try:
        findings = sorted(compared["case_results"], key=lambda row: row["case"])
        owner = sorted(owner_receipt["case_results"], key=lambda row: row["case"])
        model = sorted(model_receipt["case_results"], key=lambda row: row["case"])
        if (
            [row["case"] for row in findings] != [0, 1, 2]
            or [row["case"] for row in owner] != [0, 1, 2]
            or [row["case"] for row in model] != [0, 1, 2, 3, 4]
        ):
            return result
        for index in range(3):
            f, o, m = findings[index], owner[index], model[index]
            if (
                f.get("classification") not in _CLASSES
                or o.get("owner_resolution") not in _OWNER
                or f.get("owner_resolution") != o["owner_resolution"]
                or f.get("model_resolution") != m.get("resolution")
                or f.get("model_selected_slot") != m.get("model_selected_slot")
                or m.get("kind") != "current"
                or type(f.get("categorical_agreement")) is not bool
                or f["categorical_agreement"]
                   is not f["classification"].startswith("OWNER_MODEL_AGREE")
            ):
                return result
        if any(
            row.get("kind") != "negative"
            or row.get("resolution") != "UNKNOWN"
            or row.get("pass") is not True
            for row in model[3:]
        ):
            return result
        classifications = [row["classification"] for row in findings]
        agreements = sum(row["categorical_agreement"] for row in findings)
        owner_collision = sum(
            row["owner_resolution"] == "COLLISION" for row in owner
        )
        owner_unknown = sum(
            row["owner_resolution"] == "UNKNOWN" for row in owner
        )
        result.update({
            "status": "BOUNDED_OWNER_LABELS_CLASSIFIED",
            "owner_labeled_current_cases": 3,
            "owner_single_source_cases": 3 - owner_collision - owner_unknown,
            "owner_collision_cases": owner_collision,
            "owner_unknown_cases": owner_unknown,
            "attested_negative_controls": 2,
            "owner_model_categorical_agreements": agreements,
            "owner_model_categorical_disagreements": 3 - agreements,
            "single_source_grounded_agreements": classifications.count(
                "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED"
            ),
            "collision_claim_agreements_unverified": classifications.count(
                "OWNER_MODEL_AGREE_COLLISION_UNVERIFIED"
            ),
            "model_missed_owner_collision": classifications.count(
                "MODEL_SELECTED_MEMBER_BUT_MISSED_COLLISION"
            ),
            "owner_generator_supported_cases": sum(
                row.get("generator_expected_supported") is True
                for row in owner
            ),
            "owner_generator_unique_correct_cases": sum(
                row.get("generator_expected_is_unique_owner_answer") is True
                for row in owner
            ),
            "case_scope": "ONE_ATTESTED_THREE_CURRENT_TWO_NEGATIVE_SAMPLE",
            "source_retrievability_is_not_semantic_entailment": True,
            "new_owner_cases_added": 0,
            "next_evidence": (
                "NEW_AUTHENTIC_INDEPENDENT_OWNER_LABELED_QUERIES_REQUIRED"
            ),
        })
        return result
    except (KeyError, IndexError, TypeError, ValueError):
        return _hold()
