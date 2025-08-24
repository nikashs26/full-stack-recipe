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

# Create a simple Flask app with real recipe data
RUN echo 'from flask import Flask, request, jsonify\n\
from flask_cors import CORS\n\
import os\n\
\n\
app = Flask(__name__)\n\
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")\n\
\n\
# Configure CORS\n\
CORS(app, origins=["https://betterbulk.netlify.app", "http://localhost:8081", "http://localhost:8083"])\n\
\n\
# Real recipe data (5 recipes)\n\
RECIPES = [\n\
    {"id": "1", "title": "Budino Di Ricotta", "description": "Italian dessert - 30 minutes", "cuisine": ["Italian"], "image": "https://www.themealdb.com/images/media/meals/1549542877.jpg", "ready_in_minutes": 30, "calories": 420, "protein": 15, "carbs": 60, "fat": 18},\n\
    {"id": "2", "title": "Chicken Alfredo Primavera", "description": "Italian pasta - 30 minutes", "cuisine": ["Italian"], "image": "https://www.themealdb.com/images/media/meals/syqypv1486981727.jpg", "ready_in_minutes": 30, "calories": 740, "protein": 40, "carbs": 63, "fat": 43},\n\
    {"id": "3", "title": "Chilli Prawn Linguine", "description": "Italian seafood - 30 minutes", "cuisine": ["Italian"], "image": "https://www.themealdb.com/images/media/meals/yyxssu1487486469.jpg", "ready_in_minutes": 30, "calories": 420, "protein": 37, "carbs": 43, "fat": 18},\n\
    {"id": "4", "title": "Fettuccine Alfredo", "description": "Italian pasta - 30 minutes", "cuisine": ["Italian"], "image": "https://www.themealdb.com/images/media/meals/0jv5gx1661040802.jpg", "ready_in_minutes": 30, "calories": 824, "protein": 26, "carbs": 57, "fat": 70},\n\
    {"id": "5", "title": "Lasagne", "description": "Italian classic - 60 minutes", "cuisine": ["Italian"], "image": "https://www.themealdb.com/images/media/meals/wtsvxx1511296896.jpg", "ready_in_minutes": 60, "calories": 1042, "protein": 49, "carbs": 46, "fat": 72}\n\
]\n\
\n\
@app.route("/")\n\
def root():\n\
    return {"message": f"Recipe App Backend API with {len(RECIPES)} recipes"}\n\
\n\
@app.route("/get_recipes")\n\
def get_recipes():\n\
    query = request.args.get("query", "")\n\
    offset = int(request.args.get("offset", 0))\n\
    limit = int(request.args.get("limit", 20))\n\
    \n\
    filtered = RECIPES\n\
    if query:\n\
        filtered = [r for r in RECIPES if query.lower() in r["title"].lower()]\n\
    \n\
    total = len(filtered)\n\
    paginated = filtered[offset:offset + limit]\n\
    \n\
    return jsonify({\n\
        "recipes": paginated,\n\
        "total": total,\n\
        "offset": offset,\n\
        "limit": limit\n\
    })\n\
\n\
@app.route("/api/health")\n\
def health():\n\
    return {"status": "healthy", "message": f"Backend running with {len(RECIPES)} recipes"}\n\
\n\
if __name__ == "__main__":\n\
    port = int(os.environ.get("PORT", 8000))\n\
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
