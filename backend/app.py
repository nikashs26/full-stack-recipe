from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import json
import os
import requests
import time

# Assuming these exist for auth and favorites
from auth import require_auth, get_user_id_from_request
from routes.favorites import favorites_bp
from routes.preferences import preferences_bp
from routes.meal_planner import meal_planner_bp # Import the new meal planner blueprint
from services.recipe_service import RecipeService # Import RecipeService

# Initialize Flask App
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Initialize services
recipe_service = RecipeService()

# Register blueprints
app.register_blueprint(favorites_bp, url_prefix='/api')
app.register_blueprint(preferences_bp, url_prefix='/api')
app.register_blueprint(meal_planner_bp, url_prefix='/api') # Register the meal planner blueprint

# New route for fetching all recipes
@app.route('/api/recipes', methods=['GET'])
@require_auth
def get_all_recipes():
    try:
        recipes = recipe_service.get_all_recipes()
        return jsonify(recipes), 200
    except Exception as e:
        app.logger.error(f"Error fetching all recipes: {e}")
        return jsonify({"error": "Failed to fetch recipes", "details": str(e)}), 500

# MongoDB Setup
# ... existing code ... 