"""ScampOS: independent read-only selection for multiple spontaneous guests."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
DEFAULT_GUEST="SCAMP-001"

def _json(relative):
    return json.loads((BASE/relative).read_text(encoding="utf-8"))

def load_registry():
    current=_json("CURRENT.json")
    guests=current.get("guests")
    order=current.get("guest_order")
    if not isinstance(guests,dict) or order!=["SCAMP-001","SCAMP-002"]:
        raise ValueError("ScampOS guest roster must contain exactly two separate Scamps")
    output={}
    for guest_id in order:
        info=guests[guest_id]
        root=BASE.parents[3]
        def load_path(path):
            target=(root/path).resolve()
            target.relative_to(root.resolve())
            return json.loads(target.read_text(encoding="utf-8"))
        character=load_path(info["character"])
        policy=load_path(info["policy"])
        if (character.get("id")!=guest_id or policy.get("guest_id")!=guest_id
            or character.get("header")!=info["header"]
            or policy.get("guest_header")!=info["header"]
            or character.get("prime_member") is not False
            or character.get("tool_access") is not False
            or policy.get("effect_authority")!="NONE"
            or policy.get("excluded_contexts")!=[]):
            raise ValueError("ScampOS source disagreement: "+guest_id)
        output[guest_id]={"character":character,"policy":policy,"source":info}
    if len(set(x["character"]["header"] for x in output.values()))!=2:
        raise ValueError("ScampOS identities collide")
    return output

def load_policy(guest_id=DEFAULT_GUEST):
    return load_registry()[guest_id]["policy"]

def select(turn,context="unknown",last_turn=None,roll=None,explicit=False,muted=False,
           guest_id=DEFAULT_GUEST):
    """Select one guest independently. Context never vetoes an interruption."""
    p=load_policy(guest_id)
    if not isinstance(turn,int) or isinstance(turn,bool) or turn<0:
        raise ValueError("invalid turn")
    if last_turn is not None and (not isinstance(last_turn,int) or last_turn>=turn):
        raise ValueError("invalid previous appearance turn")
    if roll is not None and (not isinstance(roll,(int,float)) or not 0<=roll<1):
        raise ValueError("invalid random roll")
    if not isinstance(context,str): raise ValueError("invalid context")
    result={"appear":False,"reason":"NOT_ELIGIBLE","guest_id":guest_id,
            "header":p["guest_header"],"next_last_turn":last_turn,
            "guest_authority":"NONE"}
    if muted or not p["enabled"]:
        result["reason"]="MUTED"
    elif explicit and p["explicit_invocation_bypasses_chance"]:
        result.update(appear=True,reason="EXPLICIT",next_last_turn=turn)
    elif last_turn is not None and turn-last_turn<=p["cooldown_turns"]:
        result["reason"]="COOLDOWN"
    else:
        draw=random.random() if roll is None else roll
        if draw<p["chance"]:
            result.update(appear=True,reason="CHANCE",next_last_turn=turn)
        else:
            result["reason"]="CHANCE_SKIPPED"
    return result

def select_guests(turn,context="unknown",last_turns=None,rolls=None,
                  explicit_guests=(),muted_guests=()):
    """No Prime mutations. Exactly zero or one guest may appear in a response."""
    order=tuple(load_registry())
    last_turns=last_turns or {}
    rolls=rolls or {}
    explicit=set(explicit_guests)
    muted=set(muted_guests)
    if not explicit.issubset(order) or not muted.issubset(order):
        raise ValueError("unknown Scamp guest")
    evaluated={}
    for guest_id in order:
        evaluated[guest_id]=select(
            turn,context=context,last_turn=last_turns.get(guest_id),
            roll=rolls.get(guest_id),explicit=guest_id in explicit,
            muted=guest_id in muted,guest_id=guest_id
        )
    eligible=[g for g in order if evaluated[g]["appear"]]
    if not eligible:
        return {"appear":False,"reason":"NONE_SELECTED","guest_id":None,
                "header":None,"evaluations":evaluated,"context":context}
    # Explicitly requested guest wins over chance. Remaining ties rotate.
    explicit_eligible=[g for g in eligible if g in explicit]
    pool=explicit_eligible or eligible
    tie_order=order if turn%2 else tuple(reversed(order))
    winner=next(g for g in tie_order if g in pool)
    return {**evaluated[winner],"evaluations":evaluated,"context":context,
            "collision":len(eligible)>1}

def render_guest(dialogue,guest_id=DEFAULT_GUEST):
    p=load_policy(guest_id)
    if not isinstance(dialogue,str): raise ValueError("dialogue must be text")
    lines=[line.strip() for line in dialogue.splitlines() if line.strip()]
    if not lines: raise ValueError("dialogue cannot be empty")
    return p["guest_header"]+"\n"+"\n".join(lines[:p["max_guest_lines"]])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--turn",type=int,required=True)
    parser.add_argument("--context",default="unknown")
    parser.add_argument("--last-turn",type=int)
    parser.add_argument("--roll",type=float)
    parser.add_argument("--explicit",action="store_true")
    parser.add_argument("--muted",action="store_true")
    parser.add_argument("--guest-id",default=DEFAULT_GUEST)
    args=parser.parse_args()
    print(json.dumps(select(args.turn,context=args.context,last_turn=args.last_turn,
                            roll=args.roll,explicit=args.explicit,muted=args.muted,
                            guest_id=args.guest_id),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
