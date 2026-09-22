"""MemconOS durable runtime backend for MemoryOS and MemberContinuityOS."""
from __future__ import annotations

import json
import os
import re
import sqlite3

try:
    import libsql
except ImportError:  # Local development may intentionally omit the remote driver.
    libsql = None
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("MEMCONOS_DB_PATH", "/data/memconos.db"))
SCHEMA_VERSION = "memconos.runtime.v2"
BOOT_ID = "BOOT-" + uuid.uuid4().hex
RENDER_INSTANCE_ID = os.getenv("RENDER_INSTANCE_ID", "").strip()
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
STORAGE_BACKEND = "turso_libsql" if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN else "local_sqlite"
_INITIALIZED = False

def _process_fingerprint() -> dict[str, Any]:
    """Return observable OS-level facts for the currently running carrier process."""
    pid = os.getpid()
    proc_start_ticks = None
    try:
        # Linux /proc/<pid>/stat field 22 is process start time in clock ticks
        # since system boot. It distinguishes PID reuse across process lifetimes.
        stat_fields = Path(f"/proc/{pid}/stat").read_text().split()
        proc_start_ticks = stat_fields[21] if len(stat_fields) > 21 else None
    except (OSError, IndexError):
        pass
    return {
        "pid": pid,
        "proc_start_ticks": proc_start_ticks,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_dict(row: Any, cursor: Any = None) -> dict[str, Any] | None:
    if row is None:
        return None
    if hasattr(row, "keys"):
        return dict(row)
    description = getattr(cursor, "description", None)
    if description:
        names = []
        for col in description:
            if isinstance(col, (tuple, list)):
                names.append(str(col[0]))
            else:
                name = getattr(col, "name", None)
                names.append(str(name if name is not None else col))
        return {name: value for name, value in zip(names, row)}
    raise TypeError("Database row could not be mapped to column names")
def _execute_read(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    """Execute a read using the driver's native positional binding."""
    return conn.execute(sql, params)


def _fetchone_dict(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    cursor = _execute_read(conn, sql, params)
    return _row_dict(cursor.fetchone(), cursor)


def _fetchall_dicts(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = _execute_read(conn, sql, params)
    return [_row_dict(row, cursor) for row in cursor.fetchall()]


def _db():
    """Open the configured storage backend.

    Turso is selected only when both remote credentials are present. Otherwise
    local SQLite remains available for development. Production callers can
    inspect storage_status() and must not describe local ephemeral storage as
    durable merely because it is writable.
    """
    if STORAGE_BACKEND == "turso_libsql":
        if libsql is None:
            raise RuntimeError("Turso credentials are configured but the libsql driver is unavailable")
        conn = libsql.connect(database=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def storage_status() -> dict[str, Any]:
    """Return non-secret facts about the active memory storage backend."""
    return {
        "backend": STORAGE_BACKEND,
        "remote_configured": bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN),
        "database_url_present": bool(TURSO_DATABASE_URL),
        "auth_token_present": bool(TURSO_AUTH_TOKEN),
        "local_path": str(DB_PATH) if STORAGE_BACKEND == "local_sqlite" else None,
        "claim_ceiling": (
            "Remote credentials are configured; durability still requires a post-restart canary PASS."
            if STORAGE_BACKEND == "turso_libsql"
            else "Local SQLite is writable but may be ephemeral on the current carrier."
        ),
    }


def _execute_script(conn, script: str) -> None:
    """Execute our simple semicolon-delimited schema on SQLite-compatible drivers."""
    for statement in script.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)


def initialize() -> None:
    """Initialize the schema once per carrier process, not before every query."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _db() as conn:
        _execute_script(conn,
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                record_id TEXT PRIMARY KEY,
                authority TEXT NOT NULL,
                record_type TEXT NOT NULL,
                scope TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                supersedes TEXT,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_records(scope);
            CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_records(status);
            CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_records(created_at);

            CREATE TABLE IF NOT EXISTS memory_relations (
                edge_id TEXT PRIMARY KEY,
                source_record_id TEXT NOT NULL,
                target_record_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                strength REAL NOT NULL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL DEFAULT '{}',
                classifier TEXT NOT NULL,
                authority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                verified_at TEXT,
                FOREIGN KEY(source_record_id) REFERENCES memory_records(record_id),
                FOREIGN KEY(target_record_id) REFERENCES memory_records(record_id)
            );
            CREATE INDEX IF NOT EXISTS idx_galaxy_rel_source ON memory_relations(source_record_id);
            CREATE INDEX IF NOT EXISTS idx_galaxy_rel_target ON memory_relations(target_record_id);
            CREATE INDEX IF NOT EXISTS idx_galaxy_rel_status ON memory_relations(status);

            CREATE TABLE IF NOT EXISTS memory_gravity (
                record_id TEXT PRIMARY KEY,
                gravity_score REAL NOT NULL,
                score_version TEXT NOT NULL,
                components_json TEXT NOT NULL,
                reason_json TEXT NOT NULL,
                calculated_at TEXT NOT NULL,
                previous_score REAL,
                FOREIGN KEY(record_id) REFERENCES memory_records(record_id)
            );

            CREATE TABLE IF NOT EXISTS memory_importance (
                record_id TEXT PRIMARY KEY,
                gate_units INTEGER NOT NULL,
                model_version TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                authority TEXT NOT NULL,
                previous_units INTEGER,
                FOREIGN KEY(record_id) REFERENCES memory_records(record_id)
            );

            CREATE TABLE IF NOT EXISTS memory_lifecycle (
                record_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                authority TEXT NOT NULL,
                receipt_id TEXT,
                FOREIGN KEY(record_id) REFERENCES memory_records(record_id)
            );

            CREATE TABLE IF NOT EXISTS memory_syntheses (
                synthesis_record_id TEXT PRIMARY KEY,
                source_record_ids_json TEXT NOT NULL,
                method TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                authority TEXT NOT NULL,
                FOREIGN KEY(synthesis_record_id) REFERENCES memory_records(record_id)
            );

            CREATE TABLE IF NOT EXISTS runtime_receipts (
                receipt_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                record_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                result TEXT NOT NULL,
                detail TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS session_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );
            CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_session_events_actor ON session_events(actor);

            CREATE TABLE IF NOT EXISTS memory_candidates (
                candidate_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                authority TEXT NOT NULL,
                record_type TEXT NOT NULL,
                scope TEXT NOT NULL,
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                owner TEXT NOT NULL,
                why_material TEXT NOT NULL,
                other_voices TEXT NOT NULL,
                tension TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                duplicate_of TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                promoted_record_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_candidates_status ON memory_candidates(status);
            CREATE INDEX IF NOT EXISTS idx_candidates_fingerprint ON memory_candidates(fingerprint);
            CREATE TABLE IF NOT EXISTS solo_sessions (
                session_id TEXT PRIMARY KEY,
                daemon TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_solo_sessions_daemon ON solo_sessions(daemon);
            """
        )
    _INITIALIZED = True


def _receipt(operation: str, record_id: str, result: str, detail: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"MEMREC-{uuid.uuid4().hex}",
        "operation": operation,
        "record_id": record_id,
        "timestamp": _now(),
        "result": result,
        "detail": detail,
        "runtime": SCHEMA_VERSION,
    }
    with _db() as conn:
        conn.execute(
            "INSERT INTO runtime_receipts VALUES (?, ?, ?, ?, ?, ?)",
            (receipt["receipt_id"], operation, record_id, receipt["timestamp"], result, json.dumps(receipt)),
        )
    return receipt


def write_record(*, authority: str, record_type: str, scope: str, statement: str,
                 source: str, status: str = "ACTIVE", version: str = "1",
                 supersedes: str | None = None, notes: str = "",
                 approved: bool = False, record_id: str | None = None) -> dict[str, Any]:
    if authority != "NAOMI":
        raise PermissionError("Memory writes require authority=NAOMI")
    if not approved:
        raise PermissionError("Memory writes require explicit Naomi approval")
    if not statement.strip():
        raise ValueError("statement must not be empty")
    if not source.strip():
        raise ValueError("source must not be empty")
    initialize()
    record_id = record_id or f"MEM-{uuid.uuid4().hex}"
    created = _now()
    with _db() as conn:
        conn.execute(
            "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record_id, authority, record_type, scope, statement, source, status,
             version, created, created, supersedes, notes),
        )
    return {"record": get_record(record_id), "receipt": _receipt("WRITE", record_id, "SUCCESS", "Written to configured runtime store")}


def get_record(record_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn, "SELECT * FROM memory_records WHERE record_id = ?", (record_id,))
        if row is None and STORAGE_BACKEND == "turso_libsql":
            visible = _fetchall_dicts(conn, "SELECT * FROM memory_records")
            row = next((item for item in visible if item.get("record_id") == record_id), None)
    return row


def search_records(query: str, limit: int = 20, scope: str | None = None) -> dict[str, Any]:
    """Search durable records while preserving query semantics inside an optional scope.

    Every non-empty query term must match at least one indexed text field on the
    same record. Supplying scope narrows the candidate population; it never
    disables query filtering.
    """
    initialize()
    terms = [term.strip().lower() for term in query.split() if term.strip()]
    limit = max(1, min(int(limit), 100))

    clauses: list[str] = []
    params: list[Any] = []

    if scope:
        clauses.append("scope = ?")
        params.append(scope)

    for term in terms:
        pattern = f"%{term}%"
        clauses.append(
            "(lower(statement) LIKE ? OR lower(notes) LIKE ? OR lower(record_id) LIKE ? OR lower(scope) LIKE ?)"
        )
        params.extend([pattern, pattern, pattern, pattern])

    sql = "SELECT * FROM memory_records"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with _db() as conn:
        rows = _fetchall_dicts(conn, sql, tuple(params))
    return {
        "records": rows,
        "count": len(rows),
        "runtime": SCHEMA_VERSION,
        "query_terms_applied": terms,
        "scope_applied": scope,
        "query_filter_active": bool(terms),
    }


GALAXY_QUERY_RELEVANCE_MODEL_VERSION = "galaxy.query-relevance.explainable.v1"

GALAXY_QUERY_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "could", "does", "do",
    "ever", "for", "from", "how", "i", "in", "is", "it", "like", "much", "of",
    "on", "or", "should", "that", "the", "this", "to", "what", "when", "where",
    "which", "who", "why", "with", "would", "act", "become",
}

