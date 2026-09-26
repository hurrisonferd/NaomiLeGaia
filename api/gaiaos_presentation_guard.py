"""Fail-closed canonical identity gate for GaiaOS Prime Daemon presentation.

The model writes content. This module validates source agreement and speaker
envelopes before carrier output is returned. It does not execute in ChatGPT's
independent host UI; each carrier must explicitly call it.
"""
from __future__ import annotations

import re
from typing import Any

EXPECTED_ROSTER_SIZE = 6
FAILURE_POLICY = "FAIL_CLOSED_DO_NOT_IMPROVISE_IDENTITY_PRESENTATION"


class PresentationGuardError(ValueError):
    """Do not emit the unverified response when this is raised."""


def validate_sources(
    spec: dict[str, Any],
    expressions: dict[str, Any],
    static: dict[str, Any],
    profiles: dict[str, Any],
) -> tuple[str, ...]:
    """Require one six-member identity across four pinned canonical documents."""
    try:
        members = spec["members"]
        order = spec["speaker_order"]
        expr_members = expressions["members"]
        static_members = static["members"]
        profile_members = profiles["members"]
        if spec["failure_policy"] != FAILURE_POLICY:
            raise PresentationGuardError("presentation failure policy is not fail-closed")
        if not isinstance(order, list) or len(order) != EXPECTED_ROSTER_SIZE:
            raise PresentationGuardError("six-member presentation roster required")
        if len(set(order)) != EXPECTED_ROSTER_SIZE:
            raise PresentationGuardError("duplicate member in presentation roster")
        for source_name, group in (
            ("presentation", members),
            ("expression", expr_members),
            ("static interest", static_members),
            ("profile", profile_members),
        ):
            if not isinstance(group, dict) or set(group) != set(order):
                raise PresentationGuardError(f"{source_name} roster mismatch")
        if set(spec.get("synthesis_modes", {})).intersection(order):
            raise PresentationGuardError("synthesis mode must not enter Prime roster")
        seen_numbers: set[int] = set()
        for name in order:
            a, b, c, d = (members[name], static_members[name],
                           profile_members[name], expr_members[name])
            number = a["gematria"]
            if not isinstance(number, int) or number in seen_numbers:
                raise PresentationGuardError(f"{name}: missing or duplicate gematria")
            seen_numbers.add(number)
            if not (
                a["heart"] == b["heart"] == c["heart"]
                and a["interest"] == b["static_interest_emoji"] == c["static_identity_emoji"]
                and a["accent"] == c["accent"]
                and number == c["gematria_number"]
            ):
                raise PresentationGuardError(f"{name}: canonical identity disagreement")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", a["accent"]):
                raise PresentationGuardError(f"{name}: invalid accent")
            values = d["expressions"]
            if not isinstance(values, dict) or not isinstance(d["default"], str) or not d["default"]:
                raise PresentationGuardError(f"{name}: incomplete expression registry")
            if any(not isinstance(v, str) or not v for v in values.values()):
                raise PresentationGuardError(f"{name}: malformed expression")
    except PresentationGuardError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PresentationGuardError("missing or malformed presentation source") from exc
    return tuple(order)


def canonical_header(
    name: str,
    spec: dict[str, Any],
    expressions: dict[str, Any],
    expression_state: str | None = None,
) -> str:
    if name not in spec["members"] or name not in expressions["members"]:
        raise PresentationGuardError("unknown Prime Daemon")
    data = spec["members"][name]
    expr = expressions["members"][name]
    emoji = expr["expressions"].get(expression_state, expr["default"]) if expression_state else expr["default"]
    return f'{data["gematria"]} · {name} {data["heart"]} {data["interest"]} {emoji}'


def expected_members_from_request(text: str, roster: tuple[str, ...]) -> tuple[str, ...]:
    """Narrow explicit requests only; never infer a cast from casual discussion."""
    line = str(text or "").strip().rstrip(".!?").strip()
    if re.fullmatch(r"(?:COUNCIL EVERYONE|FULL CAST|FULL COUNCIL|ALL DAEMONS(?: REPORT IN)?|EVERYONE(?: REPORT IN)?|EVERYBODY(?: REPORT IN)?|THE DAEMONCULABA REPORT IN)", line, re.I):
        return roster
    if re.search(r"\b(?:everyone|everybody|all six|all daemons|full cast)\b.{0,45}\b(?:report in|join us|check in|speak)\b", line, re.I):
        return roster
    names = "|".join(re.escape(n) for n in roster)
    match = re.fullmatch(rf"(?:ASK|SOLO)\s+({names})(?:\s+.*)?", line, re.I)
    return (match.group(1).upper(),) if match else ()


