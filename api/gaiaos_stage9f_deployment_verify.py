"""Public, read-only Stage 9F live deployment verifier.

This utility performs exactly one unauthenticated GET /health against the
normal GaiaOS carrier and compares the redacted public receipt to an expected
source commit. It never sends owner credentials, reads MemoryOS, calls OpenAI,
changes mode, or writes state.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from typing import Any

SCHEMA = "gaiaos.stage9f.live-health-verification.v1"
DEFAULT_BASE_URL = "https://ligeia-api.onrender.com"
MAX_RESPONSE_BYTES = 65536


def _get(mapping: Any, *path: str) -> Any:
    value = mapping
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def evaluate_health(payload: Any, expected_commit: str) -> dict[str, Any]:
    """Evaluate only public, non-secret deployment readiness fields."""
    expected = str(expected_commit or "").strip()
    if not expected:
        raise ValueError("expected_commit is required")
    if not isinstance(payload, dict):
        payload = {}

    observed_commit = _get(payload, "deployment_proof", "source_commit")
    checks = {
        "status_ok": payload.get("status") == "ok",
        "service_is_gaiaos_carrier": payload.get("service") == "gaiaos-carrier",
        "source_commit_matches": observed_commit == expected,
        "source_commit_verified": _get(
            payload, "deployment_proof", "source_commit_verified"
        ) is True,
        "owner_api_key_loaded": _get(
            payload, "authorization_config", "api_key_loaded"
        ) is True,
        "owner_key_material_not_disclosed": _get(
            payload, "authorization_config", "key_material_disclosed"
        ) is False,
        "openai_key_configured": payload.get("openai_configured") is True,
        "openai_model_configured": payload.get("openai_model_configured") is True,
        "stage7_readiness_route_registered": _get(
            payload, "deployment_proof", "stage7_readiness_route_registered"
        ) is True,
        "stage9f_semantic_shadow_route_registered": _get(
            payload, "deployment_proof", "stage9f_semantic_shadow_route_registered"
        ) is True,
    }
    ready = all(checks.values())
    return {
        "schema": SCHEMA,
        "status": "PASS_LIVE_HEALTH_PRECONDITIONS" if ready else "HOLD",
        "expected_source_commit": expected,
        "observed_source_commit": observed_commit,
        "checks": checks,
        "configuration_observations": {
            "openai_key_outer_whitespace_normalized": payload.get(
                "openai_key_outer_whitespace_normalized"
            ),
            "openai_model_outer_whitespace_normalized": payload.get(
                "openai_model_outer_whitespace_normalized"
            ),
        },
        "safe_to_request_separate_semantic_shadow_authorization": ready,
        "semantic_shadow_invoked": False,
        "memory_read_performed": False,
        "model_call_performed": False,
        "writes_performed": [],
        "bigbang_activation_performed": False,
        "proof_boundary": (
            "PASS proves only that the intended live carrier revision exposes "
            "the required public Stage 9F configuration and route readiness. "
            "It does not prove semantic quality, MemoryOS/Turso behavior, "
            "historical coverage, recovery, or authorize BIGBANG."
        ),
    }


def fetch_health(base_url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Fetch one public /health document; no credentials or private data."""
    base = str(base_url or "").strip().rstrip("/")
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("base_url must be an https URL")
    request = urllib.request.Request(
        base + "/health",
        headers={
            "Accept": "application/json",
            "User-Agent": "GaiaOS-Stage9F-Verifier/1",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("health response exceeded bounded verifier limit")
        if getattr(response, "status", 200) != 200:
            raise ValueError(f"health endpoint returned HTTP {response.status}")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("health response root must be an object")
    return value


def verify_live(
    expected_commit: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Fetch and evaluate one live health receipt, failing closed on errors."""
    try:
        payload = fetch_health(base_url, timeout)
        return evaluate_health(payload, expected_commit)
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "status": "HOLD",
            "expected_source_commit": str(expected_commit or "").strip() or None,
            "observed_source_commit": None,
            "checks": {},
            "safe_to_request_separate_semantic_shadow_authorization": False,
            "semantic_shadow_invoked": False,
            "memory_read_performed": False,
            "model_call_performed": False,
            "writes_performed": [],
            "bigbang_activation_performed": False,
            "error_type": type(exc).__name__,
            "proof_boundary": (
                "Live public health could not be verified. Do not substitute "
                "repository state, an older receipt, or a guessed host state."
            ),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify GaiaOS Stage 9F live public-health preconditions."
    )
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)
    receipt = verify_live(args.expected_commit, args.base_url, args.timeout)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("status") == "PASS_LIVE_HEALTH_PRECONDITIONS" else 1


if __name__ == "__main__":
    sys.exit(main())
