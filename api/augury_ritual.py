"""GaiaOS AUGURY/RITUAL Phase-1 exact ritual boundary.

Phase 1 intentionally does not claim a general natural-language AUGURY parser.
It freezes the semantic laws and provides exact Ritual compilation/validation.

The first effectful Ritual family is the bounded GALAXY Phase-4 controlled
SUPERSEDES fixture. Natural language never reaches manifestation here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import galaxy_phase4

VERSION = "augury-ritual.phase1.v1"
SEMANTIC_SCHEMA = "gaiaos.semantic-unit.v1"
COMPILATION_SCHEMA = "gaiaos.ritual.compilation-receipt.v1"
MANIFESTATION_SCHEMA = "gaiaos.ritual.manifestation-receipt.v1"

PROTOCOL_PATH = Path("GaiaOS/SystemsOS/Core/BrainOS/Protocols/AUGURY-RITUAL-CONSERVATION.v1.md")
SEMANTIC_SCHEMA_PATH = Path("GaiaOS/SystemsOS/Core/BrainOS/Schemas/GAIA-SEMANTIC-UNIT.v1.schema.json")
GRIMOIRE_PATH = Path("GaiaOS/SystemsOS/Core/BrainOS/Protocols/RITUAL-GRIMOIRE.v1.json")

PROPOSE_ID = "GALAXY.PHASE4.PROPOSE_SUPERSEDES.CONTROLLED_FIXTURE"
VERIFY_ID = "GALAXY.PHASE4.VERIFY_SUPERSEDES.CONTROLLED_FIXTURE"
REVOKE_ID = "GALAXY.PHASE4.REVOKE_SUPERSEDES.CONTROLLED_FIXTURE"

SOURCE_ID = galaxy_phase4.FIXTURE_REVISION_ID
TARGET_ID = galaxy_phase4.FIXTURE_CORE_ID

CONFIRMATIONS = {
    PROPOSE_ID: "MANIFEST_GALAXY_PHASE4_PROPOSE_SUPERSEDES_CONTROLLED_FIXTURE",
    VERIFY_ID: "MANIFEST_GALAXY_PHASE4_VERIFY_SUPERSEDES_CONTROLLED_FIXTURE",
    REVOKE_ID: "MANIFEST_GALAXY_PHASE4_REVOKE_SUPERSEDES_CONTROLLED_FIXTURE",
}


def _root() -> Path:
    return Path(__file__).resolve().parent


def _source_path(relative: Path) -> Path:
    direct = _root() / relative
    if direct.exists():
        return direct
    return _root().parent / relative


def load_grimoire() -> dict[str, Any]:
    path = _source_path(GRIMOIRE_PATH)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "gaiaos.ritual-grimoire.v1":
        raise RuntimeError("Unexpected Ritual Grimoire schema")
    return data


def ritual_contract(ritual_id: str) -> dict[str, Any]:
    ritual_id = str(ritual_id or "").strip()
    for ritual in load_grimoire().get("rituals", []):
        if ritual.get("ritual_id") == ritual_id:
            return ritual
    raise KeyError(ritual_id)


def _controlled_edges(runtime: Any) -> list[dict[str, Any]]:
    detail = runtime.galaxy_record(SOURCE_ID)
    relations = list((detail or {}).get("relations") or [])
    edges = [
        edge for edge in relations
        if str(edge.get("source_record_id")) == SOURCE_ID
        and str(edge.get("target_record_id")) == TARGET_ID
        and str(edge.get("relation_type")) == "SUPERSEDES"
    ]
    return sorted(
        edges,
        key=lambda edge: (
            str(edge.get("created_at") or ""),
            str(edge.get("edge_id") or ""),
        ),
        reverse=True,
    )


def phase1_status(runtime: Any) -> dict[str, Any]:
    review = galaxy_phase4.review_pair(runtime, SOURCE_ID, TARGET_ID, "SUPERSEDES")
    edges = _controlled_edges(runtime)
    return {
        "schema": "gaiaos.augury-ritual.phase1-status.v1",
        "version": VERSION,
        "execution": "READ_ONLY",
        "authority": "NAOMI",
        "augury": {
            "general_natural_language_parser_implemented": False,
            "semantic_unit_schema_source_ready": _source_path(SEMANTIC_SCHEMA_PATH).exists(),
            "conservation_contract_source_ready": _source_path(PROTOCOL_PATH).exists(),
            "law": "AUGURY_MAY_BE_AMBIGUOUS_RITUAL_MAY_NOT_BE",
        },
        "ritual": {
            "grimoire_source_ready": _source_path(GRIMOIRE_PATH).exists(),
            "exact_compiler_available": True,
            "natural_language_manifestation_allowed": False,
            "controlled_phase4_family": [PROPOSE_ID, VERIFY_ID, REVOKE_ID],
        },
        "phase4_controlled_fixture": {
            "source_record_id": SOURCE_ID,
            "target_record_id": TARGET_ID,
            "pair_review": review,
            "supersedes_edges": edges,
            "proposed_edge_ids": [
                e.get("edge_id") for e in edges if e.get("status") == "PROPOSED"
            ],
            "verified_edge_ids": [
                e.get("edge_id") for e in edges if e.get("status") == "VERIFIED"
            ],
            "revoked_edge_ids": [
                e.get("edge_id") for e in edges if e.get("status") == "REVOKED"
            ],
            "target_governing_state": runtime.galaxy_governing_state(TARGET_ID),
        },
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "Status and compilation are read-only. Phase 1 does not implement "
            "general natural-language AUGURY. Manifestation occurs only through "
            "an exact Ritual ID plus explicit Naomi authority and confirmation."
        ),
    }


def compile_exact(
    runtime: Any,
    ritual_id: str,
    params: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate one exact ritual without performing effects."""
    ritual_id = str(ritual_id or "").strip()
    params = dict(params or {})
    contract = ritual_contract(ritual_id)
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    if ritual_id == PROPOSE_ID:
        source = str(params.get("source_record_id") or "")
        target = str(params.get("target_record_id") or "")
        if source != SOURCE_ID:
            errors.append("CONTROLLED_SOURCE_MISMATCH")
        if target != TARGET_ID:
            errors.append("CONTROLLED_TARGET_MISMATCH")
        review = galaxy_phase4.review_pair(runtime, SOURCE_ID, TARGET_ID, "SUPERSEDES")
        if review.get("status") != "PASS_READ_ONLY_REVIEW":
            errors.append("PHASE4_PAIR_REVIEW_HOLD")
        if any(e.get("status") in {"PROPOSED", "VERIFIED"} for e in _controlled_edges(runtime)):
            errors.append("ACTIVE_SUPERSEDES_EDGE_ALREADY_EXISTS")
        normalized = {
            "source_record_id": SOURCE_ID,
            "target_record_id": TARGET_ID,
            "relation_type": "SUPERSEDES",
            "strength": 1.0,
        }
        invocation = (
            f"RITUAL {PROPOSE_ID} source={SOURCE_ID} target={TARGET_ID}"
        )

    elif ritual_id == VERIFY_ID:
        edge_id = str(params.get("edge_id") or "").strip()
        edge = runtime.galaxy_relation(edge_id) if edge_id else None
        if edge is None:
            errors.append("EXACT_EDGE_NOT_FOUND")
        else:
            if edge.get("source_record_id") != SOURCE_ID:
                errors.append("CONTROLLED_SOURCE_MISMATCH")
            if edge.get("target_record_id") != TARGET_ID:
                errors.append("CONTROLLED_TARGET_MISMATCH")
            if edge.get("relation_type") != "SUPERSEDES":
                errors.append("RELATION_TYPE_MISMATCH")
            if edge.get("status") != "PROPOSED":
                errors.append("EDGE_NOT_PROPOSED")
        normalized = {"edge_id": edge_id}
        invocation = f"RITUAL {VERIFY_ID} edge={edge_id}"

    elif ritual_id == REVOKE_ID:
        edge_id = str(params.get("edge_id") or "").strip()
        reason = str(params.get("reason") or "").strip()
        edge = runtime.galaxy_relation(edge_id) if edge_id else None
        if edge is None:
            errors.append("EXACT_EDGE_NOT_FOUND")
        else:
            if edge.get("source_record_id") != SOURCE_ID:
                errors.append("CONTROLLED_SOURCE_MISMATCH")
            if edge.get("target_record_id") != TARGET_ID:
                errors.append("CONTROLLED_TARGET_MISMATCH")
            if edge.get("relation_type") != "SUPERSEDES":
                errors.append("RELATION_TYPE_MISMATCH")
            if edge.get("status") != "VERIFIED":
                errors.append("EDGE_NOT_VERIFIED")
        if not reason:
            errors.append("REVOCATION_REASON_REQUIRED")
        normalized = {"edge_id": edge_id, "reason": reason}
        invocation = f"RITUAL {REVOKE_ID} edge={edge_id} reason=<NONEMPTY>"

    else:
        errors.append("RITUAL_NOT_BOUND_TO_PHASE1_MANIFESTATION")
        invocation = str(contract.get("canonical_invocation") or ritual_id)

    return {
        "schema": COMPILATION_SCHEMA,
        "version": VERSION,
        "execution": "READ_ONLY",
        "ritual_id": ritual_id,
        "ritual_version": contract.get("ritual_version"),
        "resolution": "VALID" if not errors else "HOLD",
        "canonical_invocation": invocation,
        "normalized_params": normalized,
        "errors": errors,
        "authority_required": contract.get("authority_requirement"),
        "effect_class": contract.get("effect_class"),
        "manifestation_performed": False,
        "proof_boundary": (
            "Compilation validates exact Ritual identity and typed parameters. "
            "It grants no authority and performs no effect."
        ),
    }


