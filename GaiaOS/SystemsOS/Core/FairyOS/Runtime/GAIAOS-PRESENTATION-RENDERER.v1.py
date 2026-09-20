"""GaiaOS deterministic Prime Daemon presentation validator/renderer v1.1."""
import json
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[1] / "COUNCIL-PRESENTATION-SPEC.v1.json"
EMOJI_PATH = Path(__file__).resolve().parents[2] / "EmojiOS" / "EXPRESSION-REGISTRY.v1.json"

class PresentationError(ValueError):
    pass

def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_spec(path=SPEC_PATH):
    spec=_load(path); validate_spec(spec); return spec

def load_expressions(path=EMOJI_PATH):
    registry=_load(path); validate_expression_registry(registry); return registry

def validate_spec(spec):
    members=spec.get("members",{}); order=spec.get("speaker_order",[])
    if set(order) != set(members): raise PresentationError("speaker_order/member mismatch")
    seen_numbers=set(); seen_tuples=set(); required=spec["validation"]["required_member_fields"]
    for name,data in members.items():
        missing=[k for k in required if k not in data]
        if missing: raise PresentationError(f"{name}: missing {missing}")
        if data["gematria"] in seen_numbers: raise PresentationError("duplicate gematria")
        seen_numbers.add(data["gematria"])
        ident=(name,data["heart"],data["interest"])
        if ident in seen_tuples: raise PresentationError("duplicate identity tuple")
        seen_tuples.add(ident)
    return True

def validate_expression_registry(registry):
    for name,data in registry.get("members",{}).items():
        if not data.get("default"): raise PresentationError(f"{name}: missing default kaomoji")
        if not isinstance(data.get("expressions"),dict): raise PresentationError(f"{name}: expressions must map state to kaomoji")
    return True

def resolve_kaomoji(name, expression_state=None, registry=None):
    registry=registry or load_expressions()
    if name not in registry["members"]: raise PresentationError(f"unknown Prime Daemon in EmojiOS: {name}")
    member=registry["members"][name]
    if expression_state is None: return member["default"]
    return member["expressions"].get(expression_state, member["default"])

def canonical_header(name, expression_state=None, spec=None, registry=None):
    spec=spec or load_spec()
    if name not in spec["members"]: raise PresentationError(f"unknown Prime Daemon: {name}")
    d=spec["members"][name]; k=resolve_kaomoji(name,expression_state,registry)
    return f'{d["gematria"]} · {name} {d["heart"]} {d["interest"]} {k}'

def validate_header(name, header, expression_state=None, spec=None, registry=None):
    expected=canonical_header(name,expression_state,spec,registry)
    if header != expected: raise PresentationError(f"header mismatch: expected {expected!r}")
    return True

def render(name, content, expression_state=None, spec=None, registry=None):
    if not isinstance(content,str) or not content.strip(): raise PresentationError("content required")
    header=canonical_header(name,expression_state,spec,registry)
    return f"{header}\n{content}"
