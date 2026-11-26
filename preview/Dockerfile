FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build/web_ui/frontend
COPY web_ui/frontend/package.json web_ui/frontend/package-lock.json ./
# Rewrite the development mirror only inside the image build; keep the tracked lockfile unchanged.
RUN sed -i 's#https://bnpm.byted.org/#https://registry.npmjs.org/#g' package-lock.json \
    && npm ci --no-audit --no-fund --registry=https://registry.npmjs.org

COPY web_ui/frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY . /app
COPY --from=frontend-build /build/web_ui/dist/ /app/web_ui/dist/

RUN pip install --no-cache-dir ".[web]"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DQ_DATA_DIR=/data \
    DQ_PUBLIC_DEPLOYMENT=1

EXPOSE 8080
CMD ["sh", "-c", "exec python -m uvicorn web_ui.backend.app:create_app --factory --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips='*'"]