def manifest(
    runtime: Any,
    ritual_id: str,
    params: dict[str, Any] | None,
    *,
    authority: str,
    approved: bool,
    confirmation: str,
) -> dict[str, Any]:
    """Manifest one exact bounded Phase-4 ritual after compilation + authority."""
    if authority != "NAOMI" or approved is not True:
        raise PermissionError("Ritual manifestation requires explicit Naomi approval")
    expected_confirmation = CONFIRMATIONS.get(str(ritual_id or "").strip())
    if not expected_confirmation or confirmation != expected_confirmation:
        raise PermissionError("Exact Ritual manifestation confirmation required")

    compilation = compile_exact(runtime, ritual_id, params)
    if compilation.get("resolution") != "VALID":
        return {
            "schema": MANIFESTATION_SCHEMA,
            "version": VERSION,
            "status": "HOLD",
            "ritual_id": ritual_id,
            "compilation": compilation,
            "manifestation_performed": False,
        }

    normalized = compilation["normalized_params"]
    before = phase1_status(runtime)

    if ritual_id == PROPOSE_ID:
        effect = galaxy_phase4.propose_transition(
            runtime,
            SOURCE_ID,
            TARGET_ID,
            "SUPERSEDES",
            strength=1.0,
            evidence={
                "basis": "AUGURY/RITUAL Phase-1 controlled Phase-4 manifestation",
                "ritual_id": PROPOSE_ID,
                "source": "RITUAL_GRIMOIRE_V1",
            },
            authority="NAOMI",
            approved=True,
            confirmation="PROPOSE_GALAXY_PHASE4_RELATION",
        )
        expected = effect.get("status") in {"PROPOSED", "EXISTING"}

    elif ritual_id == VERIFY_ID:
        effect = galaxy_phase4.verify_transition(
            runtime,
            normalized["edge_id"],
            authority="NAOMI",
            approved=True,
            confirmation="VERIFY_GALAXY_PHASE4_RELATION",
        )
        expected = (
            effect.get("status") == "VERIFIED"
            and effect.get("after", {}).get("target_governing_state", {}).get("state")
            == "HISTORICAL_SUPERSEDED"
        )

    elif ritual_id == REVOKE_ID:
        effect = galaxy_phase4.revoke_transition(
            runtime,
            normalized["edge_id"],
            authority="NAOMI",
            approved=True,
            reason=normalized["reason"],
            confirmation="REVOKE_GALAXY_PHASE4_RELATION",
        )
        expected = (
            effect.get("status") == "REVOKED"
            and effect.get("after", {}).get("target_governing_state", {}).get("state")
            == "CURRENT_REVISED_CONTEXT"
        )

    else:
        raise ValueError("Unsupported Phase-1 manifested ritual")

    after = phase1_status(runtime)
    return {
        "schema": MANIFESTATION_SCHEMA,
        "version": VERSION,
        "execution": "OBSERVED_RUNTIME",
        "authority": "NAOMI",
        "status": "PASS" if expected else "HOLD",
        "ritual_id": ritual_id,
        "compilation": compilation,
        "manifestation_performed": bool(expected),
        "before_target_governing_state": (
            before.get("phase4_controlled_fixture", {}).get("target_governing_state")
        ),
        "effect": effect,
        "after_target_governing_state": (
            after.get("phase4_controlled_fixture", {}).get("target_governing_state")
        ),
        "history_preserved": True,
        "physical_delete": False,
        "production_retrieval_changed": False,
        "unrestricted_global_weighting_enabled": False,
        "proof_boundary": (
            "This receipt proves only this exact controlled Ritual call in the "
            "current carrier/runtime store. It does not prove general AUGURY, "
            "generic Phase-4 mutation, or unrestricted production behavior."
        ),
    }