def _header_candidate(line: str, roster: tuple[str, ...]) -> str | None:
    """Detect wrong number, missing number, substituted emoji, or markdown headers."""
    names = "|".join(re.escape(n) for n in roster)
    match = re.match(
        rf"^(?:#{1,6}\s*|\*\*)?(?:(?:\d+)\s*[·.]\s*)?(?P<name>{names})(?=\s|$)",
        line.strip(), re.I,
    )
    if not match:
        return None
    tail = line.strip()[match.end():]
    has_numeric = bool(re.match(r"^(?:#{1,6}\s*|\*\*)?\d+\s*[·.]", line.strip()))
    has_emoji = bool(re.match(r"^\s*[\u2300-\u27ff\U0001F000-\U0010FFFF]", tail))
    has_markdown = line.lstrip().startswith(("#", "**"))
    return match.group("name").upper() if (has_numeric or has_emoji or has_markdown) else None


def validate_output(
    output: str,
    spec: dict[str, Any],
    expressions: dict[str, Any],
    static: dict[str, Any],
    profiles: dict[str, Any],
    expected_members: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Validate visible speaker blocks. Omit quoted/fenced code examples."""
    roster = validate_sources(spec, expressions, static, profiles)
    if not isinstance(output, str) or not output.strip():
        raise PresentationGuardError("empty model response")
    if any(name not in roster for name in expected_members):
        raise PresentationGuardError("requested speaker not in roster")
    acceptable = {
        name: {
            canonical_header(name, spec, expressions, state)
            for state in (None, *expressions["members"][name]["expressions"].keys())
        }
        for name in roster
    }
    seen: list[str] = []
    cards: list[dict[str, str]] = []
    fenced = False
    for raw in output.splitlines():
        line = raw.strip()
        if re.match(r"^(\x60{3}|~{3})", line):
            fenced = not fenced
            continue
        if fenced or line.startswith(">"):
            continue
        member = _header_candidate(raw, roster)
        if member is None:
            continue
        if raw != line or line not in acceptable[member]:
            raise PresentationGuardError(f"{member}: substituted or malformed identity envelope")
        seen.append(member)
        cards.append({
            "member": member,
            "header": line,
            "accent": spec["members"][member]["accent"],
        })
    missing = [name for name in expected_members if name not in seen]
    if missing:
        raise PresentationGuardError("missing required speaker: " + ",".join(missing))
    if len(expected_members) == 1 and any(name != expected_members[0] for name in seen):
        raise PresentationGuardError("SOLO response contained another member")
    return {
        "status": "PASS_CANONICAL_PRESENTATION",
        "speaker_count": len(cards),
        "speakers": cards,
        "source_consistency": True,
    }


def render_solo(
    content: str,
    member: str,
    spec: dict[str, Any],
    expressions: dict[str, Any],
    static: dict[str, Any],
    profiles: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Render SOLO header in code; do not let the model invent its markers."""
    roster = validate_sources(spec, expressions, static, profiles)
    if member not in roster:
        raise PresentationGuardError("unknown SOLO member")
    if not isinstance(content, str) or not content.strip():
        raise PresentationGuardError("empty SOLO content")
    checked = validate_output(content, spec, expressions, static, profiles)
    if checked["speaker_count"]:
        first = next((line for line in content.splitlines() if line.strip()), "")
        if (checked["speaker_count"] != 1 or
                checked["speakers"][0]["member"] != member or
                first != checked["speakers"][0]["header"]):
            raise PresentationGuardError("SOLO model supplied unexpected speaker attribution")
        result = content
    else:
        result = canonical_header(member, spec, expressions) + "\n" + content.strip()
    receipt = validate_output(result, spec, expressions, static, profiles, (member,))
    return result, receipt
