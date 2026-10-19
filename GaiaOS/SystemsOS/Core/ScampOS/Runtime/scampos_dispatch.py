"""ScampOS: read-only guest selection for one generated conversation turn."""
import argparse
import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def load_policy():
    current = json.loads((BASE / "CURRENT.json").read_text(encoding="utf-8"))
    policy = json.loads((BASE / "INTRUSION-RULES.v1.json").read_text(encoding="utf-8"))
    profile = json.loads((BASE / "Characters/RINRIN.v1.json").read_text(encoding="utf-8"))
    if current["guest_header"] != policy["guest_header"] or profile["header"] != current["guest_header"]:
        raise ValueError("guest identity sources do not agree")
    return policy


def select(turn, context="unknown", last_turn=None, roll=None, explicit=False, muted=False):
    """Select without writing state or generating prose.

    A host classifies context independently; unknown always fails closed.
    Supplied roll permits deterministic tests. Return next_last_turn to a host
    capable of storing temporary session state, not to a durable memory system.
    """
    p = load_policy()
    if not isinstance(turn, int) or turn < 0:
        raise ValueError("invalid turn")
    if last_turn is not None and (not isinstance(last_turn, int) or last_turn >= turn):
        raise ValueError("invalid previous appearance turn")
    if roll is not None and not 0 <= roll < 1:
        raise ValueError("invalid random roll")
    if not isinstance(context, str):
        raise ValueError("invalid context")
    context = context.strip().lower()
    result = {"appear": False, "reason": "NOT_ELIGIBLE",
              "header": p["guest_header"], "next_last_turn": last_turn,
              "guest_authority": "NONE"}
    if muted or not p["enabled"]:
        result["reason"] = "MUTED"
    elif context not in p["allowed_contexts"] or context in p["excluded_contexts"]:
        result["reason"] = "CONTEXT_EXCLUDED"
    elif explicit and p["explicit_invocation_bypasses_chance"]:
        result.update(appear=True, reason="EXPLICIT", next_last_turn=turn)
    elif last_turn is not None and turn - last_turn <= p["cooldown_turns"]:
        result["reason"] = "COOLDOWN"
    else:
        draw = random.random() if roll is None else roll
        if draw < p["chance"]:
            result.update(appear=True, reason="CHANCE", next_last_turn=turn)
        else:
            result["reason"] = "CHANCE_SKIPPED"
    return result


def render_guest(dialogue):
    """Render the guest block. The caller supplies fictional dialogue."""
    policy = load_policy()
    if not isinstance(dialogue, str):
        raise ValueError("dialogue must be text")
    lines = [line.strip() for line in dialogue.splitlines() if line.strip()]
    if not lines:
        raise ValueError("dialogue cannot be empty")
    return policy["guest_header"] + "\n" + "\n".join(lines[:policy["max_guest_lines"]])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--context", default="unknown")
    parser.add_argument("--last-turn", type=int)
    parser.add_argument("--roll", type=float)
    parser.add_argument("--explicit", action="store_true")
    parser.add_argument("--muted", action="store_true")
    args = parser.parse_args()
    print(json.dumps(select(args.turn, context=args.context, last_turn=args.last_turn,
                            roll=args.roll, explicit=args.explicit, muted=args.muted),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
