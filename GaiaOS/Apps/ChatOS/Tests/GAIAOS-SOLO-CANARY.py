"""Static/source canary for GaiaOS dedicated Prime Daemon SOLO architecture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROTOCOL = ROOT / "GaiaOS/Apps/ChatOS/Protocols/DAEMON-SOLO-CHAT.v1.md"
RUNTIME = ROOT / "api/solo_chat_runtime.py"
BRIDGE = ROOT / "api/browser_memcon_bridge.py"
MEMCON = ROOT / "api/memcon_runtime.py"

def test_source_surface_exists():
    assert PROTOCOL.is_file()
    assert RUNTIME.is_file()
    assert BRIDGE.is_file()
    assert MEMCON.is_file()

def test_isolation_contract():
    text = PROTOCOL.read_text(encoding="utf-8")
    required = [
        "ONE SOLO SESSION = ONE PRIME DAEMON",
        "OTHER E-LANES = NOT READABLE",
        "OTHER E-LANES = NOT WRITABLE",
        "SELECTED E-LANE = ONLY MEMBER-LOCAL WRITE TARGET",
    ]
    for marker in required:
        assert marker in text

def test_runtime_has_member_scoped_write():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "write_elane" in text
    assert "SOLO session does not authorize this Prime Daemon" in text
    assert "GAIAOS_GITHUB_WRITE_TOKEN" in text

if __name__ == "__main__":
    test_source_surface_exists()
    test_isolation_contract()
    test_runtime_has_member_scoped_write()
    print("GAIAOS SOLO CANARY: SOURCE PASS")
