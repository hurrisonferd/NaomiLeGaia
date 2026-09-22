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
    "SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json",
    "SystemsOS/Core/FairyOS/OPERATOR-DISPATCH-MATRIX.v1.json",
    "SystemsOS/Core/FairyOS/OPERATOR-PROSODY-BASINS.v1.md",
    "SystemsOS/Core/FairyOS/HEAD-PAT-COUNTERS.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/VERA-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ANVIL-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/SELENE-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/ORIN-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/KESTREL-EXPERIENCES.v1.md",
    "SystemsOS/Core/FairyOS/IDENTITY-DATA/NIMUE-EXPERIENCES.v1.md",
]

DAEMONS = {
    "VERA": ("💚", "📚"),
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

    if current and version:
        checks.append(_check(
            "version-alignment",
            current.get("platform_version") == version.get("version"),
            f"CURRENT={current.get('platform_version')} VERSION={version.get('version')}",
        ))
        checks.append(_check(
            "current-vaskon-pointer",
            current.get("brainos", {}).get("vaskon_neural_pathways")
            == "GaiaOS/SystemsOS/Core/BrainOS/Protocols/VASKON-NEURAL-PATHWAYS.v1.json",
            "CURRENT points to canonical VASKON pathway fabric",
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
                "VERA":"46 · VERA 💚 📚 (˘‿˘)", "ANVIL":"58 · ANVIL 💗 ⌚ (¬‿¬)",
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
        checks.append(_check("carrier:/gaiaos/boot", "/gaiaos/boot" in app_text and "def _boot_packet" in app_text, "deterministic boot packet endpoint declared"))

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
            checks.append(_check("carrier-route:/gaiaos/boot", ("/gaiaos/boot", "GET") in route_pairs, "live boot packet route registration observed"))
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
        ],
    }
