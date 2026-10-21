"""Source-aligned ScampOS turn gate for ordinary hosted ChatOS."""
import re
from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
HEADER = "SCAMP-01 RINRIN 😈"
SENSITIVE = re.compile(r"\b(?:suicid\w*|self.harm|overdos\w*|hospital\w*|tonsil\w*|throat|infection|medical|medicat\w*|clinic|grief|funeral|rent|eviction|debt|financial|credit.card|paycheck|payment|bank|homeless\w*|trauma|panic.attack|depress\w*)\b",re.I)
GAMING = re.compile(r"\b(?:cyberpunk|edgerunners|night city|galena|watson|gaming|game|choom)\b",re.I)
CREATIVE = re.compile(r"\b(?:ableton|splice|synth|samples?|dj|bassline|music|song|producer|track|remix)\b",re.I)
TECH = re.compile(r"\b(?:plugin|python|code|programming|ports?|jack|cable|desktop|app|debug|adapter|build|computer)\b",re.I)
CASUAL = re.compile(r"\b(?:lol|lmao|haha|pizza|jacket|funny|hilarious|silly|ridiculous|meme|watching)\b",re.I)

def context(text):
    if not text or not isinstance(text,str): return "unknown"
    if SENSITIVE.search(text): return "serious"
    for name,matcher in (("gaming",GAMING),("creative",CREATIVE),("light_technical",TECH),("casual",CASUAL)):
        if matcher.search(text): return name
    return "unknown"

def decide(messages,bundle,roll=None,muted=False):
    if bundle["character"].get("header") != HEADER or bundle["policy"].get("guest_header") != HEADER:
        raise ValueError("RINRIN source mismatch")
    users=[m for m in messages if getattr(m,"role",None)=="user"]
    if not users: raise ValueError("missing user")
    turn=len(users)
    last_turn=None
    for i,m in enumerate(messages[:-1]):
        if getattr(m,"role",None)=="assistant" and HEADER in getattr(m,"content",""):
            last_turn=sum(1 for x in messages[:i+1] if getattr(x,"role",None)=="user")
    text=users[-1].content
    c=context(text)
    explicit=bool(re.search(r"\b(?:rinrin|rin)\b",text,re.I))
    # Explicit invitation is a casual eligible context unless high-stakes.
    if explicit and c=="unknown":
        c="casual"
    # The most recent explicit mute/unmute instruction persists within the
    # bounded supplied conversation, without a database or host side effect.
    user_muted=False
    for item in users:
        instruction=item.content.strip()
        if re.search(r"\b(?:unmute|allow|enable)\s+(?:rinrin|rin)\b",instruction,re.I):
            user_muted=False
        elif re.search(r"\b(?:mute|disable|silence)\s+(?:rinrin|rin)\b",instruction,re.I):
            user_muted=True
    spec=importlib.util.spec_from_file_location(
        "gaiaos_scamp_turn_selector",ROOT/"GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py"
    )
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result=module.select(turn,context=c,last_turn=last_turn,
                         explicit=explicit,
                         muted=muted or user_muted,roll=roll)
    result["context"]=c
    return result

def model_instruction(decision):
    if decision["appear"]:
        return ("\nSCAMPOS GUEST SELECTED THIS TURN. Include a brief, natural, "
                "non-graphic guest interruption under the exact standalone "
                "header SCAMP-01 RINRIN 😈. Preserve her cumulative character, "
                "leave the main answer useful and maintain all Prime Daemon "
                "identity headers. Never give the guest tool or memory authority.")
    return "\nSCAMPOS: no guest selected on this turn. Do not add a Rin speaker block."

def validate_output(output,decision):
    lines=[x.strip() for x in output.splitlines() if re.match(r"^\s*(?:#{1,6}\s*)?SCAMP-01\s+RINRIN\b",x,re.I)]
    if any(x != HEADER for x in lines) or len(lines)>1:
        raise ValueError("invalid guest presentation")
    if lines and not decision["appear"]:
        raise ValueError("guest bypassed selection")
    return {"status":("PASS_GUEST_RENDERED" if lines else
                     "HOLD_GUEST_SELECTED_NOT_RENDERED" if decision["appear"]
                     else "PASS_NO_GUEST_SELECTED"),
            "selected":bool(decision["appear"]),
            "rendered":bool(lines),"context":decision["context"],
            "effect_authority":"NONE"}
