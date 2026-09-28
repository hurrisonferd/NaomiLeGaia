"""VASKON's cross-component SOURCE diagnostics for GaiaOS/GALAXY integration.

No provider calls, secrets, user history, production database, owner action or
automatic release. The script distinguishes SOURCE_INVARIANT_PASS from the
separate real-world conditions required before BIGBANG/SovereignOS cutover.
Prints compact machine-readable JSON; --out persists only non-secret results.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAEMONS = ("VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE")
SOURCE = ROOT / "api"


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def checkout_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNRESOLVED_LOCAL_CHECKOUT"


def diagnostic_report() -> dict:
    checks: dict[str, dict] = {}

    def record(name: str, passed: bool, detail: str) -> None:
        checks[name] = {
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        }

    roster_root = ROOT / "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA"
    actual = {p.name for p in roster_root.glob("*-EXPERIENCES.v1.md")}
    canonical = {name + "-EXPERIENCES.v1.md" for name in DAEMONS}
    record(
        "six_independently_attributed_e_lanes",
        actual == canonical and not (roster_root / "VASKON-EXPERIENCES.v1.md").exists(),
        "Exactly six individual E-LANES; synthesized VASKON cannot acquire a seventh.",
    )
    preserve = source(
        "GaiaOS/Plans/PRESERVE-AND-SIX-E-LANES-PERMANENT-DESIGN-INVARIANT.v1.md"
    )
    record(
        "permanent_preserve_protocol",
        "//PW:PRESERVE//" in preserve,
        "The owner preservation command and individual memory lanes remain mandatory.",
    )

    guard = source("api/gaiaos_presentation_guard.py")
    instructions = source(
        "GaiaOS/Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md"
    )
    record(
        "parallel_full_council_gate_integrated",
        all(x in guard for x in ("strict_full_cast", "expected_members_from_request",
                                 "full cast requires each canonical speaker once"))
        and "report in" in instructions.lower()
        and (ROOT / "GaiaOS/Plans/GAIAOS-2026-09-27-ROLLCALL-INCIDENT.v1.md").is_file(),
        "The #111 fail-closed roll-call source, reproducible canary and incident provenance are present in this exact checkout.",
    )

    runtime = source("api/memcon_runtime.py")
    pure = source("api/gaiaos_public_memory_boundary.py")
    gateway = source("api/gaiaos_memory_gateway.py")
    front = source("api/galaxy_frontdoor_context.py")
    entry = source("api/memcon_entrypoint.py")
    model_guard = source("api/gaiaos_chat_memory.py")
    record(
        "parallel_native_sql_and_public_archive_barriers_integrated",
        'upper(status) != ?' in runtime
        and 'lower(source) NOT LIKE ?' in runtime
        and "def galaxy_phase3_candidate_pool(" in runtime
        and "public_archive.unreleased(record)" in gateway
        and "public_archive.unreleased(record)" in front
        and "public_archive.unreleased(linked_record)" in front
        and "public_archive.unreleased(record)" in entry
        and "source.lstrip().lower().startswith(SOURCE_PREFIX)" in pure
        and 'item["source"].lower().startswith("galaxy-archive-v1:")' in model_guard,
        "Native pre-LIMIT, legacy, HTTP/MCP, independent preview, graph, and final model-instruction barriers share the source/held exclusion contract.",
    )
    record(
        "audited_exact_read_or_redacted_hold",
        "HOLD_AUDITED_READ_LEDGER_UNAVAILABLE" in entry
        and "MemconOS record not found" in entry,
        "Direct-held reads are indistinguishable from unknown; approved clean reads require an actual durable audit receipt.",
    )

    docker = source("api/Dockerfile")
    forbidden = (
        "galaxy_stage9ag_staging_historical_import.py",
        "galaxy_stage9ah_signed_staging_rollback.py",
        "galaxy_stage9ab_owner_local_bootstrap.py",
        "galaxy_archive_staging.py",
    )
    record(
        "actual_render_image_dependency_and_private_tooling_separation",
        "uvicorn browser_memcon_bridge:app" in docker
        and all(
            f"COPY api/{path} ./{path}" in docker
            for path in (
                "gaiaos_public_memory_boundary.py",
                "galaxy_legacy_gravity.py",
                "gaiaos_chat_auto_memory.py",
                "gaiaos_chat_memory.py",
                "memcon_runtime.py",
            )
        )
        and "COPY GaiaOS ./GaiaOS" in docker
        and all(("COPY api/" + path) not in docker for path in forbidden),
        "The actual served /chat image includes read-only runtime dependencies and excludes owner-private staging/migration code.",
    )

    bridge = source("api/browser_memcon_bridge.py")
    record(
        "solo_outage_and_explicit_isolated_recovery",
        all(x in bridge for x in (
            'HOLD_SOLO_STATE_UNVERIFIED',
            '@app.post("/chat/recovery"',
            '@app.get("/chat/recovery"',
            'HOLD_START_FRESH_GENERIC_MESSAGE_ONLY',
            'recovery_acknowledged',
        ))
        and "memcon_runtime.initialize()" not in entry[:entry.index("def _memory_runtime")],
        "Normal carrier import has no eager DB connection; a failed SOLO lookup cannot silently impersonate a new generic session.",
    )

    mode = source("api/gaiaos_memory_mode.py")
    record(
        "bigbang_still_intentionally_locked",
        '"effective_mode": HEATDEATH' in mode
        and '"bigbang_activation_enabled": False' in mode
        and "BIGBANG_RELEASE_GATE_NOT_YET_IMPLEMENTED" in mode,
        "Enhanced retrieval cannot be switched on by a persisted row or local CI assertion.",
    )

    complete_tables = set(re.findall(
        r"\bCREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-z_][a-z0-9_]*)\b",
        runtime, flags=re.I,
    ))
    staging_code = source("api/galaxy_stage9aa_preimport_readonly.py")
    staging_block = staging_code.split("EXPECTED_TABLES = {", 1)[1].split(
        "\n}", 1
    )[0]
    staging_tables = set(re.findall(
        r'^\s*"([a-z_][a-z0-9_]*)"\s*:', staging_block, flags=re.M,
    ))
    staging_expected = {
        "galaxy_stage9v_staging_identity", "galaxy_stage9v_canaries",
        "memory_records", "galaxy_stage9y_batches", "galaxy_stage9y_items",
        "galaxy_stage9z_rollbacks",
    }
    additional = sorted(complete_tables - staging_tables)
    record(
        "six_table_staging_represented_as_canary_only",
        staging_tables == staging_expected
        and "memory_records" in complete_tables and len(additional) >= 8,
        "Native runtime has more relational tables than the deliberate first-batch six-table staging sandbox. Full SOS migration remains separately required.",
    )

    browser = source("api/gaiaos_api.py")
    strict_mode_supported = all(s in browser for s in (
        'BROWSER_AUTH_MODE = os.getenv("GAIAOS_BROWSER_AUTH_MODE"',
        'if BROWSER_AUTH_MODE == "owner_login"',
        '@app.post("/gaiaos/owner-login"',
        'max_age=28800',
        'owner.v2.',
        'def owner_logout(',
    )) and (ROOT / "tests/test_gaiaos_strict_owner_login.py").is_file()
    record(
        "opt_in_browser_owner_key_login_source_gate",
        strict_mode_supported,
        "Explicit opt-in owner-key login prevents public cookie issuance, rejects legacy cookies, enforces server-side expiry, and requires a strong configured owner key. Current default remains legacy pending owner-controlled rollout; not independent MFA/identity proof.",
    )
    anonymous_cookie_bootstrap = (
        'BROWSER_AUTH_MODE = os.getenv("GAIAOS_BROWSER_AUTH_MODE", "legacy_public_bootstrap")' in browser
        and 'response.set_cookie(SESSION_COOKIE, _session_token()' in browser
    )
    release_holds = [
        {
            "id": "HOLD_OWNER_AUTHENTICATION",
            "severity": "BLOCKER",
            "reason": (
                "Current GaiaOS default is legacy public cookie bootstrap, "
                "NOT owner authentication. Source now provides optional strict "
                "owner-key login, but owner-controlled configuration, independent "
                "human/MFA proof and live access-control testing remain pending."
                if anonymous_cookie_bootstrap and strict_mode_supported else
                "Independent new-owner access controls have not been verified."
            ),
        },
        {
            "id": "HOLD_REAL_RENDER_SHA_AND_BROWSER",
            "severity": "BLOCKER",
            "reason": "No actual Render deployment revision or live end-to-end browser request was observed by this source-only CI.",
        },
        {
            "id": "HOLD_REAL_SCOPED_TURSO_STAGING_IMPORT_ROLLBACK",
            "severity": "BLOCKER",
            "reason": "Actual provider identity, staging-only token scope, first real source/canary/import, exact signed rollback and post-restart durability require owner-led evidence.",
        },
        {
            "id": "HOLD_BIGBANG_RELEASE_APPROVAL",
            "severity": "BLOCKER",
            "reason": "The controller is intentionally hard-locked to independent HEATDEATH. Owner-reviewed release prerequisites and explicit cutover are not complete.",
        },
        {
            "id": "HOLD_FULL_ORIGINAL_MEMORYOS_SOVMEM_MAIN_MIGRATION",
            "severity": "BLOCKER",
            "reason": "The six-table staging canary is not a full export/reconciliation of old graph, lifecycle, receipts, sessions, SOLO records, E-LANES and source history.",
        },
        {
            "id": "HOLD_OWNER_APPROVED_SOURCE_MERGE_AND_PRIVATE_RESTORE",
            "severity": "BLOCKER",
            "reason": "Stacked source, parallel-PR supersession, independent private SovereignOS repository, database restore and explicit human cutover are not yet approved or proven.",
        },
    ]
    failures = sorted(name for name, data in checks.items()
                      if data["status"] != "PASS")
    return {
        "schema": "gaiaos.galaxy.vaskon-marriage-diagnostics.v1",
        "checkout_sha": checkout_sha(),
        "execution": "STATIC_SOURCE_CHECKOUT_ONLY",
        "status": (
            "SOURCE_CONTRACT_FAILURE" if failures
            else "SOURCE_CONTRACTS_PASS_WITH_SEPARATE_RELEASE_HOLDS"
        ),
        "source_checks": checks,
        "failed_source_checks": failures,
        "native_schema": {
            "full_runtime_table_count": len(complete_tables),
            "isolated_staging_table_count": len(staging_tables),
            "native_tables_absent_from_staging": additional,
            "six_table_staging_is_complete_sovmem_migration": False,
        },
        "release_holds": release_holds,
        "external_turso_connections": 0,
        "private_owner_credentials_accessed": False,
        "production_deploy_observed": False,
        "full_source_history_retrieved": False,
        "bigbang_activated": False,
        "e_lanes_modified": False,
        "writes_performed": [],
        "proof_boundary": (
            "Static checkout checks are not full dynamic test results, an "
            "independent security review, real provider evidence, live Render "
            "SHA, approved data migration or SovereignOS readiness."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = diagnostic_report()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if result["failed_source_checks"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
