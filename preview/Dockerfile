FROM python:3.12-slim
WORKDIR /app
COPY preview/index.html /app/index.html
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh", "-c", "python -m http.server ${PORT:-8080} --bind 0.0.0.0"]
