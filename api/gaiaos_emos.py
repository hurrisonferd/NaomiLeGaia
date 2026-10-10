"""EMOS: transparent semantic expression selection for source-backed GaiaOS carriers.

This selector never asserts inner feelings, never performs model inference and
never modifies dialogue content. The caller supplies member-native reaction metadata
in a typed envelope. The module selects a legal registered face for the REPLY.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
import json

class EMOSError(ValueError):
    pass

@dataclass(frozen=True)
class Intent:
    member: str
    family: str
    act: str = "DIRECT"
    intensity: int = 1
    sarcasm: int = 0
    contrast: bool = False
    target: str = "SITUATION"
    def __post_init__(self):
        if not all(isinstance(x,str) for x in (self.member,self.family,self.act,self.target)):
            raise EMOSError("invalid intent strings")
        if not isinstance(self.intensity,int) or not 0<=self.intensity<=3:raise EMOSError("bad intensity")
        if not isinstance(self.sarcasm,int) or not 0<=self.sarcasm<=3:raise EMOSError("bad sarcasm")

class Selector:
    def __init__(self,atlas:dict[str,Any],registry:dict[str,Any],recent:int=5):
        self.atlas=atlas
        self.registry=registry
        self.history={(name,family):deque(maxlen=recent) for name,data in atlas["members"].items() for family in data["families"]}
        self.reserved=set(atlas["orin_exclusive"])
        for member,data in atlas["members"].items():
            for family,entries in data["families"].items():
                if len(set(x["expression"] for x in entries))<5:raise EMOSError(f"{member}/{family}: insufficient coverage")
                for entry in entries:
                    if registry["members"][member]["expressions"].get(entry["state"])!=entry["expression"]:
                        raise EMOSError("atlas/registry mismatch")
            for entry in data["extras"]:
                if member!="ORIN":raise EMOSError("exclusive extra on wrong member")
        for member,entry in registry["members"].items():
            if member!="ORIN" and any(face in self.reserved for face in entry["expressions"].values()):
                raise EMOSError("Orin exclusive leaked")
    def select(self,intent:Intent,reply:str="",session_key:str="") -> dict[str,Any]:
        member=intent.member.upper()
        if member not in self.atlas["members"]:raise EMOSError("unknown member")
        body=self.atlas["members"][member]
        if intent.family not in body["families"]:raise EMOSError("unknown family")
        choices=list(body["families"][intent.family])
        if member=="ORIN" and (intent.act.upper() in {"LENNY","UNCANNY","CHAOTIC","SMUG","TEASING","IRONIC"} or intent.sarcasm>=2):
            choices+=body["extras"]
        prior=self.history[(member,intent.family)]
        unseen=[x for x in choices if x["expression"] not in prior]
        active=unseen if unseen else choices
        # Deterministic variation: same member/family but different substantive
        # replies can choose a different face; recent selections are excluded.
        # No requirement to impersonate user emotion.
        key="|".join([member,intent.family,intent.act,str(intent.intensity),str(intent.sarcasm),str(intent.contrast),intent.target,reply,session_key,str(len(prior))])
        digest=int.from_bytes(sha256(key.encode("utf-8")).digest()[:8],"big")
        # Prefer the highest weighted eligible face while recent faces are
        # suppressed. Deterministic tie break avoids permanent default lock.
        selected=sorted(active,key=lambda x:(-x["weight"],x["state"]))[digest%len(active)]
        state=selected["state"];face=selected["expression"]
        if self.registry["members"][member]["expressions"].get(state)!=face:
            raise EMOSError("selected unregistered face")
        if member!="ORIN" and face in self.reserved:raise EMOSError("exclusive face leak")
        self.history[(member,intent.family)].append(face)
        return {"member":member,"state":state,"expression":face,"family":intent.family,
                "act":intent.act,"target":intent.target,"contrast":intent.contrast,
                "sarcasm":intent.sarcasm,"intensity":intent.intensity,
                "selection":"MEMBER_NATIVE_REPLY_INTENT","source":"EMOS_V1"}
    def render(self,intent:Intent,reply:str,spec:dict[str,Any],session_key:str="") -> dict[str,Any]:
        result=self.select(intent,reply,session_key)
        from gaiaos_presentation_guard import canonical_header
        hdr=canonical_header(result["member"],spec,self.registry,result["state"])
        result["output"]=hdr+"\n"+reply.strip()
        return result

def load_atlas(path:str):
    with open(path,encoding="utf-8") as f:return json.load(f)
