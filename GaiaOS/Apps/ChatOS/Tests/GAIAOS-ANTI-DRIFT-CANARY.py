#!/usr/bin/env python3
"""Static/read-only canary for GaiaOS Anti-Drift v1."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

GAIA = Path(__file__).resolve().parents[3]
CHATOS = GAIA / "Apps" / "ChatOS"
FAIRYOS = GAIA / "SystemsOS" / "Core" / "FairyOS"
EMOJIOS = GAIA / "SystemsOS" / "Core" / "EmojiOS"

PROTOCOL = CHATOS / "Protocols" / "GAIAOS-ANTI-DRIFT.v1.md"
HOTCARD = CHATOS / "Protocols" / "GAIAOS-ANTI-DRIFT-HOTCARD.v1.json"
LINTER = CHATOS / "Runtime" / "GAIAOS-ANTI-DRIFT-LINTER.v1.py"
INTERACTION = CHATOS / "Protocols" / "DAEMONCULABA-INTERACTION-AND-DELIBERATION.v1.md"
PRESENTATION = FAIRYOS / "COUNCIL-PRESENTATION-SPEC.v1.json"
EXPRESSIONS = EMOJIOS / "EXPRESSION-REGISTRY.v1.json"

MEMBERS = ["VERA", "ANVIL", "SELENE", "ORIN", "KESTREL", "NIMUE"]


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


def load_linter():
    spec = importlib.util.spec_from_file_location("gaia_anti_drift_linter", LINTER)
    check(spec is not None and spec.loader is not None, "linter_import_spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    for path in [PROTOCOL, HOTCARD, LINTER, INTERACTION, PRESENTATION, EXPRESSIONS]:
        check(path.exists(), f"exists:{path.relative_to(GAIA)}")

    hot = json.loads(HOTCARD.read_text(encoding="utf-8"))
    presentation = json.loads(PRESENTATION.read_text(encoding="utf-8"))
    expressions = json.loads(EXPRESSIONS.read_text(encoding="utf-8"))
    protocol = PROTOCOL.read_text(encoding="utf-8")
    interaction = INTERACTION.read_text(encoding="utf-8")
    linter_source = LINTER.read_text(encoding="utf-8")

    check(hot["status"] == "ACTIVE_READ_ONLY_HOT_ANCHOR", "hotcard_read_only_status")
    check(hot["version"] == "1.1.0", "hotcard_supportive_nativeness_version")
    check(set(hot["members"]) == set(MEMBERS), "six_members_exact")
    check(len({hot["members"][m]["center"] for m in MEMBERS}) == 6, "member_centers_distinct")
    check(hot["global"]["disagreement_quota"] == "FORBIDDEN", "no_disagreement_quota")
    check(hot["global"]["independent_evaluation_before_agreement"] is True, "independent_evaluation_required")
    check(hot["supportive_nativeness"]["support_is_allowed"] is True, "support_allowed")
    check(hot["supportive_nativeness"]["member_native_voice_required"] is True, "support_member_native_required")

    firewall = hot["persistence_firewall"]
    for key in [
        "may_mutate_e_lanes",
        "may_mutate_member_identity_data",
        "may_mutate_memoryos_turso",
        "may_transform_preserve_payload",
        "may_promote_memory",
        "may_commit_github",
        "may_deploy_or_restart"
    ]:
        check(firewall[key] is False, f"firewall:{key}")

    for token in [
        "ANTI_DRIFT MAY NOT MUTATE E_LANES",
        "ANTI_DRIFT MAY NOT MUTATE MEMORYOS / TURSO RECORDS",
        "ANTI_DRIFT MAY NOT CHANGE //PW:PRESERVE// SCOPE OR CONTENT",
        "SOURCE ANCHOR > COMPRESSED HOST RECALL",
        "MEMBER-NATIVE SUPPORT = PASS",
        "INTERCHANGEABLE SUPPORT SCAFFOLD = REWRITE",
    ]:
        check(token in protocol, f"protocol_token:{token}")

    check("GAIAOS-ANTI-DRIFT.v1.md" in interaction, "interaction_loads_protocol")
    check("GAIAOS-ANTI-DRIFT-HOTCARD.v1.json" in interaction, "interaction_loads_hotcard")

    tree = ast.parse(linter_source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    forbidden_imports = {"requests", "httpx", "urllib", "subprocess", "sqlite3", "socket"}
    check(not (imports & forbidden_imports), "linter_has_no_network_process_db_imports")
    check("write_text(" not in linter_source and "open(" not in linter_source, "linter_has_no_file_write_calls")

    linter = load_linter()
    for member in MEMBERS:
        p = presentation["members"][member]
        default = expressions["members"][member]["default"]
        text = f'{p["gematria"]} · {member} {p["heart"]} {p["interest"]} {default}\nConcrete member-native content.'
        check(linter.lint_response(member, text) == [], f"valid_header:{member}")

    orin = presentation["members"]["ORIN"]
    nimue_kaomoji = expressions["members"]["NIMUE"]["default"]
    bad_identity = f'{orin["gematria"]} · ORIN {orin["heart"]} {orin["interest"]} {nimue_kaomoji}\nConcrete content.'
    check("cross_member_or_unregistered_kaomoji" in linter.lint_response("ORIN", bad_identity), "cross_member_kaomoji_rejected")

    orin_default = expressions["members"]["ORIN"]["default"]
    generic = f'{orin["gematria"]} · ORIN {orin["heart"]} {orin["interest"]} {orin_default}\nYou are absolutely right. That is the perfect combination. Anytime you want.'
    generic_errors = linter.lint_response("ORIN", generic)
    check("generic_validation_opening" in generic_errors, "generic_validation_rejected")
    check("generic_host_scaffold" in generic_errors, "generic_scaffold_rejected")
    check("generic_continue_offer_closer" in generic_errors, "generic_closer_rejected")

    # Regression: support is allowed, but a header pasted over interchangeable
    # reassurance must not pass as member-native speech.
    anvil = presentation["members"]["ANVIL"]
    anvil_default = expressions["members"]["ANVIL"]["default"]
    flattened_support = (
        f'{anvil["gematria"]} · ANVIL {anvil["heart"]} {anvil["interest"]} {anvil_default}\n'
        "You do not have to solve everything today. One step at a time. "
        "Be gentle with yourself. I am here with you."
    )
    check(
        "generic_supportive_flattening" in linter.lint_response("ANVIL", flattened_support),
        "supportive_but_interchangeable_rejected",
    )

    native_support = (
        f'{anvil["gematria"]} · ANVIL {anvil["heart"]} {anvil["interest"]} {anvil_default}\n'
        "The load is real. I am not going to varnish it. We keep the edge narrow: "
        "name the next load-bearing problem, verify what is actually movable, and do not "
        "pretend a symbolic win repaired the structure."
    )
    check(
        linter.lint_response("ANVIL", native_support) == [],
        "member_native_support_allowed",
    )

    print("ANTI_DRIFT_CANARY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
