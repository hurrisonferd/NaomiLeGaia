"""GaiaOS DjinnOS v1 bounded helper runtime.

Authority: NAOMI / LIGEIA
Day 0: 2026-10-03 19:41 -07:00

Djinn are stateless tools, not identities. This module deliberately keeps
judgment/authority above the dispatcher and fails closed on mutation boundaries.
"""
from __future__ import annotations

import copy
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

RUNTIME_VERSION = "1.0.0"
STATUS_GLYPH = "🧿"
ACTIVATION_MARK = "⌁"
ACTIVATION_TIMESTAMP = "2026-10-03T19:41:00-07:00"
ACTIVATION_UTC = "2026-10-04T02:41:00Z"
PRIMES = {"VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"}

HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "GaiaOS").is_dir() else HERE.parent
REGISTRY_PATH = ROOT / "GaiaOS/SystemsOS/Core/DjinnOS/Registry/DJINN-REGISTRY.v1.json"
CURRENT_PATH = ROOT / "GaiaOS/SystemsOS/Core/DjinnOS/CURRENT.json"

_EXPECTED = {
    "KYMER": "INDEX",
    "DRELAS": "JIG",
    "RONAVE": "FLOW",
    "AGREN": "QUEUE",
    "HALVEX": "SEAL",
    "SERA": "COURIER",
    "ORVAS": "WITNESS",
    "MALRIC": "LINTER",
    "MARVEK": "PROBE",
    "VASQAR": "TRACE",
    "USION": "SETTLE",
}

_REPLAY_LOCK = threading.Lock()
_CONSUMED_SALT_OPERATION_IDS: set[str] = set()


class DjinnError(RuntimeError):
    """Base DjinnOS fail-closed error."""


