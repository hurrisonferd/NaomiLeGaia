"""Stage9P: safe replay of previously signed owner-only GALAXY evidence.

No historical source is upgraded, no unsigned model receipt is back-signed,
and no source statements or private questions appear in this finite report.
The existing owner one-click endpoint may invoke this after the HEATDEATH,
remote-store, and two-current-literal gates have succeeded.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import augury_semantic_receipts as receipts
import gaiaos_memory_mode as mode

SCHEMA = "gaiaos.galaxy.stage9p.signed-owner-evidence-replay.v1"
_OWNER_FILE = "STAGE9I-LIVE-OWNER-ORACLE-OWNER-RELAY-REDACTED-2026-09-25.json"
_COLLISION_FILE = "STAGE9I-LIVE-TWO-SOURCE-OWNER-RELAY-REDACTED-2026-09-25.json"
_HOLD = frozenset({
    "OWNER_KEY_UNAVAILABLE", "ARCHIVED_RECEIPT_UNAVAILABLE",
    "ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED",
    "ARCHIVED_OWNER_COLLISION_CONTRACT_UNVERIFIED",
    "HEATDEATH_RELEASE_LOCK_UNVERIFIED",
    "LIVE_SOURCE_SAMPLE_UNAVAILABLE",
    "ARCHIVED_SAMPLE_NOT_CURRENT",
    "RELEASE_LOCK_CHANGED",
})


def _hold(reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": "HOLD",
        "reason": reason if reason in _HOLD else "ARCHIVED_RECEIPT_UNAVAILABLE",
        "source_attestations_verified": False,
        "live_sample_matches_archive": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "new_model_call_performed": False,
        "writes_performed": [], "e_lanes_modified": False,
        "release_activated": False,
    }


def _proof_directory() -> Path | None:
    """Both the repo checkout and deployed normal image are supported."""
    home = Path(__file__).resolve().parent
    for directory in (
        home / "GaiaOS" / "Proof",
        home.parent / "GaiaOS" / "Proof",
    ):
        if (directory / _OWNER_FILE).is_file() and (
            directory / _COLLISION_FILE
        ).is_file():
            return directory
    return None


def _read_signed(directory: Path, basename: str) -> dict[str, Any]:
    path = directory / basename
    if not path.is_file() or path.stat().st_size > 12000:
        raise ValueError("Archived bounded receipt unavailable")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid receipt shape")
    return data


def _locked(runtime: Any) -> dict[str, Any] | None:
    state = mode.mode_status(runtime)
    if (
        not isinstance(state, dict)
        or state.get("schema") != mode.SCHEMA
        or state.get("effective_mode") != mode.HEATDEATH
        or state.get("bigbang_activation_enabled") is not False
        or state.get("writes_performed") != []
    ):
        return None
    return state


def audit(
    runtime: Any, *, owner_key: str | None,
    proof_directory: Path | None = None,
    preview_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Verify two signed archived receipts and bind to today's live sample.

    The private current preview stays within the server. Returned fields are
    fixed booleans, enums and bounded small integers, never input data.
    """
    if not isinstance(owner_key, str) or not owner_key.strip():
        return _hold("OWNER_KEY_UNAVAILABLE")
    directory = proof_directory or _proof_directory()
    if directory is None:
        return _hold("ARCHIVED_RECEIPT_UNAVAILABLE")
    try:
        owner = _read_signed(directory, _OWNER_FILE)
        collision = _read_signed(directory, _COLLISION_FILE)
    except (OSError, UnicodeError, ValueError):
        return _hold("ARCHIVED_RECEIPT_UNAVAILABLE")
    if (
        not receipts.verified("owner", owner, owner_key=owner_key)
        or not receipts.verified("collision", collision, owner_key=owner_key)
    ):
        return _hold("ARCHIVED_ATTESTATION_INVALID_OR_KEY_ROTATED")
    rows = owner["case_results"]
    if (
        [row["case"] for row in rows] != [0, 1, 2]
        or [row["owner_resolution"] for row in rows] != [
            "B", "A", "COLLISION"
        ]
        or collision["case"] != 2
        or collision["sample_fingerprint"] != owner["sample_fingerprint"]
        or collision["quote_exact_verified"] != [True, True]
        or collision["strict_literal_compiled"] != [True, True]
        or collision["galaxy_readback_verified"] != [True, True]
        or collision["legacy_exact_parity"] is not True
    ):
        return _hold("ARCHIVED_OWNER_COLLISION_CONTRACT_UNVERIFIED")
    try:
        before = _locked(runtime)
        if before is None:
            return _hold("HEATDEATH_RELEASE_LOCK_UNVERIFIED")
        if preview_fn is None:
            import augury_semantic_retrieval as shadow
            preview_fn = shadow.owner_oracle_preview
        preview = preview_fn(runtime, fingerprint_key=owner_key)
        after = _locked(runtime)
    except Exception:
        return _hold("LIVE_SOURCE_SAMPLE_UNAVAILABLE")
    if (
        after is None
        or any(
            before.get(field) != after.get(field)
            for field in ("configured_mode", "effective_mode", "control_version")
        )
    ):
        return _hold("RELEASE_LOCK_CHANGED")
    if (
        not isinstance(preview, dict)
        or preview.get("schema")
            != "gaiaos.augury.semantic-owner-oracle-preview.v1"
        or preview.get("status") != "READY_OWNER_ADJUDICATION"
        or preview.get("sample_fingerprint_bound") is not True
        or preview.get("model_called") is not False
        or preview.get("writes_performed") != []
        or preview.get("release_activated") is not False
        or not isinstance(preview.get("records"), list)
        or len(preview["records"]) != 2
        or not isinstance(preview.get("questions"), list)
        or len(preview["questions"]) != 3
    ):
        return _hold("LIVE_SOURCE_SAMPLE_UNAVAILABLE")
    if preview.get("sample_fingerprint") != owner["sample_fingerprint"]:
        return _hold("ARCHIVED_SAMPLE_NOT_CURRENT")

    return {
        "schema": SCHEMA,
        "status": "PASS_ARCHIVED_OWNER_EVIDENCE_CURRENT_SAMPLE",
        "reason": "ARCHIVED_ATTESTATIONS_REBOUND_TO_CURRENT_SAMPLE",
        "source_attestations_verified": True,
        "live_sample_matches_archive": True,
        "owner_labeled_current_cases": 3,
        "owner_single_source_cases": 2,
        "owner_collision_cases": 1,
        "archived_two_source_literal_readback_attested": True,
        "archived_signed_model_receipt_in_repo": False,
        "model_comparison_performed": False,
        "semantic_entailment_independently_proven": False,
        "historical_retrieval_proven": False,
        "general_semantic_quality_proven": False,
        "new_model_call_performed": False,
        "writes_performed": [],
        "e_lanes_modified": False,
        "release_activated": False,
        "proof_boundary": (
            "An archived HMAC-signed owner judgment and two-source literal "
            "readback match today's approved source sample. This does not "
            "independently establish semantic entailment, historical "
            "supersession, or broad retrieval accuracy. An unsigned older "
            "model receipt has not been upgraded or used."
        ),
    }
