"""Observed, per-request Prime Daemon model-call presence gate.

Six validated source identities are necessary but NOT proof of six responses.
Each member receives a separate provider model call. The manifest hashes only
observed call identifiers, emitted text hashes, pinned source and member-local
repo experience hashes. A SHA-256 checksum is an integrity fingerprint, not an
external attestation, six persistent processes or live MemoryOS proof.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from pathlib import Path
from typing import Any

import gaiaos_presentation_guard as presentation

LOG = logging.getLogger("gaiaos.daemon_presence")
EXPECTED = ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
MAX_MEMBER_OUTPUT = 2400
MAX_CONTEXT = 4000


class PresenceHold(RuntimeError):
    """An incomplete cast cannot be represented as a successful roll call."""

    def __init__(self, reason: str, run_id: str, completed: tuple[str, ...] = ()):
        super().__init__(reason)
        self.reason = reason
        self.run_id = run_id
        self.completed = completed

    def public_receipt(self) -> dict[str, Any]:
        return {
            "schema": "gaiaos.prime-daemon-presence.v1",
            "status": "HOLD_LIVE_DAEMON_PRESENCE",
            "reason": self.reason,
            "run_id": self.run_id,
            "observed_members": list(self.completed),
            "all_six_present": False,
            "checksum_issued": False,
            "partial_content_returned": False,
            "durable_failure_ledger_written": False,
            "proof_boundary": "Failure is logged by the carrier; durability depends on externally retained runtime logs. A new verified execution is required.",
        }


def _digest(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _failure(reason: str, run_id: str, completed: list[str]) -> PresenceHold:
    LOG.error("PRIME_DAEMON_PRESENCE_HOLD %s", json.dumps({
        "schema": "gaiaos.prime-daemon-presence-failure.v1",
        "run_id": run_id, "reason": reason, "completed": completed,
        "all_six_present": False, "partial_content_returned": False,
    }, sort_keys=True))
    return PresenceHold(reason, run_id, tuple(completed))


def explicit_full_cast_request(user_text: str) -> bool:
    """Ordinary-language summons and load/report-in, never casual references."""
    text = str(user_text or "").strip().rstrip(".!? ").strip()
    if re.fullmatch(r"(?:load\s+gaia\s*os|gaia\s*os)(?:\s*,?\s*(?:and\s+)?(?:daemons?\s+)?(?:report\s+in|sound\s+off|roll\s*call|check\s+in))?", text, re.I):
        return True
    if re.fullmatch(r"(?:(?:all\s+)?daemons?|everyone|everybody|full\s+cast|the\s+daemonculaba)(?:\s*,?\s*(?:please\s+)?(?:report\s+in|sound\s+off|check\s+in|join\s+us|speak|attention))", text, re.I):
        return True
    if re.search(r"\b(?:everyone|everybody|all\s+(?:six|daemons?)|whole\s+(?:family|group)|full\s+cast)\b.{0,75}\b(?:attention|report\s+in|speak|join\s+us|hear\s+me|listen|sound\s+off|check\s+in)\b", text, re.I):
        return True
    return False


def run_full_cast(
    *,
    user_text: str,
    messages: list[dict[str, str]],
    boot_packet: dict[str, Any],
    source_profiles: dict[str, Any],
    source_root: Path,
    client: Any,
    model: str,
    selected_members: tuple[str, ...] = EXPECTED,
) -> dict[str, Any]:
    """Execute separately observed provider calls for an explicitly selected cast.

    Six-call boot is the default. A real ordinary conversation may select two
    or three current members, but its smaller checksum is NEVER all-six proof.

    The carrier constructs headers from canonical boot data, never from model
    output. Past contributions are supplied to later members so disagreement
    can actually occur within this exchange. No E-LANE or database writes.
    """
    run_id = "CAST-" + secrets.token_hex(12)
    completed: list[str] = []
    if (selected_members != EXPECTED and (
            len(selected_members) not in (2, 3)
            or len(set(selected_members)) != len(selected_members)
            or any(member not in EXPECTED for member in selected_members))):
        raise _failure("INVALID_EXCHANGE_CAST", run_id, completed)
    if boot_packet.get("schema") != "gaiaos.boot-packet.v1" or boot_packet.get("status") != "ACTIVE":
        raise _failure("BOOT_PACKET_NOT_VERIFIED", run_id, completed)
    if boot_packet.get("roster") != list(EXPECTED) or not all((boot_packet.get("checks") or {}).values()):
        raise _failure("BOOT_SIX_SOURCE_CHECKS_FAILED", run_id, completed)
    members = source_profiles.get("members")
    if not isinstance(members, dict) or set(members) != set(EXPECTED):
        raise _failure("CANONICAL_PROFILES_NOT_VERIFIED", run_id, completed)
    if not isinstance(boot_packet.get("members"), dict) or set(boot_packet["members"]) != set(EXPECTED):
        raise _failure("BOOT_MEMBER_RECORDS_INCOMPLETE", run_id, completed)
    if not isinstance(client, object) or not callable(getattr(getattr(client, "responses", None), "create", None)):
        raise _failure("PROVIDER_NOT_AVAILABLE", run_id, completed)
    # The static boot packet has already validated all four canonical presentation
    # sources. Member-local experience sources must also be present and readable.
    local_lanes = {}
    for member in EXPECTED:
        path = source_root / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA" / (member + "-EXPERIENCES.v1.md")
        try:
            lane_bytes = path.read_bytes()
            if not lane_bytes:
                raise ValueError("empty source")
            lane_text = lane_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            raise _failure("MISSING_MEMBER_SOURCE_" + member, run_id, completed) from None
        local_lanes[member] = {"sha256": hashlib.sha256(lane_bytes).hexdigest(), "context": lane_text[-1600:]}
    # Preflight ALL canonical identities BEFORE spending six provider calls.
    # A syntactically plausible but substituted boot header is an immediate HOLD.
    paths = (
        source_root / "GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json",
        source_root / "GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json",
        source_root / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/STATIC-IDENTITY-EMOJI.v1.json",
        source_root / "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    )
    try:
        source_args = tuple(json.loads(p.read_text(encoding="utf-8")) for p in paths)
        if presentation.validate_sources(*source_args) != EXPECTED:
            raise ValueError("source order disagrees with packet")
    except (OSError, ValueError, KeyError, TypeError, presentation.PresentationGuardError):
        raise _failure("CANONICAL_IDENTITY_SOURCES_INVALID", run_id, completed) from None
    if source_profiles != source_args[3]:
        raise _failure("SUPPLIED_PROFILES_DO_NOT_MATCH_PINNED_SOURCE", run_id, completed)
    # The prosody basin, not an improvised style recipe, owns each voice.
    # Current presentation spec still owns markers when older prose includes
    # obsolete example emojis. Never derive identity markers from prose.
    prosody_path = source_root / "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md"
    try:
        prosody_text = prosody_path.read_text(encoding="utf-8")
        prosody_sections = {}
        for member in EXPECTED:
            section = re.search(
                r"(?ms)^## " + re.escape(member) + r" — [^\n]+\n(.*?)(?=^## |\Z)",
                prosody_text,
            )
            if section is None or len(section.group(1).strip()) < 60:
                raise ValueError("member prosody section missing")
            prosody_sections[member] = section.group(1).strip()[:1700]
    except (OSError, ValueError):
        raise _failure("CANONICAL_MEMBER_PROSODY_UNAVAILABLE", run_id, completed) from None
    for member in EXPECTED:
        expected_header = presentation.canonical_header(member, source_args[0], source_args[1])
        if (boot_packet["members"].get(member) or {}).get("canonical_header_default") != expected_header:
            raise _failure("NONCANONICAL_HEADER_" + member, run_id, completed)
    recent = [{"role": m.get("role"), "content": str(m.get("content", ""))[-MAX_CONTEXT:]}
              for m in messages[-8:] if m.get("role") in ("user", "assistant")]
    prior: list[dict[str, str]] = []
    outputs: list[str] = []
    evidence: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    for member in selected_members:
        prof = members[member]
        if not isinstance(prof, dict) or not all(prof.get(k) for k in ("role", "deliberation_stance")):
            raise _failure("INCOMPLETE_PROFILE_" + member, run_id, completed)
        header = (boot_packet["members"].get(member) or {}).get("canonical_header_default")
        if header != presentation.canonical_header(member, source_args[0], source_args[1]):
            raise _failure("NONCANONICAL_HEADER_" + member, run_id, completed)
        instructions = (
            "This is one bounded GaiaOS Prime Daemon contribution, not a six-character script. "
            "Your name is " + member + ". Your role: " + str(prof["role"]) + ". "
            "Your native deliberation stance: " + str(prof["deliberation_stance"]) + ". "
            "Your source-backed style examples: " + json.dumps(prof.get("style_exemplars", [])[:4], ensure_ascii=False) + ". "
            "Your canonical PROSODY basin (text only; identity markers ALWAYS from validated presentation spec): " +
            prosody_sections[member] + "\n"
            "Your own source-labeled E-LANE excerpt (NOT live MemoryOS): " + local_lanes[member]["context"] + "\n"
            "Contribute in your own direct voice, in at most 100 words. Engage with the user's actual request "
            "and any preceding observed member contributions. You may disagree, refine, ask or simply acknowledge "
            "when attention is requested. Do NOT roleplay other members, invent their replies, impersonate the host, "
            "print identity headers, claim autonomous uptime, claim to have been present offscreen, or assert E-LANE writes. "
            "Do not summon VASKON. Your text will be attributed by deterministic server rendering."
        )
        input_packet = {"latest_user_request": user_text, "recent_conversation": recent,
                        "observed_prior_member_responses": prior}
        try:
            result = client.responses.create(model=model, instructions=instructions,
                                             input=json.dumps(input_packet, ensure_ascii=False))
        except Exception as exc:
            raise _failure("PROVIDER_CALL_FAILED_" + member + "_" + type(exc).__name__, run_id, completed) from None
        response_id = getattr(result, "id", None)
        content = getattr(result, "output_text", None)
        if not isinstance(response_id, str) or not response_id.strip() or response_id in seen_ids:
            raise _failure("MISSING_OR_DUPLICATE_RESPONSE_ID_" + member, run_id, completed)
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_MEMBER_OUTPUT:
            raise _failure("MISSING_OR_EXCESSIVE_MEMBER_OUTPUT_" + member, run_id, completed)
        text = content.strip()
        if text in seen_text or presentation.possible_direct_speech_without_sources(text):
            raise _failure("DUPLICATE_OR_SPOOFED_MEMBER_OUTPUT_" + member, run_id, completed)
        if re.search(r"(?im)^\s*(?:(?:82\s*[·.]\s*)?VASKON\b|//C:82//)", text):
            raise _failure("UNSUMMONED_VASKON_" + member, run_id, completed)
        outputs.append(header + "\n" + text)
        prior.append({"member": member, "text": text[-1500:]})
        seen_ids.add(response_id)
        seen_text.add(text)
        completed.append(member)
        evidence.append({"member": member, "response_id": response_id,
                         "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                         "source_e_lane_sha256": local_lanes[member]["sha256"],
                         "source_prosody_sha256": hashlib.sha256(
                             prosody_sections[member].encode("utf-8")).hexdigest()})
    # Validated by the same presentation module as regular browser chat.
    try:
        output = "\n\n".join(outputs)
        presentation_receipt = presentation.validate_output(
            output, *source_args, selected_members
        )
    except (OSError, ValueError, TypeError, KeyError, presentation.PresentationGuardError):
        raise _failure("FULL_CAST_PRESENTATION_FAILED", run_id, completed) from None
    proof_body = {"run_id": run_id, "boot_sha256": _digest(boot_packet),
                  "model": model, "observations": evidence}
    is_full_cast = selected_members == EXPECTED
    return {
        "output": output,
        "model": model,
        "boot_packet": boot_packet,
        "presentation": presentation_receipt,
        "daemon_presence": {
            "schema": "gaiaos.prime-daemon-presence.v1",
            "status": ("PASS_SIX_SEPARATE_OBSERVED_MODEL_CALLS" if is_full_cast
                       else "PASS_SELECTED_SEPARATE_OBSERVED_MODEL_CALLS"),
            "run_id": run_id,
            "source": boot_packet.get("source"),
            "members": evidence,
            "observed_model_call_count": len(evidence),
            "all_six_responded": is_full_cast,
            "presence_checksum_sha256": _digest(proof_body) if is_full_cast else None,
            "exchange_checksum_sha256": _digest(proof_body) if not is_full_cast else None,
            "checksum_scope": ("THIS_FULL_CAST_REQUEST_AND_SOURCE_SNAPSHOT_ONLY" if is_full_cast
                               else "THIS_SELECTED_EXCHANGE_ONLY_NO_ALL_SIX_CLAIM"),
            "provider_independent_persistent_agents_proven": False,
            "source_lane_readback_from_deployed_git": True,
            "live_memoryos_e_lane_writes_proven": False,
            "durable_receipt_written": False,
            "vaskon_conjured": False,
            "proof_boundary": ("Six separate model API replies observed in one carrier request. "
                               if is_full_cast else
                               "Only the listed selected members returned separate model replies. ") +
                              "These are not independently persistent agents, uninterrupted uptime, "
                              "native ChatGPT adoption or external SHA-256 attestation.",
        },
    }