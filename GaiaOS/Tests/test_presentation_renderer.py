import copy
import importlib.util
from pathlib import Path

RUNTIME=Path(__file__).resolve().parents[1]/"SystemsOS/Core/FairyOS/Runtime/GAIAOS-PRESENTATION-RENDERER.v1.py"
s=importlib.util.spec_from_file_location("presentation",RUNTIME); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def test_canonical_headers():
    spec=m.load_spec()
    expected={"VERA":"46 · VERA 💚 📚 (˘‿˘)","ANVIL":"58 · ANVIL 💗 ⌚ (¬‿¬)","SELENE":"60 · SELENE 💛 🎧 (˶ᵔ ᵕ ᵔ˶)","ORIN":"56 · ORIN 🩵 🪐 (☆▽☆)","KESTREL":"90 · KESTREL 💖 🏍️ (•̀ᴗ•́)و","NIMUE":"62 · NIMUE 💙 🍄 (－‸ლ)"}
    for name,header in expected.items(): assert m.canonical_header(name,spec=spec)==header
    assert m.canonical_header("VASKON",spec=spec)=="82 · VASKON 🖤 ✴️ (◉‿◉)"

def test_corrupt_marker_fails():
    spec=m.load_spec()
    try: m.validate_header("KESTREL","90 · KESTREL 💚 📚",spec=spec)
    except m.PresentationError: return
    raise AssertionError("corrupt identity marker was accepted")

def test_duplicate_gematria_fails():
    spec=m.load_spec(); bad=copy.deepcopy(spec); bad["members"]["NIMUE"]["gematria"]=58
    try: m.validate_spec(bad)
    except m.PresentationError: return
    raise AssertionError("duplicate gematria was accepted")

def test_unknown_member_fails():
    try: m.canonical_header("HOST")
    except m.PresentationError: return
    raise AssertionError("unknown member was accepted")

def test_vaskon_is_not_prime_daemon_member():
    spec=m.load_spec()
    assert "VASKON" not in spec["members"]
    assert "VASKON" not in spec["speaker_order"]
    assert spec["synthesis_modes"]["VASKON"]["class"]=="TEMPORARY_SIX_PRIME_DAEMON_SYNTHESIS"

def test_vaskon_corrupt_marker_fails():
    spec=m.load_spec()
    try: m.validate_header("VASKON","82 · VASKON 💗 ✴️ (◉‿◉)",spec=spec)
    except m.PresentationError: return
    raise AssertionError("corrupt VASKON identity marker was accepted")
