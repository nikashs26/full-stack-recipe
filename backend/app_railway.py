from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config.logging_config import configure_logging
from services.recipe_cache_service import RecipeCacheService
from services.email_service import EmailService
from routes.recipe_routes import register_recipe_routes
from routes.auth_routes import auth_bp
from routes.preferences import preferences_bp
from routes.meal_planner import meal_planner_bp
from routes.ai_meal_planner import ai_meal_planner_bp
from routes.health import health_bp
from routes.review_routes import review_bp
from routes.folder_routes import folder_bp
from routes.smart_features import smart_features_bp

# Load environment variables
load_dotenv()

# Configure logging
configure_logging(False)  # Disable debug logging in production

# Initialize Flask app
app = Flask(__name__)

# Configure session for authentication
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = True  # Enable secure cookies for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure CORS for Railway deployment - update with your actual Netlify URL
allowed_origins = [
    "http://localhost:8081", "http://127.0.0.1:8081", 
    "http://localhost:8083", "http://127.0.0.1:8083",
    "https://betterbulk.netlify.app",  # Update this with your actual Netlify URL
    "https://*.netlify.app",  # Allow all Netlify subdomains
]

# Configure CORS properly
cors = CORS(app, 
    origins=allowed_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    supports_credentials=True,
    max_age=3600
)

# Initialize services
try:
    recipe_cache = RecipeCacheService()
    print("✓ Recipe cache service initialized")
    
    # Populate Railway with recipes from sync data if cache is empty
    try:
        recipe_count = recipe_cache.get_recipe_count()
        if recipe_count == 0:
            print("📝 Railway cache is empty, populating from sync data...")
            try:
                from populate_railway_from_sync_data import populate_railway_from_sync_data
                success = populate_railway_from_sync_data()
                if success:
                    print("✅ Successfully populated Railway from sync data")
                else:
                    print("⚠️ Failed to populate from sync data, trying backup...")
                    from populate_railway_from_backup import populate_railway_from_backup
                    success = populate_railway_from_backup()
                    if success:
                        print("✅ Successfully populated Railway from backup recipes")
                    else:
                        print("⚠️ Failed to populate from backup, falling back to basic recipes")
                        from populate_railway_recipes import populate_railway
                        populate_railway()
            except ImportError:
                print("⚠️ Sync data population script not found, trying backup...")
                try:
                    from populate_railway_from_backup import populate_railway_from_backup
                    success = populate_railway_from_backup()
                    if success:
                        print("✅ Successfully populated Railway from backup recipes")
                    else:
                        print("⚠️ Failed to populate from backup, using basic recipes")
                        from populate_railway_recipes import populate_railway
                        populate_railway()
                except ImportError:
                    print("⚠️ Backup population script not found, using basic recipes")
                    from populate_railway_recipes import populate_railway
                    populate_railway()
        else:
            print(f"📊 Railway cache has {recipe_count} recipes")
    except Exception as e:
        print(f"⚠️ Could not check/populate recipe cache: {e}")
        print("📝 Attempting to populate with basic recipes...")
        try:
            from populate_railway_recipes import populate_railway
            populate_railway()
        except Exception as e2:
            print(f"⚠️ Could not populate with basic recipes either: {e2}")
        
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

# Basic health check route
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'Railway backend is running', 'routes': 'all registered'}

# Manual population endpoint
@app.route('/api/populate', methods=['POST'])
def manual_populate():
    """Manually trigger population from sync data"""
    try:
        from manual_populate_railway import populate_railway_manually
        success = populate_railway_manually()
        if success:
            return {'status': 'success', 'message': 'Railway populated successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to populate Railway'}, 500
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

# Root route
@app.route('/')
def root():
    return {'message': 'Recipe App Backend API - Railway Deployment'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Railway Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
