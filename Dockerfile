FROM python:3.12-slim AS base

# ─── Environment ──────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EMBEDDING_MODEL="sentence-transformers/paraphrase-xlm-r-multilingual-v1" \
    CHROMA_COLLECTION="qreen_knowledge" \
    QREEN_DOCS_DIR="/app/docs"

# ─── System Dependencies ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ─── Working Directory ────────────────────────────────
WORKDIR /app

# ─── Install Python Dependencies ──────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install uvicorn[standard]

# ─── Copy Application Code ────────────────────────────
COPY src/ ./src/
COPY api/ ./api/
COPY docs/ ./docs/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY config/ ./config/

# ─── Create necessary directories ─────────────────────
RUN mkdir -p .chroma_knowledge .telemetry_data

# ─── Pre-download embedding model (optional, speeds up first run) ───
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/paraphrase-xlm-r-multilingual-v1')" 2>/dev/null || true

# ─── Non-root User for Security ───────────────────────
RUN useradd -m -u 1000 qreen && \
    chown -R qreen:qreen /app
USER qreen

# ─── Expose Port ──────────────────────────────────────
EXPOSE 8000

# ─── Health Check ─────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# ─── Start Command ────────────────────────────────────
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
