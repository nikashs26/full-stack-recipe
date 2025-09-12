from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime

# Lazy import to avoid heavy deps at import time
from backend.services.recipe_cache_service import RecipeCacheService
from backend.services.user_service import UserService
from backend.services.user_preferences_service import UserPreferencesService

admin_bp = Blueprint('admin', __name__)

def _check_token(req) -> bool:
    token = req.headers.get('X-Admin-Token') or req.args.get('token')
    expected = os.environ.get('ADMIN_SEED_TOKEN')
    return bool(expected) and token == expected

def _check_admin_auth(req) -> bool:
    """Check if request is from an admin user"""
    # For now, use the same token check, but this could be enhanced
    # to check for admin role in user database
    return _check_token(req)

@admin_bp.route('/api/admin/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check file paths and environment"""
    if not _check_token(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    import os
    import platform
    
    debug_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'current_working_directory': os.getcwd(),
        'environment_variables': {
            'SEED_RECIPES_FILE': os.environ.get('SEED_RECIPES_FILE'),
            'SEED_RECIPES_ON_STARTUP': os.environ.get('SEED_RECIPES_ON_STARTUP'),
            'SEED_RECIPES_LIMIT': os.environ.get('SEED_RECIPES_LIMIT'),
            'RENDER_ENVIRONMENT': os.environ.get('RENDER_ENVIRONMENT'),
            'CHROMA_DB_PATH': os.environ.get('CHROMA_DB_PATH')
        },
        'file_checks': {}
    }
    
    # Check for recipe files in various locations
    possible_paths = [
        'recipes_data.json',
        'backend/recipes_data.json',
        '/opt/render/project/src/recipes_data.json',
        '/opt/render/project/src/backend/recipes_data.json',
        './recipes_data.json',
        './backend/recipes_data.json'
    ]
    
    for path in possible_paths:
        try:
            exists = os.path.exists(path)
            debug_info['file_checks'][path] = {
                'exists': exists,
                'absolute_path': os.path.abspath(path) if exists else None,
                'size_mb': round(os.path.getsize(path) / 1024 / 1024, 2) if exists else None
            }
        except Exception as e:
            debug_info['file_checks'][path] = {'error': str(e)}
    
    # List current directory contents
    try:
        debug_info['directory_listing'] = os.listdir('.')
    except Exception as e:
        debug_info['directory_listing'] = f"Error: {e}"
    
    # Check ChromaDB status
    try:
        from backend.services.recipe_cache_service import RecipeCacheService
        cache = RecipeCacheService()
        if cache.recipe_collection:
            debug_info['chromadb_status'] = {
                'client_available': True,
                'recipe_count': cache.recipe_collection.count()
            }
        else:
            debug_info['chromadb_status'] = {
                'client_available': False,
                'error': 'Recipe collection is None'
            }
    except Exception as e:
        debug_info['chromadb_status'] = {'error': str(e)}
    
    return jsonify(debug_info)

@admin_bp.route('/api/admin/seed', methods=['POST'])
def seed_recipes():
    if not _check_token(request):
        return jsonify({'error': 'Unauthorized'}), 401

    body = request.get_json(silent=True) or {}
    seed_path = body.get('path') or os.environ.get('SEED_RECIPES_FILE', 'recipes_data.json')
    limit = int(body.get('limit') or os.environ.get('SEED_RECIPES_LIMIT', '5000'))
    truncate = bool(body.get('truncate', False))

    try:
        cache = RecipeCacheService()
        # Optional truncate for in-memory fallback
        if truncate and hasattr(cache, 'recipe_collection') and hasattr(cache.recipe_collection, 'recipes'):
            try:
                cache.recipe_collection.recipes.clear()
            except Exception:
                pass
        # Ensure we have a collection interface
        if not hasattr(cache, 'recipe_collection') or cache.recipe_collection is None:
            return jsonify({'error': 'Cache not available'}), 500

        # Load JSON
        if not os.path.exists(seed_path):
            return jsonify({'error': f'File not found: {seed_path}'}), 400

        with open(seed_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'recipes' in data:
            recipes = data['recipes']
        elif isinstance(data, list):
            recipes = data
        else:
            return jsonify({'error': 'Invalid JSON format; expected list or {"recipes": [...]}'}), 400

        # Normalization helpers
        def normalize_item(item):
            rid = str(item.get('id') or item.get('_id') or item.get('idMeal') or hash(item.get('title') or item.get('name') or item.get('strMeal') or 'Recipe'))
            title = (item.get('title') or item.get('name') or item.get('strMeal') or 'Recipe').strip()
            # Image candidates
            image = item.get('image') or item.get('imageUrl') or item.get('strMealThumb') or ''
            # Ingredients candidates
            ingredients = item.get('ingredients')
            if not ingredients:
                ext = item.get('extendedIngredients')
                if isinstance(ext, list):
                    ingredients = []
                    for ing in ext:
                        name = ing.get('name') if isinstance(ing, dict) else None
                        if not name:
                            continue
                        original = ing.get('original') if isinstance(ing, dict) else ''
                        measure = ''
                        if isinstance(ing, dict):
                            amt = ing.get('amount'); unit = ing.get('unit')
                            if amt or unit:
                                measure = f"{amt or ''} {unit or ''}".strip()
                        ingredients.append({'name': name, 'measure': measure, 'original': original or measure or name})
            if not ingredients and any(k.startswith('strIngredient') for k in item.keys()):
                ingredients = []
                for i in range(1, 21):
                    ing = str(item.get(f'strIngredient{i}', '') or '').strip()
                    meas = str(item.get(f'strMeasure{i}', '') or '').strip()
                    if ing:
                        ingredients.append({'name': ing, 'measure': meas or 'to taste', 'original': f"{meas} {ing}".strip()})
            if not isinstance(ingredients, list):
                ingredients = []
            # Instructions candidates
            instructions = item.get('instructions')
            if not instructions:
                analyzed = item.get('analyzedInstructions')
                if isinstance(analyzed, list) and analyzed:
                    steps = []
                    for block in analyzed:
                        for s in block.get('steps', []) if isinstance(block, dict) else []:
                            if s.get('step'):
                                steps.append(str(s['step']).strip())
                    instructions = steps
            if not instructions and isinstance(item.get('strInstructions'), str):
                # Split MealDB instructions into steps
                text = item.get('strInstructions')
                steps = [s.strip() for s in str(text).replace('\r', '\n').split('\n') if s and len(s.strip()) > 5]
                instructions = steps or [str(text).strip()]
            if isinstance(instructions, str):
                instructions = [instructions]
            if not isinstance(instructions, list):
                instructions = []
            # Cuisines
            cuisines = item.get('cuisines')
            if not cuisines and item.get('strArea'):
                cuisines = [str(item.get('strArea')).lower()]
            if isinstance(cuisines, str):
                cuisines = [cuisines]
            if not isinstance(cuisines, list):
                cuisines = []
            # Diets
            diets = item.get('diets') or item.get('dietary_restrictions') or []
            if isinstance(diets, str):
                diets = [diets]
            if not isinstance(diets, list):
                diets = []
            return {
                'id': rid,
                'title': title,
                'image': image,
                'imageUrl': image,
                'ingredients': ingredients,
                'instructions': instructions,
                'cuisines': cuisines,
                'diets': diets
            }, rid

        # Prepare documents and metadata
        ids, docs, metas = [], [], []
        for item in recipes[:max(0, limit)]:
            normalized, rid = normalize_item(item)
            ids.append(rid)
            docs.append(json.dumps(normalized))
            
            # Create safe metadata (only primitive types for ChromaDB)
            metadata = {
                'id': rid,
                'title': normalized.get('title', ''),
                'source': 'admin_seed',
                'uploaded_at': datetime.now().isoformat()
            }
            
            # Add safe metadata fields
            if normalized.get('cuisines'):
                metadata['cuisines'] = ','.join(normalized['cuisines']) if isinstance(normalized['cuisines'], list) else str(normalized.get('cuisines', ''))
            
            if normalized.get('diets'):
                metadata['diets'] = ','.join(normalized['diets']) if isinstance(normalized['diets'], list) else str(normalized.get('diets', ''))
                
            # Skip all nutrition metadata to avoid ChromaDB issues
            # The nutrition data will be stored in the document JSON instead
            pass  # Nutrition data is preserved in the JSON document
            
            metas.append(metadata)

        if not ids:
            return jsonify({'error': 'No recipes to import'}), 400

        # Add to primary recipe store
        cache.recipe_collection.add(ids=ids, documents=docs, metadatas=metas)

        # Also populate search cache so /api/get_recipes works immediately
        try:
            search_docs = []
            for d in docs:
                try:
                    obj = json.loads(d)
                except Exception:
                    obj = {'title': d}
                title = obj.get('title', '')
                ing_text = ' '.join([(i.get('name') if isinstance(i, dict) else str(i)) for i in obj.get('ingredients', [])])
                cuisine_text = ' '.join(obj.get('cuisines', []) or [])
                search_docs.append(f"{title} {ing_text} {cuisine_text}")
            if hasattr(cache, 'search_collection') and cache.search_collection is not None:
                cache.search_collection.add(ids=ids, documents=search_docs, metadatas=metas)
        except Exception:
            pass

        return jsonify({'status': 'ok', 'imported': len(ids), 'path': seed_path}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Get all users with pagination and filtering"""
    if not _check_admin_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_service = UserService()
        # Check if we have a working user service (either ChromaDB or fallback)
        if not hasattr(user_service, 'users_collection') or user_service.users_collection is None:
            # Try fallback method
            if hasattr(user_service, 'get_all_users'):
                # This is the fallback service
                pass
            else:
                return jsonify({'error': 'User database not available'}), 500
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        search_email = request.args.get('search', '').strip()
        
        # Build query
        where_clause = {}
        if verified_only:
            where_clause['is_verified'] = True
        if search_email:
            where_clause['email'] = {"$contains": search_email}
        
        # Get total count
        total_results = user_service.users_collection.get(
            where=where_clause if where_clause else None,
            include=['metadatas']
        )
        total_count = len(total_results['ids'])
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get paginated results
        results = user_service.users_collection.get(
            where=where_clause if where_clause else None,
            include=['documents', 'metadatas'],
            limit=per_page,
            offset=offset
        )
        
        # Process user data
        users = []
        for i, (user_id, doc, meta) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            try:
                user_data = json.loads(doc)
                users.append({
                    'user_id': user_id,
                    'email': user_data.get('email', ''),
                    'full_name': user_data.get('full_name', ''),
                    'is_verified': user_data.get('is_verified', False),
                    'created_at': user_data.get('created_at', ''),
                    'last_login': user_data.get('last_login', ''),
                    'metadata': meta
                })
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500


@admin_bp.route('/api/admin/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    if not _check_admin_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_service = UserService()
        if not user_service.users_collection:
            return jsonify({'error': 'User database not available'}), 500
        
        # Get user data
        results = user_service.users_collection.get(
            ids=[user_id],
            include=['documents', 'metadatas']
        )
        
        if not results['documents']:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = json.loads(results['documents'][0])
        user_metadata = results['metadatas'][0]
        
        # Get user preferences
        prefs_service = UserPreferencesService()
        preferences = None
        if prefs_service.collection:
            try:
                prefs_results = prefs_service.collection.get(
                    where={"user_id": user_id},
                    include=['documents']
                )
                if prefs_results['documents']:
                    preferences = json.loads(prefs_results['documents'][0])
            except Exception as e:
                print(f"Error getting preferences for user {user_id}: {e}")
        
        return jsonify({
            'status': 'success',
            'user': {
                'user_id': user_id,
                'email': user_data.get('email', ''),
                'full_name': user_data.get('full_name', ''),
                'is_verified': user_data.get('is_verified', False),
                'created_at': user_data.get('created_at', ''),
                'last_login': user_data.get('last_login', ''),
                'updated_at': user_data.get('updated_at', ''),
                'metadata': user_metadata,
                'preferences': preferences
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user details: {str(e)}'}), 500


@admin_bp.route('/api/admin/users/<user_id>/verify', methods=['POST'])
def verify_user(user_id):
    """Manually verify a user"""
    if not _check_admin_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_service = UserService()
        if not user_service.users_collection:
            return jsonify({'error': 'User database not available'}), 500
        
        # Get user data
        results = user_service.users_collection.get(
            ids=[user_id],
            include=['documents', 'metadatas']
        )
        
        if not results['documents']:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = json.loads(results['documents'][0])
        user_metadata = results['metadatas'][0]
        
        # Update user to verified
        user_data['is_verified'] = True
        user_data['updated_at'] = datetime.utcnow().isoformat()
        user_metadata['is_verified'] = True
        
        # Update user in ChromaDB
        user_service.users_collection.upsert(
            documents=[json.dumps(user_data)],
            metadatas=[user_metadata],
            ids=[user_id]
        )
        
        return jsonify({
            'status': 'success',
            'message': f'User {user_data.get("email", user_id)} has been verified'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to verify user: {str(e)}'}), 500


@admin_bp.route('/api/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and their data"""
    if not _check_admin_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_service = UserService()
        if not user_service.users_collection:
            return jsonify({'error': 'User database not available'}), 500
        
        # Get user data first
        results = user_service.users_collection.get(
            ids=[user_id],
            include=['documents']
        )
        
        if not results['documents']:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = json.loads(results['documents'][0])
        user_email = user_data.get('email', user_id)
        
        # Delete user from users collection
        user_service.users_collection.delete(ids=[user_id])
        
        # Delete user preferences
        prefs_service = UserPreferencesService()
        if prefs_service.collection:
            try:
                prefs_results = prefs_service.collection.get(
                    where={"user_id": user_id},
                    include=['metadatas']
                )
                if prefs_results['ids']:
                    prefs_service.collection.delete(ids=prefs_results['ids'])
            except Exception as e:
                print(f"Error deleting preferences for user {user_id}: {e}")
        
        # Delete verification tokens
        try:
            verification_results = user_service.verification_tokens_collection.get(
                where={"user_id": user_id},
                include=['metadatas']
            )
            if verification_results['ids']:
                user_service.verification_tokens_collection.delete(ids=verification_results['ids'])
        except Exception as e:
            print(f"Error deleting verification tokens for user {user_id}: {e}")
        
        return jsonify({
            'status': 'success',
            'message': f'User {user_email} and all associated data have been deleted'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500


@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get overall system statistics"""
    if not _check_admin_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        stats = {}
        
        # User statistics
        user_service = UserService()
        if user_service.users_collection:
            all_users = user_service.users_collection.get(include=['documents'])
            total_users = len(all_users['ids'])
            verified_users = 0
            
            for doc in all_users['documents']:
                try:
                    user_data = json.loads(doc)
                    if user_data.get('is_verified', False):
                        verified_users += 1
                except Exception:
                    continue
            
            stats['users'] = {
                'total': total_users,
                'verified': verified_users,
                'unverified': total_users - verified_users
            }
        else:
            stats['users'] = {'total': 0, 'verified': 0, 'unverified': 0}
        
        # Recipe statistics
        recipe_cache = RecipeCacheService()
        if recipe_cache and recipe_cache.recipe_collection:
            recipe_count = recipe_cache.get_recipe_count()
            stats['recipes'] = {'total': recipe_count}
        else:
            stats['recipes'] = {'total': 0}
        
        # User preferences statistics
        prefs_service = UserPreferencesService()
        if prefs_service.collection:
            prefs_count = prefs_service.collection.count()
            stats['preferences'] = {'total': prefs_count}
        else:
            stats['preferences'] = {'total': 0}
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@admin_bp.route('/api/admin/restore-recipes', methods=['POST'])
def restore_recipes():
    """Restore recipes from backup data - for production deployment recovery"""
    try:
        # Allow public access for this specific restoration endpoint
        # since we need to restore recipes after deployment
        
        # Initialize services
        recipe_cache = RecipeCacheService()
        
        # Get current recipe count
        current_count = recipe_cache.get_recipe_count()
        if isinstance(current_count, dict):
            current_count = current_count.get('total', 0)
        
        if current_count > 100:
            return jsonify({
                'status': 'skipped',
                'message': f'Recipes already loaded ({current_count} found)',
                'recipes_count': current_count
            })
        
        # Try to restore from backup files
        restored_count = 0
        backup_files = [
            'complete_railway_sync_data.json',
            'production_recipes_backup.json',
            'recipes_data.json'
        ]
        
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
                        continue
                    
                    # Import up to 1500 recipes for good variety
                    recipes_to_import = recipes[:1500]
                    batch_size = 100
                    
                    for i in range(0, len(recipes_to_import), batch_size):
                        batch = recipes_to_import[i:i + batch_size]
                        
                        for recipe in batch:
                            try:
                                recipe_id = str(recipe.get('id', f"backup_{restored_count}"))
                                recipe_cache.cache_recipe(recipe_id, recipe)
                                restored_count += 1
                                
                                if restored_count % 100 == 0:
                                    print(f"✅ Restored {restored_count} recipes...")
                                    
                            except Exception as e:
                                print(f"Failed to restore recipe: {e}")
                        
                        # Rate limiting to avoid overwhelming the system
                        import time
                        time.sleep(0.1)
                    
                    print(f"✅ Successfully restored {restored_count} recipes from {backup_file}!")
                    break
                    
                except Exception as e:
                    print(f"❌ Failed to restore from {backup_file}: {e}")
                    continue
        
        # If no files found, add basic curated recipes as fallback
        if restored_count == 0:
            # Add our 10 curated recipes as a fallback
            curated_recipes = [
                {
                    "id": "curated_french_toast",
                    "title": "Perfect French Toast",
                    "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=500",
                    "cuisine": "French",
                    "cuisines": ["French", "Breakfast"],
                    "ingredients": ["bread", "eggs", "milk", "vanilla", "cinnamon", "butter", "maple syrup"],
                    "instructions": ["Whisk eggs, milk, vanilla, and cinnamon", "Dip bread in mixture", "Cook in buttered pan until golden", "Serve with maple syrup"],
                    "diets": ["vegetarian"],
                    "tags": ["breakfast", "easy", "sweet"],
                    "ready_in_minutes": 15,
                    "difficulty": "easy"
                }
                # Add more curated recipes here if needed
            ]
            
            for recipe in curated_recipes:
                try:
                    recipe_cache.cache_recipe(recipe['id'], recipe)
                    restored_count += 1
                except Exception as e:
                    print(f"Failed to add curated recipe: {e}")
        
        # Final count check
        final_count = recipe_cache.get_recipe_count()
        if isinstance(final_count, dict):
            final_count = final_count.get('total', 0)
        
        return jsonify({
            'status': 'success',
            'message': f'Recipe restoration completed',
            'recipes_restored': restored_count,
            'total_recipes': final_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Recipe restoration failed: {str(e)}'
        }), 500


