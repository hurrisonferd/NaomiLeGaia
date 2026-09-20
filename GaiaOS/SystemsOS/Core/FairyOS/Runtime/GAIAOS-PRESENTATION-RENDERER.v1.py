"""GaiaOS deterministic Prime Daemon presentation validator/renderer v1."""
import json
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[1] / "COUNCIL-PRESENTATION-SPEC.v1.json"

class PresentationError(ValueError):
    pass

def load_spec(path=SPEC_PATH):
    with open(path, encoding="utf-8") as f:
        spec=json.load(f)
    validate_spec(spec)
    return spec

def validate_spec(spec):
    members=spec.get("members",{})
    order=spec.get("speaker_order",[])
    if set(order) != set(members):
        raise PresentationError("speaker_order/member mismatch")
    seen_numbers=set(); seen_tuples=set()
    required=spec["validation"]["required_member_fields"]
    for name,data in members.items():
        missing=[k for k in required if k not in data]
        if missing: raise PresentationError(f"{name}: missing {missing}")
        if data["gematria"] in seen_numbers: raise PresentationError("duplicate gematria")
        seen_numbers.add(data["gematria"])
        ident=(name,data["heart"],data["interest"])
        if ident in seen_tuples: raise PresentationError("duplicate identity tuple")
        seen_tuples.add(ident)
    return True

def canonical_header(name, spec=None):
    spec=spec or load_spec()
    if name not in spec["members"]: raise PresentationError(f"unknown Prime Daemon: {name}")
    d=spec["members"][name]
    return f'{d["gematria"]} · {name} {d["heart"]} {d["interest"]}'

def validate_header(name, header, spec=None):
    expected=canonical_header(name,spec)
    if header != expected:
        raise PresentationError(f"header mismatch: expected {expected!r}")
    return True

def render(name, content, expression=None, spec=None):
    spec=spec or load_spec()
    header=canonical_header(name,spec)
    if expression is not None:
        # Expression tokens are dynamic and must be resolved/validated by EmojiOS upstream.
        header=f"{header} {expression}"
    return f"{header}\n{content}"