GALAXY_QUERY_CONCEPT_ALIASES = {
    "galaxy": "galaxy",
    "memory": "memory",
    "memories": "memory",
    "recall": "memory",
    "remember": "memory",
    "retrieval": "memory",
    "retrieve": "memory",
    "gravity": "gravity",
    "influence": "influence",
    "influential": "influence",
    "importance": "influence",
    "important": "influence",
    "prominence": "influence",
    "affect": "influence",
    "affects": "influence",
    "context": "context",
    "contextual": "context",
    "authority": "authority",
    "permission": "authority",
    "permit": "authority",
    "allowed": "authority",
    "allow": "authority",
    "grant": "authority",
    "govern": "authority",
    "governs": "authority",
    "truth": "truth",
    "true": "truth",
    "correct": "truth",
    "estimate": "estimate",
    "estimated": "estimate",
}

# These are deliberately narrow disambiguators for obvious external-domain uses
# represented in the Phase-2 adversarial suite. They do not claim universal
# domain classification.
GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS = {
    "planetary", "trajectory", "trajectories", "falling", "advertising",
}


def _galaxy_query_tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if token and token not in GALAXY_QUERY_STOPWORDS
    ]


def _galaxy_query_concept(token: str) -> str:
    return GALAXY_QUERY_CONCEPT_ALIASES.get(token, token)


def galaxy_query_relevance(record: dict[str, Any], query: str) -> dict[str, Any]:
    """Explain bounded query relevance without using gravity or importance.

    This is intentionally conservative and inspectable. It is not a claim of
    universal semantic understanding. RELEVANT records may enter the Phase-3
    candidate pool; AMBIGUOUS records are surfaced for inspection but are not
    silently admitted; IRRELEVANT records are excluded.
    """
    query_tokens = _galaxy_query_tokens(query)
    statement_tokens = _galaxy_query_tokens(
        f"{record.get('statement') or ''} {record.get('notes') or ''}"
    )

    record_concepts = {_galaxy_query_concept(token) for token in statement_tokens}
    if str(record.get("scope") or "").lower() == "memoryos":
        # Scope supplies a real domain fact, not a fabricated lexical match.
        record_concepts.add("memory")

    matches = []
    unmatched = []
    for token in query_tokens:
        concept = _galaxy_query_concept(token)
        if token in statement_tokens or concept in record_concepts:
            matches.append({"token": token, "concept": concept})
        else:
            unmatched.append({"token": token, "concept": concept})

    matched_count = len(matches)
    meaningful_count = len(query_tokens)
    coverage = (matched_count / meaningful_count) if meaningful_count else 0.0
    distinct_matched_concepts = sorted({item["concept"] for item in matches})
    external_domain_terms = sorted(
        token for token in query_tokens if token in GALAXY_QUERY_EXTERNAL_DOMAIN_TERMS
    )

    if not meaningful_count:
        classification = "AMBIGUOUS"
        rationale = "No meaningful query terms remain after normalization."
    elif external_domain_terms:
        classification = "IRRELEVANT"
        rationale = (
            "The query contains an explicit external-domain disambiguator from the bounded "
            "Phase-2 relevance model; shared words cannot admit the record."
        )
    elif meaningful_count == 1 and matched_count == 1:
        classification = "AMBIGUOUS"
        rationale = (
            "A one-term match is too ambiguous for automatic candidate admission."
        )
    elif matched_count >= 2 and coverage >= 0.60:
        classification = "RELEVANT"
        rationale = (
            "Multiple meaningful query terms/concepts match with sufficient coverage."
        )
    elif matched_count >= 3 and coverage >= 0.50:
        classification = "RELEVANT"
        rationale = (
            "At least three meaningful concepts match despite additional unmatched wording."
        )
    elif matched_count >= 1 and coverage >= 0.35:
        classification = "AMBIGUOUS"
        rationale = (
            "Some relevance signal exists, but not enough for automatic admission."
        )
    else:
        classification = "IRRELEVANT"
        rationale = "Insufficient query-to-record concept coverage."

    return {
        "model_version": GALAXY_QUERY_RELEVANCE_MODEL_VERSION,
        "record_id": record.get("record_id"),
        "query": query,
        "classification": classification,
        "query_candidate_eligible": classification == "RELEVANT",
        "coverage": round(coverage, 6),
        "meaningful_query_terms": query_tokens,
        "matched_terms": matches,
        "unmatched_terms": unmatched,
        "matched_concepts": distinct_matched_concepts,
        "external_domain_terms": external_domain_terms,
        "gravity_used": False,
        "importance_used": False,
        "agreement_inferred": False,
        "rationale": rationale,
        "evidence_ceiling": (
            "Bounded explainable relevance heuristic v1; passing this gate does not prove "
            "claim agreement, truth, authority, or universal semantic understanding."
        ),
    }


