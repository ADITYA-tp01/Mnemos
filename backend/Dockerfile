# Build context is the project root (see docker-compose.yml) so that both
# backend/ and scripts/ (used by swarm.py) are available and the package
# path matches local runs: `uvicorn backend.app.main:app`.
FROM python:3.11-slim

WORKDIR /app

# curl is used by the container healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
