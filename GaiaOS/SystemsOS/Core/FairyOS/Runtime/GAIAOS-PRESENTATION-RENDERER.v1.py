"""GaiaOS deterministic Prime Daemon + synthesis-mode presentation validator/renderer v1.2."""
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

def _all_identity_records(spec):
    records={}
    for name,data in spec.get("members",{}).items():
        records[name]=(data,"member")
    for name,data in spec.get("synthesis_modes",{}).items():
        if name in records:
            raise PresentationError(f"duplicate identity name: {name}")
        records[name]=(data,"synthesis_mode")
    return records

def validate_spec(spec):
    members=spec.get("members",{}); order=spec.get("speaker_order",[])
    if set(order) != set(members): raise PresentationError("speaker_order/member mismatch")
    required=spec["validation"]["required_member_fields"]
    for name,data in members.items():
        missing=[k for k in required if k not in data]
        if missing: raise PresentationError(f"{name}: missing {missing}")

    synth_required=spec["validation"].get(
        "required_synthesis_fields",
        ["gematria","heart","symbol","accent","class","invocation","expression_policy"],
    )
    for name,data in spec.get("synthesis_modes",{}).items():
        missing=[k for k in synth_required if k not in data]
        if missing: raise PresentationError(f"{name}: missing synthesis fields {missing}")

    seen_numbers=set(); seen_tuples=set()
    for name,(data,kind) in _all_identity_records(spec).items():
        if data["gematria"] in seen_numbers: raise PresentationError("duplicate gematria")
        seen_numbers.add(data["gematria"])
        static=data.get("interest",data.get("symbol"))
        ident=(name,data["heart"],static)
        if ident in seen_tuples: raise PresentationError("duplicate identity tuple")
        seen_tuples.add(ident)
        if kind=="synthesis_mode" and not static:
            raise PresentationError(f"{name}: synthesis symbol required")
    return True

def validate_expression_registry(registry):
    for group_name in ("members","synthesis_modes"):
        for name,data in registry.get(group_name,{}).items():
            if not data.get("default"): raise PresentationError(f"{name}: missing default kaomoji")
            if not isinstance(data.get("expressions"),dict): raise PresentationError(f"{name}: expressions must map state to kaomoji")
    return True

def _expression_record(name,registry):
    if name in registry.get("members",{}):
        return registry["members"][name]
    if name in registry.get("synthesis_modes",{}):
        return registry["synthesis_modes"][name]
    raise PresentationError(f"unknown speaker in EmojiOS: {name}")

def resolve_kaomoji(name, expression_state=None, registry=None):
    registry=registry or load_expressions()
    member=_expression_record(name,registry)
    if expression_state is None: return member["default"]
    return member["expressions"].get(expression_state, member["default"])

def _identity_record(name,spec):
    if name in spec.get("members",{}):
        return spec["members"][name]
    if name in spec.get("synthesis_modes",{}):
        return spec["synthesis_modes"][name]
    raise PresentationError(f"unknown speaker: {name}")

def canonical_header(name, expression_state=None, spec=None, registry=None):
    spec=spec or load_spec()
    d=_identity_record(name,spec)
    static=d.get("interest",d.get("symbol"))
    k=resolve_kaomoji(name,expression_state,registry)
    return f'{d["gematria"]} · {name} {d["heart"]} {static} {k}'

def validate_header(name, header, expression_state=None, spec=None, registry=None):
    expected=canonical_header(name,expression_state,spec,registry)
    if header != expected: raise PresentationError(f"header mismatch: expected {expected!r}")
    return True

def render(name, content, expression_state=None, spec=None, registry=None):
    if not isinstance(content,str) or not content.strip(): raise PresentationError("content required")
    header=canonical_header(name,expression_state,spec,registry)
    return f"{header}\n{content}"
