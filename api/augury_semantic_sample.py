"""Stage 9G: owner-keyed sample provenance and non-effectful oracle comparison.

The fingerprint is HMAC-SHA256 under the already configured PRIVATE owner
bearer key. It binds ordered exact approved record IDs, source statements,
source provenance, five ordered questions and their generator-target slots.
Neither the secret nor preimage is returned or sent to the OpenAI API.
Rotating the owner key intentionally invalidates cross-key comparisons.

Only REDACTED, separately owner-authorized receipts may be compared.
Comparison never asserts semantic entailment, writes memory or activates
BIGBANG, even when all owner/model categorical choices agree.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

SCHEMA = "gaiaos.augury.semantic-sample-fingerprint.v1"
COMPARE_SCHEMA = "gaiaos.augury.semantic-owner-model-comparison.v1"
_FINGERPRINT_RE = re.compile(r"^sf1_[a-f0-9]{32}$")


def fingerprint(
    *,
    owner_key: str | None,
    records: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> str | None:
    """HMAC a bounded, order-sensitive snapshot; None when unbound.

    The caller validates real technical provenance and owner authorization
    before calling this function. These material fields MUST match exactly
    between the owner's preview and model's actual source read.
    """
    if not isinstance(owner_key, str) or not owner_key.strip():
        return None
    if not isinstance(records, list) or len(records) != 2:
        return None
    if not isinstance(cases, list) or len(cases) != 5:
        return None
    allowed_records = []
    for item in records:
        if not isinstance(item, dict):
            return None
        fields = ("record_id", "statement", "source")
        if not all(isinstance(item.get(f), str) and item[f] for f in fields):
            return None
        allowed_records.append({f: item[f] for f in fields})
    if allowed_records[0]["record_id"] == allowed_records[1]["record_id"]:
        return None
    allowed_cases = []
    indices = {r["record_id"]: i for i, r in enumerate(allowed_records)}
    for item in cases:
        if not isinstance(item, dict) or item.get("kind") not in (
            "current", "negative"
        ):
            return None
        q = item.get("query")
        if not isinstance(q, str) or not q:
            return None
        expected = item.get("record_id")
        if item["kind"] == "current":
            if expected not in indices:
                return None
            expected_slot = indices[expected]
        elif expected is None:
            expected_slot = None
        else:
            return None
        allowed_cases.append({
            "kind": item["kind"],
            "query": q,
            "generator_expected_slot": expected_slot,
        })
    if [item["kind"] for item in allowed_cases] != [
        "current", "current", "current", "negative", "negative"
    ]:
        return None
    material = {
        "schema": SCHEMA,
        "ordered_approved_records": allowed_records,
        "ordered_five_cases": allowed_cases,
    }
    encoded = json.dumps(
        material, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    digest = hmac.new(
        owner_key.encode("utf-8"),
        b"GaiaOS.Stage9G.OwnerBoundSample.v1\x00" + encoded,
        hashlib.sha256,
    ).hexdigest()
    return "sf1_" + digest[:32]


def _hold(reason: str) -> dict[str, Any]:
    return {
        "schema": COMPARE_SCHEMA,
        "status": "HOLD",
        "reason": reason,
        "case_results": [],
        "sample_match_verified": False,
        "categorical_agreement_proven": False,
        "general_semantic_quality_proven": False,
        "historical_coverage": False,
        "full_readiness_status": "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
        "model_called": False,
        "writes_performed": [],
        "release_activated": False,
    }


def compare_redacted(
    model_receipt: Any, owner_receipt: Any,
) -> dict[str, Any]:
    """Read-only owner/model class agreement on one *identical* HMAC sample.

    The owner makes the independent semantic judgment. A model's COLLISION
    answer is a claim of ambiguity, NOT a source quote for both records.
    Equality of classes is evidence of agreement only, not factual truth.
    """
    if (
        not isinstance(model_receipt, dict)
        or model_receipt.get("schema") != "gaiaos.augury.semantic-read-shadow.v1"
        or not isinstance(owner_receipt, dict)
        or owner_receipt.get("schema")
            != "gaiaos.augury.semantic-owner-oracle-redacted.v1"
    ):
        return _hold("REDACTED_RECEIPT_SCHEMA_INVALID")
    left = model_receipt.get("sample_fingerprint")
    right = owner_receipt.get("sample_fingerprint")
    if (
        not isinstance(left, str)
        or not _FINGERPRINT_RE.fullmatch(left)
        or left != right
        or model_receipt.get("sample_fingerprint_bound") is not True
        or owner_receipt.get("sample_fingerprint_bound") is not True
    ):
        return _hold("UNBOUND_OR_DIFFERENT_SAMPLE")
    if (
        model_receipt.get("model_called") is not True
        or model_receipt.get("legacy_exact_parity") is not True
        or model_receipt.get("release_activated") is not False
        or model_receipt.get("writes_performed") != []
        or owner_receipt.get("model_called") is not False
        or owner_receipt.get("release_activated") is not False
        or owner_receipt.get("writes_performed") != []
    ):
        return _hold("UNVERIFIED_EFFECT_OR_PARITY_BOUNDARY")
    model = model_receipt.get("case_results")
    owner = owner_receipt.get("case_results")
    if (
        not isinstance(model, list) or len(model) != 5
        or not isinstance(owner, list) or len(owner) != 3
    ):
        return _hold("CASE_COUNT_INVALID")
    try:
        m = {item["case"]: item for item in model}
        o = {item["case"]: item for item in owner}
        if (
            len(m) != 5 or set(m) != set(range(5))
            or len(o) != 3 or set(o) != set(range(3))
        ):
            return _hold("CASE_INDICES_INVALID")
        if any(
            m[i].get("kind") != "negative"
            or m[i].get("resolution") != "UNKNOWN"
            or m[i].get("pass") is not True
            for i in (3, 4)
        ):
            return _hold("NEGATIVE_CONTROLS_UNVERIFIED")
        results = []
        for i in range(3):
            row, ground = m[i], o[i]
            if row.get("kind") != "current":
                return _hold("POSITIVE_CASE_KIND_INVALID")
            owner_class = ground.get("owner_resolution")
            model_class = row.get("resolution")
            if owner_class not in ("A", "B", "COLLISION", "UNKNOWN"):
                return _hold("OWNER_JUDGMENT_INVALID")
            if model_class not in ("RESOLVED", "COLLISION", "UNKNOWN"):
                return _hold("MODEL_CLASS_INVALID")
            expected_slots = {
                "A": [0], "B": [1], "COLLISION": [0, 1], "UNKNOWN": [],
            }[owner_class]
            if ground.get("owner_supported_slots") != expected_slots:
                return _hold("OWNER_SUPPORT_SET_INVALID")
            slot = row.get("model_selected_slot")
            if model_class == "RESOLVED":
                if type(slot) is not int or slot not in (0, 1):
                    return _hold("MODEL_SELECTED_SLOT_INVALID")
                if row.get("model_candidate_slots") != [slot]:
                    return _hold("MODEL_CANDIDATE_SET_INVALID")
                if not (
                    row.get("source_quote_verified") is True
                    and row.get("exact_read_ritual_compiled") is True
                    and row.get("galaxy_readback_verified") is True
                ):
                    return _hold("MODEL_SOURCE_READBACK_UNVERIFIED")
            elif (
                slot is not None
                or row.get("model_candidate_slots")
                    != ([0, 1] if model_class == "COLLISION" else [])
            ):
                return _hold("MODEL_NONUNIQUE_OR_UNKNOWN_SHAPE_INVALID")
            if owner_class == "COLLISION":
                classification = (
                    "OWNER_MODEL_AGREE_COLLISION_UNVERIFIED"
                    if model_class == "COLLISION" else
                    "MODEL_SELECTED_MEMBER_BUT_MISSED_COLLISION"
                    if model_class == "RESOLVED" and slot in (0, 1) else
                    "MODEL_OWNER_DISAGREE"
                )
            elif owner_class == "UNKNOWN":
                classification = (
                    "OWNER_MODEL_AGREE_UNKNOWN"
                    if model_class == "UNKNOWN" else "MODEL_OWNER_DISAGREE"
                )
            else:
                classification = (
                    "OWNER_MODEL_AGREE_SINGLE_SOURCE_GROUNDED"
                    if model_class == "RESOLVED" and slot == expected_slots[0]
                    else "MODEL_OWNER_DISAGREE"
                )
            results.append({
                "case": i, "owner_resolution": owner_class,
                "model_resolution": model_class,
                "model_selected_slot": slot,
                "classification": classification,
                "categorical_agreement": classification.startswith(
                    "OWNER_MODEL_AGREE"
                ),
            })
    except (TypeError, KeyError, ValueError):
        return _hold("MALFORMED_REDACTED_CASE")
    aligned = all(row["categorical_agreement"] for row in results)
    return {
        "schema": COMPARE_SCHEMA,
        "status": "AGREEMENT_ON_BOUNDED_SAMPLE_ONLY" if aligned else "HOLD",
        "reason": (
            "CATEGORICAL_AGREEMENT_NOT_SEMANTIC_OR_RELEASE_PROOF"
            if aligned else "OWNER_MODEL_CATEGORICAL_DISAGREEMENT"
        ),
        "sample_fingerprint": left,
        "sample_match_verified": True,
        "case_results": results,
        "categorical_agreement_proven": aligned,
        "general_semantic_quality_proven": False,
        "historical_coverage": False,
        "full_readiness_status": "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN",
        "model_called": False,
        "writes_performed": [],
        "release_activated": False,
    }
