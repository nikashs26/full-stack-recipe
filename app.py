from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
import os
import json

# Set Render environment variable for persistent storage and disable all telemetry FIRST
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['DISABLE_SMART_FEATURES'] = os.environ.get('DISABLE_SMART_FEATURES', 'TRUE')
os.environ['MINIMAL_STARTUP'] = os.environ.get('MINIMAL_STARTUP', 'TRUE')
# Force clean ChromaDB initialization to resolve deprecated configuration issues
os.environ['CHROMADB_FORCE_CLEAN_INIT'] = 'true'

# Disable ChromaDB telemetry IMMEDIATELY before any ChromaDB imports
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
os.environ['CHROMA_CLIENT_AUTHN_PROVIDER'] = ''
os.environ['CHROMA_CLIENT_AUTHN_CREDENTIALS'] = ''
# Additional telemetry disable attempts
os.environ['ALLOW_RESET'] = 'FALSE'
# Remove deprecated CHROMA_DB_IMPL - use default for v0.4.22+
# os.environ['CHROMA_DB_IMPL'] = 'duckdb+parquet'  # This is deprecated
os.environ['CHROMA_SERVER_NOFILE'] = '65536'
# Disable PostHog completely
os.environ['POSTHOG_DISABLED'] = 'TRUE'
os.environ['TELEMETRY_DISABLED'] = 'TRUE'

# Use local path for development, Render path for production
if os.path.exists('/opt/render'):
    os.environ['CHROMA_DB_PATH'] = '/opt/render/project/src/chroma_db'
else:
    os.environ['CHROMA_DB_PATH'] = './chroma_db'

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
# Smart features will be imported later conditionally
smart_features_bp = None
from backend.routes.admin import admin_bp
from backend.routes.migration_api import migration_bp

# Environment variables already set at top of file

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

# Initialize services with memory optimization
def initialize_services_safely():
    """Initialize services with proper error handling and memory management"""
    recipe_cache = None
    
    # Check if we should skip heavy initialization
    minimal_startup = os.environ.get('MINIMAL_STARTUP', 'FALSE').upper() == 'TRUE'
    
    if minimal_startup:
        print("🚀 Minimal startup mode - delaying heavy initialization")
        try:
            # Lazy initialization - create service but don't populate data
            recipe_cache = RecipeCacheService()
            print("✓ Recipe cache service initialized (minimal mode)")
        except Exception as e:
            print(f"⚠️ Recipe cache service failed to initialize: {e}")
            recipe_cache = None
    else:
        try:
            recipe_cache = RecipeCacheService()
            print("✓ Recipe cache service initialized")
            
            # Initialize and restore user accounts for Render persistence
            print("🔄 Initializing user accounts...")
            from backend.services.user_service import UserService
            user_service = UserService()
            
            # Restore users from backup on startup (for Render persistence)
            print("🔄 Render detected - restoring user accounts from backup...")
            user_service.restore_users_from_backup()
            
            # Check if recipes need to be seeded
            try:
                count_result = recipe_cache.get_recipe_count()
                if isinstance(count_result, dict):
                    recipe_count = count_result.get('total', 0)
                else:
                    recipe_count = count_result
                print(f"📊 Render cache has {recipe_count} recipes")
                
                # If no recipes, automatically populate
                if recipe_count == 0:
                    print("🌱 No recipes found - auto-seeding recipes...")
                    auto_seed_recipes()
                else:
                    print("✅ Recipes already loaded")
            except Exception as e:
                print(f"⚠️ Could not check recipe cache: {e}")
                # Still try to seed recipes on error
                print("🌱 Error checking cache - attempting to seed recipes...")
                auto_seed_recipes()
                
        except Exception as e:
            print(f"⚠️ Recipe cache service failed to initialize: {e}")
            recipe_cache = None
    
    return recipe_cache

# Initialize with safety checks
recipe_cache = initialize_services_safely()

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
# Import and register smart features conditionally 
if not os.environ.get('DISABLE_SMART_FEATURES', 'FALSE').upper() == 'TRUE':
    try:
        from backend.routes.smart_features import smart_features_bp
        app.register_blueprint(smart_features_bp, url_prefix='/api')
        print("✓ Smart features routes imported and registered")
    except Exception as e:
        print(f"⚠️ Smart features could not be imported: {e}")
