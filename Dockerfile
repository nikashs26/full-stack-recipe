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

# Copy entire repository (safer for varing build contexts)
COPY . .

# Install backend requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements-railway.txt

# Hint for population script: prefer URL, not file copy
# Set BACKUP_RECIPES_URL in Railway to something like https://your-site.netlify.app/recipes_backup.json

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
