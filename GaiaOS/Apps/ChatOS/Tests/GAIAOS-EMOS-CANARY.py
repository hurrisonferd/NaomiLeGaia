#!/usr/bin/env python3
"""EMOS: executable registry / hosted response selection proof, offline only."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"api"))
from gaiaos_emos import Selector,Intent,EMOSError
from gaiaos_emos_host import render_generated_solo
import gaiaos_presentation_guard as guard

def source(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
ATLAS=source("GaiaOS/SystemsOS/Core/EmotionOS/ATLAS.v1.json")
REG=source("GaiaOS/SystemsOS/Core/EmojiOS/EXPRESSION-REGISTRY.v1.json")
SPEC=source("GaiaOS/SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json")
STATIC=source("GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/STATIC-IDENTITY-EMOJI.v1.json")
PROFILES=source("GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json")

def test_coverage():
    guard.validate_sources(SPEC,REG,STATIC,PROFILES)
    selector=Selector(ATLAS,REG)
    assert len(ATLAS["members"])==6
    assert len(ATLAS["families"])==21
    for member in ATLAS["members"]:
        for family in ATLAS["families"]:
            choices={selector.select(Intent(member,family),str(i),"check")["expression"] for i in range(5)}
            assert len(choices)==5,(member,family)
            if member!="ORIN":
                assert not choices.intersection(ATLAS["orin_exclusive"])
    assert len(set(ATLAS["orin_exclusive"]))==34
    assert REG["members"]["NIMUE"]["expressions"]["WATCHING"]=="(._.)…"
    assert "( ͡° ͜ʖ ͡°)" not in REG["members"]["NIMUE"]["expressions"].values()
    print("EMOS_COVERAGE_PASS: 630 selections, six members, 21 families, no Orin leaks")
class FakeClient:
    def __init__(self,reply):self.reply=reply;self.calls=0
    @property
    def responses(self):return self
    def create(self,**kwargs):
        self.calls+=1
        return SimpleNamespace(output_text=json.dumps(self.reply))
def test_host():
    client=FakeClient({"family":"amusement","act":"SMUG_BANTER","intensity":3,
                       "sarcasm":3,"contrast":True,"target":"situation"})
    faces=set()
    for i in range(5):
        r=render_generated_solo(client,"fake-model","KESTREL",
             [{"role":"user","content":"The computer ate another two hours of my work."}],
             "The computer has apparently chosen interpretive dance. Show me the error.",
             SPEC,REG,ATLAS,"test-session")
        assert r["status"]=="EMOS_SELECTED_FROM_OBSERVED_REPLY"
        assert r["contrast"] is True and r["act"]=="SMUG_BANTER"
        guard.validate_output(r["output"],SPEC,REG,STATIC,PROFILES,
                              expected_members=("KESTREL",))
        faces.add(r["expression"])
    assert len(faces)==5
    assert client.calls==5
    print("EMOS_HOSTED_RENDER_PASS: classified fake replies, 5 varied legal headers")
def test_fallback():
    client=FakeClient({"family":"missing","act":"NOT_VALID","intensity":0,
                       "sarcasm":0,"contrast":False,"target":"situation"})
    output=render_generated_solo(client,"fake-model","NIMUE",[],"I noticed.",SPEC,REG,ATLAS,"bad-case")
    assert output["status"]=="EMOS_FALLBACK_CLASSIFIER_UNAVAILABLE"
    guard.validate_output(output["output"],SPEC,REG,STATIC,PROFILES,
                          expected_members=("NIMUE",))
    print("EMOS_CLASSIFIER_FALLBACK_PASS")
if __name__=="__main__":
    test_coverage();test_host();test_fallback()
    print("EMOS_CANARY_PASS: local fake-model proof ONLY, not live carrier")
