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
            
            # Skip automatic population on startup - will be done manually
            try:
                recipe_count = recipe_cache.get_recipe_count()
                print(f"📊 Render cache has {recipe_count} recipes")
            except Exception as e:
                print(f"⚠️ Could not check recipe cache: {e}")
                
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
        print(f"⚠️ Smart features disabled due to import error: {e}")
        print(f"⚠️ Error details: {type(e).__name__}: {str(e)}")
        # Create a simple recommendations fallback route
        @app.route('/api/recommendations', methods=['GET'])
        def simple_recommendations_fallback():
            """Simple recommendations fallback when smart_features fails to import"""
            try:
                # Get some recipes from our cache
                limit = request.args.get('limit', 8, type=int)
                all_recipes = recipe_cache.get_cached_recipes("", "", {})[:limit*2]  # Get more for variety
                
                # Simple filtering for variety
                recommendations = []
                seen_cuisines = set()
                
                for recipe in all_recipes:
                    if len(recommendations) >= limit:
                        break
                    
                    # Try to get variety of cuisines
                    cuisine = recipe.get('cuisine', 'Unknown')
                    if cuisine not in seen_cuisines or len(recommendations) < limit//2:
                        recommendations.append({
                            "id": recipe.get('id'),
                            "title": recipe.get('title', recipe.get('name')),
                            "image": recipe.get('image', recipe.get('imageUrl')),
                            "cuisine": cuisine,
                            "cuisines": recipe.get('cuisines', [cuisine] if cuisine != 'Unknown' else []),
                            "ingredients": recipe.get('ingredients', []),
                            "instructions": recipe.get('instructions', []),
                            "ready_in_minutes": recipe.get('ready_in_minutes', 30),
                            "diets": recipe.get('diets', []),
                            "tags": recipe.get('tags', [])
                        })
                        seen_cuisines.add(cuisine)
                
                return jsonify({
                    "success": True,
                    "recommendations": recommendations,
                    "total": len(recommendations),
                    "message": "Simple recommendations (smart features unavailable)"
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
else:
    print("⚠️ Smart features disabled via environment variable")
app.register_blueprint(admin_bp, url_prefix='/')
app.register_blueprint(migration_bp, url_prefix='/')

print("✓ All route blueprints registered")

# Add a dedicated recommendations route that works with preferences
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get personalized recommendations based on user preferences"""
    try:
        from middleware.auth_middleware import get_current_user_id
        from backend.services.user_preferences_service import UserPreferencesService
        
        user_id = get_current_user_id()
        limit = request.args.get('limit', 8, type=int)
        
        print(f"🔍 Recommendations for user: {user_id}, limit: {limit}")
        
        # Get user preferences
        prefs_service = UserPreferencesService()
        preferences = prefs_service.get_preferences(user_id) if user_id else None
        
        print(f"📋 User preferences: {preferences}")
        
        # Get recipes from cache
        all_recipes = recipe_cache.get_cached_recipes("", "", {})
        
        # Apply basic preference filtering
        filtered_recipes = []
        if preferences:
            favorite_cuisines = preferences.get('favoriteCuisines', [])
            dietary_restrictions = preferences.get('dietaryRestrictions', [])
            
            print(f"🍽️ Filtering for cuisines: {favorite_cuisines}, diets: {dietary_restrictions}")
            
            for recipe in all_recipes:
                include_recipe = True
                
                # Filter by favorite cuisines (if specified)
                if favorite_cuisines:
                    recipe_cuisines = recipe.get('cuisines', [])
                    if isinstance(recipe_cuisines, list):
                        cuisine_match = any(fav.lower() in [c.lower() for c in recipe_cuisines] for fav in favorite_cuisines)
                    else:
                        cuisine_match = any(fav.lower() in str(recipe_cuisines).lower() for fav in favorite_cuisines)
                    
                    if not cuisine_match:
                        include_recipe = False
                
                # Filter by dietary restrictions
                if dietary_restrictions and include_recipe:
                    recipe_diets = recipe.get('diets', [])
                    if isinstance(recipe_diets, list):
                        diet_match = any(diet.lower() in [d.lower() for d in recipe_diets] for diet in dietary_restrictions)
                    else:
                        diet_match = any(diet.lower() in str(recipe_diets).lower() for diet in dietary_restrictions)
                    
                    if not diet_match:
                        include_recipe = False
                
                if include_recipe:
                    filtered_recipes.append(recipe)
                    if len(filtered_recipes) >= limit * 2:  # Get extra for variety
                        break
        else:
            # No preferences - return variety
            filtered_recipes = all_recipes[:limit * 2]
        
        # Format recommendations
        recommendations = []
        seen_cuisines = set()
        
        for recipe in filtered_recipes:
            if len(recommendations) >= limit:
                break
                
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
                }
                recommendations.append(formatted_recipe)
                seen_cuisines.add(cuisine)
        
        print(f"✅ Returning {len(recommendations)} recommendations")
        
        return jsonify({
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations),
            "preferences_applied": preferences is not None,
            "message": f"Recommendations based on your preferences" if preferences else "General recommendations"
        })
        
    except Exception as e:
        print(f"❌ Error in recommendations: {e}")
        return jsonify({"error": str(e)}), 500

# Check and restore data if needed
def check_and_restore_data():
    """Check if data exists and automatically restore if needed"""
    try:
        # Check if we have any recipes
        result = recipe_cache.recipe_collection.get(limit=1)
        if not result['ids']:
            print("⚠️ No recipes found in ChromaDB - automatically importing...")
            auto_import_recipes()
        else:
            print(f"✅ ChromaDB has {len(result['ids'])} recipes")
    except Exception as e:
        print(f"⚠️ Error checking ChromaDB: {e}")

def auto_import_recipes():
    """Automatically import recipes from local data files"""
    try:
        import json
        import os
        
        # Try to find recipe data files
        recipe_files = ["recipes_data.json", "backend/recipes_data.json"]
        
        for file_path in recipe_files:
            if os.path.exists(file_path):
                print(f"📁 Found recipe data: {file_path}")
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'recipes' in data:
                    recipes = data['recipes']
                elif isinstance(data, list):
                    recipes = data
                else:
                    continue
                
                # Import all recipes for complete recipe collection
                recipes_to_import = recipes
                print(f"🚀 Auto-importing {len(recipes_to_import)} recipes...")
                
                # Simple recipe normalization for auto-import
                ids, docs, metas = [], [], []
                for i, item in enumerate(recipes_to_import):
                    try:
                        # Basic normalization
                        recipe_id = str(item.get('id', f'recipe_{i}'))
                        title = str(item.get('title', item.get('name', f'Recipe {i}')))
                        
                        # Create minimal normalized recipe
                        normalized = {
                            'id': recipe_id,
                            'title': title,
                            'ingredients': item.get('ingredients', []),
                            'instructions': item.get('instructions', []),
                            'image': item.get('image', ''),
                            'cuisines': item.get('cuisines', []),
                            'diets': item.get('diets', [])
                        }
                        
                        ids.append(recipe_id)
                        docs.append(json.dumps(normalized))
                        
                        metadata = {
                            'id': recipe_id,
                            'title': title,
                            'source': 'auto_startup',
                        }
                        
                        if normalized.get('cuisines') and isinstance(normalized['cuisines'], list):
                            metadata['cuisines'] = ','.join(normalized['cuisines'][:3])  # First 3 cuisines
                        
                        metas.append(metadata)
                        
                    except Exception as e:
                        print(f"⚠️ Error processing recipe {i}: {e}")
                        continue
                
                if ids:
                    recipe_cache.recipe_collection.add(ids=ids, documents=docs, metadatas=metas)
                    print(f"✅ Successfully imported {len(ids)} recipes automatically!")
                    return
                
        print("⚠️ No recipe data files found for auto-import")
        
    except Exception as e:
        print(f"❌ Auto-import failed: {e}")

# Check data on startup
check_and_restore_data()

# Basic health check route - lightweight for Render monitoring
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'Render backend is running', 'routes': 'all registered'}

# Separate readiness check for heavy operations
@app.route('/api/ready')
def readiness_check():
    """Check if the app is ready to serve requests (includes database checks)"""
    try:
        ready = True
        services = {}
        
        # Check recipe cache only if initialized
        if recipe_cache:
            try:
                # Lightweight check - just verify collection exists
                services['recipe_cache'] = 'ready'
            except Exception as e:
                services['recipe_cache'] = f'error: {str(e)}'
                ready = False
        else:
            services['recipe_cache'] = 'not_initialized'
            
        return {
            'status': 'ready' if ready else 'not_ready',
            'services': services,
            'message': 'All services operational' if ready else 'Some services unavailable'
        }, 200 if ready else 503
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }, 500

# Debug endpoint for ChromaDB status
@app.route('/api/debug-chromadb', methods=['GET'])
def debug_chromadb():
    """Debug endpoint to check ChromaDB status"""
    try:
        import os
        from backend.services.user_service import UserService
        from backend.services.user_preferences_service import UserPreferencesService
        
        debug_info = {
            'chromadb_available': True,  # We know it's available since we're using it
            'environment': {
                'CHROMA_DB_PATH': os.environ.get('CHROMA_DB_PATH'),
                'RENDER_ENVIRONMENT': os.environ.get('RENDER_ENVIRONMENT'),
                'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            },
            'paths': {
                'current_dir': os.getcwd(),
                'chroma_path': os.path.abspath(os.environ.get('CHROMA_DB_PATH', './chroma_db')),
                'path_exists': os.path.exists(os.path.abspath(os.environ.get('CHROMA_DB_PATH', './chroma_db')))
            }
        }
        
        # Test UserService initialization
        try:
            user_service = UserService()
            debug_info['user_service'] = {
                'client_available': user_service.client is not None,
                'users_collection_available': user_service.users_collection is not None,
                'verification_tokens_collection_available': user_service.verification_tokens_collection is not None
            }
        except Exception as e:
            debug_info['user_service'] = {'error': str(e)}
        
        # Test UserPreferencesService initialization
        try:
            prefs_service = UserPreferencesService()
            debug_info['preferences_service'] = {
                'client_available': prefs_service.client is not None,
                'collection_available': prefs_service.collection is not None
            }
        except Exception as e:
            debug_info['preferences_service'] = {'error': str(e)}
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

# Root route
@app.route('/')
def root():
    return {'message': 'Recipe App Backend API - Render Deployment', 'url': 'https://dietary-delight.onrender.com'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Render Flask app on port {port}...")
    print(f"🌐 Binding to host 0.0.0.0 and port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)