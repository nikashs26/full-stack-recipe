# Root-level Dockerfile that builds and runs the real backend (backend/app_railway.py)

FROM public.ecr.aws/docker/library/python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# Workdir
WORKDIR /app

# Copy entire repository (ensures backend/ is present in all build contexts)
COPY . .

# Install backend requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-railway.txt

# Non-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose
EXPOSE $PORT

# Run the full backend app
CMD gunicorn backend.app_railway:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100
