from flask import Blueprint, request, jsonify
import os
import json

# Lazy import to avoid heavy deps at import time
from backend.services.recipe_cache_service import RecipeCacheService

admin_bp = Blueprint('admin', __name__)

def _check_token(req) -> bool:
    token = req.headers.get('X-Admin-Token') or req.args.get('token')
    expected = os.environ.get('ADMIN_SEED_TOKEN')
    return bool(expected) and token == expected

@admin_bp.route('/api/admin/seed', methods=['POST'])
def seed_recipes():
    if not _check_token(request):
        return jsonify({'error': 'Unauthorized'}), 401

    body = request.get_json(silent=True) or {}
    seed_path = body.get('path') or os.environ.get('SEED_RECIPES_FILE', 'recipes_data.json')
    limit = int(body.get('limit') or os.environ.get('SEED_RECIPES_LIMIT', '5000'))

    try:
        cache = RecipeCacheService()
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

        # Prepare minimal fields
        ids, docs, metas = [], [], []
        for item in recipes[:max(0, limit)]:
            rid = str(item.get('id') or item.get('_id') or item.get('idMeal') or hash(item.get('title', '')))
            title = item.get('title') or item.get('name') or item.get('strMeal') or 'Recipe'
            ids.append(rid)
            docs.append(title)
            metas.append(item)

        if not ids:
            return jsonify({'error': 'No recipes to import'}), 400

        # Add to primary recipe store
        cache.recipe_collection.add(ids=ids, documents=docs, metadatas=metas)

        # Also populate search cache so /api/get_recipes works immediately
        try:
            search_docs = []
            for m in metas:
                title = m.get('title') or m.get('name') or m.get('strMeal') or ''
                ingredients = m.get('ingredients') or m.get('strIngredients') or []
                if isinstance(ingredients, list):
                    ing_text = ' '.join([
                        (i.get('name') if isinstance(i, dict) else str(i))
                        for i in ingredients
                    ])
                else:
                    ing_text = str(ingredients)
                cuisines = m.get('cuisines') or []
                cuisine_text = ' '.join(cuisines) if isinstance(cuisines, list) else str(cuisines)
                search_docs.append(f"{title} {ing_text} {cuisine_text}")
            if hasattr(cache, 'search_collection') and cache.search_collection is not None:
                cache.search_collection.add(ids=ids, documents=search_docs, metadatas=metas)
        except Exception:
            pass

        return jsonify({'status': 'ok', 'imported': len(ids), 'path': seed_path}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


