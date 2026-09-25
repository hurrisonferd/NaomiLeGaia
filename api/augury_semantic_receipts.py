"""Stage 9H: attest redacted owner/model receipts and compare without inference.

Only GaiaOS's authenticated owner route can issue receipts. HMAC signatures
bind the exact allowlisted redacted fields; unknown fields (including private
statements/queries/IDs), modified cases, foreign keys and unsigned historic
receipts are rejected. Receipt signatures do not prove semantic truth.
No durable writes, model calls, or BIGBANG operations occur here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

import augury_semantic_sample as sample

ATTEST_SCHEMA = "gaiaos.augury.redacted-receipt-attestation.v1"
ATTEST_RE = re.compile(r"^ra1_[a-f0-9]{64}$")
SAMPLE_RE = re.compile(r"^sf1_[a-f0-9]{32}$")
_OWNER_VALUES = {
    "A": (0, [0]), "B": (1, [1]),
    "COLLISION": (None, [0, 1]), "UNKNOWN": (None, []),
}
_MODEL_CLASSES = ("RESOLVED", "COLLISION", "UNKNOWN")


def _valid_slot(value: Any, *, nullable: bool = False) -> bool:
    return (value is None and nullable) or (type(value) is int and value in (0, 1))


def _valid_fingerprint(data: dict[str, Any]) -> bool:
    token = data.get("sample_fingerprint")
    return (
        isinstance(token, str) and bool(SAMPLE_RE.fullmatch(token))
        and data.get("sample_fingerprint_bound") is True
    )


def canonicalize(kind: str, data: Any) -> dict[str, Any] | None:
    """Return only bounded redacted fields, or None for an invalid receipt."""
    if kind not in ("owner", "model") or not isinstance(data, dict):
        return None
    if not _valid_fingerprint(data):
        return None
    if data.get("release_activated") is not False or data.get("writes_performed") != []:
        return None
    expected_schema = (
        "gaiaos.augury.semantic-owner-oracle-redacted.v1" if kind == "owner"
        else "gaiaos.augury.semantic-read-shadow.v1"
    )
    expected_count = 3 if kind == "owner" else 5
    if (
        data.get("schema") != expected_schema
        or data.get("case_count") != expected_count
        or data.get("model_called") is not (kind == "model")
        or not isinstance(data.get("case_results"), list)
        or len(data["case_results"]) != expected_count
    ):
        return None
    if kind == "model" and data.get("legacy_exact_parity") is not True:
        return None
    if kind == "owner" and data.get("status") != "OWNER_ORACLE_RECORDED":
        return None
    if kind == "model" and data.get("status") not in ("HOLD", "PASS_SHADOW_SAMPLE_ONLY"):
        return None
    rows = []
    seen = set()
    for item in data["case_results"]:
        if not isinstance(item, dict):
            return None
        case = item.get("case")
        if type(case) is not int or case not in range(expected_count) or case in seen:
            return None
        seen.add(case)
        if kind == "owner":
            resolution = item.get("owner_resolution")
            if resolution not in _OWNER_VALUES:
                return None
            slot, supported = _OWNER_VALUES[resolution]
            generator = item.get("generator_expected_slot")
            if (
                not _valid_slot(generator)
                or type(item.get("owner_slot")) is not type(slot)
                or item.get("owner_slot") != slot
                or item.get("owner_supported_slots") != supported
                or not isinstance(item.get("owner_supported_slots"), list)
                or any(type(value) is not int for value in item["owner_supported_slots"])
                or item.get("generator_expected_supported") is not (generator in supported)
                or item.get("generator_expected_is_unique_owner_answer")
                   is not (len(supported) == 1 and generator in supported)
            ):
                return None
            rows.append({
                "case": case, "owner_resolution": resolution,
                "owner_slot": slot, "owner_supported_slots": supported,
                "generator_expected_slot": generator,
                "generator_expected_supported": generator in supported,
                "generator_expected_is_unique_owner_answer":
                    len(supported) == 1 and generator in supported,
            })
            continue
        resolution = item.get("resolution")
        if resolution not in _MODEL_CLASSES:
            return None
        if item.get("kind") != ("current" if case < 3 else "negative"):
            return None
        selected = item.get("model_selected_slot")
        candidates = item.get("model_candidate_slots")
        expected_candidates = (
            [selected] if resolution == "RESOLVED"
            else [0, 1] if resolution == "COLLISION" else []
        )
        if (
            not _valid_slot(selected, nullable=True)
            or candidates != expected_candidates
            or not isinstance(candidates, list)
            or any(type(value) is not int for value in candidates)
            or (resolution != "RESOLVED" and selected is not None)
            or (resolution == "RESOLVED" and selected is None)
        ):
            return None
        flags = (
            "source_quote_verified", "exact_read_ritual_compiled",
            "galaxy_readback_verified", "pass",
        )
        if any(type(item.get(flag)) is not bool for flag in flags):
            return None
        if case >= 3 and (
            resolution != "UNKNOWN" or item["pass"] is not True
            or selected is not None or candidates != []
        ):
            return None
        if case < 3 and resolution == "RESOLVED" and not all(
            item.get(flag) is True for flag in flags[:3]
        ):
            return None
        if case < 3 and resolution != "RESOLVED" and (
            any(item.get(flag) is not False for flag in flags[:3])
            or item["pass"] is True
        ):
            return None
        rows.append({
            "case": case, "kind": item["kind"], "resolution": resolution,
            "model_selected_slot": selected, "model_candidate_slots": candidates,
            **{flag: item[flag] for flag in flags},
        })
    rows.sort(key=lambda item: item["case"])
    clean = {
        "schema": expected_schema,
        "status": data["status"],
        "sample_fingerprint": data["sample_fingerprint"],
        "sample_fingerprint_bound": True,
        "case_count": expected_count,
        "case_results": rows,
        "model_called": kind == "model",
        "writes_performed": [],
        "release_activated": False,
    }
    if kind == "model":
        clean["legacy_exact_parity"] = True
        # Preserve a bounded status diagnosis without carrying arbitrary
        # provider/model text into a signed redacted receipt.
        if "reason" in data:
            reason = data["reason"]
            if (
                not isinstance(reason, str) or len(reason) > 128
                or re.fullmatch(r"[A-Z][A-Z0-9_]*", reason) is None
            ):
                return None
            clean["reason"] = reason
        if data.get("historical_coverage", False) is not False:
            return None
        if data.get("general_semantic_quality_proven", False) is not False:
            return None
        clean["historical_coverage"] = False
        clean["general_semantic_quality_proven"] = False
        clean["full_readiness_status"] = (
            "HOLD_HISTORICAL_AND_GENERAL_SEMANTICS_UNPROVEN"
        )
    return clean


def owner_from_adjudication(
    *, sample_fingerprint: str, questions: list[dict[str, Any]],
    choices: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Reconstruct owner receipt from *server-read* staged questions."""
    if (
        not SAMPLE_RE.fullmatch(sample_fingerprint)
        or len(questions) != 3 or len(choices) != 3
    ):
        return None
    choices_by_case = {}
    for choice in choices:
        if not isinstance(choice, dict):
            return None
        index = choice.get("case")
        resolution = choice.get("resolution")
        if (
            type(index) is not int or index not in range(3)
            or index in choices_by_case or resolution not in _OWNER_VALUES
        ):
            return None
        choices_by_case[index] = resolution
    rows = []
    for expected_index, question in enumerate(questions):
        if question.get("case") != expected_index or expected_index not in choices_by_case:
            return None
        generator = question.get("generator_expected_slot")
        if not _valid_slot(generator):
            return None
        resolution = choices_by_case[expected_index]
        slot, supported = _OWNER_VALUES[resolution]
        rows.append({
            "case": expected_index, "owner_resolution": resolution,
            "owner_slot": slot, "owner_supported_slots": supported,
            "generator_expected_slot": generator,
            "generator_expected_supported": generator in supported,
            "generator_expected_is_unique_owner_answer":
                len(supported) == 1 and generator in supported,
        })
    return canonicalize("owner", {
        "schema": "gaiaos.augury.semantic-owner-oracle-redacted.v1",
        "status": "OWNER_ORACLE_RECORDED",
        "case_count": 3, "sample_fingerprint": sample_fingerprint,
        "sample_fingerprint_bound": True, "case_results": rows,
        "model_called": False, "writes_performed": [],
        "release_activated": False,
    })