def galaxy_phase3_candidate_pool(query: str, *, scope: str = "MemoryOS", limit: int = 20) -> dict[str, Any]:
    """Build the relevance-qualified pool that future Phase-3 modifiers may rerank.

    Scope narrows the inspected population. Query relevance then determines
    candidate admission without consulting gravity or explicit importance.
    """
    initialize()
    scan_limit = max(20, min(max(int(limit) * 5, 50), 100))
    with _db() as conn:
        rows = _fetchall_dicts(
            conn,
            "SELECT * FROM memory_records WHERE scope=? ORDER BY created_at DESC LIMIT ?",
            (scope, scan_limit),
        )

    relevant = []
    ambiguous = []
    irrelevant = []
    for row in rows:
        relevance = galaxy_query_relevance(row, query)
        item = {
            "record_id": str(row.get("record_id")),
            "statement": row.get("statement"),
            "scope": row.get("scope"),
            "relevance": relevance,
        }
        if relevance["classification"] == "RELEVANT":
            relevant.append(item)
        elif relevance["classification"] == "AMBIGUOUS":
            ambiguous.append(item)
        else:
            irrelevant.append(item)

    relevant.sort(
        key=lambda item: (
            float(item["relevance"]["coverage"]),
            len(item["relevance"]["matched_concepts"]),
        ),
        reverse=True,
    )
    selected = relevant[: max(1, min(int(limit), 100))]
    record_ids = [item["record_id"] for item in selected]

    return {
        "contract_version": GALAXY_RETRIEVAL_CONTRACT_VERSION,
        "relevance_model_version": GALAXY_QUERY_RELEVANCE_MODEL_VERSION,
        "query": query,
        "scope": scope,
        "scope_eligible_population_count": len(rows),
        "candidate_record_ids": record_ids,
        "candidate_count": len(record_ids),
        "candidates": selected,
        "ambiguous_record_ids": [item["record_id"] for item in ambiguous],
        "ambiguous_count": len(ambiguous),
        "query_filter_active": bool(_galaxy_query_tokens(query)),
        "modifier_stage": "NOT_APPLIED_PHASE2",
        "gravity_is_contractually_confined_to_candidate_pool": True,
        "gravity_reranking_observed": False,
        "gravity_may_introduce_nonmatching_candidates": False,
        "retrieval_weighting_enabled": False,
        "phase3_experimental_weighting_enabled": True,
        "production_weighted_retrieval_enabled": False,
        "eligibility_dimensions": {
            "scope_eligible": "record is inside the requested scope",
            "query_candidate_eligible": "bounded relevance model classified the record RELEVANT",
            "current_context_eligible": "resolved separately by galaxy.governing-state.v1",
            "historical_context_eligible": "resolved separately by galaxy.governing-state.v1",
        },
        "invariants": list(GALAXY_RETRIEVAL_INVARIANTS),
    }



GALAXY_PHASE3_EXPERIMENT_VERSION = "galaxy.phase3.weighted-retrieval.v1"
GALAXY_PHASE3_RELEVANCE_WEIGHT = 0.80
GALAXY_PHASE3_GRAVITY_WEIGHT = 0.20


def galaxy_phase3_weighted_experiment(query: str, *, scope: str = "MemoryOS", limit: int = 10) -> dict[str, Any]:
    """Compare unweighted candidate order with bounded gravity reranking.

    This experiment cannot introduce records outside the query-qualified pool,
    performs no writes, and does not alter ordinary MemoryOS retrieval.
    """
    pool = galaxy_phase3_candidate_pool(query, scope=scope, limit=limit)
    candidates = list(pool.get("candidates", []))
    candidate_ids = [str(item.get("record_id")) for item in candidates]

    gravity_by_id: dict[str, float] = {}
    if candidate_ids:
        placeholders = ",".join("?" for _ in candidate_ids)
        with _db() as conn:
            rows = _fetchall_dicts(
                conn,
                f"SELECT record_id,gravity_score,score_version FROM memory_gravity WHERE record_id IN ({placeholders})",
                tuple(candidate_ids),
            )
        for row in rows:
            gravity_by_id[str(row["record_id"])] = float(row.get("gravity_score") or 0.0)

    control = []
    weighted = []
    for index, item in enumerate(candidates):
        record_id = str(item.get("record_id"))
        relevance = float((item.get("relevance") or {}).get("coverage") or 0.0)
        gravity = max(0.0, min(1.0, gravity_by_id.get(record_id, 0.0)))
        score = (
            GALAXY_PHASE3_RELEVANCE_WEIGHT * relevance
            + GALAXY_PHASE3_GRAVITY_WEIGHT * gravity
        )
        row = {
            "record_id": record_id,
            "statement": item.get("statement"),
            "control_rank": index + 1,
            "query_relevance_coverage": round(relevance, 6),
            "gravity_score": round(gravity, 6),
            "weighted_score": round(score, 6),
        }
        control.append(dict(row))
        weighted.append(dict(row))

    weighted.sort(
        key=lambda item: (
            float(item["weighted_score"]),
            float(item["query_relevance_coverage"]),
            -int(item["control_rank"]),
        ),
        reverse=True,
    )
    for index, item in enumerate(weighted):
        item["weighted_rank"] = index + 1

    weighted_ids = [item["record_id"] for item in weighted]
    same_candidate_set = set(weighted_ids) == set(candidate_ids) and len(weighted_ids) == len(candidate_ids)

    return {
        "schema": "gaiaos.galaxy.phase3-weighted-retrieval-experiment.v1",
        "status": "PHASE3_EXPERIMENT_OBSERVED",
        "authority": "NAOMI",
        "experiment_version": GALAXY_PHASE3_EXPERIMENT_VERSION,
        "query": query,
        "scope": scope,
        "candidate_gate": pool,
        "control_order": control,
        "weighted_order": weighted,
        "weights": {
            "query_relevance_coverage": GALAXY_PHASE3_RELEVANCE_WEIGHT,
            "gravity_score": GALAXY_PHASE3_GRAVITY_WEIGHT,
        },
        "checks": {
            "candidate_set_preserved": same_candidate_set,
            "gravity_introduced_no_candidates": same_candidate_set,
            "zero_writes": True,
            "ordinary_memoryos_retrieval_changed": False,
            "production_weighted_retrieval_enabled": False,
        },
        "proof_boundary": (
            "This is an experimental reranking receipt over the already relevance-qualified "
            "candidate pool. It does not alter ordinary MemoryOS retrieval, grant authority to "
            "retrieved context, prove the coefficients are optimal, or establish universal semantic relevance."
        ),
    }


