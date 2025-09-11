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
            metas.append(item)

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
        if not user_service.users_collection:
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


