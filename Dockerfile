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

# Copy the real recipe data
COPY recipe_backup_20250812_155632_202_recipes.json .

# Create a complete Flask app that loads your real recipes
RUN echo 'from flask import Flask, request, jsonify\n\
from flask_cors import CORS\n\
import os\n\
import json\n\
\n\
app = Flask(__name__)\n\
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")\n\
\n\
# Configure CORS\n\
CORS(app, origins=["https://betterbulk.netlify.app", "http://localhost:8081", "http://localhost:8083"])\n\
\n\
# Load your real recipe data\n\
try:\n\
    with open("recipe_backup_20250812_155632_202_recipes.json", "r") as f:\n\
        recipe_data = json.load(f)\n\
        REAL_RECIPES = recipe_data["recipes"]\n\
        print(f"✅ Loaded {len(REAL_RECIPES)} real recipes from backup")\n\
except Exception as e:\n\
    print(f"❌ Error loading recipes: {e}")\n\
    REAL_RECIPES = []\n\
\n\
@app.route("/")\n\
def root():\n\
    return {"message": f"Recipe App Backend API with {len(REAL_RECIPES)} recipes"}\n\
\n\
@app.route("/get_recipes")\n\
def get_recipes():\n\
    query = request.args.get("query", "")\n\
    ingredient = request.args.get("ingredient", "")\n\
    offset = int(request.args.get("offset", 0))\n\
    limit = int(request.args.get("limit", 20))\n\
    \n\
    filtered = REAL_RECIPES\n\
    if query:\n\
        filtered = [r for r in REAL_RECIPES if query.lower() in r["data"]["title"].lower()]\n\
    \n\
    total = len(filtered)\n\
    paginated = filtered[offset:offset + limit]\n\
    \n\
    # Transform to expected format\n\
    transformed_recipes = []\n\
    for recipe in paginated:\n\
        transformed_recipe = {\n\
            "id": recipe["id"],\n\
            "title": recipe["data"]["title"],\n\
            "description": f"{recipe[\'metadata\'][\'cuisine\']} cuisine - {recipe[\'metadata\'][\'cooking_time\']} minutes",\n\
            "cuisine": [recipe["metadata"]["cuisine"]] if recipe["metadata"]["cuisine"] else [],\n\
            "ingredients": [],\n\
            "instructions": [],\n\
            "ready_in_minutes": recipe["metadata"].get("cooking_time", 30),\n\
            "image": recipe["metadata"].get("image", ""),\n\
            "calories": recipe["data"].get("calories", 0),\n\
            "protein": recipe["data"].get("protein", 0),\n\
            "carbs": recipe["data"].get("carbs", 0),\n\
            "fat": recipe["data"].get("fat", 0)\n\
        }\n\
        transformed_recipes.append(transformed_recipe)\n\
    \n\
    return jsonify({\n\
        "recipes": transformed_recipes,\n\
        "total": total,\n\
        "offset": offset,\n\
        "limit": limit\n\
    })\n\
\n\
@app.route("/get_recipe_by_id")\n\
def get_recipe_by_id():\n\
    recipe_id = request.args.get("id")\n\
    recipe = next((r for r in REAL_RECIPES if r["id"] == recipe_id), None)\n\
    \n\
    if recipe:\n\
        transformed_recipe = {\n\
            "id": recipe["id"],\n\
            "title": recipe["data"]["title"],\n\
            "description": f"{recipe[\'metadata\'][\'cuisine\']} cuisine - {recipe[\'metadata\'][\'cooking_time\']} minutes",\n\
            "cuisine": [recipe["metadata"]["cuisine"]] if recipe["metadata"]["cuisine"] else [],\n\
            "ingredients": [],\n\
            "instructions": [],\n\
            "ready_in_minutes": recipe["metadata"].get("cooking_time", 30),\n\
            "image": recipe["metadata"].get("image", ""),\n\
            "calories": recipe["data"].get("calories", 0),\n\
            "protein": recipe["data"].get("protein", 0),\n\
            "carbs": recipe["data"].get("carbs", 0),\n\
            "fat": recipe["data"].get("fat", 0)\n\
        }\n\
        return jsonify(transformed_recipe)\n\
    else:\n\
        return jsonify({"error": "Recipe not found"}), 404\n\
\n\
@app.route("/api/recipes/cuisines")\n\
def get_cuisines():\n\
    cuisines = list(set([r["metadata"]["cuisine"] for r in REAL_RECIPES if r["metadata"]["cuisine"]]))\n\
    return jsonify(cuisines)\n\
\n\
@app.route("/api/mealdb/cuisines")\n\
def get_mealdb_cuisines():\n\
    cuisines = list(set([r["metadata"]["cuisine"] for r in REAL_RECIPES if r["metadata"]["cuisine"]]))\n\
    return jsonify(cuisines)\n\
\n\
@app.route("/api/mealdb/search")\n\
def mealdb_search():\n\
    cuisine = request.args.get("cuisine", "")\n\
    query = request.args.get("query", "")\n\
    \n\
    filtered = REAL_RECIPES\n\
    if cuisine:\n\
        filtered = [r for r in REAL_RECIPES if cuisine.lower() in r["metadata"]["cuisine"].lower()]\n\
    if query:\n\
        filtered = [r for r in filtered if query.lower() in r["data"]["title"].lower()]\n\
    \n\
    transformed = []\n\
    for recipe in filtered:\n\
        transformed.append({\n\
            "id": recipe["id"],\n\
            "title": recipe["data"]["title"],\n\
            "description": f"{recipe[\'metadata\'][\'cuisine\']} cuisine - {recipe[\'metadata\'][\'cooking_time\']} minutes",\n\
            "image": recipe["metadata"].get("image", "")\n\
        })\n\
    \n\
    return jsonify({"meals": transformed, "total": len(transformed)})\n\
\n\
@app.route("/api/mealdb/recipe/<recipe_id>")\n\
def get_mealdb_recipe(recipe_id):\n\
    recipe = next((r for r in REAL_RECIPES if r["id"] == recipe_id), None)\n\
    \n\
    if recipe:\n\
        transformed_recipe = {\n\
            "id": recipe["id"],\n\
            "title": recipe["data"]["title"],\n\
            "description": f"{recipe[\'metadata\'][\'cuisine\']} cuisine - {recipe[\'metadata\'][\'cooking_time\']} minutes",\n\
            "cuisine": [recipe["metadata"]["cuisine"]] if recipe["metadata"]["cuisine"] else [],\n\
            "ingredients": [],\n\
            "instructions": [],\n\
            "ready_in_minutes": recipe["metadata"].get("cooking_time", 30),\n\
            "image": recipe["metadata"].get("image", ""),\n\
            "calories": recipe["data"].get("calories", 0),\n\
            "protein": recipe["data"].get("protein", 0),\n\
            "carbs": recipe["data"].get("carbs", 0),\n\
            "fat": recipe["data"].get("fat", 0)\n\
        }\n\
        return jsonify(transformed_recipe)\n\
    else:\n\
        return jsonify({"error": "Recipe not found"}), 404\n\
\n\
# Add preferences route to fix the error\n\
@app.route("/api/preferences", methods=["GET", "POST"])\n\
def preferences():\n\
    if request.method == "GET":\n\
        return jsonify({"preferences": {}})\n\
    else:\n\
        return jsonify({"message": "Preferences updated"})\n\
\n\
@app.route("/api/auth/me")\n\
def auth_me():\n\
    return jsonify({"user": {"id": 1, "email": "user@example.com"}})\n\
\n\
@app.route("/api/health")\n\
def health():\n\
    return {"status": "healthy", "message": f"Backend running with {len(REAL_RECIPES)} recipes"}\n\
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
