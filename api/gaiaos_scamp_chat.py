"""Source-pinned, open-ended two-guest ScampOS host bridge.

An elected HELTI-SKELTI speaks using the underlying model's generative
intelligence. Search is host-granted per request, not a character privilege.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from urllib.parse import urlsplit

# The source checkout imports this module from api/, but the production
# Dockerfile flattens it to /app/gaiaos_scamp_chat.py and copies GaiaOS under
# /app/GaiaOS. Resolve the real adjacent source tree in either layout.
MODULE_DIR = Path(__file__).resolve().parent
SCAMP_RUNTIME = Path("GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py")
ROOT = MODULE_DIR if (MODULE_DIR / SCAMP_RUNTIME).is_file() else MODULE_DIR.parent
HEADERS = {
    "SCAMP-001": "SCAMP-001 RIN-RIN 😈",
    "SCAMP-002": "SCAMP-002 HELTI-SKELTI 🕸️",
}
HEADER = HEADERS["SCAMP-001"]  # Compatibility for existing first-guest readers.

GAMING = re.compile(r"\b(?:cyberpunk|edgerunners|night city|galena|gaming|game|choom)\b", re.I)
CREATIVE = re.compile(r"\b(?:ableton|splice|synth|samples?|music|track|remix)\b", re.I)
TECH = re.compile(r"\b(?:plugin|python|code|programming|port|cable|desktop|app|debug|computer|network)\b", re.I)
CASUAL = re.compile(r"\b(?:lol|lmao|haha|pizza|jacket|funny|silly|meme|watching)\b", re.I)
NAME_PATTERNS = {
    "SCAMP-001": re.compile(r"\b(?:rin[ -]?rin|rin|SCAMP-001)\b", re.I),
    "SCAMP-002": re.compile(r"\b(?:helti[ -]?skelti|helti|skelti|SCAMP-002)\b", re.I),
}
MUTE_WORDS = re.compile(r"\b(?:mute|disable|silence)\b", re.I)
UNMUTE_WORDS = re.compile(r"\b(?:unmute|allow|enable)\b", re.I)
FOLLOWUP_WORDS = re.compile(
    r"\b(?:explain|elaborate|expand|show|demonstrate|teach|clarify|"
    r"why|how|what|tell me more|go on|example|source|prove|verify)\b", re.I
)
SPEAKER_RE = re.compile(r"^\s*(?:#{1,6}\s*)?SCAMP-?0*\d+\s+\S+", re.I)


def context(text):
    """Report a loose topic label; never gate by subject or seriousness."""
    if not isinstance(text, str) or not text.strip():
        return "unknown"
    for name, pattern in (
        ("gaming", GAMING), ("creative", CREATIVE),
        ("light_technical", TECH), ("casual", CASUAL)
    ):
        if pattern.search(text):
            return name
    return "unknown"


def _load_selector():
    spec = importlib.util.spec_from_file_location(
        "gaiaos_scamp_dispatch_runtime",
        ROOT / "GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py"
    )
    if spec is None or spec.loader is None:
        raise ValueError("ScampOS selector unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _explicit_names(text):
    return {id for id, pattern in NAME_PATTERNS.items() if pattern.search(text)}


def _historical_last_turns(messages):
    last = {}
    for i, message in enumerate(messages[:-1]):
        if getattr(message, "role", None) != "assistant":
            continue
        lines = {line.strip() for line in getattr(message, "content", "").splitlines()}
        for id, header in HEADERS.items():
            if header in lines:
                last[id] = sum(
                    1 for m in messages[: i + 1] if getattr(m, "role", None) == "user"
                )
    return last


def _muted_guests(user_messages):
    muted = set()
    for msg in user_messages:
        line = msg.content.strip()
        names = _explicit_names(line)
        if re.search(r"\b(?:all\s+scamps|scamps\s+all)\b", line, re.I):
            names = set(HEADERS)
        if UNMUTE_WORDS.search(line):
            muted -= names
        elif MUTE_WORDS.search(line):
            muted |= names
    return muted


def _direct_helti_followup(messages, text):
    """A substantive follow-up to a just-spoken HELTI does not need re-summoning."""
    if not FOLLOWUP_WORDS.search(text):
        return False
    if _explicit_names(text):
        return False
    if not messages or getattr(messages[-1], "role", None) != "user":
        return False
    earlier = list(messages[:-1])
    if not earlier or getattr(earlier[-1], "role", None) != "assistant":
        return False
    previous = getattr(earlier[-1], "content", "")
    return HEADERS["SCAMP-002"] in [ln.strip() for ln in previous.splitlines()]


def decide(messages, bundle, roll=None, muted=False):
    guests = bundle.get("guests")
    if not isinstance(guests, dict) or set(guests) != set(HEADERS):
        raise ValueError("two-source ScampOS bundle required")
    for guest_id, header in HEADERS.items():
        source = guests[guest_id]
        if (source["character"].get("header") != header
                or source["policy"].get("guest_header") != header):
            raise ValueError("ScampOS identity disagreement")
    users = [m for m in messages if getattr(m, "role", None) == "user"]
    if not users:
        raise ValueError("missing user turn")
    turn = len(users)
    text = users[-1].content
    explicit = _explicit_names(text)
    followup = _direct_helti_followup(messages, text)
    if followup:
        explicit.add("SCAMP-002")
    muteds = _muted_guests(users)
    if muted:
        muteds = set(HEADERS)
    rolls = (
        roll if isinstance(roll, dict)
        else {"SCAMP-001": roll} if roll is not None
        else {}
    )
    result = _load_selector().select_guests(
        turn, context=context(text), last_turns=_historical_last_turns(messages),
        rolls=rolls, explicit_guests=explicit, muted_guests=muteds
    )
    result["interaction_mode"] = (
        "dialogue" if result.get("guest_id") == "SCAMP-002" and
        (followup or "SCAMP-002" in _explicit_names(text))
        else "intrusion"
    )
    result["knowledge_mode"] = (
        "GENERATIVE_WITH_OPTIONAL_WEB_RESEARCH"
        if result.get("guest_id") == "SCAMP-002" else "NATIVE_CHARACTER"
    )
    return result


def model_instruction(decision):
    if not decision["appear"]:
        return "\nSCAMPOS: no guest selected. Do not include a Scamp speaker block."
    if decision["guest_id"] == "SCAMP-001":
        return (
            "\nSCAMPOS: RIN-RIN selected. Give her a spontaneous brief interruption "
            "under this exact standalone header: SCAMP-001 RIN-RIN 😈. "
            "Preserve her full cumulative character and independent voice. "
            "No topic exclusions; no access to tools, data writes or Prime identity."
        )
    header = HEADERS["SCAMP-002"]
    base = (
        "\nSCAMPOS: HELTI-SKELTI is speaking. Use the underlying AI model's "
        "OPEN-ENDED reasoning and knowledge, plus optional authorized research "
        "tools available in this request. Never select from or enumerate a fixed "
        "catalog of technical facts. Investigate unfamiliar or changing claims "
        "through available web search; do not claim to have searched unless a "
        "search actually occurred. Do not invent sources, exploits, incidents, "
        "access to private computers or confidential data. "
        "Use real-world computing, networking, OS, security and adjacent knowledge "
        "at any depth the situation warrants. Maintain their ice-cold, clinical, "
        "unexpectedly unsettling but matter-of-fact delivery and UNKNOWN motives. "
        "For direct questions, explain accurately and substantially, with "
        "practical examples and exercises on systems the user controls. "
        "No topic-based exclusion, no Prime identity, no external effect authority. "
        f"Give HELTI-SKELTI exactly this standalone guest header: {header}. "
    )
    if decision["interaction_mode"] == "dialogue":
        return (
            base
            + "DIALOGUE MODE: They were asked or a user followed up on their "
            "previous technical contribution. Respond as a full, capable technical "
            "AI interlocutor. Do not limit the answer to one sentence, two lines, "
            "or one fact. Answer the actual question and keep Prime speech distinct."
        )
    return (
        base
        + "INTRUSION MODE: Initiate one original, concise, verifiable observation "
        "with a disquieting real-world implication. Do not force a connection to "
        "the user's current topic. No buildup, canned trivia rotation, ominous "
        "roleplay, threat, or forced explanation. Then leave the conversation "
        "room for its original subject."
    )


def response_tool_options(decision):
    """The host offers model-controlled live research only when HELTI is selected."""
    if decision and decision.get("appear") and decision.get("guest_id") == "SCAMP-002":
        return {
            "tools": [{"type": "web_search", "search_context_size": "medium"}],
            "tool_choice": "auto"
        }
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
    if not isinstance(output, str):
        raise ValueError("output must be text")
    lines = [line.strip() for line in output.splitlines()]
    candidates = [line for line in lines if SPEAKER_RE.match(line)]
    if len(candidates) > 1:
        raise ValueError("only one Scamp guest per response")
    expected = HEADERS.get(decision.get("guest_id"))
    if candidates and (not decision.get("appear") or candidates[0] != expected):
        raise ValueError("Scamp identity or selection mismatch")
    if candidates:
        index = lines.index(candidates[0])
        if not any(line for line in lines[index + 1:]):
            raise ValueError("Scamp spoke without any actual content")
    return {
        "status": (
            "PASS_GUEST_RENDERED" if candidates else
            "HOLD_GUEST_SELECTED_NOT_RENDERED" if decision.get("appear")
            else "PASS_NO_GUEST_SELECTED"
        ),
        "guest_id": decision.get("guest_id"),
        "selected": bool(decision.get("appear")),
        "rendered": bool(candidates),
        "context": decision.get("context", "unknown"),
        "interaction_mode": decision.get("interaction_mode"),
        "knowledge_mode": decision.get("knowledge_mode"),
        "effect_authority": "NONE"
    }
