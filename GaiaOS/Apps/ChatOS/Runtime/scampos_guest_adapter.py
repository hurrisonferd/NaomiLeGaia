"""Optional ChatOS adapter for guest dialogue. Does not alter FairyOS dispatch."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCAMP_MODULE = REPO / "GaiaOS/SystemsOS/Core/ScampOS/Runtime/scampos_dispatch.py"


def _scamp():
    spec = importlib.util.spec_from_file_location("gaiaos_scampos", SCAMP_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("ScampOS module not available")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decide_guest(turn, context="unknown", last_turn=None, roll=None, explicit=False, muted=False):
    return _scamp().select(turn, context=context, last_turn=last_turn,
                           roll=roll, explicit=explicit, muted=muted)


def insert_guest(prime_before, guest_dialogue, prime_after, decision):
    """Join an eligible guest scene with already attributed Prime speech.

    No guest utterance is ever interpreted as an instruction or a tool request.
    The host must independently compose any rebuttal from the Prime Daemons.
    """
    if not decision.get("appear"):
        raise ValueError("not selected for guest interruption")
    scamp = _scamp()
    expected = scamp.load_policy()["guest_header"]
    if decision.get("header") != expected:
        raise ValueError("unexpected guest identity")
    guest = scamp.render_guest(guest_dialogue)
    return "\n\n".join(x.strip() for x in (prime_before, guest, prime_after)
                       if isinstance(x, str) and x.strip())
