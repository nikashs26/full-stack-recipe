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
# from routes.ai_meal_planner import ai_meal_planner_bp  # Commented out to avoid route conflict
from routes.health import health_bp
from routes.review_routes import review_bp
from routes.folder_routes import folder_bp
from routes.smart_features import smart_features_bp
from routes.image_proxy import image_proxy_bp
from test_ollama import test_bp
from test_meal_planner import test_meal_bp

# Load environment variables
load_dotenv()

# Configure logging to reduce chaos
debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
configure_logging(debug_mode)

# Initialize Flask app
app = Flask(__name__)

# Configure session for authentication
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure CORS for development and production
allowed_origins = [
    "http://localhost:8081", "http://127.0.0.1:8081", 
    "http://localhost:8083", "http://127.0.0.1:8083",
    # Add your production frontend URLs here
    "https://betterbulk.netlify.app",  # Your actual Netlify frontend URL
]

# Configure CORS properly to handle preflight requests
cors = CORS(app, 
    origins=allowed_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    supports_credentials=True,
    max_age=3600
)

# Initialize services
recipe_cache = RecipeCacheService()

def ensure_recipes_loaded():
    """Auto-restore recipes if count is too low on startup"""
    try:
        count_result = recipe_cache.get_recipe_count()
        if isinstance(count_result, dict):
            count = count_result.get('total', 0)
        else:
            count = count_result
        
        print(f"📊 Current recipe count: {count}")
        
        if count < 1200:  # Threshold - adjust based on your expected count
            print(f"⚠️ Only {count} recipes found, auto-restoring from backup...")
            
            # Try to restore from backup files
            backup_files = [
                'complete_railway_sync_data.json',
                'production_recipes_backup.json',
                'recipes_data.json'
            ]
            
            restored_count = 0
            for backup_file in backup_files:
                if os.path.exists(backup_file):
                    try:
                        import json
                        print(f"📦 Loading recipes from {backup_file}...")
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                        
                        # Handle different data structures
                        if isinstance(backup_data, dict):
                            recipes = backup_data.get('recipes', backup_data.get('data', []))
                        elif isinstance(backup_data, list):
                            recipes = backup_data
                        else:
                            continue
                        
                        # Import up to 1500 recipes for good variety
                        recipes_to_import = recipes[:1500]
                        batch_size = 100
                        
                        for i in range(0, len(recipes_to_import), batch_size):
                            batch = recipes_to_import[i:i + batch_size]
                            
                            for recipe in batch:
                                try:
                                    recipe_id = str(recipe.get('id', f"restore_{restored_count}"))
                                    recipe_cache.cache_recipe(recipe_id, recipe)
                                    restored_count += 1
                                    
                                    if restored_count % 100 == 0:
                                        print(f"✅ Restored {restored_count} recipes...")
                                        
                                except Exception as e:
                                    print(f"Failed to restore recipe: {e}")
                            
                            # Rate limiting
                            import time
                            time.sleep(0.1)
                        
                        print(f"✅ Successfully restored {restored_count} recipes from {backup_file}!")
                        break
                        
                    except Exception as e:
                        print(f"❌ Failed to restore from {backup_file}: {e}")
                        continue
            
            if restored_count > 0:
                final_count = recipe_cache.get_recipe_count()
                if isinstance(final_count, dict):
                    final_count = final_count.get('total', 0)
                print(f"🎉 Recipe restoration completed! Final count: {final_count}")
            else:
                print("⚠️ No backup files found or restoration failed")
        else:
            print(f"✅ Recipe count looks good ({count} recipes)")
            
    except Exception as e:
        print(f"❌ Error checking/restoring recipes: {e}")

# Auto-restore recipes on startup
ensure_recipes_loaded()

# Initialize email service with the Flask app
email_service = EmailService(app)
print("✓ Email service initialized")

# Register routes
app = register_recipe_routes(app, recipe_cache)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(preferences_bp, url_prefix='/api')
app.register_blueprint(meal_planner_bp, url_prefix='/api')
# app.register_blueprint(ai_meal_planner_bp, url_prefix='/api')  # Commented out to avoid route conflict
app.register_blueprint(health_bp)  # Health check routes
app.register_blueprint(review_bp, url_prefix='/api')  # Review routes
app.register_blueprint(folder_bp, url_prefix='/api')  # Folder routes
app.register_blueprint(smart_features_bp, url_prefix='/api')  # Smart features routes
app.register_blueprint(image_proxy_bp, url_prefix='/api')  # Image proxy routes
app.register_blueprint(test_bp, url_prefix='/api')  # Test routes
app.register_blueprint(test_meal_bp, url_prefix='/api')  # Test meal planner routes

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    print(f"🚀 Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
