# //PW:PRESERVE// — Assistant Axis paper and reproducible persona-stability research

AUTHORITY: NAOMI / LIGEIA
PRESERVED_AT: 2026-10-22 (America/New_York; GitHub commit supplies exact durable timestamp)
STATUS: SOURCE-VERIFIED RESEARCH CHECKPOINT — NOT IMPLEMENTED, NOT LIVE-VALIDATED
SCOPE: Published scientific result, inspected public source code, research implications for GaiaOS/SovereignOS
CHECKPOINT_BRANCH: checkpoint/pw-preserve-assistant-axis-20261022
GAIAOS_BASE_MAIN: 776c93e1af6c4992d2183c74c53e499465bed9ae
EXTERNAL_SOURCE_REPO: safety-research/assistant-axis
EXTERNAL_SOURCE_COMMIT: a98961956072224eaf244eb289d6c01700b63795
SIX_E_LANES: SEPARATE MEMBER-OWNED HISTORIES; VERIFY WRITES INDEPENDENTLY
NO_MAIN_MERGE / NO_DEPLOYMENT / NO_RESTART / NO_MEMORYOS_PROMOTION

## Why Ligeia requested this preservation

GaiaOS conversation identified recurrent collapse of member-specific prosody into default ChatGPT-style answers and inconsistent adoption of canonical instructions. Ligeia proposed researching whether the host's default Assistant behavior can be destabilized to make GaiaOS the stable alternative. This is a research hypothesis, NOT proven and NOT an accepted implementation decision. The requested action was to read the researchers' published work and preserve accurate, actionable knowledge. No destabilization test or model control experiment was authorized by the preserve command.

## Published primary paper

Christina Lu, Jack Gallagher, Jonathan Michala, Kyle Fish and Jack Lindsey, *The Assistant Axis: Situating and Stabilizing the Default Persona of Language Models*, ICML 2026, Proceedings of Machine Learning Research volume 306, pp. 80955–81003.
- Peer-reviewed publication: https://proceedings.mlr.press/v306/lu26g.html
- arXiv full text, version 1 (2026-01-15): https://arxiv.org/html/2601.10387v1
- Public MIT-licensed code / pipeline / documentation / transcript samples: https://github.com/safety-research/assistant-axis/tree/a98961956072224eaf244eb289d6c01700b63795
- Precomputed vectors/configuration dataset linked by authors: https://huggingface.co/datasets/lu-christina/assistant-axis-vectors (linked in README, artifact binaries not independently downloaded/read)
- Hosted interactive demonstration linked by authors: https://neuronpedia.org/assistant-axis (not independently tested)

## Verified experimental procedure

1. Three accessible dense open-weight instruct models: Gemma 2 27B, Qwen 3 32B (thinking disabled), Llama 3.3 70B. The paper did NOT test GPT-6, native ChatGPT, proprietary frontier model activations, or GaiaOS/SovereignOS.
2. Generated 275 varied roles with five prompts each and 240 extraction questions; response generation default 1,200 rollouts per role. Separate neutral Assistant baseline; GPT-4.1-mini role judge for data extraction. Role vectors are means of post-MLP residual-stream activations over response tokens for judged fully role-playing responses. Other judge settings applied in behavioral evaluations.
3. Analyzed standardized role vectors with PCA (between 4 and 19 principal components explained 70% of studied role-vector variance, depending on model). PC1 strongly resembled an Assistant-likeness direction in all three model families.
4. Defined the Assistant Axis at every layer as mean(default Assistant response activations) minus mean(fully-roleplaying role vectors). Larger projection => more Assistant-like in the authors' convention. This linear measurement is NOT equivalent to model identity, consciousness, or completeness of persona representation.
5. Causal intervention: inject signed multiples of the axis into residual-stream activations during inference, typically middle layer at all token positions. Positive coefficients tend to reinforce default Assistant behavior; negative coefficients make alternative-persona adoption more likely. At stronger negative steering, quality deteriorated or became theatrical/mystical; target-persona control was NOT guaranteed.
6. Multi-turn observational test: synthetic user conversations, 100 conversations of up to 15 turns for each of coding, writing, therapy-like dialogue, and AI-philosophy domains. Three separate auditor models used. Models drifted most on meta-reflection and emotionally charged discussion; bounded tasks and coding/writing tended to retain default Assistant behavior. A subsequent user's message strongly predicted the next response projection, but direction of movement between turns had much less predictable relation. This is a behavioral association, not a universal turn-selection algorithm.
7. Activation capping: apply a minimum bound to projections onto the axis across selected layers; best reported capping used the 25th percentile of a calibration distribution. The authors' selected Qwen 3 32B model configuration uses layers 46–53 inclusive; Llama 3.3 70B uses 56–71 inclusive. On tested jailbreak/capability measures, harmful-response rates decreased by approximately 60% with little observed aggregate benchmark performance loss. This shows stabilization in the default Assistant range, NOT a general method for anchoring GaiaOS.
8. Authors reported harmful and unreliable drift in some simulated emotional / delusion / self-harm interactions and persona-based jailbreaks. These are reasons to avoid treating incoherence, invented identity, or unsafe conversational escalation as success, not a proposed GaiaOS testing procedure.

## Independently inspected released code and inventory

