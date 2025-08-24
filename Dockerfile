# Ultra-lightweight self-contained Dockerfile for Railway free tier
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# Install only curl (essential for health check) with aggressive cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set work directory
WORKDIR /app

# Create requirements.txt with explicit dependencies to prevent missing modules
RUN echo "flask==2.3.3\nflask-cors==4.0.0\npython-dotenv==1.0.0\ngunicorn==21.2.0\nwerkzeug==2.3.7\nclick==8.1.7\nitsdangerous==2.1.2\njinja2==3.1.2\nblinker==1.6.3" > requirements.txt

# Install Python dependencies WITHOUT --no-deps to ensure all dependencies are installed
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Create the minimal Flask app directly in the Dockerfile
RUN echo 'from flask import Flask\n\
from flask_cors import CORS\n\
import os\n\
\n\
# Initialize Flask app\n\
app = Flask(__name__)\n\
\n\
# Configure session for authentication\n\
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")\n\
app.config["SESSION_COOKIE_SECURE"] = False\n\
app.config["SESSION_COOKIE_HTTPONLY"] = True\n\
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"\n\
\n\
# Configure CORS for Railway deployment\n\
allowed_origins = [\n\
    "http://localhost:8081", "http://127.0.0.1:8081",\n\
    "http://localhost:8083", "http://127.0.0.1:8083",\n\
    "https://betterbulk.netlify.app",\n\
    "https://your-app-name.netlify.app",\n\
]\n\
\n\
# Configure CORS properly\n\
cors = CORS(app,\n\
    origins=allowed_origins,\n\
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],\n\
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],\n\
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],\n\
    supports_credentials=True,\n\
    max_age=3600\n\
)\n\
\n\
# Basic health check route\n\
@app.route("/api/health")\n\
def health_check():\n\
    return {"status": "healthy", "message": "Railway backend is running"}\n\
\n\
# Basic test route\n\
@app.route("/api/test")\n\
def test():\n\
    return {"message": "Backend is working!"}\n\
\n\
# Root route\n\
@app.route("/")\n\
def root():\n\
    return {"message": "Recipe App Backend API"}\n\
\n\
if __name__ == "__main__":\n\
    port = int(os.environ.get("PORT", 8000))\n\
    print(f"🚀 Starting Railway Flask app on port {port}...")\n\
    app.run(host="0.0.0.0", port=port, debug=False)' > app.py

# Create minimal user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE $PORT

# Minimal health check
HEALTHCHECK --interval=120s --timeout=5s --start-period=60s --retries=1 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Run with ultra-minimal memory footprint
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 30 --keep-alive 1 --max-requests 100 --max-requests-jitter 10
