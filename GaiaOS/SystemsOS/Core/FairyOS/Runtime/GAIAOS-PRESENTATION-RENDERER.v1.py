"""GaiaOS deterministic Prime Daemon + synthesis-mode presentation validator/renderer v1.3."""
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
    if set(order) != set(members):
        raise PresentationError("speaker_order/member mismatch")
    required=spec["validation"]["required_member_fields"]
    for name,data in members.items():
        missing=[k for k in required if k not in data]
        if missing:
            raise PresentationError(f"{name}: missing {missing}")

    synth_required=spec["validation"].get(
        "required_synthesis_fields",
        ["gematria","heart","symbol","accent","class","invocation","aliases","expression_policy"],
    )
    for name,data in spec.get("synthesis_modes",{}).items():
        missing=[k for k in synth_required if k not in data]
        if missing:
            raise PresentationError(f"{name}: missing synthesis fields {missing}")
        aliases=data.get("aliases")
        if not isinstance(aliases,list) or not aliases or not all(isinstance(x,str) and x for x in aliases):
            raise PresentationError(f"{name}: synthesis aliases must be a nonempty string list")
        if data["invocation"] in aliases:
            raise PresentationError(f"{name}: canonical invocation must not be duplicated in aliases")
        if len(set(aliases)) != len(aliases):
            raise PresentationError(f"{name}: duplicate synthesis aliases")

    seen_numbers=set(); seen_tuples=set(); seen_invocations=set()
    for name,(data,kind) in _all_identity_records(spec).items():
        if data["gematria"] in seen_numbers:
            raise PresentationError("duplicate gematria")
        seen_numbers.add(data["gematria"])
        static=data.get("interest",data.get("symbol"))
        ident=(name,data["heart"],static)
        if ident in seen_tuples:
            raise PresentationError("duplicate identity tuple")
        seen_tuples.add(ident)
        if kind=="synthesis_mode":
            if not static:
                raise PresentationError(f"{name}: synthesis symbol required")
            commands=[data["invocation"],*data["aliases"]]
            for command in commands:
                if command in seen_invocations:
                    raise PresentationError(f"duplicate synthesis invocation: {command}")
                seen_invocations.add(command)
    return True

def validate_expression_registry(registry):
    for group_name in ("members","synthesis_modes"):
        for name,data in registry.get(group_name,{}).items():
            if not data.get("default"):
                raise PresentationError(f"{name}: missing default kaomoji")
            if not isinstance(data.get("expressions"),dict):
                raise PresentationError(f"{name}: expressions must map state to kaomoji")
            legal=[data["default"],*data["expressions"].values()]
            if any(not isinstance(x,str) or not x for x in legal):
                raise PresentationError(f"{name}: invalid kaomoji value")
    return True

def _expression_record(name,registry):
    if name in registry.get("members",{}):
        return registry["members"][name]
    if name in registry.get("synthesis_modes",{}):
        return registry["synthesis_modes"][name]
    raise PresentationError(f"unknown speaker in EmojiOS: {name}")

def resolve_kaomoji(name, expression_state=None, registry=None):
    registry=registry or load_expressions()
    record=_expression_record(name,registry)
    if expression_state is None:
        return record["default"]
    return record["expressions"].get(expression_state, record["default"])

def _identity_record(name,spec):
    if name in spec.get("members",{}):
        return spec["members"][name],"member"
    if name in spec.get("synthesis_modes",{}):
        return spec["synthesis_modes"][name],"synthesis_mode"
    raise PresentationError(f"unknown speaker: {name}")

def normalize_synthesis_invocation(name, invocation, spec=None):
    """Require an explicit valid synthesis invocation and normalize aliases."""
    spec=spec or load_spec()
    data,kind=_identity_record(name,spec)
    if kind!="synthesis_mode":
        if invocation is not None:
            raise PresentationError(f"{name}: invocation is only valid for synthesis modes")
        return None
    if not isinstance(invocation,str) or not invocation:
        raise PresentationError(f"{name}: explicit synthesis invocation required")
    accepted={data["invocation"],*data.get("aliases",[])}
    if invocation not in accepted:
        raise PresentationError(f"{name}: invalid synthesis invocation")
    return data["invocation"]

def canonical_header(name, expression_state=None, spec=None, registry=None, invocation=None):
    spec=spec or load_spec()
    data,kind=_identity_record(name,spec)
    if kind=="synthesis_mode":
        normalize_synthesis_invocation(name,invocation,spec)
    elif invocation is not None:
        raise PresentationError(f"{name}: Prime Daemon header does not accept synthesis invocation")
    static=data.get("interest",data.get("symbol"))
    k=resolve_kaomoji(name,expression_state,registry)
    return f'{data["gematria"]} · {name} {data["heart"]} {static} {k}'

def validate_header(name, header, expression_state=None, spec=None, registry=None, invocation=None):
    expected=canonical_header(name,expression_state,spec,registry,invocation=invocation)
    if header != expected:
        raise PresentationError(f"header mismatch: expected {expected!r}")
    return True

def render(name, content, expression_state=None, spec=None, registry=None, invocation=None):
    """Render one attributed utterance. Synthesis modes fail closed unless explicitly conjured."""
    if not isinstance(content,str) or not content.strip():
        raise PresentationError("content required")
    header=canonical_header(name,expression_state,spec,registry,invocation=invocation)
    return f"{header}\n{content}"

def render_vaskon(content, invocation, expression_state=None, spec=None, registry=None):
    """Canonical explicit-conjure entrypoint for VASKON presentation."""
    return render(
        "VASKON",
        content,
        expression_state=expression_state,
        spec=spec,
        registry=registry,
        invocation=invocation,
    )
