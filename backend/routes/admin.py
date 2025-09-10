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


