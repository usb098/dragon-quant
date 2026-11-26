# Temporary dashboard deployment

This Dockerfile builds the React/Vite dashboard from source and serves the generated bundle through the existing FastAPI dashboard service.

## Runtime contract

- The Railway service must keep `preview/Dockerfile` as its Dockerfile path.
- The dashboard is protected by HTTP Basic Auth. `GET /health` remains available to Railway health checks.
- The persistent Railway volume is mounted at `/data`; `DQ_DATA_DIR=/data` keeps the existing cloud SQLite files across deployments.
- Deploying this branch does not copy any database from a developer's local computer. Existing data on the attached Railway volume is preserved.
- Workspace writes remain disabled. Scan/prep collection is explicit and manual from the dashboard; no brokerage order endpoint is exposed.
- The LLM Agent is disabled until `OPENAI_API_KEY` and `DQ_INTELLIGENCE_LLM_ENABLED=1` are configured as server-side Railway variables. The key must never be stored in Git, Docker build arguments, or frontend environment variables.
- Public web research is separately opt-in with `DQ_INTELLIGENCE_WEB_SEARCH=1`; it is off by default.
- User-provided private trading notes, deal slips and distilled knowledge bases are never part of the Docker build context or runtime image. The `/data` volume must not be used as a public file-download surface.

## Local build

From the repository root:

    docker build -f preview/Dockerfile -t dragon-quant-preview .
