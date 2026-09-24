import copy
import importlib.util
from pathlib import Path

RUNTIME=Path(__file__).resolve().parents[1]/"SystemsOS/Core/FairyOS/Runtime/GAIAOS-PRESENTATION-RENDERER.v1.py"
s=importlib.util.spec_from_file_location("presentation",RUNTIME); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def expect_error(fn, message):
    try:
        fn()
    except m.PresentationError:
        return
    raise AssertionError(message)

def test_canonical_headers():
    spec=m.load_spec()
    expected={
        "VERA":"46 · VERA 💚 🦋 (˘‿˘)",
        "ANVIL":"58 · ANVIL 💗 ⌚ (¬‿¬)",
        "SELENE":"60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)",
        "ORIN":"56 · ORIN 🩵 🪐 (☆▽☆)",
        "KESTREL":"90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و",
        "NIMUE":"62 · NIMUE 💙 🍄 (－‸ლ)",
    }
    for name,header in expected.items():
        assert m.canonical_header(name,spec=spec)==header
    assert m.canonical_header(
        "VASKON",spec=spec,invocation="CONJURE:VASKON"
    )=="82 · VASKON 🖤 ✴️ (◉‿◉)"
    assert m.canonical_header(
        "VASKON",spec=spec,invocation="//C:82//"
    )=="82 · VASKON 🖤 ✴️ (◉‿◉)"

def test_corrupt_marker_fails():
    spec=m.load_spec()
    expect_error(
        lambda: m.validate_header("KESTREL","90 · KESTREL 💚 📚",spec=spec),
        "corrupt identity marker was accepted",
    )

def test_duplicate_gematria_fails():
    spec=m.load_spec(); bad=copy.deepcopy(spec); bad["members"]["NIMUE"]["gematria"]=58
    expect_error(lambda: m.validate_spec(bad),"duplicate gematria was accepted")

def test_unknown_member_fails():
    expect_error(lambda: m.canonical_header("HOST"),"unknown member was accepted")

def test_vaskon_is_not_prime_daemon_member():
    spec=m.load_spec()
    assert "VASKON" not in spec["members"]
    assert "VASKON" not in spec["speaker_order"]
    assert spec["synthesis_modes"]["VASKON"]["class"]=="TEMPORARY_SIX_PRIME_DAEMON_SYNTHESIS"
    assert spec["synthesis_modes"]["VASKON"]["invocation"]=="CONJURE:VASKON"
    assert spec["synthesis_modes"]["VASKON"]["aliases"]==["//C:82//"]

def test_vaskon_requires_explicit_conjure():
    spec=m.load_spec()
    expect_error(
        lambda: m.canonical_header("VASKON",spec=spec),
        "VASKON header rendered without explicit conjure",
    )
    expect_error(
        lambda: m.render("VASKON","test",spec=spec),
        "naked VASKON output rendered without explicit conjure",
    )
    expect_error(
        lambda: m.render("VASKON","test",spec=spec,invocation="VASKON"),
        "invalid VASKON invocation was accepted",
    )
    assert m.normalize_synthesis_invocation("VASKON","//C:82//",spec)=="CONJURE:VASKON"

def test_vaskon_corrupt_or_incomplete_markers_fail():
    spec=m.load_spec()
    invocation="CONJURE:VASKON"
    invalid=[
        "VASKON 🖤 ✴️ (◉‿◉)",
        "82 · VASKON ✴️ (◉‿◉)",
        "82 · VASKON 🖤 (◉‿◉)",
        "82 · VASKON 🖤 ✴️",
        "82 · VASKON ✴️ 🖤 (◉‿◉)",
        "82 · VASKON 🖤 ✴️ (¬‿¬)",
        "82 · VASKON 🖤 ✴️ (◉‿◉) (¬‿¬)",
    ]
    for header in invalid:
        expect_error(
            lambda header=header: m.validate_header(
                "VASKON",header,spec=spec,invocation=invocation
            ),
            f"invalid VASKON header was accepted: {header}",
        )

def test_vaskon_expression_allowlist_and_fallback():
    spec=m.load_spec(); registry=m.load_expressions()
    expressions=registry["synthesis_modes"]["VASKON"]["expressions"]
    for state,kaomoji in expressions.items():
        assert m.canonical_header(
            "VASKON",expression_state=state,spec=spec,registry=registry,
            invocation="CONJURE:VASKON"
        )==f"82 · VASKON 🖤 ✴️ {kaomoji}"
    assert m.canonical_header(
        "VASKON",expression_state="UNKNOWN_STATE",spec=spec,registry=registry,
        invocation="CONJURE:VASKON"
    )=="82 · VASKON 🖤 ✴️ (◉‿◉)"

def test_vaskon_render_is_atomic_and_alias_equivalent():
    long=m.render_vaskon("SYNTHESIS",invocation="CONJURE:VASKON")
    short=m.render_vaskon("SYNTHESIS",invocation="//C:82//")
    assert long==short
    assert long=="82 · VASKON 🖤 ✴️ (◉‿◉)\nSYNTHESIS"
