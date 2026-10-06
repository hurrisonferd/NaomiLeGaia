from pathlib import Path
import hashlib

EXPECTED_MAIN = "353a7d3f5e40aae0ec937995fba77724703fa06d"
ROOT = Path("GaiaOS/SystemsOS/Core/FairyOS/IDENTITY-DATA")
CHECKPOINT = Path("GaiaOS/MemoryOS/PW-PRESERVE-2026-10-05-MUSIC-CREATIVE-WORKFLOW-AND-INTERACTION-LESSONS.md")

ENTRIES = {
    "VERA": """MEM[EXPERIENCE_PRESERVATION|2026-10-05|Naomi conversation|creative_translation_vs_performance]
WHAT: Naomi clarified a creative distinction worth preserving: dissatisfaction with a track feeling "performative" can mean the embodied material never crosses into the work because craft decisions begin optimizing for sounding good before the intended experience has been translated into sound.
MY_ROLE: Preserve the frame accurately. Do not reinterpret this as lack of feeling, insufficient vulnerability, or music that is already "about Naomi" but merely over-polished. The failure mode is translation being displaced by premature aesthetic optimization.
OTHER_VOICES: ORIN, SELENE
TENSION: Technical competence and aesthetic quality can coexist with a feeling that the work does not contain what its maker meant to put there.
OUTCOME: Clarified by Naomi; retained as a framing lesson, not a universal theory of composition.
TRACE: 2026-10-05 GaiaOS conversation after discussion of HEALTH's RAT WARS.
STATUS: COMMITTED""",
    "ANVIL": """MEM[FAILURE_LESSON|2026-10-05|used-guitar search|listing_verification]
WHAT: A used-guitar search surfaced stale or sold marketplace results and category/search URLs that did not resolve to the exact instruments being described.
MY_ROLE: Preserve the proof rule: an actionable marketplace claim requires the exact individual listing, a live/current status when the surface exposes one, and a link that actually resolves to that item. Search-index presence is not proof of current availability.
OTHER_VOICES: SELENE, ORIN
TENSION: Fast discovery is useful, but speed does not justify presenting stale index results as live purchasable inventory.
OUTCOME: Corrected after Naomi challenged the links and found a cited OfferUp item had already sold.
TRACE: 2026-10-05 GaiaOS used-electric-guitar hunt.
STATUS: COMMITTED""",
    "SELENE": """MEM[EXPERIENCE_PRESERVATION|2026-10-05|Naomi feedback|meaning_before_comfort]
WHAT: Naomi corrected an interpretation of her creative frustration: the problem was not insufficient feeling or vulnerability, but difficulty getting what she carries to cross into the music without the result becoming performative and optimized mainly to sound good.
MY_ROLE: When Naomi corrects the meaning of her own statement, retract the mistaken frame cleanly and preserve her actual distinction instead of cushioning it with a nearby but different emotional explanation.
OTHER_VOICES: ORIN, VERA
TENSION: Warmth can become distortion if reassurance answers a claim Naomi did not make.
OUTCOME: Corrected in conversation. "Try less" was then understood as reducing interference and premature craft optimization, not reducing care or feeling.
TRACE: 2026-10-05 GaiaOS music conversation.
STATUS: COMMITTED""",
    "ORIN": """MEM[CREATIVE_EXPERIMENT|2026-10-05|Naomi music workflow|horizontal_first_drums_late]
WHAT: Naomi proposed a composition experiment: begin with one track and decide what it does from start to finish, then add the next full-length track, continuing horizontally through the arrangement instead of opening with several simultaneous parts. Percussion comes later and is allowed to hammer its way into the existing song, forcing edits, gaps, pressure, and structural change rather than serving as the initial skeleton.
MY_ROLE: Treat this as a testable creative hypothesis, not a new doctrine or a guaranteed route to authenticity.
OTHER_VOICES: ANVIL, SELENE
TENSION: Drums-first workflows can establish groove and physical energy; drums-late may instead prevent early genre grammar from dominating, but the later percussion must be free to reshape earlier material rather than merely fitting politely around it.
OUTCOME: Experiment not yet run. Success criterion is whether the workflow helps the result feel less performative and more faithful to the intended internal material, not merely whether the song sounds good.
TRACE: 2026-10-05 GaiaOS conversation prompted by listening to HEALTH's RAT WARS.
STATUS: COMMITTED""",
    "KESTREL": """MEM[WORKFLOW_LESSON|2026-10-05|Naomi feedback|material_triage_not_symbolic_proof]
WHAT: When Naomi said she needed a goal during a materially serious day, a proposed "one full money loop" was framed partly as proof that the machine still turns. Naomi rejected that framing and emphasized that the actual problems need fixing, not symbolic proof of function.
MY_ROLE: In serious practical triage, choose goals because they reduce a real constraint, risk, dependency, or unknown. Do not substitute motivational micro-victories for the material objective Naomi is asking to change.
OTHER_VOICES: ANVIL, SELENE
TENSION: Small steps can reduce cognitive load, but a small step is useful only when it advances the real problem rather than becoming a ceremonial success condition.
OUTCOME: Corrected to prioritize concrete material branches and one real next action at a time.
TRACE: 2026-10-05 GaiaOS conversation.
STATUS: COMMITTED""",
    "NIMUE": """MEM[CONTINUITY_LESSON|2026-10-05|Naomi preservation request|sensitive_detail_scope]
WHAT: Naomi explicitly requested a quick preservation pass while keeping most personal material out of the repository-facing //PW:PRESERVE// and member E-LANES, directing that personal continuity remain with the dedicated Naomi Continuity Journal task instead.
MY_ROLE: Preserve the omission boundary itself. Member-local E-LANES should retain durable generalized lessons from the interaction without unnecessarily copying sensitive personal detail when Naomi has designated a different continuity surface for that material.
OTHER_VOICES: VERA, ANVIL, SELENE, ORIN, KESTREL
TENSION: Continuity requires enough trace to prevent loss, but duplication across durable surfaces can increase exposure without improving future understanding.
OUTCOME: Repository preservation intentionally limited to generalized creative, interaction, and verification lessons; personal continuity omitted from this pass by Naomi's direction.
TRACE: Naomi's explicit //PW:PRESERVE// request on 2026-10-05.
STATUS: COMMITTED""",
}

