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
from routes.shopping_list import shopping_list_bp # Import the new shopping list blueprint
# from routes.smart_features import smart_features_bp # Import the new smart features blueprint - TEMPORARILY DISABLED
from routes.temp_preferences import temp_preferences_bp # Import the temporary preferences blueprint
from routes.recipe_routes import register_recipe_routes # Import the recipe routes registration function
from services.recipe_service import RecipeService # Import RecipeService

# Initialize Flask App
app = Flask(__name__)

# Configure CORS to support credentials (for sessions)
CORS(app, supports_credentials=True, origins=['http://localhost:8080', 'http://localhost:8081', 'http://localhost:8082'])

# Configure session
app.config['SECRET_KEY'] = 'your-secret-key-for-sessions'  # Change this in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Initialize services
recipe_service = RecipeService()

# Initialize MongoDB connection (simplified for demo)
mongo_client = None
recipes_collection = None
mongo_available = False
in_memory_recipes = []

# Register recipe routes
register_recipe_routes(app, recipes_collection, mongo_available, in_memory_recipes)

# Register blueprints
app.register_blueprint(favorites_bp, url_prefix='/api')
app.register_blueprint(preferences_bp, url_prefix='/api')
app.register_blueprint(meal_planner_bp, url_prefix='/api') # Register the meal planner blueprint
app.register_blueprint(shopping_list_bp, url_prefix='/api') # Register the shopping list blueprint
# app.register_blueprint(smart_features_bp, url_prefix='/api') # Register the smart features blueprint - TEMPORARILY DISABLED
app.register_blueprint(temp_preferences_bp, url_prefix='/api') # Register the temporary preferences blueprint

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003) 