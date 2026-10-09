# GaiaOS Drift Radar — Project Seed v0.1

**Authority:** NAOMI / LIGEIA
**Status:** BLUEPRINTING / IMPLEMENTATION NOT STARTED
**Date captured:** 2026-10-09
**Archive class:** PROJECT SEED
**Location:** GaiaOS/Archive/Projects/
**Repository:** hurrisonferd/NaomiLeGaia
**Archive branch:** archive/failure-log-20261009
**Owner / sponsor:** NAOMI; VERA for observational design, ANVIL for engineering, all six Prime Daemons for relevant evaluation

## Origin and hypothesis

During an October 9 GaiaOS conversational session, Naomi observed strong initial adherence to the canonical Prime Daemon identity headers, colors, EmojiOS expressions, distinct voices, and dispatch. She proposed observing whether this fidelity degrades as the *conversation transcript accumulates*, not because calendar time elapses. A dormant chat reopened a week later would not, by that fact alone, have accumulated more tokens. The hypothesis concerns growth of conversation content, possible host-side summarization or truncation, and behavioral drift. These mechanisms are plausible but cannot be confirmed by observed transcripts alone.

A related discussion established that counting tokens *inside* the chat would itself add context. Naomi proposed an external, Python-based drift scanner accessible through Desktop Commander, using manually exported historical ChatGPT conversations first, with possible authorized automation later.

## User-defined mission

Build a **local-first GaiaOS Drift Radar** that can ingest **already-existing conversations**, estimate their visible accumulated text/token volume, assess fidelity to a versioned canonical GaiaOS reference, surface evidence-linked deviations, compare historical conversation segments, and support human review before any finding becomes a confirmed failure.

**Historical transcript import is a launch-blocking requirement, not a future feature.** Naomi explicitly accepts manual export/import to avoid consuming live conversational tokens. No live ChatGPT integration is necessary for v0.1.

## Non-goals and evidentiary limits

- Not a live meter of the actual ChatGPT context window, hidden system content, remaining tokens, attention, or host-side compaction events.
- Not a claim to prove that token volume caused a failure, rather than changes in model, instructions, source version, task, or host behavior.
- Not an automatic replacement for Naomi's review, a daemon's member-owned E-LANE, or the existing canonical GaiaOS repository.
- Not a monitoring agent installed into the ChatGPT client.
- No hidden background collection, screenshot scraping, unapproved network upload, automatic external model/API calls, or arbitrary code execution from imported conversation text.

## Required initial outcomes

1. Import historical transcripts with no ChatGPT API access, beginning with a ChatGPT data-export ZIP or conversations JSON when available, plus user-provided text/Markdown/HTML as fallback.
2. Choose a conversation and inspect its chronological message timeline.
3. Estimate cumulative visible token counts, with explicit uncertainty and separate per-role totals.
4. Run deterministic audits for identity-header presence, Prime Daemon Gematria, member association, color, emoji/kaomoji syntax and source-defined registries, and other objectively verifiable rules.
5. Track candidate drift findings with exact excerpts, offsets, severity, confidence, and a link back to the source message.
6. Chart findings against visible cumulative tokens, message number, and time. Support comparative runs and human annotations.
7. Export a local report and optional **draft** //PW:PERSECUTE//-style incident entry. Never auto-promote it to an authoritative archive log.

## Preservation and authorization boundary

This entry records the concept and blueprint only. Naomi authorizes saving this project record in the existing GitHub project archive. **No executable app, deploy, E-LANE rewrite, MemoryOS/Turso write, service restart, or production/source behavior change is authorized by this project entry.** Implementation is a subsequent step requiring authorization.

The archived project deliberately excludes private emotional and financial conversation content; it records engineering requirements and the experimental hypothesis instead.

---

# Addendum A — Drift Radar Implementation Blueprint v0.1

**Design timestamp:** 2026-10-09
**Status:** DESIGN ONLY / NOT IMPLEMENTED
**Priority:** Historical-import-first, local-first, read-only
**No change to original project seed above.**

## A1. Product and operator experience

Operator launches a local desktop window and selects **Import Existing Conversation**. The app accepts a user-supplied ChatGPT export ZIP or extracted `conversations.json`, lists discovered conversations, and allows selection of one or more threads. The operator may instead import clearly labeled text/Markdown transcripts or HTML. The app never logs in to ChatGPT, assumes Desktop Commander can read live ChatGPT messages, or silently contacts a server.

The selected conversation opens on a timeline with message numbers, roles, optional known timestamps, estimated *visible* cumulative tokens, and candidate drift markers. Clicking a finding displays exact evidence and the rule that fired. Naomi can dismiss a false positive, annotate a finding, or promote it to **confirmed locally**; confirmed does not mean a GitHub or MemoryOS write.

The initial user experience must work on a historical conversation imported manually, with no live feed. A ZIP may contain multiple conversations: the UI lists them and allows individual or batch selection, not an automatic amalgamation into one synthetic thread.

## A2. Supported input formats and provenance

