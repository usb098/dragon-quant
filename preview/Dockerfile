# Build the existing React dashboard, then run its FastAPI backend.
FROM node:22-bookworm-slim AS frontend
WORKDIR /workspace/web_ui/frontend
COPY web_ui/frontend/package.json web_ui/frontend/package-lock.json ./
RUN npm install --include=dev --no-audit --no-fund \
    && test -x node_modules/.bin/tsc \
    && test -x node_modules/.bin/vite
COPY web_ui/frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir ".[web]"
COPY --from=frontend /workspace/web_ui/dist /app/web_ui/dist

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DQ_DATA_DIR=/data DQ_PUBLIC_DEPLOYMENT=1
EXPOSE 8080
CMD ["sh", "-c", "exec python -m uvicorn web_ui.backend.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
