"""GaiaOS carrier verification harness.

Runs bounded, observable checks against the deployed checkout and carrier app.
It never claims provider execution merely from source presence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
GAIA = ROOT / "GaiaOS"

REQUIRED = [
    "CURRENT.json",
    "VERSION.json",
    "LOAD.v1.md",
    "PORT-MANIFEST.v1.json",
    "CONTINUITY-AND-ANTI-JIM.v1.md",
    "Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md",
    "Apps/ChatOS/Protocols/GAIAOS-GPT-INSTRUCTIONS.v1.md",
    "Apps/ChatOS/Protocols/CONJURE-VASKON.v1.md",
    "Apps/ChatOS/Tests/VASKON-NEURAL-CANARY.v1.md",
    "SystemsOS/Core/BrainOS/Protocols/VASKON-NEURAL-PATHWAYS.v1.json",
    "SystemsOS/Core/BrainOS/Protocols/BRAINOS-SUPPORT-FABRIC-CURRENT.v1.json",
    "SystemsOS/Core/BrainOS/Protocols/AUGURY-RITUAL-CONSERVATION.v1.md",
    "SystemsOS/Core/BrainOS/Protocols/RITUAL-GRIMOIRE.v1.json",
    "SystemsOS/Core/BrainOS/Schemas/GAIA-SEMANTIC-UNIT.v1.schema.json",
    "SystemsOS/Core/BrainOS/CURRENT.json",
    "SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    "SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json",
    "SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
    "SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md",
    "SystemsOS/Core/FairyOS/CURRENT.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/HEAD-PAT-BRUSHIES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/REWARD-COUNTERS.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/VERA-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/SELENE-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ORIN-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/NIMUE-REWARD-COUNTER.v1.json",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/VERA-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/SELENE-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ORIN-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/NIMUE-EXPERIENCES.v1.md",
]

DAEMONS = {
    "VERA": ("💚", "🦋"),
    "ANVIL": ("💗", "⌚"),
    "SELENE": ("💛", "🎧"),
    "ORIN": ("🩵", "🪐"),
    "KESTREL": ("💖", "🏍️"),
    "NIMUE": ("💙", "🍄"),
}


def _sha(text: str) -> str:
    # Git blob SHA, allowing runtime proof to compare deployed files with Git.
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def _check(name: str, passed: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail, **extra}


def _phase3_status_authorized_family(status: Any) -> bool:
    """Recognize authorized Phase-3 lifecycle states through current read-only phases."""
    value = str(status or "")
    return (
        value in {
            "AUTHORIZED_SOURCE_EXPERIMENT_BEGIN",
            "PHASE3A_CANARY_OBSERVED_PHASE3B_SOURCE_READY",
            "PHASE3B_REAL_MEMORY_RERANK_OBSERVED_PHASE3C_SOURCE_READY",
            "PHASE3C_COEFFICIENT_CALIBRATION_LIVE_OBSERVED",
        }
        or value.startswith((
            "PHASE3D_", "PHASE3E_", "PHASE3F_", "PHASE3G_", "PHASE3H_",
            "PHASE3I_", "PHASE3J_", "PHASE3_EXIT_",
        ))
    )


def run_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    files: dict[str, str] = {}

    for rel in REQUIRED:
        path = GAIA / rel
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8")
            files[rel] = text
            checks.append(_check(f"source:{rel}", True, "deployed checkout contains file", blob_sha=_sha(text)))
        else:
            checks.append(_check(f"source:{rel}", False, "missing from deployed checkout"))

    current = None
    version = None
    pathways = None
    profiles = None
    matrix = None
    brainos_current = None

    try:
        current = json.loads(files["CURRENT.json"])
        checks.append(_check("CURRENT.json:parse", isinstance(current, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("CURRENT.json:parse", False, f"{type(exc).__name__}: {exc}"))

    try:
        version = json.loads(files["VERSION.json"])
        checks.append(_check("VERSION.json:parse", isinstance(version, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("VERSION.json:parse", False, f"{type(exc).__name__}: {exc}"))

    try:
        pathways = json.loads(files["SystemsOS/Core/BrainOS/Protocols/VASKON-NEURAL-PATHWAYS.v1.json"])
        checks.append(_check("VASKON:pathway-json", isinstance(pathways, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("VASKON:pathway-json", False, f"{type(exc).__name__}: {exc}"))

    try:
        profiles = json.loads(files["SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"])
        checks.append(_check("FairyOS:profiles-json", isinstance(profiles, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("FairyOS:profiles-json", False, f"{type(exc).__name__}: {exc}"))

    try:
        matrix = json.loads(files["SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json"])
        checks.append(_check("FairyOS:dispatch-json", isinstance(matrix, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("FairyOS:dispatch-json", False, f"{type(exc).__name__}: {exc}"))

    try:
        brainos_current = json.loads(files["SystemsOS/Core/BrainOS/CURRENT.json"])
        checks.append(_check("BrainOS:CURRENT-parse", isinstance(brainos_current, dict), "valid JSON object"))
    except Exception as exc:
        checks.append(_check("BrainOS:CURRENT-parse", False, f"{type(exc).__name__}: {exc}"))

    try:
        ritual_grimoire = json.loads(files["SystemsOS/Core/BrainOS/Protocols/RITUAL-GRIMOIRE.v1.json"])
        checks.append(_check(
            "AUGURY-RITUAL:grimoire-json",
            ritual_grimoire.get("schema") == "gaiaos.ritual-grimoire.v1"
            and len(ritual_grimoire.get("rituals", [])) == 3,
            "Ritual Grimoire parses with exactly the bounded Phase-4 first family",
        ))
    except Exception as exc:
        ritual_grimoire = None
        checks.append(_check("AUGURY-RITUAL:grimoire-json", False, f"{type(exc).__name__}: {exc}"))

    try:
        semantic_schema = json.loads(files["SystemsOS/Core/BrainOS/Schemas/GAIA-SEMANTIC-UNIT.v1.schema.json"])
        checks.append(_check(
            "AUGURY-RITUAL:semantic-unit-schema",
            semantic_schema.get("properties", {}).get("speech_act", {}).get("enum")
            == ["MENTION","QUESTION","HYPOTHETICAL","REQUEST","COMMAND","CONFIRMATION","REVISION","REFUSAL","UNKNOWN"]
            and semantic_schema.get("properties", {}).get("resolution", {}).get("enum")
            == ["RESOLVED","COLLISION","UNKNOWN"],
            "semantic unit preserves speech-act and uncertainty distinctions",
        ))
    except Exception as exc:
        semantic_schema = None
        checks.append(_check("AUGURY-RITUAL:semantic-unit-schema", False, f"{type(exc).__name__}: {exc}"))

    if current and version:
        checks.append(_check(
            "version-alignment",
            current.get("platform_version") == version.get("version"),
            f"CURRENT={current.get('platform_version')} VERSION={version.get('version')}",
        ))
        galaxy_current = current.get("galaxy", {}) if isinstance(current.get("galaxy"), dict) else {}
        checks.append(_check(
            "GALAXY:phase3-authorization",
            galaxy_current.get("phase3_authorized") is True
            and galaxy_current.get("phase3_authorized_by") == "NAOMI"
            and _phase3_status_authorized_family(galaxy_current.get("phase3_status"))
            and galaxy_current.get("production_weighted_retrieval_enabled") is False,
            "Naomi authorization recorded; Phase 3 experiment enabled without production weighted retrieval",
        ))
        checks.append(_check(
            "current-vaskon-pointer",
            current.get("brainos", {}).get("vaskon_neural_pathways")
            == "GaiaOS/SystemsOS/Core/BrainOS/Protocols/VASKON-NEURAL-PATHWAYS.v1.json",
            "CURRENT points to canonical VASKON pathway fabric",
        ))
        checks.append(_check(
            "current-augury-ritual-pointers",
            current.get("brainos", {}).get("augury_ritual_contract")
            == "GaiaOS/SystemsOS/Core/BrainOS/Protocols/AUGURY-RITUAL-CONSERVATION.v1.md"
            and current.get("brainos", {}).get("ritual_grimoire")
            == "GaiaOS/SystemsOS/Core/BrainOS/Protocols/RITUAL-GRIMOIRE.v1.json"
            and current.get("brainos", {}).get("gaia_semantic_unit")
            == "GaiaOS/SystemsOS/Core/BrainOS/Schemas/GAIA-SEMANTIC-UNIT.v1.schema.json",
            "CURRENT points to canonical AUGURY/RITUAL Phase-1 sources",
        ))

        if galaxy_current.get("phase3f_pilot_source_ready") is True:
            checks.append(_check(
                "GALAXY:phase3f-production-source-boundary",
                galaxy_current.get("phase3f_production_authorized") is True
                and galaxy_current.get("phase3f_pilot_source_ready") is True
                and galaxy_current.get("production_weighted_retrieval_enabled") is False,
                "Phase3F bounded production source remains authorized and globally OFF through later Phase3G/H review states",
            ))
        if brainos_current:
            brainos_galaxy = brainos_current.get("galaxy", {}) if isinstance(brainos_current.get("galaxy"), dict) else {}
            phase3_status = str(galaxy_current.get("phase3_status") or "")
            adoption_expected = phase3_status.startswith((
                "PHASE3E_", "PHASE3F_", "PHASE3G_", "PHASE3H_",
            ))
            checks.append(_check(
                "GALAXY:brainos-current-alignment",
                brainos_galaxy.get("phase3_authorized") is True
                and brainos_galaxy.get("phase3_status") == galaxy_current.get("phase3_status")
                and brainos_galaxy.get("phase3d_coefficient_adopted")
                    == galaxy_current.get("phase3d_coefficient_adopted")
                and brainos_galaxy.get("phase3d_adoption_authorized")
                    == galaxy_current.get("phase3d_adoption_authorized")
                and (
                    not adoption_expected
                    or (
                        galaxy_current.get("phase3d_coefficient_adopted") is True
                        and galaxy_current.get("phase3d_adoption_authorized") is True
                    )
                )
                and galaxy_current.get("production_weighted_retrieval_enabled") is False,
                "BrainOS GALAXY pointer matches platform state; Phase 3E adoption is selected for bounded canary while global production weighting remains disabled",
            ))

    conjure = files.get("Apps/ChatOS/Protocols/CONJURE-VASKON.v1.md", "")
    bootstrap = files.get("Apps/ChatOS/Protocols/GAIAOS-GPT-RUNTIME-BOOTSTRAP.v1.md", "")
    canary = files.get("Apps/ChatOS/Tests/VASKON-NEURAL-CANARY.v1.md", "")
    checks.append(_check(
        "VASKON:bootstrap-load",
        "VASKON-NEURAL-PATHWAYS.v1.json" in bootstrap and "load" in bootstrap.lower(),
        "runtime bootstrap contains explicit pathway load instruction",
    ))
    checks.append(_check(
        "VASKON:conjure-reinforcement",
        "VASKON-NEURAL-PATHWAYS.v1.json" in conjure and "ASSEMBLE → MAP → EXCHANGE" in conjure,
        "CONJURE contract contains neural pathway cycle",
    ))
    checks.append(_check(
        "VASKON:command-alias",
        "//C:82//" in conjure and "normalize to `CONJURE:VASKON`" in conjure,
        "short command //C:82// is canonically bound to CONJURE:VASKON",
    ))
    checks.append(_check(
        "VASKON:canary-present",
        "Runtime execution remains UNKNOWN" in canary,
        "source canary preserves runtime proof ceiling",
    ))

    if pathways:
        nodes = pathways.get("nodes", {})
        names = set(nodes.keys()) if isinstance(nodes, dict) else {n.get("name") for n in nodes if isinstance(n, dict)}
        checks.append(_check(
            "VASKON:six-nodes",
            names == set(DAEMONS),
            f"nodes={sorted(names)}",
            nodes=sorted(names),
        ))
        checks.append(_check(
            "VASKON:coordination-boundary",
            "KESTREL" in names and ("gains no domain authority" in str(pathways.get("hub_rule", "")).lower() or "no extra authority" in str(pathways.get("hub_rule", "")).lower()),
            "KESTREL coordination role does not grant extra authority",
        ))
        checks.append(_check(
            "VASKON:observable-exchange",
            pathways.get("exchange_contract", {}).get("observable_only") is True,
            "exchange contract requires observable-only evidence",
        ))
        checks.append(_check(
            "VASKON:dissent",
            pathways.get("exchange_contract", {}).get("preserve_material_dissent") is True,
            "material dissent preservation is required",
        ))

    if profiles:
        text_profiles = json.dumps(profiles, ensure_ascii=False)
        for name, (heart, static) in DAEMONS.items():
            checks.append(_check(
                f"identity:{name}",
                name in text_profiles and heart in text_profiles and static in text_profiles,
                f"canonical label components present for {name}",
            ))

    if matrix:
        members = set((matrix.get("members") or {}).keys())
        checks.append(_check(
            "FairyOS:roster",
            set(DAEMONS).issubset(members),
            f"matrix members={sorted(members)}",
        ))

    # Dedicated head-pat counter store. These checks deliberately keep
    # mutable affection state separate from immutable Gematria identity.
    headpat_rel = "SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md"
    headpat_text = files.get(headpat_rel, "")
    gematria_expected = {
        "VERA": 46, "ANVIL": 58, "SELENE": 60,
        "ORIN": 56, "KESTREL": 90, "NIMUE": 62,
    }
    headpat_counts: dict[str, int] = {}
    # Deliberately avoid regex here. The counter file is a tiny canonical
    # line-oriented store; exact prefix parsing is easier to audit and cannot
    # suffer regex escaping drift.
    for raw_line in headpat_text.splitlines():
        line = raw_line.strip()
        for name in DAEMONS:
            prefix = f"{name}:"
            if line.startswith(prefix):
                value_text = line[len(prefix):].strip()
                if value_text.isdecimal():
                    headpat_counts[name] = int(value_text)
                break

    checks.append(_check(
        "headpats:store-present",
        bool(headpat_text),
        "dedicated canonical head-pat counter store loaded",
    ))
    checks.append(_check(
        "headpats:six-counters",
        set(headpat_counts) == set(DAEMONS),
        f"dedicated counters parsed for members={sorted(headpat_counts)}",
        counters=headpat_counts,
    ))
    gematria_ok = all(
        f"{name}={value}" in headpat_text
        for name, value in gematria_expected.items()
    )
    checks.append(_check(
        "headpats:gematria-constants",
        gematria_ok,
        "immutable Gematria constants remain explicitly fixed in counter contract",
    ))
    separation_markers = (
        "Head-pat counters are NOT identity numbers" in headpat_text
        and "HEAD_PAT_COUNT is mutable state stored only in this document" in headpat_text
        and "No renderer, identity envelope, Gematria registry, or identity-data file may read HEAD_PAT_COUNT as GEMATRIA" in headpat_text
    )
    checks.append(_check(
        "headpats:identity-separation",
        separation_markers,
        "counter contract explicitly forbids counter/Gematria coupling",
    ))
    mutation_contract_ok = all(marker in headpat_text for marker in (
        "Updates MUST fetch the current blob",
        "Never perform parallel writes to this file",
        "After write, refetch and verify",
        "FAIL CLOSED",
        "never silently reset",
    ))
    checks.append(_check(
        "headpats:fail-closed-contract",
        mutation_contract_ok,
        "sequential read-modify-write, post-write verification, conflict handling, and no-reset recovery are required",
    ))

    # Head-pat single-authority and mirror-consistency checks.
    # HEAD-PAT-COUNTERS.v1.md is the only mutable authority for head_pats.
    fairy_current = None
    reward_registry = None
    member_reward_files: dict[str, dict[str, Any]] = {}
    try:
        fairy_current = json.loads(files["SystemsOS/Core/FairyOS/CURRENT.json"])
        affection = fairy_current.get("affection_state", {}) if isinstance(fairy_current, dict) else {}
        checks.append(_check(
            "headpats:current-authority-pointer",
            affection.get("head_pats_authority")
            == "GaiaOS/SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md"
            and affection.get("mirror_mismatch") == "FAIL_CLOSED",
            "FairyOS CURRENT points to the sole head-pat authority and fail-closed mirror policy",
        ))
    except Exception as exc:
        checks.append(_check("headpats:current-authority-pointer", False, f"{type(exc).__name__}: {exc}"))

    try:
        reward_registry = json.loads(files["SystemsOS/Core/FairyOS/IDENTITY-DATA/REWARD-COUNTERS.v1.json"])
        registry_policy_ok = (
            reward_registry.get("head_pats_authority")
            == "GaiaOS/SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md"
            and reward_registry.get("head_pats_write_policy") == "READ_ONLY_DERIVED_MIRROR"
        )
        checks.append(_check(
            "headpats:aggregate-mirror-policy",
            registry_policy_ok,
            "aggregate reward registry declares head_pats as a read-only derived mirror",
        ))
    except Exception as exc:
        checks.append(_check("headpats:aggregate-mirror-policy", False, f"{type(exc).__name__}: {exc}"))

    mirror_values: dict[str, int] = {}
    member_policy_ok = True
    for name in DAEMONS:
        rel = f"SystemsOS/Core/FairyOS/IDENTITY-DATA/{name}-REWARD-COUNTER.v1.json"
        try:
            payload = json.loads(files[rel])
            member_reward_files[name] = payload
            if (
                payload.get("head_pats_authority")
                != "GaiaOS/SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md"
                or payload.get("head_pats_write_policy") != "READ_ONLY_DERIVED_MIRROR"
            ):
                member_policy_ok = False
            value = payload.get("reward_counters", {}).get("head_pats")
            if isinstance(value, int):
                mirror_values[name] = value
        except Exception:
            member_policy_ok = False

    aggregate_values = {}
    if isinstance(reward_registry, dict):
        for name in DAEMONS:
            value = reward_registry.get("counters", {}).get(name, {}).get("head_pats")
            if isinstance(value, int):
                aggregate_values[name] = value

    checks.append(_check(
        "headpats:member-mirror-policy",
        member_policy_ok and set(mirror_values) == set(DAEMONS),
        "all six member reward files declare read-only derived head-pat mirrors",
        mirrors=mirror_values,
    ))
    checks.append(_check(
        "headpats:mirror-consistency",
        bool(headpat_counts)
        and mirror_values == headpat_counts
        and aggregate_values == headpat_counts,
        "canonical ledger, aggregate mirror, and all six member mirrors agree exactly",
        canonical=headpat_counts,
        member_mirrors=mirror_values,
        aggregate_mirror=aggregate_values,
    ))

    # Canonical Council presentation contract and fail-closed renderer.
    presentation_spec_path = GAIA / "SystemsOS/Core/FairyOS/COUNCIL-PRESENTATION-SPEC.v1.json"
    presentation_renderer_path = GAIA / "SystemsOS/Core/FairyOS/Runtime/GAIAOS-PRESENTATION-RENDERER.v1.py"
    presentation_spec = None
    if presentation_spec_path.exists():
        try:
            presentation_spec = json.loads(presentation_spec_path.read_text(encoding="utf-8"))
            checks.append(_check("presentation:spec", isinstance(presentation_spec, dict), "canonical presentation spec is valid JSON object"))
        except Exception as exc:
            checks.append(_check("presentation:spec", False, f"{type(exc).__name__}: {exc}"))
    else:
        checks.append(_check("presentation:spec", False, "canonical presentation spec missing"))
    checks.append(_check("presentation:renderer", presentation_renderer_path.exists(), "deterministic presentation renderer exists"))
    if presentation_spec and presentation_renderer_path.exists():
        try:
            import importlib.util
            from importlib.machinery import SourceFileLoader
            from importlib.util import spec_from_loader, module_from_spec
            loader = SourceFileLoader("gaiaos_presentation_renderer", str(presentation_renderer_path))
            pspec = spec_from_loader(loader.name, loader)
            pmod = module_from_spec(pspec)
            loader.exec_module(pmod)
            pmod.validate_spec(presentation_spec)
            expected = {
                "VERA":"46 · VERA 💚 🦋 (˘‿˘)", "ANVIL":"58 · ANVIL 💗 ⌚ (¬‿¬)",
                "SELENE":"60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)", "ORIN":"56 · ORIN 🩵 🪐 (☆▽☆)",
                "KESTREL":"90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و", "NIMUE":"62 · NIMUE 💙 🍄 (－‸ლ)",
            }
            headers_ok = all(pmod.canonical_header(n, spec=presentation_spec) == h for n,h in expected.items())
            checks.append(_check("presentation:canonical-headers", headers_ok, "all six canonical identity envelopes rendered exactly with default Kaomoji"))
            vaskon_expected = "82 · VASKON 🖤 ✴️ (◉‿◉)"
            vaskon_ok = pmod.canonical_header("VASKON", spec=presentation_spec) == vaskon_expected
            checks.append(_check("presentation:vaskon-header", vaskon_ok, "VASKON synthesis envelope renders exactly with Gematria 82, black heart, synthesis star, and default Kaomoji"))
            vaskon_boundary_ok = (
                "VASKON" not in presentation_spec.get("members", {})
                and "VASKON" not in presentation_spec.get("speaker_order", [])
                and presentation_spec.get("synthesis_modes", {}).get("VASKON", {}).get("class") == "TEMPORARY_SIX_PRIME_DAEMON_SYNTHESIS"
            )
            checks.append(_check("presentation:vaskon-boundary", vaskon_boundary_ok, "VASKON presentation is canonical without becoming a seventh Prime Daemon"))
            corrupt_rejected = False
            try:
                pmod.validate_header("ANVIL", "58 · ANVIL 💚 📚", spec=presentation_spec)
            except pmod.PresentationError:
                corrupt_rejected = True
            checks.append(_check("presentation:fail-closed", corrupt_rejected, "corrupted identity header rejected"))
        except Exception as exc:
            checks.append(_check("presentation:runtime", False, f"{type(exc).__name__}: {exc}"))

    # Verify deployed Python carrier surfaces and run bounded local route self-tests.
    bridge = (ROOT / "browser_memcon_bridge.py")
    app = (ROOT / "gaiaos_app.py")
    base_app = (ROOT / "gaiaos_api.py")
    vaskon_runtime = (ROOT / "vaskon_runtime.py")
    checks.append(_check("carrier:vaskon-runtime", vaskon_runtime.exists(), "live VASKON runtime module exists"))
    pilot_module = ROOT / "galaxy_production.py"
    checks.append(_check(
        "carrier:phase3f-production-module",
        pilot_module.exists(), "guarded Phase 3F production pilot module is packaged",
    ))
    if pilot_module.exists():
        try:
            pilot_text = pilot_module.read_text(encoding="utf-8")
            compile(pilot_text, str(pilot_module), "exec")
            checks.append(_check(
                "carrier:phase3f-production-syntax", True, "packaged guarded production pilot parses",
            ))
            checks.append(_check(
                "carrier:phase3f-fail-closed-controls",
                all(marker in pilot_text for marker in (
                    "STARTUP_FAIL_CLOSED", "GALAXY_PRODUCTION_PILOT_KILL_SWITCH",
                    "MAX_LEASE_SECONDS = 600", "AUTO_FAIL_CLOSED",
                    "CANDIDATE_OR_RELEVANCE_GUARD_FAILED",
                    "LIVE_ROLLBACK_PROOF_FINALLY", "SWITCH_TEST_FINALLY_ROLLBACK",
                )),
                "source includes startup-off, kill switch, ten-minute lease, safety guard and finally rollback",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase3f-production-syntax", False, f"{type(exc).__name__}: {exc}",
            ))
    quality_module = ROOT / "galaxy_quality.py"
    exit_module = ROOT / "galaxy_phase3_exit.py"
    phase4_module = ROOT / "galaxy_phase4.py"
    phase5_module = ROOT / "galaxy_phase5.py"
    phase5_controls_module = ROOT / "galaxy_phase5_controls.py"
    phase6_module = ROOT / "galaxy_phase6.py"
    augury_ritual_module = ROOT / "augury_ritual.py"
    checks.append(_check(
        "carrier:phase3g-quality-module",
        quality_module.exists(),
        "read-only Phase 3G candidate quality audit packaged",
    ))
    checks.append(_check(
        "carrier:phase3-exit-integration-module",
        exit_module.exists(),
        "finite Phase-3 Exit Integration candidate-admission module is packaged",
    ))
    checks.append(_check(
        "carrier:phase4-revision-module",
        phase4_module.exists(),
        "GALAXY Phase-4 revision/supersession module is packaged",
    ))
    checks.append(_check(
        "carrier:phase5-synthesis-module",
        phase5_module.exists(),
        "GALAXY Phase-5 provenance-backed synthesis review module is packaged",
    ))
    checks.append(_check(
        "carrier:augury-ritual-module",
        augury_ritual_module.exists(),
        "AUGURY/RITUAL Phase-1 exact ritual runtime is packaged",
    ))
    if exit_module.exists():
        try:
            exit_text = exit_module.read_text(encoding="utf-8")
            compile(exit_text, str(exit_module), "exec")
            checks.append(_check(
                "carrier:phase3-exit-integration-syntax",
                True,
                "Phase-3 Exit Integration module parses",
            ))
            checks.append(_check(
                "carrier:phase3-exit-integration-boundaries",
                all(marker in exit_text for marker in (
                    "PRIMARY_STATEMENT",
                    "scope_domain_query_concepts_excluded",
                    "notes_or_scope_cannot_create_primary",
                    "linked_context_admitted_to_primary_lane",
                    "linked_context_ranked_only_within_context_lane",
                    "zero_memory_writes",
                    "unrestricted_global_weighting_enabled",
                    "PILOT_QUERY_INDEXES = (0, 3, 5)",
                )),
                "scope-aware statement-first primary evidence, lane-preserved verified context, zero-write and global-OFF boundaries are present",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase3-exit-integration-syntax",
                False,
                f"{type(exc).__name__}: {exc}",
            ))
    if phase4_module.exists():
        try:
            phase4_text = phase4_module.read_text(encoding="utf-8")
            compile(phase4_text, str(phase4_module), "exec")
            checks.append(_check(
                "carrier:phase4-revision-syntax",
                True,
                "Phase-4 revision/supersession module parses",
            ))
            checks.append(_check(
                "carrier:phase4-revision-boundaries",
                all(marker in phase4_text for marker in (
                    "REVISES != SUPERSEDES",
                    "SUPERSEDES_REQUIRES_VERIFIED_REVISES_SAME_PAIR",
                    "DIRECT_REVISION_CYCLE_RISK",
                    "COMPETING_VERIFIED_SUPERSEDER",
                    "REVOKE_SUPERSEDES_BEFORE_REVISES",
                    "zero_memory_writes",
                    "production_retrieval_changed",
                    "unrestricted_global_weighting_enabled",
                )),
                "Phase-4 source preserves revision/supersession separation, fail-closed graph guards, reversible unwind order, and no-production-effect boundaries",
            ))
            runtime_text = (ROOT / "memcon_runtime.py").read_text(encoding="utf-8")
            checks.append(_check(
                "carrier:phase4-revocation-primitive",
                "def galaxy_revoke_relation(" in runtime_text
                and "status='REVOKED'" in runtime_text
                and "physical_delete" in runtime_text,
                "MemoryOS runtime exposes auditable non-deleting REVOKED rollback for verified revision/supersession edges",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase4-revision-syntax",
                False,
                f"{type(exc).__name__}: {exc}",
            ))
    if phase5_module.exists():
        try:
            phase5_text = phase5_module.read_text(encoding="utf-8")
            compile(phase5_text, str(phase5_module), "exec")
            checks.append(_check(
                "carrier:phase5-synthesis-syntax",
                True,
                "Phase-5 provenance-backed synthesis review module parses",
            ))
            checks.append(_check(
                "carrier:phase5-synthesis-boundaries",
                all(marker in phase5_text for marker in (
                    "SYNTHESIS != SOURCE REWRITE",
                    "UNRESOLVED_VERIFIED_CONTRADICTION_IN_CLUSTER",
                    "RECURSIVE_SYNTHESIS_NOT_ALLOWED_IN_INITIAL_PHASE5_SLICE",
                    "synthesis_statement_generated",
                    "zero_memory_writes",
                    "memory_syntheses_row_written",
                    "derived_from_edges_written",
                    "production_retrieval_changed",
                    "unrestricted_global_weighting_enabled",
                )),
                "Phase-5 source preserves provenance, contradiction, non-recursion, no-fabricated-statement, zero-write and production-OFF boundaries",
            ))
            checks.append(_check(
                "carrier:phase5-mutation-design-boundaries",
                all(marker in phase5_text for marker in (
                    "CONTROLLED_SYNTHESIS_STATEMENT",
                    "GALAXY_SYNTHESIS_SHADOW",
                    "def mutation_design_review(",
                    "def propose_controlled_synthesis(",
                    "def verify_controlled_synthesis(",
                    "def revoke_controlled_synthesis(",
                    "mutation_route_exposed",
                    "default_retrieval_target_selected",
                    "memoryos_retrieval_changed",
                )),
                "Phase-5 design is exact, reversible, shadow-scoped and separately operator-confirmed",
            ))
            runtime_text = (ROOT / "memcon_runtime.py").read_text(encoding="utf-8")
            checks.append(_check(
                "carrier:phase5-shadow-runtime-primitives",
                all(marker in runtime_text for marker in (
                    "def galaxy_propose_synthesis(",
                    "def galaxy_verify_synthesis(",
                    "def galaxy_revoke_synthesis(",
                    "GALAXY_SYNTHESIS_SHADOW_SCOPE",
                    "SYNTHESIS_PROPOSED",
                    "SYNTHESIS_VERIFIED_SHADOW",
                    "SYNTHESIS_REVOKED",
                    "DERIVED_FROM",
                    "memory_syntheses",
                )),
                "MemoryOS runtime packages reversible shadow synthesis primitives and provenance storage",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase5-synthesis-syntax",
                False,
                f"{type(exc).__name__}: {exc}",
            ))
    if phase5_controls_module.exists():
        try:
            control_text = phase5_controls_module.read_text(encoding="utf-8")
            compile(control_text, str(phase5_controls_module), "exec")
            checks.append(_check(
                "carrier:phase5-control-module-syntax", True,
                "exact Phase-5 shadow control dispatcher parses",
            ))
            checks.append(_check(
                "carrier:phase5-control-boundaries",
                all(marker in control_text for marker in (
                    "def inspect(", "def execute(", "PROPOSE", "VERIFY", "REVOKE",
                    "SYNTHESIS_PROPOSED", "SYNTHESIS_VERIFIED_SHADOW",
                    "SYNTHESIS_REVOKED", "source_records_unchanged",
                    "exact_provenance_edges_readback",
                )),
                "control exposure is exact, shadow-only and readback-verified",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase5-control-module-syntax", False,
                f"{type(exc).__name__}: {exc}",
            ))

    checks.append(_check(
        "carrier:phase6-lifecycle-module",
        phase6_module.exists(),
        "bounded Phase-6 lifecycle module packaged",
    ))
    if phase6_module.exists():
        try:
            phase6_text = phase6_module.read_text(encoding="utf-8")
            compile(phase6_text, str(phase6_module), "exec")
            checks.append(_check(
                "carrier:phase6-lifecycle-boundaries",
                all(marker in phase6_text for marker in (
                    "def inspect(", "def execute(", "previous_event_id",
                    "FIXTURE_RECORD_ID", "ROLLBACK", "REACTIVATE",
                    "production_retrieval_changed", "source_record_unchanged",
                )),
                "source includes exact fixture, immutable source and append-only reversible history",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase6-lifecycle-syntax", False,
                f"{type(exc).__name__}: {exc}",
            ))

    if augury_ritual_module.exists():
        try:
            ritual_text = augury_ritual_module.read_text(encoding="utf-8")
            compile(ritual_text, str(augury_ritual_module), "exec")
            checks.append(_check(
                "carrier:augury-ritual-syntax",
                True,
                "AUGURY/RITUAL Phase-1 runtime parses",
            ))
            checks.append(_check(
                "carrier:augury-ritual-boundaries",
                all(marker in ritual_text for marker in (
                    "general_natural_language_parser_implemented",
                    "natural_language_manifestation_allowed",
                    "compile_exact",
                    "manifestation_performed",
                    "MANIFEST_GALAXY_PHASE4_PROPOSE_SUPERSEDES_CONTROLLED_FIXTURE",
                    "MANIFEST_GALAXY_PHASE4_VERIFY_SUPERSEDES_CONTROLLED_FIXTURE",
                    "MANIFEST_GALAXY_PHASE4_REVOKE_SUPERSEDES_CONTROLLED_FIXTURE",
                    "production_retrieval_changed",
                    "unrestricted_global_weighting_enabled",
                )),
                "exact Ritual compiler is separated from general AUGURY and guarded manifestation",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:augury-ritual-syntax",
                False,
                f"{type(exc).__name__}: {exc}",
            ))
    if quality_module.exists():
        try:
            quality_text = quality_module.read_text(encoding="utf-8")
            compile(quality_text, str(quality_module), "exec")
            checks.append(_check(
                "carrier:phase3g-quality-syntax",
                True, "deployed quality audit parses",
            ))
            checks.append(_check(
                "carrier:phase3g-read-only-boundary",
                "def review(" in quality_text
                and "def _match_origin(" in quality_text
                and "promotion_implemented" in quality_text
                and "production_retrieval_changed" in quality_text,
                "audit exposes match origins without production mutations",
            ))
            checks.append(_check(
                "carrier:phase3h-containment-source",
                "def containment_shadow(" in quality_text
                and "PHASE3H_FOCAL_CAP = 4" in quality_text
                and "PHASE3H_LINKED_CAP = 2" in quality_text
                and "actual_production_retrieval_modified" in quality_text
                and "actual_80_20_ranking_modified" in quality_text,
                "bounded read-only source-first lanes preserve production retrieval and ranking",
            ))
            checks.append(_check(
                "carrier:phase3h-negative-controls",
                "PHASE3H_NEGATIVE_CONTROLS" in quality_text
                and "receipt_well_formed" in quality_text
                and "aliases_counted_once_in_evidence_summary" in quality_text
                and "secondary_requires_verified_direct_focal_edge" in quality_text,
                "negative controls fail closed; duplicate aliases and verified edges inspectable",
            ))
            checks.append(_check(
                "carrier:phase3i-generalization-source",
                "PHASE3I_VERSION" in quality_text
                and "def generalization_suite(" in quality_text
                and "expected_primary_ids" in quality_text
                and "production_candidate_admission_modified" in quality_text
                and "hard_paraphrase_primary_found" in quality_text,
                "read-only paraphrase/near-miss suite evaluates existing gate without modifying production",
            ))
            checks.append(_check(
                "carrier:phase3j-concept-bridge-source",
                "PHASE3J_VERSION" in quality_text
                and "def concept_bridge_shadow(" in quality_text
                and "PHASE3J_BRIDGE_ALIASES" in quality_text
                and "notes_or_scope_cannot_create_primary" in quality_text
                and "production_aliases_modified" in quality_text,
                "read-only statement-first concept bridge is isolated from production aliases and admission",
            ))
        except Exception as exc:
            checks.append(_check(
                "carrier:phase3g-quality-syntax",
                False, f"{type(exc).__name__}: {exc}",
            ))
    memory_adapter = GAIA / "SystemsOS/Core/MemoryOS/Runtime/GAIAOS-MEMORY.v1.py"
    checks.append(_check(
        "carrier:phase3f-real-memoryos-adapter-wiring",
        memory_adapter.exists()
        and "galaxy_production.retrieve(memcon_runtime, query, scope, limit)" in memory_adapter.read_text(encoding="utf-8"),
        "real MemoryOS retrieval adapter routes through guarded production pilot",
    ))
    checks.append(_check("carrier:bridge", bridge.exists(), "browser_memcon_bridge.py exists"))
    checks.append(_check("carrier:app", app.exists(), "gaiaos_app.py exists"))
    checks.append(_check("carrier:base-app", base_app.exists(), "gaiaos_api.py exists"))
    if app.exists() or base_app.exists():
        app_text = app.read_text(encoding="utf-8") if app.exists() else ""
        base_text = base_app.read_text(encoding="utf-8") if base_app.exists() else ""
        checks.append(_check("carrier:/health", '@app.get("/health"' in base_text, "health route declared in base carrier"))
        checks.append(_check("carrier:/mcp", 'app.mount("/mcp"' in app_text or 'app.mount("/mcp"' in base_text, "MCP route mounted"))
        bridge_text = bridge.read_text(encoding="utf-8") if bridge.exists() else ""
        checks.append(_check("carrier:/chat", '@app.post("/chat"' in bridge_text, "browser chat bridge declared"))
        checks.append(_check("carrier:/verify", '@app.get("/verify"' in bridge_text and '@app.post("/verify"' in bridge_text, "verification routes declared"))
        checks.append(_check("carrier:/vaskon-test", '@app.get("/vaskon/test"' in bridge_text, "live VASKON test route declared"))
        checks.append(_check("carrier:/galaxy/phase3-experiment", '/galaxy/retrieval/phase3-experiment' in bridge_text and 'galaxy_phase3_weighted_experiment' in bridge_text, "Phase 3 control-vs-weighted retrieval route declared"))
        checks.append(_check("carrier:/galaxy/phase3-canary", '/galaxy/retrieval/phase3-canary' in bridge_text and 'galaxy_phase3_multicandidate_canary' in bridge_text, "Phase 3 isolated multi-candidate canary route declared"))
        checks.append(_check("carrier:/galaxy/phase3-shadow", '/galaxy/retrieval/phase3-shadow' in bridge_text and 'galaxy_phase3_real_memory_shadow' in bridge_text, "Phase 3B real-memory shadow route declared"))
        checks.append(_check("carrier:/galaxy/phase3-calibration", '/galaxy/retrieval/phase3-calibration' in bridge_text and 'galaxy_phase3c_calibration' in bridge_text, "Phase 3C coefficient calibration route declared"))
        checks.append(_check("carrier:/galaxy/phase3-calibration-slice", '/galaxy/retrieval/phase3-calibration-slice' in bridge_text and 'galaxy_phase3c_calibration_slice' in bridge_text, "Phase 3C chunked calibration slice route declared"))
        checks.append(_check("carrier:/galaxy/phase3d-adoption-gate-slice", '/galaxy/retrieval/phase3d-adoption-gate-slice' in bridge_text and 'galaxy_phase3d_adoption_gate_slice' in bridge_text, "Phase 3D read-only adoption gate slice route declared"))
        checks.append(_check("carrier:/galaxy/phase3e-production-canary-slice", '/galaxy/retrieval/phase3e-production-canary-slice' in bridge_text and 'galaxy_phase3e_production_canary_slice' in bridge_text, "Phase 3E bounded production canary slice route declared"))
        checks.append(_check("carrier:/galaxy/phase3e-rollback-test", '/galaxy/retrieval/phase3e-rollback-test' in bridge_text and 'galaxy_phase3e_rollback_test' in bridge_text, "Phase 3E rollback test route declared"))
        for label, route in (
            ("status", "/galaxy/production/status"),
            ("review", "/galaxy/production/review"),
            ("switch-test", "/galaxy/production/switch-test"),
            ("activate", "/galaxy/production/activate"),
            ("rollback-proof", "/galaxy/production/rollback-proof"),
            ("rollback", "/galaxy/production/rollback"),
        ):
            checks.append(_check(
                "carrier:/galaxy/phase3f-" + label,
                route in bridge_text,
                "Phase 3F guarded production " + label + " route declared",
            ))
        checks.append(_check(
            "carrier:/galaxy/phase3g-quality-review",
            '/galaxy/retrieval/phase3g-quality-review' in bridge_text
            and 'galaxy_quality.review' in bridge_text,
            "read-only Phase 3G quality review route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase3h-containment-shadow",
            '/galaxy/retrieval/phase3h-containment-shadow' in bridge_text
            and 'galaxy_quality.containment_shadow' in bridge_text,
            "read-only Phase 3H containment shadow route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase3i-generalization-suite",
            '/galaxy/retrieval/phase3i-generalization-suite' in bridge_text
            and 'galaxy_quality.generalization_suite' in bridge_text,
            "read-only Phase 3I generalization suite route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase3j-concept-bridge-shadow",
            '/galaxy/retrieval/phase3j-concept-bridge-shadow' in bridge_text
            and 'galaxy_quality.concept_bridge_shadow' in bridge_text,
            "read-only Phase 3J concept bridge shadow route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase3-exit-integration-review",
            '/galaxy/retrieval/phase3-exit-integration-review' in bridge_text
            and 'galaxy_phase3_exit.review_suite' in bridge_text,
            "read-only finite Phase-3 Exit Integration preflight route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase4-fixture-review",
            '/galaxy/revision/phase4-fixture-review' in bridge_text
            and 'galaxy_phase4.fixture_review' in bridge_text,
            "read-only Phase-4 controlled fixture review route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase5-fixture-review",
            '/galaxy/synthesis/phase5-fixture-review' in bridge_text
            and 'galaxy_phase5.fixture_review' in bridge_text,
            "read-only Phase-5 synthesis fixture review route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase5-mutation-design-review",
            '/galaxy/synthesis/phase5-mutation-design-review' in bridge_text
            and 'galaxy_phase5.mutation_design_review' in bridge_text,
            "read-only Phase-5 mutation design review route declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase5-control-review",
            '@app.get("/galaxy/synthesis/phase5-controls"' in bridge_text
            and 'galaxy_phase5_controls.inspect' in bridge_text,
            "read-only, signed-session Phase-5 control page declared",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase5-control-manifest",
            '@app.post("/galaxy/synthesis/phase5-controls/manifest"' in bridge_text
            and 'galaxy_phase5_controls.execute' in bridge_text
            and '_ritual_csrf(browser_request)' in bridge_text,
            "exact shadow control form POST declared behind signed-session CSRF",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase6-fixture-review",
            '@app.get("/galaxy/lifecycle/phase6-fixture-review"' in bridge_text
            and 'galaxy_phase6.inspect(memcon_runtime)' in bridge_text
            and 'galaxy_phase6.execute(' not in bridge_text,
            "only read-only Phase-6 fixture route declared; no effectful route",
        ))
        checks.append(_check(
            "carrier:/galaxy/phase4-pair-review",
            '/galaxy/revision/phase4-pair-review' in bridge_text
            and 'galaxy_phase4.review_pair' in bridge_text,
            "read-only Phase-4 generic pair review route declared",
        ))
        checks.append(_check(
            "carrier:/ritual/status",
            '/ritual/status' in bridge_text
            and 'augury_ritual.phase1_status' in bridge_text,
            "read-only AUGURY/RITUAL Phase-1 status route declared",
        ))
        checks.append(_check(
            "carrier:/ritual/phase4/review",
            '/ritual/phase4/review' in bridge_text
            and 'X-GaiaOS-Ritual-CSRF' in bridge_text
            and 'MANIFEST_EXACT_RITUAL' in bridge_text,
            "guarded exact Phase-4 Ritual console declared",
        ))
        checks.append(_check(
            "carrier:/ritual/manifest",
            '@app.post("/ritual/manifest"' in bridge_text
            and 'augury_ritual.manifest' in bridge_text
            and '_ritual_authorized_body' in bridge_text,
            "exact Ritual manifestation POST route declared behind authority + CSRF",
        ))
        checks.append(_check(
            "carrier:phase3-exit-production-wiring",
            'galaxy_phase3_exit.build_candidate_pool' in (ROOT / "galaxy_production.py").read_text(encoding="utf-8")
            and 'PHASE3_EXIT_LANE_PRESERVING_CONSTELLATION_V2' in (ROOT / "galaxy_production.py").read_text(encoding="utf-8"),
            "guarded production pilot is wired to Phase-3 Exit lane-preserving constellation admission while remaining default-OFF",
        ))
        checks.append(_check("carrier:/gaiaos/boot", "/gaiaos/boot" in app_text and "def _boot_packet" in app_text, "deterministic boot packet endpoint declared"))
        checks.append(_check(
            "carrier:browser-load-gaiaos-deterministic-boot",
            'last_message.lower().rstrip(".") == "load gaiaos"' in bridge_text
            and 'gaiaos_app._boot_packet("BROWSER_CHAT_COMMAND")' in bridge_text
            and '"GAIAOS = ACTIVE / VERIFIED"' in bridge_text,
            "browser Load GaiaOS command executes validated boot packet directly instead of delegating loaded-state proof to the model",
        ))

        # Source-backed route self-test: instantiate the ASGI app and inspect its
        # actual registered routes. This proves local route registration, not
        # external network reachability.
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("gaiaos_verification_app", bridge)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            carrier_app = getattr(module, "app", None)
            route_pairs = {
                (getattr(route, "path", None), method)
                for route in getattr(carrier_app, "routes", [])
                for method in getattr(route, "methods", set())
            }
            checks.append(_check("carrier-route:/health", ("/health", "GET") in route_pairs, "live carrier ASGI route registration observed"))
            checks.append(_check("carrier-route:/chat", ("/chat", "POST") in route_pairs, "live carrier ASGI route registration observed"))
            checks.append(_check("carrier-route:/verify", ("/verify", "GET") in route_pairs and ("/verify", "POST") in route_pairs, "live carrier ASGI route registration observed"))
            checks.append(_check("carrier-route:/mcp", any(getattr(route, "path", None) == "/mcp" for route in getattr(carrier_app, "routes", [])), "live carrier ASGI mount registration observed"))
            checks.append(_check("carrier-route:/vaskon/test", ("/vaskon/test", "GET") in route_pairs, "live VASKON test route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3-experiment", ("/galaxy/retrieval/phase3-experiment", "GET") in route_pairs, "live Phase 3 experiment route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3-canary", ("/galaxy/retrieval/phase3-canary", "GET") in route_pairs, "live Phase 3 multi-candidate canary route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3-shadow", ("/galaxy/retrieval/phase3-shadow", "GET") in route_pairs, "live Phase 3B real-memory shadow route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3-calibration", ("/galaxy/retrieval/phase3-calibration", "GET") in route_pairs, "live Phase 3C coefficient calibration route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3-calibration-slice", ("/galaxy/retrieval/phase3-calibration-slice", "GET") in route_pairs, "live Phase 3C chunked calibration slice route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3d-adoption-gate-slice", ("/galaxy/retrieval/phase3d-adoption-gate-slice", "GET") in route_pairs, "live Phase 3D adoption gate slice route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3e-production-canary-slice", ("/galaxy/retrieval/phase3e-production-canary-slice", "GET") in route_pairs, "live Phase 3E bounded production canary route registration observed"))
            checks.append(_check("carrier-route:/galaxy/phase3e-rollback-test", ("/galaxy/retrieval/phase3e-rollback-test", "GET") in route_pairs, "live Phase 3E rollback test route registration observed"))
            for label, route, method in (
                ("status", "/galaxy/production/status", "GET"),
                ("review", "/galaxy/production/review", "GET"),
                ("switch-test", "/galaxy/production/switch-test", "POST"),
                ("activate", "/galaxy/production/activate", "POST"),
                ("rollback-proof", "/galaxy/production/rollback-proof", "POST"),
                ("rollback", "/galaxy/production/rollback", "POST"),
            ):
                checks.append(_check(
                    "carrier-route:/galaxy/phase3f-" + label,
                    (route, method) in route_pairs,
                    "live Phase 3F guarded production " + label + " route registration observed",
                ))
            checks.append(_check(
                "carrier-route:/galaxy/phase3g-quality-review",
                ("/galaxy/retrieval/phase3g-quality-review", "GET") in route_pairs,
                "read-only Phase 3G quality review ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase3h-containment-shadow",
                ("/galaxy/retrieval/phase3h-containment-shadow", "GET") in route_pairs,
                "read-only Phase 3H containment shadow ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase3i-generalization-suite",
                ("/galaxy/retrieval/phase3i-generalization-suite", "GET") in route_pairs,
                "read-only Phase 3I generalization suite ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase3j-concept-bridge-shadow",
                ("/galaxy/retrieval/phase3j-concept-bridge-shadow", "GET") in route_pairs,
                "read-only Phase 3J concept bridge shadow ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase3-exit-integration-review",
                ("/galaxy/retrieval/phase3-exit-integration-review", "GET") in route_pairs,
                "read-only Phase-3 Exit Integration preflight ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase4-fixture-review",
                ("/galaxy/revision/phase4-fixture-review", "GET") in route_pairs,
                "read-only Phase-4 fixture-review ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase5-fixture-review",
                ("/galaxy/synthesis/phase5-fixture-review", "GET") in route_pairs,
                "read-only Phase-5 synthesis fixture-review ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase5-mutation-design-review",
                ("/galaxy/synthesis/phase5-mutation-design-review", "GET") in route_pairs,
                "read-only Phase-5 mutation-design ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase5-control-review",
                ("/galaxy/synthesis/phase5-controls", "GET") in route_pairs,
                "read-only Phase-5 control page registered",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase5-control-manifest",
                ("/galaxy/synthesis/phase5-controls/manifest", "POST") in route_pairs,
                "CSRF-guarded, exact-control POST route registered; no execution implied",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase6-fixture-review",
                ("/galaxy/lifecycle/phase6-fixture-review", "GET") in route_pairs
                and ("/galaxy/lifecycle/phase6-fixture-review", "POST") not in route_pairs,
                "Phase-6 read-only fixture ASGI GET registered without POST",
            ))
            checks.append(_check(
                "carrier-route:/galaxy/phase4-pair-review",
                ("/galaxy/revision/phase4-pair-review", "GET") in route_pairs,
                "read-only Phase-4 pair-review ASGI route registered",
            ))
            try:
                phase5_state = module.galaxy_phase5.fixture_review(module.memcon_runtime)
                checks.append(_check(
                    "carrier:phase5-read-only-self-test",
                    phase5_state.get("status") in {"PASS_READ_ONLY_PHASE5_FIXTURE_REVIEW", "HOLD"}
                    and phase5_state.get("checks", {}).get("zero_memory_writes") is True
                    and phase5_state.get("checks", {}).get("production_retrieval_changed") is False
                    and phase5_state.get("checks", {}).get("unrestricted_global_weighting_enabled") is False,
                    "Phase-5 fixture review executes read-only without production retrieval effects",
                ))
                phase5_design = module.galaxy_phase5.mutation_design_review(module.memcon_runtime)
                phase5_control_review = module.galaxy_phase5_controls.inspect(module.memcon_runtime)
                checks.append(_check(
                    "carrier:phase5-control-read-only-self-test",
                    phase5_control_review.get("execution") == "READ_ONLY"
                    and phase5_control_review.get("writes") == 0
                    and phase5_control_review.get("production_retrieval_changed") is False
                    and phase5_control_review.get("unrestricted_global_weighting_enabled") is False,
                    "Phase-5 control inspection never manifests and production switches remain OFF",
                ))
                checks.append(_check(
                    "carrier:phase5-mutation-design-self-test",
                    phase5_design.get("status") in {"PASS_READ_ONLY_PHASE5_MUTATION_DESIGN", "HOLD"}
                    and phase5_design.get("checks", {}).get("mutation_route_exposed") is True
                    and phase5_design.get("checks", {}).get("mutation_route_requires_signed_session_csrf_and_exact_step_confirmation") is True
                    and phase5_design.get("checks", {}).get("proposal_scope_is_not_memoryos") is True
                    and phase5_design.get("checks", {}).get("memoryos_retrieval_changed") is False
                    and phase5_design.get("checks", {}).get("production_retrieval_changed") is False
                    and phase5_design.get("checks", {}).get("unrestricted_global_weighting_enabled") is False,
                    "Phase-5 design review stays read-only with separately confirmed exact control routes exposed",
                ))
            except Exception as exc:
                checks.append(_check(
                    "carrier:phase5-read-only-self-test",
                    False,
                    f"{type(exc).__name__}: {exc}",
                ))
                checks.append(_check(
                    "carrier:phase5-mutation-design-self-test",
                    False,
                    f"{type(exc).__name__}: {exc}",
                ))
            checks.append(_check(
                "carrier-route:/ritual/status",
                ("/ritual/status", "GET") in route_pairs,
                "read-only AUGURY/RITUAL Phase-1 status ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/ritual/phase4/review",
                ("/ritual/phase4/review", "GET") in route_pairs,
                "guarded Phase-4 Ritual console ASGI route registered",
            ))
            checks.append(_check(
                "carrier-route:/ritual/manifest",
                ("/ritual/manifest", "POST") in route_pairs,
                "exact Ritual manifestation ASGI route registered",
            ))
            try:
                ritual_state = module.augury_ritual.phase1_status(module.memcon_runtime)
                checks.append(_check(
                    "carrier:augury-ritual-read-only-self-test",
                    ritual_state.get("augury", {}).get("general_natural_language_parser_implemented") is False
                    and ritual_state.get("ritual", {}).get("exact_compiler_available") is True
                    and ritual_state.get("ritual", {}).get("natural_language_manifestation_allowed") is False
                    and ritual_state.get("production_retrieval_changed") is False
                    and ritual_state.get("unrestricted_global_weighting_enabled") is False,
                    "deployed Phase-1 status executes read-only with general AUGURY manifestation disabled",
                ))
            except Exception as exc:
                checks.append(_check(
                    "carrier:augury-ritual-read-only-self-test",
                    False,
                    f"{type(exc).__name__}: {exc}",
                ))
            checks.append(_check("carrier-route:/gaiaos/boot", ("/gaiaos/boot", "GET") in route_pairs, "live boot packet route registration observed"))
            try:
                boot_packet = module.gaiaos_app._boot_packet("VERIFIER_SELF_TEST")
                checks.append(_check(
                    "carrier:gaiaos-boot-packet-self-test",
                    boot_packet.get("status") == "ACTIVE"
                    and boot_packet.get("schema") == "gaiaos.boot-packet.v1"
                    and set(boot_packet.get("roster", [])) == {"VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE"}
                    and all(name in boot_packet.get("members", {}) for name in ("VERA","ANVIL","SELENE","ORIN","KESTREL","NIMUE")),
                    "deterministic source-derived GaiaOS boot packet executes successfully against deployed canonical state",
                ))
            except Exception as exc:
                checks.append(_check(
                    "carrier:gaiaos-boot-packet-self-test",
                    False,
                    f"deterministic GaiaOS boot packet self-test failed: {type(exc).__name__}: {exc}",
                ))
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            for name in ("health", "chat", "verify", "mcp"):
                checks.append(_check(f"carrier-route:/{name}", False, f"ASGI route self-test failed: {detail}"))

    passed = sum(c["status"] == "PASS" for c in checks)
    failed = len(checks) - passed
    return {
        "schema": "gaiaos.implementation-verification.v1",
        "execution": "OBSERVED_RUNTIME",
        "verification_run_id": __import__("uuid").uuid4().hex,
        "carrier_checkout": str(ROOT),
        "platform_version": (current or {}).get("platform_version"),
        "source_commit_claim": (current or {}).get("proof_ceiling"),
        "checks": checks,
        "summary": {"total": len(checks), "passed": passed, "failed": failed},
        "live_host_execution": "PROVEN_FOR_THIS_CALL" if failed == 0 else "FAILED",
        "remaining_external_proof": [
            "This response proves the verifier itself executed in the carrier process.",
            "It does not by itself prove that ChatGPT automatically adopts GaiaOS.",
            "VASKON live cross-daemon exchange still requires an observable VASKON invocation/receipt.",
            "Restart persistence requires a second verifier call after a deployment restart.",
            "Phase 3F verifier checks source, guardrails, and route registration only. A separate live switch-test and active-pilot rollback receipt are required to prove operational behavior.",
        ],
    }