def update_record(record_id: str, *, authority: str, approved: bool, statement: str | None = None,
                  status: str | None = None, notes: str | None = None,
                  supersedes: str | None = None) -> dict[str, Any]:
    if authority != "NAOMI" or not approved:
        raise PermissionError("Record updates require explicit Naomi approval")
    initialize()
    old = get_record(record_id)
    if old is None:
        raise KeyError(record_id)
    values = {
        "statement": statement if statement is not None else old["statement"],
        "status": status if status is not None else old["status"],
        "notes": notes if notes is not None else old["notes"],
        "supersedes": supersedes if supersedes is not None else old["supersedes"],
        "updated_at": _now(),
    }
    with _db() as conn:
        conn.execute(
            "UPDATE memory_records SET statement=?, status=?, notes=?, supersedes=?, updated_at=? WHERE record_id=?",
            (values["statement"], values["status"], values["notes"], values["supersedes"], values["updated_at"], record_id),
        )
    return {"record": get_record(record_id), "receipt": _receipt("UPDATE", record_id, "SUCCESS", "Updated in configured runtime store")}



GALAXY_RELATION_TYPES = {
    "REINFORCES", "EXTENDS", "EXPLAINS", "EXEMPLIFIES", "CONTRADICTS",
    "REVISES", "SUPERSEDES", "DERIVED_FROM", "CONTEXT_FOR", "ASSOCIATED_WITH",
}
GALAXY_LIFECYCLE_STATES = {"ACTIVE", "BACKGROUND", "ARCHIVED", "COMPRESSED", "PRUNABLE"}
GALAXY_SCORE_VERSION = "galaxy.gravity.shadow.v4.governing-aware"
GALAXY_WEIGHT_PROFILE = "NERGAL_475_PARITY_QUALITY_CONDITIONED_GOVERNING_AWARE"
GALAXY_SHADOW_WEIGHTS = {
    "durable_active": 0.25,
    "verified_graph_degree": 0.117647,
    "verified_relation_strength": 0.132353,
    "provenance_confidence": 0.15,
    "revision_significance": 0.10,
    "explicit_importance": 0.25,
}
GALAXY_IMPORTANCE_MODEL_VERSION = "galaxy.importance.seven-gates.continuous.v1"
GALAXY_IMPORTANCE_CURVE_VERSION = "galaxy.importance.influence.nergal-threshold.v1"
GALAXY_IMPORTANCE_GATES = ("SIN", "NEBO", "ISHTAR", "SHAMMASH", "NERGAL", "MARDUK", "ADAR")
GALAXY_GOVERNING_MODEL_VERSION = "galaxy.governing-state.v1"
GALAXY_RETRIEVAL_CONTRACT_VERSION = "galaxy.retrieval.contract.v1"
GALAXY_RETRIEVAL_INVARIANTS = (
    "QUERY_RELEVANCE_IS_FIRST_CLASS",
    "GRAVITY_MODIFIES_RELEVANCE_NOT_CANDIDATE_ELIGIBILITY",
    "ZERO_QUERY_RELEVANCE_CANNOT_BE_RESCUED_BY_GRAVITY",
    "RETRIEVAL_INFLUENCE != AUTHORITY",
    "QUERY_GATE_ORDER_PROVEN != QUERY_RELEVANCE_QUALITY_PROVEN",
    "QUERY_RELEVANCE != CLAIM_AGREEMENT",
)
GALAXY_SEMANTIC_INVARIANTS = (
    "CONTRIBUTION_PARITY != SEMANTIC_EQUIVALENCE",
    "CONTRIBUTION_PARITY != EVIDENCE_PARITY",
    "CONTRIBUTION_PARITY != AUTHORITY_PARITY",
    "STORAGE_PRECISION != EPISTEMIC_PRECISION",
    "HISTORY_PRESERVED != HISTORY_GOVERNS_PRESENT",
    "REVISES != SUPERSEDES",
    "SUPERSEDED != ERASED",
)
GALAXY_IMPORTANCE_CURVE_ANCHORS = (
    (0, 0.00),
    (1000, 0.08),
    (2000, 0.16),
    (3000, 0.24),
    (4000, 0.34),
    (5000, 0.62),
    (6000, 0.82),
    (7000, 1.00),
)


def galaxy_importance_influence(gate_units: int) -> float:
    """Map one exact Seven Gates position onto Naomi's approved nonlinear influence curve."""
    if isinstance(gate_units, bool):
        raise ValueError("gate_units must be an integer from 0 through 7000")
    try:
        gate_units = int(gate_units)
    except (TypeError, ValueError) as exc:
        raise ValueError("gate_units must be an integer from 0 through 7000") from exc
    if gate_units < 0 or gate_units > 7000:
        raise ValueError("gate_units must be in 0..7000")
    if gate_units == 7000:
        return 1.0

    left_index = gate_units // 1000
    left_units, left_value = GALAXY_IMPORTANCE_CURVE_ANCHORS[left_index]
    right_units, right_value = GALAXY_IMPORTANCE_CURVE_ANCHORS[left_index + 1]
    span = right_units - left_units
    t = (gate_units - left_units) / span
    return round(float(left_value) + ((float(right_value) - float(left_value)) * t), 6)


def galaxy_importance_descriptor(gate_units: int) -> dict[str, Any]:
    """Describe one exact Seven Gates importance position and its approved influence."""
    if isinstance(gate_units, bool):
        raise ValueError("gate_units must be an integer from 0 through 7000")
    try:
        gate_units = int(gate_units)
    except (TypeError, ValueError) as exc:
        raise ValueError("gate_units must be an integer from 0 through 7000") from exc
    if gate_units < 0 or gate_units > 7000:
        raise ValueError("gate_units must be in 0..7000")
    gate_index = 6 if gate_units == 7000 else gate_units // 1000
    linear_normalized_position = round(gate_units / 7000.0, 6)
    return {
        "gate_units": gate_units,
        "gate_position": round(gate_units / 1000.0, 3),
        "display_position": f"{gate_units / 1000.0:.3f}",
        "gate_index": gate_index,
        "gate": GALAXY_IMPORTANCE_GATES[gate_index],
        "linear_normalized_position": linear_normalized_position,
        "normalized_importance": linear_normalized_position,
        "effective_influence": galaxy_importance_influence(gate_units),
        "influence_curve_version": GALAXY_IMPORTANCE_CURVE_VERSION,
        "model_version": GALAXY_IMPORTANCE_MODEL_VERSION,
        "precision_semantics": "EXACT_COORDINATE_NOT_CONFIDENCE_CLAIM",
    }


def galaxy_importance(record_id: str) -> dict[str, Any] | None:
    """Read the explicit Naomi importance signal for one memory."""
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn, "SELECT * FROM memory_importance WHERE record_id=?", (record_id,))
    if row is None:
        return None
    return {**row, **galaxy_importance_descriptor(int(row["gate_units"]))}