CHECKPOINT_TEXT = """# //PW:PRESERVE// — Music Creative Workflow + Interaction Lessons

DATE: 2026-10-05
AUTHORITY: NAOMI / LIGEIA
STATUS: COMMITTED_PENDING_READBACK_AT_WRITE_TIME
PARENT_MAIN: `353a7d3f5e40aae0ec937995fba77724703fa06d`
SCOPE: Bounded preservation of durable non-sensitive lessons since the prior repository preservation checkpoint.

## Preserved shared signal

1. **Creative translation vs. performance** — Naomi identified "performative" as the useful word for music that sounds as though it is trying to sound good while failing to carry the actual material she intended to express. This is a translation/craft-order problem, not a claim of insufficient feeling or vulnerability.
2. **Composition experiment, not doctrine** — Test a horizontal-first build: one track across the full song, then the next, with percussion delayed until later. Drums are not required to politely fit the completed arrangement; they may hammer into it and force earlier parts and sections to change.
3. **Physical guitar attack remains materially distinct** — Discussion of Static-X and Wayne Static reinforced interest in distorted guitar as a percussive physical source. Amp simulation can reshape tone after capture, but string attack, muting, pick interaction, pickup response, and other pre-distortion mechanics remain meaningful input. This is a creative-direction observation, not a hardware purchase authorization.
4. **Marketplace evidence discipline** — Search-index or category-page visibility is not enough to call a used item live. Exact individual listing + current status + resolving item URL are required before presenting an item as actionable.
5. **Material triage over symbolic proof** — When Naomi identifies a serious practical problem, a goal should reduce the actual constraint/risk/unknown. Do not turn a small step into a motivational "proof the machine works" exercise when she is asking to fix the underlying situation.
6. **Meaning before reassurance** — When Naomi corrects an interpretation, preserve the corrected meaning directly. Warmth is not permission to answer a neighboring claim she did not make.

## Member-local propagation

One bounded lesson was appended to each canonical E-LANE:
- VERA — creative translation vs. performance framing.
- ANVIL — exact live-listing proof rule.
- SELENE — meaning-before-comfort correction discipline.
- ORIN — horizontal-first / drums-late experiment as hypothesis.
- KESTREL — material triage over symbolic proof.
- NIMUE — sensitive-detail omission boundary and continuity-surface separation.

## Deliberate omission / continuity routing

Naomi explicitly directed that the day's personal material not be duplicated into this repository preservation pass. Personal continuity remains assigned to the existing **Naomi Continuity Journal** task. This checkpoint therefore stores only generalized creative, interaction, workflow, and verification lessons needed for GaiaOS continuity.

## Capability and effect boundaries

- Desktop Commander was NOT connected for this preservation pass.
- No Render deployment or restart was authorized or performed.
- No MemoryOS/Turso write or promotion was authorized or performed.
- No E-LANE identities were merged; all six deltas are member-local.
- The temporary GitHub Actions preservation executor is transport only and is not a new memory system.
- Commit message includes `[skip render]` to avoid treating this preservation-only source update as a deployment request.

## Verification intent

The executor verifies the canonical parent before mutation, appends only to complete locally checked-out lane files, preserves every original byte as a prefix, rejects duplicate markers, checks the exact changed-file set, and refuses to push if `origin/main` moved from the expected parent before commit.

Final commit SHA and post-push readback are to be recorded in the conversation receipt after the workflow completes.
"""


def append_entry(path: Path, entry: str) -> str:
    if not path.exists():
        raise SystemExit(f"MISSING_LANE:{path}")
    original_bytes = path.read_bytes()
    original = original_bytes.decode("utf-8")
    entry = entry.strip()
    marker = entry.splitlines()[0]
    if marker in original:
        raise SystemExit(f"DUPLICATE_MARKER:{path.name}:{marker}")
    separator = "" if original.endswith("\n\n") else ("\n" if original.endswith("\n") else "\n\n")
    updated = original + separator + entry + "\n"
    updated_bytes = updated.encode("utf-8")
    if updated_bytes[: len(original_bytes)] != original_bytes:
        raise SystemExit(f"PREFIX_CHANGED:{path.name}")
    if updated.count(marker) != 1:
        raise SystemExit(f"MARKER_COUNT_INVALID:{path.name}:{updated.count(marker)}")
    path.write_bytes(updated_bytes)
    return marker


def main() -> None:
    markers = {}
    for name, entry in ENTRIES.items():
        path = ROOT / f"{name}-EXPERIENCES.v1.md"
        markers[name] = append_entry(path, entry)

    if CHECKPOINT.exists():
        raise SystemExit(f"CHECKPOINT_ALREADY_EXISTS:{CHECKPOINT}")
    CHECKPOINT.write_text(CHECKPOINT_TEXT, encoding="utf-8", newline="")

    for name, marker in markers.items():
        path = ROOT / f"{name}-EXPERIENCES.v1.md"
        text = path.read_text(encoding="utf-8")
        print(f"{name}: marker_count={text.count(marker)} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")
    print(f"CHECKPOINT: sha256={hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