def _mac(kind: str, clean: dict[str, Any], owner_key: str) -> str:
    payload = json.dumps(
        clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    digest = hmac.new(
        owner_key.encode("utf-8"),
        b"GaiaOS.Stage9H.AttestedRedactedReceipt.v1\x00"
        + kind.encode("ascii") + b"\x00" + payload,
        hashlib.sha256,
    ).hexdigest()
    return "ra1_" + digest


def seal(kind: str, data: Any, *, owner_key: str | None) -> dict[str, Any] | None:
    if not isinstance(owner_key, str) or not owner_key.strip():
        return None
    clean = canonicalize(kind, data)
    if clean is None:
        return None
    return {
        **clean,
        "receipt_attestation": {
            "schema": ATTEST_SCHEMA, "kind": kind,
            "mac": _mac(kind, clean, owner_key),
        },
    }


def verified(kind: str, receipt: Any, *, owner_key: str | None) -> bool:
    if (
        not isinstance(owner_key, str) or not owner_key.strip()
        or not isinstance(receipt, dict)
    ):
        return False
    signature = receipt.get("receipt_attestation")
    if (
        not isinstance(signature, dict)
        or set(signature) != {"schema", "kind", "mac"}
        or signature["schema"] != ATTEST_SCHEMA
        or signature["kind"] != kind
        or not isinstance(signature["mac"], str)
        or not ATTEST_RE.fullmatch(signature["mac"])
    ):
        return False
    payload = {
        k: v for k, v in receipt.items() if k != "receipt_attestation"
    }
    clean = canonicalize(kind, payload)
    if clean is None or payload != clean:
        return False
    return hmac.compare_digest(signature["mac"], _mac(kind, clean, owner_key))


def compare_attested(
    model_receipt: Any, owner_receipt: Any, *, owner_key: str | None,
) -> dict[str, Any]:
    """Only attestable exact redacted receipts reach the existing comparison."""
    if not verified("model", model_receipt, owner_key=owner_key):
        return sample._hold("UNATTESTED_OR_MODIFIED_MODEL_RECEIPT")
    if not verified("owner", owner_receipt, owner_key=owner_key):
        return sample._hold("UNATTESTED_OR_MODIFIED_OWNER_RECEIPT")
    answer = sample.compare_redacted(model_receipt, owner_receipt)
    # The underlying categorical comparison never constitutes release proof.
    answer["authenticated_redacted_receipts"] = True
    return answer