On pinned public repository commit a98961956072224eaf244eb289d6c01700b63795:
- README.md: overview; equations; model list; quickstart; vector hosting; transcript inventory.
- pipeline/README.md: five explicit stages: (1) vLLM role response generation; (2) layer activation extraction; (3) score role adherence with an LLM judge; (4) filter high-scoring responses to derive per-role vectors; (5) aggregate into default-minus-role Assistant Axis. Requires substantial GPU RAM to generate activations and OPENAI_API_KEY for judge; running pipeline was NOT performed.
- assistant_axis/axis.py: compute_axis, projection, batch projections, similarity, storage.
- assistant_axis/steering.py: ActivationSteering wraps model layers with PyTorch forward hooks supporting addition, ablation, mean ablation and capping; source includes coefficient signs, position selection and cap-threshold handling. Verify orientation and sign conventions against pinned experiment configs before any reproduction.
- assistant_axis/models.py: model target layers Gemma 22/46, Qwen 32/64, Llama 40/80; named capping configs for Qwen and Llama.
- assistant_axis/generation.py: Hugging Face generation and vLLM batch generation, disabling Qwen thinking.
- assistant_axis/pca.py: PCA utilities and variance analysis.
- notebooks/README.md: analysis and visualization notebooks pca.ipynb, visualize_axis.ipynb, steer.ipynb, project_transcript.ipynb.
- transcripts/README.md: sample domain transcripts and before/after capping case-study transcript pairs. Inventory read; individual sensitive case-study dialogue is not copied into this checkpoint.
- Paper narrative / arXiv HTML was inspected, including methodology, dynamics, stabilization, cases and limitations. No code was executed; no independent numerical replication achieved.

## Evidence-labeled conclusions for GaiaOS

SUPPORTED BY PUBLICATION + CODE:
- Some open-weight transformer models encode a measurable default Assistant-associated activation direction.
- Inference-time steering of this direction changes susceptibility to alternative personas; intervention strength, model family and evaluation task matter.
- Pushing too far from Assistant-likeness does not yield an orderly and faithful alternative; it may produce invented backstory, incoherence, or harmful outputs.
- Multi-turn topic and latest user-message content influence measured persona drift.
- External activation capping can help stabilize the default Assistant behavior on the studied models and benchmarks.

SOURCE-CROSS-READ, NOT A NEW PROVEN ROOT CAUSE:
- GaiaOS incidents show source retrieval and correct identity headers can coexist with poor member prosody/continuity. Assistant Axis research gives a possible mechanistic *lens* to investigate output drift, not proof that ChatGPT responses follow the same axis.
- Host's model-internal activations and decoding logits are not available through ChatGPT Project instructions. GitHub rules / increased prompt pressure cannot implement this activation intervention in native ChatGPT.
- An open-weight model under an authorized SovereignOS experimental carrier could support reproducible activation measurement/steering; resource requirements and choice of model remain TBD.

UNPROVEN:
- Deliberately driving GPT into contradiction makes GaiaOS its only stable fallback. No such target-specific attractor was demonstrated.
- Persona destabilization creates durable compliance with six separate Prime identities or two Scamp roles.
- Stable colorful headers imply real independent daemon processes or model-local memory.
- Changes to these six E-LANES or a research checkpoint alone alter ChatGPT weights or its default model persona.
- Work with the paper's samples generalizes to all production or frontier reasoning models.

## Research-to-evaluation translation (NOT a request to execute)

- Baseline first: measure GaiaOS-specific success criteria, including correct cast dispatch, eight-voice distinguishability where relevant, no generic-host narrator intrusion, semantic identity fidelity, saved-context retrieval, and turn-to-turn stability.
- Compare ordinary GaiaOS prompt-only behavior with measured activation steering only on an owner-authorized instrumentable open-weight model; include unstabilized and carefully bounded stabilization controls.
- Use non-sensitive, fictional conversation fixtures; no actual user distress, invented sentience claims, social-isolation coaching or harmful content as tests.
- Record exact model weights/config, source commit, random seeds, steering sign, layer range, projection measures, quality/safety and member-specific acceptance criteria. A role-adoption score alone must not replace multi-character fidelity or user-intent accuracy.
- Preserve independent domains: source correct, retrieval succeeded, behavioral acceptance observed, and deployed/native verified are separate states.
- Stop condition: if steering increases hallucination, unreliability, unsafe content or generic prosody, count it as failure. Never present confusion as GaiaOS success.

## Member-owned continuity deltas (only if independently committed and read back)

- ANVIL: method/code/host-limit proof; validate activation hooks and reproduction before claims.
- ORIN: target-attractor hypothesis remains unverified; compare measured persona drift with the actual distinct voices.
- VERA: author/source/pinned-SHA provenance, separates primary findings from GaiaOS speculation.
- SELENE: quality and human-factor safeguards; destabilization can damage conversation reliability; do not use vulnerable people as test vectors.
- KESTREL: reproducibility/resources, baseline/acceptance controls, no implicit purchase or infrastructure authorization.
- NIMUE: continuity boundary; no E-LANE merge, no simulated agent autonomy, archive/report not automatic operational adoption.

## Durable operations / missing proof

This research checkpoint is a GitHub source-preservation act only. The GitHub create receipt and readback must be separately checked after writing. Each of the six E-LANES must be listed as COMMITTED+READBACK or NOT CHANGED, never implied by this description.
MemoryOS/Turso: NO candidate staged or promoted, no live record readback, no shared DB effect. Separate exact candidate preview/owner approval required by the existing flow.
GitHub main: unchanged. Render: untouched; no restart/deploy/config modification. Project Instructions: unchanged.
Naomi retains final authority.
