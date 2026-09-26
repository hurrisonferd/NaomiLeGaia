FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    MEMCONOS_DB_PATH=/data/memconos.db \
    GAIAOS_WORKSPACE_ROOT=/data/gaiaos-workspace

WORKDIR /app

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/gaiaos_api.py ./gaiaos_api.py
COPY api/gaiaos_context_runtime.py ./gaiaos_context_runtime.py
COPY api/legacy_memory_reader.py ./legacy_memory_reader.py
COPY api/gaiaos_memory_mode.py ./gaiaos_memory_mode.py
COPY api/gaiaos_memory_gateway.py ./gaiaos_memory_gateway.py
COPY api/gaiaos_bigbang_readiness.py ./gaiaos_bigbang_readiness.py
COPY api/gaiaos_historical_evidence_audit.py ./gaiaos_historical_evidence_audit.py
COPY api/gaiaos_historical_audit_console.py ./gaiaos_historical_audit_console.py
COPY api/gaiaos_one_click_readiness.py ./gaiaos_one_click_readiness.py
COPY api/gaiaos_one_click_console.py ./gaiaos_one_click_console.py
COPY api/gaiaos_one_click_readiness.py ./gaiaos_one_click_readiness.py
COPY api/gaiaos_one_click_console.py ./gaiaos_one_click_console.py
COPY api/gaiaos_lazy_diagnostics.py ./gaiaos_lazy_diagnostics.py
COPY api/gaiaos_chat_memory.py ./gaiaos_chat_memory.py
COPY api/galaxy_frontdoor_context.py ./galaxy_frontdoor_context.py
COPY api/gaiaos_app.py ./gaiaos_app.py
COPY api/memcon_runtime.py ./memcon_runtime.py
COPY api/galaxy_production.py ./galaxy_production.py
COPY api/galaxy_quality.py ./galaxy_quality.py
COPY api/galaxy_phase3_exit.py ./galaxy_phase3_exit.py
COPY api/galaxy_phase4.py ./galaxy_phase4.py
COPY api/galaxy_phase5.py ./galaxy_phase5.py
COPY api/galaxy_phase5_controls.py ./galaxy_phase5_controls.py
COPY api/galaxy_phase6.py ./galaxy_phase6.py
COPY api/galaxy_phase6_controls.py ./galaxy_phase6_controls.py
COPY api/galaxy_phase7.py ./galaxy_phase7.py
COPY api/galaxy_phase7_tombstone.py ./galaxy_phase7_tombstone.py
COPY api/galaxy_phase7_tombstone_shadow.py ./galaxy_phase7_tombstone_shadow.py
COPY api/galaxy_phase7_isolated_restore.py ./galaxy_phase7_isolated_restore.py
COPY api/augury_ritual.py ./augury_ritual.py
COPY api/augury_semantic_sample.py ./augury_semantic_sample.py
COPY api/augury_semantic_receipts.py ./augury_semantic_receipts.py
COPY api/augury_semantic_collision.py ./augury_semantic_collision.py
COPY api/augury_semantic_retrieval.py ./augury_semantic_retrieval.py
COPY api/memcon_entrypoint.py ./memcon_entrypoint.py
COPY api/browser_memcon_bridge.py ./browser_memcon_bridge.py
COPY api/solo_chat_runtime.py ./solo_chat_runtime.py
COPY api/host_memory_gateway.py ./host_memory_gateway.py
COPY api/gaiaos_verification.py ./gaiaos_verification.py
COPY api/vaskon_runtime.py ./vaskon_runtime.py
COPY GaiaOS ./GaiaOS

EXPOSE 10000

CMD ["sh", "-c", "uvicorn browser_memcon_bridge:app --host 0.0.0.0 --port ${PORT:-10000}"]
