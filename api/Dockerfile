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
COPY api/augury_ritual.py ./augury_ritual.py
COPY api/memcon_entrypoint.py ./memcon_entrypoint.py
COPY api/browser_memcon_bridge.py ./browser_memcon_bridge.py
COPY api/solo_chat_runtime.py ./solo_chat_runtime.py
COPY api/host_memory_gateway.py ./host_memory_gateway.py
COPY api/gaiaos_verification.py ./gaiaos_verification.py
COPY api/vaskon_runtime.py ./vaskon_runtime.py
COPY GaiaOS ./GaiaOS

EXPOSE 10000

CMD ["sh", "-c", "uvicorn browser_memcon_bridge:app --host 0.0.0.0 --port ${PORT:-10000}"]
