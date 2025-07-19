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
from routes.ai_meal_planner import ai_meal_planner_bp
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

# Configure CORS to support credentials (for sessions)
CORS(app,
     supports_credentials=True,
     origins=[
         'http://localhost:5173',  # Vite default port
         'http://localhost:8080',
         'http://localhost:8081',
         'http://127.0.0.1:5173',
         'http://127.0.0.1:8080',
         'http://127.0.0.1:8081',
         'http://127.0.0.1:3000'
     ],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
     expose_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     max_age=3600
)

# Configure session for temp preferences
app.config['SECRET_KEY'] = 'your-secret-key-for-sessions'  # Change this in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Register routes using Chroma services
register_recipe_routes(app, recipe_cache)
# If you want to keep folders, refactor folder routes to use Chroma or remove them
# register_folder_routes(app)
# register_diagnostic_routes(app)

# Register temp preferences routes
app.register_blueprint(temp_preferences_bp, url_prefix='/api')
app.register_blueprint(ai_meal_planner_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
print("Temp preferences routes registered successfully")
print("Auth routes registered successfully")

if __name__ == "__main__":
    print("Starting Flask application...")
    # Run the Flask app on 127.0.0.1 to make it accessible only locally
    app.run(host='127.0.0.1', debug=True, port=8000) 