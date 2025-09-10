from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
import os
import time
import sys
import json

# Import modules
from routes.recipe_routes import register_recipe_routes
from routes.folder_routes import register_folder_routes
from routes.diagnostic_routes import register_diagnostic_routes
from routes.temp_preferences import temp_preferences_bp
from routes.auth_routes import auth_bp
# from routes.ai_meal_planner import ai_meal_planner_bp  # Commented out to avoid route conflict
from routes.mealdb_routes import register_mealdb_routes
from services.recipe_cache_service import RecipeCacheService
from services.user_preferences_service import UserPreferencesService

# Print Python version and path for debugging
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Load environment variables from .env file
load_dotenv('../info.env')

# Initialize Flask app
app = Flask(__name__)

# Initialize ChromaDB services
recipe_cache = RecipeCacheService()
user_preferences = UserPreferencesService()

# Initialize recipe service
from services.recipe_service import recipe_service

# Configure CORS to be very permissive for development
from flask_cors import CORS, cross_origin

# Minimal CORS configuration
cors = CORS()

def init_cors(app):
    # Apply CORS to all routes
    cors.init_app(app, 
        resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": "*",
                "expose_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
                "max_age": 3600
            }
        },
        supports_credentials=True
    )
    
    # Handle preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            headers = {}
            headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            headers['Access-Control-Allow-Credentials'] = 'true'
            headers['Access-Control-Max-Age'] = '3600'
            
            for key, value in headers.items():
                response.headers[key] = value
            return response
    
    return app

# Initialize CORS
app = init_cors(app)

# Configure session for temp preferences
app.config['SECRET_KEY'] = 'your-secret-key-for-sessions'  # Change this in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Create a blueprint for recipe routes
from routes.recipe_routes import recipe_bp

# Register recipe routes with the /api prefix
app.register_blueprint(recipe_bp, url_prefix='/api')

# Initialize and register recipe routes
register_recipe_routes(app, recipe_cache)
register_folder_routes(app, recipe_cache)
register_diagnostic_routes(app)
register_mealdb_routes(app)
app.register_blueprint(temp_preferences_bp, url_prefix='/api')
# app.register_blueprint(ai_meal_planner_bp, url_prefix='/api')  # Commented out to avoid route conflict
app.register_blueprint(auth_bp, url_prefix='/api/auth')
print("Recipe routes registered successfully")
print("Temp preferences routes registered successfully")
print("Auth routes registered successfully")

if __name__ == "__main__":
    print("Starting Flask application...")
    # Run the Flask app on 127.0.0.1 to make it accessible only locally
    app.run(host='127.0.0.1', debug=True, port=8000) 