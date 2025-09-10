from flask import Flask, request, make_response
from flask_cors import CORS
import os
import json

# Try to load dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, using environment variables only")

from backend.config.logging_config import configure_logging
from backend.services.recipe_cache_service import RecipeCacheService
from backend.services.email_service import EmailService
from backend.routes.recipe_routes import register_recipe_routes
from backend.routes.auth_routes import auth_bp
from backend.routes.preferences import preferences_bp
from backend.routes.meal_planner import meal_planner_bp
from backend.routes.ai_meal_planner import ai_meal_planner_bp
from backend.routes.health import health_bp
from backend.routes.review_routes import review_bp
from backend.routes.folder_routes import folder_bp
from backend.routes.smart_features import smart_features_bp

# Set Render environment variable for persistent storage
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = '/opt/render/project/chroma_db'

# Configure logging
configure_logging(False)  # Disable debug logging in production

# Initialize Flask app
app = Flask(__name__)

# Configure session for authentication
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = True  # Enable secure cookies for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure CORS for Render deployment
allowed_origins = [
    "http://localhost:8081", "http://127.0.0.1:8081", 
    "http://localhost:8083", "http://127.0.0.1:8083",
    "https://betterbulk.netlify.app",
    "https://betterbulk.netlify.app/",  # Include trailing slash variant
    "https://dietary-delight.onrender.com",  # Add Render URL
    "https://dietary-delight.onrender.com/",  # Include trailing slash variant
]

# Configure CORS properly - use regex for wildcard support
cors = CORS(app, 
    origins=allowed_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with", "Accept"],
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    supports_credentials=True,
    max_age=3600
)

# Additional CORS configuration for Netlify wildcard support
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and ('netlify.app' in origin or 'onrender.com' in origin or origin in allowed_origins):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, x-requested-with, Accept'
    return response

# Global OPTIONS handler for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        origin = request.headers.get('Origin')
        if origin and ('netlify.app' in origin or 'onrender.com' in origin or origin in allowed_origins):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, x-requested-with, Accept'
        return response

# Initialize services
try:
    recipe_cache = RecipeCacheService()
    print("✓ Recipe cache service initialized")
    
    # Skip automatic population on startup - will be done manually
    try:
        recipe_count = recipe_cache.get_recipe_count()
        print(f"📊 Render cache has {recipe_count} recipes")
    except Exception as e:
        print(f"⚠️ Could not check recipe cache: {e}")
        
except Exception as e:
    print(f"⚠️ Recipe cache service failed to initialize: {e}")
    recipe_cache = None

# Initialize email service
try:
    email_service = EmailService(app)
    print("✓ Email service initialized")
except Exception as e:
    print(f"⚠️ Email service failed to initialize: {e}")

# Register all routes
if recipe_cache:
    app = register_recipe_routes(app, recipe_cache)
    print("✓ Recipe routes registered")
else:
    print("⚠️ Recipe routes not registered - cache service unavailable")

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(preferences_bp, url_prefix='/api')
app.register_blueprint(meal_planner_bp, url_prefix='/api')
app.register_blueprint(ai_meal_planner_bp, url_prefix='/api')
app.register_blueprint(health_bp)
app.register_blueprint(review_bp, url_prefix='/api')
app.register_blueprint(folder_bp, url_prefix='/api')
app.register_blueprint(smart_features_bp, url_prefix='/api')

print("✓ All route blueprints registered")

# Check and restore data if needed
def check_and_restore_data():
    """Check if data exists and restore if needed"""
    try:
        # Check if we have any recipes
        result = recipe_cache.recipe_collection.get(limit=1)
        if not result['ids']:
            print("⚠️ No recipes found in ChromaDB, data may have been lost")
            print("💡 Data will need to be restored via sync script")
        else:
            print(f"✅ ChromaDB has {len(result['ids'])} recipes")
    except Exception as e:
        print(f"⚠️ Error checking ChromaDB: {e}")

# Check data on startup
check_and_restore_data()

# Basic health check route
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'Render backend is running', 'routes': 'all registered'}

# Root route
@app.route('/')
def root():
    return {'message': 'Recipe App Backend API - Render Deployment', 'url': 'https://dietary-delight.onrender.com'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Render Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)