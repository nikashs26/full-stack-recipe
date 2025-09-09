# Use Python 3.11 slim image for smaller size and faster builds
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-railway.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (backend folder)
COPY . .

# ChromaDB will be created and populated from sync data on startup

# Sync data will be created programmatically
# No need to copy sync data file during build

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Create data directory for persistent storage and give app user access
RUN mkdir -p /app/data/chroma_db && \
    chown -R app:app /app && \
    chmod -R 755 /app/data

USER app

# Expose port (Railway will override this)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Run the application with ChromaDB - Updated to use app_railway.py with proper database
# This will enable recipe uploads via API and use persistent storage
CMD gunicorn app_railway:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100