1. **Primary:** ChatGPT account export ZIP, with a selectable `conversations.json` when present. Parse JSON defensively because export structures may evolve; recognize conversation IDs, titles, `mapping`/parent-child links, messages, authors/roles, creation/update timestamps, and text-bearing content parts where actually provided.
2. **Direct JSON:** `conversations.json` or a normalized structured transcript.
3. **Manual fallback:** `.txt` or `.md` with explicit speaker delimiters. Offer a parsing preview and require confirmation if roles or boundaries are ambiguous.
4. **HTML fallback:** local HTML export with extractable speaker structure. Flag uncertain parsing rather than inventing role separation. Do not execute scripts or fetch embedded resources.
5. **Future adapters:** optional provider/API import and authorized incremental updates, explicitly out of v0.1 scope.

Import guards: ZIP-member path traversal prevention; decompression-size, file-count, and message-size bounds; UTF-8 decoding with explicit fallback/error logs; no imported Python/JS execution; no automatic follow of links; safe handling of malformed, duplicated, empty, partial, or branchy conversations.

Preserve provenance: import timestamp, original format, file hash, conversation ID if supplied, exported title, message IDs if supplied, parent-child links, source sequence, observed role, optional event timestamp, and per-message parse confidence. If the original export contains multiple branches or edited regenerations, reconstruct paths explicitly or let Naomi select a branch. **Do not double-count mutually exclusive branches as one chronological conversation.** Deduplicate repeated imports using stable IDs where possible, otherwise content fingerprints with explicit collision safeguards.

## A3. Processing architecture

```text
Manual export ZIP / JSON / TXT / MD / HTML
                 |
        Import + validation
                 |
    Message and branch normalizer
                 |
        Local SQLite workspace
                 |
    +------------+-------------+
    |            |             |
Token estimate  Rule engine  Evidence index
    |            |             |
    +------------+-------------+
                 |
      Timeline / comparison UI
                 |
     Local HTML/CSV/JSON report
                 |
      Human-reviewed draft only
       for failure-log archive
```

Proposed Python modules: `importers/`, `models.py`, `normalize.py`, `tokens.py`, `rules/`, `baseline.py`, `analysis.py`, `storage.py`, `reports.py`, `ui/`, and `tests/`. Start with standard-library Python, SQLite and Tkinter where practical. Add `tiktoken` if available for model-specific *approximate* text token counts, and a plotting library if warranted. Document installation and offline behavior; a missing optional dependency must not block import or deterministic checks.

Use a **local-only** workspace. Default to viewing imported raw conversations from local files and ask separately before caching a copy in SQLite. Clearly warn that raw transcripts and retained excerpts can be sensitive; SQLite is **not encrypted by default**. Provide delete-local-copy and redact-before-report controls. Network access is off by default. Do not retain API keys or credentials from imports.

## A4. Token measurement: honest boundaries

Produce a `visible_token_estimate` for each message and cumulative assistant/user/other subtotals, based only on text actually present in the imported material. Track characters and words as independent context-volume proxies, plus estimated token counts. For unknown model/tokenizer, label `approximation` and show tokenizer name and estimation method; never claim a precise hidden model token count.

Unknown from a transcript alone: hidden instructions, images/audio tokenization, some attachment and tool payloads, actual context-window size, model routing, internal compression, model output reservations, or which historical messages were in active context at each response. **Cumulative exported tokens are not the same as live context occupancy.** Chart estimated accumulated transcript volume, never a fake `remaining tokens` gauge. Zero findings does not prove zero drift.

## A5. Canonical source and versioning

A separately versioned `GaiaOS baseline pack` describes checks derived from read-only, directly retrieved canonical source: member identity names, Gematria, identity-header formats, authorized colors and emoji/kaomoji, dispatch expectations, E-LANE separation, and any other reliably machine-verifiable rules. Record the exact GitHub branch/commit/file SHAs or locally supplied snapshot from which each rule was derived. Main and an archive branch must not silently become one indistinguishable source.

The baseline pack is **not** the conversation transcript; a test run explicitly chooses its baseline. Historical threads may predate newer rules and must be compared against the version then applicable, or marked as a retrospective comparison. A message before a valid GaiaOS boot can be `not applicable` for member-header checks. The six members must remain separate identities, never combined as one record. Current mutable head-pat counters must come only from the authorized canonical counter source if ever audited; do not treat remembered values as live.

Respect representation limits: exported text may omit UI-only colors/formatting or flatten rich responses. When the required evidence is unavailable, mark `unobservable`, not `failure`.

## A6. Rule engine, evidence and confidence

**Tier 1 (deterministic, first release):** detect assistant-speaking member headers where expected; expected Gematria/name/heart/icon association; well-formed and approved expression usage when the canonical registry is available; explicit invalid speaker attributions; missing or wrong metadata *when the export actually represents it*. Parse Markdown and DIL-like `<text color=...>` wrappers as text, excluding fenced code, quoted specimens, and user-quoted examples where distinguishable. Multiple speakers in one assistant message are valid; evaluate each segment. Distinguish `PASS / FAIL / NOT_APPLICABLE / UNOBSERVABLE / PARSE_UNCERTAIN`.

