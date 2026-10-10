# GuruSetu backend image. Owner: P1 (T0.P1.1).
# Spec: docs/phases/phase-0-setup.md T0.P1.1, docs/06-ai/ai-system.md §5,
#       docs/10-devops/environments-and-deployment.md §2.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# MDL-02 model cache. Set before the bake so the download lands in $HF_HOME/hub,
# which is exactly where SentenceTransformer(EMBEDDING_MODEL) looks at runtime.
# Do not pass cache_folder= here: it would write to /models instead of /models/hub
# and the runtime load would miss the cache and try the network (RISK-08, FM-08).
ENV HF_HOME=/models

WORKDIR /app

# CPU-only torch first, from PyTorch's own index: the PyPI wheel is the CUDA build
# (multi-GB, useless here). [VERIFIED 2026-10-10: cp312 manylinux wheel present]
RUN pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Bake the 384-d embedding model into the image so the demo runs with the network
# off (NFR-04, TEST-52).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# After the bake, never reach for the network to resolve a model: a missing or
# changed EMBEDDING_MODEL fails fast instead of hanging at startup.
ENV HF_HUB_OFFLINE=1

COPY app/ ./app/
COPY schema/ ./schema/
COPY scripts/ ./scripts/
COPY seed/ ./seed/
COPY extraction_cache/ ./extraction_cache/
# pyproject carries the ruff and pytest settings; tests so the documented
# `docker compose exec backend pytest -q` works inside the container.
COPY pyproject.toml ./
COPY tests/ ./tests/

# One worker: the rate limiter and BackgroundTasks assume a single process (A-13).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