def galaxy_set_importance(record_id: str, gate_units: int, *, authority: str, approved: bool) -> dict[str, Any]:
    """Persist one exact Naomi-approved Seven Gates importance signal."""
    if authority != "NAOMI" or not approved:
        raise PermissionError("GALAXY explicit importance requires explicit Naomi approval")
    if get_record(record_id) is None:
        raise KeyError(record_id)
    descriptor = galaxy_importance_descriptor(gate_units)
    previous = galaxy_importance(record_id)
    if previous is not None and int(previous["gate_units"]) == int(descriptor["gate_units"]):
        return {
            "status": "IMPORTANCE_SET",
            "importance": previous,
            "previous": previous,
            "receipt": None,
            "idempotent": True,
            "retrieval_effect": "NONE",
            "gravity_effect": "SHADOW_PREVIEW_ONLY_NO_RETRIEVAL_EFFECT",
        }

    updated_at = _now()
    previous_units = int(previous["gate_units"]) if previous is not None else None
    with _db() as conn:
        if previous is None:
            conn.execute(
                """INSERT INTO memory_importance
                   (record_id,gate_units,model_version,updated_at,authority,previous_units)
                   VALUES (?,?,?,?,?,NULL)""",
                (
                    record_id,
                    int(descriptor["gate_units"]),
                    GALAXY_IMPORTANCE_MODEL_VERSION,
                    updated_at,
                    authority,
                ),
            )
        else:
            conn.execute(
                """UPDATE memory_importance
                   SET gate_units=?, model_version=?, updated_at=?, authority=?, previous_units=?
                   WHERE record_id=?""",
                (
                    int(descriptor["gate_units"]),
                    GALAXY_IMPORTANCE_MODEL_VERSION,
                    updated_at,
                    authority,
                    previous_units,
                    record_id,
                ),
            )

    receipt = _receipt(
        "GALAXY_SET_IMPORTANCE",
        record_id,
        "SUCCESS",
        (
            f"Set explicit importance to {descriptor['display_position']} {descriptor['gate']} "
            f"under {GALAXY_IMPORTANCE_MODEL_VERSION}; retrieval unchanged; active Phase-2 shadow preview may change"
        ),
    )
    return {
        "status": "IMPORTANCE_SET",
        "importance": galaxy_importance(record_id),
        "previous": previous,
        "receipt": receipt,
        "idempotent": False,
        "retrieval_effect": "NONE",
        "gravity_effect": "NONE_UNTIL_WEIGHT_PROFILE_REVISION",
    }



def galaxy_status() -> dict[str, Any]:
    """Read-only GALAXY implementation status. Phase 3 experiment is authorized; production retrieval remains unchanged."""
    initialize()
    with _db() as conn:
        relations = _fetchone_dict(conn, "SELECT COUNT(*) AS n FROM memory_relations")
        gravity = _fetchone_dict(conn, "SELECT COUNT(*) AS n FROM memory_gravity")
        lifecycle = _fetchone_dict(conn, "SELECT COUNT(*) AS n FROM memory_lifecycle")
        syntheses = _fetchone_dict(conn, "SELECT COUNT(*) AS n FROM memory_syntheses")
        importance = _fetchone_dict(conn, "SELECT COUNT(*) AS n FROM memory_importance")
    return {
        "schema": "gaiaos.galaxy.runtime.v1",
        "phase": "PHASE_3_WEIGHTED_RETRIEVAL_EXPERIMENT",
        "mode": "CONTROL_VS_WEIGHTED_EXPERIMENT_PRODUCTION_UNCHANGED",
        "storage": storage_status(),
        "counts": {
            "relations": int((relations or {}).get("n", 0)),
            "gravity_scores": int((gravity or {}).get("n", 0)),
            "lifecycle_rows": int((lifecycle or {}).get("n", 0)),
            "syntheses": int((syntheses or {}).get("n", 0)),
            "importance_signals": int((importance or {}).get("n", 0)),
        },
        "retrieval_weighting_enabled": False,
        "explicit_importance_weighting_enabled": True,
        "active_shadow_weight_profile": GALAXY_WEIGHT_PROFILE,
        "active_shadow_score_version": GALAXY_SCORE_VERSION,
        "importance_model_version": GALAXY_IMPORTANCE_MODEL_VERSION,
        "importance_curve_version": GALAXY_IMPORTANCE_CURVE_VERSION,
        "importance_curve_semantics_active": True,
        "semantic_invariants": list(GALAXY_SEMANTIC_INVARIANTS),
        "retrieval_contract_version": GALAXY_RETRIEVAL_CONTRACT_VERSION,
        "retrieval_invariants": list(GALAXY_RETRIEVAL_INVARIANTS),
        "query_relevance_model_version": GALAXY_QUERY_RELEVANCE_MODEL_VERSION,
        "phase2_status": "CLOSED",
        "phase3_blockers": [],
        "phase3_cleared_checks": [
            "SCOPE_FILTERED_SEARCH_QUERY_TERMS_LIVE_PROVEN",
            "GOVERNING_STATE_V1_LIVE_PROVEN",
            "QUERY_RELEVANCE_FIRST_CLASS_CONTRACT_LIVE_PROVEN",
            "QUERY_RELEVANCE_QUALITY_V1_ADVERSARIAL_LIVE_PROVEN",
        ],
        "phase3_ready_for_authorization": True,
        "phase3_authorized": True,
        "phase3_status": "AUTHORIZED_SOURCE_EXPERIMENT_BEGIN",
        "physical_pruning_enabled": False,
        "authority": "NAOMI",
        "proof_boundary": "Phase 2 is closed and Naomi explicitly authorized Phase 3. Experimental weighted reranking may now be compared against an unweighted control, but ordinary production retrieval remains unchanged until separately deployed and behaviorally proven.",
    }


def galaxy_record(record_id: str) -> dict[str, Any] | None:
    """Return one record with its GALAXY neighborhood without changing state."""
    record = get_record(record_id)
    if record is None:
        return None
    initialize()
    with _db() as conn:
        edges = _fetchall_dicts(conn,
            """SELECT * FROM memory_relations
               WHERE source_record_id=? OR target_record_id=?
               ORDER BY created_at DESC""", (record_id, record_id))
        gravity = _fetchone_dict(conn, "SELECT * FROM memory_gravity WHERE record_id=?", (record_id,))
        lifecycle = _fetchone_dict(conn, "SELECT * FROM memory_lifecycle WHERE record_id=?", (record_id,))
        importance = _fetchone_dict(conn, "SELECT * FROM memory_importance WHERE record_id=?", (record_id,))
    for edge in edges:
        try:
            edge["evidence"] = json.loads(edge.pop("evidence_json"))
        except (TypeError, json.JSONDecodeError):
            edge["evidence"] = {}
    if gravity:
        for field in ("components_json", "reason_json"):
            try:
                gravity[field[:-5]] = json.loads(gravity.pop(field))
            except (TypeError, json.JSONDecodeError):
                gravity[field[:-5]] = {}
    return {
        "record": record,
        "relations": edges,
        "gravity": gravity,
        "lifecycle": lifecycle,
        "importance": ({**importance, **galaxy_importance_descriptor(int(importance["gate_units"]))} if importance else None),
        "retrieval_effect": "NONE_SHADOW_MODE",
    }