else:
    print("⚠️ Smart features disabled via environment variable")
    # Create a simple recommendations fallback route
    @app.route('/api/recommendations', methods=['GET'])
    def simple_recommendations_fallback():
        """Simple recommendations fallback when smart_features fails to import"""
        try:
            from middleware.auth_middleware import get_current_user_id
            from backend.services.user_preferences_service import UserPreferencesService
            
            # Get user info for preferences
            user_id = get_current_user_id()
            limit = request.args.get('limit', 16, type=int)
            
            print(f"🔍 Fallback recommendations for user: {user_id}, limit: {limit}")
            
            # Get user preferences if available
            prefs_service = UserPreferencesService()
            preferences = prefs_service.get_preferences(user_id) if user_id else None
            
            print(f"📋 User preferences: {preferences}")
            
            # Get all available recipes
            all_recipes = recipe_cache.get_cached_recipes("", "", {})
            
            # Apply basic preference filtering if preferences exist
            filtered_recipes = []
            if preferences:
                favorite_cuisines = preferences.get('favoriteCuisines', [])
                dietary_restrictions = preferences.get('dietaryRestrictions', [])
                
                print(f"🍽️ Filtering for cuisines: {favorite_cuisines}, diets: {dietary_restrictions}")
                
                for recipe in all_recipes:
                    include_recipe = True
                    
                    # Filter by favorite cuisines
                    if favorite_cuisines:
                        recipe_cuisine = recipe.get('cuisine', '').lower()
                        recipe_cuisines = recipe.get('cuisines', [])
                        if isinstance(recipe_cuisines, list):
                            cuisine_match = any(fav.lower() in [c.lower() for c in recipe_cuisines] for fav in favorite_cuisines)
                        else:
                            cuisine_match = any(fav.lower() in recipe_cuisine for fav in favorite_cuisines)
                        
                        if not cuisine_match:
                            include_recipe = False
                    
                    # Filter by dietary restrictions
                    if dietary_restrictions and include_recipe:
                        recipe_diets = recipe.get('diets', [])
                        if isinstance(recipe_diets, list):
                            diet_match = all(any(diet.lower() in d.lower() for d in recipe_diets) for diet in dietary_restrictions)
                        else:
                            diet_match = all(diet.lower() in str(recipe_diets).lower() for diet in dietary_restrictions)
                        
                        if not diet_match:
                            include_recipe = False
                    
                    if include_recipe:
                        filtered_recipes.append(recipe)
                        if len(filtered_recipes) >= limit * 3:  # Get extra for variety
                            break
            else:
                # No preferences - return variety from all recipes
                filtered_recipes = all_recipes[:limit * 3]
            
            # Create diverse recommendations
            recommendations = []
            seen_cuisines = set()
            
            # Shuffle for variety
            import random
            random.shuffle(filtered_recipes)
            
            for recipe in filtered_recipes:
                if len(recommendations) >= limit:
                    break
                
                # Try to get variety of cuisines
                cuisine = recipe.get('cuisine', 'Unknown')
                if cuisine not in seen_cuisines or len(recommendations) < limit//2:
                    formatted_recipe = {
                        "id": recipe.get('id'),
                        "title": recipe.get('title', recipe.get('name')),
                        "image": recipe.get('image', recipe.get('imageUrl')),
                        "cuisine": cuisine,
                        "cuisines": recipe.get('cuisines', [cuisine] if cuisine != 'Unknown' else []),
                        "ingredients": recipe.get('ingredients', []),
                        "instructions": recipe.get('instructions', []),
                        "ready_in_minutes": recipe.get('ready_in_minutes', 30),
                        "diets": recipe.get('diets', []),
                        "tags": recipe.get('tags', []),
                        "description": recipe.get('description', ''),
                        "prep_time": recipe.get('prep_time', ''),
                        "cooking_time": recipe.get('cooking_time', ''),
                        "calories": recipe.get('calories'),
                        "protein": recipe.get('protein'),
                        "carbs": recipe.get('carbs'),
                        "fat": recipe.get('fat')
                    }
                    recommendations.append(formatted_recipe)
                    seen_cuisines.add(cuisine)
            
            print(f"✅ Returning {len(recommendations)} fallback recommendations")
            
            return jsonify({
                "success": True,
                "recommendations": recommendations,
                "total": len(recommendations),
                "preferences_applied": preferences is not None,
                "message": f"Recommendations based on your preferences (fallback mode)" if preferences else "General recommendations (fallback mode)"
            })
            
        except Exception as e:
            print(f"❌ Error in fallback recommendations: {e}")
            return jsonify({"error": str(e)}), 500

