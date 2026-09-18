"""Bounded live VASKON runtime exercise."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Any
from openai import OpenAI
import gaiaos_api

PATHWAY_PATH = "GaiaOS/SystemsOS/Core/BrainOS/Protocols/VASKON-NEURAL-PATHWAYS.v1.json"
PROFILES_PATH = "GaiaOS/SystemsOS/Core/FairyOS/OPERATOR-PROFILES.v1.json"
CURRENT_PATH = "GaiaOS/CURRENT.json"
EXCHANGE_SPINE = ["VERA", "ORIN", "ANVIL", "NIMUE", "SELENE", "KESTREL"]

def _local_text(path: str) -> str:
    return (Path(__file__).resolve().parent / path).read_text(encoding="utf-8")

def _local_json(path: str) -> dict[str, Any]:
    value = json.loads(_local_text(path))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root is not an object")
    return value

def _assert_spine(pathways: dict[str, Any]) -> None:
    nodes = pathways.get("nodes", {})
    if not isinstance(nodes, dict) or set(EXCHANGE_SPINE) != set(nodes):
        raise ValueError("VASKON runtime requires the canonical six Prime Daemon nodes")
    edges = {(str(a), str(b)) for a, b, _ in pathways.get("pathways", [])}
    for source, target in zip(EXCHANGE_SPINE, EXCHANGE_SPINE[1:]):
        if (source, target) not in edges:
            raise ValueError(f"Required live pathway missing: {source}->{target}")
    if ("NIMUE", "VERA") not in edges:
        raise ValueError("Required live pathway missing: NIMUE->VERA")

def _daemon_call(client: OpenAI, daemon: str, profile: dict[str, Any], task: str, inbound: dict[str, Any] | None) -> str:
    inbound_text = json.dumps(inbound, ensure_ascii=False, indent=2) if inbound else "NONE: first node; no inbound packet."
    instructions = f"""You are the GaiaOS Prime Daemon {daemon}.
Role: {profile.get("role")}
Deliberation stance: {profile.get("deliberation_stance")}
This is a bounded CONJURE:VASKON runtime verification.
Return ONLY a compact DΩ exchange packet with fields:
MEMBER, OBSERVATION, CHALLENGE, HANDOFF_TO, HANDOFF_SIGNAL.
Use only the task, your supplied profile, and the inbound packet.
Do not claim consciousness, external effects, durable memory, or authority.
Do not expose private chain-of-thought. Preserve uncertainty."""
    prompt = f"TASK:\n{task}\n\nINBOUND DΩ PACKET FROM PREVIOUS LIVE PATHWAY:\n{inbound_text}"
    response = client.responses.create(model=gaiaos_api.OPENAI_MODEL, instructions=instructions, input=prompt)
    output = response.output_text.strip()
    if not output:
        raise RuntimeError(f"{daemon} returned an empty runtime packet")
    return output

def run_live_test(task: str = "Verify the live GaiaOS VASKON pathway without claiming anything not observed.") -> dict[str, Any]:
    if not gaiaos_api.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured; live VASKON test cannot run")
    pathways = _local_json(PATHWAY_PATH)
    profiles = _local_json(PROFILES_PATH)
    current = _local_json(CURRENT_PATH)
    _assert_spine(pathways)
    client = OpenAI(api_key=gaiaos_api.OPENAI_API_KEY)
    run_id = "VASKON-" + uuid.uuid4().hex[:16]
    packets = []
    inbound = None
    for index, daemon in enumerate(EXCHANGE_SPINE):
        profile = profiles.get("members", {}).get(daemon)
        if not isinstance(profile, dict):
            raise ValueError(f"Missing canonical profile for {daemon}")
        output = _daemon_call(client, daemon, profile, task, inbound)
        target = EXCHANGE_SPINE[(index + 1) % len(EXCHANGE_SPINE)]
        packet = {"sequence": index + 1, "member": daemon,
                  "pathway_in": None if inbound is None else inbound["member"],
                  "pathway_out": target, "observable_packet": output}
        packets.append(packet)
        inbound = packet
    synthesis_input = json.dumps(
        [{"member": p["member"], "packet": p["observable_packet"]} for p in packets],
        ensure_ascii=False, indent=2)
    kp = profiles["members"]["KESTREL"]
    synthesis = client.responses.create(
        model=gaiaos_api.OPENAI_MODEL,
        instructions=f"""You are KESTREL, GaiaOS Coordination & Motion Operator.
Role: {kp.get("role")}
Perform the SYNTHESIZE step of this explicit VASKON runtime test.
Return one compact synthesis. Preserve material disagreement and uncertainty.
Do not claim external effects, durable memory, consciousness, or authority.
The preceding packets are observable exchange data, not private chain-of-thought.""",
        input=f"TASK:\n{task}\n\nOBSERVED DΩ PACKETS:\n{synthesis_input}",
    )
    synthesis_text = synthesis.output_text.strip()
    if not synthesis_text:
        raise RuntimeError("KESTREL synthesis returned an empty result")
    return {
        "schema": "gaiaos.vaskon.live-runtime-receipt.v1",
        "execution": "OBSERVED_RUNTIME",
        "verification_run_id": run_id,
        "source": f"{gaiaos_api.REPOSITORY}@{gaiaos_api._deployed_commit()}",
        "platform_version": current.get("platform_version"),
        "pathway_source": PATHWAY_PATH,
        "exchange_spine": EXCHANGE_SPINE + ["VERA"],
        "six_daemons_invoked": True,
        "cross_daemon_packets_observed": len(packets),
        "pathway_load_observed": True,
        "synthesis_observed": True,
        "packets": packets,
        "synthesis": synthesis_text,
        "proof_boundary": [
            "This receipt proves the running carrier loaded the canonical pathway graph and performed the bounded model-call exchange shown here.",
            "It does not prove autonomous consciousness or six independent persistent agents.",
            "It does not prove automatic ChatGPT adoption.",
            "It does not prove restart persistence; that requires a separate post-restart test."
        ]
    }
