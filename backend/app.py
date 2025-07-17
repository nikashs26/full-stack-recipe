from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import json
import os
import requests
import time

# Import authentication and services
from routes.auth_routes import auth_bp
from services.email_service import EmailService
from routes.favorites import favorites_bp
from routes.preferences import preferences_bp
from routes.meal_planner import meal_planner_bp
from routes.shopping_list import shopping_list_bp
from routes.recipe_routes import register_recipe_routes
from routes.review_routes import review_bp
from services.recipe_service import RecipeService

# Import the new bulk import routes
from routes.bulk_import_routes import create_bulk_import_routes

# Import AI recipe routes
from routes.ai_recipes import ai_recipes_bp

# Initialize Flask App
app = Flask(__name__)

# Configure CORS to support credentials (for sessions)
CORS(app, supports_credentials=True, origins=['http://localhost:8080', 'http://localhost:8081', 'http://localhost:8082'])

# Configure session and security
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-for-sessions-change-in-production')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Initialize email service
email_service = EmailService(app)

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
app.register_blueprint(auth_bp, url_prefix='/api/auth')  # New authentication routes
app.register_blueprint(favorites_bp, url_prefix='/api')
app.register_blueprint(preferences_bp, url_prefix='/api')  # Now requires authentication
app.register_blueprint(meal_planner_bp, url_prefix='/api')  # Now requires authentication
app.register_blueprint(shopping_list_bp, url_prefix='/api')  # Now requires authentication
app.register_blueprint(review_bp, url_prefix='/api')  # New ChromaDB review routes

# Register bulk import routes
bulk_import_bp = create_bulk_import_routes(recipes_collection, mongo_available)
app.register_blueprint(bulk_import_bp, url_prefix='/api')

# Register AI recipe routes
app.register_blueprint(ai_recipes_bp, url_prefix='/api')

# Fix the untitled recipe issue in existing routes
@app.before_request
def improve_recipe_data_quality():
    """Middleware to improve recipe data quality on the fly"""
    pass  # This will be a placeholder for now

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Recipe App Backend with ChromaDB Authentication",
        "features": {
            "authentication": "ChromaDB + JWT",
            "email_verification": "Enabled",
            "protected_routes": [
                "/api/preferences",
                "/api/meal-plan/generate", 
                "/api/shopping-list/generate"
            ]
        }
    }), 200

# Remove temporary preferences - no longer needed
# temp_preferences_bp is removed since we now require authentication

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003) 