class SaltCircleBreach(DjinnError):
    """Raised when a requested effect leaves its authorization perimeter."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include an offset")
    return dt.astimezone(timezone.utc)


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


def load_registry() -> dict[str, Any]:
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DjinnError(f"DJINN_REGISTRY_UNAVAILABLE:{type(exc).__name__}") from exc
    members = registry.get("members")
    if not isinstance(members, list):
        raise DjinnError("DJINN_REGISTRY_INVALID:MEMBERS")
    observed: dict[str, str] = {}
    for row in members:
        if not isinstance(row, dict):
            raise DjinnError("DJINN_REGISTRY_INVALID:ROW")
        name = str(row.get("name", "")).upper()
        operation = str(row.get("operation_class", "")).upper()
        if not name or name in observed:
            raise DjinnError("DJINN_REGISTRY_INVALID:DUPLICATE_OR_EMPTY_NAME")
        observed[name] = operation
    if observed != _EXPECTED:
        raise DjinnError("DJINN_REGISTRY_INVALID:ROSTER_MISMATCH")
    if registry.get("status") != "ACTIVE" or registry.get("epoch") != 1:
        raise DjinnError("DJINN_REGISTRY_INVALID:DAY0_STATUS")
    if registry.get("status_glyph") != STATUS_GLYPH or registry.get("activation_mark") != ACTIVATION_MARK:
        raise DjinnError("DJINN_REGISTRY_INVALID:VISIBLE_GRAMMAR")
    if registry.get("retroactive_operation_claims") != "FORBIDDEN":
        raise DjinnError("DJINN_REGISTRY_INVALID:RETROACTIVITY")
    return registry


def status(source_commit: str | None = None) -> dict[str, Any]:
    registry = load_registry()
    active = datetime.now(timezone.utc) >= _parse_time(ACTIVATION_UTC)
    return {
        "schema": "gaiaos.djinn.status.v1",
        "status": "ACTIVE" if active else "ARMED_PENDING_DAY0",
        "authority": "NAOMI",
        "epoch": 1,
        "runtime_version": RUNTIME_VERSION,
        "operator_activation_timestamp": ACTIVATION_TIMESTAMP,
        "operator_activation_timestamp_utc": ACTIVATION_UTC,
        "source_commit": source_commit or "RESOLVE_FROM_CARRIER",
        "roster": [
            {"name": row["name"], "glyph": STATUS_GLYPH, "operation_class": row["operation_class"], "effect_class": row["effect_class"]}
            for row in registry["members"]
        ],
        "counts": {"djinn": 11, "durable_memories": 0, "elanes": 0},
        "dispatch_law": "FAIRYOS_SELECTS_PRIME_PRIME_SELECTS_DJINN",
        "recursion_policy": "FORBIDDEN",
        "retroactive_operation_claims": "FORBIDDEN",
        "salt_circle": {
            "status": "ENFORCED",
            "fail_closed": True,
            "replay_guard": "PROCESS_LOCAL_PLUS_HOST_REQUIRED_ACROSS_RESTARTS",
        },
        "halvex_external_effect_adapters": "NONE_BY_DEFAULT_DEPENDENCY_INJECTION_REQUIRED",
    }


def _member_for(selector: str) -> tuple[str, str]:
    selector_n = str(selector).strip().upper()
    if selector_n in _EXPECTED:
        return selector_n, _EXPECTED[selector_n]
    matches = [name for name, operation in _EXPECTED.items() if operation == selector_n]
    if len(matches) == 1:
        return matches[0], selector_n
    raise DjinnError(f"UNKNOWN_DJINN_OR_OPERATION:{selector_n or 'EMPTY'}")


def _base_result(name: str, operation: str, calling_prime: str, invocation_id: str) -> dict[str, Any]:
    return {
        "schema": "gaiaos.djinn.result.v1",
        "status": "OK",
        "invocation_id": invocation_id,
        "djinn": {"name": name, "glyph": STATUS_GLYPH, "activation_mark": ACTIVATION_MARK},
        "operation_performed": operation,
        "calling_prime": calling_prime,
        "effect_authority": "NONE_DJINN_CANNOT_CREATE_AUTHORITY",
        "evidence": [],
        "unknowns": [],
        "warnings": [],
        "next_required_proof": [],
        "completed_at": _iso_now(),
        "retroactive_claim": False,
    }


def _op_index(payload: dict[str, Any]) -> dict[str, Any]:
    values = payload.get("items", payload.get("records", []))
    if not isinstance(values, list):
        values = [values]
    keys = payload.get("keys", ["id", "record_id", "candidate_id", "receipt_id", "commit", "sha", "path", "version", "timestamp", "source"])
    if not isinstance(keys, list):
        raise DjinnError("INDEX_KEYS_MUST_BE_LIST")
    entries = []
    hashes: dict[str, list[int]] = {}
    for idx, item in enumerate(values):
        selected = {}
        if isinstance(item, dict):
            for key in keys:
                if key in item:
                    selected[str(key)] = copy.deepcopy(item[key])
        digest = _sha256(item)
        hashes.setdefault(digest, []).append(idx)
        entries.append({"index": idx, "coordinates": selected, "sha256": digest})
    duplicates = [positions for positions in hashes.values() if len(positions) > 1]
    compare = payload.get("compare")
    comparison = None
    if isinstance(compare, list) and len(compare) == 2:
        comparison = {"exact_equal": compare[0] == compare[1], "left_sha256": _sha256(compare[0]), "right_sha256": _sha256(compare[1])}
    return {"entries": entries, "exact_duplicate_index_groups": duplicates, "comparison": comparison}


def _step_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name", value.get("step", "")))
    return str(value)


def _op_jig(payload: dict[str, Any]) -> dict[str, Any]:
    required = payload.get("template", payload.get("required_steps", []))
    actual = payload.get("steps", [])
    if not isinstance(required, list) or not isinstance(actual, list):
        raise DjinnError("JIG_STEPS_MUST_BE_LISTS")
    req = [_step_name(x) for x in required]
    obs = [_step_name(x) for x in actual]
    missing = [step for step in req if step not in obs]
    positions = [obs.index(step) for step in req if step in obs]
    ordered = positions == sorted(positions) and len(positions) == len(req)
    invariant_failures = []
    invariants = payload.get("invariants", {})
    observed = payload.get("observed", {})
    if isinstance(invariants, dict) and isinstance(observed, dict):
        for key, expected in invariants.items():
            if key not in observed or observed[key] != expected:
                invariant_failures.append({"field": key, "expected": expected, "observed": observed.get(key, "UNKNOWN")})
    return {"conforms": not missing and ordered and not invariant_failures, "missing_steps": missing, "ordered": ordered, "invariant_failures": invariant_failures}


def _dedupe_lines(text: str) -> str:
    seen = set()
    out = []
    for raw in str(text).splitlines():
        line = raw.rstrip()
        key = line.strip()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(line)
    return "\n".join(out).strip()


def _op_flow(payload: dict[str, Any]) -> dict[str, Any]:
    body = _dedupe_lines(str(payload.get("text", "")))
    return {
        "compact_text": body,
        "evidence": copy.deepcopy(payload.get("evidence", [])),
        "warnings": copy.deepcopy(payload.get("warnings", [])),
        "unknowns": copy.deepcopy(payload.get("unknowns", [])),
        "substance_preservation": "PROTECTED_FIELDS_COPIED_VERBATIM",
    }


def _op_queue(payload: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(payload.get("state") or {})
    if not isinstance(state, dict):
        raise DjinnError("QUEUE_STATE_MUST_BE_OBJECT")
    action = str(payload.get("action", "INIT")).upper()
    if action == "INIT":
        state = {
            "active_objective": payload.get("active_objective"),
            "active_packet_id": payload.get("active_packet_id"),
            "current_step": payload.get("current_step"),
            "completed_steps": list(payload.get("completed_steps", [])),
            "blockers": list(payload.get("blockers", [])),
            "authority_state": payload.get("authority_state", "UNKNOWN"),
            "superseded_instructions": list(payload.get("superseded_instructions", [])),
        }
    elif action == "ADVANCE":
        current = state.get("current_step")
        if current is not None:
            state.setdefault("completed_steps", []).append(current)
        state["current_step"] = payload.get("current_step")
    elif action == "BLOCK":
        blocker = payload.get("blocker")
        if blocker is not None:
            state.setdefault("blockers", []).append(blocker)
    elif action == "SUPERSEDE":
        instruction = payload.get("instruction")
        if instruction is not None:
            state.setdefault("superseded_instructions", []).append(instruction)
    else:
        raise DjinnError(f"QUEUE_UNKNOWN_ACTION:{action}")
    return {"state": state, "ephemeral": True, "persisted": False, "cross_invocation_memory": False}


def _op_courier(payload: dict[str, Any]) -> dict[str, Any]:
    packet = {
        "schema": "gaiaos.djinn.courier-packet.v1",
        "objective": payload.get("objective"),
        "accepted_evidence": copy.deepcopy(payload.get("accepted_evidence", [])),
        "authority_envelope": copy.deepcopy(payload.get("authority_envelope", {})),
        "constraints": copy.deepcopy(payload.get("constraints", [])),
        "current_state": copy.deepcopy(payload.get("current_state", {})),
        "exact_next_step": payload.get("exact_next_step"),
        "unknowns": copy.deepcopy(payload.get("unknowns", [])),
    }
    return {"packet": packet, "packet_sha256": _sha256(packet)}


def _op_witness(payload: dict[str, Any]) -> dict[str, Any]:
    expected = payload.get("expected", {})
    observed = payload.get("observed", {})
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        raise DjinnError("WITNESS_EXPECTED_OBSERVED_MUST_BE_OBJECTS")
    required = payload.get("required_fields", list(expected.keys()))
    if not isinstance(required, list):
        raise DjinnError("WITNESS_REQUIRED_FIELDS_MUST_BE_LIST")
    comparisons = []
    missing = []
    mismatches = []
    for field in required:
        key = str(field)
        if key not in observed:
            missing.append(key)
            comparisons.append({"field": key, "status": "UNKNOWN"})
            continue
        if key in expected and observed[key] != expected[key]:
            mismatches.append(key)
            comparisons.append({"field": key, "status": "MISMATCH", "expected": expected[key], "observed": observed[key]})
        else:
            comparisons.append({"field": key, "status": "MATCH", "observed": observed[key]})
    verified = not missing and not mismatches
    return {"verified": verified, "comparisons": comparisons, "missing_fields": missing, "mismatches": mismatches, "proof_rule": "EXACT_FIELDS_ONLY_NO_INFERENCE"}


def _op_linter(payload: dict[str, Any]) -> dict[str, Any]:
    issues = []
    def flag(condition: bool, code: str, detail: str) -> None:
        if condition:
            issues.append({"code": code, "detail": detail})
    flag(payload.get("requested") is True and payload.get("completed") is not True, "REQUESTED_NOT_COMPLETED", "Requested work is not proven complete.")
    flag(payload.get("candidate") is True and payload.get("durable") is True and payload.get("readback") is not True, "CANDIDATE_DURABLE_WITHOUT_READBACK", "Durability claim lacks readback.")
    flag(payload.get("receipt") is True and payload.get("readback") is not True and payload.get("verified") is True, "RECEIPT_TREATED_AS_VERIFICATION", "Receipt alone is not verification.")
    flag(payload.get("source_present") is True and payload.get("runtime_present") is not True and payload.get("live_claim") is True, "SOURCE_RUNTIME_CONFLATION", "Source presence cannot prove runtime presence.")
    flag(payload.get("unknown_coerced") is True, "UNKNOWN_COERCION", "UNKNOWN must remain UNKNOWN.")
    flag(payload.get("cross_member_merge") is True, "CROSS_MEMBER_MERGE", "Member-owned records must remain separate.")
    flag(payload.get("authority_expanded") is True, "AUTHORITY_SCOPE_EXPANSION", "Authorization scope was enlarged.")
    flag(payload.get("retroactive_djinn_claim") is True, "RETROACTIVE_DJINN_CLAIM", "Djinn history may not predate Day 0.")
    flag(payload.get("nested_djinn") is True, "AUTONOMOUS_DJINN_CHAIN", "Djinn-to-Djinn autonomous spawning is forbidden.")
    return {"pass": not issues, "issues": issues, "rules_checked": 9}


def _op_probe(payload: dict[str, Any]) -> dict[str, Any]:
    required = payload.get("required_capabilities", [])
    observed = payload.get("observed_capabilities", {})
    if not isinstance(required, list) or not isinstance(observed, dict):
        raise DjinnError("PROBE_INVALID_CAPABILITY_SHAPE")
    normalized = {str(k): str(v).upper() for k, v in observed.items()}
    rows = []
    for capability in required:
        name = str(capability)
        state = normalized.get(name, "UNKNOWN")
        if state not in {"AVAILABLE", "UNAVAILABLE", "UNKNOWN"}:
            state = "UNKNOWN"
        rows.append({"capability": name, "state": state})
    ready = bool(rows) and all(row["state"] == "AVAILABLE" for row in rows)
    if not required:
        ready = True
    return {"ready": ready, "capabilities": rows, "unavailable": [r["capability"] for r in rows if r["state"] == "UNAVAILABLE"], "unknown": [r["capability"] for r in rows if r["state"] == "UNKNOWN"]}


def _op_trace(payload: dict[str, Any]) -> dict[str, Any]:
    order = list(payload.get("order", ["source", "test", "deployment", "route", "runtime", "persistence"]))
    stages = payload.get("stages", {})
    if not isinstance(stages, dict) or not isinstance(order, list):
        raise DjinnError("TRACE_INVALID_STAGE_SHAPE")
    rows = []
    highest = None
    blocked = False
    gaps = []
    for stage in order:
        name = str(stage)
        raw = stages.get(name, "UNKNOWN")
        if isinstance(raw, dict):
            state = str(raw.get("state", "UNKNOWN")).upper()
            evidence = copy.deepcopy(raw.get("evidence", []))
        else:
            state = str(raw).upper()
            evidence = []
        if state not in {"PROVEN", "UNPROVEN", "UNKNOWN", "NOT_APPLICABLE"}:
            state = "UNKNOWN"
        rows.append({"stage": name, "state": state, "evidence": evidence})
        if not blocked and state in {"PROVEN", "NOT_APPLICABLE"}:
            highest = name
        else:
            if state not in {"PROVEN", "NOT_APPLICABLE"}:
                blocked = True
                gaps.append(name)
    return {"stages": rows, "highest_contiguous_proof_stage": highest, "gaps": gaps, "complete": not gaps}


def _op_settle(payload: dict[str, Any]) -> dict[str, Any]:
    baseline = {
        "objective": payload.get("objective"),
        "verified_now": copy.deepcopy(payload.get("verified", [])),
        "superseded_operational_assumptions": copy.deepcopy(payload.get("superseded", [])),
        "historical_truth_preserved": True,
        "remaining_unknowns": copy.deepcopy(payload.get("unknowns", [])),
        "out_of_scope": copy.deepcopy(payload.get("out_of_scope", [])),
        "next_active_work": payload.get("next_active_work"),
    }
    return {"baseline": baseline, "persisted": False, "requires_separate_preservation_if_desired": True}


def _normalize_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, list):
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:ALLOWLIST_NOT_LIST")
    return {str(x) for x in value}


def validate_salt_circle(circle: dict[str, Any], *, invocation_id: str, consume: bool = False) -> dict[str, Any]:
    if not isinstance(circle, dict):
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:MISSING")
    if circle.get("authority") != "NAOMI":
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:AUTHORITY")
    if circle.get("operation_id") != invocation_id:
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:OPERATION_ID")
    if circle.get("single_use") is not True:
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:SINGLE_USE_REQUIRED")
    valid_until = circle.get("valid_until")
    if valid_until:
        try:
            if datetime.now(timezone.utc) > _parse_time(str(valid_until)):
                raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:EXPIRED")
        except ValueError as exc:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:INVALID_EXPIRY") from exc
    validated = {
        "authority": "NAOMI",
        "operation_id": invocation_id,
        "allowed_operations": _normalize_set(circle.get("allowed_operations")),
        "allowed_targets": _normalize_set(circle.get("allowed_targets")),
        "allowed_scopes": _normalize_set(circle.get("allowed_scopes")),
        "explicit_forbiddens": _normalize_set(circle.get("explicit_forbiddens", [])),
        "single_use": True,
    }
    if not validated["allowed_operations"] or not validated["allowed_targets"] or not validated["allowed_scopes"]:
        raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:EMPTY_ALLOWLIST")
    if consume:
        with _REPLAY_LOCK:
            if invocation_id in _CONSUMED_SALT_OPERATION_IDS:
                raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:REPLAY")
            _CONSUMED_SALT_OPERATION_IDS.add(invocation_id)
    return validated


def _op_seal(payload: dict[str, Any], *, invocation_id: str, salt_circle: dict[str, Any] | None, action_adapters: dict[str, Callable[[dict[str, Any]], Any]] | None) -> dict[str, Any]:
    circle = validate_salt_circle(salt_circle or {}, invocation_id=invocation_id, consume=False)
    steps = payload.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise DjinnError("SEAL_STEPS_REQUIRED")
    authorized = []
    for index, raw in enumerate(steps):
        if not isinstance(raw, dict):
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:STEP_NOT_OBJECT")
        operation = str(raw.get("operation", ""))
        target = str(raw.get("target", ""))
        scope = str(raw.get("scope", ""))
        if operation in circle["explicit_forbiddens"] or target in circle["explicit_forbiddens"] or scope in circle["explicit_forbiddens"]:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:EXPLICIT_FORBIDDEN")
        if operation not in circle["allowed_operations"]:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:OPERATION")
        if target not in circle["allowed_targets"]:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:TARGET")
        if scope not in circle["allowed_scopes"]:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:SCOPE")
        authorized.append({"index": index, "operation": operation, "target": target, "scope": scope, "payload": copy.deepcopy(raw.get("payload", {}))})
    if not action_adapters:
        return {
            "status": "READY_NO_EXECUTOR",
            "authorized_plan": authorized,
            "executed": [],
            "external_effects": False,
            "warning": "NO_EXTERNAL_ACTION_ADAPTERS_INJECTED",
        }
    validate_salt_circle(salt_circle or {}, invocation_id=invocation_id, consume=True)
    executed = []
    for step in authorized:
        adapter = action_adapters.get(step["operation"])
        if adapter is None:
            raise SaltCircleBreach("SALT_CIRCLE: BREACH_ATTEMPT:ADAPTER_UNAVAILABLE")
        outcome = adapter(copy.deepcopy(step))
        executed.append({"index": step["index"], "operation": step["operation"], "target": step["target"], "scope": step["scope"], "outcome": outcome})
    return {"status": "EXECUTED", "authorized_plan": authorized, "executed": executed, "external_effects": True}


_HANDLERS = {
    "INDEX": _op_index,
    "JIG": _op_jig,
    "FLOW": _op_flow,
    "QUEUE": _op_queue,
    "COURIER": _op_courier,
    "WITNESS": _op_witness,
    "LINTER": _op_linter,
    "PROBE": _op_probe,
    "TRACE": _op_trace,
    "SETTLE": _op_settle,
}


def dispatch(
    selector: str,
    *,
    calling_prime: str,
    objective: str,
    payload: dict[str, Any] | None = None,
    invocation_id: str | None = None,
    invoked_at: str | None = None,
    call_depth: int = 0,
    salt_circle: dict[str, Any] | None = None,
    action_adapters: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
) -> dict[str, Any]:
    """Run exactly one bounded Djinn operation and return control to the Prime."""
    load_registry()
    name, operation = _member_for(selector)
    prime = str(calling_prime).strip().upper()
    if prime not in PRIMES:
        raise DjinnError(f"CALLING_PRIME_REQUIRED:{prime or 'EMPTY'}")
    if int(call_depth) != 0:
        raise DjinnError("AUTONOMOUS_DJINN_TO_DJINN_SPAWNING_FORBIDDEN")
    if not str(objective).strip():
        raise DjinnError("ACTIVE_OBJECTIVE_REQUIRED")
    when = _parse_time(invoked_at) if invoked_at else datetime.now(timezone.utc)
    if when < _parse_time(ACTIVATION_UTC):
        raise DjinnError("RETROACTIVE_DJINN_INVOCATION_FORBIDDEN")
    invocation_id = invocation_id or f"DJINN-{uuid.uuid4().hex}"
    body = copy.deepcopy(payload or {})
    result = _base_result(name, operation, prime, invocation_id)
    try:
        if operation == "SEAL":
            operation_result = _op_seal(body, invocation_id=invocation_id, salt_circle=salt_circle, action_adapters=action_adapters)
        else:
            operation_result = _HANDLERS[operation](body)
    except SaltCircleBreach as exc:
        result.update({
            "status": "HALT",
            "result": {"error": str(exc), "action": "RETURN_TO_PRIME"},
            "warnings": ["SALT_CIRCLE_BREACH"],
            "next_required_proof": ["FRESH_EXPLICIT_AUTHORIZATION_OR_CORRECTED_SCOPE"],
        })
        return result
    result["result"] = operation_result
    if operation == "WITNESS" and not operation_result.get("verified", False):
        result["status"] = "HOLD"
        result["unknowns"] = list(operation_result.get("missing_fields", []))
        result["warnings"] = ["WITNESS_NOT_VERIFIED"] if operation_result.get("mismatches") else []
    elif operation == "PROBE" and not operation_result.get("ready", False):
        result["status"] = "HOLD"
        result["unknowns"] = list(operation_result.get("unknown", []))
        result["warnings"] = ["REQUIRED_CAPABILITY_UNAVAILABLE"] if operation_result.get("unavailable") else []
    elif operation == "LINTER" and not operation_result.get("pass", False):
        result["status"] = "HOLD"
        result["warnings"] = [issue["code"] for issue in operation_result.get("issues", [])]
    elif operation == "TRACE" and not operation_result.get("complete", False):
        result["status"] = "HOLD"
        result["unknowns"] = list(operation_result.get("gaps", []))
    elif operation == "JIG" and not operation_result.get("conforms", False):
        result["status"] = "HOLD"
    elif operation == "SEAL" and operation_result.get("status") == "READY_NO_EXECUTOR":
        result["status"] = "HOLD"
        result["warnings"] = ["NO_EXTERNAL_ACTION_ADAPTERS_INJECTED"]
    return result


def run_canary(source_commit: str | None = None, invoked_at: str | None = None) -> dict[str, Any]:
    """Exercise all eleven Djinn with bounded synthetic inputs; no external writes."""
    rows = []
    def run(selector: str, payload: dict[str, Any], prime: str = "ANVIL", **kwargs: Any) -> dict[str, Any]:
        out = dispatch(selector, calling_prime=prime, objective="DAY0_RUNTIME_CANARY", payload=payload, invoked_at=invoked_at, **kwargs)
        rows.append({"name": out["djinn"]["name"], "operation": out["operation_performed"], "status": out["status"]})
        return out

    run("KYMER", {"items": [{"id": "A", "commit": source_commit or "CANARY"}, {"id": "B"}]})
    run("DRELAS", {"template": ["A", "B"], "steps": ["A", "B"], "invariants": {"fail_closed": True}, "observed": {"fail_closed": True}})
    run("RONAVE", {"text": "alpha\nalpha\nbeta", "evidence": ["kept"], "warnings": [], "unknowns": []}, prime="SELENE")
    q = run("AGREN", {"action": "INIT", "active_objective": "canary", "current_step": "probe"}, prime="KESTREL")
    if q["result"].get("persisted") is not False:
        raise DjinnError("CANARY_QUEUE_PERSISTENCE_FAILURE")
    run("SERA", {"objective": "canary", "accepted_evidence": ["E1"], "exact_next_step": "DONE"}, prime="KESTREL")
    run("ORVAS", {"expected": {"x": 1}, "observed": {"x": 1}, "required_fields": ["x"]})
    run("MALRIC", {"requested": True, "completed": True, "readback": True, "verified": True})
    run("MARVEK", {"required_capabilities": ["registry"], "observed_capabilities": {"registry": "AVAILABLE"}})
    run("VASQAR", {"order": ["source", "runtime"], "stages": {"source": "PROVEN", "runtime": "PROVEN"}})
    run("USION", {"objective": "canary", "verified": ["runtime"], "superseded": [], "unknowns": [], "next_active_work": None}, prime="VERA")

    operation_id = f"DJINN-CANARY-{uuid.uuid4().hex}"
    circle = {
        "authority": "NAOMI",
        "operation_id": operation_id,
        "single_use": True,
        "allowed_operations": ["NOOP"],
        "allowed_targets": ["DJINN_CANARY"],
        "allowed_scopes": ["SYNTHETIC_NO_EXTERNAL_EFFECT"],
        "explicit_forbiddens": ["GITHUB_WRITE", "MEMORYOS_WRITE", "DEPLOY", "RESTART"],
    }
    def noop(step: dict[str, Any]) -> dict[str, Any]:
        return {"status": "PASS", "external_mutation": False, "target": step["target"]}
    halvex = run(
        "HALVEX",
        {"steps": [{"operation": "NOOP", "target": "DJINN_CANARY", "scope": "SYNTHETIC_NO_EXTERNAL_EFFECT"}]},
        invocation_id=operation_id,
        salt_circle=circle,
        action_adapters={"NOOP": noop},
    )
    if halvex["result"].get("status") != "EXECUTED":
        raise DjinnError("CANARY_HALVEX_EXECUTION_FAILURE")
    names = {row["name"] for row in rows}
    all_pass = names == set(_EXPECTED) and all(row["status"] == "OK" for row in rows)
    return {
        "schema": "gaiaos.djinn.canary.v1",
        "status": "PASS" if all_pass else "FAIL",
        "source_commit": source_commit or "RESOLVE_FROM_CARRIER",
        "operator_activation_timestamp": ACTIVATION_TIMESTAMP,
        "external_mutations": [],
        "rows": rows,
        "count": len(rows),
        "all_eleven_exercised": names == set(_EXPECTED),
    }
