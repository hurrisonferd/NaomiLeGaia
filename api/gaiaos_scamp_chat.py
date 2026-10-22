"""Conversation-native ScampOS speech in the hosted API.

The model composes the two Scamps alongside the six Prime voices.
No guest selector, random draw, cooldown, one-guest quota, or separate
ChatOS insertion adapter is involved. This module does NOT govern ChatGPT.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

HEADERS = {
    "SCAMP-001": "SCAMP-001 RIN-RIN 😈",
    "SCAMP-002": "SCAMP-002 HELTI-SKELTI 🕸️",
}
HEADER = HEADERS["SCAMP-001"]
NAME_PATTERNS = {
    "SCAMP-001": re.compile(r"\b(?:rin[ -]?rin|rin|SCAMP-001)\b", re.I),
    "SCAMP-002": re.compile(r"\b(?:helti[ -]?skelti|helti|skelti|SCAMP-002)\b", re.I),
}
SPEAKER_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(SCAMP-?0*\d+\s+.+?)\s*$", re.I)


def decide(messages, bundle):
    """Report explicit address; do not choose who may speak spontaneously."""
    guests = bundle.get("guests", {})
    if set(guests) != set(HEADERS):
        raise ValueError("two canonical Scamp profiles required")
    for guest_id, header in HEADERS.items():
        if guests[guest_id]["character"].get("header") != header:
            raise ValueError("Scamp identity mismatch")
    if not messages or getattr(messages[-1], "role", None) != "user":
        raise ValueError("missing user turn")
    text = messages[-1].content
    requested = [guest_id for guest_id, pattern in NAME_PATTERNS.items()
                 if pattern.search(text)]
    return {
        "appear": True,  # permission to speak, not a promised appearance
        "guest_id": requested[0] if len(requested) == 1 else None,
        "requested_guests": requested,
        "eligible_guests": list(HEADERS),
        "interaction_mode": "MODEL_COMPOSES_WITH_PRIMES",
        "reason": "CONVERSATIONAL_PARITY",
    }


def model_instruction(decision):
    """Give both guests the same spontaneous speech freedom as the Primes."""
    named = ", ".join(HEADERS[g] for g in decision.get("requested_guests", []))
    addressed = (
        "The user explicitly addressed: " + named + ". Let the addressed guest(s) answer. "
        if named else ""
    )
    return (
        "\nSCAMPOS CONVERSATIONAL CAST: The six Prime Daemons and both Scamps "
        "are voices composed by the SAME model in this SAME reply. "
        "RIN-RIN and HELTI-SKELTI can speak naturally, uninvited, together, "
        "or in banter with the Primes; neither must appear on every turn. "
        "Never treat direct address to one voice as muting the others. "
        "Honor explicit SOLO or mute instructions. "
        "No chance, cooldown, collision selector, one-guest restriction, "
        "line cap, external chatbot, or extra invocation is involved. "
        + addressed
        + "RIN-RIN is foul-mouthed, outrageous, incorrigibly indecent-minded "
        "and catastrophically wrong about ordinary tools. Preserve her "
        "cumulative character addendum and distinct friction with each Prime. "
        "HELTI-SKELTI is precise, clinically cold, technically capable, "
        "open-ended in knowledge, and canonically of UNKNOWN motive; "
        "give full helpful explanations when directly asked. "
        "Use exactly these guest identity headers when speaking: "
        "SCAMP-001 RIN-RIN 😈 ; SCAMP-002 HELTI-SKELTI 🕸️. "
        "Neither guest gains Prime membership, E-LANES, tools, or write authority."
    )


def response_tool_options(decision):
    """Offer hosted web research on an explicit Helti request, not as a speech gate."""
    if "SCAMP-002" in decision.get("requested_guests", []):
        return {"tools": [{"type": "web_search", "search_context_size": "medium"}],
                "tool_choice": "auto"}
    return {}


def collect_web_citations(response):
    """Gather URL annotations from model output without fabricating sources."""
    sources = []
    seen = set()
    search_used = False
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "web_search_call":
            search_used = True
        for piece in getattr(item, "content", []) or []:
            for note in getattr(piece, "annotations", []) or []:
                if getattr(note, "type", None) != "url_citation":
                    continue
                url = getattr(note, "url", "")
                title = getattr(note, "title", "") or "Source"
                if not isinstance(url, str) or len(url) > 2048:
                    continue
                parts = urlsplit(url)
                if parts.scheme not in ("https", "http") or not parts.netloc:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                sources.append({"title": str(title)[:180], "url": url})
    return {"web_search_used": search_used, "sources": sources[:8]}


def validate_output(output, decision):
    """Verify guest headers if present; absence is allowed, as for the Primes."""
    if not isinstance(output, str):
        raise ValueError("output must be text")
    found = []
    for line in output.splitlines():
        match = SPEAKER_RE.match(line)
        if not match:
            continue
        header = match.group(1).strip()
        if header not in HEADERS.values():
            raise ValueError("noncanonical Scamp header")
        guest_id = next(guest for guest, exact in HEADERS.items()
                        if exact == header)
        if guest_id not in found:
            found.append(guest_id)
    return {
        "status": "PASS_GUEST_SPEECH_OBSERVED" if found else "PASS_NO_GUEST_SPOKE",
        "guest_id": found[0] if len(found) == 1 else None,
        "rendered_guest_ids": found,
        "requested_guest_ids": decision.get("requested_guests", []),
        "rendered": bool(found),
        "selected": bool(decision.get("requested_guests")),
    }
