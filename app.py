from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
import os
import json

# Set Render environment variable for persistent storage and disable all telemetry FIRST
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['DISABLE_SMART_FEATURES'] = os.environ.get('DISABLE_SMART_FEATURES', 'FALSE')
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
        print(f"⚠️ Smart features could not be imported: {e}")
else:
    print("⚠️ Smart features disabled via environment variable")
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
                    
                    # Skip recipes with missing essential data
                    title = recipe.get('title', recipe.get('name', ''))
                    if not title or title.strip() == '':
                        continue
                    
                    # Try to get variety of cuisines
                    cuisine = recipe.get('cuisine', 'Unknown')
                    
                    # Skip recipes with unknown cuisine if we have enough variety
                    if cuisine == 'Unknown' and len(seen_cuisines) > 2:
                        continue
                    
                    if cuisine not in seen_cuisines or len(recommendations) < limit//2:
                        recommendations.append({
                            "id": recipe.get('id'),
                            "title": title,
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

# Register image proxy for handling external images
try:
    app.register_blueprint(image_proxy_bp, url_prefix='/api')
    print("✓ Image proxy routes registered")
except Exception as e:
    print(f"⚠️ Image proxy could not be registered: {e}")

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
    """Automatically import recipes from your existing data files"""
    try:
        import json
        import os
        import time
        
        print("🌱 Starting automatic recipe seeding...")
        
        # Try to load from your existing recipe data files
        backup_files = [
            "complete_railway_sync_data.json",
            "recipes_data.json", 
            "batch_1.json",
            "batch_2.json",
            "production_recipes_backup.json",
            "production_recipes_essential.json"
        ]
        
        total_added = 0
        recipes_loaded = False
        
        for backup_file in backup_files:
            if os.path.exists(backup_file):
                try:
                    print(f"📦 Loading recipes from {backup_file}...")
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    # Handle different data structures
                    if isinstance(backup_data, dict):
                        recipes = backup_data.get('recipes', backup_data.get('data', []))
                    elif isinstance(backup_data, list):
                        recipes = backup_data
                    else:
                        print(f"⚠️ Unknown data structure in {backup_file}")
                        continue
                    
                    print(f"📊 Found {len(recipes)} recipes in backup")
                    
                    # Import recipes directly to ChromaDB collections
                    recipes_to_import = recipes[:1000]  # Limit to 1000 for startup speed
                    
                    # Prepare data for ChromaDB
                    ids = []
                    documents = []
                    metadatas = []
                    
                    for recipe in recipes_to_import:
                        try:
                            recipe_id = str(recipe.get('id', f"backup_{total_added}"))
                            ids.append(recipe_id)
                            
                            # Store the full recipe as a JSON string
                            documents.append(json.dumps(recipe))
                            
                            # Create metadata
                            metadata = {
                                'id': recipe_id,
                                'title': recipe.get('title', 'Unknown Recipe'),
                                'source': recipe.get('source', 'backup'),
                                'cached_at': str(int(time.time()))
                            }
                            
                            # Add additional metadata if available
                            if recipe.get('cuisines'):
                                metadata['cuisines'] = ','.join(recipe['cuisines'][:3])
                            if recipe.get('diets'):
                                metadata['diets'] = ','.join(recipe['diets'][:3])
                            
                            metadatas.append(metadata)
                            total_added += 1
                        except Exception as e:
                            print(f"❌ Failed to process recipe {recipe.get('title', 'Unknown')}: {e}")
                    
                    # Batch insert to ChromaDB
                    if ids:
                        try:
                            recipe_cache.recipe_collection.upsert(
                                ids=ids,
                                documents=documents,
                                metadatas=metadatas
                            )
                            print(f"✅ Successfully imported {len(ids)} recipes to ChromaDB")
                        except Exception as e:
                            print(f"❌ Failed to upsert recipes to ChromaDB: {e}")
                    
                    recipes_loaded = True
                    print(f"✅ Successfully loaded {total_added} recipes from {backup_file}!")
                    break
                    
                except Exception as e:
                    print(f"❌ Failed to load {backup_file}: {e}")
                    continue
        
        # If no backup files found, add some basic recipes as fallback
        if not recipes_loaded:
            print("⚠️ No backup files found, adding basic curated recipes...")
            
            curated_recipes = [
                {
                    "id": "curated_french_toast",
                    "title": "Perfect French Toast",
                    "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=500",
                    "cuisine": "French",
                    "cuisines": ["French", "Breakfast"],
                    "ingredients": ["4 slices thick bread", "3 large eggs", "1/2 cup milk", "1 tsp vanilla extract", "1 tsp cinnamon", "2 tbsp butter", "maple syrup"],
                    "instructions": ["Whisk together eggs, milk, vanilla, and cinnamon", "Heat butter in skillet", "Dip bread in mixture", "Cook until golden brown", "Serve with maple syrup"],
                    "diets": ["vegetarian"],
                    "tags": ["breakfast", "easy", "sweet"],
                    "ready_in_minutes": 15,
                    "difficulty": "easy",
                    "source": "curated"
                },
                {
                    "id": "curated_overnight_oats",
                    "title": "Overnight Oats with Berries", 
                    "image": "https://images.unsplash.com/photo-1571197119587-cfac4ac57e4a?w=500",
                    "cuisine": "American",
                    "cuisines": ["American", "Healthy"],
                    "ingredients": ["1/2 cup rolled oats", "1/2 cup milk", "1 tbsp chia seeds", "1 tbsp maple syrup", "1/4 cup mixed berries", "1 tbsp almond butter"],
                    "instructions": ["Combine oats, milk, chia seeds, and maple syrup in jar", "Refrigerate overnight", "Top with berries and almond butter", "Enjoy cold"],
                    "diets": ["vegetarian", "healthy", "gluten-free"],
                    "tags": ["breakfast", "no-cook", "healthy"],
                    "ready_in_minutes": 5,
                    "difficulty": "easy",
                    "source": "curated"
                }
            ]
            
            # Add curated recipes to ChromaDB
            if curated_recipes:
                try:
                    curated_ids = []
                    curated_docs = []
                    curated_metas = []
                    
                    for recipe in curated_recipes:
                        curated_ids.append(recipe['id'])
                        curated_docs.append(json.dumps(recipe))
                        curated_metas.append({
                            'id': recipe['id'],
                            'title': recipe['title'],
                            'source': recipe['source'],
                            'cached_at': str(int(time.time()))
                        })
                    
                    recipe_cache.recipe_collection.upsert(
                        ids=curated_ids,
                        documents=curated_docs,
                        metadatas=curated_metas
                    )
                    total_added += len(curated_recipes)
                    print(f"✅ Added {len(curated_recipes)} curated recipes")
                    
                except Exception as e:
                    print(f"❌ Failed to add curated recipes: {e}")
        
        print(f"🎉 Auto-seeding complete! Added {total_added} recipes")
        return total_added
        
    except Exception as e:
        print(f"❌ Auto-seeding failed: {e}")
        return 0

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

# Check data on startup - ensure recipes are loaded
check_and_restore_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Render Flask app on port {port}...")
    print(f"🌐 Binding to host 0.0.0.0 and port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)