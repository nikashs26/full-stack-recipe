# Root-level Dockerfile that builds the real backend (backend/app_railway.py)
# Copies only what's needed reliably and minimizes base layer installs

FROM public.ecr.aws/docker/library/python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy backend sources first into a stable path
COPY backend/ /app/backend/

# Install backend requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements-railway.txt

# Copy the rest of the repo (ignored by .dockerignore as configured)
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
