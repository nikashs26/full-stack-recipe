from flask import Blueprint, request, jsonify
from services.recipe_search_service import RecipeSearchService
from services.meal_history_service import MealHistoryService
from services.smart_shopping_service import SmartShoppingService
from services.user_preferences_service import UserPreferencesService
import logging
from middleware.auth_middleware import get_current_user_id, require_auth
from flask_cors import cross_origin

logger = logging.getLogger(__name__)

smart_features_bp = Blueprint('smart_features', __name__)

# Initialize services
recipe_search_service = RecipeSearchService()
meal_history_service = MealHistoryService()
smart_shopping_service = SmartShoppingService()
user_preferences_service = UserPreferencesService()

@smart_features_bp.route('/search/semantic', methods=['POST'])
def semantic_recipe_search():
    """
    Semantic recipe search endpoint
    
    Example queries:
    - "healthy dinner for weight loss"
    - "quick breakfast with eggs"
    - "comfort food for cold weather"
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "success": False
            }), 400
            
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request format",
                "success": False
            }), 400
        
        # Get and validate parameters
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                "error": "Query is required",
                "success": False
            }), 400
            
        # Validate filters
        filters = data.get('filters', {})
        if not isinstance(filters, dict):
            return jsonify({
                "error": "Filters must be an object",
                "success": False
            }), 400
            
        # Validate and bound limit
        try:
            limit = int(data.get('limit', 10))
            limit = max(1, min(limit, 50))  # Bound between 1 and 50
        except (ValueError, TypeError):
            limit = 10
        
        # Perform semantic search with error handling
        try:
            results = recipe_search_service.semantic_search(query, filters, limit)
            
            if not isinstance(results, list):
                return jsonify({
                    "error": "Invalid search results format",
                    "success": False
                }), 500
            
            return jsonify({
                "success": True,
                "query": query,
                "results": results,
                "total": len(results),
                "filters_applied": filters,
                "limit_used": limit
            }), 200
            
        except Exception as search_error:
            logger.error(f"Semantic search error: {search_error}")
            return jsonify({
                "error": "Failed to perform semantic search",
                "details": str(search_error),
                "success": False
            }), 500
            
    except Exception as e:
        logger.error(f"Semantic search endpoint error: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "success": False
        }), 500

@smart_features_bp.route('/search/similar/<recipe_id>', methods=['GET'])
def find_similar_recipes(recipe_id):
    """
    Find recipes similar to a given recipe
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        
        results = recipe_search_service.find_similar_recipes(recipe_id, limit)
        
        return jsonify({
            "success": True,
            "recipe_id": recipe_id,
            "similar_recipes": results,
            "total": len(results)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recommendations', methods=['GET'])
@require_auth  # Enable authentication to get proper user ID
def get_personalized_recommendations():
    """
    Get personalized recipe recommendations based on user preferences
    """
    try:
        # Get the actual user ID
        user_id = get_current_user_id()
        print(f"🔍 Recommendations endpoint - User ID: {user_id}")
        
        limit = request.args.get('limit', 16, type=int)  # Increased from 8 to 16 for better cuisine distribution
        print(f"📊 Requested limit: {limit}")
        
        # Get user preferences from the database
        preferences = user_preferences_service.get_preferences(user_id)
        print(f"📋 Retrieved preferences: {preferences}")
        
        if not preferences:
            print("⚠️ No preferences found")
            return jsonify({
                "success": True,
                "recommendations": [],
                "message": "No preferences found. Please set your preferences first."
            }), 200
        
        # Log the preferences being used for debugging
        print(f"✅ Using preferences for user {user_id}: {preferences}")
        
        results = recipe_search_service.get_recipe_recommendations(preferences, limit)
        print(f"🎯 Generated {len(results)} recommendations")
        
        return jsonify({
            "success": True,
            "recommendations": results,
            "preferences_used": preferences,
            "total": len(results)
        }), 200
        
    except Exception as e:
        print(f"❌ Error in recommendations endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recommendations/simple', methods=['GET'])
def get_simple_recommendations():
    """
    Get simple, fast recipe recommendations without complex AI processing
    Note: This endpoint ignores user preferences for speed. Use /recommendations for personalized results.
    """
    try:
        limit = request.args.get('limit', 8, type=int)
        print(f"🚀 Simple recommendations - Requested limit: {limit}")
        
        # Get recipes directly from the recipe cache (much faster)
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        # Get a simple list of popular recipes
        all_recipes = recipe_cache.get_cached_recipes()  # Get all recipes
        
        if not all_recipes:
            print("⚠️ No recipes found in simple recommendations")
            return jsonify({
                "success": True,
                "recommendations": [],
                "message": "No recipes available"
            }), 200
        
        # Implement diverse sampling to avoid clustering by cuisine
        import random
        
        # Group recipes by cuisine for better distribution
        recipes_by_cuisine = {}
        for recipe in all_recipes:
            cuisine = recipe.get('cuisine', 'Unknown')
            if cuisine not in recipes_by_cuisine:
                recipes_by_cuisine[cuisine] = []
            recipes_by_cuisine[cuisine].append(recipe)
        
        print(f"📊 Found recipes from {len(recipes_by_cuisine)} cuisines: {list(recipes_by_cuisine.keys())}")
        print(f"⚠️  WARNING: Simple recommendations ignore user preferences. Showing variety from all cuisines.")
        
        # Shuffle cuisines to avoid always starting with the same ones
        cuisines = list(recipes_by_cuisine.keys())
        random.shuffle(cuisines)
        
        # Sample evenly from each cuisine to ensure variety
        formatted_recipes = []
        
        # Calculate how many recipes to take from each cuisine
        recipes_per_cuisine = max(1, limit // len(cuisines))
        extra_recipes = limit % len(cuisines)
        
        for i, cuisine in enumerate(cuisines):
            cuisine_recipes = recipes_by_cuisine[cuisine]
            # Take recipes_per_cuisine + 1 extra for the first few cuisines
            current_limit = recipes_per_cuisine + (1 if i < extra_recipes else 0)
            
            # Randomly sample from this cuisine's recipes
            if len(cuisine_recipes) > current_limit:
                sampled_recipes = random.sample(cuisine_recipes, current_limit)
            else:
                sampled_recipes = cuisine_recipes
            
            for recipe in sampled_recipes:
                if len(formatted_recipes) >= limit:
                    break
                    
                # Include ALL available recipe fields for complete data
                formatted_recipe = {
                    "id": recipe.get('id', recipe.get('recipe_id', 'unknown')),
                    "title": recipe.get('title', recipe.get('name', 'Unknown Recipe')),
                    "name": recipe.get('title', recipe.get('name', 'Unknown Recipe')),
                    "cuisine": recipe.get('cuisine', ''),
                    "cuisines": [recipe.get('cuisine', '')] if recipe.get('cuisine') else [],
                    "image": recipe.get('image', ''),
                    "calories": recipe.get('calories', 0),
                    "protein": recipe.get('protein', 0),
                    "carbs": recipe.get('carbs', 0),
                    "fat": recipe.get('fat', 0),
                    "source": recipe.get('source', ''),
                    "type": "recommended",
                    
                    # Add missing fields that the frontend expects
                    "tags": recipe.get('tags', []),
                    "dietary_restrictions": recipe.get('dietary_restrictions', []),
                    "diets": recipe.get('diets', []),
                    "ingredients": recipe.get('ingredients', []),
                    "instructions": recipe.get('instructions', []),
                    "servings": recipe.get('servings', 1),
                    "readyInMinutes": recipe.get('readyInMinutes', recipe.get('cooking_time', 0)),
                    "cooking_time": recipe.get('cooking_time', ''),
                    "difficulty": recipe.get('difficulty', ''),
                    "meal_type": recipe.get('meal_type', ''),
                    "avg_rating": recipe.get('avg_rating', 0),
                    "ratings": recipe.get('ratings', 0),
                    "prep_time": recipe.get('prep_time', ''),
                    "total_time": recipe.get('total_time', ''),
                    "dish_types": recipe.get('dish_types', []),
                    "occasions": recipe.get('occasions', [])
                }
                formatted_recipes.append(formatted_recipe)
        
        print(f"✅ Simple recommendations: {len(formatted_recipes)} recipes")
        
        return jsonify({
            "success": True,
            "recommendations": formatted_recipes,
            "total": len(formatted_recipes),
            "message": "Simple recommendations generated successfully"
        }), 200
        
    except Exception as e:
        print(f"❌ Error in simple recommendations: {e}")
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recommendations/test-balance', methods=['GET'])
@cross_origin(origins=["http://localhost:5173"], supports_credentials=True)
def test_recommendation_balance():
    """Test endpoint to check recommendation balance and distribution"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "User not authenticated"
            }), 401
        
        # Get user preferences
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "status": "error",
                "message": "No user preferences found"
            }), 404
        
        # Get recommendations
        limit = int(request.args.get('limit', 8))
        results = recipe_search_service.get_recipe_recommendations(preferences, limit)
        
        # Analyze distribution
        cuisine_counts = {}
        favorite_food_matches = []
        
        for recipe in results:
            # Count cuisines
            cuisine = recipe.get('cuisine', 'Unknown')
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            
            # Check for favorite food matches
            if preferences.get('favoriteFoods'):
                recipe_text = f"{recipe.get('title', '')} {recipe.get('description', '')}".lower()
                for food in preferences['favoriteFoods']:
                    if food.lower() in recipe_text:
                        favorite_food_matches.append({
                            'recipe': recipe.get('title', recipe.get('name', 'Unknown')),
                            'favorite_food': food,
                            'cuisine': cuisine
                        })
                        break
        
        # Calculate balance metrics
        total_recipes = len(results)
        max_cuisine_count = max(cuisine_counts.values()) if cuisine_counts else 0
        min_cuisine_count = min(cuisine_counts.values()) if cuisine_counts else 0
        balance_ratio = max_cuisine_count / min_cuisine_count if min_cuisine_count > 0 else float('inf')
        
        return jsonify({
            "status": "success",
            "data": {
                "total_recipes": total_recipes,
                "cuisine_distribution": cuisine_counts,
                "favorite_food_matches": favorite_food_matches,
                "balance_metrics": {
                    "max_cuisine_count": max_cuisine_count,
                    "min_cuisine_count": min_cuisine_count,
                    "balance_ratio": round(balance_ratio, 2),
                    "is_balanced": balance_ratio <= 2.0
                },
                "recommendations": results
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error in test balance endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to test recommendations: {str(e)}"
        }), 500

@smart_features_bp.route('/recommendations/debug', methods=['GET'])
@cross_origin(origins=["http://localhost:5173"], supports_credentials=True)
def debug_recommendations():
    """Debug endpoint to investigate cuisine distribution issues"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "User not authenticated"
            }), 401
        
        # Get user preferences
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "status": "error",
                "message": "No user preferences found"
            }), 404
        
        limit = int(request.args.get('limit', 8))
        
        # Get recommendations
        results = recipe_search_service.get_recipe_recommendations(preferences, limit)
        
        # Detailed analysis
        cuisine_counts = {}
        cuisine_details = {}
        favorite_food_matches = []
        
        for i, recipe in enumerate(results):
            # Count cuisines
            cuisine = recipe.get('cuisine', 'Unknown')
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            
            # Track recipe details for each cuisine
            if cuisine not in cuisine_details:
                cuisine_details[cuisine] = []
            
            recipe_info = {
                'index': i,
                'title': recipe.get('title') or recipe.get('name', 'Unknown'),
                'id': recipe.get('id') or recipe.get('_id', 'Unknown'),
                'original_cuisine': recipe.get('cuisine', 'Unknown'),
                'detected_cuisine': recipe_search_service._detect_cuisine_from_ingredients(recipe),
                'normalized_cuisine': recipe_search_service._normalize_cuisine(recipe.get('cuisine', ''), recipe)
            }
            cuisine_details[cuisine].append(recipe_info)
            
            # Check for favorite food matches
            if preferences.get('favoriteFoods'):
                recipe_text = f"{recipe.get('title', '')} {recipe.get('description', '')}".lower()
                for food in preferences['favoriteFoods']:
                    if food.lower() in recipe_text:
                        favorite_food_matches.append({
                            'recipe': recipe.get('title', recipe.get('name', 'Unknown')),
                            'favorite_food': food,
                            'cuisine': cuisine,
                            'index': i
                        })
                        break
        
        # Analyze distribution
        total_recipes = len(results)
        max_cuisine_count = max(cuisine_counts.values()) if cuisine_counts else 0
        min_cuisine_count = min(cuisine_counts.values()) if cuisine_counts else 0
        balance_ratio = max_cuisine_count / min_cuisine_count if min_cuisine_count > 0 else float('inf')
        
        # Check if user preferences match what we're seeing
        user_cuisines = preferences.get('favoriteCuisines', [])
        user_foods = preferences.get('favoriteFoods', [])
        
        return jsonify({
            "status": "success",
            "data": {
                "user_preferences": {
                    "favoriteCuisines": user_cuisines,
                    "favoriteFoods": user_foods,
                    "dietaryRestrictions": preferences.get('dietaryRestrictions', [])
                },
                "requested_limit": limit,
                "total_recipes": total_recipes,
                "cuisine_distribution": cuisine_counts,
                "cuisine_details": cuisine_details,
                "favorite_food_matches": favorite_food_matches,
                "balance_metrics": {
                    "max_cuisine_count": max_cuisine_count,
                    "min_cuisine_count": min_cuisine_count,
                    "balance_ratio": round(balance_ratio, 2),
                    "is_balanced": balance_ratio <= 2.0
                },
                "analysis": {
                    "expected_cuisines": len(user_cuisines),
                    "expected_per_cuisine": limit // len(user_cuisines) if user_cuisines else 0,
                    "actual_distribution": cuisine_counts,
                    "distribution_issues": []
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error in debug endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to debug recommendations: {str(e)}"
        }), 500

@smart_features_bp.route('/meal-history/log', methods=['POST'])
@cross_origin(origins=['http://localhost:8081', 'http://localhost:5173'], supports_credentials=True)
@require_auth
def log_meal_generation():
    """
    Log when a meal plan is generated
    """
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
            
        print(f"💾 Logging meal generation for user: {user_id}")
        
        meal_plan = data.get('meal_plan', {})
        preferences_used = data.get('preferences_used', {})
        
        meal_history_service.log_meal_generated(user_id, meal_plan, preferences_used)
        
        print(f"✅ Meal generation logged successfully for user: {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Meal generation logged successfully"
        }), 200
        
    except Exception as e:
        print(f"❌ Error logging meal generation: {e}")
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/feedback', methods=['POST'])
def log_meal_feedback():
    """
    Log user feedback on meals
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        meal_id = data.get('meal_id', '')
        feedback_type = data.get('feedback_type', '')  # 'liked', 'disliked', 'cooked', 'skipped'
        rating = data.get('rating')
        notes = data.get('notes')
        
        if not meal_id or not feedback_type:
            return jsonify({"error": "meal_id and feedback_type are required"}), 400
        
        meal_history_service.log_meal_feedback(user_id, meal_id, feedback_type, rating, notes)
        
        return jsonify({
            "success": True,
            "message": "Feedback logged successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/patterns/<user_id>', methods=['GET'])
def get_meal_patterns(user_id):
    """
    Get user's meal patterns and preferences from history
    """
    try:
        days_back = request.args.get('days_back', 30, type=int)
        
        patterns = meal_history_service.get_user_meal_patterns(user_id, days_back)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
            "days_analyzed": days_back
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/suggestions', methods=['GET'])
def get_personalized_meal_suggestions():
    """
    Get personalized meal suggestions based on history
    """
    try:
        user_id = request.args.get('user_id', 'demo_user')
        meal_type = request.args.get('meal_type', 'dinner')
        exclude_recent = request.args.get('exclude_recent', 'true').lower() == 'true'
        
        suggestions = meal_history_service.get_personalized_meal_suggestions(user_id, meal_type, exclude_recent)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "meal_type": meal_type,
            "suggestions": suggestions
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/trending', methods=['GET'])
def get_trending_meals():
    """
    Get trending meals based on recent positive feedback
    """
    try:
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        trending = meal_history_service.get_trending_meals(days_back, limit)
        
        return jsonify({
            "success": True,
            "trending_meals": trending,
            "days_analyzed": days_back
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/smart-list', methods=['POST'])
def create_smart_shopping_list():
    """
    Create an intelligent shopping list from meal plans
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        meal_plans = data.get('meal_plans', [])
        dietary_restrictions = data.get('dietary_restrictions', [])
        
        if not meal_plans:
            return jsonify({"error": "meal_plans are required"}), 400
        
        shopping_list = smart_shopping_service.create_smart_shopping_list(
            user_id, meal_plans, dietary_restrictions
        )
        
        return jsonify({
            "success": True,
            "shopping_list": shopping_list
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/substitutions', methods=['GET'])
def get_ingredient_substitutions():
    """
    Get possible substitutions for an ingredient
    """
    try:
        ingredient_name = request.args.get('ingredient', '')
        dietary_restrictions = request.args.getlist('dietary_restrictions')
        
        if not ingredient_name:
            return jsonify({"error": "ingredient parameter is required"}), 400
        
        substitutions = smart_shopping_service.get_ingredient_substitutions(
            ingredient_name, dietary_restrictions
        )
        
        return jsonify({
            "success": True,
            "ingredient": ingredient_name,
            "substitutions": substitutions,
            "dietary_restrictions": dietary_restrictions
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/missing-ingredients', methods=['POST'])
def find_missing_ingredients():
    """
    Find ingredients that are missing from user's pantry
    """
    try:
        data = request.get_json()
        user_pantry = data.get('user_pantry', [])
        shopping_list = data.get('shopping_list', [])
        
        missing_ingredients = smart_shopping_service.find_missing_ingredients(
            user_pantry, shopping_list
        )
        
        return jsonify({
            "success": True,
            "missing_ingredients": missing_ingredients,
            "pantry_items": len(user_pantry),
            "shopping_list_items": len(shopping_list)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/history/<user_id>', methods=['GET'])
def get_shopping_history(user_id):
    """
    Get user's shopping list history
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        history = smart_shopping_service.get_shopping_list_history(user_id, limit)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "history": history,
            "total": len(history)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recipes/index', methods=['POST'])
def index_recipe():
    """
    Index a recipe for semantic search
    """
    try:
        data = request.get_json()
        recipe = data.get('recipe', {})
        
        if not recipe:
            return jsonify({"error": "recipe data is required"}), 400
        
        recipe_search_service.index_recipe(recipe)
        
        return jsonify({
            "success": True,
            "message": "Recipe indexed successfully",
            "recipe_id": recipe.get('id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recipes/bulk-index', methods=['POST'])
def bulk_index_recipes():
    """
    Index multiple recipes at once
    """
    try:
        data = request.get_json()
        recipes = data.get('recipes', [])
        
        if not recipes:
            return jsonify({"error": "recipes array is required"}), 400
        
        recipe_search_service.bulk_index_recipes(recipes)
        
        return jsonify({
            "success": True,
            "message": f"Successfully indexed {len(recipes)} recipes",
            "total_indexed": len(recipes)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/analytics/meal-success-rate', methods=['GET'])
def get_meal_success_rate():
    """
    Get success metrics for a specific meal
    """
    try:
        user_id = request.args.get('user_id', 'demo_user')
        meal_id = request.args.get('meal_id', '')
        
        if not meal_id:
            return jsonify({"error": "meal_id parameter is required"}), 400
        
        success_rate = meal_history_service.get_meal_success_rate(user_id, meal_id)
        
        return jsonify({
            "success": True,
            "meal_id": meal_id,
            "success_metrics": success_rate
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history', methods=['GET'])
@cross_origin(origins=['http://localhost:8081', 'http://localhost:5173'], supports_credentials=True)
@require_auth
def get_meal_plan_history():
    """
    Get user's meal plan generation history
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        print(f"🔍 Getting meal history for user: {user_id}")
        
        limit = request.args.get('limit', 20, type=int)
        limit = max(1, min(limit, 50))  # Bound between 1 and 50
        
        history = meal_history_service.get_user_meal_plan_history(user_id, limit)
        
        print(f"📊 Found {len(history)} meal plans in history")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "history": history,
            "total": len(history),
            "limit_used": limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving meal plan history: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve meal plan history",
            "details": str(e)
        }), 500

@smart_features_bp.route('/meal-history/<plan_id>', methods=['GET'])
@cross_origin(origins=['http://localhost:8081', 'http://localhost:5173'], supports_credentials=True)
@require_auth
def get_meal_plan_details(plan_id):
    """
    Get detailed information about a specific meal plan
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        plan_details = meal_history_service.get_meal_plan_details(user_id, plan_id)
        
        if not plan_details:
            return jsonify({
                "success": False,
                "error": "Meal plan not found"
            }), 404
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "plan_details": plan_details
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving meal plan details: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve meal plan details",
            "details": str(e)
        }), 500 