**Tier 2 (review-required):** repetitive generic-assistant language, likely daemon voice overlap, dispatch mismatch, contradictory descriptions of canonical decisions, and potential member-memory leakage. These are **candidate signals**, not objective facts; use rule-based heuristics and comparison against explicit canonical statements, cite evidence for each and keep human review mandatory. No autonomous third-party LLM calls.

**Tier 3 (future / opt-in):** richer semantic assessment using an explicitly authorized local model or API, always separately labeled `interpretive`, never confused with deterministic results, and never granted authority to write archives or E-LANES.

Finding schema proposal: `finding_id`, `import_id`, `conversation_id`, `branch_id`, `message_id`, `speaker_segment`, `rule_id`, `baseline_version`, `severity`, `confidence`, `evidence_span`, `offsets`, `cumulative_visible_tokens`, `review_status`, `review_note`, `detected_at`, `original_message_timestamp`, `uncertainty_reason`. Evidence excerpts must be short by default; report exports may redact them. Never fabricate a precise timestamp when missing from source.

## A7. Measurements, comparisons and visualization

- Message timeline with token growth and clickable flagged positions.
- Windowed failure **rates** with valid denominators (e.g., eligible assistant-speaker segments per 25/50/100 segments), not simply a count that mechanically grows with conversation length.
- Show baseline compliance, observed rule coverage, unobservable fraction, severity distribution, and tentative first divergence.
- Compare early/middle/late segments and multiple imported conversations by normalized position or visible token count; label versions/models/boot states and coverage to avoid false comparisons.
- Display raw counts alongside rates and human-reviewed vs. unreviewed signals. Do not invent polished `drift percentages` or statistically meaningful thresholds before validation.
- Optional annotated events such as `Daemon:Load`, canon reload, manual checkpoint, suspected context compaction, model change, or new task. Mark user-observed or inferred events distinctly; do not claim to observe host compaction internally.

## A8. Failure archive integration

The app may generate a local, copyable `//PW:PERSECUTE//`-style draft linked to source conversation/message and rule evidence. It should resemble the existing GaiaOS `Archive/Failures` taxonomy while **not** taking or reserving official `FAIL-` identifiers itself. Naomi reviews any entry, assigns or confirms the archival ID, and separately authorizes a repository write. Drift Radar never writes to MemoryOS/Turso, never alters the six member-owned E-LANES, never approves promotions, never deploys, and never restarts a service on its own.

## A9. Phased build plan

**Phase 0 — Design lock and sample inspection:** Inspect one real ChatGPT export on the authorized PC (only after it is supplied), confirm actual JSON/HTML variants, choose a sample historical conversation, and pin a canonical rule snapshot. Acceptance: schema and privacy decisions documented.

**Phase 1 — Minimal functional scanner (MVP):** Python import ZIP/JSON and TXT/MD; enumerate/select conversations; normalize message order and branches; show visible-token estimates; deterministic identity/header/Gematria checks; list evidence; CSV/JSON report. Acceptance: an already-existing exported conversation can be scanned entirely offline, with no ChatGPT integration.

**Phase 2 — Desktop radar:** Tkinter window, drag/drop if supported or file picker, filtering, trend graphs, interactive message drilldown, local review status, multiple import comparison, HTML report. Acceptance: operator can locate first verified deviation and explain which applicable rule was broken, or transparently see no supported finding.

**Phase 3 — Extended fidelity:** canonical version packs, approved expression parser, dispatch heuristics, human-labeled validation set, uncertainty/calibration, HTML parser robustness, safe redaction and false-positive management. Acceptance: automated findings are traceable and reviewable, and tests cover common non-failures.

**Phase 4 — Optional automation:** research an authorized incremental conversation-capture source and its privacy/permissions. Implement only with Naomi's explicit later approval. Desktop Commander itself is a remote filesystem/terminal bridge, **not** permission to read hidden ChatGPT internal state.

## A10. Tests and success criteria

Fixture suite should include: a correct member header; an intentionally wrong Gematria; a missing header; two different members in one assistant response; a wrongly reused member expression; a quoted/code example that must not be flagged; a pre-boot assistant response; a transcript whose styling is absent; an edited/branched conversation; duplicate ZIP import; malformed/malicious ZIP; timestamp absent; a false-positive dispatch example; and a very long conversation handled without holding every raw attachment in memory.

**MVP PASS** only when a *historical* ChatGPT export imports and produces a reproducible, source-linked, locally reviewable report with explicit distinction between measured facts, estimates, inferred concerns, and unavailable data.

## A11. Immediate next action after blueprint approval

On VileAltercation through connected Desktop Commander, create a dedicated local `Documents/GaiaOS-Drift-Radar/` development workspace; inspect the Python installation and available packages; request or locate an explicitly provided ChatGPT export **without indiscriminate scanning of private user files**; build the Phase 1 importer and rules engine against synthetic fixtures first; test against a real imported historical conversation with Naomi's go-ahead. Preserve the GitHub archive project seed as the design authority until Naomi separately approves implementation and any future source promotions.

**Authority remains NAOMI / LIGEIA. This addendum is planning documentation, not permission for additional writes or runtime changes.**