def galaxy_governing_state(record_id: str) -> dict[str, Any]:
    """Resolve ordinary-current-context governance without mutating history.

    Direction is canonical GALAXY revision direction:
    B REVISES A / B SUPERSEDES A means B is source and A is target.

    REVISES alone flags changed context but does not displace A from ordinary
    current-context eligibility. A VERIFIED incoming SUPERSEDES edge does.
    The target remains durable and historically retrievable.
    """
    record = get_record(record_id)
    if record is None:
        raise KeyError(record_id)
    initialize()
    with _db() as conn:
        incoming = _fetchall_dicts(
            conn,
            """SELECT edge_id,source_record_id,target_record_id,relation_type,strength,
                      status,authority,verified_at
               FROM memory_relations
               WHERE target_record_id=? AND status='VERIFIED'
                 AND relation_type IN ('REVISES','SUPERSEDES')
               ORDER BY verified_at DESC, created_at DESC""",
            (record_id,),
        )

    revises = [edge for edge in incoming if edge.get("relation_type") == "REVISES"]
    supersedes = [edge for edge in incoming if edge.get("relation_type") == "SUPERSEDES"]
    record_active = str(record.get("status") or "").upper() == "ACTIVE"

    if not record_active:
        state = "NONACTIVE_HISTORICAL"
        current_default_eligible = False
        companion_required = False
    elif supersedes:
        state = "HISTORICAL_SUPERSEDED"
        current_default_eligible = False
        companion_required = True
    elif revises:
        state = "CURRENT_REVISED_CONTEXT"
        current_default_eligible = True
        companion_required = True
    else:
        state = "CURRENT"
        current_default_eligible = True
        companion_required = False

    return {
        "record_id": record_id,
        "model_version": GALAXY_GOVERNING_MODEL_VERSION,
        "state": state,
        "record_status": record.get("status"),
        "current_default_eligible": current_default_eligible,
        "historical_retrieval_eligible": True,
        "revision_companion_required_when_material": companion_required,
        "incoming_verified_revises": revises,
        "incoming_verified_supersedes": supersedes,
        "durable_active_component": 1.0 if current_default_eligible else 0.0,
        "direction_semantics": "B REVISES/SUPERSEDES A => source=B, target=A",
        "authority_boundary": (
            "Governance affects ordinary-current-context eligibility only. "
            "It does not erase the record, alter its historical importance, or grant truth/authority."
        ),
    }


def galaxy_gravity(record_id: str) -> dict[str, Any] | None:
    """Read one stored shadow gravity row without changing retrieval."""
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn, "SELECT * FROM memory_gravity WHERE record_id=?", (record_id,))
    if row is None:
        return None
    for field in ("components_json", "reason_json"):
        try:
            row[field[:-5]] = json.loads(row.pop(field))
        except (TypeError, json.JSONDecodeError):
            row[field[:-5]] = {}
    return row


def galaxy_gravity_preview(record_id: str) -> dict[str, Any]:
    """Calculate the approved Phase-2 NERGAL_475_PARITY shadow score without writing it.

    The score may use Naomi's stored Seven Gates importance through the approved
    nonlinear NERGAL-threshold curve. It remains shadow-only and cannot alter
    ordinary retrieval in Phase 2.
    """
    record = get_record(record_id)
    if record is None:
        raise KeyError(record_id)
    initialize()
    with _db() as conn:
        verified_edges = _fetchall_dicts(
            conn,
            """SELECT relation_type, strength, source_record_id, target_record_id
               FROM memory_relations
               WHERE status='VERIFIED' AND (source_record_id=? OR target_record_id=?)""",
            (record_id, record_id),
        )

    degree = len(verified_edges)
    strengths = [max(0.0, min(float(edge.get("strength") or 0.0), 1.0)) for edge in verified_edges]
    mean_strength = (sum(strengths) / len(strengths)) if strengths else 0.0
    raw_degree_norm = min(degree / 4.0, 1.0)
    degree_norm = raw_degree_norm * mean_strength
    significant_types = {"REVISES", "SUPERSEDES"}
    significant_count = sum(1 for edge in verified_edges if str(edge.get("relation_type") or "") in significant_types)
    revision_significance = min(significant_count / 2.0, 1.0)
    stored_importance = galaxy_importance(record_id)
    governing_state = galaxy_governing_state(record_id)

    explicit_importance = (
        float(stored_importance.get("effective_influence") or 0.0)
        if stored_importance is not None
        else 0.0
    )
    normalized = {
        "durable_active": float(governing_state["durable_active_component"]),
        "verified_graph_degree": degree_norm,
        "verified_relation_strength": mean_strength,
        "provenance_confidence": 1.0 if str(record.get("authority") or "").upper() == "NAOMI" else 0.0,
        "revision_significance": revision_significance,
        "explicit_importance": explicit_importance,
    }
    weights = dict(GALAXY_SHADOW_WEIGHTS)
    components = {}
    for name, value in normalized.items():
        components[name] = {
            "normalized": round(float(value), 6),
            "weight": weights[name],
            "contribution": round(float(value) * weights[name], 6),
        }
    score = round(sum(item["contribution"] for item in components.values()), 6)
    relation_types = sorted({str(edge.get("relation_type") or "") for edge in verified_edges if edge.get("relation_type")})
    reason = {
        "score_meaning": "Present shadow retrieval influence estimate only. It is not truth, authority, or permission.",
        "verified_relation_count": degree,
        "verified_relation_types": relation_types,
        "mean_verified_relation_strength": round(mean_strength, 6),
        "raw_degree_normalized": round(raw_degree_norm, 6),
        "strength_conditioned_degree_normalized": round(degree_norm, 6),
        "verified_graph_degree_semantics": (
            "Capped relation breadth multiplied by mean verified relation strength. "
            "This prevents weak-link count from receiving full breadth credit."
        ),
        "revision_significance_edges": significant_count,
        "revision_significance_types": ["REVISES", "SUPERSEDES"],
        "contradicts_receives_revision_premium": False,
        "governing_state": governing_state,
        "active_weight_profile": GALAXY_WEIGHT_PROFILE,
        "explicit_importance_basis": (
            "A stored Naomi Seven Gates signal is mapped through the approved NERGAL-threshold influence curve "
            "and is active inside the Phase-2 NERGAL_475_PARITY shadow formula. This remains non-authoritative "
            "and has no ordinary retrieval effect."
        ),
        "stored_explicit_importance": stored_importance,
        "omitted_from_current_shadow_profile": {
            "recency": "Excluded to prevent uncalibrated recency domination.",
            "retrieval_usefulness": "Excluded until Phase 3 supplies observed behavioral evidence.",
            "redundancy": "Excluded until correspondence quality is separately tested.",
            "staleness": "Excluded until lifecycle attenuation is implemented and tested.",
        },
        "anti_feedback_guard": "Stored gravity is never used as an input to this score and Phase 2 does not alter retrieval ordering.",
    }
    return {
        "record_id": record_id,
        "gravity_score": score,
        "score_version": GALAXY_SCORE_VERSION,
        "components": components,
        "reason": reason,
        "retrieval_effect": "NONE_SHADOW_MODE",
        "authoritative": False,
    }


