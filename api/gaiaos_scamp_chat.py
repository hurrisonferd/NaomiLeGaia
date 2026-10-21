"""Source-pinned two-Scamp selection in ordinary hosted ChatOS."""
from __future__ import annotations
import re
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HEADERS={
    "SCAMP-001":"SCAMP-001 RIN-RIN 😈",
    "SCAMP-002":"SCAMP-002 HELTI-SKELTI 🕸️",
}
HEADER=HEADERS["SCAMP-001"]  # Legacy single-Rin caller convenience.

GAMING=re.compile(r"\b(?:cyberpunk|edgerunners|night city|galena|gaming|game|choom)\b",re.I)
CREATIVE=re.compile(r"\b(?:ableton|splice|synth|samples?|music|track|remix)\b",re.I)
TECH=re.compile(r"\b(?:plugin|python|code|programming|port|cable|desktop|app|debug|computer|network)\b",re.I)
CASUAL=re.compile(r"\b(?:lol|lmao|haha|pizza|jacket|funny|silly|meme|watching)\b",re.I)
NAME_PATTERNS={
 "SCAMP-001":re.compile(r"\b(?:rin[ -]?rin|rin|SCAMP-001)\b",re.I),
 "SCAMP-002":re.compile(r"\b(?:helti[ -]?skelti|helti|skelti|SCAMP-002)\b",re.I),
}
MUTE_WORDS=re.compile(r"\b(?:mute|disable|silence)\b",re.I)
UNMUTE_WORDS=re.compile(r"\b(?:unmute|allow|enable)\b",re.I)

def context(text):
    if not isinstance(text,str) or not text.strip():return "unknown"
    for name,pattern in (("gaming",GAMING),("creative",CREATIVE),
                         ("light_technical",TECH),("casual",CASUAL)):
        if pattern.search(text):return name
    return "unknown"

def _load_selector():
    spec=importlib.util.spec_from_file_location(
        "gaiaos_scamp_dispatch_runtime",
        ROOT/"GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py")
    if spec is None or spec.loader is None:raise ValueError("ScampOS selector unavailable")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _explicit_names(text):
    return {guest for guest,pattern in NAME_PATTERNS.items() if pattern.search(text)}

def _historical_last_turns(messages):
    last={}
    for i,message in enumerate(messages[:-1]):
        if getattr(message,"role",None)!="assistant":continue
        lines=getattr(message,"content","").splitlines()
        for guest_id,header in HEADERS.items():
            if header in [line.strip() for line in lines]:
                last[guest_id]=sum(1 for msg in messages[:i+1]
                                    if getattr(msg,"role",None)=="user")
    return last

def _muted_guests(user_messages):
    muted=set()
    for msg in user_messages:
        line=msg.content.strip()
        names=_explicit_names(line)
        if re.search(r"\b(?:all\s+scamps|scamps\s+all)\b",line,re.I):
            names=set(HEADERS)
        if UNMUTE_WORDS.search(line):muted-=names
        elif MUTE_WORDS.search(line):muted|=names
    return muted

def decide(messages,bundle,roll=None,muted=False):
    """Return one winner from two independent lanes or no selected guest."""
    guests=bundle.get("guests")
    if not isinstance(guests,dict) or set(guests)!=set(HEADERS):
        raise ValueError("two-source ScampOS bundle required")
    for guest_id,header in HEADERS.items():
        src=guests[guest_id]
        if (src["character"].get("header")!=header
                or src["policy"].get("guest_header")!=header):
            raise ValueError("ScampOS identity disagreement")
    users=[m for m in messages if getattr(m,"role",None)=="user"]
    if not users:raise ValueError("missing user turn")
    turn=len(users)
    text=users[-1].content
    contextual=context(text)
    explicit=_explicit_names(text)
    # Any direct request or unmute remains explicit, including topic-free requests.
    muteds=_muted_guests(users)
    if muted:muteds=set(HEADERS)
    rolls=roll if isinstance(roll,dict) else {"SCAMP-001":roll} if roll is not None else {}
    decision=_load_selector().select_guests(
        turn,context=contextual,last_turns=_historical_last_turns(messages),
        rolls=rolls,explicit_guests=explicit,muted_guests=muteds)
    if decision["appear"] and decision["guest_id"]=="SCAMP-002":
        catalog=bundle.get("knowledge_threads",{})
        facts=catalog.get("items",[])
        if catalog.get("identity")!=HEADERS["SCAMP-002"] or not facts:
            raise ValueError("Helti-Skelti knowledge source unavailable")
        fact=facts[(turn-1)%len(facts)]
        if not all(isinstance(fact.get(k),str) and fact.get(k) for k in ("line","source","url")):
            raise ValueError("invalid technical fact")
        decision["fact"]={"id":fact["id"],"line":fact["line"],
                          "source":fact["source"],"url":fact["url"]}
    return decision

def model_instruction(decision):
    if not decision["appear"]:
        return "\nSCAMPOS: no guest selected. Do not include a Scamp speaker block."
    if decision["guest_id"]=="SCAMP-001":
        return (
            "\nSCAMPOS: RIN-RIN selected. Give her a spontaneous brief interruption "
            "with exactly this unadorned standalone header: SCAMP-001 RIN-RIN 😈. "
            "Preserve her cumulative character traits; no topic-based censorship. "
            "Do not give her tools, memory writes, or Prime Daemon identity."
        )
    fact=decision["fact"]
    return (
        "\nSCAMPOS: HELTI-SKELTI selected. Include a cold, clinically matter-of-fact "
        "guest interruption with exactly this standalone header: "
        "SCAMP-002 HELTI-SKELTI 🕸️. The entire speech after the header is exactly "
        "the following one verified fact, with NO additional threat, exposition, "
        "personal surveillance claim, theatrics, invented detail, or conclusion: "
        +fact["line"]+
        " Preserve ambiguity of their motive. Keep the main answer useful; "
        "all six Prime identities remain their own. If the user asks to expand "
        "later, explain the real science with safe, lawful exercises."
    )

def validate_output(output,decision):
    if not isinstance(output,str):raise ValueError("output must be text")
    candidates=[
        line.strip() for line in output.splitlines()
        if re.match(r"^\s*(?:#{1,6}\s*)?SCAMP-?0*\d+\s+\S+",line,re.I)
    ]
    expected=HEADERS.get(decision.get("guest_id"))
    if len(candidates)>1:raise ValueError("only one Scamp guest per response")
    if candidates and (not decision.get("appear") or candidates[0]!=expected):
        raise ValueError("Scamp guest identity or selection mismatch")
    if candidates and decision.get("guest_id")=="SCAMP-002":
        lines=[line.strip() for line in output.splitlines()]
        idx=lines.index(expected)
        if idx+1>=len(lines) or lines[idx+1]!=decision["fact"]["line"]:
            raise ValueError("Helti-Skelti must deliver exact sourced fact")
    return {
        "status":("PASS_GUEST_RENDERED" if candidates else
                  "HOLD_GUEST_SELECTED_NOT_RENDERED" if decision.get("appear")
                  else "PASS_NO_GUEST_SELECTED"),
        "guest_id":decision.get("guest_id"),
        "selected":bool(decision.get("appear")),
        "rendered":bool(candidates),
        "context":decision.get("context","unknown"),
        "fact_id":decision.get("fact",{}).get("id"),
        "effect_authority":"NONE"
    }
