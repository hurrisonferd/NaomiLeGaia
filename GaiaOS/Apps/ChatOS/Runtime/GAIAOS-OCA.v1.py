"""GaiaOS Operational Context Acquisition v1.

Read-only, provider-agnostic normalizer for operational-context evidence.

The host performs any real provider reads. This module accepts those observations,
classifies freshness, preserves provider provenance, surfaces conflicts, and emits
one bounded ephemeral packet. It performs no network, persistence, deployment,
or repository effects.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "gaiaos.oca.packet.v1"
COLLECTORS = ("SESSION", "SOURCE", "RUNTIME_CONTINUITY")
STATUSES = {"VERIFIED", "PARTIAL", "UNAVAILABLE", "UNKNOWN"}
SOURCE_CLASSES = {"SOURCE_READ", "TOOL_RESULT", "PROVIDER_RESULT", "SYSTEM_STATE", "UNKNOWN"}


class OCAError(RuntimeError):
    """Fail-closed validation error for malformed OCA input."""


def _parse_time(value: str) -> datetime:
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise OCAError("INVALID_TIMESTAMP") from exc
    if parsed.tzinfo is None:
        raise OCAError("TIMESTAMP_REQUIRES_OFFSET")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    return [copy.deepcopy(value)]


def _dict(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise OCAError(f"{field}_MUST_BE_OBJECT")
    return copy.deepcopy(value)


def _freshness(observed_at: str | None, max_age_seconds: int | None, now: datetime) -> str:
    if observed_at is None or max_age_seconds is None:
        return "UNKNOWN"
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds < 0:
        raise OCAError("MAX_AGE_SECONDS_INVALID")
    observed = _parse_time(observed_at)
    if observed > now:
        raise OCAError("OBSERVATION_FROM_FUTURE")
    age = (now - observed).total_seconds()
    return "FRESH" if age <= max_age_seconds else "STALE"


def _unknown_observation(name: str) -> dict[str, Any]:
    return {
        "collector": name,
        "status": "UNKNOWN",
        "source_class": "UNKNOWN",
        "provider": "UNOBSERVED",
        "observed_at": None,
        "max_age_seconds": None,
        "freshness": "UNKNOWN",
        "coordinates": {},
        "facts": {},
        "verified_facts": {},
        "unknowns": ["collector was not observed in this acquisition pass"],
        "errors": [],
    }


def normalize_observation(raw: dict[str, Any], now: datetime) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise OCAError("OBSERVATION_MUST_BE_OBJECT")

    collector = str(raw.get("collector", "")).strip().upper()
    if collector not in COLLECTORS:
        raise OCAError(f"UNKNOWN_COLLECTOR:{collector or 'EMPTY'}")

    status = str(raw.get("status", "UNKNOWN")).strip().upper()
    if status not in STATUSES:
        raise OCAError(f"UNKNOWN_STATUS:{status}")

    source_class = str(raw.get("source_class", "UNKNOWN")).strip().upper()
    if source_class not in SOURCE_CLASSES:
        raise OCAError(f"UNKNOWN_SOURCE_CLASS:{source_class}")

    provider = str(raw.get("provider", "")).strip()
    if not provider:
        raise OCAError("PROVIDER_REQUIRED")

    if raw.get("effect_authority") not in (None, "NONE"):
        raise OCAError("OCA_CANNOT_ACCEPT_EFFECT_AUTHORITY")
    if raw.get("persistence") not in (None, "EPHEMERAL_ONLY"):
        raise OCAError("OCA_CANNOT_ACCEPT_DURABLE_PERSISTENCE")

    observed_at_raw = raw.get("observed_at")
    observed_at = None if observed_at_raw is None else _iso(_parse_time(str(observed_at_raw)))
    max_age = raw.get("max_age_seconds")
    freshness = _freshness(observed_at, max_age, now)

    verified_facts = _dict(raw.get("verified_facts"), "VERIFIED_FACTS")
    if status != "VERIFIED" and verified_facts:
        raise OCAError("NON_VERIFIED_OBSERVATION_HAS_VERIFIED_FACTS")

    return {
        "collector": collector,
        "status": status,
        "source_class": source_class,
        "provider": provider,
        "observed_at": observed_at,
        "max_age_seconds": max_age,
        "freshness": freshness,
        "coordinates": _dict(raw.get("coordinates"), "COORDINATES"),
        "facts": _dict(raw.get("facts"), "FACTS"),
        "verified_facts": verified_facts,
        "unknowns": _list(raw.get("unknowns")),
        "errors": _list(raw.get("errors")),
    }


def _observation_sort_key(observation: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(observation.get("provider", "")),
        str(observation.get("observed_at") or ""),
        str(observation.get("source_class", "")),
        _sha256(observation),
    )


def _annotate(collector: str, provider: str, values: list[Any]) -> list[dict[str, Any]]:
    return [
        {"collector": collector, "provider": provider, "value": copy.deepcopy(value)}
        for value in values
    ]


def build_packet(
    *,
    objective: str,
    observations: list[dict[str, Any]],
    generated_at: str | None = None,
    exact_next_step: str | None = None,
) -> dict[str, Any]:
    objective = str(objective).strip()
    if not objective:
        raise OCAError("OBJECTIVE_REQUIRED")
    if not isinstance(observations, list):
        raise OCAError("OBSERVATIONS_MUST_BE_LIST")

    now = _parse_time(generated_at) if generated_at else datetime.now(timezone.utc)
    generated = _iso(now)

    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in COLLECTORS}
    seen: dict[str, set[str]] = {name: set() for name in COLLECTORS}
    for raw in observations:
        item = normalize_observation(raw, now)
        name = item["collector"]
        identity = _sha256(item)
        if identity in seen[name]:
            continue
        seen[name].add(identity)
        grouped[name].append(item)

    collectors: dict[str, list[dict[str, Any]]] = {}
    for name in COLLECTORS:
        items = sorted(grouped[name], key=_observation_sort_key)
        collectors[name] = items if items else [_unknown_observation(name)]

    field_observations: dict[str, list[dict[str, Any]]] = {}
    blockers: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []

    for name in COLLECTORS:
        for observation in collectors[name]:
            provider = observation["provider"]
            blockers.extend(_annotate(name, provider, _list(observation["facts"].get("blockers"))))
            unknowns.extend(_annotate(name, provider, observation["unknowns"]))
            unknowns.extend(
                _annotate(name, provider, [f"provider error: {err}" for err in observation["errors"]])
            )

            if observation["status"] in {"UNAVAILABLE", "UNKNOWN"}:
                unknowns.append(
                    {
                        "collector": name,
                        "provider": provider,
                        "value": f"{name} status is {observation['status']}",
                    }
                )
            if observation["freshness"] == "STALE":
                unknowns.append(
                    {
                        "collector": name,
                        "provider": provider,
                        "value": f"{name} observation is STALE",
                    }
                )

            if observation["status"] == "VERIFIED" and observation["freshness"] == "FRESH":
                for field, value in observation["verified_facts"].items():
                    field_observations.setdefault(str(field), []).append(
                        {
                            "collector": name,
                            "provider": provider,
                            "value": copy.deepcopy(value),
                        }
                    )

    verified_state: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    for field, entries in sorted(field_observations.items()):
        first = entries[0]["value"]
        if all(entry["value"] == first for entry in entries[1:]):
            verified_state[field] = copy.deepcopy(first)
        else:
            conflicts.append({"field": field, "observations": copy.deepcopy(entries)})
            blockers.append(
                {
                    "collector": entries[0]["collector"],
                    "provider": entries[0]["provider"],
                    "value": f"conflicting verified fact: {field}",
                }
            )

    capabilities: set[str] = set()
    for observation in collectors["SESSION"]:
        if observation["status"] != "VERIFIED" or observation["freshness"] != "FRESH":
            continue
        raw_caps = observation["verified_facts"].get("available_capabilities", [])
        if not isinstance(raw_caps, list):
            raise OCAError("AVAILABLE_CAPABILITIES_MUST_BE_LIST")
        capabilities.update(str(item).strip() for item in raw_caps if str(item).strip())

    last_effect = verified_state.get("last_verified_effect")

    body = {
        "schema": SCHEMA,
        "objective": objective,
        "generated_at": generated,
        "effect_authority": "NONE",
        "persistence": "EPHEMERAL_ONLY",
        "collectors": collectors,
        "verified_current_state": verified_state,
        "capabilities_available_now": sorted(capabilities),
        "last_verified_effect": copy.deepcopy(last_effect),
        "blockers": blockers,
        "unknowns": unknowns,
        "conflicts": conflicts,
        "exact_next_step": exact_next_step,
    }
    digest = _sha256(body)
    return {
        "schema": SCHEMA,
        "packet_id": f"OCA-{digest[:16]}",
        **{k: v for k, v in body.items() if k != "schema"},
        "packet_sha256": digest,
    }


def _load_input(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OCAError(f"INPUT_UNAVAILABLE:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise OCAError("INPUT_MUST_BE_OBJECT")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only GaiaOS OCA packet from supplied observations.")
    parser.add_argument("--input", required=True, help="JSON file containing objective and observations")
    args = parser.parse_args()

    payload = _load_input(Path(args.input))
    packet = build_packet(
        objective=payload.get("objective", ""),
        observations=payload.get("observations", []),
        generated_at=payload.get("generated_at"),
        exact_next_step=payload.get("exact_next_step"),
    )
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
