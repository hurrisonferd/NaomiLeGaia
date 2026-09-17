#!/usr/bin/env python3
"""Source canary for AgencyOS, WorkspaceOS, and EvolutionOS."""
from __future__ import annotations
import importlib.util, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

agency=load("GaiaOS/SystemsOS/Core/AgencyOS/Runtime/GAIAOS-AGENCY.v1.py","agency")
workspace=load("GaiaOS/SystemsOS/Core/WorkspaceOS/Runtime/GAIAOS-WORKSPACE.v1.py","workspace")
evolution=load("GaiaOS/SystemsOS/Core/EvolutionOS/Runtime/GAIAOS-EVOLUTION.v1.py","evolution")

p=agency.plan("build and verify a GaiaOS artifact",["READ","CREATE","DEPLOY"])
assert p["status"]=="PROPOSED" and "CREATE" in [x["name"] for x in p["capabilities"]]
h=agency.execute_capability("DEPLOY",False,{})
assert h["status"]=="HOLD"
with tempfile.TemporaryDirectory() as d:
    workspace.ROOT=Path(d).resolve()
    hold=workspace.write_artifact("canary.txt","gaia","GAIAOS-CANARY",False)
    assert hold["status"]=="HOLD"
    ok=workspace.write_artifact("canary.txt","gaia","GAIAOS-CANARY",True)
    assert ok["status"]=="EXECUTED"
    read=workspace.read_artifact("canary.txt")
    assert read["status"]=="OBSERVED" and read["content"]=="gaia"
e=evolution.propose("observed gap","provider missing","register provider","more agency",["AgencyOS"],"run canary","disable provider")
assert e["status"]=="PROPOSED" and e["automatic_adoption"] is False
print("GAIAOS_AGENCY_WORKSPACE_EVOLUTION_CANARY PASS")
