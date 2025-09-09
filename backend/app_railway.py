from flask import Flask, request, make_response
from flask_cors import CORS
import os
import json
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

# Set Railway environment variable for persistent storage
os.environ['RAILWAY_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = '/app/data/chroma_db'

# Configure logging
configure_logging(False)  # Disable debug logging in production

# Initialize Flask app
app = Flask(__name__)

# Configure session for authentication
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = True  # Enable secure cookies for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure CORS for Railway deployment
allowed_origins = [
    "http://localhost:8081", "http://127.0.0.1:8081", 
    "http://localhost:8083", "http://127.0.0.1:8083",
    "https://betterbulk.netlify.app",
    "https://betterbulk.netlify.app/",  # Include trailing slash variant
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
    if origin and ('netlify.app' in origin or origin in allowed_origins):
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
        if origin and ('netlify.app' in origin or origin in allowed_origins):
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
        print(f"📊 Railway cache has {recipe_count} recipes")
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

# Basic health check route
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'Railway backend is running', 'routes': 'all registered'}

# Upload sync data file (JSON) to container: /app/railway_sync_data.json
@app.route('/api/upload-sync', methods=['POST'])
def upload_sync():
    try:
        if 'file' not in request.files:
            return {'status': 'error', 'message': 'No file part'}, 400
        file = request.files['file']
        if file.filename == '':
            return {'status': 'error', 'message': 'No selected file'}, 400
        contents = file.read()
        if not contents:
            return {'status': 'error', 'message': 'Empty file'}, 400
        dest_path = '/app/railway_sync_data.json'
        with open(dest_path, 'wb') as f:
            f.write(contents)
        return {'status': 'success', 'message': 'Sync data uploaded', 'path': dest_path}
    except Exception as e:
        return {'status': 'error', 'message': f'Upload failed: {str(e)}'}, 500

# Populate from uploaded sync data file
@app.route('/api/populate-from-file', methods=['POST'])
def populate_from_file():
    try:
        sync_file_path = '/app/railway_sync_data.json'
        if not os.path.exists(sync_file_path):
            return {'status': 'error', 'message': 'No sync data file found'}, 404
        
        with open(sync_file_path, 'r') as f:
            sync_data = json.load(f)
        
        if not recipe_cache:
            return {'status': 'error', 'message': 'Recipe cache not available'}, 500
        
        # Process recipes from sync data
        recipes = sync_data.get('recipes', [])
        if not recipes:
            return {'status': 'error', 'message': 'No recipes in sync data'}, 400
        
        print(f"Processing {len(recipes)} recipes from sync data...")
        
        # Add recipes to cache
        for i, recipe_info in enumerate(recipes):
            try:
                recipe_id = recipe_info['id']
                metadata = recipe_info['metadata']
                recipe_data = recipe_info['data']
                
                # Use document field if available (merged data), otherwise merge data and metadata
                if 'document' in recipe_info:
                    document_data = recipe_info['document']
                else:
                    # Merge metadata into recipe data for frontend compatibility
                    merged_recipe = recipe_data.copy()
                    for key, value in metadata.items():
                        if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                            merged_recipe[key] = value
                    document_data = json.dumps(merged_recipe)
                
                # Store in recipe collection
                recipe_cache.recipe_collection.upsert(
                    ids=[recipe_id],
                    documents=[document_data],
                    metadatas=[metadata]
                )
                
                if (i + 1) % 100 == 0:
                    print(f"Processed {i + 1}/{len(recipes)} recipes...")
                    
            except Exception as e:
                print(f"Error processing recipe {recipe_id}: {e}")
                continue
        
        print(f"Successfully processed {len(recipes)} recipes")
        return {'status': 'success', 'message': f'Successfully populated {len(recipes)} recipes'}
        
    except Exception as e:
        return {'status': 'error', 'message': f'Population failed: {str(e)}'}, 500

# Download sync data JSON from a URL and save to /app/railway_sync_data.json
@app.route('/api/populate-from-url', methods=['POST'])
def populate_from_url():
    try:
        import requests as pyrequests
        url = request.args.get('url') or (request.json.get('url') if request.is_json else None)
        if not url:
            return {'status': 'error', 'message': 'Missing url parameter'}, 400
        resp = pyrequests.get(url, timeout=60)
        if resp.status_code != 200:
            return {'status': 'error', 'message': f'Failed to download: HTTP {resp.status_code}'}, 400
        if not resp.content:
            return {'status': 'error', 'message': 'Downloaded file is empty'}, 400
        dest_path = '/app/railway_sync_data.json'
        with open(dest_path, 'wb') as f:
            f.write(resp.content)
        return {'status': 'success', 'message': 'Sync data downloaded', 'path': dest_path}
    except Exception as e:
        return {'status': 'error', 'message': f'Download failed: {str(e)}'}, 500

# Debug endpoint to check sync data
@app.route('/api/debug-sync', methods=['GET'])
def debug_sync_data():
    """Debug endpoint to check sync data availability"""
    try:
        import os
        import json
        
        # Check for sync data files
        sync_files = [
            "railway_sync_data.json",
            "railway_sync_data_20250907_210446.json",
            os.environ.get('SYNC_DATA_PATH', '')
        ]
        
        found_files = []
        for file_path in sync_files:
            if file_path and os.path.exists(file_path):
                found_files.append({
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'exists': True
                })
            else:
                found_files.append({
                    'path': file_path,
                    'exists': False
                })
        
        # Check current directory contents
        current_dir = os.listdir('.')
        json_files = [f for f in current_dir if f.endswith('.json')]
        
        return {
            'status': 'success',
            'sync_files': found_files,
            'current_dir_files': current_dir[:10],  # First 10 files
            'json_files': json_files,
            'working_dir': os.getcwd()
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

# Debug endpoint to check recipe collection
@app.route('/api/debug-recipes', methods=['GET'])
def debug_recipes():
    """Debug endpoint to check recipe collection contents"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        cache = RecipeCacheService()
        
        # Check recipe collection count
        if cache.recipe_collection:
            count = cache.recipe_collection.count()
            
            # Get a few sample recipes
            sample_recipes = cache.recipe_collection.get(limit=3, include=['metadatas', 'documents'])
            
            return {
                'status': 'success',
                'recipe_collection_count': count,
                'sample_recipes': sample_recipes.get('metadatas', []),
                'sample_titles': [meta.get('title', 'No title') for meta in sample_recipes.get('metadatas', [])]
            }
        else:
            return {
                'status': 'error',
                'message': 'Recipe collection not initialized'
            }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

# Manual population endpoint
@app.route('/api/populate', methods=['POST'])
def manual_populate():
    """Manually trigger full population from backup"""
    try:
        from full_railway_populate import restore_full_database
        success = restore_full_database()
        if success:
            return {'status': 'success', 'message': 'Railway populated with complete database successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to populate Railway'}, 500
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

# Background population support to avoid HTTP timeouts on long runs
# Simple in-process status tracking
population_status = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'success': None,
    'message': None
}

@app.route('/api/populate-async', methods=['POST'])
def populate_async():
    """Start population in background and return immediately."""
    try:
        import threading
        from datetime import datetime
        from full_railway_populate import restore_full_database

        if population_status.get('running'):
            return {
                'status': 'in_progress',
                'message': 'Population already running',
                'started_at': population_status.get('started_at')
            }, 202

        def _run():
            try:
                population_status.update({
                    'running': True,
                    'started_at': datetime.utcnow().isoformat() + 'Z',
                    'finished_at': None,
                    'success': None,
                    'message': 'Population started'
                })
                ok = restore_full_database()
                population_status.update({
                    'running': False,
                    'finished_at': datetime.utcnow().isoformat() + 'Z',
                    'success': bool(ok),
                    'message': 'Completed successfully' if ok else 'Completed with errors'
                })
            except Exception as e:
                population_status.update({
                    'running': False,
                    'finished_at': datetime.utcnow().isoformat() + 'Z',
                    'success': False,
                    'message': f'Exception: {str(e)}'
                })

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return {
            'status': 'started',
            'message': 'Population kicked off in background',
            'started_at': population_status.get('started_at')
        }, 202
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

@app.route('/api/populate-status', methods=['GET'])
def populate_status():
    """Check background population status."""
    try:
        # Also include current recipe count for convenience
        current_count = None
        try:
            if recipe_cache:
                current_count = recipe_cache.get_recipe_count()
        except Exception:
            current_count = None
        return {
            'status': 'success',
            'population': population_status,
            'recipe_count': current_count
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

@app.route('/api/fix-missing-cuisines', methods=['POST'])
def fix_missing_cuisines():
    """Backfill cuisine metadata for recipes that are missing it."""
    try:
        from scripts.update_recipe_cuisines import update_recipe_cuisines
        update_recipe_cuisines()
        return {'status': 'success', 'message': 'Cuisine metadata backfill completed'}
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

@app.route('/api/export-preferences', methods=['GET'])
def export_preferences():
    """Export all user preferences from local ChromaDB."""
    try:
        from services.user_preferences_service import UserPreferencesService
        prefs_service = UserPreferencesService()
        
        # Get all preferences
        all_prefs = prefs_service.collection.get(include=['documents', 'metadatas'])
        
        preferences_data = []
        for i, (doc, meta) in enumerate(zip(all_prefs['documents'], all_prefs['metadatas'])):
            try:
                import json
                pref_data = json.loads(doc)
                preferences_data.append({
                    'user_id': meta.get('user_id'),
                    'preferences': pref_data
                })
            except Exception as e:
                print(f"Error parsing preferences for user {meta.get('user_id', 'unknown')}: {e}")
                continue
        
        return {
            'status': 'success',
            'count': len(preferences_data),
            'preferences': preferences_data
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

@app.route('/api/import-preferences', methods=['POST'])
def import_preferences():
    """Import user preferences to Railway ChromaDB."""
    try:
        from services.user_preferences_service import UserPreferencesService
        import json
        
        data = request.get_json()
        if not data or 'preferences' not in data:
            return {'status': 'error', 'message': 'No preferences data provided'}, 400
        
        prefs_service = UserPreferencesService()
        imported_count = 0
        
        for pref_data in data['preferences']:
            try:
                user_id = pref_data.get('user_id')
                preferences = pref_data.get('preferences', {})
                
                if user_id and preferences:
                    prefs_service.save_preferences(user_id, preferences)
                    imported_count += 1
            except Exception as e:
                print(f"Error importing preferences for user {pref_data.get('user_id', 'unknown')}: {e}")
                continue
        
        return {
            'status': 'success',
            'message': f'Imported {imported_count} user preferences',
            'count': imported_count
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

@app.route('/api/preferences-status', methods=['GET'])
def preferences_status():
    """Check user preferences count in Railway ChromaDB."""
    try:
        from services.user_preferences_service import UserPreferencesService
        prefs_service = UserPreferencesService()
        count = prefs_service.collection.count()
        return {
            'status': 'success',
            'count': count,
            'message': f'Found {count} user preferences in Railway'
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Error: {str(e)}'}, 500

# Minimal population endpoint (for testing)
@app.route('/api/populate-minimal', methods=['POST'])
def minimal_populate():
    """Manually trigger minimal population with sample recipes"""
    try:
        from minimal_populate import populate_railway_minimal
        success = populate_railway_minimal()
        if success:
            return {'status': 'success', 'message': 'Railway populated with sample recipes successfully'}
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
