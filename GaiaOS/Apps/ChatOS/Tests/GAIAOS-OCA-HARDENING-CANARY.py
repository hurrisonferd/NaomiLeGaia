#!/usr/bin/env python3
"""Read-only hardening canary for GaiaOS OCA v1.

This canary is intentionally a bounded tripwire. It inventories explicit workflow
write signals, validates adapter isolation/minimization laws, and checks that OCA
keeps expected automation distinct from observed secondary effects.
"""
from __future__ import annotations

import json
from pathlib import Path

CHATOS = Path(__file__).resolve().parents[1]
REPO = CHATOS.parents[2]
PROTOCOLS = CHATOS / "Protocols"
HARDENING = PROTOCOLS / "GAIAOS-OCA-HARDENING.v1.md"
HOTCARD = PROTOCOLS / "GAIAOS-OCA-HOTCARD.v1.json"
ADAPTERS = PROTOCOLS / "GAIAOS-OCA-ADAPTERS.v1.json"
EFFECTS = PROTOCOLS / "GAIAOS-OCA-DOWNSTREAM-EFFECTS.v1.json"
WORKFLOWS = REPO / ".github/workflows"

for path in (HARDENING, HOTCARD, ADAPTERS, EFFECTS, WORKFLOWS):
    assert path.exists(), path

hardening = HARDENING.read_text(encoding="utf-8")
for token in (
    "OCA_PACKET != TRUTH",
    "AVAILABLE_TO_READ != REQUIRED_TO_READ",
    "SOURCE_DIFF != TOTAL_EFFECT_SURFACE",
    "EXPECTED_AUTOMATION != OBSERVED_SECONDARY_EFFECT",
    "SILENCE != NO_SECONDARY_EFFECT",
    "READ LESS; PROVE ENOUGH",
):
    assert token in hardening, token

hotcard = json.loads(HOTCARD.read_text(encoding="utf-8"))
assert hotcard["version"] == "1.1.0"
assert hotcard["effect_authority"] == "NONE"
assert hotcard["persistence"] == "EPHEMERAL_ONLY"
rules = hotcard["acquisition_rules"]
assert rules["smallest_sufficient_read_set"] is True
assert rules["task_selected_provider_set"] is True
assert rules["provider_availability_is_not_read_justification"] is True
assert rules["collect_irrelevant_personal_data"] is False
assert rules["packet_is_truth"] is False
assert rules["source_diff_is_total_effect_surface"] is False
assert rules["expected_automation_is_observed_effect"] is False
preflight = hotcard["repository_effect_preflight"]
assert preflight["inspect_write_capable_workflow_inventory_when_relevant"] is True
assert preflight["completion_requires_secondary_effect_accounting_when_expected"] is True
assert preflight["silent_downstream_state_means_no_effect"] is False
assert preflight["classifications"] == [
    "DIRECT_EFFECT",
    "EXPECTED_AUTOMATION",
    "OBSERVED_SECONDARY_EFFECT",
    "UNRESOLVED_DOWNSTREAM_EFFECT",
]

adapters = json.loads(ADAPTERS.read_text(encoding="utf-8"))
assert adapters["version"] == "1.1.0"
assert adapters["adapter_law"]["versioned"] is True
assert adapters["adapter_law"]["single_collector_binding"] is True
assert adapters["adapter_law"]["cross_adapter_authority_grant"] is False
allowed_collectors = {"SESSION", "SOURCE", "RUNTIME_CONTINUITY"}
for name, adapter in adapters["adapters"].items():
    assert adapter["adapter_version"], name
    assert adapter["collector"] in allowed_collectors, name
    assert adapter["read_only"] is True, name
    forbidden = set(adapter.get("forbidden_operations", []))
    assert forbidden, name
    accepted = set(adapter.get("accepted_read_operations", [])) | set(adapter.get("accepted_read_surfaces", []))
    assert not ({"TRIGGER_DEPLOY", "WRITE_RECORD", "CREATE_OR_UPDATE_FILE", "MOVE_REF"} & accepted), name
assert "GITHUB_WORKFLOW_EFFECT_SURFACE" in adapters["adapters"]
assert adapters["normalization_rules"]["do_not_read_irrelevant_personal_data"] is True
assert adapters["normalization_rules"]["provider_availability_alone_does_not_justify_read"] is True

effects = json.loads(EFFECTS.read_text(encoding="utf-8"))
assert effects["status"] == "ACTIVE_READ_ONLY_EFFECT_SURFACE_INVENTORY"
assert effects["effect_authority"] == "NONE"
assert effects["persistence"] == "EPHEMERAL_ONLY"
assert effects["classification_order"] == [
    "DIRECT_EFFECT",
    "EXPECTED_AUTOMATION",
    "OBSERVED_SECONDARY_EFFECT",
    "UNRESOLVED_DOWNSTREAM_EFFECT",
]
policy = effects["discovery_policy"]
assert policy["scan_workflow_directory_in_canary"] is True
assert policy["unregistered_write_capable_workflow"] == "FAIL_CANARY"
assert policy["registered_workflow_missing"] == "FAIL_CANARY"
assert policy["inventory_is_not_authority"] is True
assert policy["inventory_is_not_proof_that_a_workflow_ran"] is True
assert policy["bounded_signal_scan_is_exhaustive_proof"] is False

# Tripwire: discover workflows carrying the bounded explicit write signals in the
# inventory. This does not claim to prove the absence of every possible effect.
signals = [str(item).lower() for item in policy["write_signals"]]
discovered: set[str] = set()
for path in sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))):
    text = path.read_text(encoding="utf-8").lower()
    if any(signal in text for signal in signals):
        discovered.add(path.relative_to(REPO).as_posix())

registered = {item["path"] for item in effects["workflows"]}
missing_from_inventory = sorted(discovered - registered)
stale_inventory = sorted(registered - discovered)
assert not missing_from_inventory, f"UNREGISTERED_WRITE_CAPABLE_WORKFLOWS:{missing_from_inventory}"
assert not stale_inventory, f"REGISTERED_WORKFLOW_NO_LONGER_MATCHES_WRITE_SIGNALS:{stale_inventory}"

for item in effects["workflows"]:
    path = REPO / item["path"]
    assert path.is_file(), item["path"]
    lower = path.read_text(encoding="utf-8").lower()
    declared_signals = [str(signal).lower() for signal in item["write_signals"]]
    assert any(signal in lower for signal in declared_signals), (
        item["path"],
        "none of the declared write signals are present",
    )

# Specific regression for the secondary effect discovered during OCA promotion.
identity_sync = next(
    item for item in effects["workflows"]
    if item["path"] == ".github/workflows/GAIAOS-MEMBER-IDENTITY-SYNC.yml"
)
identity_text = (REPO / identity_sync["path"]).read_text(encoding="utf-8")
assert "branches: [main]" in identity_text
assert "paths-ignore:" in identity_text
assert "GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA/**" in identity_text
assert "SOURCE_CHANGE_SYNC" in identity_text
assert "no experience or internal state was inferred" in identity_text

# Regression for multi-commit push boundaries: the workflow must have complete
# history so github.event.before and github.sha can always be diffed exactly.
assert "fetch-depth: 0" in identity_text
assert "fetch-depth: 2" not in identity_text

print("OCA_HARDENING_CANARY PASS")