# Register image proxy for handling external images
try:
    app.register_blueprint(image_proxy_bp, url_prefix='/api')
    print("✓ Image proxy routes registered")
except Exception as e:
    print(f"⚠️ Image proxy could not be registered: {e}")

app.register_blueprint(admin_bp, url_prefix='/')
app.register_blueprint(migration_bp, url_prefix='/')

print("✓ All route blueprints registered")

# The recommendations route is handled by smart_features.py when available
# or by the fallback route when smart features are disabled

def auto_seed_recipes():
    """Automatically seed recipes on startup for production deployment"""
    try:
        print("🌱 Starting automatic recipe seeding...")
        import json
        import os
        
        # First try to load exported recipes from backup files
        backup_files = [
            "production_recipes_essential.json",
            "production_recipes_backup.json"
        ]
        
        total_added = 0
        recipes_loaded = False
        
        for backup_file in backup_files:
            if os.path.exists(backup_file):
                try:
                    print(f"📦 Loading recipes from {backup_file}...")
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    recipes = backup_data.get('recipes', [])
                    print(f"📊 Found {len(recipes)} recipes in backup")
                    
                    for recipe in recipes:
                        try:
                            recipe_id = recipe.get('id', f"backup_{total_added}")
                            recipe_cache.cache_recipe(recipe_id, recipe)
                            total_added += 1
                            if total_added % 100 == 0:
                                print(f"✅ Loaded {total_added} recipes...")
                        except Exception as e:
                            print(f"❌ Failed to load recipe {recipe.get('title', 'Unknown')}: {e}")
                    
                    recipes_loaded = True
                    print(f"✅ Successfully loaded {total_added} recipes from backup!")
                    break
                    
                except Exception as e:
                    print(f"❌ Failed to load {backup_file}: {e}")
                    continue
        
        # If no backup files found, fall back to minimal seeding
        if not recipes_loaded:
            print("⚠️ No recipe backup found, creating minimal seed recipes...")
            
            minimal_recipes = [
                {
                    'id': 'seed_chicken_pasta',
                    'title': 'Chicken Alfredo Pasta',
                    'image': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=500',
                    'cuisine': 'Italian',
                    'cuisines': ['Italian'],
                    'ingredients': ['chicken breast', 'fettuccine pasta', 'heavy cream', 'parmesan cheese', 'garlic', 'butter'],
                    'instructions': ['Cook pasta according to package directions', 'Season and cook chicken', 'Make alfredo sauce with cream and cheese', 'Combine all ingredients'],
                    'source': 'Fallback',
                    'diets': [],
                    'tags': ['pasta', 'chicken', 'creamy'],
                    'ready_in_minutes': 30,
                    'difficulty': 'medium'
                }
            ]
            
            for recipe in minimal_recipes:
                try:
                    recipe_cache.cache_recipe(recipe['id'], recipe)
                    total_added += 1
                    print(f"✅ Added fallback recipe: {recipe['title']}")
                except Exception as e:
                    print(f"❌ Failed to add fallback recipe: {e}")
        
        print(f"🎉 Auto-seeding complete! Added {total_added} recipes")
        return total_added
        
    except Exception as e:
        print(f"❌ Auto-seeding failed: {e}")
        return 0


# Initialize the application
if __name__ == "__main__":
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    
    if debug_mode:
        print("🐛 Debug mode enabled")
        
    # Start the application
    port = int(os.environ.get("PORT", 8081))
    print(f"🚀 Starting Flask app on port {port}")
    
    # Initialize the app properly
    print("✅ App initialization complete")
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode,
        threaded=True
    )