def galaxy_calculate_gravity(record_id: str, *, authority: str, approved: bool) -> dict[str, Any]:
    """Persist one explainable shadow score. It has no retrieval effect."""
    if authority != "NAOMI" or not approved:
        raise PermissionError("GALAXY shadow gravity calculation requires explicit Naomi approval")
    preview = galaxy_gravity_preview(record_id)
    previous = galaxy_gravity(record_id)
    if (
        previous is not None
        and previous.get("score_version") == preview.get("score_version")
        and float(previous.get("gravity_score") or 0.0) == float(preview.get("gravity_score") or 0.0)
        and previous.get("components") == preview.get("components")
    ):
        return {
            "status": "SHADOW_SCORED",
            "gravity": previous,
            "previous": previous,
            "receipt": None,
            "idempotent": True,
            "retrieval_effect": "NONE",
            "retrieval_weighting_enabled": False,
            "authority_boundary": "The current identical shadow score was already stored; no new mutation was performed.",
        }
    calculated_at = _now()
    with _db() as conn:
        if previous is None:
            conn.execute(
                """INSERT INTO memory_gravity
                   (record_id,gravity_score,score_version,components_json,reason_json,calculated_at,previous_score)
                   VALUES (?,?,?,?,?,?,NULL)""",
                (
                    record_id,
                    preview["gravity_score"],
                    preview["score_version"],
                    json.dumps(preview["components"], sort_keys=True),
                    json.dumps(preview["reason"], sort_keys=True),
                    calculated_at,
                ),
            )
        else:
            conn.execute(
                """UPDATE memory_gravity
                   SET gravity_score=?, score_version=?, components_json=?, reason_json=?,
                       calculated_at=?, previous_score=?
                   WHERE record_id=?""",
                (
                    preview["gravity_score"],
                    preview["score_version"],
                    json.dumps(preview["components"], sort_keys=True),
                    json.dumps(preview["reason"], sort_keys=True),
                    calculated_at,
                    previous.get("gravity_score"),
                    record_id,
                ),
            )
    receipt = _receipt(
        "GALAXY_SHADOW_GRAVITY",
        record_id,
        "SUCCESS",
        f"Stored explainable {GALAXY_SCORE_VERSION} shadow score; ordinary retrieval unchanged",
    )
    return {
        "status": "SHADOW_SCORED",
        "gravity": galaxy_gravity(record_id),
        "previous": previous,
        "receipt": receipt,
        "retrieval_effect": "NONE",
        "retrieval_weighting_enabled": False,
        "authority_boundary": "This score is non-authoritative and cannot change ordinary retrieval in Phase 2.",
    }


def galaxy_propose_relation(*, source_record_id: str, target_record_id: str,
                            relation_type: str, strength: float, evidence: dict[str, Any],
                            classifier: str = "GALAXY_MANUAL_V1") -> dict[str, Any]:
    """Create a non-authoritative relation proposal. It has no retrieval effect."""
    relation_type = relation_type.strip().upper()
    if relation_type not in GALAXY_RELATION_TYPES:
        raise ValueError(f"Unsupported GALAXY relation type: {relation_type}")
    if source_record_id == target_record_id:
        raise ValueError("A GALAXY relation cannot target itself")
    strength = float(strength)
    if not 0.0 <= strength <= 1.0:
        raise ValueError("Relation strength must be between 0 and 1")
    if get_record(source_record_id) is None or get_record(target_record_id) is None:
        raise KeyError("Both GALAXY relation endpoints must be existing durable memory records")
    initialize()
    with _db() as conn:
        duplicate = _fetchone_dict(conn,
            """SELECT * FROM memory_relations
               WHERE source_record_id=? AND target_record_id=? AND relation_type=? AND status IN ('PROPOSED','VERIFIED')
               ORDER BY created_at DESC LIMIT 1""",
            (source_record_id, target_record_id, relation_type))
        if duplicate:
            return {"status": "EXISTING", "relation": duplicate, "retrieval_effect": "NONE"}
        edge_id = "EDGE-" + uuid.uuid4().hex
        created = _now()
        conn.execute(
            """INSERT INTO memory_relations
               (edge_id,source_record_id,target_record_id,relation_type,strength,status,evidence_json,classifier,authority,created_at,verified_at)
               VALUES (?,?,?,?,?,'PROPOSED',?,?,?, ?,NULL)""",
            (edge_id, source_record_id, target_record_id, relation_type, strength,
             json.dumps(evidence, sort_keys=True), classifier, "NONE", created),
        )
    return {
        "status": "PROPOSED",
        "relation": galaxy_relation(edge_id),
        "retrieval_effect": "NONE",
        "proof_boundary": "A proposed edge is not verified truth and does not alter retrieval.",
    }


def galaxy_relation(edge_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        edge = _fetchone_dict(conn, "SELECT * FROM memory_relations WHERE edge_id=?", (edge_id,))
    if edge is None:
        return None
    try:
        edge["evidence"] = json.loads(edge.pop("evidence_json"))
    except (TypeError, json.JSONDecodeError):
        edge["evidence"] = {}
    return edge


def galaxy_verify_relation(edge_id: str, *, authority: str, approved: bool) -> dict[str, Any]:
    """Naomi may verify a proposed edge. Verification still has no retrieval effect in Phase 1."""
    if authority != "NAOMI" or not approved:
        raise PermissionError("GALAXY relation verification requires explicit Naomi approval")
    edge = galaxy_relation(edge_id)
    if edge is None:
        raise KeyError(edge_id)
    if edge["status"] == "VERIFIED":
        return {"status": "VERIFIED", "relation": edge, "idempotent": True, "retrieval_effect": "NONE"}
    if edge["status"] != "PROPOSED":
        raise ValueError(f"Only PROPOSED relations can be verified; current status={edge['status']}")
    verified_at = _now()
    with _db() as conn:
        conn.execute("UPDATE memory_relations SET status='VERIFIED', authority='NAOMI', verified_at=? WHERE edge_id=?",
                     (verified_at, edge_id))
    receipt = _receipt("GALAXY_VERIFY_RELATION", edge_id, "SUCCESS", "Verified relation in GALAXY shadow graph; retrieval unchanged")
    return {"status": "VERIFIED", "relation": galaxy_relation(edge_id), "receipt": receipt, "retrieval_effect": "NONE"}



def create_session(session_id: str, source: str, subject: str = "") -> None:
    initialize()
    with _db() as conn:
        conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (session_id, source, subject, _now()))


def create_session_event(*, event_id: str, session_id: str, actor: str,
                         event_type: str, statement: str, source: str,
                         relation: str = "PART_OF") -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            "INSERT INTO session_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, session_id, actor, event_type, statement, source, relation, _now()),
        )


def get_session_event(event_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn, "SELECT * FROM session_events WHERE event_id=?", (event_id,))
    return row


