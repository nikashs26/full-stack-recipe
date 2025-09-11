"""
Migration API endpoints for proper recipe upload with format preservation
"""

from flask import Blueprint, request, jsonify
import json
import logging
from typing import Dict, List, Any, Optional
import traceback
from datetime import datetime

# Import your existing services
from ..services.recipe_cache_service import RecipeCacheService
from ..utils.chromadb_singleton import get_chromadb_client

logger = logging.getLogger(__name__)

migration_bp = Blueprint('migration', __name__)

@migration_bp.route('/api/admin/maintenance', methods=['POST'])
def maintenance_operations():
    """Handle ChromaDB maintenance operations"""
    try:
        # Verify admin token
        admin_token = request.headers.get('X-Admin-Token')
        if not admin_token or admin_token != "390a77929dbe4a50705a8d8cd2888678":
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json()
        action = data.get('action')
        
        if action == 'reset_chromadb_schema':
            return reset_chromadb_schema(data)
        else:
            return jsonify({"error": "Unknown action"}), 400
            
    except Exception as e:
        logger.error(f"Maintenance operation error: {e}")
        return jsonify({"error": str(e)}), 500

def reset_chromadb_schema(data: Dict[str, Any]) -> tuple:
    """Reset ChromaDB schema to fix compatibility issues"""
    try:
        force_clean = data.get('force_clean', False)
        migrate_to_latest = data.get('migrate_to_latest', False)
        
        logger.info(f"Resetting ChromaDB schema: force_clean={force_clean}, migrate={migrate_to_latest}")
        
        client = get_chromadb_client()
        if client is None:
            return jsonify({"error": "ChromaDB not available"}), 500
        
        collections_reset = []
        
        if force_clean:
            # List existing collections
            try:
                existing_collections = client.list_collections()
                for collection in existing_collections:
                    try:
                        client.delete_collection(collection.name)
                        collections_reset.append(collection.name)
                        logger.info(f"Deleted collection: {collection.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete collection {collection.name}: {e}")
            except Exception as e:
                logger.warning(f"Could not list collections: {e}")
        
        # Create fresh collections with proper schema
        recipe_cache = RecipeCacheService()
        
        return jsonify({
            "success": True,
            "message": "ChromaDB schema reset completed",
            "collections_reset": collections_reset,
            "new_collections_created": ["recipe_search_cache", "recipe_details_cache"]
        }), 200
        
    except Exception as e:
        logger.error(f"ChromaDB reset error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@migration_bp.route('/api/admin/seed', methods=['POST'])
def enhanced_seed_recipes():
    """Enhanced recipe seeding with format preservation"""
    try:
        # Verify admin token
        admin_token = request.headers.get('X-Admin-Token')
        if not admin_token or admin_token != "390a77929dbe4a50705a8d8cd2888678":
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json()
        action = data.get('action', 'upload_complete_recipes')
        
        if action == 'upload_complete_recipes':
            return upload_complete_recipes(data)
        elif action == 'batch_upload':
            return batch_upload_legacy(data)
        elif action == 'single_upload':
            return single_upload_legacy(data)
        else:
            return jsonify({"error": "Unknown action"}), 400
            
    except Exception as e:
        logger.error(f"Seed operation error: {e}")
        return jsonify({"error": str(e)}), 500

def upload_complete_recipes(data: Dict[str, Any]) -> tuple:
    """Upload complete recipes with proper format preservation"""
    try:
        recipes = data.get('recipes', [])
        preserve_format = data.get('preserve_format', True)
        batch_info = data.get('batch_info', {})
        
        if not recipes:
            return jsonify({"error": "No recipes provided"}), 400
        
        logger.info(f"Uploading {len(recipes)} complete recipes (preserve_format={preserve_format})")
        
        # Initialize recipe cache service
        recipe_cache = RecipeCacheService()
        
        if recipe_cache.recipe_collection is None:
            logger.error("Recipe collection not available")
            return jsonify({"error": "Recipe storage not available"}), 500
        
        uploaded_count = 0
        errors = []
        
        for i, recipe in enumerate(recipes):
            try:
                # Validate recipe has essential data
                if not _validate_complete_recipe(recipe):
                    errors.append(f"Recipe {i}: Missing essential data")
                    continue
                
                # Store recipe with proper format
                recipe_id = str(recipe.get('id', f'imported_{i}'))
                
                # Create the document (for search) - combine key fields
                document_text = _create_search_document(recipe)
                
                # Create comprehensive metadata
                metadata = _create_recipe_metadata(recipe)
                
                # Store the complete recipe as JSON document
                recipe_json = json.dumps(recipe, ensure_ascii=False)
                
                # Upsert to ChromaDB
                recipe_cache.recipe_collection.upsert(
                    ids=[recipe_id],
                    documents=[recipe_json],
                    metadatas=[metadata]
                )
                
                uploaded_count += 1
                
                if uploaded_count % 5 == 0:
                    logger.info(f"Uploaded {uploaded_count}/{len(recipes)} recipes...")
                    
            except Exception as e:
                error_msg = f"Recipe {i} ({recipe.get('title', 'Unknown')}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        logger.info(f"Upload complete: {uploaded_count} success, {len(errors)} errors")
        
        return jsonify({
            "success": True,
            "uploaded_count": uploaded_count,
            "total_recipes": len(recipes),
            "errors": errors[:10],  # Limit error list
            "batch_info": batch_info
        }), 200
        
    except Exception as e:
        logger.error(f"Upload complete recipes error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

def _validate_complete_recipe(recipe: Dict[str, Any]) -> bool:
    """Validate that a recipe has essential complete data"""
    required_fields = ['title', 'ingredients', 'instructions']
    
    for field in required_fields:
        if not recipe.get(field):
            return False
        
        if field == 'ingredients':
            ingredients = recipe[field]
            if not isinstance(ingredients, list) or len(ingredients) == 0:
                return False
            # Check at least one ingredient has a name
            if not any(ing.get('name') for ing in ingredients if isinstance(ing, dict)):
                return False
        
        if field == 'instructions':
            instructions = recipe[field]
            if not isinstance(instructions, list) or len(instructions) == 0:
                return False
            # Check at least one instruction is not empty
            if not any(inst.strip() for inst in instructions if isinstance(inst, str)):
                return False
    
    return True

def _create_search_document(recipe: Dict[str, Any]) -> str:
    """Create searchable document text from recipe"""
    parts = [
        recipe.get('title', ''),
        ' '.join(recipe.get('cuisines', [])),
        ' '.join(recipe.get('tags', [])),
        ' '.join(recipe.get('dish_types', [])),
        ' '.join(recipe.get('diets', []))
    ]
    
    # Add ingredient names
    ingredients = recipe.get('ingredients', [])
    if isinstance(ingredients, list):
        ingredient_names = [
            ing.get('name', '') for ing in ingredients 
            if isinstance(ing, dict) and ing.get('name')
        ]
        parts.extend(ingredient_names)
    
    return ' '.join(filter(None, parts))

def _create_recipe_metadata(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Create comprehensive metadata for ChromaDB"""
    metadata = {
        'id': str(recipe.get('id', '')),
        'title': recipe.get('title', ''),
        'type': recipe.get('type', 'imported'),
        'source': recipe.get('source', 'migration'),
        'uploaded_at': datetime.utcnow().isoformat()
    }
    
    # Add cuisines
    cuisines = recipe.get('cuisines', [])
    if isinstance(cuisines, list) and cuisines:
        metadata['cuisines'] = ','.join(cuisines)
        metadata['cuisine'] = cuisines[0]  # Primary cuisine
    
    # Add diets
    diets = recipe.get('diets', [])
    if isinstance(diets, list) and diets:
        metadata['diets'] = ','.join(diets)
    
    # Add tags
    tags = recipe.get('tags', [])
    if isinstance(tags, list) and tags:
        metadata['tags'] = ','.join(tags)
    
    # Add dish types
    dish_types = recipe.get('dish_types', [])
    if isinstance(dish_types, list) and dish_types:
        metadata['dish_types'] = ','.join(dish_types)
    
    # Add nutrition info
    nutrition = recipe.get('nutrition', {})
    if isinstance(nutrition, dict):
        metadata['calories'] = nutrition.get('calories', 0)
        metadata['protein'] = nutrition.get('protein', 0)
        metadata['carbs'] = nutrition.get('carbs', 0)
        metadata['fat'] = nutrition.get('fat', 0)
    
    # Add ingredient count
    ingredients = recipe.get('ingredients', [])
    if isinstance(ingredients, list):
        metadata['ingredient_count'] = len(ingredients)
    
    # Add cooking time
    metadata['ready_in_minutes'] = recipe.get('ready_in_minutes', 30)
    
    # Add image availability
    metadata['has_image'] = bool(recipe.get('image', '').strip())
    
    return metadata

def batch_upload_legacy(data: Dict[str, Any]) -> tuple:
    """Legacy batch upload support"""
    recipes = data.get('recipes', [])
    
    # Convert to complete recipe format and use new upload method
    complete_recipes = []
    for recipe in recipes:
        complete_recipe = _convert_legacy_recipe(recipe)
        if complete_recipe:
            complete_recipes.append(complete_recipe)
    
    return upload_complete_recipes({
        "recipes": complete_recipes,
        "preserve_format": True,
        "batch_info": data.get('batch_info', {})
    })

def single_upload_legacy(data: Dict[str, Any]) -> tuple:
    """Legacy single upload support"""
    recipe = data.get('recipe', {})
    
    complete_recipe = _convert_legacy_recipe(recipe)
    if not complete_recipe:
        return jsonify({"error": "Invalid recipe data"}), 400
    
    return upload_complete_recipes({
        "recipes": [complete_recipe],
        "preserve_format": True
    })

def _convert_legacy_recipe(recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert legacy/flattened recipe format to complete format"""
    try:
        # Handle flattened data (JSON strings need to be parsed)
        complete_recipe = {}
        
        for key, value in recipe.items():
            if isinstance(value, str) and value.strip().startswith(('[', '{')):
                # Try to parse JSON strings
                try:
                    complete_recipe[key] = json.loads(value)
                except:
                    complete_recipe[key] = value
            else:
                complete_recipe[key] = value
        
        # Ensure required fields exist
        if not complete_recipe.get('title'):
            return None
        
        if not complete_recipe.get('ingredients'):
            complete_recipe['ingredients'] = []
        
        if not complete_recipe.get('instructions'):
            complete_recipe['instructions'] = ["No instructions provided."]
        
        # Ensure arrays are properly formatted
        for field in ['cuisines', 'diets', 'tags', 'dish_types']:
            value = complete_recipe.get(field, [])
            if isinstance(value, str):
                complete_recipe[field] = [value] if value.strip() else []
            elif not isinstance(value, list):
                complete_recipe[field] = []
        
        return complete_recipe
        
    except Exception as e:
        logger.error(f"Error converting legacy recipe: {e}")
        return None

@migration_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Get admin statistics"""
    try:
        admin_token = request.args.get('token')
        if not admin_token or admin_token != "390a77929dbe4a50705a8d8cd2888678":
            return jsonify({"error": "Unauthorized"}), 401
        
        client = get_chromadb_client()
        if client is None:
            return jsonify({"error": "ChromaDB not available"}), 500
        
        stats = {
            "chromadb_available": True,
            "collections": [],
            "recipe_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            collections = client.list_collections()
            for collection in collections:
                collection_info = {
                    "name": collection.name,
                    "count": collection.count()
                }
                stats["collections"].append(collection_info)
                
                if collection.name == "recipe_details_cache":
                    stats["recipe_count"] = collection.count()
        except Exception as e:
            stats["error"] = str(e)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        return jsonify({"error": str(e)}), 500
