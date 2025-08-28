# Root-level Dockerfile that builds the real backend (backend/app_railway.py)
# Copies entire repo to avoid path issues in different build contexts

FROM public.ecr.aws/docker/library/python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# System deps
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy backend requirements first and install deps (more reliable in CI)
COPY backend/requirements-railway.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy entire repository
COPY . .

# Non-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose
EXPOSE $PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/api/health || exit 1

# Command: run the full backend app
CMD gunicorn backend.app_railway:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100
