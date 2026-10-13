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
def test_loader_allowlist():
    import ast
    tree=ast.parse((ROOT/"api/gaiaos_api.py").read_text(encoding="utf-8"))
    assigned=None
    for node in tree.body:
        if isinstance(node,ast.Assign):
            if any(isinstance(t,ast.Name) and t.id=="COUNCIL_PATHS" for t in node.targets):
                assigned=ast.literal_eval(node.value)
                break
    required={
        "GaiaOS/SystemsOS/Core/EmotionOS/CURRENT.json",
        "GaiaOS/SystemsOS/Core/EmotionOS/ATLAS.v1.json",
        "GaiaOS/Apps/ChatOS/Protocols/EMOS-RESPONSE-CHANNEL.v1.md",
    }
    assert isinstance(assigned,list) and required.issubset(set(assigned)), "EMOS canonical loader source allowlist incomplete"
    print("EMOS_CANONICAL_LOADER_PATHS_PASS")

def test_production_docker_copy():
    dockerfile=(ROOT/"api/Dockerfile").read_text(encoding="utf-8")
    for source in ("gaiaos_emos.py","gaiaos_emos_host.py"):
        expected=f"COPY api/{source} ./{source}"
        assert expected in dockerfile, f"EMOS module missing from production Dockerfile: {source}"
    print("EMOS_DOCKER_COPY_PASS: selector and hosted classifier included")

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

def test_classic_solo_rollback():
    """Exercise real SOLO response logic with a fake provider and no network."""
    import importlib.util
    import os
    import types
    from unittest.mock import patch

    class FakeClient:
        def __init__(self):
            self.calls = 0
            self.responses = self
        def create(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(output_text="The corridor is quiet.")

    client = FakeClient()
    loaded_paths = []
    def load_json(commit, path):
        loaded_paths.append(path)
        return source(path)

    fake_api = types.ModuleType("gaiaos_api")
    fake_api._resolve_commit = lambda: "test-source-commit"
    fake_api.OPENAI_API_KEY = "test-only"
    fake_api.OPENAI_MODEL = "fake-model"
    fake_api.REPOSITORY = "hurrisonferd/NaomiLeGaia"
    fake_api._json_file = load_json

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda **kwargs: client
    fake_fastapi = types.ModuleType("fastapi")
    fake_fastapi.HTTPException = RuntimeError
    fake_memcon = types.ModuleType("memcon_runtime")

    enabled_calls = []
    fake_host = types.ModuleType("gaiaos_emos_host")
    def opt_in_render(client_arg, model, daemon, messages, draft, spec, registry,
                      atlas, session_key=""):
        enabled_calls.append(daemon)
        return {
            "status": "EMOS_SELECTED_FROM_OBSERVED_REPLY",
            "output": guard.canonical_header(daemon, spec, registry) + "\n" + draft.strip(),
            "family": "amusement", "state": None,
            "expression": registry["members"][daemon]["default"],
        }
    fake_host.render_generated_solo = opt_in_render

    with patch.dict(sys.modules, {
        "openai": fake_openai, "fastapi": fake_fastapi,
        "gaiaos_api": fake_api, "memcon_runtime": fake_memcon,
        "gaiaos_emos_host": fake_host,
    }):
        spec = importlib.util.spec_from_file_location(
            "gaiaos_solo_rollback_canary", ROOT / "api/solo_chat_runtime.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.roster = lambda commit: ["NIMUE"]
        module.profile = lambda commit, daemon: {"name": daemon}
        module.elane = lambda commit, daemon: "NIMUE OWNED EXPERIENCE"
        module._raw = lambda commit, path: "SOLO SOURCE CONTRACT"
        payload = [{"role": "user", "content": "Test the classic speech pathway."}]
        session = {"daemon": "NIMUE", "session_id": "test-session"}

        with patch.dict(os.environ, {"GAIAOS_EMOS_ENABLED": "false"}):
            assert "EMOS EXPRESSION CHANNEL:" not in module.instructions("fake", "NIMUE")
            classic = module.respond(payload, session)

        assert classic["emos"]["status"] == "EMOS_DISABLED_CLASSIC_PRESENTATION"
        assert classic["output"] == (
            guard.canonical_header("NIMUE", SPEC, REG) + "\nThe corridor is quiet."
        )
        assert client.calls == 1, "default-off must make exactly one model call"
        assert not enabled_calls, "default-off must not classify"
        assert not any("EmotionOS/ATLAS" in p for p in loaded_paths), (
            "default-off must not load EmotionOS atlas"
        )

        with patch.dict(os.environ, {"GAIAOS_EMOS_ENABLED": "true"}):
            assert "EMOS EXPRESSION CHANNEL:" in module.instructions("fake", "NIMUE")
            opt_in = module.respond(payload, session)
        assert opt_in["emos"]["status"] == "EMOS_SELECTED_FROM_OBSERVED_REPLY"
        assert enabled_calls == ["NIMUE"]
        assert any("EmotionOS/ATLAS" in p for p in loaded_paths)
        assert client.calls == 2
    print("EMOS_CLASSIC_ROLLBACK_PASS: default off, native headers, no extra model call; opt-in retained")

if __name__=="__main__":
    test_coverage();test_loader_allowlist();test_production_docker_copy();test_host();test_fallback();test_classic_solo_rollback()
    print("EMOS_CANARY_PASS: local fake-model proof ONLY, not live carrier")