def get_session(session_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        session = _fetchone_dict(conn, "SELECT * FROM sessions WHERE session_id=?", (session_id,))
        events = _fetchall_dicts(conn, "SELECT * FROM session_events WHERE session_id=? ORDER BY created_at", (session_id,))
    if session is None:
        return None
    result = session
    result["events"] = events
    return result


def create_memory_candidate(candidate: dict[str, Any]) -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            """INSERT INTO memory_candidates
            (candidate_id,event_id,authority,record_type,scope,statement,source,owner,
             why_material,other_voices,tension,fingerprint,duplicate_of,status,created_at,promoted_record_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
            (
                candidate["candidate_id"], candidate["event_id"], candidate["authority"],
                candidate["record_type"], candidate["scope"], candidate["statement"],
                candidate["source"], candidate["owner"], candidate["why_material"],
                json.dumps(candidate.get("other_voices", [])),
                candidate.get("tension", ""), candidate["fingerprint"],
                candidate.get("duplicate_of"), candidate["status"], candidate["created_at"],
            ),
        )


def get_memory_candidate(candidate_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn, "SELECT * FROM memory_candidates WHERE candidate_id=?", (candidate_id,))
    if row is None:
        return None
    result = row
    result["other_voices"] = json.loads(result["other_voices"])
    return result


def list_memory_candidates(session_id: str | None = None, status: str | None = "CANDIDATE", limit: int = 50, subject: str | None = None) -> dict[str, Any]:
    """List bounded MemoryOS candidates, optionally restricted to one session."""
    initialize()
    limit = max(1, min(int(limit), 100))
    with _db() as conn:
        clauses = []
        params: list[Any] = []
        if session_id:
            clauses.append("e.session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("c.status = ?")
            params.append(status)
        if subject:
            clauses.append("s.subject LIKE ?")
            params.append(f"%{subject}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = _fetchall_dicts(conn,
            f"""SELECT c.*, e.session_id, s.subject
                FROM memory_candidates c
                JOIN session_events e ON e.event_id = c.event_id
                JOIN sessions s ON s.session_id = e.session_id
                {where}
                ORDER BY c.created_at DESC
                LIMIT ?""",
            (*params, limit),
        )
    candidates = []
    for row in rows:
        item = row
        item["other_voices"] = json.loads(item["other_voices"])
        candidates.append(item)
    return {
        "schema": "memconos.runtime.v2",
        "candidates": candidates,
        "count": len(candidates),
        "session_id": session_id,
        "subject_filter": subject,
        "status_filter": status,
        "runtime": SCHEMA_VERSION,
    }


def get_latest_memory_candidate(owner: str, status: str = "CANDIDATE") -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn,
            "SELECT * FROM memory_candidates WHERE owner=? AND status=? ORDER BY created_at DESC LIMIT 1",
            (owner, status),
        )
    if row is None:
        return None
    result = dict(row)
    result["other_voices"] = json.loads(result["other_voices"])
    return result


def find_fingerprint(fingerprint: str) -> str | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn,
            "SELECT record_id FROM memory_records WHERE lower(notes) LIKE ? LIMIT 1",
            (f'"fingerprint": "{fingerprint}"',),
        )
    return row["record_id"] if row else None


def mark_candidate(candidate_id: str, status: str, promoted_record_id: str | None = None) -> None:
    initialize()
    with _db() as conn:
        conn.execute(
            "UPDATE memory_candidates SET status=?, promoted_record_id=? WHERE candidate_id=?",
            (status, promoted_record_id, candidate_id),
        )



def create_solo_session(session_id: str, daemon: str, source: str) -> dict[str, Any]:
    """Create or replace the active dedicated Prime Daemon session for one browser session."""
    initialize()
    daemon = daemon.strip().upper()
    with _db() as conn:
        conn.execute("UPDATE solo_sessions SET active=0 WHERE session_id=?", (session_id,))
        conn.execute(
            "INSERT OR REPLACE INTO solo_sessions(session_id,daemon,source,created_at,active) VALUES(?,?,?,?,1)",
            (session_id, daemon, source, _now()),
        )
    return get_solo_session(session_id)  # type: ignore[return-value]


def get_solo_session(session_id: str) -> dict[str, Any] | None:
    initialize()
    with _db() as conn:
        row = _fetchone_dict(conn,
            "SELECT * FROM solo_sessions WHERE session_id=? AND active=1",
            (session_id,),
        )
    return row


def end_solo_session(session_id: str) -> None:
    initialize()
    with _db() as conn:
        conn.execute("UPDATE solo_sessions SET active=0 WHERE session_id=?", (session_id,))



def restart_canary(token: str | None = None) -> dict[str, Any]:
    """Prove the durable runtime store survives a process restart."""
    initialize()
    marker_id = token.strip() if token else f"RESTART-{uuid.uuid4().hex}"
    if token is None:
        with _db() as conn:
            conn.execute(
                "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    marker_id, "NAOMI", "RESTART_CANARY", "MemconOS",
                    "GaiaOS restart persistence canary",
                    "GaiaOS runtime restart verification",
                    "ACTIVE", "1", _now(), _now(), None,
                    json.dumps({"boot_id": BOOT_ID, "render_instance_id": RENDER_INSTANCE_ID, "process_fingerprint": _process_fingerprint()}),
                ),
            )
        return {
            "schema": SCHEMA_VERSION,
            "status": "ARMED",
            "token": marker_id,
            "boot_id": BOOT_ID,
            "render_instance_id": RENDER_INSTANCE_ID or None,
            "process_fingerprint": _process_fingerprint(),
            "instruction": "Restart or redeploy the service, then call /persistence/canary?token=<token>.",
            "proof_boundary": "Armed only. Persistence is not proven until the token is read after a different process boot.",
        }

    with _db() as conn:
        cursor = _execute_read(
            conn,
            "SELECT notes, created_at FROM memory_records WHERE record_id=? AND record_type='RESTART_CANARY'",
            (marker_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return {
            "schema": SCHEMA_VERSION,
            "status": "FAIL",
            "token": marker_id,
            "boot_id": BOOT_ID,
            "render_instance_id": RENDER_INSTANCE_ID or None,
            "process_fingerprint": _process_fingerprint(),
            "detail": "Restart canary marker was not found in the durable runtime store.",
        }
    saved = json.loads(_row_dict(row, cursor)["notes"])
    prior_boot = str(saved.get("boot_id", ""))
    prior_render_instance = str(saved.get("render_instance_id", ""))
    prior_process = saved.get("process_fingerprint") or {}
    current_process = _process_fingerprint()
    process_changed = bool(prior_process) and (
        prior_process.get("pid") != current_process.get("pid")
        or (
            prior_process.get("proc_start_ticks") is not None
            and current_process.get("proc_start_ticks") is not None
            and prior_process.get("proc_start_ticks") != current_process.get("proc_start_ticks")
        )
    )
    boot_changed = bool(prior_boot) and prior_boot != BOOT_ID
    render_instance_changed = bool(prior_render_instance) and bool(RENDER_INSTANCE_ID) and prior_render_instance != RENDER_INSTANCE_ID
    restarted = boot_changed or render_instance_changed or process_changed
    return {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if restarted else "NOT_RESTARTED",
        "token": marker_id,
        "boot_id": BOOT_ID,
        "prior_boot_id": prior_boot,
        "render_instance_id": RENDER_INSTANCE_ID or None,
        "prior_render_instance_id": prior_render_instance or None,
        "boot_id_changed": boot_changed,
        "render_instance_changed": render_instance_changed,
        "process_fingerprint": current_process,
        "prior_process_fingerprint": prior_process or None,
        "process_fingerprint_changed": process_changed,
        "restart_predicate": "boot_id_changed OR render_instance_changed OR process_fingerprint_changed",
        "marker_created_at": _row_dict(row, cursor)["created_at"],
        "durable_read_observed": True,
        "different_process_boot_observed": restarted,
        "proof_boundary": "PASS proves the marker survived into a different carrier process identity. It does not prove every memory operation is automatically persisted.",
    }

def canary() -> dict[str, Any]:
    initialize()
    canary_id = "GAIA-MEMCON-ALPHA-001"
    existing = get_record(canary_id)
    if existing is None:
        write_record(
            authority="NAOMI", approved=True, record_id=canary_id,
            record_type="CANARY", scope="MemconOS",
            statement="When information fits the MemconOS criteria, record it for future recall.",
            source="GaiaOS/SystemsOS/Core/MemberContinuityOS/MEMCONOS-CANARY.v1.md",
            status="ACTIVE", version="1", notes="Runtime bootstrap canary",
        )
        existing = get_record(canary_id)
    read_receipt = _receipt("READ", canary_id, "SUCCESS", "Canary retrieved from runtime store")
    return {
        "schema": SCHEMA_VERSION,
        "canary_id": canary_id,
        "runtime_store": storage_status(),
        "record": existing,
        "read_receipt": read_receipt,
        "runtime_persistence": True,
        "source_persistence": True,
        "claim_ceiling": "This proves the running service can durably read/write the runtime store. It does not prove automatic capture from every ChatGPT conversation.",
    }
