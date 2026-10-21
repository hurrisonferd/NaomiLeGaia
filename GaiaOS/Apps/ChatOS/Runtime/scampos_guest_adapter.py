"""Optional ChatOS multi-Scamp adapter; does not alter FairyOS dispatch."""
import importlib.util
from pathlib import Path
REPO=Path(__file__).resolve().parents[4]
SCAMP_MODULE=REPO/"GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py"

def _scamp():
    spec=importlib.util.spec_from_file_location("gaiaos_scampos",SCAMP_MODULE)
    if spec is None or spec.loader is None: raise RuntimeError("ScampOS unavailable")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def decide_guest(turn,context="unknown",last_turn=None,roll=None,explicit=False,
                 muted=False,guest_id="SCAMP-001"):
    return _scamp().select(turn,context=context,last_turn=last_turn,roll=roll,
                           explicit=explicit,muted=muted,guest_id=guest_id)

def decide_guests(turn,context="unknown",last_turns=None,rolls=None,
                  explicit_guests=(),muted_guests=()):
    return _scamp().select_guests(turn,context=context,last_turns=last_turns,
                                  rolls=rolls,explicit_guests=explicit_guests,
                                  muted_guests=muted_guests)

def insert_guest(prime_before,guest_dialogue,prime_after,decision):
    if not decision.get("appear"): raise ValueError("not selected")
    scamp=_scamp()
    guest_id=decision.get("guest_id","SCAMP-001")
    expected=scamp.load_policy(guest_id)["guest_header"]
    if decision.get("header")!=expected: raise ValueError("guest identity mismatch")
    guest=scamp.render_guest(guest_dialogue,guest_id=guest_id)
    return "\n\n".join(x.strip() for x in (prime_before,guest,prime_after)
                       if isinstance(x,str) and x.strip())
