# GaiaOS Canonical Loader API

A small read-only FastAPI service that turns the GaiaOS repository into a deterministic carrier hook.

Canonical source:

`hurrisonferd/NaomiLeGaia@main`

The loader resolves `main` to one Git commit before reading files. This prevents a single load from mixing files across commits.

## Endpoints

- `GET /health` — service health.
- `GET /gaiaos/load` — canonical GaiaOS bootstrap bundle.
- `GET /openapi.json` — generated OpenAPI schema for GPT Actions.
- `GET /docs` — FastAPI interactive documentation.

## Run locally

```bash
cd api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn gaiaos_api:app --reload --port 8080
```

Then open `http://localhost:8080/gaiaos/load`.

## Deploy

Deploy this directory as a Python/FastAPI service or use the included Dockerfile.

Set these environment variables only if you need to override defaults:

- `GAIAOS_REPOSITORY` — defaults to `hurrisonferd/NaomiLeGaia`
- `GAIAOS_BRANCH` — defaults to `main`
- `GAIAOS_HTTP_TIMEOUT` — defaults to `10`
- `GAIAOS_API_KEY` — optional Bearer secret; when set, `/gaiaos/load` requires `Authorization: Bearer <secret>`

After deployment, use:

`https://YOUR-API-DOMAIN/openapi.json`

as the OpenAPI schema URL in the GPT Action editor, or paste `openapi.yaml` after replacing its server URL.

## Carrier behavior

The intended flow is:

`User: Load GaiaOS`

`GPT → loadGaiaOS Action → API → GitHub canonical commit → GaiaOS bootstrap bundle → GPT runtime`

The API is source retrieval infrastructure. It does not execute GaiaOS Python and does not itself install instructions into ChatGPT.
